"""只驗證服務器階段執行合同；專業准入前置使用顯式替身，不代表真實批准。"""

from dataclasses import replace
import pytest
from fastapi import HTTPException
from medical_quality import access, release
from medical_quality.db import transaction
from medical_quality.models import Actor, Case, ReleaseRequest, GateDecision
from medical_quality.config import settings


def test_stages_scope_qualification_expiry_and_roles_are_rechecked(monkeypatch):
    original = settings()
    monkeypatch.setattr(access, "settings", lambda: replace(original, mode="production"))
    monkeypatch.setattr(
        release,
        "deployment_policy",
        lambda: {
            k: {"approved_by": "synthetic-authority", "evidence_ref": "synthetic-policy"}
            for k in ["identity", "data_domain", "retention"]
        },
    )
    eligible = {"value": True}
    monkeypatch.setattr(
        release, "conditions", lambda *a: [{"status": "met" if eligible["value"] else "unmet"}]
    )
    with transaction() as db:
        access.refresh_actor(db, "qc1")
        case = db.get(Case, "C001")
        actor = Actor(
            id="synthetic-oidc-qc",
            role="qc",
            enabled=True,
            groups=[case.group_id],
            case_ids=[],
            oidc_subject="synthetic-subject",
            expires_at=None,
        )
        baseline = {
            "semantic_release_id": "semantic-v1",
            "rule_ids": ["synthetic-rule"],
            "model": {"sha256": "synthetic-model-digest"},
        }
        request = ReleaseRequest(
            id="stage-fixture",
            stage="shadow",
            status="approved",
            baseline=baseline,
            scope={"department": case.department},
            conditions=[],
            acceptances=[],
        )
        db.add(request)
        db.flush()
        db.add(
            GateDecision(
                request_id=request.id,
                actor_id="manager1",
                outcome="approve",
                reason="工程階段能力夾具；不是專業批准",
                evidence={"baseline": baseline},
            )
        )
        db.flush()
        shadow = release.runtime_capability(db, actor, case, baseline, "production")
        assert shadow["stage"] == "shadow" and shadow["request_id"] == request.id
        request.stage = "assisted"
        db.flush()
        assert release.runtime_capability(db, actor, case, baseline, "production")["stage"] == "assisted"
        for changed in [
            {**baseline, "rule_ids": ["wrong-rule"]},
            {**baseline, "model": {"sha256": "changed"}},
        ]:
            with pytest.raises(HTTPException) as error:
                release.runtime_capability(db, actor, case, changed, "production")
            assert error.value.status_code == 403
        eligible["value"] = False
        with pytest.raises(HTTPException):
            release.runtime_capability(db, actor, case, baseline, "production")
        eligible["value"] = True
        request.status = "stopped"
        db.flush()
        with pytest.raises(HTTPException):
            release.runtime_capability(db, actor, case, baseline, "production")
        request.status = "approved"
        db.flush()
        actor.role = "support"
        with pytest.raises(HTTPException) as error:
            release.runtime_capability(db, actor, case, baseline, "production")
        assert error.value.detail["code"] == "action_denied"
        assert db.get(ReleaseRequest, request.id).baseline == baseline
