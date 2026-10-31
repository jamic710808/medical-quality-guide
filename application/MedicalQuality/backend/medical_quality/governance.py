"""規則與本體候選的責任審核。工程審核不會生成臨床批准。"""

from __future__ import annotations
import copy
from pathlib import Path

from rdflib import Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef, XSD
from rdflib.namespace import SH
from rdflib.collection import Collection
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from .access import require
from .common import Command, audit, check_version, command, digest, fail, public
from .config import settings
from .models import Actor, Evidence, OntologyDraft, Outbox, Rule, SemanticRelease, Source
from .ontology import (
    concept_iris,
    get_release,
    native_projection,
    required_concept_iri,
    validate_native,
    validate_package,
)


def new_rule_version(db: Session, actor: Actor, rule_id: str, cmd: Command):
    require(actor, "knowledge_edit")
    base = db.get(Rule, rule_id)
    if not base:
        fail("rule_missing", "規則不可訪問。", 404)

    def perform():
        check_version(base, cmd.expected_version)
        db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": int(digest(base.rule_key)[:15], 16)})
        release = get_release(db, cmd.payload.get("semantic_release_id", base.semantic_release_id))
        content = str(cmd.payload.get("content", base.content)).strip()
        if not content or len(content) > 20000:
            fail("rule_content", "規則說明不能為空或超過預算。", 422)
        specification = {**base.specification, **cmd.payload.get("specification", {})}
        known = concept_iris(release)
        if not {required_concept_iri(x) for x in specification.get("concepts", [])} <= known:
            fail("rule_concepts", "規則引用了當前本體沒有的概念。", 422)
        version = db.scalar(select(func.max(Rule.version)).where(Rule.rule_key == base.rule_key)) + 1
        candidate = Rule(
            id=base.rule_key + "-v" + str(version),
            rule_key=base.rule_key,
            version=version,
            name=base.name,
            category=base.category,
            severity=base.severity,
            status="candidate",
            purpose="engineering" if settings().mode == "local" else "research",
            semantic_release_id=release.id,
            content=content,
            specification=specification,
            provenance={
                **base.provenance,
                "parent_rule_id": base.id,
                "change_reason": cmd.reason,
                "created_by": actor.id,
                "professional_review": "pending",
                "reviews": [],
                "executor_binding": "mq-eight-document-checks-v1",
                "definition_change_requires_executor_evaluation": True,
            },
        )
        db.add(candidate)
        db.flush()
        audit(db, actor, "rule.version.create", candidate.id, reason=cmd.reason, after=version)
        return public(candidate)

    return command(db, actor, "rule.version.create", base.id, cmd, perform)


def review_rule(db: Session, actor: Actor, rule_id: str, cmd: Command):
    require(actor, "knowledge_edit")
    if actor.role != "expert":
        fail("professional_role", "規則審核由獲權專業審核人執行。", 403)
    rule = db.scalar(select(Rule).where(Rule.id == rule_id).with_for_update())
    if not rule:
        fail("rule_missing", "規則不可用。", 404)

    def perform():
        if rule.policy_version != cmd.expected_version:
            fail("version_conflict", "規則資格已改變。")
        decision = cmd.payload.get("decision")
        if decision not in {"approve", "reject"}:
            fail("review_decision", "請選擇審核通過或退回。", 422)
        record = {
            "actor_id": actor.id,
            "actor_name": actor.name,
            "decision": decision,
            "reason": cmd.reason,
            "identity_mode": settings().mode,
            "rule_version": rule.version,
        }
        clinical = False
        if decision == "approve" and settings().mode == "production":
            from .release import deployment_policy

            policy = deployment_policy()
            refs = cmd.payload.get("evidence_ids", [])
            if (
                not actor.oidc_subject
                or not refs
                or not cmd.payload.get("scope")
                or not cmd.payload.get("effective_from")
            ):
                fail("clinical_review_inputs", "生產審核需要真實身份、依據、適用範圍和生效時間。")
            for ref in refs:
                evidence = db.get(Evidence, ref)
                source = db.get(Source, evidence.source_id) if evidence else None
                if (
                    not evidence
                    or evidence.data_role != "rule_reference"
                    or not source
                    or source.id not in policy.get("authorized_knowledge_source_ids", [])
                    or source.data_kind == "synthetic"
                ):
                    fail("knowledge_authority", "依據來源或使用資格未獲得授權。")
            record.update(
                evidence_ids=refs, scope=cmd.payload["scope"], effective_from=cmd.payload["effective_from"]
            )
            clinical = True
        rule.status = "approved" if clinical else ("retired" if decision == "reject" else "candidate")
        if clinical:
            rule.purpose = "production"
        rule.provenance = {
            **rule.provenance,
            "reviews": [*rule.provenance.get("reviews", []), record],
            "professional_review": "approved" if clinical else "pending",
            "engineering_review": decision if settings().mode == "local" else None,
        }
        rule.policy_version += 1
        audit(
            db,
            actor,
            "rule.review",
            rule.id,
            reason=cmd.reason,
            after=rule.policy_version,
            details={"clinical_approved": clinical, "decision": decision},
        )
        db.add(
            Outbox(
                kind="rule.qualification.changed",
                aggregate_id=rule.id,
                payload={"policy_version": rule.policy_version, "status": rule.status},
            )
        )
        return {**public(rule), "clinical_approved": clinical}

    return command(db, actor, "rule.review", rule.id, cmd, perform)


def candidate_graph(draft: OntologyDraft) -> Graph:
    """Turn the declared type-only candidate into a reviewed OWL definition module."""
    ontology = draft.ontology
    issues = validate_native(ontology)
    if any(i["blocking"] for i in issues):
        fail("draft_invalid", "候選定義或引用存在缺口。")
    if draft.loss_report:
        fail("semantic_loss", "導入存在未解決語義損失，不能發佈。")
    graph = Graph()
    graph.bind("owl", OWL)
    graph.bind("rdfs", RDFS)
    graph.bind("mq", Namespace("urn:mq:ontology:"))
    graph.add((URIRef("urn:mq:ontology"), RDF.type, OWL.Ontology))
    graph.add(
        (URIRef("urn:mq:ontology"), RDFS.label, Literal(ontology.get("name", "醫療應用本體"), lang="zh"))
    )
    uris = {n["id"]: URIRef(n.get("iri") or "urn:mq:ontology:" + n["id"]) for n in ontology["entityTypes"]}
    datatypes = {
        "string": XSD.string,
        "integer": XSD.integer,
        "decimal": XSD.decimal,
        "double": XSD.double,
        "date": XSD.date,
        "datetime": XSD.dateTime,
        "boolean": XSD.boolean,
        "enum": XSD.string,
    }
    for node in ontology["entityTypes"]:
        iri = uris[node["id"]]
        graph.add((iri, RDF.type, OWL.Class))
        graph.add((iri, RDFS.label, Literal(node["name"], lang="zh")))
        graph.add((iri, RDFS.comment, Literal(node["description"], lang="zh")))
        for prop in node.get("properties", []):
            p = URIRef(prop.get("iri") or "urn:mq:property:" + node["id"] + ":" + prop["name"])
            graph.add((p, RDF.type, OWL.DatatypeProperty))
            graph.add((p, RDFS.domain, iri))
            graph.add((p, RDFS.range, datatypes[prop["type"]]))
            graph.add((p, RDFS.label, Literal(prop["name"], lang="zh")))
    for edge in ontology["relationships"]:
        left, right = uris[edge["from"]], uris[edge["to"]]
        if edge.get("kind") == "subclass":
            graph.add((left, RDFS.subClassOf, right))
            continue
        iri = URIRef(edge.get("iri") or "urn:mq:relation:" + edge["id"])
        graph.add((iri, RDF.type, OWL.ObjectProperty))
        graph.add((iri, RDFS.domain, left))
        graph.add((iri, RDFS.range, right))
        graph.add((iri, RDFS.label, Literal(edge["name"], lang="zh")))
    return graph


def candidate_shapes(draft: OntologyDraft, base_path: Path) -> Graph:
    shapes = Graph().parse(base_path, format="turtle")
    nodes = {n["id"]: n for n in draft.ontology["entityTypes"]}

    def uri(key):
        return URIRef(nodes[key].get("iri") or "urn:mq:ontology:" + key)

    for node in nodes.values():
        for prop in node.get("properties", []):
            if not prop.get("isIdentifier") and not prop.get("values"):
                continue
            shape = URIRef("urn:mq:shape:" + digest([node["id"], prop["name"]])[:24])
            path = URIRef(prop.get("iri") or "urn:mq:property:" + node["id"] + ":" + prop["name"])
            shapes.add((shape, RDF.type, SH.PropertyShape))
            shapes.add((shape, SH.targetClass, uri(node["id"])))
            shapes.add((shape, SH.path, path))
            if prop.get("isIdentifier"):
                shapes.add((shape, SH.minCount, Literal(1)))
                shapes.add((shape, SH.maxCount, Literal(1)))
            if prop.get("values"):
                head = URIRef(str(shape) + ":values")
                Collection(shapes, head, [Literal(v) for v in prop["values"]])
                shapes.add((shape, SH["in"], head))
    for edge in draft.ontology["relationships"]:
        if edge.get("kind") == "subclass" or edge.get("cardinalityKnown") is False:
            continue
        meta = draft.metadata_map.get("edge_meta", {}).get(edge["id"], {})
        if meta.get("cardinality_status") == "unknown" and edge.get("cardinalityKnown") is not True:
            continue
        cardinality = edge["cardinality"]
        predicate = URIRef(edge.get("iri") or "urn:mq:relation:" + edge["id"])
        if cardinality in {"one-to-one", "many-to-one"}:
            shape = URIRef("urn:mq:shape:" + digest([edge["id"], "forward"])[:24])
            shapes.add((shape, RDF.type, SH.PropertyShape))
            shapes.add((shape, SH.targetClass, uri(edge["from"])))
            shapes.add((shape, SH.path, predicate))
            shapes.add((shape, SH.maxCount, Literal(1)))
        if cardinality in {"one-to-one", "one-to-many"}:
            shape = URIRef("urn:mq:shape:" + digest([edge["id"], "inverse"])[:24])
            inverse = URIRef(str(shape) + ":inverse")
            shapes.add((shape, RDF.type, SH.PropertyShape))
            shapes.add((shape, SH.targetClass, uri(edge["to"])))
            shapes.add((shape, SH.path, inverse))
            shapes.add((inverse, SH.inversePath, predicate))
            shapes.add((shape, SH.maxCount, Literal(1)))
    return shapes


def review_draft(db: Session, actor: Actor, draft_id: str, cmd: Command):
    require(actor, "knowledge_edit")
    if actor.role != "expert":
        fail("reviewer_role", "本體審核由獲指派專家執行。", 403)
    draft = db.scalar(select(OntologyDraft).where(OntologyDraft.id == draft_id).with_for_update())
    if not draft or draft.review.get("reviewer_id") != actor.id:
        fail("reviewer_assignment", "不是本候選的審核責任人。", 403)

    def perform():
        check_version(draft, cmd.expected_version)
        if draft.status != "in_review":
            fail("draft_state", "候選當前不在審核中。")
        decision = cmd.payload.get("decision")
        if decision not in {"approve", "reject"}:
            fail("review_decision", "審核結果無效。", 422)
        record = {
            "actor_id": actor.id,
            "actor_name": actor.name,
            "decision": decision,
            "reason": cmd.reason,
            "identity_mode": settings().mode,
        }
        if decision == "reject":
            draft.status = "draft"
            draft.version += 1
            draft.review = {**draft.review, "history": [*draft.review.get("history", []), record]}
            audit(db, actor, "ontology.review.return", draft.id, reason=cmd.reason, after=draft.version)
            return {**public(draft), "semantic_release_id": None, "clinical_approved": False}
        clinical = settings().mode == "production"
        if clinical:
            from .release import deployment_policy

            authority = deployment_policy().get("ontology_publication", {})
            if (
                not actor.oidc_subject
                or authority.get("candidate_digest") != digest(draft.ontology)
                or not authority.get("evaluation_ref")
                or not authority.get("approved_by")
            ):
                fail(
                    "clinical_release_prerequisites", "缺少同候選版本的真實身份、獨立本體評估及責任發佈記錄。"
                )
        graph = candidate_graph(draft)
        base = get_release(db, draft.base_release_id)
        release_id = "semantic-" + draft.id[:16] + "-v" + str(draft.version)
        root = settings().artifacts / "ontology"
        folder = root / release_id
        folder.mkdir(parents=True, exist_ok=True)
        for name in ["imports.json", "bindings.json", "mappings.sssom.tsv"]:
            original = root / base.id / name
            if not original.is_file():
                fail("base_package_missing", "原本體包資源不完整。")
            destination = folder / name
            if not destination.exists():
                destination.write_bytes(original.read_bytes())
        core = graph.serialize(format="turtle")
        target = folder / "core.ttl"
        if target.exists() and target.read_text() != core:
            fail("candidate_package_changed", "候選發佈目錄已有不同內容，需重新建立候選。")
        target.write_text(core)
        shape_graph = candidate_shapes(draft, root / base.id / "shapes.ttl")
        (folder / "shapes.ttl").write_text(shape_graph.serialize(format="turtle"))
        validation = validate_package(folder, source_dir=folder)
        if validation["profile"] != "pass" or validation["elk"] != "pass" or not validation["shacl_fixture"]:
            fail(
                "ontology_checks_failed",
                "OWL/ELK/SHACL 工程檢查未全部通過，候選未發佈。",
                validation=validation,
            )
        _, projected_meta = native_projection(graph)
        native = copy.deepcopy(draft.ontology)
        metadata = {"node_meta": {}, "edge_meta": {}}
        for node in native["entityTypes"]:
            metadata["node_meta"][node["id"]] = {
                "semantic_kind": "class",
                "original_iri": node.get("iri") or "urn:mq:ontology:" + node["id"],
                "source_ref": release_id + "/core.ttl",
                "approval_status": "approved" if clinical else "engineering_candidate",
            }
        for edge in native["relationships"]:
            metadata["edge_meta"][edge["id"]] = {
                "predicate_ref": edge.get("iri") or "urn:mq:relation:" + edge["id"],
                "cardinality_status": "unknown" if edge.get("cardinalityKnown") is False else "declared",
                "assertion_layer": "ontology_definition",
                "support_refs": [release_id + "/core.ttl"],
            }
        manifest = {
            key: digest((folder / name).read_bytes())
            for key, name in [
                ("core", "core.ttl"),
                ("shapes", "shapes.ttl"),
                ("mappings", "mappings.sssom.tsv"),
                ("bindings", "bindings.json"),
            ]
        }
        manifest.update(
            {
                "value_set": base.manifest["value_set"],
                "graph_metadata": metadata,
                "base_release_id": base.id,
                "draft_id": draft.id,
                "review": record,
                "bindings_view": base.manifest.get("bindings_view", []),
                "clinical_review": "approved" if clinical else "pending",
                "engineering_only": not clinical,
            }
        )
        published = SemanticRelease(
            id=release_id,
            name=draft.ontology["name"] + (" · 已批准版本" if clinical else " · 工程版本"),
            status="approved" if clinical else "engineering_ready",
            purpose="production" if clinical else "engineering",
            digest=validation["package_digest"],
            ontology=native,
            manifest=manifest,
            validation=validation,
        )
        db.add(published)
        draft.status = "engineering_released"
        draft.version += 1
        draft.review = {
            **draft.review,
            "history": [*draft.review.get("history", []), record],
            "release_id": release_id,
        }
        audit(
            db,
            actor,
            "ontology.publish",
            draft.id,
            reason=cmd.reason,
            after=draft.version,
            details={"semantic_release_id": release_id, "clinical_approved": clinical},
        )
        db.add(
            Outbox(
                kind="semantic.engineering_release.created",
                aggregate_id=release_id,
                payload={"base_release_id": base.id, "draft_id": draft.id},
            )
        )
        return {**public(draft), "semantic_release_id": release_id, "clinical_approved": clinical}

    return command(db, actor, "ontology.review", draft.id, cmd, perform)
