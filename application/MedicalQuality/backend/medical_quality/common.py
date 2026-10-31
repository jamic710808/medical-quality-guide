from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Callable

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from .models import Actor, Audit, Operation, Outbox, uid


def digest(value: Any) -> str:
    raw = (
        value
        if isinstance(value, bytes)
        else json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
        ).encode()
    )
    return hashlib.sha256(raw).hexdigest()


def public(record, exclude: tuple[str, ...] = ()) -> dict:
    if record is None:
        return {}
    out = {}
    for column in inspect(record).mapper.column_attrs:
        if column.key in exclude:
            continue
        value = getattr(record, column.key)
        if isinstance(value, datetime):
            value = value.isoformat()
        out[column.key] = value
    return out


class Command(BaseModel):
    expected_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=100)
    reason: str = Field(min_length=1, max_length=2000)
    payload: dict = Field(default_factory=dict)
    purpose: str = "engineering"


def fail(code: str, message: str, status: int = 409, **details):
    raise HTTPException(status, {"code": code, "message": message, **details})


def audit(
    db: Session,
    actor: Actor,
    action: str,
    resource_id: str,
    *,
    case_id=None,
    outcome="success",
    purpose="engineering",
    reason="",
    before=None,
    after=None,
    operation_id=None,
    details=None,
) -> Audit:
    item = Audit(
        id=uid(),
        actor_id=actor.id,
        role=actor.role,
        action=action,
        resource_id=resource_id,
        case_id=case_id,
        outcome=outcome,
        purpose=purpose,
        reason=reason[:2000],
        before_version=before,
        after_version=after,
        operation_id=operation_id or db.info.get("operation_id"),
        details={
            **(details or {}),
            **({"request_id": db.info["request_id"]} if db.info.get("request_id") else {}),
        },
    )
    db.add(item)
    db.flush()  # Failure must roll back the same business transaction.
    return item


def command(
    db: Session, actor: Actor, action: str, target: str, cmd: Command, perform: Callable[[], dict]
) -> dict:
    fingerprint = digest(cmd.model_dump(exclude={"idempotency_key"}))
    lock_key = int(digest([actor.id, action, target, cmd.idempotency_key])[:15], 16)
    db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock_key})
    old = db.scalar(
        select(Operation).where(
            Operation.actor_id == actor.id,
            Operation.action == action,
            Operation.target_id == target,
            Operation.operation_key == cmd.idempotency_key,
        )
    )
    if old:
        if old.request_digest != fingerprint:
            fail("idempotency_conflict", "同一操作編號對應不同內容，請核對後重新提交。")
        return old.result
    operation_id = uid()
    previous = db.info.get("operation_id")
    db.info["operation_id"] = operation_id
    try:
        result = perform()
    finally:
        if previous:
            db.info["operation_id"] = previous
        else:
            db.info.pop("operation_id", None)
    op = Operation(
        id=operation_id,
        actor_id=actor.id,
        action=action,
        target_id=target,
        operation_key=cmd.idempotency_key,
        request_digest=fingerprint,
        result=result,
    )
    db.add(op)
    db.add(
        Outbox(
            kind=action, aggregate_id=target, payload={"operation_id": op.id, "result_ref": result.get("id")}
        )
    )
    db.flush()
    return result


def check_version(record, expected: int):
    if record.version != expected:
        fail("version_conflict", "內容已被更新，請刷新並核對差異後提交。", current_version=record.version)
