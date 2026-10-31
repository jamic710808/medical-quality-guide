from __future__ import annotations

from datetime import datetime
from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command as Resume
from langgraph.checkpoint.postgres import PostgresSaver
from sqlalchemy import select
from sqlalchemy.orm import Session

from .access import get_case, require, refresh_actor
from .clinical_context.context import current_documents
from .common import Command, audit, check_version, command, digest, fail
from .config import settings
from .evidence import document_evidence
from .models import Actor, Case, Decision, Document, Finding, Job, Rule, Signature, Source, Task, now, uid
from .ontology import get_release
from .quality import create_run


def refresh_case_summary(db: Session, case: Case):
    tasks = db.scalars(select(Task).where(Task.case_id == case.id)).all()
    terminal = {"signed", "closed_false_positive", "superseded"}
    active = [t for t in tasks if t.state not in terminal]
    states = {t.state for t in active}
    priorities = [
        "disputed",
        "blocked",
        "verifying",
        "verification_pending",
        "verify_ready",
        "doctor",
        "appeal",
        "review",
        "sign",
    ]
    if active:
        case.status = next((s for s in priorities if s in states), active[0].state)
    elif tasks:
        case.status = "signed" if any(t.state == "signed" for t in tasks) else "closed_false_positive"
    else:
        case.status = "checked"
    risks = [db.get(Finding, t.finding_id).severity for t in active]
    case.risk = next((r for r in ["high", "medium", "low"] if r in risks), "unknown")
    case.details = {
        **case.details,
        "active_issue_count": len(active),
        "no_active_issue": bool(tasks and not active),
        "overdue_count": sum(t.deadline < now() for t in active),
    }


def current_semantic_scope(db: Session, task: Task):
    manifest = task.scope_manifest
    if manifest.get("graph_version") != "mq-sg-1" or manifest.get("schema_version") != "1.0":
        fail("execution_version_incompatible", "執行圖或狀態版本不兼容，需核對遷移後再恢復。")
    case = db.get(Case, task.case_id)
    if case.details.get("semantic_release_id") != manifest["semantic_release_id"]:
        fail("semantic_scope_stale", "病例使用的語義基線已經改變，必須再次核驗當前範圍。")
    release = get_release(db, manifest["semantic_release_id"], manifest["purpose"])
    if release.digest != manifest["semantic_digest"]:
        fail("semantic_scope_stale", "語義包摘要改變，不能將新內容套入舊責任範圍。")
    for rule_id in manifest.get("rule_scope", manifest["rule_ids"]):
        rule = db.get(Rule, rule_id)
        qualification = manifest["rule_qualification"].get(rule_id, {})
        if (
            not rule
            or rule.version != manifest["rule_versions"].get(rule_id)
            or {"policy_version": rule.policy_version, "status": rule.status, "purpose": rule.purpose}
            != qualification
            or rule.status not in {"candidate", "approved"}
        ):
            fail("rule_qualification_changed", "當前規則版本或資格已經改變，需重新核驗；歷史決定保留。")


def task_scope_current(db: Session, task: Task):
    current_semantic_scope(db, task)
    case = db.get(Case, task.case_id)
    current_rules = set(case.details.get("rule_ids", task.scope_manifest.get("rule_ids", [])))
    if (
        not set(task.scope_manifest.get("rule_scope", task.scope_manifest.get("rule_ids", [])))
        <= current_rules
    ):
        fail("rule_scope_stale", "當前規則基線已經改變，舊核驗範圍不能直接簽字。")
    current = {d.document_key: d.id for d in current_documents(db, task.case_id)}
    docs = db.scalars(select(Document).where(Document.id.in_(task.scope_manifest["document_ids"]))).all()
    if any(current.get(d.document_key) != d.id for d in docs) or len(docs) != len(
        task.scope_manifest["document_ids"]
    ):
        fail("signature_scope_stale", "文書已變化，必須再次核驗當前範圍。")


def act(db: Session, actor: Actor, task_id: str, action: str, cmd: Command):
    task = db.scalar(select(Task).where(Task.id == task_id).with_for_update())
    if not task:
        fail("not_found", "任務不存在或不可訪問。", 404)
    case = get_case(db, actor, task.case_id, lock=True)
    action_permission = {
        "accept": "review",
        "reject": "review",
        "revise": "revise",
        "appeal": "appeal",
        "arbitrate": "arbitrate",
        "recheck": "verify",
        "confirm": "verify",
        "return": "verify",
        "assign": "assign",
        "extend": "assign",
        "sign": "sign_doctor" if actor.role == "doctor" else "sign_qc",
        "reopen": "review",
    }.get(action)
    if not action_permission:
        fail("unknown_action", "未知任務動作。", 422)
    require(actor, action_permission, case, cmd.purpose)
    if action in {"revise", "appeal"} and actor.id != task.doctor_id:
        fail("responsibility_denied", "只有當前責任醫生可處理。", 403)
    if action in {"accept", "reject", "recheck", "confirm", "return"} and actor.id != task.reviewer_id:
        fail("responsibility_denied", "只有當前複核人可處理。", 403)
    if action == "arbitrate" and actor.id != task.expert_id:
        fail("assignment_required", "只有被指派專家可裁決。", 403)

    def perform():
        check_version(task, cmd.expected_version)
        before = task.state
        payload = cmd.payload
        extra = {}
        if action == "accept":
            if before != "review":
                fail("invalid_state", "只有待複核問題可確認。")
            finding = db.get(Finding, task.finding_id)
            if finding.details.get("blocking"):
                fail("evidence_blocked", "先補齊阻斷條件再確認問題。")
            severity = payload.get("severity", finding.severity)
            if severity not in {"high", "medium", "low"}:
                fail("severity_confirmation", "請確認問題的風險級別。", 422)
            finding.details = {
                **finding.details,
                "suggested_severity": finding.severity,
                "confirmed_severity": severity,
                "confirmed_by": actor.id,
            }
            finding.severity = severity
            task.state = "doctor"
            finding.status = "confirmed"
        elif action == "reject":
            if before not in {"review", "verify_ready"}:
                fail("invalid_state", "當前狀態不能駁回誤報。")
            task.state = "closed_false_positive"
            db.get(Finding, task.finding_id).status = "rejected"
        elif action == "revise":
            if before not in {"doctor", "blocked", "signed", "sign"}:
                fail("invalid_state", "當前狀態不接受整改文書。")
            old = db.get(Document, payload.get("document_id", ""))
            if not old or old.case_id != case.id:
                fail("document_scope", "文書不屬於當前病例。", 422)
            if old.id not in [d.id for d in current_documents(db, case.id)]:
                fail("document_stale", "請在當前文書版本上整改。")
            content = payload.get("content")
            if not isinstance(content, str) or not content.strip() or len(content) > 200000:
                fail("content_invalid", "請填寫有效整改內容。", 422)
            fields = {**old.fields, **payload.get("fields", {})}
            fields["author"] = actor.name
            new = Document(
                id=uid(),
                case_id=case.id,
                document_key=old.document_key,
                title=old.title,
                content=content,
                digest=digest(content),
                parent_id=old.id,
                version=old.version + 1,
                author_id=actor.id,
                source_id=old.source_id,
                fields=fields,
            )
            db.add(new)
            db.flush()
            source = db.get(Source, old.source_id)
            document_evidence(db, source, new)
            task.state = "verification_pending"
            task.details = {**task.details, "revision_id": new.id, "verification_confirmed": False}
            # Every directly affected scope loses current completion, while old signatures stay immutable.
            for other in db.scalars(select(Task).where(Task.case_id == case.id, Task.id != task.id)).all():
                if old.id in other.scope_manifest.get("document_ids", []) and other.state in {
                    "sign",
                    "signed",
                    "verify_ready",
                }:
                    other.state = "verification_pending"
                    other.version += 1
                    other.details = {
                        **other.details,
                        "verification_confirmed": False,
                        "version_invalidated_by": new.id,
                    }
            extra = {"document_id": new.id, "document_version": new.version}
        elif action == "appeal":
            if before != "doctor":
                fail("invalid_state", "當前狀態不能申訴。")
            expert_id = payload.get("expert_id", "expert1")
            expert = db.get(Actor, expert_id)
            if not expert or expert.role != "expert" or case.id not in expert.case_ids:
                fail("expert_scope", "需指派具有當前病例權限的專家。", 422)
            task.expert_id = expert.id
            task.state = "appeal"
        elif action == "arbitrate":
            if before not in {"appeal", "disputed"}:
                fail("invalid_state", "沒有待裁決的申訴。")
            verdict = payload.get("verdict")
            if verdict not in {"revision_required", "not_a_problem", "escalate"}:
                fail("verdict_invalid", "請選擇明確裁決出口。", 422)
            task.state = {
                "revision_required": "doctor",
                "not_a_problem": "closed_false_positive",
                "escalate": "disputed",
            }[verdict]
            if verdict == "escalate":
                expert = db.get(Actor, payload.get("next_expert_id", ""))
                if not expert or expert.role != "expert" or case.id not in expert.case_ids:
                    fail("next_owner_required", "升級需要明確有權的下一責任專家。", 422)
                task.expert_id = expert.id
        elif action == "recheck":
            if before not in {"verification_pending", "blocked", "doctor", "verify_ready"}:
                fail("invalid_state", "當前狀態不能重新核驗。")
            run = create_run(db, actor, case.id, cmd.purpose)
            run.manifest = {**run.manifest, "recheck_task_id": task.id}
            job = Job(
                id=uid(), actor_id=actor.id, case_id=case.id, kind="quality", payload={"run_id": run.id}
            )
            db.add(job)
            task.state = "verifying"
            task.details = {**task.details, "recheck_run_id": run.id, "verification_confirmed": False}
            extra = {"job_id": job.id, "run_id": run.id}
        elif action == "confirm":
            if before != "verify_ready" or not task.details.get("machine_recheck_passed"):
                fail("verification_required", "需要當前文書的再次核驗結果，再由複核人確認。")
            task_scope_current(db, task)
            task.state = "sign"
            task.details = {**task.details, "verification_confirmed": True}
        elif action == "return":
            if before not in {"verify_ready", "blocked", "verification_pending"}:
                fail("invalid_state", "當前狀態不能退回。")
            task.state = "doctor"
            task.details = {**task.details, "verification_confirmed": False}
        elif action in {"assign", "extend"}:
            if before in {"signed", "closed_false_positive"}:
                fail("closed_scope", "已結束範圍不可改派或延期。")
            if action == "assign":
                target = db.get(Actor, payload.get("doctor_id", ""))
                if not target or target.role != "doctor" or case.group_id not in target.groups:
                    fail("assignee_scope", "責任醫生不屬於當前責任組。", 422)
                if not target.enabled or (target.expires_at and target.expires_at <= now()):
                    fail("assignee_expired", "被指派人的授權已失效。", 422)
                previous_doctor = db.get(Actor, task.doctor_id)
                task.doctor_id = target.id
                if target.id != case.owner_id and case.id not in target.case_ids:
                    target.case_ids = [*target.case_ids, case.id]
                    target.version += 1
                    audit(
                        db,
                        actor,
                        "access.task_grant",
                        target.id,
                        case_id=case.id,
                        reason=cmd.reason,
                        after=target.version,
                    )
                if previous_doctor.id != case.owner_id and previous_doctor.id != target.id:
                    remaining = db.scalar(
                        select(Task.id)
                        .where(
                            Task.case_id == case.id,
                            Task.id != task.id,
                            Task.doctor_id == previous_doctor.id,
                            Task.state.not_in(["signed", "closed_false_positive", "superseded"]),
                        )
                        .limit(1)
                    )
                    if not remaining and case.id in previous_doctor.case_ids:
                        previous_doctor.case_ids = [cid for cid in previous_doctor.case_ids if cid != case.id]
                        previous_doctor.auth_version += 1
                        previous_doctor.version += 1
                        audit(
                            db,
                            actor,
                            "access.task_revoke",
                            previous_doctor.id,
                            case_id=case.id,
                            reason=cmd.reason,
                            after=previous_doctor.version,
                        )
                if payload.get("reviewer_id"):
                    reviewer = db.get(Actor, payload["reviewer_id"])
                    if not reviewer or reviewer.role != "qc" or case.group_id not in reviewer.groups:
                        fail("reviewer_scope", "複核人不在授權病區。", 422)
                    task.reviewer_id = reviewer.id
            else:
                try:
                    deadline = datetime.fromisoformat(payload["deadline"])
                except (ValueError, KeyError, TypeError):
                    fail("deadline_invalid", "請填寫帶時區的截止時間。", 422)
                if deadline.tzinfo is None:
                    fail("deadline_timezone", "截止時間必須包含時區。", 422)
                task.deadline = deadline
        elif action == "sign":
            if before not in {"sign", "signed"} or not task.details.get("verification_confirmed"):
                fail("signature_blocked", "尚未完成當前範圍的核驗與人工確認。")
            if actor.role == "doctor" and actor.id != task.doctor_id:
                fail("signature_actor", "不能替責任醫生簽字。", 403)
            if actor.role == "qc" and actor.id != task.reviewer_id:
                fail("signature_actor", "不能替複核人簽字。", 403)
            task_scope_current(db, task)
            scope_digest = digest(task.scope_manifest)
            existing = db.scalar(
                select(Signature).where(
                    Signature.task_id == task.id,
                    Signature.scope_digest == scope_digest,
                    Signature.role == actor.role,
                )
            )
            if not existing:
                db.add(
                    Signature(
                        case_id=case.id,
                        task_id=task.id,
                        actor_id=actor.id,
                        role=actor.role,
                        scope_digest=scope_digest,
                        manifest=task.scope_manifest,
                        mode="local_engineering" if settings().mode == "local" else "authenticated_record",
                    )
                )
                db.flush()
            roles = set(
                db.scalars(
                    select(Signature.role).where(
                        Signature.task_id == task.id, Signature.scope_digest == scope_digest
                    )
                ).all()
            )
            task.state = "signed" if roles == {"doctor", "qc"} else "sign"
        elif action == "reopen":
            if before not in {"signed", "closed_false_positive"}:
                fail("invalid_state", "只有已結束範圍可重新建立核驗鏈。")
            task.state = "verification_pending"
            task.details = {**task.details, "verification_confirmed": False, "reopened": True}
        task.version += 1
        case.version += 1
        decision = Decision(
            id=uid(),
            case_id=case.id,
            task_id=task.id,
            actor_id=actor.id,
            action=action,
            reason=cmd.reason,
            before_state=before,
            after_state=task.state,
            manifest={
                **task.scope_manifest,
                "task_version": task.version,
                "actor_snapshot": {"id": actor.id, "name": actor.name, "role": actor.role},
                "finding_id": task.finding_id,
                "before_task_version": cmd.expected_version,
            },
        )
        db.add(decision)
        db.flush()
        audit(
            db,
            actor,
            "task." + action,
            task.id,
            case_id=case.id,
            purpose=cmd.purpose,
            reason=cmd.reason,
            before=cmd.expected_version,
            after=task.version,
            details={"decision_id": decision.id, "before_state": before, "after_state": task.state},
        )
        db.add(
            Job(
                actor_id=actor.id,
                case_id=case.id,
                kind="human_resume",
                payload={"task_id": task.id, "decision_id": decision.id},
            )
        )
        if task.state not in {"signed", "closed_false_positive", "superseded", "verifying"}:
            db.add(
                Job(
                    actor_id=actor.id,
                    case_id=case.id,
                    kind="human_wait",
                    payload={"task_id": task.id, "task_version": task.version},
                )
            )
        refresh_case_summary(db, case)
        return {
            "id": task.id,
            "version": task.version,
            "state": task.state,
            "decision_id": decision.id,
            **extra,
        }

    return command(db, actor, "task." + action, task.id, cmd, perform)


class WaitState(TypedDict, total=False):
    task_id: str
    task_version: int
    decision_id: str
    accepted: bool


def wait_for_human(db: Session, actor: Actor, task_id: str, task_version: int):
    task = db.get(Task, task_id)
    if not task:
        fail("task_missing", "人工任務不可訪問。", 404)
    get_case(db, actor, task.case_id)
    if task.version != task_version:
        return {"status": "stale", "task_id": task.id}
    current_semantic_scope(db, task)

    def wait(state):
        decision_id = interrupt(
            {
                "task_id": state["task_id"],
                "task_version": state["task_version"],
                "required": "saved_decision_id",
            }
        )
        # A resumed execution must read a committed business decision, never accept arbitrary tool values.
        decision = db.get(Decision, str(decision_id))
        if (
            not decision
            or decision.task_id != task.id
            or decision.manifest.get("before_task_version") != state["task_version"]
        ):
            fail("saved_decision_required", "沒有匹配的已提交業務決定。", 403)
        return {"decision_id": decision.id, "accepted": True}

    builder = StateGraph(WaitState)
    builder.add_node("await_decision", wait)
    builder.add_edge(START, "await_decision")
    builder.add_edge("await_decision", END)
    config = {"configurable": {"thread_id": f"human:{task.id}:v{task_version}"}}
    with PostgresSaver.from_conn_string(settings().checkpoint_url) as saver:
        graph = builder.compile(checkpointer=saver)
        if not graph.get_state(config).values:
            graph.invoke({"task_id": task.id, "task_version": task_version}, config)
    return {
        "status": "waiting_for_human",
        "task_id": task.id,
        "task_version": task_version,
        "business_completed": False,
    }


def resume_human(db: Session, actor: Actor, task_id: str, decision_id: str):
    decision = db.get(Decision, decision_id)
    task = db.get(Task, task_id)
    if not task or not decision or decision.task_id != task.id or decision.actor_id != actor.id:
        fail("saved_decision_required", "恢復只能消費應用已保存且屬於當前主體的決定。", 403)
    get_case(db, actor, task.case_id)
    if decision.manifest["task_version"] != task.version:
        return {"status": "stale", "reason": "newer_business_decision", "decision_id": decision_id}
    current_semantic_scope(db, task)

    def wait(state):
        incoming = interrupt(
            {
                "task_id": state["task_id"],
                "task_version": state["task_version"],
                "required": "saved_decision_id",
            }
        )
        if incoming != decision.id:
            fail("invalid_resume", "恢復值不是已提交業務決定。", 403)
        refresh_actor(db, actor.id)
        current_semantic_scope(db, task)
        return {"decision_id": incoming, "accepted": True}

    graph = StateGraph(WaitState)
    graph.add_node("await_decision", wait)
    graph.add_edge(START, "await_decision")
    graph.add_edge("await_decision", END)
    before_version = decision.manifest.get("before_task_version", decision.manifest["task_version"] - 1)
    config = {"configurable": {"thread_id": f"human:{task.id}:v{before_version}"}}
    with PostgresSaver.from_conn_string(settings().checkpoint_url) as saver:
        runner = graph.compile(checkpointer=saver)
        snapshot = runner.get_state(config)
        if snapshot.values.get("accepted"):
            return {"status": "already_resumed", "decision_id": decision.id}
        if not snapshot.values:
            runner.invoke({"task_id": task.id, "task_version": before_version}, config)
        runner.invoke(Resume(resume=decision.id), config)
    return {"status": "resumed", "decision_id": decision.id, "meaning": "業務決定已先提交，圖只恢復執行"}
