from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select, update, func
from fastapi import HTTPException

from medical_quality.db import transaction
from medical_quality.access import refresh_actor
from medical_quality.models import Evidence, Job, now
from medical_quality import worker
from conftest import login, cmd


def test_stale_worker_cannot_publish_parse_results():
    with transaction() as db:
        db.execute(update(Job).values(status="cancelled"))
        actor = refresh_actor(db, "qc1")
        count_before = db.scalar(
            select(func.count()).select_from(Evidence).where(Evidence.source_id == "rule-candidates-v1")
        )
        job = Job(
            id=uuid4().hex,
            actor_id=actor.id,
            kind="parse",
            payload={"source_id": "rule-candidates-v1", "version": 1, "scope": {"limit": 1}},
        )
        db.add(job)
        job_id = job.id
    first = worker.claim()
    assert first["id"] == job_id
    with transaction() as db:
        db.get(Job, job_id).lease_until = now() - timedelta(seconds=2)
    second = worker.claim()
    assert second["token"] > first["token"]
    worker.process(first)
    with transaction() as db:
        actor = refresh_actor(db, "qc1")
        job = db.get(Job, job_id)
        assert job.fencing_token == second["token"] and job.status == "running"
        assert (
            db.scalar(
                select(func.count()).select_from(Evidence).where(Evidence.source_id == "rule-candidates-v1")
            )
            == count_before
        )
    worker.process(second)
    with transaction() as db:
        actor = refresh_actor(db, "qc1")
        job = db.get(Job, job_id)
        assert job.status == "completed" and job.result["status"] == "partial"
        assert (
            db.scalar(
                select(func.count()).select_from(Evidence).where(Evidence.source_id == "rule-candidates-v1")
            )
            == count_before + 1
        )


def test_source_snapshot_change_and_denied_reference_material(tmp_path):
    from medical_quality.sources import register, source_for_read
    from medical_quality.config import settings

    path = settings().artifacts / "uploads" / ("test-" + uuid4().hex + ".json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"id":"001"}')
    try:
        with transaction() as db:
            actor = refresh_actor(db, "info1")
            entry = {
                "name": "版本測試",
                "reference": "upload:" + path.name,
                "namespace": "version_test",
                "role": "business_evidence",
                "kind": "synthetic",
                "license": "自建測試",
            }
            one = register(db, actor, upload=entry)
            two = register(db, actor, upload=entry)
            assert one["id"] == two["id"] and one["version"] == two["version"] == 1
        path.write_text('{"id":"002"}')
        with transaction() as db:
            actor = refresh_actor(db, "info1")
            with pytest.raises(HTTPException):
                source_for_read(db, actor, one["id"], 1)
            new = register(db, actor, upload=entry)
            assert new["id"] == one["id"] and new["version"] == 2
        with transaction() as db:
            actor = refresh_actor(db, "info1")
            with pytest.raises(HTTPException):
                register(db, actor, upload={**entry, "role": "reference_label"})
    finally:
        path.unlink(missing_ok=True)


def test_revocation_rejects_old_sessions_and_restore_is_bounded(client):
    from fastapi.testclient import TestClient
    from medical_quality.app import app

    second = TestClient(app)
    try:
        login(second, "qc2")
        headers = login(client, "info1")
        actors = client.get("/api/v1/access/actors").json()["items"]
        target = next(a for a in actors if a["id"] == "qc2")
        revoked = client.post(
            "/api/v1/access/actors/qc2/revoke", headers=headers, json=cmd(target["version"])
        )
        assert revoked.status_code == 200
        assert second.get("/api/v1/cases").status_code == 401
        assert second.get("/api/v1/knowledge-graphs/views").status_code == 401
        restored = client.post(
            "/api/v1/access/actors/qc2/restore",
            headers=headers,
            json=cmd(revoked.json()["version"], {"expires_at": (now() + timedelta(hours=2)).isoformat()}),
        )
        assert restored.status_code == 200 and restored.json()["enabled"]
        assert second.get("/api/v1/session").status_code == 401
        login(second, "qc2")
        assert second.get("/api/v1/cases").status_code == 200
    finally:
        second.close()


def test_http_failure_does_not_emit_success_or_sensitive_details(client, monkeypatch):
    import medical_quality.app as module

    headers = login(client, "qc1")
    before = client.get("/api/v1/cases/C002").json()["case"]["version"]

    def failure(*args, **kwargs):
        raise RuntimeError("sensitive-patient-content-must-not-be-returned")

    monkeypatch.setattr(module, "create_run", failure)
    response = client.post("/api/v1/cases/C002/quality-runs", headers=headers, json=cmd(before))
    assert response.status_code == 500 and "sensitive-patient-content" not in response.text
    assert client.get("/api/v1/cases/C002").json()["case"]["version"] == before


def test_graph_rejects_instance_candidate_and_malformed_native_shapes(client):
    headers = login(client, "qc1")
    graph = client.get("/api/v1/knowledge-graphs/views?view_kind=case&scope_ref=C001").json()
    response = client.post(
        "/api/v1/knowledge-graphs/drafts",
        headers=headers,
        json={"ontology": graph["ontology"], "metadata_map": {"node_meta": graph["node_meta"]}},
    )
    assert response.status_code == 422 and response.json()["error"]["code"] == "instance_not_definition"
    bad = '{"ontology":{"entityTypes":[{"id":"x","name":"X","description":"D","properties":"bad"}],"relationships":[]}}'
    response = client.post(
        "/api/v1/knowledge-graphs/import", headers=headers, json={"format": "json", "content": bad}
    )
    assert response.status_code == 422


def test_parse_request_retry_reuses_committed_unit_and_new_scope_preserves_it(client):
    from medical_quality.models import Source

    headers = login(client, "qc1")
    with transaction() as db:
        db.execute(update(Job).values(status="cancelled"))
        refresh_actor(db, "qc1")
        source = db.get(Source, "rule-candidates-v1")
        version = source.version
    payload = cmd(version, {"limit": 1})
    first = client.post(
        "/api/v1/source-versions/rule-candidates-v1/parse-runs", headers=headers, json=payload
    )
    assert first.status_code == 202
    first_id = first.json()["id"]
    claimed = worker.claim()
    assert claimed["id"] == first_id
    worker.process(claimed)
    repeated = client.post(
        "/api/v1/source-versions/rule-candidates-v1/parse-runs", headers=headers, json=payload
    )
    assert repeated.json()["id"] == first_id
    with transaction() as db:
        refresh_actor(db, "qc1")
        first_result = dict(db.get(Job, first_id).result)
        assert first_result["evidence_ids"]
    second = client.post(
        "/api/v1/source-versions/rule-candidates-v1/parse-runs",
        headers=headers,
        json=cmd(version, {"limit": 2}),
    )
    assert second.status_code == 202 and second.json()["id"] != first_id
    claimed = worker.claim()
    assert claimed["id"] == second.json()["id"]
    worker.process(claimed)
    with transaction() as db:
        refresh_actor(db, "qc1")
        assert db.get(Job, first_id).result == first_result
        assert all(db.get(Evidence, eid) for eid in first_result["evidence_ids"])
        assert len(db.get(Job, second.json()["id"]).result["evidence_ids"]) == 2
    current = client.get("/api/v1/sources/rule-candidates-v1/evidence").json()
    assert current["total"] == 2 and current["parse_run_id"] == second.json()["id"]
    history = client.get(
        "/api/v1/sources/rule-candidates-v1/evidence", params={"parse_run_id": first_id}
    ).json()
    assert history["total"] == 1 and history["items"][0]["id"] == first_result["evidence_ids"][0]
