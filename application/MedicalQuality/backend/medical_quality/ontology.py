from __future__ import annotations

import json
import re
import os
import shutil
import subprocess
from pathlib import Path

from pyshacl import validate
from rdflib import Graph, Literal, Namespace, RDF, RDFS, OWL, URIRef
from sqlalchemy.orm import Session

from .common import digest, fail
from .config import PROJECT, settings
from .models import SemanticRelease

MQ = Namespace("urn:mq:ontology:")
ONTOLOGY_DIR = Path(__file__).parent / "clinical_context/ontology"
PALETTE = ["#0A84FF", "#30D158", "#BF5AF2", "#FF9F0A", "#64D2FF", "#FF375F", "#5E5CE6"]
ICONS = [
    "📁",
    "📋",
    "🔗",
    "👤",
    "🏥",
    "📄",
    "🗂️",
    "📝",
    "💬",
    "🧬",
    "🔬",
    "🧪",
    "💊",
    "📑",
    "🩺",
    "🖼️",
    "📖",
    "🔀",
    "📚",
    "🛡️",
    "🎯",
    "⚙️",
    "⚠️",
    "👩‍⚕️",
    "✍️",
    "🔏",
    "👥",
    "💠",
]


def label(graph: Graph, node) -> str:
    labels = list(graph.objects(node, RDFS.label))
    return str(
        next((v for v in labels if v.language == "zh"), labels[0] if labels else str(node).split(":")[-1])
    )


def native_projection(graph: Graph) -> tuple[dict, dict]:
    classes = sorted(set(graph.subjects(RDF.type, OWL.Class)), key=str)
    nodes = []
    meta = {}
    edges = []
    edge_meta = {}
    for i, uri in enumerate(classes):
        key = str(uri).split(":")[-1]
        nodes.append(
            {
                "id": key,
                "name": label(graph, uri),
                "description": str(graph.value(uri, RDFS.comment) or ""),
                "properties": [
                    {
                        "name": "id",
                        "type": "string",
                        "isIdentifier": True,
                        "description": "來源域內穩定記錄標識",
                    }
                ],
                "icon": ICONS[i % len(ICONS)],
                "color": PALETTE[i % len(PALETTE)],
            }
        )
        meta[key] = {
            "semantic_kind": "class",
            "original_iri": str(uri),
            "machine_name": key,
            "label_zh": label(graph, uri),
            "approval_status": "engineering_candidate",
            "source_ref": "PRD/PSC 與本地應用本體 0.1.0",
            "source_role": "schema_reference",
        }
    known = {n["id"] for n in nodes}
    for predicate in sorted(graph.subjects(RDF.type, OWL.ObjectProperty), key=str):
        left = graph.value(predicate, RDFS.domain)
        right = graph.value(predicate, RDFS.range)
        if left is None or right is None:
            continue
        src, dst = str(left).split(":")[-1], str(right).split(":")[-1]
        if src not in known or dst not in known:
            continue
        key = str(predicate).split(":")[-1]
        edges.append(
            {
                "id": key,
                "name": label(graph, predicate),
                "from": src,
                "to": dst,
                "cardinality": "many-to-many",
                "kind": "association",
                "description": "應用定義關係；未聲明臨床基數，見關係詳情。",
            }
        )
        edge_meta[key] = {
            "predicate_ref": str(predicate),
            "cardinality_status": "unknown",
            "assertion_layer": "ontology_definition",
            "source_ref": "core.ttl",
            "direction": "outgoing",
            "support_refs": ["core.ttl"],
        }
    for child, parent in graph.subject_objects(RDFS.subClassOf):
        src, dst = str(child).split(":")[-1], str(parent).split(":")[-1]
        if src in known and dst in known:
            key = f"subclass_{src}_{dst}"
            edges.append(
                {
                    "id": key,
                    "name": "屬於",
                    "from": src,
                    "to": dst,
                    "kind": "subclass",
                    "cardinality": "many-to-one",
                }
            )
            edge_meta[key] = {
                "predicate_ref": str(RDFS.subClassOf),
                "cardinality_status": "not_applicable",
                "assertion_layer": "ontology_definition",
                "support_refs": ["core.ttl"],
            }
    return {
        "name": "醫療病歷質控應用本體",
        "description": "術語、證據與責任的共同語義 · 工程候選 0.1.0",
        "entityTypes": nodes,
        "relationships": edges,
    }, {"node_meta": meta, "edge_meta": edge_meta}


def validate_package(output: Path, source_dir: Path | None = None) -> dict:
    source_dir = source_dir or ONTOLOGY_DIR
    package_files = ["core.ttl", "shapes.ttl", "imports.json", "bindings.json", "mappings.sssom.tsv"]
    output.mkdir(parents=True, exist_ok=True)
    for name in package_files:
        source = source_dir / name
        if source.is_file():
            target = output / source.name
            if target.exists() and target.read_bytes() != source.read_bytes():
                raise ValueError("已固定本體包內容變化，請使用新發布版本目錄")
            if not target.exists():
                target.write_bytes(source.read_bytes())
    Graph().parse(source_dir / "core.ttl", format="turtle")
    shapes = Graph().parse(source_dir / "shapes.ttl", format="turtle")
    sample = Graph()
    evidence = URIRef("urn:mq:fixture:evidence")
    assertion = URIRef("urn:mq:fixture:assertion")
    for triple in [
        (assertion, RDF.type, MQ.ClinicalAssertion),
        (assertion, MQ.subjectRole, Literal("patient")),
        (assertion, MQ.polarity, Literal("negated")),
        (assertion, MQ.temporality, Literal("current")),
        (assertion, MQ.hasEvidence, evidence),
        (assertion, MQ.documentVersion, Literal("fixture-v1")),
        (evidence, RDF.type, MQ.EvidenceReference),
        (evidence, MQ.sourceVersion, Literal("fixture-source-v1")),
        (evidence, MQ.locator, Literal("line:1")),
    ]:
        sample.add(triple)
    sample.add((assertion, URIRef("urn:mq:property:ClinicalAssertion:id"), Literal("fixture-assertion")))
    sample.add((evidence, URIRef("urn:mq:property:EvidenceReference:id"), Literal("fixture-evidence")))
    conforms, report, report_text = validate(
        sample, shacl_graph=shapes, advanced=False, js=False, inference="none"
    )
    (output / "shacl-report.ttl").write_text(report.serialize(format="turtle"))
    result = {
        "rdflib": True,
        "shacl_fixture": bool(conforms),
        "clinical_review": "pending",
        "profile": "not_run",
        "elk": "not_run",
        "scope": "engineering_fixture",
    }
    tools = PROJECT / ".runtime/tools"
    javas = list(tools.glob("*/Contents/Home/bin/java"))
    if os.name == "nt" and shutil.which("java"):
        javas = [shutil.which("java")]
    if javas and (tools / "robot.jar").exists():
        commands = [
            [
                "validate-profile",
                "--input",
                str(source_dir / "core.ttl"),
                "--profile",
                "EL",
                "--output",
                str(output / "profile.txt"),
            ],
            [
                "reason",
                "--input",
                str(source_dir / "core.ttl"),
                "--reasoner",
                "ELK",
                "--output",
                str(output / "classified.owl"),
            ],
        ]
        for key, args in zip(["profile", "elk"], commands):
            proc = subprocess.run(
                [str(javas[0]), "-Xmx512m", "-jar", str(tools / "robot.jar"), *args],
                capture_output=True,
                text=True,
                timeout=90,
            )
            (output / f"{key}.log").write_text(proc.stdout + proc.stderr)
            result[key] = "pass" if proc.returncode == 0 else "fail"
    result["package_digest"] = digest({name: (source_dir / name).read_text() for name in package_files})
    result["shape_fixture_scope"] = ["ClinicalAssertion", "EvidenceReference"]
    (output / "validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def get_release(db: Session, release_id: str, purpose="engineering") -> SemanticRelease:
    release = db.get(SemanticRelease, release_id)
    if not release or release.status not in {"engineering_ready", "approved"}:
        fail("semantic_release_unavailable", "所需本體版本不存在、失效或未就緒。")
    if purpose == "production" and (release.status != "approved" or release.purpose != "production"):
        fail("semantic_not_approved", "該本體只有工程驗證資格，尚未獲得臨床批准。")
    for key in ["core", "shapes", "mappings", "bindings", "value_set"]:
        if not release.manifest.get(key):
            fail("semantic_manifest_incomplete", "語義版本清單不完整。")
    return release


def concept_iris(release: SemanticRelease) -> set[str]:
    metadata = release.manifest.get("graph_metadata", {}).get("node_meta", {})
    return {
        node.get("iri") or metadata.get(node["id"], {}).get("original_iri") or "urn:mq:ontology:" + node["id"]
        for node in release.ontology["entityTypes"]
    }


def required_concept_iri(value: str) -> str:
    return value if ":" in value else "urn:mq:ontology:" + value


def resolve(db: Session, release_id: str, mentions: list[str], purpose="engineering") -> dict:
    release = get_release(db, release_id, purpose)
    found = []
    ambiguous = []
    missing = []
    for mention in mentions:
        matches = [e for e in release.ontology["entityTypes"] if mention in [e["id"], e["name"]]]
        if len(matches) == 1:
            found.append(matches[0])
        elif len(matches) > 1:
            ambiguous.append(mention)
        else:
            missing.append(mention)
    return {
        "requested_release": release_id,
        "actual_release": release.id,
        "concepts": found,
        "ambiguous": ambiguous,
        "unsupported": missing,
        "result_kind": "partial" if missing or ambiguous else "resolved",
        "support_refs": [release.manifest["core"]],
        "purpose": purpose,
    }


def validate_assertions(assertions: list[dict], *, shapes_path=None) -> dict:
    data = Graph()
    for a in assertions:
        node = URIRef("urn:mq:assertion:" + a["id"])
        data.add((node, RDF.type, MQ.ClinicalAssertion))
        data.add((node, URIRef("urn:mq:property:ClinicalAssertion:id"), Literal(a["id"])))
        for key, pred in [
            ("subject", "subjectRole"),
            ("polarity", "polarity"),
            ("temporality", "temporality"),
            ("document_id", "documentVersion"),
        ]:
            if key in a:
                data.add((node, MQ[pred], Literal(a[key])))
        for evidence in a.get("evidence_ids", []):
            data.add((node, MQ.hasEvidence, URIRef("urn:mq:evidence:" + evidence)))
    ok, report, text = validate(
        data,
        shacl_graph=str(shapes_path or ONTOLOGY_DIR / "shapes.ttl"),
        advanced=False,
        js=False,
        inference="none",
    )
    return {
        "conforms": bool(ok),
        "report": str(text),
        "assertions": len(assertions),
        "meaning": "數據形狀核對，不是臨床判斷",
    }


def pinned_shapes(release: SemanticRelease) -> Path:
    root = settings().artifacts / "ontology"
    path = (root / release.id / "shapes.ttl").resolve()
    if (
        not path.is_relative_to(root.resolve())
        or not path.is_file()
        or digest(path.read_bytes()) != release.manifest["shapes"]
    ):
        fail("semantic_shapes_unavailable", "固定語義版本的形狀資源缺失或摘要不匹配。")
    return path


def validate_native(ontology: dict) -> list[dict]:
    if (
        not isinstance(ontology, dict)
        or not isinstance(ontology.get("entityTypes"), list)
        or not isinstance(ontology.get("relationships"), list)
    ):
        fail("ontology_shape", "需要原生 ontology 對象。", 422)
    nodes = ontology["entityTypes"]
    edges = ontology["relationships"]
    issues = []
    if len(nodes) + len(edges) > 5000:
        fail("ontology_budget", "候選超過當前編輯預算，請按模塊導入。", 422)
    ids = [n.get("id") for n in nodes]
    if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        issues.append({"code": "duplicate_or_missing_id", "blocking": True})
    edge_ids = [e.get("id") for e in edges]
    if len(set(edge_ids)) != len(edge_ids) or set(ids) & set(edge_ids):
        issues.append({"code": "duplicate_graph_id", "blocking": True})
    for edge in edges:
        if edge.get("from") not in ids or edge.get("to") not in ids:
            issues.append({"code": "dangling_relation", "id": edge.get("id"), "blocking": True})
    for node in nodes:
        if not isinstance(node.get("properties", []), list):
            fail("property_shape", "屬性列表無效。", 422)
        for prop in node.get("properties", []):
            if (
                not isinstance(prop, dict)
                or not isinstance(prop.get("name"), str)
                or prop.get("type")
                not in {"string", "integer", "decimal", "double", "date", "datetime", "boolean", "enum"}
            ):
                fail("property_shape", "屬性名稱或類型不符合原生合同。", 422)
        if not node.get("name") or not node.get("description"):
            issues.append({"code": "definition_required", "id": node.get("id"), "blocking": True})
        if not re.fullmatch(r"[A-Za-z0-9]([A-Za-z0-9_-]{0,24}[A-Za-z0-9])?", node.get("name", "")):
            issues.append(
                {
                    "code": "fabric_name_incompatible",
                    "id": node.get("id"),
                    "blocking": False,
                    "message": "中文醫學名稱可保存；該名稱不符合 Fabric 導出約定。",
                }
            )
    return issues


def import_rdf(text: str, fmt: str) -> dict:
    if len(text.encode()) > 5 * 1024 * 1024:
        fail("import_budget", "本體文件超過 5 MiB 導入預算。", 422)
    if re.search(r"<!DOCTYPE|<!ENTITY", text, re.I):
        fail("external_entity", "不允許外部實體或 DTD。", 422)
    if fmt not in {"turtle", "xml", "json"}:
        fail("unsupported_format", "本體格式不支持。", 422)
    import_id = digest(text)
    folder = settings().artifacts / "ontology-imports"
    folder.mkdir(parents=True, exist_ok=True)
    original_path = folder / (import_id + "." + {"xml": "rdf", "turtle": "ttl", "json": "json"}[fmt])
    if not original_path.exists():
        original_path.write_text(text)
    original_ref = str(original_path.relative_to(settings().artifacts))
    if fmt == "json":
        try:
            value = json.loads(text)
        except ValueError:
            fail("json_invalid", "JSON 內容無效。", 422)
        ontology = value.get("ontology", value)
        issues = validate_native(ontology)
        if any(i["blocking"] for i in issues):
            fail("draft_invalid", "本體候選存在結構缺口。", 422, issues=issues)
        return {
            "ontology": ontology,
            "bindings": value.get("bindings", []),
            "node_meta": {},
            "edge_meta": {},
            "loss_report": [],
            "original_digest": import_id,
            "original_ref": original_ref,
            "status": "candidate",
            "format": fmt,
        }
    graph = Graph()
    try:
        graph.parse(data=text, format=fmt)
    except Exception:
        fail("rdf_parse_failed", "無法解析本體，請核對格式。", 422)
    ontology, meta = native_projection(graph)
    complex_predicates = [OWL.intersectionOf, OWL.unionOf, OWL.onProperty, OWL.equivalentClass, OWL.sameAs]
    loss = [
        {
            "predicate": str(p),
            "count": len(list(graph.triples((None, p, None)))),
            "reason": "not_represented_in_native_view",
        }
        for p in complex_predicates
        if (None, p, None) in graph
    ]
    if (
        fmt == "xml"
        and re.search(r'rdf:(?:about|resource)=["\'](?:#|\.\.?/)', text)
        and "xml:base=" not in text
    ):
        loss.append(
            {
                "reason": "relative_iri_base_unresolved",
                "message": "相對 IRI 缺少原始基準，不能當作已確定的絕對標識。",
            }
        )
    return {
        "ontology": ontology,
        **meta,
        "loss_report": loss,
        "original_digest": digest(text),
        "original_ref": original_ref,
        "format": fmt,
        "preserved_original": text,
        "status": "partial" if loss else "candidate",
    }
