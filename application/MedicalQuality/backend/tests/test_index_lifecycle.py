import numpy as np
import pytest
from fastapi import HTTPException
from sqlalchemy import select, func
from medical_quality import retrieval
from medical_quality.access import refresh_actor
from medical_quality.db import transaction
from medical_quality.models import KnowledgeIndex, KnowledgeChunk, Rule, Job, now
from datetime import timedelta


def test_index_publication_is_atomic_reusable_and_rejects_changed_inputs(monkeypatch):
    calls = []

    def vectors(texts):
        calls.append(len(texts))
        v = np.zeros((len(texts), 1024))
        v[:, 0] = 1
        return v

    monkeypatch.setattr(retrieval, "embed", vectors)
    first = retrieval.build_index("qc1")
    assert first["status"] == "ready" and first["dimensions"] == 1024
    again = retrieval.build_index("qc1")
    assert again["id"] == first["id"] and again["reused"] and len(calls) == 1
    with transaction() as db:
        refresh_actor(db, "qc1")
        count = db.scalar(select(func.count()).select_from(KnowledgeIndex))
        rule = db.get(Rule, "MQC-DOC-001-v1")
        rule.policy_version += 1
        old_ids = set(
            db.scalars(select(KnowledgeChunk.id).where(KnowledgeChunk.index_version == first["id"]))
        )
    original_audit = retrieval.audit

    def fail_audit(*args, **kwargs):
        raise RuntimeError("synthetic audit failure")

    monkeypatch.setattr(retrieval, "audit", fail_audit)
    with pytest.raises(RuntimeError):
        retrieval.build_index("qc1")
    with transaction() as db:
        refresh_actor(db, "qc1")
        assert db.scalar(select(func.count()).select_from(KnowledgeIndex)) == count
        assert (
            set(db.scalars(select(KnowledgeChunk.id).where(KnowledgeChunk.index_version == first["id"])))
            == old_ids
        )
    monkeypatch.setattr(retrieval, "audit", original_audit)

    def changed_during_embedding(texts):
        with transaction() as db:
            refresh_actor(db, "qc1")
            db.get(Rule, "MQC-DOC-001-v1").policy_version += 1
        return vectors(texts)

    monkeypatch.setattr(retrieval, "embed", changed_during_embedding)
    with pytest.raises(HTTPException) as error:
        retrieval.build_index("qc1")
    assert error.value.detail["code"] == "index_input_changed"
    monkeypatch.setattr(retrieval, "embed", vectors)
    with transaction() as db:
        actor = refresh_actor(db, "qc1")
        job = Job(
            actor_id=actor.id,
            kind="index",
            status="running",
            payload={},
            fencing_token=2,
            lease_until=now() + timedelta(minutes=1),
        )
        db.add(job)
        db.flush()
        job_id = job.id
    with pytest.raises(HTTPException) as error:
        retrieval.build_index("qc1", lease={"id": job_id, "token": 1})
    assert error.value.detail["code"] == "stale_worker"
    published = retrieval.build_index("qc1", lease={"id": job_id, "token": 2})
    assert published["id"] != first["id"] and published["status"] == "ready"
    with transaction() as db:
        actor = refresh_actor(db, "qc1")
        assert db.get(KnowledgeIndex, first["id"]).status == "ready"
        rule = db.get(Rule, "MQC-DOC-001-v1")
        rule.status = "retired"
        db.flush()
        result = retrieval.retrieve(
            db, actor, "MQC-DOC-001", "semantic-v1", index_id=first["id"], rule_id=rule.id
        )
        assert not result["results"]
        rule.status = "candidate"
        # These generations contain explicit vector substitutes; retire them after this fixture
        # so later lexical-only checks cannot accidentally consume synthetic dense vectors.
        db.get(KnowledgeIndex, first["id"]).status = "retired"
        db.get(KnowledgeIndex, published["id"]).status = "retired"
