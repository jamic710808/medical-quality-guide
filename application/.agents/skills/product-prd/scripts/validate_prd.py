#!/usr/bin/env python3
"""Validate the lightweight product-level PRD contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


REQUIRED_HEADINGS = (
    "文檔信息",
    "背景、問題與目標",
    "目標用戶與場景",
    "產品目標與成功信號",
    "核心用戶旅程",
    "產品範圍",
    "功能需求",
    "業務規則與狀態",
    "非功能要求",
    "驗收標準",
    "依賴、約束與風險",
    "開放問題與決策記錄",
    "變更記錄",
)

PLACEHOLDERS = (
    re.compile(r"【待填寫[^】]*】"),
    re.compile(r"\{\{[^}]+\}\}"),
    re.compile(r"\b(?:TODO|TBD)\b", re.IGNORECASE),
)


def parse_frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    result: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return result
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return {}


def duplicate_ids(ids: list[str]) -> list[str]:
    return sorted(item for item, count in Counter(ids).items() if count > 1)


def table_rows(text: str, prefix: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        if re.match(rf"^\|[ \t]*{prefix}-\d{{3}}[ \t]*\|", line):
            content = line.strip().removeprefix("|").removesuffix("|")
            rows.append([cell.strip() for cell in re.split(r"(?<!\\)\|", content)])
    return rows


def acceptance_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"(?m)^###\s+(AC-\d{3})\b[^\n]*$", text))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        candidates = [matches[index + 1].start()] if index + 1 < len(matches) else []
        next_section = re.search(r"(?m)^##\s+", text[match.end() :])
        if next_section:
            candidates.append(match.end() + next_section.start())
        end = min(candidates) if candidates else len(text)
        blocks.append((match.group(1), text[match.end() : end]))
    return blocks


def validate_prd(project: Path, require_confirmed: bool = False) -> dict[str, object]:
    project = project.resolve()
    path = project / "docs/PRD.md"
    errors: list[str] = []
    warnings: list[str] = []
    if not path.is_file():
        return {
            "ok": False,
            "project": str(project),
            "errors": ["missing docs/PRD.md"],
            "warnings": [],
        }

    text = path.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(text)
    if frontmatter.get("document") != "product-prd":
        errors.append("docs/PRD.md must declare document: product-prd")
    status = frontmatter.get("status")
    if status not in {"draft", "confirmed"}:
        errors.append("docs/PRD.md status must be draft or confirmed")
    if require_confirmed and status != "confirmed":
        errors.append("docs/PRD.md must have status: confirmed")

    for heading in REQUIRED_HEADINGS:
        if not re.search(rf"(?m)^##\s+.*{re.escape(heading)}.*$", text):
            errors.append(f"docs/PRD.md missing heading: {heading}")

    requirement_rows = table_rows(text, "REQ")
    nfr_rows = table_rows(text, "NFR")
    requirements = [row[0] for row in requirement_rows]
    nfrs = [row[0] for row in nfr_rows]
    for label, ids in (("REQ", requirements), ("NFR", nfrs)):
        duplicates = duplicate_ids(ids)
        if duplicates:
            errors.append(f"duplicate {label} definitions: {', '.join(duplicates)}")
    if not requirements:
        errors.append("docs/PRD.md must define at least one REQ-NNN table row")
    if not nfrs:
        errors.append("docs/PRD.md must define at least one NFR-NNN table row")

    blocks = acceptance_blocks(text)
    acceptance_ids = [item[0] for item in blocks]
    duplicates = duplicate_ids(acceptance_ids)
    if duplicates:
        errors.append(f"duplicate AC definitions: {', '.join(duplicates)}")
    if not blocks:
        errors.append("docs/PRD.md must define at least one AC-NNN heading")

    known_sources = set(requirements) | set(nfrs)
    covered_sources: set[str] = set()
    for acceptance_id, block in blocks:
        source_match = re.search(r"(?m)^\s*-\s*來源[：:]\s*(.+)$", block)
        sources = (
            set(re.findall(r"\b(?:REQ|NFR)-\d{3}\b", source_match.group(1)))
            if source_match
            else set()
        )
        if not sources:
            errors.append(f"{acceptance_id} must declare 來源 with REQ/NFR IDs")
        unknown = sorted(sources - known_sources)
        if unknown:
            errors.append(f"{acceptance_id} references unknown sources: {', '.join(unknown)}")
        covered_sources.update(sources & known_sources)
        for keyword in ("Given", "When", "Then"):
            step = re.search(rf"(?mi)^[ \t]*-[ \t]*{keyword}\b([^\n]*)$", block)
            if not step or not step.group(1).strip():
                errors.append(f"{acceptance_id} missing non-empty {keyword}")

    uncovered = sorted(known_sources - covered_sources)
    if uncovered:
        errors.append(f"requirements without acceptance coverage: {', '.join(uncovered)}")

    if status == "confirmed" or require_confirmed:
        if any(pattern.search(text) for pattern in PLACEHOLDERS):
            errors.append("confirmed docs/PRD.md still contains template placeholders")
        for rows, minimum in ((requirement_rows, 7), (nfr_rows, 4)):
            for row in rows:
                if len(row) < minimum or any(not cell for cell in row):
                    errors.append(
                        f"{row[0]} must contain at least {minimum} columns with non-empty content; "
                        "explain any inapplicable field"
                    )

        open_states = {"open", "待確認", "處理中"}
        closed_states = {"closed", "已解決", "已關閉"}
        blocking_values = {"是", "阻塞", "blocking"}
        nonblocking_values = {"否", "非阻塞", "non-blocking"}
        for row in table_rows(text, "OQ"):
            if len(row) < 5 or any(not cell for cell in row[:5]):
                errors.append(f"{row[0]} must declare question, blocking flag, verification plan and status")
                continue
            blocking, question_status = row[2].lower(), row[4].lower()
            if blocking not in blocking_values | nonblocking_values:
                errors.append(f"{row[0]} has unknown blocking flag: {row[2]}")
            if question_status not in open_states | closed_states:
                errors.append(f"{row[0]} has unknown question status: {row[4]}")
            elif question_status in closed_states:
                if len(row) < 6 or not row[5]:
                    errors.append(f"{row[0]} closed question must include resolution and supporting evidence")
            elif blocking in blocking_values:
                errors.append("confirmed docs/PRD.md still contains a blocking open question")

    return {
        "ok": not errors,
        "project": str(project),
        "status": status,
        "requirements": len(requirements),
        "nfrs": len(nfrs),
        "acceptance_criteria": len(blocks),
        "errors": errors,
        "warnings": warnings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Project root containing docs/PRD.md")
    parser.add_argument("--require-confirmed", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = validate_prd(args.project, require_confirmed=args.require_confirmed)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
