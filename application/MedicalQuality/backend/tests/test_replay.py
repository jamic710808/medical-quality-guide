import copy

from sqlalchemy import select
from conftest import login
from medical_quality.db import transaction
from medical_quality.access import refresh_actor
from medical_quality.models import Evidence


def test_wrong_offset_and_incompatible_contract_are_rejected(client):
    login(client, "qc1")
    with transaction() as db:
        refresh_actor(db, "qc1")
        evidence = db.scalar(select(Evidence).where(Evidence.case_id == "C006").limit(1))
        original = copy.deepcopy(evidence.envelope)
        identity = evidence.id
    good = client.get("/api/v1/evidence/" + identity)
    assert good.status_code == 200 and good.json()["replay"]["status"] == "verified"
    try:
        with transaction() as db:
            refresh_actor(db, "qc1")
            evidence = db.get(Evidence, identity)
            bad = copy.deepcopy(original)
            bad["locator"]["char_start"] += 1
            evidence.envelope = bad
        response = client.get("/api/v1/evidence/" + identity)
        assert response.status_code == 409 and response.json()["error"]["code"] == "evidence_locator_mismatch"
        with transaction() as db:
            refresh_actor(db, "qc1")
            bad = copy.deepcopy(original)
            bad["schema_version"] = "2.0"
            db.get(Evidence, identity).envelope = bad
        response = client.get("/api/v1/evidence/" + identity)
        assert (
            response.status_code == 409
            and response.json()["error"]["code"] == "evidence_contract_incompatible"
        )
    finally:
        with transaction() as db:
            refresh_actor(db, "qc1")
            db.get(Evidence, identity).envelope = original
