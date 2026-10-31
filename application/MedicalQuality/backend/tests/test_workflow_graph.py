import json
import subprocess
import sys
from datetime import timedelta
import pytest
from fastapi import HTTPException
from sqlalchemy import select

from medical_quality.db import transaction
from medical_quality.models import Actor, Document, Evidence, QualityRun, Rule, Source, Task, now
from medical_quality import quality
from medical_quality.sources import source_path
from medical_quality.remediation import resume_human
from conftest import login, cmd


def isolated_wait(action, task_id, value):
    script = """
import json,sys
from medical_quality.db import transaction
from medical_quality.access import refresh_actor
from medical_quality.remediation import wait_for_human,resume_human
with transaction() as db:
 actor=refresh_actor(db,'qc1')
 result=wait_for_human(db,actor,sys.argv[2],int(sys.argv[3])) if sys.argv[1]=='wait' else resume_human(db,actor,sys.argv[2],sys.argv[3])
print(json.dumps(result))
"""
    result = subprocess.run(
        [sys.executable, "-c", script, action, task_id, str(value)],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    return json.loads(result.stdout)


def actor_record(id):
    with transaction() as db:
        actor = db.get(Actor, id)
        db.expunge(actor)
        return actor


def process_quality(run_id, monkeypatch):
    # Contract-level tests substitute only the generative response; graph, DB, rules,
    # evidence, checkpoint and authorization are the actual implementation.
    monkeypatch.setattr(
        quality,
        "local_model_candidates",
        lambda context: {"status": "candidate_only", "candidates": [], "fixture": True},
    )
    actor = actor_record("qc1")
    computed = quality.compute_run(actor.id, run_id, 1)
    with transaction(actor) as db:
        run = db.get(QualityRun, run_id)
        result = quality.execute_run(db, actor, run, 1, computed)
    return result


def create_processed(client, case_id, monkeypatch):
    headers = login(client, "qc1")
    case = client.get("/api/v1/cases/" + case_id).json()["case"]
    request = client.post(
        "/api/v1/cases/" + case_id + "/quality-runs", headers=headers, json=cmd(case["version"])
    )
    assert request.status_code == 202, request.text
    run_id = request.json()["id"]
    process_quality(run_id, monkeypatch)
    detail = client.get("/api/v1/cases/" + case_id).json()
    task = next(
        t
        for t in detail["tasks"]
        if t["scope_manifest"].get("document_ids")
        and any(f["id"] == t["finding_id"] and f["run_id"] == run_id for f in detail["findings"])
    )
    return headers, run_id, task, detail


def test_full_revision_recheck_dual_signature_and_history(client, monkeypatch):
    headers, run_id, task, detail = create_processed(client, "C001", monkeypatch)
    assert task["state"] == "review"
    accepted = client.post(
        "/api/v1/tasks/" + task["id"] + "/accept", headers=headers, json=cmd(task["version"])
    )
    assert accepted.status_code == 200, accepted.text
    task_version = accepted.json()["version"]
    headers = login(client, "doctor1")
    doc = next(d for d in detail["documents"] if d["document_key"] == "discharge")
    content = doc["content"].replace("藥物過敏史：否認。", "藥物過敏史：青黴素過敏。")
    request = cmd(task_version, {"document_id": doc["id"], "content": content, "fields": doc["fields"]})
    changed = client.post("/api/v1/tasks/" + task["id"] + "/revise", headers=headers, json=request)
    assert changed.status_code == 200, changed.text
    repeat = client.post("/api/v1/tasks/" + task["id"] + "/revise", headers=headers, json=request)
    assert repeat.status_code == 200 and repeat.json() == changed.json()
    revised_id = changed.json()["document_id"]
    actor = actor_record("doctor1")
    with transaction(actor) as db:
        assert db.get(Document, doc["id"]).content == doc["content"]
        assert db.get(Document, revised_id).parent_id == doc["id"]
        for evidence in db.scalars(select(Evidence).where(Evidence.document_id == revised_id)):
            source = db.get(Source, evidence.source_id)
            raw = source_path(source.reference).read_text()
            loc = evidence.envelope["locator"]
            assert raw[loc["char_start"] : loc["char_end"]] == evidence.envelope["content"]["text"]
    premature = client.post(
        "/api/v1/tasks/" + task["id"] + "/sign", headers=headers, json=cmd(changed.json()["version"])
    )
    assert premature.status_code == 409
    headers = login(client, "qc1")
    recheck = client.post(
        "/api/v1/tasks/" + task["id"] + "/recheck", headers=headers, json=cmd(changed.json()["version"])
    )
    assert recheck.status_code == 200, recheck.text
    process_quality(recheck.json()["run_id"], monkeypatch)
    detail = client.get("/api/v1/cases/C001").json()
    current = next(t for t in detail["tasks"] if t["id"] == task["id"])
    assert current["state"] == "verify_ready" and not current["details"]["verification_confirmed"]
    confirm = client.post(
        "/api/v1/tasks/" + task["id"] + "/confirm", headers=headers, json=cmd(current["version"])
    )
    assert confirm.status_code == 200, confirm.text
    signed_qc = client.post(
        "/api/v1/tasks/" + task["id"] + "/sign", headers=headers, json=cmd(confirm.json()["version"])
    )
    assert signed_qc.status_code == 200 and signed_qc.json()["state"] == "sign"
    headers = login(client, "doctor1")
    signed_doctor = client.post(
        "/api/v1/tasks/" + task["id"] + "/sign", headers=headers, json=cmd(signed_qc.json()["version"])
    )
    assert signed_doctor.status_code == 200 and signed_doctor.json()["state"] == "signed"
    detail = client.get("/api/v1/cases/C001").json()
    signatures = [s for s in detail["signatures"] if s["task_id"] == task["id"]]
    assert {s["role"] for s in signatures} == {"qc", "doctor"} and len(
        {s["scope_digest"] for s in signatures}
    ) == 1
    assert all(s["mode"] == "local_engineering" for s in signatures)
    # A new version cannot inherit completion, but historical signatures remain available.
    latest = next(d for d in detail["documents"] if d["id"] == revised_id)
    changed_again = client.post(
        "/api/v1/tasks/" + task["id"] + "/revise",
        headers=headers,
        json=cmd(
            signed_doctor.json()["version"],
            {
                "document_id": revised_id,
                "content": latest["content"] + "\n補充：合成測試新版本。",
                "fields": latest["fields"],
            },
        ),
    )
    assert changed_again.status_code == 200 and changed_again.json()["state"] == "verification_pending"
    assert len(client.get("/api/v1/cases/C001").json()["signatures"]) == len(detail["signatures"])
    with transaction(actor) as db:
        result = resume_human(db, actor, task["id"], changed_again.json()["decision_id"])
        assert result["status"] == "resumed"
    with transaction(actor) as db:
        assert (
            resume_human(db, actor, task["id"], changed_again.json()["decision_id"])["status"]
            == "already_resumed"
        )


def test_appeal_and_false_positive_are_not_rectification(client, monkeypatch):
    headers, run_id, task, detail = create_processed(client, "C008", monkeypatch)
    accepted = client.post(
        "/api/v1/tasks/" + task["id"] + "/accept", headers=headers, json=cmd(task["version"])
    ).json()
    headers = login(client, "doctor2")
    appeal = client.post(
        "/api/v1/tasks/" + task["id"] + "/appeal",
        headers=headers,
        json=cmd(accepted["version"], {"expert_id": "expert3"}),
    )
    assert appeal.status_code == 200 and appeal.json()["state"] == "appeal"
    headers = login(client, "expert3")
    result = client.post(
        "/api/v1/tasks/" + task["id"] + "/arbitrate",
        headers=headers,
        json=cmd(appeal.json()["version"], {"verdict": "not_a_problem"}),
    )
    assert result.status_code == 200 and result.json()["state"] == "closed_false_positive"
    after = client.get("/api/v1/cases/C008").json()
    assert not after["signatures"] and len(after["documents"]) == len(detail["documents"])


def test_graph_semantic_layers_export_authorization_and_candidate_flow(client, monkeypatch):
    headers = login(client, "qc1")
    ontology = client.get("/api/v1/knowledge-graphs/views").json()
    assert ontology["loaded_counts"]["nodes"] == 28 and all(
        v["semantic_kind"] == "class" for v in ontology["node_meta"].values()
    )
    graph = client.get("/api/v1/knowledge-graphs/views?view_kind=case&scope_ref=C001").json()
    assert any(m["semantic_kind"] == "assertion" for m in graph["node_meta"].values())
    ev = next(m["evidence_id"] for m in graph["node_meta"].values() if m.get("evidence_id"))
    assert client.get("/api/v1/evidence/" + ev).status_code == 200
    denied = client.post(
        "/api/v1/knowledge-graphs/export-authorizations",
        headers=headers,
        json={
            "kind": "native_rdf",
            "view_kind": "case",
            "scope_ref": "C001",
            "projection_digest": graph["projection_digest"],
        },
    )
    assert denied.status_code == 422
    permit = client.post(
        "/api/v1/knowledge-graphs/export-authorizations",
        headers=headers,
        json={
            "kind": "png",
            "view_kind": "case",
            "scope_ref": "C001",
            "projection_digest": graph["projection_digest"],
        },
    )
    assert permit.status_code == 200, permit.text
    created = client.post(
        "/api/v1/knowledge-graphs/drafts",
        headers=headers,
        json={"ontology": ontology["ontology"], "base_release_id": "semantic-v1"},
    )
    assert created.status_code == 200 and created.json()["status"] == "draft"
    draft = created.json()
    changed = dict(draft["ontology"])
    changed["description"] = "候選定義修改"
    update = client.patch(
        "/api/v1/knowledge-graphs/drafts/" + draft["id"], headers=headers, json=cmd(1, {"ontology": changed})
    )
    assert update.status_code == 200 and update.json()["version"] == 2
    stale = client.patch(
        "/api/v1/knowledge-graphs/drafts/" + draft["id"], headers=headers, json=cmd(1, {"ontology": changed})
    )
    assert stale.status_code == 409
    submitted = client.post(
        "/api/v1/knowledge-graphs/drafts/" + draft["id"] + "/submit", headers=headers, json=cmd(2)
    )
    assert submitted.status_code == 200 and submitted.json()["status"] == "in_review"
    assert (
        client.get("/api/v1/knowledge-graphs/views").json()["ontology"]["description"]
        != changed["description"]
    )
    login(client, "doctor1")
    assert client.get("/api/v1/knowledge-graphs/views?view_kind=case&scope_ref=C004").status_code == 404


def test_independent_judgments_and_arbitration_keep_originals(client, monkeypatch):
    headers, run_id, task, detail = create_processed(client, "C003", monkeypatch)
    with transaction() as db:
        from medical_quality.access import refresh_actor

        refresh_actor(db, "qc1")
        expert = db.get(Actor, "expert1")
        expert.case_ids = [cid for cid in expert.case_ids if cid != "C003"]
    login(client, "expert1")
    assert client.get("/api/v1/cases/C003").status_code == 404
    headers = login(client, "qc1")
    created = client.post(
        "/api/v1/evaluation-batches",
        headers=headers,
        json={
            "name": "獨立原判合同樣本",
            "run_ids": [run_id],
            "raters": ["expert1", "expert2"],
            "arbitrator": "expert3",
        },
    )
    assert created.status_code == 200, created.text
    batch = created.json()
    sample = batch["samples"][0]
    path = "/api/v1/evaluation-batches/" + batch["id"]
    headers = login(client, "expert1")
    assert client.get("/api/v1/cases/C003").status_code == 200
    unauthorized = client.post("/api/v1/evaluation-batches", headers=headers, json={"run_ids": [run_id]})
    assert unauthorized.status_code == 403
    protocol = client.post(
        path + "/protocol",
        headers=headers,
        json=cmd(
            batch["version"],
            {
                "thresholds": {
                    "min_end_to_end_recall": 0.9,
                    "max_false_positive_rate": 0.1,
                    "min_reference_coverage": 1,
                }
            },
        ),
    )
    assert protocol.status_code == 200 and protocol.json()["protocol"]["clinical_approved"] is False
    batch = protocol.json()
    fixed = client.get(path + "/samples/" + sample["id"])
    assert (
        fixed.status_code == 200 and fixed.json()["manifest"]["document_digest"] == sample["document_digest"]
    )
    first = client.post(
        path + "/judgments",
        headers=headers,
        json=cmd(
            batch["version"],
            {
                "sample_id": sample["id"],
                "verdict": "positive",
                "severity": "high",
                "rubric": {"support": "fail"},
            },
        ),
    )
    assert first.status_code == 200, first.text
    late = client.post(
        path + "/protocol",
        headers=headers,
        json=cmd(
            first.json()["version"],
            {
                "thresholds": {
                    "min_end_to_end_recall": 0,
                    "max_false_positive_rate": 1,
                    "min_reference_coverage": 0,
                }
            },
        ),
    )
    assert late.status_code == 409 and late.json()["error"]["code"] == "protocol_frozen"
    duplicate = client.post(
        path + "/judgments",
        headers=headers,
        json=cmd(first.json()["version"], {"sample_id": sample["id"], "verdict": "negative"}),
    )
    assert duplicate.status_code == 409
    headers = login(client, "expert2")
    blind = client.get(path + "/report").json()
    assert not blind["judgments"]
    second = client.post(
        path + "/judgments",
        headers=headers,
        json=cmd(
            first.json()["version"], {"sample_id": sample["id"], "verdict": "negative", "severity": "medium"}
        ),
    )
    assert second.status_code == 200, second.text
    headers = login(client, "expert3")
    before = client.get(path + "/report").json()
    assert before["agreement"]["observed"] == 0
    decision = client.post(
        path + "/arbitrations",
        headers=headers,
        json=cmd(
            second.json()["version"], {"sample_id": sample["id"], "verdict": "positive", "severity": "high"}
        ),
    )
    assert decision.status_code == 200, decision.text
    after = client.get(path + "/report").json()
    assert after["agreement"]["observed"] == 0
    assert len(after["judgments"]) == 2 and len(after["arbitrations"]) == 1
    assert (
        after["qualification"] == "engineering_only" and after["thresholds"]["min_end_to_end_recall"] == 0.9
    )
    assert after["rubrics"]["support"]["counts"]["fail"] == 1
    assert after["strata"]["data_kind"]["synthetic"]["total"] == len(batch["samples"])


def test_persistent_wait_survives_process_exit_and_rejects_changed_rule(client, monkeypatch):
    headers, _, task, _ = create_processed(client, "C012", monkeypatch)
    waiting = isolated_wait("wait", task["id"], task["version"])
    assert waiting["status"] == "waiting_for_human" and not waiting["business_completed"]
    saved = client.post("/api/v1/tasks/" + task["id"] + "/accept", headers=headers, json=cmd(task["version"]))
    assert saved.status_code == 200, saved.text
    decision_id = saved.json()["decision_id"]
    actor = actor_record("qc1")
    with transaction(actor) as db:
        current = db.get(Task, task["id"])
        rule_id = current.scope_manifest["rule_scope"][0]
        rule = db.get(Rule, rule_id)
        original = rule.status
        rule.status = "retired"
    try:
        with pytest.raises(HTTPException) as error:
            with transaction(actor) as db:
                resume_human(db, actor, task["id"], decision_id)
        assert error.value.detail["code"] == "rule_qualification_changed"
        with pytest.raises(HTTPException):
            with transaction(actor) as db:
                resume_human(db, actor, task["id"], "tool-approved-not-a-decision")
    finally:
        with transaction(actor) as db:
            db.get(Rule, rule_id).status = original
    assert isolated_wait("resume", task["id"], decision_id)["status"] == "resumed"
    assert isolated_wait("resume", task["id"], decision_id)["status"] == "already_resumed"
    after = client.get("/api/v1/cases/C012").json()
    assert next(t for t in after["tasks"] if t["id"] == task["id"])["state"] == "doctor"
    assert not after["signatures"]


def test_reassignment_deadline_and_escalation_keep_actual_responsibility(client, monkeypatch):
    headers, _, task, detail = create_processed(client, "C005", monkeypatch)
    doctor_id = "doctor_delegate"
    with transaction() as db:
        db.add(
            Actor(
                id=doctor_id,
                name="工程委派身份",
                role="doctor",
                groups=[detail["case"]["group_id"]],
                case_ids=[],
                enabled=True,
            )
        )
    assigned = client.post(
        "/api/v1/tasks/" + task["id"] + "/assign",
        headers=headers,
        json=cmd(task["version"], {"doctor_id": doctor_id}),
    )
    assert assigned.status_code == 200, assigned.text
    extended = client.post(
        "/api/v1/tasks/" + task["id"] + "/extend",
        headers=headers,
        json=cmd(assigned.json()["version"], {"deadline": (now() - timedelta(hours=1)).isoformat()}),
    )
    assert extended.status_code == 200
    accepted = client.post(
        "/api/v1/tasks/" + task["id"] + "/accept", headers=headers, json=cmd(extended.json()["version"])
    )
    assert accepted.status_code == 200
    headers = login(client, doctor_id)
    after = client.get("/api/v1/cases/C005").json()
    assert (
        after["case"]["owner_id"] == detail["case"]["owner_id"]
        and after["case"]["details"]["overdue_count"] >= 1
    )
    assert next(t for t in after["tasks"] if t["id"] == task["id"])["state"] == "doctor"
    appealed = client.post(
        "/api/v1/tasks/" + task["id"] + "/appeal",
        headers=headers,
        json=cmd(accepted.json()["version"], {"expert_id": "expert3"}),
    )
    assert appealed.status_code == 200
    headers = login(client, "expert3")
    escalated = client.post(
        "/api/v1/tasks/" + task["id"] + "/arbitrate",
        headers=headers,
        json=cmd(appealed.json()["version"], {"verdict": "escalate", "next_expert_id": "expert2"}),
    )
    assert escalated.status_code == 200 and escalated.json()["state"] == "disputed"
    wrong = client.post(
        "/api/v1/tasks/" + task["id"] + "/arbitrate",
        headers=headers,
        json=cmd(escalated.json()["version"], {"verdict": "not_a_problem"}),
    )
    assert wrong.status_code == 403
    headers = login(client, "expert2")
    returned = client.post(
        "/api/v1/tasks/" + task["id"] + "/arbitrate",
        headers=headers,
        json=cmd(escalated.json()["version"], {"verdict": "revision_required"}),
    )
    assert returned.status_code == 200 and returned.json()["state"] == "doctor"


def test_execution_rejects_unknown_graph_and_changed_semantics_before_model(client, monkeypatch):
    from medical_quality.models import SemanticRelease

    headers = login(client, "qc1")
    case = client.get("/api/v1/cases/C006").json()["case"]
    response = client.post("/api/v1/cases/C006/quality-runs", headers=headers, json=cmd(case["version"]))
    assert response.status_code == 202
    run_id = response.json()["id"]
    actor = actor_record("qc1")
    calls = []
    monkeypatch.setattr(quality, "local_model_candidates", lambda context: calls.append(context))
    with transaction(actor) as db:
        run = db.get(QualityRun, run_id)
        original = dict(run.manifest)
        run.manifest = {**original, "graph_version": "unknown-future"}
    with pytest.raises(HTTPException) as error:
        quality.compute_run(actor.id, run_id, 1)
    assert error.value.detail["code"] == "execution_version_incompatible" and calls == []
    with transaction(actor) as db:
        db.get(QualityRun, run_id).manifest = original
        release = db.get(SemanticRelease, original["semantic_release_id"])
        status = release.status
        release.status = "retired"
    try:
        with pytest.raises(HTTPException) as error:
            quality.compute_run(actor.id, run_id, 2)
        assert error.value.detail["code"] == "semantic_release_unavailable" and calls == []
    finally:
        with transaction(actor) as db:
            db.get(SemanticRelease, original["semantic_release_id"]).status = status
    with transaction(actor) as db:
        rule = db.get(Rule, original["rule_ids"][0])
        prior = rule.policy_version
        rule.policy_version += 1
    try:
        with pytest.raises(HTTPException) as error:
            quality.compute_run(actor.id, run_id, 3)
        assert error.value.detail["code"] == "rule_qualification_changed" and calls == []
    finally:
        with transaction(actor) as db:
            db.get(Rule, original["rule_ids"][0]).policy_version = prior
    assert client.get("/api/v1/cases/C006").status_code == 200

    def interrupt_model(context):
        raise RuntimeError("synthetic node interruption")

    monkeypatch.setattr(quality, "local_model_candidates", interrupt_model)
    with pytest.raises(RuntimeError):
        quality.compute_run(actor.id, run_id, 4)
    with transaction(actor) as db:
        assert db.get(QualityRun, run_id).results == []
    monkeypatch.setattr(
        quality, "local_model_candidates", lambda context: {"status": "candidate_only", "candidates": []}
    )
    recovered = quality.compute_run(actor.id, run_id, 5)
    with transaction(actor) as db:
        run = db.get(QualityRun, run_id)
        quality.execute_run(db, actor, run, 5, recovered)
        assert len(run.results) == 8 and run.manifest["document_digest"] == original["document_digest"]
