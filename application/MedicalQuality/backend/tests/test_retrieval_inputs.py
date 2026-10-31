import json
from uuid import uuid4


from medical_quality.access import refresh_actor
from medical_quality.config import settings
from medical_quality.db import transaction
from medical_quality.evidence import ingest_source
from medical_quality.models import Rule
from medical_quality.retrieval import reciprocal_rank_fusion, retrieve
from medical_quality.sources import register
from medical_quality.clinical_context.context import import_case


def test_same_source_text_and_identifier_do_not_merge_namespaces():
    paths = []
    ids = []
    try:
        for namespace in ["fixture_namespace_a", "fixture_namespace_b"]:
            path = settings().artifacts / "uploads" / ("namespace-" + uuid4().hex + ".jsonl")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    {"doc_id": "same-id", "text": "合成工程原文：過敏史未核查。", "title": "來源敘述"},
                    ensure_ascii=False,
                )
                + "\n"
            )
            paths.append(path)
            with transaction() as db:
                actor = refresh_actor(db, "qc1")
                s = register(
                    db,
                    actor,
                    upload={
                        "name": "同標識不同來源",
                        "reference": "upload:" + path.name,
                        "namespace": namespace,
                        "role": "business_evidence",
                        "kind": "synthetic",
                        "license": "自建工程測試",
                    },
                )
                result = ingest_source(db, actor, s["id"], 1, "namespace-" + uuid4().hex, {"limit": 1})
                case = import_case(db, actor, result["evidence_ids"][0], "doctor1")
                ids.append(case["id"])
                assert case["identity"] == "unlinked" and case["scope_confirmed"] is False
        assert ids[0] != ids[1]
    finally:
        for p in paths:
            p.unlink(missing_ok=True)


def test_rrf_preserves_native_ranks_and_exact_rule_version():
    scores = reciprocal_rank_fusion([["a", "b"], ["b", "c"]])
    assert scores["b"] == 1 / 62 + 1 / 61 and scores["a"] == 1 / 61
    with transaction() as db:
        actor = refresh_actor(db, "qc1")
        exact = retrieve(db, actor, "MQC-DOC-005", "semantic-v1", rule_id="MQC-DOC-005-v1")
        assert exact["mode"] == "exact_id" and len(exact["results"]) == 1
        assert exact["results"][0]["rule"]["id"] == "MQC-DOC-005-v1"
        assert exact["results"][0]["evidence_ids"] == ["rule-evidence-5"]
        result = retrieve(db, actor, "zxq9876unknownlookup", "semantic-v1")
        assert result["mode"] == "lexical_only" and result["results"] == []
        dense = retrieve(db, actor, "過敏", "semantic-v1", require_dense=True)
        assert dense["mode"] == "blocked" and dense["results"] == []


def test_retired_rule_filtered_before_retrieval_and_historical_id_preserved():
    with transaction() as db:
        actor = refresh_actor(db, "qc1")
        rule = db.get(Rule, "MQC-DOC-004-v1")
        original = (rule.version, rule.content)
        rule.status = "retired"
        db.flush()
        result = retrieve(db, actor, "MQC-DOC-004", "semantic-v1", rule_id=rule.id)
        assert result["results"] == [] and result["gaps"] == ["rule_version_not_eligible"]
        assert (rule.version, rule.content) == original
        rule.status = "candidate"


def test_ontology_query_expansion_keeps_origin_and_version():
    from medical_quality.models import SemanticRelease
    from medical_quality.retrieval import semantic_expansion

    with transaction() as db:
        release = db.get(SemanticRelease, "semantic-v1")
        expansion = semantic_expansion("查看臨床斷言", release)
        assert expansion["original_query"] == "查看臨床斷言"
        assert "ClinicalAssertion" in expansion["terms"]
        assert expansion["paths"][0]["release_id"] == "semantic-v1"
        assert expansion["used_for"] == "retrieval_only_not_patient_facts"


def test_model_endpoint_and_fabricated_evidence_cannot_escape_scope(monkeypatch):
    from dataclasses import replace
    import medical_quality.quality as quality
    import httpx

    original = quality.settings()
    monkeypatch.setattr(
        quality, "settings", lambda: replace(original, model_url="https://unapproved.invalid")
    )
    sent = []
    monkeypatch.setattr(quality.httpx, "post", lambda *a, **k: sent.append((a, k)))
    assert (
        quality.local_model_candidates({"evidence": []})["reason"] == "model_endpoint_outside_domain"
        and sent == []
    )
    monkeypatch.setattr(quality, "settings", lambda: original)
    response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "candidates": [
                                {
                                    "rule_key": "MQC-DOC-005",
                                    "reason": "文書差異",
                                    "evidence_ids": ["not-input", "also-not-input"],
                                    "quotes": ["fake", "fake"],
                                }
                            ]
                        }
                    )
                }
            }
        ]
    }

    def post(*args, **kwargs):
        assert kwargs["trust_env"] is False
        return httpx.Response(200, json=response, request=httpx.Request("POST", args[0]))

    monkeypatch.setattr(quality.httpx, "post", post)
    result = quality.local_model_candidates(
        {"evidence": [{"id": "one", "envelope": {"content": {"text": "原始輸入"}}}]}
    )
    assert (
        result["candidates"] == [] and result["rejected_unsupported"] == 1 and result["status"] == "partial"
    )
