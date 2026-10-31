from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..access import get_case
from ..common import digest, public, fail, audit
from ..models import Actor, Case, Document, Evidence, Source, uid


def current_documents(db: Session, case_id: str) -> list[Document]:
    docs = db.scalars(
        select(Document).where(Document.case_id == case_id).order_by(Document.version.desc(), Document.id)
    ).all()
    seen = set()
    result = []
    for doc in docs:
        if doc.document_key not in seen:
            seen.add(doc.document_key)
            result.append(doc)
    return result


def parse_quantity(raw: str) -> dict:
    match = re.fullmatch(r"\s*([<>≤≥]?)\s*([-+]?\d+(?:\.\d+)?)\s*([^\d\s].*)?\s*", raw)
    if not match:
        return {"raw_value": raw, "value": None, "status": "unknown"}
    try:
        value = str(Decimal(match[2]))
    except InvalidOperation:
        return {"raw_value": raw, "value": None, "status": "unknown"}
    return {
        "raw_value": raw,
        "value": value,
        "comparator": match[1] or "=",
        "unit": match[3] or None,
        "status": "parsed" if match[3] else "unit_unknown",
    }


def assertions_from_evidence(evidences: list[Evidence]) -> list[dict]:
    result = []
    for evidence in evidences:
        text = evidence.envelope["content"].get("text", "")
        if not text:
            continue
        for index, match in enumerate(re.finditer(r"[^。；;\n]+[。；;]?", text)):
            span = match[0]
            if not any(
                term in span
                for term in [
                    "過敏",
                    "診斷",
                    "肺炎",
                    "用藥",
                    "檢驗",
                    "檢查",
                    "發熱",
                    "allerg",
                    "diagnos",
                    "pneumonia",
                ]
            ):
                continue
            family = bool(re.search(r"家族|父親|母親|家屬|family|mother|father", span, re.I))
            patient = bool(re.search(r"患者|本人|patient", span, re.I))
            subject = "unknown" if family and patient else ("family" if family else "patient")
            temporality = (
                "planned"
                if re.search(r"擬|計劃|建議|plan", span, re.I)
                else ("historical" if re.search(r"既往|曾|history of", span, re.I) else "current")
            )
            polarity = (
                "unknown"
                if re.search(r"無記錄|未記錄|未提供|待補|不詳|unknown|not recorded", span, re.I)
                else (
                    "hypothetical"
                    if re.search(r"假如|如果|if ", span, re.I)
                    else (
                        "uncertain"
                        if re.search(r"疑似|考慮|可能|待排|possible|suspect", span, re.I)
                        else ("negated" if re.search(r"否認|無|未見|no |denies", span, re.I) else "affirmed")
                    )
                )
            )
            result.append(
                {
                    "id": digest([evidence.id, index])[:24],
                    "text": span,
                    "raw_text": span,
                    "subject": subject,
                    "polarity": polarity,
                    "temporality": temporality,
                    "certainty": "candidate",
                    "document_id": evidence.document_id or "source-record",
                    "evidence_ids": [evidence.id],
                    "local_span": [match.start(), match.end()],
                    "layer": "source_assertion",
                    "mapping_status": "local_candidate",
                    "not_patient_truth": True,
                }
            )
    return result


def case_context(db: Session, actor: Actor, case_id: str, manifest: dict | None = None):
    case = get_case(db, actor, case_id)
    if manifest:
        doc_ids = manifest["document_ids"]
        docs = db.scalars(select(Document).where(Document.case_id == case_id, Document.id.in_(doc_ids))).all()
    else:
        docs = current_documents(db, case_id)
        doc_ids = [x.id for x in docs]
    evidence = db.scalars(
        select(Evidence).where(Evidence.case_id == case_id, Evidence.document_id.in_(doc_ids))
    ).all()
    assertions = assertions_from_evidence(evidence)
    gaps = []
    if not docs:
        gaps.append("no_documents")
    if manifest and len(docs) != len(manifest["document_ids"]):
        gaps.append("document_version_unavailable")
    gaps.extend(case.details.get("gaps", []))
    return {
        "schema_version": "1.0",
        "case": public(case),
        "documents": [public(d) for d in docs],
        "evidence": [public(e) for e in evidence],
        "assertions": assertions,
        "coverage": {"declared_documents": len(doc_ids), "available_documents": len(docs), "gaps": gaps},
        "namespace": case.namespace,
        "context_version": case.version,
        "document_ids": doc_ids,
        "document_digest": digest({d.id: d.digest for d in docs}),
    }


def import_case(db: Session, actor: Actor, evidence_id: str, owner_id: str):
    from ..access import require
    from ..evidence import document_evidence

    require(actor, "review")
    evidence = db.get(Evidence, evidence_id)
    if not evidence or evidence.data_role != "business_evidence":
        fail("evidence_scope", "需要當前可讀的病例原文證據；規則或評測答案不能導為病例。", 404)
    source = db.get(Source, evidence.source_id)
    if source.data_kind == "unknown":
        fail("source_kind_unconfirmed", "先核實來源性質與允許用途，未知來源不自動進入病例建模。")
    if evidence.case_id:
        return {"id": evidence.case_id, "status": "already_linked"}
    raw = evidence.envelope["content"]
    record = raw.get("value", {})
    text = raw.get("text") or (record.get("text") if isinstance(record, dict) else None)
    if not isinstance(text, str) or not text.strip():
        fail(
            "clinical_text_missing",
            "當前證據沒有獨立臨床正文。結構字段須先按明確映射關聯，不能直接編造病歷。",
            422,
        )
    if len(text) > 200000:
        fail("case_budget", "正文超出一次病例接入預算。", 422)
    owner = db.get(Actor, owner_id)
    groups = set(actor.groups) & set(owner.groups if owner else [])
    if not owner or owner.role != "doctor" or not groups:
        fail("owner_scope", "責任醫生需位於當前獲准責任組。", 403)
    source_record = str(
        record.get("doc_id") if isinstance(record, dict) and record.get("doc_id") else evidence_id
    )
    encounter = "unlinked:" + source_record
    existing = db.scalar(
        select(Case).where(Case.namespace == source.namespace, Case.encounter_id == encounter)
    )
    if existing:
        return {"id": existing.id, "status": "already_registered"}
    title = str(record.get("title") or "來源病例敘述") if isinstance(record, dict) else "來源病例敘述"
    case = Case(
        id=uid(),
        namespace=source.namespace,
        encounter_id=encounter,
        patient_key="unlinked:" + source_record,
        display_name=title[:100],
        group_id=sorted(groups)[0],
        owner_id=owner.id,
        department="來源資料 · 待適配",
        disease_scope="尚未核對",
        data_kind=source.data_kind,
        status="blocked",
        risk="unknown",
        details={
            "scope_confirmed": False,
            "patient_identity": "unlinked",
            "encounter_identity": "unlinked",
            "origin_evidence_id": evidence.id,
            "origin_record_id": source_record,
            "source_namespace": source.namespace,
            "text_group": digest(text),
            "semantic_release_id": "semantic-v1",
            "gaps": ["encounter_and_scope_unconfirmed"],
            "assignment_purpose": "本地研究資料核查，不代表來源醫院實際醫生指派",
        },
    )
    db.add(case)
    db.flush()
    document = Document(
        id=uid(),
        case_id=case.id,
        document_key="source-narrative",
        title=title[:160],
        content=text,
        digest=digest(text),
        author_id="source-unspecified",
        source_id=source.id,
        fields={"original_record_id": source_record, "source_role": source.data_kind},
    )
    db.add(document)
    db.flush()
    document_evidence(db, source, document, "case-import")
    evidence.case_id = case.id
    audit(
        db,
        actor,
        "case.import",
        case.id,
        case_id=case.id,
        details={
            "evidence_id": evidence.id,
            "source_id": source.id,
            "identity": "unlinked",
            "data_kind": source.data_kind,
        },
    )
    return {"id": case.id, "status": case.status, "identity": "unlinked", "scope_confirmed": False}
