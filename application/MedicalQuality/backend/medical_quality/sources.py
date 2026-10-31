from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from .access import require
from .common import audit, fail, public
from .config import settings
from .models import Actor, Source, SourceSnapshot, uid

CATALOGUE = [
    {
        "key": "hospital",
        "name": "醫院結構化資料",
        "path": "01_醫院結構化數據/醫院結構化數據.sqlite",
        "format": "sqlite",
        "namespace": "hospital_demo",
        "role": "business_evidence",
        "kind": "public_deidentified",
        "license": "ODbL-1.0",
    },
    {
        "key": "cmqcic",
        "name": "中文病例原文",
        "path": "02_病例文本/CMQCIC-病例.jsonl.gz",
        "format": "jsonl.gz",
        "namespace": "cmqcic",
        "role": "business_evidence",
        "kind": "public",
        "license": "CC BY-NC 4.0；本地參考研究",
    },
    {
        "key": "pmc",
        "name": "文獻病例敘述",
        "path": "02_病例文本/PMC-Patients.jsonl.gz",
        "format": "jsonl.gz",
        "namespace": "pmc_patients",
        "role": "business_evidence",
        "kind": "literature",
        "license": "CC BY-NC-SA 4.0；本地參考研究",
    },
    {
        "key": "rules",
        "name": "中文質控參考規則",
        "path": "03_質控規則與參考標註/CMQCIC-規則.json",
        "format": "json",
        "namespace": "cmqcic_rules",
        "role": "rule_reference",
        "kind": "public",
        "license": "CC BY-NC 4.0；不是已批准規則",
    },
    {
        "key": "pdf2016",
        "name": "病案首頁規範 · 2016",
        "path": "03_質控規則與參考標註/住院病案首頁數據填寫質量規範-2016.pdf",
        "format": "pdf",
        "namespace": "nhc_2016",
        "role": "rule_reference",
        "kind": "public",
        "license": "官方公開參考；適用性尚待專業審核",
    },
    {
        "key": "table_catalog",
        "name": "醫院表結構目錄",
        "path": "01_醫院結構化數據/表目錄.csv",
        "format": "csv",
        "namespace": "hospital_catalog",
        "role": "schema_reference",
        "kind": "public_deidentified",
        "license": "ODbL-1.0",
    },
]


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def source_path(reference: str) -> Path:
    prefix, sep, relative = reference.partition(":")
    roots = {
        "data": settings().data_root,
        "upload": settings().artifacts / "uploads",
        "synthetic": settings().artifacts / "synthetic",
        "revision": settings().artifacts / "document_revisions",
    }
    if not sep or prefix not in roots or Path(relative).is_absolute():
        fail("source_reference_invalid", "資料引用不屬於已批准的本地入口。", 422)
    root = roots[prefix].resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        fail("source_unavailable", "資料路徑不可用。", 422)
    return path


def detect_format(path: Path) -> str:
    with path.open("rb") as stream:
        prefix = stream.read(64)
    if prefix.startswith(b"%PDF-"):
        return "pdf"
    if prefix.startswith(b"SQLite format 3"):
        return "sqlite"
    if prefix.startswith(b"\x1f\x8b"):
        return "jsonl.gz" if path.name.endswith(".jsonl.gz") else "unsupported"
    suffix = path.suffix.lower()
    return {
        ".csv": "csv",
        ".json": "json",
        ".jsonl": "jsonl",
        ".md": "markdown",
        ".txt": "text",
        ".xml": "xml",
        ".xlsx": "xlsx",
        ".png": "image",
        ".jpg": "image",
        ".hea": "waveform",
    }.get(suffix, "unsupported")


def register(db: Session, actor: Actor, *, key: str | None = None, upload: dict | None = None):
    require(actor, "source_register" if actor.role == "info" else "sources")
    entry = next((x for x in CATALOGUE if x["key"] == key), None) if key else upload
    if not entry:
        fail("source_not_allowed", "請選擇已登記入口或上傳文件。", 422)
    if entry["role"] in {"reference_label", "heldout", "validation"}:
        fail("evaluator_only", "評測資料必須通過獨立評測入口登記。", 403)
    reference = "data:" + entry["path"] if key else entry["reference"]
    path = source_path(reference)
    sha = hash_file(path)
    fmt = detect_format(path)
    existing = db.scalar(
        select(Source)
        .where(Source.reference == reference, Source.namespace == entry["namespace"])
        .with_for_update()
    )
    if existing and existing.digest == sha:
        audit(db, actor, "source.duplicate", existing.id, details={"source_version": existing.version})
        return public(existing)
    if existing:
        existing.version += 1
        existing.digest = sha
        existing.status = "registered"
        source = existing
    else:
        source = Source(
            id=uid(),
            name=entry["name"],
            namespace=entry["namespace"],
            reference=reference,
            format=fmt,
            data_role=entry["role"],
            data_kind=entry["kind"],
            purpose="research" if key else "engineering",
            license=entry["license"],
            status="registered",
            digest=sha,
            scope={},
            details={"bytes": path.stat().st_size, "path_base": reference.partition(":")[0]},
        )
        db.add(source)
    db.flush()
    db.add(
        SourceSnapshot(
            source_id=source.id,
            version=source.version,
            digest=sha,
            reference=reference,
            manifest={
                "format": fmt,
                "namespace": source.namespace,
                "data_role": source.data_role,
                "data_kind": source.data_kind,
                "license": source.license,
                "path_base": source.details["path_base"],
                "consistency": "file_digest",
            },
        )
    )
    audit(
        db,
        actor,
        "source.register",
        source.id,
        after=source.version,
        details={"format": fmt, "data_kind": source.data_kind, "data_role": source.data_role},
    )
    return public(source)


@contextmanager
def read_database(path: Path):
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    connection.enable_load_extension(False)
    allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE}
    connection.set_authorizer(
        lambda op, a, b, c, d: (
            sqlite3.SQLITE_OK
            if op in allowed or (op == sqlite3.SQLITE_PRAGMA and a == "table_info")
            else sqlite3.SQLITE_DENY
        )
    )
    steps = 0

    def progress():
        nonlocal steps
        steps += 1
        return int(steps > 50_000)

    connection.set_progress_handler(progress, 1000)
    try:
        yield connection
    finally:
        connection.close()


def schema_catalog(path: Path) -> list[dict]:
    with read_database(path) as connection:
        names = [
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        ]
        out = []
        # pragma_table_info is a SELECT table-valued function, not arbitrary PRAGMA input.
        for name in names:
            fields = [dict(row) for row in connection.execute("SELECT * FROM pragma_table_info(?)", (name,))]
            out.append(
                {
                    "table": name,
                    "columns": fields,
                    "namespace": name.split("__")[0],
                    "identity_scope": "snapshot",
                    "foreign_keys_declared": False,
                }
            )
        return out


def fixed_records(path: Path, table: str, limit: int, offset: int = 0) -> list[dict]:
    with read_database(path) as connection:
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if table not in names:
            fail("table_not_allowed", "表名不在此快照結構目錄中。", 422)
        quoted = '"' + table.replace('"', '""') + '"'
        return [
            dict(row)
            for row in connection.execute(
                f"SELECT * FROM {quoted} LIMIT ? OFFSET ?", (min(limit, 500), offset)
            )
        ]


def source_for_read(db: Session, actor: Actor, source_id: str, version: int) -> tuple[Source, Path]:
    source = db.get(Source, source_id)
    if not source:
        fail("not_found", "資料不存在或不可訪問。", 404)
    require(actor, "parse" if actor.role == "info" else "sources", purpose=source.purpose)
    if source.data_role in {"reference_label", "validation", "heldout"}:
        fail("evaluator_only", "該資料不允許進入建設和運行管線。", 403)
    snapshot = db.scalar(
        select(SourceSnapshot).where(SourceSnapshot.source_id == source_id, SourceSnapshot.version == version)
    )
    if not snapshot:
        fail("source_version_missing", "來源版本不可用。", 409)
    path = source_path(snapshot.reference)
    if hash_file(path) != snapshot.digest:
        fail("source_changed", "原件已變化，無法以舊摘要讀取；請登記新版本。")
    return source, path
