from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from .access import require
from .common import Command, audit, check_version, command, digest, fail, public
from .config import PROJECT, settings
from .evaluation import report
from .models import Actor, GateDecision, ReleaseRequest, Rule, SemanticRelease, uid


def deployment_policy() -> dict:
    path = PROJECT / ".runtime/production-policy.json"
    return json.loads(path.read_text()) if path.exists() else {}


def conditions(db: Session, actor: Actor, baseline: dict, stage: str) -> list[dict]:
    checks = []

    def add(key, label, value, reason, evidence=None):
        checks.append(
            {
                "key": key,
                "label": label,
                "required": True,
                "status": "met" if value else "unmet",
                "reason": reason,
                "evidence": evidence or [],
            }
        )

    batches = baseline.get("batch_ids", [])
    reports = []
    for bid in batches:
        reports.append(report(db, actor, bid, gate=True))
    add(
        "evaluation",
        "固定樣本與專業評測",
        bool(reports)
        and all(r["status"] == "complete" and r["qualification"] == "professional_accepted" for r in reports),
        "工程身份、待責任接受與合成樣本不能證明專業驗收。",
        batches,
    )
    high_fn = [x for r in reports for x in r["metrics"]["high_risk_false_negatives"]]
    unresolved = [x for r in reports for x in r["metrics"]["unresolved_high_risk"]]
    add(
        "high_risk_veto",
        "高風險漏報與未決項",
        bool(reports) and not high_fn and not unresolved,
        "任一已確認高風險漏報或未決項否決晉級。",
        high_fn + unresolved,
    )
    add(
        "thresholds",
        "正式指標口徑與閾值",
        bool(reports) and all(r["thresholds"] for r in reports),
        "未凍結閾值不填默認分數。",
    )
    passed = []
    for r in reports:
        t = r["thresholds"] or {}
        m = r["metrics"]
        values = [
            m["end_to_end_recall"]["value"],
            m["false_positive_rate"]["value"],
            m["reference_coverage"]["value"],
        ]
        passed.append(
            all(v is not None for v in values)
            and values[0] >= t.get("min_end_to_end_recall", 2)
            and values[1] <= t.get("max_false_positive_rate", -1)
            and values[2] >= t.get("min_reference_coverage", 2)
        )
    add(
        "metric_results",
        "實際分項結果滿足凍結門檻",
        bool(passed) and all(passed),
        "分母為零、尚未評測或未達到門檻均不放行。",
    )
    frozen = baseline.get("evaluation_versions", {})
    add(
        "evaluation_version",
        "評測基線沒有漂移",
        bool(reports) and all(frozen.get(r["batch"]["id"]) == r["batch"]["version"] for r in reports),
        "判斷、仲裁或協議改變後必須建立新准入基線。",
    )
    model = baseline.get("model", {})
    add(
        "model_version",
        "模型與評測版本一致",
        bool(model.get("sha256"))
        and bool(reports)
        and all(
            manifest.get("model", {}).get("sha256") == model["sha256"]
            for r in reports
            for manifest in r["batch"]["manifest"]["runs"].values()
        ),
        "模型權重或配置變更不能沿用舊版本的評測准入。",
    )
    kinds = {s["data_kind"] for r in reports for s in r["samples"]}
    add(
        "production_sample",
        "目標業務資料與來源資格",
        kinds == {"production"},
        "公開/合成/文獻資料不是目標醫院生產驗收樣本。",
    )
    rules = db.scalars(select(Rule).where(Rule.id.in_(baseline.get("rule_ids", [])))).all()
    add(
        "rules",
        "規則專業審核",
        len(rules) == 8 and all(r.status == "approved" and r.purpose == "production" for r in rules),
        "一期八條規則必須具有適用範圍和專業批准。",
    )
    release = db.get(SemanticRelease, baseline.get("semantic_release_id", ""))
    add(
        "ontology",
        "本體與約束基線",
        bool(release and release.status == "approved" and release.purpose == "production"),
        "工程本體發佈不替代專業資格。",
    )
    policy = deployment_policy()
    for key, label in [
        ("identity", "醫院身份映射"),
        ("data_domain", "數據域與最小化"),
        ("retention", "留存與刪除條件"),
        ("workflow", "責任流程驗收"),
        ("graph", "原生圖譜 PG-006 驗收"),
        ("operations", "備份/回退與運行保障"),
    ]:
        evidence = policy.get(key, {})
        add(
            key,
            label,
            bool(
                evidence.get("approved_by")
                and evidence.get("evidence_ref")
                and evidence.get("baseline_digest") == digest(baseline)
            ),
            "須由目標環境的受控配置提供同基線責任證據；客戶端複選框不能批准。",
            [evidence.get("evidence_ref")] if evidence else [],
        )
    if stage == "assisted":
        add(
            "shadow",
            "限定影子運行證據",
            bool(policy.get("shadow", {}).get("accepted")),
            "輔助決策前需完成同範圍影子運行驗收。",
        )
    return checks


def create_request(db: Session, actor: Actor, payload: dict):
    require(actor, "release")
    stage = payload.get("stage", "shadow")
    if stage not in {"shadow", "assisted"}:
        fail("stage_invalid", "只接受影子運行或輔助決策申請。", 422)
    baseline = payload.get("baseline", {})
    from .models import EvaluationBatch

    versions = {}
    for bid in baseline.get("batch_ids", []):
        batch = db.get(EvaluationBatch, bid)
        if not batch:
            fail("batch_missing", "准入引用的評測批次不可用。", 422)
        versions[bid] = batch.version
    from .quality import model_manifest

    baseline = {
        **baseline,
        "application_version": "0.1.0",
        "graph_version": "mq-sg-1",
        "evaluation_versions": versions,
        "model": model_manifest(),
    }
    request = ReleaseRequest(
        id=uid(),
        stage=stage,
        status="pending",
        baseline=baseline,
        scope={"department": "內科一病區", "disease": "成人肺炎文書質控"},
        conditions=conditions(db, actor, baseline, stage),
        acceptances=[],
    )
    db.add(request)
    db.flush()
    audit(
        db,
        actor,
        "release.request",
        request.id,
        details={"stage": stage, "baseline_digest": digest(baseline)},
    )
    return public(request)


def decide(db: Session, actor: Actor, request_id: str, cmd: Command):
    require(actor, "release")
    request = db.scalar(select(ReleaseRequest).where(ReleaseRequest.id == request_id).with_for_update())
    if not request:
        fail("request_missing", "准入申請不可用。", 404)

    def perform():
        check_version(request, cmd.expected_version)
        current = conditions(db, actor, request.baseline, request.stage)
        accepts = request.acceptances
        roles = {
            a["role"]
            for a in accepts
            if a.get("identity_mode") != "local" and a.get("baseline_digest") == digest(request.baseline)
        }
        current.append(
            {
                "key": "responsibility_acceptance",
                "label": "關鍵崗位責任接受",
                "required": True,
                "status": "met" if {"qc", "doctor", "info", "manager"} <= roles else "unmet",
                "reason": "必要崗位分別綁定真實身份及當前基線。",
                "evidence": [],
            }
        )
        outcome = "approve" if all(c["status"] == "met" for c in current) else "reject"
        decision = GateDecision(
            id=uid(),
            request_id=request.id,
            actor_id=actor.id,
            outcome=outcome,
            reason=cmd.reason,
            evidence={"conditions": current, "baseline": request.baseline},
        )
        db.add(decision)
        request.conditions = current
        request.status = "approved" if outcome == "approve" else "blocked"
        request.version += 1
        db.flush()
        audit(
            db,
            actor,
            "release." + outcome,
            request.id,
            reason=cmd.reason,
            before=cmd.expected_version,
            after=request.version,
            details={"decision_id": decision.id},
        )
        return {
            "id": request.id,
            "version": request.version,
            "status": request.status,
            "decision_id": decision.id,
            "conditions": current,
        }

    return command(db, actor, "release.decide", request.id, cmd, perform)


def accept_responsibility(db: Session, actor: Actor, request_id: str, cmd: Command):
    if actor.role not in {"qc", "doctor", "info", "manager"}:
        fail("role_denied", "當前崗位不承擔此准入責任。", 403)
    request = db.scalar(select(ReleaseRequest).where(ReleaseRequest.id == request_id).with_for_update())
    if not request:
        fail("request_missing", "申請不可用。", 404)

    def perform():
        check_version(request, cmd.expected_version)
        record = {
            "actor_id": actor.id,
            "role": actor.role,
            "reason": cmd.reason,
            "identity_mode": settings().mode,
            "baseline_digest": digest(request.baseline),
        }
        if any(
            a["actor_id"] == actor.id and a["baseline_digest"] == record["baseline_digest"]
            for a in request.acceptances
        ):
            fail("already_accepted", "該主體已記錄本基線責任意見。")
        request.acceptances = [*request.acceptances, record]
        request.version += 1
        audit(
            db, actor, "release.accept_responsibility", request.id, reason=cmd.reason, after=request.version
        )
        return public(request)

    return command(db, actor, "release.accept", request.id, cmd, perform)


def stop_release(db: Session, actor: Actor, request_id: str, cmd: Command):
    require(actor, "release")
    request = db.scalar(select(ReleaseRequest).where(ReleaseRequest.id == request_id).with_for_update())
    if not request:
        fail("request_missing", "申請不可用。", 404)

    def perform():
        check_version(request, cmd.expected_version)
        request.status = "stopped"
        request.version += 1
        decision = GateDecision(
            id=uid(),
            request_id=request.id,
            actor_id=actor.id,
            outcome="stop",
            reason=cmd.reason,
            evidence={"baseline": request.baseline, "revalidation_required": True},
        )
        db.add(decision)
        audit(db, actor, "release.stop", request.id, reason=cmd.reason, after=request.version)
        return public(request)

    return command(db, actor, "release.stop", request.id, cmd, perform)


def runtime_capability(db: Session, actor: Actor, case, manifest: dict, purpose: str):
    if purpose != "production":
        if case.data_kind == "production" and purpose != "research":
            fail("production_purpose", "真實生產資料不能偽裝為工程夾具運行。", 403)
        if case.data_kind == "production" and not deployment_policy().get("authorized_research_scope"):
            fail("research_scope", "缺少目標醫院明確的離線研究/評估範圍。", 403)
        return {"stage": "offline", "request_id": None, "version": None}
    require(actor, "run", case, purpose="production")
    requests = db.scalars(
        select(ReleaseRequest)
        .where(ReleaseRequest.status == "approved")
        .order_by(ReleaseRequest.created_at.desc())
    ).all()
    for request in requests:
        if request.scope.get("department") != case.department:
            continue
        if request.baseline.get("semantic_release_id") != manifest["semantic_release_id"] or set(
            request.baseline.get("rule_ids", [])
        ) != set(manifest["rule_ids"]):
            continue
        if request.baseline.get("model", {}).get("sha256") != manifest.get("model", {}).get("sha256"):
            continue
        # Gate evaluation uses its original authorized management record; it never borrows that role for clinical actions.
        last = db.scalar(
            select(GateDecision)
            .where(GateDecision.request_id == request.id, GateDecision.outcome == "approve")
            .order_by(GateDecision.created_at.desc())
        )
        manager = db.get(Actor, last.actor_id) if last else None
        if not manager or not manager.enabled:
            continue
        current = conditions(db, manager, request.baseline, request.stage)
        if not all(c["status"] == "met" for c in current):
            continue
        if last.evidence.get("baseline") != request.baseline:
            continue
        return {"stage": request.stage, "request_id": request.id, "version": request.version}
    fail("capability_not_released", "當前病例範圍或版本沒有有效准入；不執行生產自動檢查。", 403)
