from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from .common import audit, fail
from .config import settings
from .db import set_actor, transaction
from .models import Actor, Case, LoginSession, now

ROLE_NAMES = {
    "qc": "質控人員",
    "doctor": "責任醫生",
    "expert": "複核專家",
    "info": "信息科",
    "manager": "管理部門",
    "support": "供應商支持",
}
PERMISSIONS = {
    "qc": {
        "cases",
        "run",
        "review",
        "verify",
        "assign",
        "sign_qc",
        "knowledge",
        "graph",
        "export_graph",
        "sources",
        "audit",
        "evaluation",
        "knowledge_edit",
        "draft",
    },
    "doctor": {"cases", "revise", "appeal", "sign_doctor", "knowledge", "graph", "export_graph"},
    "expert": {
        "cases",
        "arbitrate",
        "evaluation",
        "judge",
        "knowledge",
        "knowledge_edit",
        "graph",
        "draft",
        "export_graph",
    },
    "info": {
        "sources",
        "source_register",
        "parse",
        "source_schema",
        "knowledge",
        "graph",
        "draft",
        "knowledge_edit",
        "audit",
        "manage_access",
        "operations",
        "export_assets",
        "export_graph",
    },
    "manager": {"release", "evaluation_report", "knowledge", "graph", "audit", "export_assets"},
    "support": {"operations"},
}


def token_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def require(actor: Actor, action: str, case: Case | None = None, purpose: str = "engineering"):
    if not actor.enabled or (actor.expires_at and actor.expires_at <= now()):
        fail("authorization_expired", "當前授權已失效。", 403)
    if purpose not in {"engineering", "research", "production"}:
        fail("purpose_invalid", "未登記的使用目的。", 403)
    if purpose == "production":
        from .release import deployment_policy

        policy = deployment_policy()
        if (
            settings().mode != "production"
            or not actor.oidc_subject
            or any(
                not policy.get(key, {}).get("approved_by") or not policy.get(key, {}).get("evidence_ref")
                for key in ["identity", "data_domain", "retention"]
            )
        ):
            fail("production_not_authorized", "尚無目標醫院的真實身份、數據域、留存及責任授權。", 403)
    if action not in PERMISSIONS.get(actor.role, set()):
        fail("action_denied", "當前崗位沒有此操作權限。", 403)
    if case is not None:
        allowed = (
            (actor.role == "qc" and case.group_id in actor.groups)
            or (actor.role == "doctor" and case.owner_id == actor.id)
            or case.id in actor.case_ids
        )
        if not allowed:
            fail("not_found", "對象不存在或當前不可訪問。", 404)


def get_case(db: Session, actor: Actor, case_id: str, *, lock=False, action="cases") -> Case:
    statement = select(Case).where(Case.id == case_id)
    if lock:
        statement = statement.with_for_update()
    case = db.scalar(statement)
    if not case:
        fail("not_found", "對象不存在或當前不可訪問。", 404)
    require(actor, action, case)
    if case.data_kind == "production":
        require(actor, action, case, purpose="production")
    return case


def authenticate(request: Request) -> Actor:
    raw = request.cookies.get("mq_session", "")
    if not raw:
        fail("authentication_required", "請先登錄。", 401)
    with transaction() as db:
        session = db.get(LoginSession, token_hash(raw))
        actor = db.get(Actor, session.actor_id) if session else None
        if (
            not session
            or session.expires_at <= now()
            or not actor
            or not actor.enabled
            or (actor.auth_version != session.auth_version)
            or (actor.expires_at and actor.expires_at <= now())
        ):
            fail("session_expired", "會話或授權已過期，請重新登錄。", 401)
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            csrf = request.headers.get("x-csrf-token", "")
            if not secrets.compare_digest(token_hash(csrf), session.csrf_hash):
                fail("csrf_invalid", "操作校驗失效，請刷新頁面。", 403)
            origin = request.headers.get("origin")
            if origin and origin != f"{request.url.scheme}://{request.url.netloc}":
                fail("origin_denied", "不接受跨站操作。", 403)
        db.expunge(actor)
        return actor


def issue_session(db: Session, actor: Actor):
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    db.add(
        LoginSession(
            token_hash=token_hash(token),
            csrf_hash=token_hash(csrf),
            actor_id=actor.id,
            auth_version=actor.auth_version,
            expires_at=now() + timedelta(hours=12),
        )
    )
    audit(db, actor, "session.login", actor.id, details={"identity_mode": settings().mode})
    return token, csrf


def refresh_actor(db: Session, actor_id: str) -> Actor:
    actor = db.get(Actor, actor_id, populate_existing=True)
    if not actor or not actor.enabled or (actor.expires_at and actor.expires_at <= now()):
        fail("authorization_expired", "作業主體的當前授權已失效。", 403)
    set_actor(db, actor)
    return actor
