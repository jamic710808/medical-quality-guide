import io
import copy
import json
import zipfile
import pytest
from fastapi import HTTPException

from medical_quality.evaluation import compute_metrics, compare_reports, rubric_metrics
from medical_quality.delivery import verify_export
from medical_quality.common import digest
from conftest import login, cmd


def test_denominators_abstentions_and_high_risk_veto():
    rows = [
        {"id": "tp", "reference": "positive", "prediction": "issue", "severity": "high"},
        {"id": "fn", "reference": "positive", "prediction": "pass", "severity": "high"},
        {"id": "up", "reference": "positive", "prediction": "unknown", "severity": "medium"},
        {"id": "fp", "reference": "negative", "prediction": "issue", "severity": "medium"},
        {"id": "tn", "reference": "negative", "prediction": "pass", "severity": "low"},
        {"id": "un", "reference": "negative", "prediction": "failed", "severity": "low"},
        {"id": "ur", "reference": None, "prediction": "issue", "severity": "high"},
    ]
    metrics = compute_metrics(rows)
    assert metrics["counts"] == {"TP": 1, "FP": 1, "FN": 1, "TN": 1, "U_pos": 1, "U_neg": 1, "U_ref": 1}
    assert metrics["end_to_end_recall"]["value"] == 1 / 3 and metrics["conditional_recall"]["value"] == 1 / 2
    assert (
        metrics["high_risk_false_negatives"] == ["fn"]
        and metrics["unresolved_high_risk"] == ["ur"]
        and metrics["veto"]
    )
    empty = compute_metrics([])
    assert empty["precision"]["value"] is None and empty["reference_coverage"]["denominator"] == 0
    # The frozen F008 acceptance example is an arithmetic fixture, not clinical performance.
    fixture = []
    for reference, prediction, count in [
        ("positive", "issue", 8),
        ("positive", "pass", 1),
        ("positive", "unknown", 1),
        ("negative", "issue", 2),
        ("negative", "pass", 7),
        ("negative", "unknown", 1),
    ]:
        fixture.extend(
            {
                "id": str(len(fixture) + i),
                "reference": reference,
                "prediction": prediction,
                "severity": "medium",
            }
            for i in range(count)
        )
    checked = compute_metrics(fixture)
    assert checked["end_to_end_recall"]["value"] == 8 / 10
    assert checked["conditional_recall"]["value"] == 8 / 9
    assert checked["precision"]["value"] == 8 / 10
    assert checked["decision_coverage"]["value"] == 18 / 20
    assert checked["abstention"]["value"] == 2 / 20


def test_paired_comparison_rejects_changed_scope_and_reference():
    sample = {
        "id": "s",
        "group": "g",
        "document_digest": "fixed",
        "rule_key": "MQC-DOC-005",
        "prediction": "pass",
        "reference": "positive",
        "severity": "high",
    }
    before = {
        "samples": [sample],
        "thresholds": {"min_end_to_end_recall": 0.9},
        "metrics": compute_metrics([sample]),
    }
    after = copy.deepcopy(before)
    after["samples"][0]["prediction"] = "issue"
    after["metrics"] = compute_metrics(after["samples"])
    compared = compare_reports(before, after)
    assert compared["pairs"][0]["changed"] and not compared["clinical_approval"]
    assert compared["left_metrics"]["high_risk_false_negatives"] == ["s"]
    for field, value in [("document_digest", "changed"), ("reference", "negative")]:
        altered = copy.deepcopy(after)
        altered["samples"][0][field] = value
        with pytest.raises(HTTPException):
            compare_reports(before, altered)


def test_rubric_denominators_keep_missing_and_unable_separate():
    result = rubric_metrics(
        [
            {"rubric": {"location": "pass", "support": "fail", "explanation": "unable"}},
            {"rubric": {"location": "fail", "support": "pass"}},
        ],
        4,
    )
    assert result["location"]["counts"] == {"pass": 1, "fail": 1, "unable": 0, "unreviewed": 2}
    assert result["location"]["value"] == 0.5 and result["location"]["denominator"] == 2
    assert result["explanation"]["counts"]["unable"] == 1 and result["explanation"]["value"] is None
    assert result["suggestion"]["counts"]["unreviewed"] == 4


def test_gate_cannot_approve_empty_or_engineering_conditions(client):
    headers = login(client, "manager1")
    rules = client.get("/api/v1/rules").json()["items"]
    request = client.post(
        "/api/v1/release-requests",
        headers=headers,
        json={
            "stage": "shadow",
            "baseline": {
                "batch_ids": [],
                "rule_ids": [r["id"] for r in rules],
                "semantic_release_id": "semantic-v1",
            },
        },
    )
    assert request.status_code == 200, request.text
    record = request.json()
    assert all(c["status"] == "unmet" for c in record["conditions"])
    decided = client.post(
        "/api/v1/release-requests/" + record["id"] + "/decisions",
        headers=headers,
        json=cmd(record["version"]),
    )
    assert decided.status_code == 200 and decided.json()["status"] == "blocked"
    stopped = client.post(
        "/api/v1/release-requests/" + record["id"] + "/stop",
        headers=headers,
        json=cmd(decided.json()["version"]),
    )
    assert stopped.status_code == 200 and stopped.json()["status"] == "stopped"


def test_export_preserves_unreleased_status_and_excludes_sensitive_data(client):
    headers = login(client, "manager1")
    rules = client.get("/api/v1/rules").json()["items"]
    request = client.post(
        "/api/v1/release-requests",
        headers=headers,
        json={
            "stage": "shadow",
            "baseline": {
                "batch_ids": [],
                "rule_ids": [r["id"] for r in rules],
                "semantic_release_id": "semantic-v1",
            },
        },
    ).json()
    exported = client.post("/api/v1/exports", headers=headers, json={"release_request_id": request["id"]})
    assert exported.status_code == 200, exported.text
    item = exported.json()
    repeat = client.post("/api/v1/exports", headers=headers, json={"release_request_id": request["id"]})
    assert (
        repeat.status_code == 200
        and repeat.json()["id"] == item["id"]
        and repeat.json()["digest"] == item["digest"]
    )
    response = client.get("/api/v1/exports/" + item["id"] + "/download")
    assert response.status_code == 200
    assert digest(response.content) == item["digest"]
    checked = verify_export(response.content)
    assert checked["status"] == "valid" and not checked["activated"]
    assert (
        checked["manifest"]["gate_status"] == "pending"
        and checked["manifest"]["clinical_qualification"] == "not_granted"
    )
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        names = archive.namelist()
        assert "licenses/Ontology-Playground-MIT.txt" in names
        assert not any("patient" in n or ".env" in n or "credential" in n for n in names)
        assert all(r["status"] == "candidate" for r in json.loads(archive.read("rules.json")))
        files = {n: archive.read(n) for n in names}
    # Even a self-consistent file list cannot omit a required dependency.
    incomplete = dict(files)
    incomplete.pop("ontology/shapes.ttl")
    manifest = json.loads(incomplete["manifest.json"])
    manifest["included"] = [entry for entry in manifest["included"] if entry["path"] != "ontology/shapes.ttl"]
    incomplete["manifest.json"] = json.dumps(manifest).encode()
    missing = io.BytesIO()
    with zipfile.ZipFile(missing, "w") as archive:
        for name, content in incomplete.items():
            archive.writestr(name, content)
    assert verify_export(missing.getvalue())["status"] == "invalid"
    files["rules.json"] = b"changed"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for n, content in files.items():
            archive.writestr(n, content)
    assert verify_export(buffer.getvalue())["status"] == "invalid"
    login(client, "doctor1")
    assert client.get("/api/v1/exports/" + item["id"] + "/download").status_code == 403
