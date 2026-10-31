from __future__ import annotations

import io
import json
from pathlib import Path
import zipfile

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .access import require, PERMISSIONS
from .common import audit, digest, fail, public
from .config import settings
from .models import Actor, Export, ReleaseRequest, Rule, SemanticRelease


def build_export(db: Session, actor: Actor, release_id: str):
    require(actor, "export_assets")
    gate = db.get(ReleaseRequest, release_id)
    if not gate:
        fail("gate_missing", "請先形成准入或未放行基線。", 422)
    rules = db.scalars(select(Rule).where(Rule.id.in_(gate.baseline.get("rule_ids", [])))).all()
    semantic = db.get(SemanticRelease, gate.baseline.get("semantic_release_id", ""))
    if not semantic:
        fail("semantic_missing", "交付基線缺少可回查語義版本。")
    from .evaluation import report

    summaries = [report(db, actor, bid, for_export=True) for bid in gate.baseline.get("batch_ids", [])]
    request_digest = digest(
        {
            "actor_id": actor.id,
            "gate_id": gate.id,
            "gate_version": gate.version,
            "baseline": gate.baseline,
            "rules": [(r.id, r.version, r.policy_version, r.status) for r in rules],
            "semantic_digest": semantic.digest,
            "evaluation": summaries,
        }
    )
    export_id = "export-" + request_digest[:32]
    db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": int(request_digest[:15], 16)})
    existing = db.get(Export, export_id)
    if existing:
        path = settings().artifacts / existing.artifact_ref
        if not path.is_file() or digest(path.read_bytes()) != existing.digest:
            fail("export_integrity", "已發佈包的資源缺失或損壞，先核查再重建。")
        return public(existing)
    files = {
        "rules.json": json.dumps([public(r) for r in rules], ensure_ascii=False, indent=2).encode(),
        "permissions.json": json.dumps(
            {k: sorted(v) for k, v in PERMISSIONS.items()}, ensure_ascii=False, indent=2
        ).encode(),
        "responsibility-flow.json": json.dumps(
            {
                "stages": [
                    "review",
                    "doctor",
                    "appeal",
                    "verification_pending",
                    "verify_ready",
                    "sign",
                    "signed",
                ],
                "terminal_alternative": "closed_false_positive",
                "clinical_state": "not_qualified",
                "source": "PSC-006/007",
            },
            ensure_ascii=False,
            indent=2,
        ).encode(),
        "semantic-manifest.json": json.dumps(
            public(semantic, ("ontology",)), ensure_ascii=False, indent=2
        ).encode(),
        "release.json": json.dumps(public(gate), ensure_ascii=False, indent=2).encode(),
    }
    for summary in summaries:
        files["evaluation/" + summary["batch_id"] + "-summary.json"] = json.dumps(
            summary, ensure_ascii=False, indent=2
        ).encode()
    package = settings().artifacts / "ontology" / semantic.id
    for filename, key in [
        ("core.ttl", "core"),
        ("shapes.ttl", "shapes"),
        ("bindings.json", "bindings"),
        ("mappings.sssom.tsv", "mappings"),
    ]:
        path = package / filename
        if not path.is_file() or digest(path.read_bytes()) != semantic.manifest[key]:
            fail("semantic_integrity", "交付引用的固定語義包缺失或被改動。")
        files["ontology/" + filename] = path.read_bytes()
    if (package / "imports.json").is_file():
        files["ontology/imports.json"] = (package / "imports.json").read_bytes()
    for path in (Path(__file__).resolve().parents[2] / "evals").glob("*.json"):
        files["engineering-evals/" + path.name] = path.read_bytes()
    notice = Path(__file__).resolve().parents[2] / "frontend/src/vendor/ontology-playground/UPSTREAM-LICENSE"
    if notice.exists():
        files["licenses/Ontology-Playground-MIT.txt"] = notice.read_bytes()
    manifest = {
        "schema_version": "1.0",
        "baseline": gate.baseline,
        "gate_request_id": gate.id,
        "gate_version": gate.version,
        "request_digest": request_digest,
        "gate_status": gate.status,
        "purpose": "engineering_handoff",
        "clinical_qualification": "not_granted",
        "included": [
            {"path": name, "sha256": digest(data), "bytes": len(data)} for name, data in files.items()
        ],
        "excluded": [
            "患者原文",
            "原始數據/影像",
            "參考答案/留出標註",
            "憑據/真實身份映射",
            "未獲分發權的外部詞表",
        ],
        "instructions": "驗證摘要/版本和使用許可；不得將工程候選直接激活為生產規則。",
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    raw = buffer.getvalue()
    folder = settings().artifacts / "exports"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (export_id + ".zip")
    temporary = path.with_suffix(".part")
    temporary.write_bytes(raw)
    temporary.replace(path)
    item = Export(
        id=export_id,
        actor_id=actor.id,
        status="ready",
        manifest=manifest,
        artifact_ref=str(path.relative_to(settings().artifacts)),
        digest=digest(raw),
        purpose="engineering_handoff",
    )
    db.add(item)
    db.flush()
    audit(
        db,
        actor,
        "asset.export",
        item.id,
        details={"baseline_id": gate.id, "digest": item.digest, "gate_status": gate.status},
    )
    return public(item)


def verify_export(raw: bytes):
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            names = archive.namelist()
            if any(Path(n).is_absolute() or ".." in Path(n).parts for n in names):
                raise ValueError("unsafe_path")
            if sum(i.file_size for i in archive.infolist()) > 20 * 1024 * 1024:
                raise ValueError("archive_budget")
            manifest = json.loads(archive.read("manifest.json"))
            if manifest.get("schema_version") != "1.0":
                raise ValueError("schema_incompatible")
            declared = [item["path"] for item in manifest["included"]]
            required = {
                "rules.json",
                "permissions.json",
                "responsibility-flow.json",
                "semantic-manifest.json",
                "release.json",
                "ontology/core.ttl",
                "ontology/shapes.ttl",
                "ontology/bindings.json",
                "ontology/mappings.sssom.tsv",
                "licenses/Ontology-Playground-MIT.txt",
            }
            if len(names) != len(set(names)) or len(declared) != len(set(declared)):
                raise ValueError("duplicate_entry")
            if set(names) != set(declared) | {"manifest.json"} or not required.issubset(declared):
                raise ValueError("missing_or_undeclared_dependency")
            for item in manifest["included"]:
                data = archive.read(item["path"])
                if digest(data) != item["sha256"] or len(data) != item["bytes"]:
                    raise ValueError("digest_mismatch")
            baseline = manifest["baseline"]
            semantic = json.loads(archive.read("semantic-manifest.json"))
            release = json.loads(archive.read("release.json"))
            rules = json.loads(archive.read("rules.json"))
            if semantic["id"] != baseline["semantic_release_id"] or release["baseline"] != baseline:
                raise ValueError("baseline_mismatch")
            if {r["id"] for r in rules} != set(baseline["rule_ids"]):
                raise ValueError("rule_dependency_mismatch")
            for filename, key in [
                ("core.ttl", "core"),
                ("shapes.ttl", "shapes"),
                ("bindings.json", "bindings"),
                ("mappings.sssom.tsv", "mappings"),
            ]:
                if digest(archive.read("ontology/" + filename)) != semantic["manifest"][key]:
                    raise ValueError("semantic_dependency_mismatch")
            for batch_id in baseline.get("batch_ids", []):
                if "evaluation/" + batch_id + "-summary.json" not in declared:
                    raise ValueError("evaluation_dependency_missing")
            return {"status": "valid", "manifest": manifest, "activated": False}
    except (ValueError, KeyError, TypeError, zipfile.BadZipFile):
        return {"status": "invalid", "reason": "schema_digest_or_dependency_invalid", "activated": False}
