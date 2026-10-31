#!/usr/bin/env python3
"""Validate the project-level product specification contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


REQUIRED_HEADINGS = (
    "文檔職責與來源",
    "全局合同索引",
    "產品對象與職責",
    "全局狀態與生命週期",
    "跨 Feature 不變量與共享行為",
    "共享交互、事件與證據",
    "安全、權限、失敗與恢復",
    "兼容、能力與產品語言",
    "總體驗收與 Feature 提取約束",
    "開放問題、決策與變更",
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


def prd_requirements(text: str) -> set[str]:
    return set(re.findall(r"(?m)^\|\s*((?:REQ|NFR)-\d{3})\s*\|", text))


def prd_acceptance(text: str) -> set[str]:
    return set(re.findall(r"(?m)^###\s+(AC-\d{3})\b", text))


def contract_rows(text: str, errors: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not re.match(r"^\|\s*PSC-\d{3}\s*\|", line):
            continue
        content = line.strip().removeprefix("|").removesuffix("|")
        cells = [cell.strip() for cell in re.split(r"(?<!\\)\|", content)]
        if len(cells) != 7:
            errors.append(f"product-spec line {number} must contain exactly 7 columns")
            continue
        rows.append(
            {
                "id": cells[0],
                "type": cells[1],
                "requirements": cells[2],
                "acceptance": cells[3],
                "summary": cells[4],
                "detail": cells[5],
                "scope": cells[6],
            }
        )
    return rows


def section_body(text: str, heading: str) -> str:
    match = re.search(
        rf"(?ms)^##[ \t]+[^\n]*{re.escape(heading)}[^\n]*\n(.*?)(?=^##[ \t]+|\Z)",
        text,
    )
    return match.group(1) if match else ""


def validate_product_spec(project: Path, require_confirmed: bool = False) -> dict[str, object]:
    project = project.resolve()
    prd_path = project / "docs/PRD.md"
    spec_path = project / "docs/specs/product-spec.md"
    errors: list[str] = []
    warnings: list[str] = []

    if not prd_path.is_file():
        errors.append("missing docs/PRD.md")
    if not spec_path.is_file():
        errors.append("missing docs/specs/product-spec.md")
    if errors:
        return {"ok": False, "project": str(project), "errors": errors, "warnings": warnings}

    prd_text = prd_path.read_text(encoding="utf-8")
    prd_meta = parse_frontmatter(prd_text)
    if prd_meta.get("document") != "product-prd" or prd_meta.get("status") != "confirmed":
        errors.append("docs/PRD.md must be a confirmed product-prd")
    known_requirements = prd_requirements(prd_text)
    known_acceptance = prd_acceptance(prd_text)
    if not known_requirements:
        errors.append("docs/PRD.md does not define REQ/NFR table rows")
    if not known_acceptance:
        errors.append("docs/PRD.md does not define AC-NNN acceptance criteria")

    text = spec_path.read_text(encoding="utf-8")
    metadata = parse_frontmatter(text)
    if metadata.get("document") != "product-spec":
        errors.append("product-spec.md must declare document: product-spec")
    if metadata.get("prd") != "docs/PRD.md":
        errors.append("product-spec.md must declare prd: docs/PRD.md")
    status = metadata.get("status")
    if status not in {"draft", "confirmed"}:
        errors.append("product-spec.md status must be draft or confirmed")
    if require_confirmed and status != "confirmed":
        errors.append("product-spec.md must have status: confirmed")

    for heading in REQUIRED_HEADINGS:
        if not re.search(rf"(?m)^##\s+.*{re.escape(heading)}.*$", text):
            errors.append(f"product-spec.md missing heading: {heading}")

    rows = contract_rows(text, errors)
    contract_ids = [row["id"] for row in rows]
    duplicates = duplicate_ids(contract_ids)
    if duplicates:
        errors.append(f"duplicate PSC definitions: {', '.join(duplicates)}")
    if not rows:
        errors.append("product-spec.md must define at least one PSC-NNN contract row")

    covered_requirements: set[str] = set()
    covered_acceptance: set[str] = set()
    detailed_text = "\n".join(section_body(text, heading) for heading in REQUIRED_HEADINGS[2:-1])
    for row in rows:
        contract_id = row["id"]
        requirements = set(re.findall(r"\b(?:REQ|NFR)-\d{3}\b", row["requirements"]))
        acceptance = set(re.findall(r"\bAC-\d{3}\b", row["acceptance"]))
        if not requirements:
            errors.append(f"{contract_id} must reference at least one REQ/NFR")
        if not acceptance:
            errors.append(f"{contract_id} must reference at least one PRD AC-NNN")
        unknown_requirements = sorted(requirements - known_requirements)
        unknown_acceptance = sorted(acceptance - known_acceptance)
        if unknown_requirements:
            errors.append(f"{contract_id} references unknown requirements: {', '.join(unknown_requirements)}")
        if unknown_acceptance:
            errors.append(f"{contract_id} references unknown PRD acceptance: {', '.join(unknown_acceptance)}")
        covered_requirements.update(requirements & known_requirements)
        covered_acceptance.update(acceptance & known_acceptance)
        if not re.search(rf"\b{contract_id}\b", detailed_text):
            errors.append(f"{contract_id} is indexed but not referenced in a detailed contract section")

    missing_requirements = sorted(known_requirements - covered_requirements)
    missing_acceptance = sorted(known_acceptance - covered_acceptance)
    if missing_requirements:
        errors.append(f"PRD requirements missing from Product Spec: {', '.join(missing_requirements)}")
    if missing_acceptance:
        errors.append(f"PRD acceptance missing from Product Spec: {', '.join(missing_acceptance)}")

    if re.search(r"(?m)^- \[[ xX]\]\s+T\d{3}\b", text):
        errors.append("product-spec.md must not contain implementation Task checklists")

    if status == "confirmed" or require_confirmed:
        if any(pattern.search(text) for pattern in PLACEHOLDERS):
            errors.append("confirmed product-spec.md still contains template placeholders")
        for row in rows:
            if any(not value for value in row.values()):
                errors.append(f"{row['id']} contract index fields must be non-empty")
        for line in text.splitlines():
            if not re.match(r"^\|[ \t]*OQ-\d{3}[ \t]*\|", line):
                continue
            cells = [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip()[1:].removesuffix("|"))]
            if len(cells) < 5 or any(not cell for cell in cells[:5]):
                errors.append(f"{cells[0]} must declare question, blocking flag, verification plan and status")
                continue
            blocking, question_status = cells[2].lower(), cells[4].lower()
            if blocking not in {"是", "阻塞", "blocking", "否", "非阻塞", "non-blocking"}:
                errors.append(f"{cells[0]} has unknown blocking flag: {cells[2]}")
            if question_status in {"closed", "已解決", "已關閉"}:
                if len(cells) < 6 or not cells[5]:
                    errors.append(f"{cells[0]} closed question must include resolution and supporting evidence")
            elif question_status in {"open", "待確認", "處理中"}:
                if blocking in {"是", "阻塞", "blocking"}:
                    errors.append("confirmed product-spec.md still contains a blocking open question")
            else:
                errors.append(f"{cells[0]} has unknown question status: {cells[4]}")

    return {
        "ok": not errors,
        "project": str(project),
        "status": status,
        "contracts": len(rows),
        "requirements": len(known_requirements),
        "acceptance_criteria": len(known_acceptance),
        "errors": errors,
        "warnings": warnings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--require-confirmed", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = validate_product_spec(args.project, require_confirmed=args.require_confirmed)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
