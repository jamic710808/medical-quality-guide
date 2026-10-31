import pytest
from sqlalchemy import select, text
from fastapi import HTTPException

from medical_quality.access import require
from medical_quality.db import transaction
from medical_quality.models import Actor, Audit, Case
from medical_quality.common import command, Command, check_version
from conftest import login, cmd


def test_identity_session_csrf_and_forged_role(client):
    assert client.get("/api/v1/cases", headers={"X-Role": "qc"}).status_code == 401
    headers = login(client, "doctor1")
    cases = client.get("/api/v1/cases?page_size=50").json()["items"]
    assert cases and all(c["owner_id"] == "doctor1" for c in cases)
    assert client.get("/api/v1/cases/C004", headers={"X-Role": "qc"}).status_code == 404
    assert client.post("/api/v1/tasks/missing/accept", json=cmd()).status_code == 403
    assert (
        client.post(
            "/api/v1/auth/logout", headers={**headers, "Origin": "https://external.invalid"}, json={}
        ).status_code
        == 403
    )
    assert client.post("/api/v1/auth/logout", headers=headers, json={}).status_code == 200
    assert client.get("/api/v1/session").status_code == 401


@pytest.mark.parametrize("role", ["info1", "manager1", "support1"])
def test_nonclinical_roles_cannot_read_cases_or_graph(client, role):
    login(client, role)
    assert client.get("/api/v1/cases").status_code == 403
    assert client.get("/api/v1/cases/C001").status_code in {403, 404}
    assert client.get("/api/v1/knowledge-graphs/views?view_kind=case&scope_ref=C001").status_code in {
        403,
        404,
    }


def test_rls_runtime_role_and_transaction_scope_reset():
    with transaction() as db:
        row = db.execute(
            text("SELECT current_user,rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user")
        ).one()
        assert row[0] == "mq_app" and not row[1] and not row[2]
        assert db.scalars(select(Case)).all() == []
        actor = db.get(Actor, "doctor1")
        db.expunge(actor)
    with transaction(actor) as db:
        cases = db.scalars(select(Case)).all()
        assert cases and all(c.owner_id == "doctor1" for c in cases)
    with transaction() as db:
        assert db.scalars(select(Case)).all() == []


def test_atomic_audit_failure_rolls_back_business_state():
    with transaction() as db:
        actor = db.get(Actor, "qc1")
        db.expunge(actor)
    with transaction(actor) as db:
        before = db.get(Case, "C001").version
    with pytest.raises(Exception):
        with transaction(actor) as db:
            case = db.get(Case, "C001")
            case.version += 1
            db.add(
                Audit(
                    actor_id=None,
                    role="qc",
                    action="invalid",
                    resource_id="C001",
                    purpose="engineering",
                    outcome="success",
                    details={},
                )
            )
            db.flush()
    with transaction(actor) as db:
        assert db.get(Case, "C001").version == before


def test_idempotency_digest_and_version_conflict():
    with transaction() as db:
        actor = db.get(Actor, "qc1")
        db.expunge(actor)
    calls = []
    payload = Command(**cmd(key="same-command-key"))
    with transaction(actor) as db:

        def perform():
            calls.append(1)
            return {"id": "fixed-result"}

        one = command(db, actor, "test.idempotency", "C001", payload, perform)
        two = command(db, actor, "test.idempotency", "C001", payload, perform)
        assert one == two and len(calls) == 1
    with pytest.raises(HTTPException):
        with transaction(actor) as db:
            different = Command(**cmd(key="same-command-key", reason="另一請求內容"))
            command(db, actor, "test.idempotency", "C001", different, lambda: {})
    with transaction(actor) as db:
        with pytest.raises(HTTPException):
            check_version(db.get(Case, "C001"), 999)


def test_production_purpose_and_runtime_native_mutation_rejected():
    from medical_quality.native_semantic import call_tool

    with transaction() as db:
        actor = db.get(Actor, "qc1")
    with pytest.raises(HTTPException):
        require(actor, "run", purpose="production")
    with pytest.raises(PermissionError):
        call_tool("set_active_version", {"version": "ontology_v999"})
