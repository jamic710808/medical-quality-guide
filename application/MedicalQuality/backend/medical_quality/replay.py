"""在已通過對象授權的證據上重放固定位置；不重新生成或偷偷換版本。"""

from __future__ import annotations
import csv
import gzip
import json
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from .common import fail
from .config import settings
from .evidence import validate_envelope
from .models import Document, Evidence, SourceSnapshot
from .sources import hash_file, read_database, source_path


def pointer(value, path):
    if path in {"", "#"}:
        return value
    if path.startswith("#"):
        path = path[1:]
    for part in path.lstrip("/").split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def verify(db: Session, evidence: Evidence):
    item = evidence.envelope
    try:
        validate_envelope(item)
    except ValueError:
        fail("evidence_contract_incompatible", "證據合同版本或結構不受支持。")
    locator = item["locator"]
    content = item["content"]
    kind = locator["type"]
    snapshot = db.scalar(
        select(SourceSnapshot).where(
            SourceSnapshot.source_id == evidence.source_id, SourceSnapshot.version == evidence.source_version
        )
    )
    if not snapshot:
        fail("source_version_missing", "證據對應的來源快照不存在。")
    path = source_path(snapshot.reference)
    if hash_file(path) != snapshot.digest:
        fail("source_changed", "來源摘要已變化，不能以舊位置讀取當前內容。")
    matched = True
    try:
        if kind == "text":
            with path.open(encoding="utf-8-sig", newline="") as stream:
                raw = stream.read()
            if "char_start" in locator:
                matched = raw[locator["char_start"] : locator["char_end"]] == content.get("text", "")
            else:
                lines = raw.splitlines()
                matched = "\n".join(lines[locator["line_start"] - 1 : locator["line_end"]]) == content.get(
                    "text", ""
                )
        elif kind == "csv":
            with path.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.reader(stream)
                next(reader)
                row = next((r for n, r in enumerate(reader, 1) if n == locator["record_number"]), None)
            matched = row == content.get("value")
        elif kind == "json":
            if locator.get("record_number"):
                opener = gzip.open if str(path).endswith(".gz") else open
                with opener(path, "rt", encoding="utf-8-sig") as stream:
                    line = next(
                        (line for n, line in enumerate(stream, 1) if n == locator["record_number"]), None
                    )
                value = json.loads(line) if line else None
            else:
                value = json.loads(path.read_text(encoding="utf-8-sig"))
            value = pointer(value, locator["pointer"])
            matched = value == content.get("value")
        elif kind == "database" and evidence.envelope["kind"] == "schema":
            from .sources import schema_catalog

            table = next((t for t in schema_catalog(path) if t["table"] == locator["table"]), None)
            matched = bool(table) and table["columns"] == content.get("columns")
        elif kind == "database" and evidence.envelope["kind"] == "record":
            key = locator.get("row_key", {})
            if set(key) != {"_source_record_number"}:
                fail("locator_key_unavailable", "缺少可重放的快照記錄鍵。")
            with read_database(path) as connection:
                names = {
                    r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
                }
                table = locator["table"]
                if table not in names:
                    fail("source_table_missing", "快照表不再存在。")
                quoted = '"' + table.replace('"', '""') + '"'
                row = connection.execute(
                    f"SELECT * FROM {quoted} WHERE _source_record_number=?", (key["_source_record_number"],)
                ).fetchone()
                matched = bool(row) and dict(row) == content.get("value")
        elif kind == "xml":
            from defusedxml import ElementTree

            match = re.fullmatch(r"\(//(.+)\)\[(\d+)\]", locator["xpath"])
            if not match:
                fail("xpath_unsupported", "該 XPath 不在已驗證的回放子集中。")
            nodes = [n for n in ElementTree.parse(path).getroot().iter() if n.tag == match[1]]
            selected = nodes[int(match[2]) - 1]
            matched = "".join(selected.itertext()).strip() == content.get("text")
        elif kind == "pdf":
            from pypdf import PdfReader

            reader = PdfReader(path)
            page = locator["page"]
            if not 1 <= page <= len(reader.pages):
                matched = False
            else:
                ref = content.get("payload_ref", "")
                artifact = (settings().artifacts / ref).resolve()
                if not artifact.is_relative_to(settings().artifacts.resolve()) or not artifact.is_file():
                    fail("native_payload_missing", "原生解析記錄不可用。")
                native = json.loads(artifact.read_text())
                part = pointer(native, content["metadata"]["native_ref"])
                if content.get("text"):
                    matched = part.get("text") == content["text"]
                matched = matched and any(p.get("page_no") == page for p in part.get("prov", []))
                if locator.get("bbox"):
                    box = locator["bbox"]
                    geometry = native.get("pages", {}).get(str(page), {}).get("size", {})
                    width = float(geometry.get("width", reader.pages[page - 1].mediabox.width))
                    height = float(geometry.get("height", reader.pages[page - 1].mediabox.height))
                    matched = (
                        matched
                        and 0 <= min(box[0], box[2]) <= max(box[0], box[2]) <= width + 1
                        and 0 <= min(box[1], box[3]) <= max(box[1], box[3]) <= height + 1
                    )
        elif kind == "spreadsheet":
            import openpyxl

            book = openpyxl.load_workbook(path, read_only=True, data_only=False, keep_links=False)
            try:
                sheet = book[locator["sheet"]]
                for cell in content["metadata"]["cells"]:
                    actual = sheet[cell["coordinate"]].value
                    expected = cell["raw_value"]
                    if isinstance(expected, dict) and "iso" in expected:
                        matched = hasattr(actual, "isoformat") and actual.isoformat() == expected["iso"]
                    else:
                        matched = actual == expected
                    if not matched:
                        break
            finally:
                book.close()
        elif kind == "image":
            from PIL import Image

            with Image.open(path) as image:
                matched = (
                    0 <= locator["frame"] < getattr(image, "n_frames", 1)
                    and image.width == content["metadata"]["width"]
                    and image.height == content["metadata"]["height"]
                )
        elif kind == "waveform":
            import wfdb

            header = wfdb.rdheader(str(path.with_suffix("")))
            matched = (
                locator["record"] == header.record_name
                and 0 <= locator["start_sample"] < locator["end_sample"] <= header.sig_len
                and locator["channels"] == header.sig_name
            )
        elif kind == "unavailable":
            fail("locator_unavailable", "證據沒有可回放位置。")
    except (KeyError, IndexError, TypeError, ValueError, StopIteration):
        matched = False
    if not matched:
        fail("evidence_locator_mismatch", "定位重放與保存的原值不一致；已停止展示，需核對來源和解析。")
    if evidence.document_id:
        document = db.get(Document, evidence.document_id)
        with path.open(encoding="utf-8", newline="") as stream:
            raw = stream.read()
        if not document or document.content != raw:
            fail("document_source_mismatch", "文書版本與其證據原件不一致。")
    return {
        "status": "verified",
        "source_version": evidence.source_version,
        "locator_type": kind,
        "meaning": "固定原值/位置可回放，不表示醫學主張正確",
    }


def pdf_page_image(db: Session, evidence: Evidence) -> bytes:
    """調用方先做當前證據授權/回放；只渲染該固定頁，不開放任意文件 URL。"""
    import io
    import json
    import pypdfium2 as pdfium
    from PIL import ImageDraw
    from .common import digest

    item = evidence.envelope
    locator = item["locator"]
    if locator["type"] != "pdf":
        fail("not_pdf_evidence", "此證據沒有 PDF 原頁。", 422)
    snapshot = db.scalar(
        select(SourceSnapshot).where(
            SourceSnapshot.source_id == evidence.source_id, SourceSnapshot.version == evidence.source_version
        )
    )
    raw = source_path(snapshot.reference).read_bytes()
    if digest(raw) != snapshot.digest:
        fail("source_changed", "渲染前原件已經變化，已停止顯示。")
    pdf = pdfium.PdfDocument(raw)
    try:
        page = pdf.get_page(locator["page"] - 1)
        try:
            bitmap = page.render(scale=1.5)
            try:
                picture = bitmap.to_pil().copy()
            finally:
                bitmap.close()
        finally:
            page.close()
        native = json.loads((settings().artifacts / item["content"]["payload_ref"]).read_text())
        geometry = native["pages"][str(locator["page"])]["size"]
        width, height = float(geometry["width"]), float(geometry["height"])
        if locator.get("bbox"):
            left, top, right, bottom = locator["bbox"]
            if locator.get("origin") == "bottom_left":
                top, bottom = height - top, height - bottom
            scale_x, scale_y = picture.width / width, picture.height / height
            rectangle = (
                min(left, right) * scale_x,
                min(top, bottom) * scale_y,
                max(left, right) * scale_x,
                max(top, bottom) * scale_y,
            )
            ImageDraw.Draw(picture).rectangle(rectangle, outline=(0, 122, 255), width=3)
            if evidence.case_id:
                # Case permission alone does not authorize other content on a shared PDF page.
                picture = picture.crop(
                    (
                        max(0, int(rectangle[0]) - 12),
                        max(0, int(rectangle[1]) - 12),
                        min(picture.width, int(rectangle[2]) + 13),
                        min(picture.height, int(rectangle[3]) + 13),
                    )
                )
        elif evidence.case_id:
            fail("page_scope_unconfirmed", "病例證據缺少可限制顯示範圍的頁框，需先核查頁面授權。")
        result = io.BytesIO()
        picture.save(result, format="PNG")
        return result.getvalue()
    finally:
        pdf.close()
