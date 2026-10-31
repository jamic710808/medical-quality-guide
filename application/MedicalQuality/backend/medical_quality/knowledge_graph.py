from __future__ import annotations

import copy
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .access import require, get_case
from .clinical_context.context import case_context
from .common import Command, audit, check_version, command, digest, fail, public
from .config import settings
from .models import Actor, Decision, ExportPermit, Finding, OntologyDraft, QualityRun, Rule, Task, now, uid
from .ontology import get_release, validate_native


def view(db: Session, actor: Actor, kind="ontology", scope_ref=None, release_id="semantic-v1", run_id=None):
    require(actor, "graph")
    release = get_release(db, release_id)
    ontology = copy.deepcopy(release.ontology)
    metadata = copy.deepcopy(release.manifest.get("graph_metadata", {"node_meta": {}, "edge_meta": {}}))
    ontology["iri"] = "urn:mq:ontology"
    for node in ontology["entityTypes"]:
        iri = metadata["node_meta"].get(node["id"], {}).get("original_iri")
        if iri:
            node["iri"] = iri
    for edge in ontology["relationships"]:
        meta = metadata["edge_meta"].get(edge["id"], {})
        if meta.get("predicate_ref"):
            edge["iri"] = meta["predicate_ref"]
        if meta.get("cardinality_status") == "unknown":
            edge["cardinalityKnown"] = False
    version_refs = {"semantic_release_id": release.id, "semantic_digest": release.digest}
    gaps = []
    bindings = release.manifest.get("bindings_view", [])
    if kind == "case":
        case = get_case(db, actor, scope_ref)
        run = db.get(QualityRun, run_id or case.details.get("current_run_id", ""))
        if run and run.case_id != case.id:
            fail("run_scope", "質控運行不屬於該病例。", 404)
        if run and run.manifest["semantic_release_id"] != release.id:
            release = get_release(db, run.manifest["semantic_release_id"])
            version_refs = {"semantic_release_id": release.id, "semantic_digest": release.digest}
        context = case_context(db, actor, case.id, run.manifest if run else None)
        nodes = []
        edges = []
        metadata = {"node_meta": {}, "edge_meta": {}}
        bindings = []

        def node(key, name, description, semantic_kind, color, icon, **meta):
            if any(n["id"] == key for n in nodes):
                return
            nodes.append(
                {
                    "id": key,
                    "name": name,
                    "description": description,
                    "properties": [],
                    "color": color,
                    "icon": icon,
                }
            )
            metadata["node_meta"][key] = {
                "semantic_kind": semantic_kind,
                "source_role": case.data_kind,
                **meta,
            }

        def edge(key, name, left, right, layer="source_link", **meta):
            edges.append(
                {
                    "id": key,
                    "name": name,
                    "from": left,
                    "to": right,
                    "cardinality": "many-to-many",
                    "kind": "association",
                }
            )
            metadata["edge_meta"][key] = {
                "assertion_layer": layer,
                "cardinality_status": "not_applicable",
                **meta,
            }

        node(
            case.id,
            case.display_name + " · " + case.encounter_id,
            "尚未確認就診歸屬的來源敘述"
            if case.details.get("encounter_identity") == "unlinked"
            else "固定來源域內的一次就診記錄",
            "instance",
            "#0A84FF",
            "🏥",
            case_id=case.id,
            namespace=case.namespace,
        )
        for doc in context["documents"]:
            node(
                doc["id"],
                doc["title"],
                f"文書版本 {doc['version']}",
                "document",
                "#64D2FF",
                "📄",
                document_id=doc["id"],
                version=doc["version"],
            )
            edge("case_" + doc["id"], "包含文書", case.id, doc["id"])
        for ev in context["evidence"]:
            text = ev["envelope"]["content"].get("text", "")
            node(
                ev["id"],
                text[:24] or "來源字段",
                text,
                "evidence",
                "#30D158",
                "📝",
                evidence_id=ev["id"],
                document_id=ev["document_id"],
                locator=ev["envelope"]["locator"],
                quality=ev["envelope"]["quality"],
                source_version=ev["source_version"],
            )
            edge("doc_" + ev["id"], "原文位置", ev["document_id"], ev["id"], support_refs=[ev["id"]])
        for assertion in context["assertions"]:
            node(
                assertion["id"],
                assertion["text"][:24],
                assertion["text"],
                "assertion",
                "#BF5AF2",
                "💬",
                assertion=assertion,
            )
            for eid in assertion["evidence_ids"]:
                edge(
                    "a_" + assertion["id"] + "_" + eid,
                    "記載主張",
                    eid,
                    assertion["id"],
                    layer="source_assertion",
                    support_refs=[eid],
                )
        findings = (
            db.scalars(select(Finding).where(Finding.case_id == case.id, Finding.run_id == run.id)).all()
            if run
            else []
        )
        for finding in findings:
            node(
                finding.id,
                finding.title,
                finding.reason,
                "finding",
                "#FF453A" if finding.severity == "high" else "#FF9F0A",
                "⚠️",
                finding_id=finding.id,
                risk=finding.severity,
                status=finding.status,
                layer=finding.layer,
                case_id=case.id,
            )
            rule = db.get(Rule, finding.rule_id)
            node(
                rule.id,
                rule.name,
                rule.content,
                "rule",
                "#5E5CE6",
                "🛡️",
                rule_id=rule.id,
                rule_key=rule.rule_key,
                version=rule.version,
            )
            edge(
                "rule_" + finding.id,
                "依據規則",
                finding.id,
                rule.id,
                layer="rule_judgment",
                support_refs=[rule.id],
            )
            for eid in finding.evidence_ids:
                if eid in metadata["node_meta"]:
                    edge(
                        "support_" + finding.id + "_" + eid,
                        "引用證據",
                        finding.id,
                        eid,
                        layer=finding.layer,
                        support_refs=[eid],
                    )
            task = db.scalar(select(Task).where(Task.finding_id == finding.id))
            if task:
                for dec in db.scalars(select(Decision).where(Decision.task_id == task.id)).all():
                    node(
                        dec.id,
                        "責任意見 · " + dec.action,
                        dec.reason,
                        "decision",
                        "#AC8E68",
                        "✍️",
                        decision_id=dec.id,
                        actor_id=dec.actor_id,
                        version=dec.version,
                    )
                    edge(
                        "decision_" + dec.id,
                        "決定對象",
                        dec.id,
                        finding.id,
                        layer="human_decision",
                        support_refs=[dec.id],
                    )
        ontology = {
            "name": case.display_name + " · 病例證據",
            "description": "來源斷言、疑似問題與固定證據的關係",
            "entityTypes": nodes,
            "relationships": edges,
        }
        version_refs.update(
            {
                "case_id": case.id,
                "context_version": context["context_version"],
                "run_id": run.id if run else None,
                "document_ids": context["document_ids"],
                "document_digest": context["document_digest"],
            }
        )
        gaps = context["coverage"]["gaps"]
        scope_ref = case.id
    elif kind == "rule":
        rules = db.scalars(select(Rule).where(Rule.semantic_release_id == release.id)).all()
        selected = next((r for r in rules if scope_ref in {r.id, r.rule_key}), None) if scope_ref else None
        if scope_ref and not selected:
            fail("rule_missing", "此語義版本沒有所選規則。", 404)
        rules = [selected] if selected else rules
        for rule in rules:
            ontology["entityTypes"].append(
                {
                    "id": rule.id,
                    "name": rule.name,
                    "description": rule.content,
                    "properties": [],
                    "icon": "🛡️",
                    "color": "#FF9F0A",
                }
            )
            metadata["node_meta"][rule.id] = {
                "semantic_kind": "rule",
                "rule_id": rule.id,
                "rule_key": rule.rule_key,
                "approval_status": rule.status,
                "version": rule.version,
            }
            for concept in rule.specification.get("concepts", []):
                if concept in metadata["node_meta"]:
                    key = rule.id + "_" + concept
                    ontology["relationships"].append(
                        {
                            "id": key,
                            "name": "檢查依據",
                            "from": rule.id,
                            "to": concept,
                            "cardinality": "many-to-many",
                        }
                    )
                    metadata["edge_meta"][key] = {
                        "assertion_layer": "rule_definition",
                        "cardinality_status": "not_applicable",
                        "support_refs": [rule.id],
                    }
        version_refs["rule_versions"] = {r.id: r.version for r in rules}
        ontology["name"] = "規則與語義依據"
        ontology["description"] = "規則適用關係不代表實際病例結果或臨床因果。"
    elif kind != "ontology":
        fail("view_kind_invalid", "圖譜視圖類型無效。", 422)
    result = {
        "schema_version": "1.0",
        "view_kind": kind,
        "scope_ref": scope_ref or release.id,
        "ontology": ontology,
        "bindings": bindings,
        **metadata,
        "version_refs": version_refs,
        "gaps": gaps,
        "loss_report": release.manifest.get("loss_report", []),
        "loaded_counts": {"nodes": len(ontology["entityTypes"]), "edges": len(ontology["relationships"])},
        "has_more": False,
        "capabilities": {
            "edit": actor.role in {"info", "expert", "qc"} and kind == "ontology",
            "export": actor.role in {"qc", "doctor", "expert"},
            "publish": False,
            "clinical_approval": False,
        },
    }
    result["projection_digest"] = digest(result)
    result["view_id"] = digest([actor.id, actor.auth_version, kind, result["scope_ref"], version_refs])[:32]
    audit(
        db,
        actor,
        "graph.view",
        result["view_id"],
        case_id=scope_ref if kind == "case" else None,
        details={"view_kind": kind, "counts": result["loaded_counts"]},
    )
    return result


def save_draft(db: Session, actor: Actor, payload: dict, draft_id=None, cmd: Command | None = None):
    require(actor, "draft")
    ontology = payload.get("ontology", {})
    if any(
        n.get("semantic_kind") not in {None, "class", "concept"}
        for n in payload.get("metadata_map", {}).get("node_meta", {}).values()
    ):
        fail("instance_not_definition", "業務實例和病歷證據不能作為本體類型保存。", 422)
    issues = validate_native(ontology)
    if any(x.get("blocking") for x in issues):
        fail("draft_invalid", "候選存在結構或定義缺口。", 422, issues=issues)
    if draft_id:
        draft = db.scalar(select(OntologyDraft).where(OntologyDraft.id == draft_id).with_for_update())
        if not draft or draft.actor_id != actor.id:
            fail("draft_scope", "候選不存在或不屬於當前維護者。", 404)
        check_version(draft, cmd.expected_version)
        if draft.status != "draft":
            fail("draft_submitted", "已提交的候選不能覆蓋，請建立後續候選。")
        draft.ontology = ontology
        draft.version += 1
    else:
        release = get_release(db, payload.get("base_release_id", "semantic-v1"))
        draft = OntologyDraft(
            id=uid(),
            actor_id=actor.id,
            base_release_id=release.id,
            status="draft",
            ontology=ontology,
            metadata_map=payload.get("metadata_map", {}),
            loss_report=payload.get("loss_report", []),
            review={},
        )
        db.add(draft)
    db.flush()
    audit(
        db,
        actor,
        "ontology.draft.save",
        draft.id,
        after=draft.version,
        details={"base_release_id": draft.base_release_id, "format_issues": len(issues)},
    )
    return {**public(draft), "validation_issues": issues, "production_published": False}


def submit_draft(db: Session, actor: Actor, draft_id: str, cmd: Command):
    require(actor, "draft")
    draft = db.scalar(select(OntologyDraft).where(OntologyDraft.id == draft_id).with_for_update())
    if not draft or draft.actor_id != actor.id:
        fail("draft_scope", "候選不可訪問。", 404)

    def perform():
        check_version(draft, cmd.expected_version)
        if draft.status != "draft":
            fail("draft_state", "候選已經提交。")
        if draft.loss_report:
            fail("semantic_loss_unresolved", "仍有未解決的語義轉換損失，先核對原始包。")
        if any(i["blocking"] for i in validate_native(draft.ontology)):
            fail("draft_invalid", "候選定義不完整。")
        reviewer_id = cmd.payload.get("reviewer_id", "expert3" if settings().mode == "local" else "")
        reviewer = db.get(Actor, reviewer_id)
        if not reviewer or reviewer.role != "expert" or not reviewer.enabled:
            fail("reviewer_required", "請指定有效的專業審核責任人。", 422)
        draft.status = "in_review"
        draft.version += 1
        draft.review = {
            **draft.review,
            "submitted_by": actor.id,
            "reason": cmd.reason,
            "reviewer_id": reviewer_id,
            "reviewer_name": reviewer.name,
            "required": ["專業定義審核", "OWL 2 EL/ELK", "SHACL/CQ", "映射與許可", "固定語義發佈"],
            "production_approval": False,
        }
        audit(db, actor, "ontology.draft.submit", draft.id, after=draft.version, reason=cmd.reason)
        return public(draft)

    return command(db, actor, "ontology.draft.submit", draft.id, cmd, perform)


def authorize_export(db: Session, actor: Actor, payload: dict):
    require(actor, "export_graph")
    kind = payload.get("kind", "png")
    view_kind = payload.get("view_kind", "ontology")
    if kind not in {"png", "projection_json", "native_rdf", "native_json", "formal_package"}:
        fail("export_kind", "導出格式無效。", 422)
    if payload.get("draft_id"):
        require(actor, "draft")
        draft = db.get(OntologyDraft, payload["draft_id"])
        if not draft or draft.actor_id != actor.id:
            fail("draft_scope", "候選不可訪問。", 404)
        if draft.version != payload.get("draft_version"):
            fail("draft_changed", "候選已更新，請重新保存和核對導出。")
        if kind not in {"native_rdf", "native_json"}:
            fail("draft_export_kind", "候選只提供標明狀態的原生子集導出。", 422)
        audit(
            db,
            actor,
            "ontology.draft.export",
            draft.id,
            details={"kind": kind, "version": draft.version, "status": draft.status},
        )
        return {"draft": public(draft), "kind": kind, "production_published": False}
    if view_kind != "ontology" and kind in {"native_rdf", "native_json", "formal_package"}:
        fail("instance_export_type", "包含業務實例的圖只允許顯示投影或圖像導出，不能序列化為 OWL 類。", 422)
    current = view(
        db,
        actor,
        view_kind,
        payload.get("scope_ref"),
        payload.get("release_id", "semantic-v1"),
        payload.get("run_id"),
    )
    if payload.get("projection_digest") != current["projection_digest"]:
        fail("graph_changed", "圖譜基線已變化，請重新核對導出內容。")
    permit = ExportPermit(
        id=uid(),
        actor_id=actor.id,
        scope={
            "view_id": current["view_id"],
            "digest": current["projection_digest"],
            "case_id": payload.get("scope_ref") if view_kind == "case" else None,
        },
        kind=kind,
        expires_at=now() + timedelta(minutes=1),
    )
    db.add(permit)
    db.flush()
    audit(
        db,
        actor,
        "graph.export.authorize",
        permit.id,
        case_id=permit.scope["case_id"],
        reason=payload.get("purpose", "本地核查"),
        details={"kind": kind, "view_id": current["view_id"]},
    )
    return {"id": permit.id, "expires_at": permit.expires_at.isoformat(), "kind": kind, "view": current}
