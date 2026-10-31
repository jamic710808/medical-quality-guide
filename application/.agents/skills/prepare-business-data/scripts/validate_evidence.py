#!/usr/bin/env python3
"""Validate a bounded EvidenceItem JSONL batch without reading referenced sources."""

from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys


SCHEMA = Path(__file__).resolve().parents[1] / "references/evidence-item.schema.json"
MAX_LINE_BYTES = 4 * 1024 * 1024


def reject_constant(value):
    raise ValueError("non_finite_json_number")


def build_validator():
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise RuntimeError("jsonschema is required in the selected Python environment; no automatic install") from exc
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def item_errors(item, validator):
    """Report paths/keywords, never echo the instance's business values."""
    errors = [{"path": "/" + "/".join(map(str, e.absolute_path)), "rule": str(e.validator)}
              for e in validator.iter_errors(item)]
    if errors:
        return errors
    kind, loc = item["kind"], item["locator"]
    valid_locators = {
        "schema": {"database", "json", "spreadsheet", "unavailable"},
        "record": {"database", "csv", "json", "xml", "spreadsheet", "unavailable"},
        "table": {"database", "csv", "json", "pdf", "spreadsheet", "unavailable"},
        "text": {"database", "csv", "json", "xml", "text", "pdf", "spreadsheet", "unavailable"},
        "image": {"image", "pdf", "unavailable"},
        "waveform": {"waveform", "unavailable"},
    }
    def fail(path, rule):
        errors.append({"path": path, "rule": rule})
    if loc["type"] not in valid_locators[kind]:
        fail("/locator/type", "incompatible_with_content_kind")
        return errors
    if loc["type"] == "database" and kind in {"record", "text"}:
        if "row_key" in loc:
            if any(value is None for value in loc["row_key"].values()) or loc.get("identity_scope") != "declared_key":
                fail("/locator", "declared_key_requires_non_null_key_and_scope")
        elif not all(k in loc for k in ("row_ordinal", "query_id")) or loc.get("identity_scope") != "snapshot":
            fail("/locator", "record_requires_declared_key_or_snapshot_ordinal")
    if loc["type"] == "text":
        if loc["line_end"] < loc["line_start"]:
            fail("/locator/line_end", "reversed_line_range")
        if ("char_start" in loc) != ("char_end" in loc) or loc.get("char_end", 0) < loc.get("char_start", 0):
            fail("/locator", "invalid_character_range")
    if loc["type"] == "pdf" and "bbox" in loc:
        if not all(k in loc for k in ("unit", "origin", "page_width", "page_height")):
            fail("/locator", "bbox_requires_coordinate_system_and_page_size")
        else:
            x0, y0, x1, y1 = loc["bbox"]
            if x1 < x0 or y1 < y0:
                fail("/locator/bbox", "bbox_requires_min_max_order")
            width = 1 if loc["unit"] == "normalized" else loc["page_width"]
            height = 1 if loc["unit"] == "normalized" else loc["page_height"]
            if not (0 <= x0 <= x1 <= width and 0 <= y0 <= y1 <= height):
                fail("/locator/bbox", "bbox_outside_page")
    if loc["type"] == "waveform":
        if loc["end_sample"] <= loc["start_sample"]:
            fail("/locator", "empty_or_reversed_sample_range")
        units = item["content"]["metadata"].get("units")
        if units is not None and (not isinstance(units, list) or len(units) != len(loc["channels"])):
            fail("/content/metadata/units", "channel_unit_count_mismatch")
        if item["source"]["format"] == "wfdb" and len(set(item["native_refs"])) < 2:
            fail("/native_refs", "wfdb_requires_header_and_signal_references")
    return errors


def validate_file(path, max_items=10000):
    validator = build_validator()
    checked, error_count, errors, seen, truncated = 0, 0, [], set(), False
    def record(line, items):
        nonlocal error_count
        error_count += len(items)
        errors.extend({"line": line, **item} for item in items[:max(0, 20-len(errors))])
    with Path(path).open("rb") as stream:
        line_no = 0
        while True:
            line = stream.readline(MAX_LINE_BYTES + 1)
            if not line:
                break
            line_no += 1
            if not line.strip():
                continue
            if checked >= max_items:
                truncated = True
                break
            checked += 1
            if len(line) > MAX_LINE_BYTES:
                record(line_no, [{"path": "/", "rule": "line_exceeds_4_MiB_use_payload_reference"}])
                truncated = True
                break
            try:
                item = json.loads(line, parse_float=Decimal, parse_constant=reject_constant)
            except (ValueError, UnicodeError, RecursionError):
                record(line_no, [{"path": "/", "rule": "invalid_json"}])
                continue
            found = item_errors(item, validator)
            if not found:
                if item["id"] in seen:
                    found.append({"path": "/id", "rule": "duplicate_id_in_checked_batch"})
                seen.add(item["id"])
            record(line_no, found)
    if not checked:
        record(0, [{"path": "/", "rule": "empty_input"}])
    return {"ok": error_count == 0 and not truncated, "checked_items": checked,
            "input_truncated": truncated, "error_count": error_count, "errors": errors,
            "checks": "schema_and_item_invariants_and_batch_ids",
            "source_content_and_locator_replay": "not_checked",
            "clinical_or_business_correctness": "not_checked"}


def positive(value):
    result = int(value)
    if result < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--max-items", type=positive, default=10000)
    args = parser.parse_args()
    try:
        result = validate_file(args.input, args.max_items)
    except (OSError, RuntimeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2 if result["input_truncated"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
