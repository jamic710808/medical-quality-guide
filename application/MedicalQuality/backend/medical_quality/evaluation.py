from __future__ import annotations

from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from .access import require, get_case
from .common import audit, command, check_version, Command, digest, fail, public
from .config import settings
from .models import Actor, Arbitration, EvaluationBatch, Judgment, QualityRun, now, uid

VERDICTS = {"positive", "negative", "unable"}


def compute_metrics(rows: list[dict]) -> dict:
    counts = Counter({"TP": 0, "FP": 0, "FN": 0, "TN": 0, "U_pos": 0, "U_neg": 0, "U_ref": 0})
    high_fn = []
    unresolved_high = []
    for row in rows:
        reference = row.get("reference")
        pred = row.get("prediction", "unknown")
        if reference not in {"positive", "negative"}:
            counts["U_ref"] += 1
            if row.get("severity") == "high":
                unresolved_high.append(row["id"])
            continue
        if reference == "positive":
            key = "TP" if pred == "issue" else ("FN" if pred == "pass" else "U_pos")
            if row.get("severity") == "high" and key == "FN":
                high_fn.append(row["id"])
            if row.get("severity") == "high" and key == "U_pos":
                unresolved_high.append(row["id"])
        else:
            key = "FP" if pred == "issue" else ("TN" if pred == "pass" else "U_neg")
        counts[key] += 1
    p = counts["TP"] + counts["FN"] + counts["U_pos"]
    n = counts["TN"] + counts["FP"] + counts["U_neg"]

    def metric(num, den):
        return {
            "numerator": num,
            "denominator": den,
            "value": num / den if den else None,
            "reason": None if den else "zero_denominator",
        }

    return {
        "counts": dict(counts),
        "total": len(rows),
        "positive_reference": p,
        "negative_reference": n,
        "end_to_end_recall": metric(counts["TP"], p),
        "conditional_recall": metric(counts["TP"], counts["TP"] + counts["FN"]),
        "precision": metric(counts["TP"], counts["TP"] + counts["FP"]),
        "specificity": metric(counts["TN"], counts["TN"] + counts["FP"]),
        "false_positive_rate": metric(counts["FP"], n),
        "decision_coverage": metric(counts["TP"] + counts["FN"] + counts["TN"] + counts["FP"], p + n),
        "abstention": metric(counts["U_pos"] + counts["U_neg"], p + n),
        "reference_coverage": metric(p + n, len(rows)),
        "high_risk_false_negatives": high_fn,
        "unresolved_high_risk": unresolved_high,
        "veto": bool(high_fn or unresolved_high),
    }


def rubric_metrics(judgments: list[dict], expected_judgments: int) -> dict:
    """按獨立原判計數，缺項、無法判斷不計作通過；不把仲裁合併成原判。"""
    result = {}
    for field in ("location", "support", "explanation", "suggestion"):
        counts = Counter(j.get("rubric", {}).get(field, "unreviewed") for j in judgments)
        counts["unreviewed"] += max(0, expected_judgments - len(judgments))
        assessed = counts["pass"] + counts["fail"]
        result[field] = {
            "counts": {key: counts[key] for key in ("pass", "fail", "unable", "unreviewed")},
            "numerator": counts["pass"],
            "denominator": assessed,
            "value": counts["pass"] / assessed if assessed else None,
            "expected_judgments": expected_judgments,
            "unit": "sample_x_independent_rater",
        }
    return result


def create_batch(db: Session, actor: Actor, payload: dict):
    require(actor, "evaluation")
    require(actor, "assign")
    batch_id = uid()
    run_ids = payload.get("run_ids", [])
    if not run_ids or len(run_ids) > 50:
        fail("batch_scope", "請選擇 1～50 個固定質控運行。", 422)
    raters = payload.get("raters", ["expert1", "expert2"])
    arbitrator = payload.get("arbitrator", "expert3")
    if len(raters) != 2 or len(set(raters + [arbitrator])) != 3:
        fail("independent_raters", "兩位原判者與仲裁者必須是不同主體。", 422)
    for key in raters + [arbitrator]:
        person = db.get(Actor, key)
        if (
            not person
            or person.role != "expert"
            or not person.enabled
            or (person.expires_at and person.expires_at <= now())
        ):
            fail("expert_identity", "評測人員無效。", 422)
    samples = []
    versions = {}
    groups = []
    for rid in dict.fromkeys(run_ids):
        run = db.get(QualityRun, rid)
        if not run or run.status in {"queued", "running"}:
            fail("run_incomplete", "質控運行尚未形成固定結果。", 422)
        case = get_case(db, actor, run.case_id)
        for key in raters + [arbitrator]:
            person = db.get(Actor, key)
            if case.data_kind == "production" and not person.oidc_subject:
                fail("expert_identity", "生產樣本必須指派已映射真實身份的專家。", 403)
            if case.id not in person.case_ids:
                before = person.version
                person.case_ids = [*person.case_ids, case.id]
                person.version += 1
                audit(
                    db,
                    actor,
                    "evaluation.case_assignment",
                    person.id,
                    case_id=case.id,
                    reason="創建評測批次時明確指派此病例範圍",
                    before=before,
                    after=person.version,
                    details={
                        "batch_id": batch_id,
                        "assigned_role": "arbitrator" if key == arbitrator else "rater",
                    },
                )
        group = (
            case.details.get("text_group")
            if case.details.get("patient_identity") == "unlinked"
            else digest([case.namespace, case.patient_key])
        )
        group = group or digest([case.namespace, case.patient_key])
        groups.append(group)
        versions[rid] = run.manifest
        for result in run.results:
            samples.append(
                {
                    "id": digest([rid, result["rule_id"]])[:24],
                    "run_id": rid,
                    "case_id": case.id,
                    "rule_id": result["rule_id"],
                    "rule_key": result["rule_key"],
                    "title": result["name"],
                    "prediction": result["status"],
                    "severity": result["severity"],
                    "evidence_ids": result["evidence_ids"],
                    "data_kind": case.data_kind,
                    "group": group,
                    "document_digest": run.manifest["document_digest"],
                }
            )
    batch = EvaluationBatch(
        id=batch_id,
        name=str(payload.get("name", "新評測批次"))[:160],
        status="frozen",
        samples=samples,
        assignments={"raters": raters, "arbitrator": arbitrator},
        manifest={
            "runs": versions,
            "groups": sorted(set(groups)),
            "partition": "evaluation",
            "identity_mode": settings().mode,
            "sample_digest": digest(samples),
        },
        protocol={
            "unit": "case_version_x_rule",
            "thresholds": None,
            "rubric_version": "mq-rubric-1",
            "clinical_approved": False,
        },
    )
    db.add(batch)
    db.flush()
    audit(
        db,
        actor,
        "evaluation.freeze",
        batch.id,
        details={"samples": len(samples), "source_kinds": sorted({s["data_kind"] for s in samples})},
    )
    return public(batch)


def judge(db: Session, actor: Actor, batch_id: str, cmd: Command):
    require(actor, "judge")
    batch = db.scalar(select(EvaluationBatch).where(EvaluationBatch.id == batch_id).with_for_update())
    if not batch or actor.id not in batch.assignments["raters"]:
        fail("rater_assignment", "不是本批次的原判人員。", 403)
    sample = next((s for s in batch.samples if s["id"] == cmd.payload.get("sample_id")), None)
    if not sample:
        fail("sample_missing", "樣本不在凍結批次中。", 404)
    get_case(db, actor, sample["case_id"])

    def perform():
        check_version(batch, cmd.expected_version)
        if db.scalar(
            select(Judgment).where(
                Judgment.batch_id == batch.id,
                Judgment.sample_id == sample["id"],
                Judgment.actor_id == actor.id,
            )
        ):
            fail("judgment_immutable", "原判已保存；不能覆蓋或重複計作第二位專家。")
        verdict = cmd.payload.get("verdict")
        severity = cmd.payload.get("severity", sample["severity"])
        rubric = cmd.payload.get("rubric", {})
        if verdict not in VERDICTS or severity not in {"high", "medium", "low", "unknown"}:
            fail("verdict_invalid", "判定或風險級別無效。", 422)
        allowed = {"location", "support", "explanation", "suggestion"}
        if set(rubric) - allowed or any(v not in {"pass", "fail", "unable"} for v in rubric.values()):
            fail("rubric_invalid", "分項評價格式無效。", 422)
        item = Judgment(
            id=uid(),
            batch_id=batch.id,
            sample_id=sample["id"],
            actor_id=actor.id,
            verdict=verdict,
            severity=severity,
            reason=cmd.reason,
            rubric=rubric,
        )
        db.add(item)
        batch.version += 1
        db.flush()
        audit(
            db,
            actor,
            "evaluation.judge",
            batch.id,
            case_id=sample["case_id"],
            reason=cmd.reason,
            after=batch.version,
            details={"judgment_id": item.id, "sample_id": sample["id"]},
        )
        return {"id": item.id, "batch_id": batch.id, "version": batch.version, "status": "submitted"}

    return command(db, actor, "evaluation.judge", batch.id + ":" + sample["id"], cmd, perform)


def arbitrate(db: Session, actor: Actor, batch_id: str, cmd: Command):
    require(actor, "judge")
    batch = db.scalar(select(EvaluationBatch).where(EvaluationBatch.id == batch_id).with_for_update())
    if not batch or batch.assignments["arbitrator"] != actor.id:
        fail("arbitrator_assignment", "不是本批次的仲裁人員。", 403)
    sample = next((s for s in batch.samples if s["id"] == cmd.payload.get("sample_id")), None)
    if not sample:
        fail("sample_missing", "樣本不存在。", 404)
    get_case(db, actor, sample["case_id"])

    def perform():
        check_version(batch, cmd.expected_version)
        judgments = db.scalars(
            select(Judgment).where(Judgment.batch_id == batch.id, Judgment.sample_id == sample["id"])
        ).all()
        if len(judgments) != 2 or len({j.actor_id for j in judgments}) != 2:
            fail("two_judgments_required", "須先保留兩名獨立原判。")
        verdict = cmd.payload.get("verdict")
        if verdict not in VERDICTS:
            fail("verdict_invalid", "裁決無效。", 422)
        prior = db.scalars(
            select(Arbitration).where(Arbitration.batch_id == batch.id, Arbitration.sample_id == sample["id"])
        ).all()
        item = Arbitration(
            id=uid(),
            batch_id=batch.id,
            sample_id=sample["id"],
            actor_id=actor.id,
            judgment_ids=[j.id for j in judgments],
            verdict=verdict,
            severity=cmd.payload.get("severity", sample["severity"]),
            reason=cmd.reason,
            version=len(prior) + 1,
        )
        db.add(item)
        batch.version += 1
        db.flush()
        audit(
            db,
            actor,
            "evaluation.arbitrate",
            batch.id,
            case_id=sample["case_id"],
            reason=cmd.reason,
            after=batch.version,
            details={"arbitration_id": item.id},
        )
        return {"id": item.id, "version": batch.version, "status": "arbitrated"}

    return command(db, actor, "evaluation.arbitrate", batch.id + ":" + sample["id"], cmd, perform)


def report(db: Session, actor: Actor, batch_id: str, *, gate=False, for_export=False):
    require(
        actor,
        "export_assets" if for_export else ("evaluation_report" if actor.role == "manager" else "evaluation"),
    )
    batch = db.get(EvaluationBatch, batch_id)
    if not batch:
        fail("batch_missing", "批次不可用。", 404)
    if actor.role == "expert" and actor.id not in batch.assignments["raters"] + [
        batch.assignments["arbitrator"]
    ]:
        fail("batch_assignment", "未指派此評測批次。", 403)
    judgments = db.scalars(select(Judgment).where(Judgment.batch_id == batch.id)).all()
    arbitrations = db.scalars(
        select(Arbitration).where(Arbitration.batch_id == batch.id).order_by(Arbitration.version.desc())
    ).all()
    rows = []
    agreement_pairs = []
    visible_judgments = []
    for sample in batch.samples:
        own = [j for j in judgments if j.sample_id == sample["id"]]
        a = next((x for x in arbitrations if x.sample_id == sample["id"]), None)
        verdict = None
        severity = sample["severity"]
        if len(own) == 2:
            agreement_pairs.append((own[0].verdict, own[1].verdict))
            if own[0].verdict == own[1].verdict:
                verdict = own[0].verdict
                severity = "high" if any(j.severity == "high" for j in own) else severity
            elif a:
                verdict = a.verdict
                severity = a.severity
        # A rater cannot see the other verdict before independently submitting.
        allowed = (
            actor.role != "expert"
            or actor.id == batch.assignments["arbitrator"]
            or any(j.actor_id == actor.id for j in own)
        )
        visible_judgments.extend(public(j) for j in own if allowed or j.actor_id == actor.id)
        rows.append(
            {
                **sample,
                "reference": verdict,
                "severity": severity,
                "judgment_count": len(own),
                "disagreement": len(own) == 2 and own[0].verdict != own[1].verdict,
                "arbitrated": bool(a),
            }
        )
    metrics = compute_metrics(rows)
    strata = {
        field: {
            value: compute_metrics([row for row in rows if row[field] == value])
            for value in sorted({row[field] for row in rows})
        }
        for field in ("severity", "rule_key", "data_kind")
    }
    rubrics = rubric_metrics(visible_judgments, len(rows) * 2)
    pair_count = len(agreement_pairs)
    same = sum(a == b for a, b in agreement_pairs)
    left = Counter(a for a, b in agreement_pairs)
    right = Counter(b for a, b in agreement_pairs)
    expected = sum(left[k] * right[k] for k in VERDICTS) / (pair_count**2) if pair_count else None
    agreement = same / pair_count if pair_count else None
    kappa = (agreement - expected) / (1 - expected) if expected is not None and expected != 1 else None
    complete = all(row["reference"] in {"positive", "negative"} for row in rows)
    qualification = (
        "engineering_only"
        if batch.manifest["identity_mode"] == "local"
        else (
            "professional_accepted"
            if batch.protocol.get("clinical_approved") and complete
            else "pending_professional_acceptance"
        )
    )
    if for_export:
        return {
            "batch_id": batch.id,
            "batch_version": batch.version,
            "sample_digest": batch.manifest["sample_digest"],
            "protocol": batch.protocol,
            "metrics": metrics,
            "strata": strata,
            "rubrics": rubrics,
            "agreement": {"observed": agreement, "pairs": pair_count, "kappa": kappa},
            "qualification": qualification,
            "status": "complete" if complete else "partial",
            "excluded": ["逐樣本答案", "患者原文", "人員真實身份映射", "受限留出數據"],
            "reproduction_boundary": "聚合報告可核查；沒有受限樣本/原判的交付包不能完整重現臨床評測。",
        }
    return {
        "batch": public(batch),
        "samples": rows,
        "judgments": visible_judgments,
        "arbitrations": [public(a) for a in arbitrations],
        "metrics": metrics,
        "strata": strata,
        "rubrics": rubrics,
        "agreement": {
            "observed": agreement,
            "pairs": pair_count,
            "kappa": kappa,
            "basis": "原始兩份判定，不以仲裁覆蓋",
        },
        "status": "complete" if complete else ("partial" if judgments else "not_evaluated"),
        "qualification": qualification,
        "thresholds": batch.protocol.get("thresholds"),
        "missing": ["clinical_thresholds"] if not batch.protocol.get("thresholds") else [],
    }


def freeze_protocol(db: Session, actor: Actor, batch_id: str, cmd: Command):
    if actor.role not in {"expert", "manager"}:
        fail("protocol_role", "評測口徑由專家或業務責任人記錄。", 403)
    batch = db.scalar(select(EvaluationBatch).where(EvaluationBatch.id == batch_id).with_for_update())
    if not batch:
        fail("batch_missing", "批次不可用。", 404)
    if actor.role == "expert" and actor.id not in batch.assignments["raters"] + [
        batch.assignments["arbitrator"]
    ]:
        fail("batch_assignment", "未獲派當前評測。", 403)

    def perform():
        check_version(batch, cmd.expected_version)
        if db.scalar(select(Judgment.id).where(Judgment.batch_id == batch.id).limit(1)):
            fail("protocol_frozen", "原判開始後不能調整閾值來改善分數；請建立後續批次。")
        values = cmd.payload.get("thresholds", {})
        allowed = {"min_end_to_end_recall", "max_false_positive_rate", "min_reference_coverage"}
        if set(values) != allowed or any(
            not isinstance(v, (int, float)) or isinstance(v, bool) or not 0 <= v <= 1 for v in values.values()
        ):
            fail("thresholds_invalid", "請由責任人明確填寫三項 0～1 的門檻；系統不提供默認合格線。", 422)
        clinical = bool(
            settings().mode == "production"
            and actor.oidc_subject
            and cmd.payload.get("protocol_evidence_ref")
        )
        batch.protocol = {
            **batch.protocol,
            "thresholds": values,
            "protocol_evidence_ref": cmd.payload.get("protocol_evidence_ref"),
            "recorded_by": actor.id,
            "reason": cmd.reason,
            "clinical_approved": clinical,
            "identity_mode": settings().mode,
        }
        batch.version += 1
        audit(
            db,
            actor,
            "evaluation.protocol.freeze",
            batch.id,
            reason=cmd.reason,
            after=batch.version,
            details={"clinical_approved": clinical, "threshold_digest": digest(values)},
        )
        return public(batch)

    return command(db, actor, "evaluation.protocol.freeze", batch.id, cmd, perform)


def sample_detail(db: Session, actor: Actor, batch_id: str, sample_id: str):
    require(actor, "evaluation")
    batch = db.get(EvaluationBatch, batch_id)
    if not batch:
        fail("batch_missing", "批次不可訪問。", 404)
    if actor.role == "expert" and actor.id not in batch.assignments["raters"] + [
        batch.assignments["arbitrator"]
    ]:
        fail("batch_assignment", "未獲派此評測。", 403)
    sample = next((s for s in batch.samples if s["id"] == sample_id), None)
    if not sample:
        fail("sample_missing", "凍結樣本不存在。", 404)
    get_case(db, actor, sample["case_id"])
    from .clinical_context.context import case_context

    context = case_context(db, actor, sample["case_id"], batch.manifest["runs"][sample["run_id"]])
    audit(
        db,
        actor,
        "evaluation.sample.read",
        batch.id,
        case_id=sample["case_id"],
        details={"sample_id": sample_id, "fixed_run": sample["run_id"]},
    )
    return {
        "sample": sample,
        "documents": context["documents"],
        "evidence": context["evidence"],
        "manifest": batch.manifest["runs"][sample["run_id"]],
    }


def compare_reports(left: dict, right: dict):
    def scope(report):
        return sorted((s["group"], s["document_digest"], s["rule_key"]) for s in report["samples"])

    if scope(left) != scope(right) or left["thresholds"] != right["thresholds"]:
        fail("comparison_mismatch", "樣本/文書/規則範圍或閾值口徑不同，不能作配對改善比較。")

    def entries(report):
        return {(s["group"], s["document_digest"], s["rule_key"]): s for s in report["samples"]}

    a, b = entries(left), entries(right)
    rows = []
    for key, x in a.items():
        y = b[key]
        if x["reference"] != y["reference"]:
            fail("reference_changed", "參照結果改變，不能將差異歸為模型或版本改善。")
        rows.append(
            {
                "group": key[0],
                "rule_key": key[2],
                "before": x["prediction"],
                "after": y["prediction"],
                "reference": x["reference"],
                "changed": x["prediction"] != y["prediction"],
                "unresolved": x["reference"] not in {"positive", "negative"} or y["prediction"] == "unknown",
            }
        )
    return {
        "pairs": rows,
        "left_metrics": left["metrics"],
        "right_metrics": right["metrics"],
        "qualification": "paired_engineering_comparison",
        "high_risk_regressions": right["metrics"]["high_risk_false_negatives"],
        "clinical_approval": False,
    }
