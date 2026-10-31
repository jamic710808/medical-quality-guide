from __future__ import annotations

import csv
import gzip
import importlib.metadata
import json
from pathlib import Path
import re

from defusedxml import ElementTree
from jsonschema import Draft202012Validator, ValidationError
from sqlalchemy.orm import Session

from .common import audit, digest, fail
from .config import settings
from .models import Actor, Document, Evidence, Source, SourceSnapshot, uid
from .sources import fixed_records, schema_catalog, source_for_read

SCHEMA = json.loads((Path(__file__).parent / "schemas/evidence-item.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)


def validate_envelope(item: dict):
    try:
        VALIDATOR.validate(item)
    except ValidationError as exc:
        raise ValueError("EvidenceItem 結構不符合合同：" + exc.json_path) from None
    locator = item["locator"]
    if locator["type"] == "text" and locator["line_end"] < locator["line_start"]:
        raise ValueError("文本行範圍倒置")
    if "char_end" in locator and locator["char_end"] < locator["char_start"]:
        raise ValueError("字符範圍倒置")
    if (
        item["source"]["data_role"] in {"reference_label", "validation", "heldout"}
        and item["quality"]["modeling_access"] == "allowed"
    ):
        raise ValueError("受限評測資料不能獲得建設權限")


def envelope(
    source: Source,
    version: int,
    run_id: str,
    kind: str,
    locator: dict,
    content: dict,
    *,
    tool="medical-quality-reader",
    tool_version="0.1.0",
    status="success",
    issues=None,
    transformations=None,
):
    role = source.data_role
    item = {
        "schema_version": "1.0",
        "id": uid(),
        "kind": kind,
        "source": {
            "id": source.id,
            "uri": source.reference,
            "version": str(version),
            "format": source.format,
            "data_role": role,
            "data_kind": source.data_kind,
            "authorized_use": source.purpose,
        },
        "locator": locator,
        "content": content,
        "provenance": {
            "tool": tool,
            "tool_version": tool_version,
            "run_id": run_id,
            "transformations": transformations or [],
        },
        "quality": {
            "status": status,
            "issues": issues or [],
            "modeling_access": "evaluator_only"
            if role in {"reference_label", "validation", "heldout"}
            else ("allowed" if status == "success" and source.data_kind != "unknown" else "restricted"),
        },
    }
    if status == "partial":
        item["quality"]["usable_scope"] = "僅保留當前可回放的原值與位置；存在的問題未經解決不得自動消費。"
    if source.data_kind == "unknown":
        item["quality"]["issues"].append("source_kind_unconfirmed")
    if kind in {"image", "waveform"}:
        item["native_refs"] = [source.uri if hasattr(source, "uri") else source.reference]
    validate_envelope(item)
    return item


def document_source(db: Session, parent: Source, document: Document) -> Source:
    """The locator basis is immutable document text, never the JSON wrapper or an older source."""
    directory = settings().artifacts / "document_revisions"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (document.id + ".txt")
    raw = document.content.encode("utf-8")
    if path.exists() and path.read_bytes() != raw:
        raise ValueError("固定文書資源不能覆蓋")
    if not path.exists():
        path.write_bytes(raw)
    key = "document-source-" + document.id
    source = db.get(Source, key)
    if source:
        return source
    source = Source(
        id=key,
        version=1,
        name=document.title + " · " + document.id[:12],
        namespace=parent.namespace,
        reference="revision:" + path.name,
        format="text",
        data_role="business_evidence",
        data_kind=parent.data_kind,
        purpose=parent.purpose,
        license=parent.license,
        status="success",
        digest=digest(raw),
        scope={"case_id": document.case_id},
        details={
            "path_base": "revision",
            "internal_document": True,
            "document_id": document.id,
            "document_version": document.version,
            "author_id": document.author_id,
            "derived_from": {"source_id": parent.id, "source_version": parent.version},
        },
    )
    db.add(source)
    db.flush()
    db.add(
        SourceSnapshot(
            source_id=source.id,
            version=1,
            digest=source.digest,
            reference=source.reference,
            manifest={
                "document_id": document.id,
                "document_version": document.version,
                "parent_source": parent.id,
                "data_kind": parent.data_kind,
                "locator_basis": "exact_utf8_document_text",
            },
        )
    )
    return source


def document_evidence(
    db: Session, source: Source, document: Document, run_id="document-ingest"
) -> list[Evidence]:
    source = document_source(db, source, document)
    items = []
    offset = 0
    for number, line in enumerate(document.content.splitlines(keepends=True), 1):
        value = line.rstrip("\r\n")
        if value.strip():
            item = envelope(
                source,
                source.version,
                run_id,
                "text",
                {
                    "type": "text",
                    "line_start": number,
                    "line_end": number,
                    "char_start": offset,
                    "char_end": offset + len(value),
                },
                {"text": value, "metadata": {"document_version": document.version}},
            )
            item["provenance"]["transformations"] = [
                "physician_submitted_revision" if document.parent_id else "materialize_source_document_text"
            ]
            evidence = Evidence(
                id=item["id"],
                case_id=document.case_id,
                source_id=source.id,
                source_version=source.version,
                document_id=document.id,
                data_role="business_evidence",
                envelope=item,
            )
            db.add(evidence)
            items.append(evidence)
        offset += len(line)
    db.flush()
    return items


def parse_file(source: Source, path: Path, version: int, run_id: str, scope: dict) -> dict:
    limit = scope.get("limit", 100)
    if not isinstance(limit, int) or isinstance(limit, bool) or not 0 <= limit <= 500:
        fail("parse_scope_invalid", "讀取條數須為 0～500 的整數；不能擴大或猜測請求範圍。", 422)
    if limit == 0:
        return {
            "items": [],
            "failures": [],
            "status": "empty",
            "coverage": {
                "unit": "declared_scope",
                "expected_total": 0,
                "completed": 0,
                "failed": 0,
                "unread": 0,
                "declared_scope": scope,
                "source_total": None,
            },
        }
    items, failures = [], []
    expected = None
    truncated = False

    def add(kind, locator, content, **kwargs):
        items.append(envelope(source, version, run_id, kind, locator, content, **kwargs))

    fmt = source.format
    if fmt == "sqlite":
        tables = schema_catalog(path)
        selected = scope.get("table")
        if selected:
            table = next((x for x in tables if x["table"] == selected), None)
            if not table:
                fail("table_not_allowed", "請求的表不在已讀目錄中。", 422)
            add(
                "schema",
                {"type": "database", "table": selected},
                {"columns": table["columns"], "metadata": table},
            )
            rows = fixed_records(path, selected, limit + 1)
            truncated = len(rows) > limit
            for i, row in enumerate(rows[:limit], 1):
                key = row.get("_source_record_number")
                locator = {
                    "type": "database",
                    "table": selected,
                    "row_ordinal": i,
                    "identity_scope": "snapshot",
                }
                if key is not None:
                    locator["row_key"] = {"_source_record_number": key}
                add(
                    "record",
                    locator,
                    {
                        "value": row,
                        "metadata": {"namespace": table["namespace"], "source_values": "unchanged"},
                    },
                )
        else:
            expected = len(tables)
            for table in tables:
                add(
                    "schema",
                    {"type": "database", "table": table["table"]},
                    {"columns": table["columns"], "metadata": table},
                )
    elif fmt in {"jsonl", "jsonl.gz"}:
        opener = gzip.open if fmt.endswith(".gz") else open
        with opener(path, "rt", encoding="utf-8-sig") as stream:
            for i, line in enumerate(stream, 1):
                if i > limit:
                    truncated = True
                    break
                try:
                    row = json.loads(line)
                    content = {"value": row}
                    if isinstance(row, dict) and isinstance(row.get("text"), str):
                        content["text"] = row["text"]
                    add("record", {"type": "json", "pointer": "", "record_number": i}, content)
                except (ValueError, TypeError):
                    failures.append({"unit": i, "reason": "invalid_json_record"})
        if not truncated:
            expected = len(items) + len(failures)
    elif fmt == "json":
        if path.stat().st_size > 20 * 1024 * 1024:
            fail("input_budget", "JSON 超出本次結構讀取預算，請使用流式 JSONL。", 422)
        obj = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(obj, dict):
            entries = list(obj.items())
        elif isinstance(obj, list):
            entries = list(enumerate(obj))
        else:
            entries = [(None, obj)]
        expected = len(entries)
        truncated = expected > limit
        for key, value in entries[:limit]:
            pointer = "" if key is None else "/" + str(key).replace("~", "~0").replace("/", "~1")
            add("record", {"type": "json", "pointer": pointer}, {"value": value})
    elif fmt == "csv":
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream)
            headers = next(reader)
            for i, row in enumerate(reader, 1):
                if i > limit:
                    truncated = True
                    break
                malformed = len(row) != len(headers) or len(set(headers)) != len(headers)
                add(
                    "record",
                    {"type": "csv", "record_number": i},
                    {"columns": [{"name": x, "index": j} for j, x in enumerate(headers)], "value": row},
                    status="partial" if malformed else "success",
                    issues=["column_shape_or_duplicate_header"] if malformed else [],
                )
        expected = None if truncated else len(items)
    elif fmt == "markdown":
        from markdown_it import MarkdownIt

        with path.open(encoding="utf-8-sig", newline="") as stream:
            text = stream.read()
        tokens = MarkdownIt("commonmark").enable("table").parse(text)
        raw_lines = text.splitlines(keepends=True)
        offsets = [0]
        for line in raw_lines:
            offsets.append(offsets[-1] + len(line))
        folder = settings().artifacts / "parsing" / run_id
        folder.mkdir(parents=True, exist_ok=True)
        native = folder / "markdown-ast.json"
        native.write_text(json.dumps([t.as_dict() for t in tokens], ensure_ascii=False))
        heading = []
        blocks = [(i, t) for i, t in enumerate(tokens) if t.level == 0 and t.map and t.nesting != -1]
        expected = len(blocks)
        truncated = expected > limit
        for index, token in blocks[:limit]:
            start, end = token.map
            if token.type == "heading_open":
                level = int(token.tag[1:])
                title = tokens[index + 1].content
                heading = heading[: level - 1] + [title]
            content = {
                "text": text[offsets[start] : offsets[end]],
                "payload_ref": str(native.relative_to(settings().artifacts)),
                "metadata": {
                    "block_type": token.type,
                    "heading_path": heading.copy(),
                    "native_ref": f"/tokens/{index}",
                    "line_ending_preserved": True,
                    "offset_basis": "decoded_unicode_without_bom",
                },
            }
            if token.type == "table_open":
                rows = []
                row = []
                for child in tokens[index + 1 :]:
                    if child.type == "table_close":
                        break
                    if child.type == "tr_open":
                        row = []
                    elif child.type == "inline":
                        row.append(child.content)
                    elif child.type == "tr_close":
                        rows.append(row)
                content["rows"] = rows
                content["metadata"]["header_rows"] = 1
            add(
                "table" if token.type == "table_open" else "text",
                {
                    "type": "text",
                    "line_start": start + 1,
                    "line_end": end,
                    "char_start": offsets[start],
                    "char_end": offsets[end],
                },
                content,
                tool="markdown-it-py",
                tool_version=importlib.metadata.version("markdown-it-py"),
                transformations=["parse_markdown_ast"],
            )
    elif fmt == "text":
        with path.open(encoding="utf-8-sig", newline="") as stream:
            text = stream.read()
        heading, offset = [], 0
        for i, line in enumerate(text.splitlines(keepends=True), 1):
            value = line.rstrip("\r\n")
            match = re.match(r"^(#{1,6})\s+(.+)$", value)
            if match:
                heading = heading[: len(match[1]) - 1] + [match[2]]
            if value:
                add(
                    "text",
                    {
                        "type": "text",
                        "line_start": i,
                        "line_end": i,
                        "char_start": offset,
                        "char_end": offset + len(value),
                    },
                    {"text": value, "metadata": {"heading_path": heading.copy()}},
                )
            offset += len(line)
        expected = len(items)
    elif fmt == "xml":
        if path.stat().st_size > 10 * 1024 * 1024:
            fail("input_budget", "XML 超出解析預算。", 422)
        tree = ElementTree.parse(path)
        root = tree.getroot()
        for i, child in enumerate(root.iter(), 1):
            value = "".join(child.itertext()).strip()
            if len(child) == 0 and value:
                add(
                    "text",
                    {
                        "type": "xml",
                        "xpath": f"(//{child.tag})[{sum(1 for x in list(root.iter())[:i] if x.tag == child.tag)}]",
                    },
                    {"text": value, "metadata": {"tag": child.tag, "attributes": child.attrib}},
                )
        expected = len(items)
    elif fmt == "pdf":
        return parse_pdf(source, path, version, run_id, scope)
    elif fmt == "xlsx":
        import openpyxl
        from datetime import date, datetime, time
        from openpyxl.utils import get_column_letter

        book = openpyxl.load_workbook(path, read_only=True, data_only=False, keep_links=False)
        cached = openpyxl.load_workbook(path, read_only=True, data_only=True, keep_links=False)

        def cell_value(value):
            return (
                {"type": type(value).__name__, "iso": value.isoformat()}
                if isinstance(value, (date, datetime, time))
                else value
            )

        try:
            expected = len(book.sheetnames)
            for sheet in book:
                if scope.get("sheet") and sheet.title != scope["sheet"]:
                    continue
                if sheet.max_column > 2000:
                    fail("sheet_budget", "工作表列數超出結構讀取預算。", 422)
                rows = []
                cells = []
                formulas = False
                for row in sheet.iter_rows(max_row=min(sheet.max_row, limit)):
                    row_values = []
                    for cell in row:
                        value = cell.value
                        row_values.append(cell_value(value))
                        if value is not None:
                            formulas = formulas or cell.data_type == "f"
                            cells.append(
                                {
                                    "coordinate": cell.coordinate,
                                    "raw_value": cell_value(value),
                                    "data_type": cell.data_type,
                                    "number_format": cell.number_format,
                                    "cached_value": cell_value(cached[sheet.title][cell.coordinate].value)
                                    if cell.data_type == "f"
                                    else None,
                                }
                            )
                    rows.append(row_values)
                partial = sheet.max_row > limit or formulas
                if sheet.max_row > limit:
                    truncated = True
                add(
                    "table",
                    {
                        "type": "spreadsheet",
                        "sheet": sheet.title,
                        "range": f"A1:{get_column_letter(max(1, sheet.max_column))}{max(1, min(sheet.max_row, limit))}",
                    },
                    {
                        "rows": rows,
                        "payload_ref": source.reference,
                        "metadata": {
                            "sheet_names": book.sheetnames,
                            "cells": cells,
                            "formulas_executed": False,
                            "cached_values_may_be_stale": formulas,
                            "row_total": sheet.max_row,
                        },
                    },
                    status="partial" if partial else "success",
                    issues=(["formula_cache_requires_review"] if formulas else [])
                    + (["sheet_rows_not_fully_read"] if sheet.max_row > limit else []),
                    tool="openpyxl",
                    tool_version=importlib.metadata.version("openpyxl"),
                )
        finally:
            book.close()
            cached.close()
    elif fmt == "image":
        from PIL import Image

        with Image.open(path) as image:
            metadata = {
                "width": image.width,
                "height": image.height,
                "mode": image.mode,
                "format": image.format,
                "frames": getattr(image, "n_frames", 1),
                "decoded_for_metadata_only": True,
                "diagnostic_interpretation": False,
            }
            image.verify()
        add(
            "image",
            {"type": "image", "frame": 0},
            {"payload_ref": source.reference, "metadata": metadata},
            status="partial",
            issues=["metadata_only_no_clinical_interpretation"],
        )
        expected = 1
    elif fmt == "waveform":
        import wfdb

        lines = path.read_text(encoding="utf-8").splitlines()
        try:
            header = wfdb.rdheader(str(path.with_suffix("")))
            channel_count = header.n_sig
            frequency = float(header.fs)
            sample_count = header.sig_len
            if not 1 <= channel_count <= 64 or frequency <= 0 or sample_count < 1:
                raise ValueError()
        except (ValueError, IndexError, TypeError):
            fail("waveform_header_invalid", "WFDB 頭字段不完整或無效。", 422)
        channels = header.sig_name
        if len(channels) != channel_count:
            fail("waveform_channel_mismatch", "聲明通道數與頭字段不一致。", 422)
        add(
            "waveform",
            {
                "type": "waveform",
                "record": header.record_name,
                "start_sample": 0,
                "end_sample": sample_count,
                "channels": channels,
                "sample_frequency_hz": frequency,
            },
            {
                "payload_ref": source.reference,
                "metadata": {
                    "header_lines": lines,
                    "sample_count": sample_count,
                    "channels": channel_count,
                    "sample_frequency_hz": frequency,
                    "paired_dat_available": path.with_suffix(".dat").is_file(),
                    "units": header.units,
                    "adc_gain": header.adc_gain,
                    "baseline": header.baseline,
                    "signal_formats": header.fmt,
                    "signal_decoded": False,
                    "values_decoded": False,
                    "diagnostic_interpretation": False,
                },
            },
            status="partial",
            issues=["header_only_signal_not_decoded"],
            tool="wfdb.rdheader",
            tool_version=importlib.metadata.version("wfdb"),
        )
        expected = 1
    else:
        failures.append({"unit": path.name, "reason": "unsupported_format", "format": fmt})
    return {
        "items": items,
        "failures": failures,
        "coverage": {
            "unit": "evidence_unit",
            "expected_total": expected,
            "completed": len([x for x in items if x["quality"]["status"] == "success"]),
            "partial": len([x for x in items if x["quality"]["status"] == "partial"]),
            "failed": len(failures),
            "truncated": truncated,
            "declared_scope": scope,
        },
        "status": "partial"
        if failures or truncated or any(x["quality"]["status"] != "success" for x in items)
        else "success",
    }


def coverage_summary(results: list[dict], declared_total: int | None) -> dict:
    """按已聲明讀取單元彙總，不把不同格式的行/頁數相加成病例數量。"""
    counts = {"success": 0, "partial": 0, "failed": 0, "blocked": 0, "empty": 0, "not_run": 0}
    for result in results:
        status = result.get("status", "not_run")
        counts[status if status in counts else "not_run"] += 1
    if declared_total is not None:
        if declared_total < len(results):
            fail("coverage_scope_mismatch", "結果單元超出聲明範圍。", 422)
        counts["not_run"] += declared_total - len(results)
    complete = declared_total is not None and counts["success"] + counts["empty"] == declared_total
    return {
        "unit": "source_read_unit",
        "expected_total": declared_total,
        "observed_units": len(results),
        "counts": counts,
        "status": "empty" if declared_total == 0 else ("success" if complete else "partial"),
        "completion_ratio": (counts["success"] + counts["empty"]) / declared_total
        if declared_total
        else None,
        "meaning": "僅表示聲明讀取單元，不表示建模資格、完整病歷或臨床通過",
    }


def parse_pdf(source, path, version, run_id, scope):
    """Docling is the authoritative PDF path; missing local artifacts fail closed."""
    artifacts = settings().artifacts / "models/docling"
    if not artifacts.exists():
        return {
            "items": [],
            "failures": [
                {"unit": str(scope.get("page_range", "all")), "reason": "docling_artifacts_unavailable"}
            ],
            "coverage": {
                "unit": "page",
                "expected_total": None,
                "completed": 0,
                "failed": 0,
                "blocked": 1,
                "declared_scope": scope,
            },
            "status": "blocked",
        }
    try:
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions

        options = PdfPipelineOptions(artifacts_path=artifacts, do_ocr=True, do_table_structure=True)
        ocr_root = settings().artifacts / "models/rapidocr"
        required = [
            ocr_root / name
            for name in [
                "ch_PP-OCRv4_det_infer.onnx",
                "ch_PP-OCRv4_rec_infer.onnx",
                "ch_ppocr_mobile_v2.0_cls_infer.onnx",
            ]
        ]
        if not all(p.exists() for p in required):
            raise RuntimeError("ocr_artifacts_unavailable")
        options.ocr_options = RapidOcrOptions(
            backend="onnxruntime",
            det_model_path=str(required[0]),
            rec_model_path=str(required[1]),
            cls_model_path=str(required[2]),
        )
        converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
        )
        max_pages = min(int(scope.get("max_pages", 20)), 100)
        result = converter.convert(path, max_num_pages=max_pages, raises_on_error=False)
        from pypdf import PdfReader

        source_pages = PdfReader(path).pages
        native = result.document.export_to_dict()
        target = settings().artifacts / "parsing" / run_id
        target.mkdir(parents=True, exist_ok=True)
        (target / "docling.json").write_text(json.dumps(native, ensure_ascii=False))
        items = []
        restricted_pages = set()
        for element, level in result.document.iterate_items():
            if not getattr(element, "prov", None):
                continue
            for prov in element.prov:
                box = prov.bbox
                locator = {
                    "type": "pdf",
                    "page": prov.page_no,
                    "bbox": [box.l, box.t, box.r, box.b],
                    "unit": "pt",
                    "origin": "bottom_left"
                    if str(box.coord_origin).lower().endswith("bottomleft")
                    else "top_left",
                }
                table = element.__class__.__name__ == "TableItem"
                content = {
                    "text": getattr(element, "text", ""),
                    "payload_ref": str((target / "docling.json").relative_to(settings().artifacts)),
                    "metadata": {
                        "native_ref": getattr(element, "self_ref", None),
                        "label": str(getattr(element, "label", "")),
                    },
                }
                if table:
                    content["rows"] = element.export_to_dataframe(doc=result.document).values.tolist()
                rotation = int(source_pages[prov.page_no - 1].rotation) % 360
                review_table = table and rotation != 0
                content["metadata"]["source_page_rotation"] = rotation
                if review_table:
                    content["metadata"]["table_structure_status"] = "orientation_requires_review"
                    restricted_pages.add(prov.page_no)
                items.append(
                    envelope(
                        source,
                        version,
                        run_id,
                        "table" if table else "text",
                        locator,
                        content,
                        tool="docling+rapidocr-onnx",
                        tool_version=importlib.metadata.version("docling"),
                        transformations=["layout_analysis", "ocr_when_required"],
                        status="partial" if review_table else "success",
                        issues=["rotated_table_requires_structure_review"] if review_table else None,
                    )
                )
        result_status = str(result.status.value)
        ok = result_status == "success"
        return {
            "items": items,
            "failures": [] if ok else [{"unit": "document", "reason": result_status}],
            "status": "success" if ok and not restricted_pages else "partial",
            "coverage": {
                "unit": "page",
                "expected_total": len(result.document.pages),
                "processed_pages": len(result.document.pages),
                "completed": max(0, len(result.document.pages) - len(restricted_pages)) if ok else 0,
                "partial": len(restricted_pages) if ok else len(result.document.pages),
                "failed": 0,
                "declared_scope": scope,
            },
        }
    except ImportError:
        code = "docling_dependency_unavailable"
    except Exception as exc:
        code = str(exc) if str(exc) in {"ocr_artifacts_unavailable"} else "pdf_conversion_failed"
    return {
        "items": [],
        "failures": [{"unit": "document", "reason": code}],
        "status": "blocked",
        "coverage": {
            "unit": "page",
            "expected_total": None,
            "completed": 0,
            "blocked": 1,
            "declared_scope": scope,
        },
    }


def ingest_source(db: Session, actor: Actor, source_id: str, version: int, run_id: str, scope: dict):
    source, path = source_for_read(db, actor, source_id, version)
    parsed = parse_file(source, path, version, run_id, scope)
    for item in parsed["items"]:
        db.add(
            Evidence(
                id=item["id"],
                source_id=source.id,
                source_version=version,
                data_role=source.data_role,
                envelope=item,
            )
        )
    source.status = parsed["status"]
    source.details = {
        **source.details,
        "last_parse": {
            "run_id": run_id,
            "coverage": parsed["coverage"],
            "failures": parsed["failures"],
            "evidence_count": len(parsed["items"]),
        },
    }
    audit(
        db,
        actor,
        "source.parse",
        source.id,
        details={"run_id": run_id, "status": parsed["status"], "coverage": parsed["coverage"]},
    )
    return {
        "source_id": source.id,
        "status": parsed["status"],
        "coverage": parsed["coverage"],
        "failures": parsed["failures"],
        "evidence_ids": [i["id"] for i in parsed["items"]],
    }
