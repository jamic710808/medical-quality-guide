#!/usr/bin/env python3
"""Validate Feature Map and per-Feature spec/plan/tasks documents."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


FEATURE_ID = re.compile(r"^F\d{3}$")
FEATURE_DIR = re.compile(r"^(F\d{3})-[a-z0-9]+(?:-[a-z0-9]+)*$")
TASK_HEADER = re.compile(r"(?m)^- \[([ xX])\] (T\d{3})\s+(.+)$")
FORBIDDEN_TASK_LABELS = re.compile(
    r"\[(?:FE|BE|INT)\]|\bpack\s*[:=：]\s*(?:frontend|backend|integration)\b",
    re.IGNORECASE,
)
FORBIDDEN_TASK_TITLE_PREFIX = re.compile(
    r"^(?:(?:FE|BE|INT)\b|(?:frontend|backend|integration)\s+pack\b)",
    re.IGNORECASE,
)
PLACEHOLDERS = (
    re.compile(r"【待填寫[^】]*】"),
    re.compile(r"\{\{[^}]+\}\}"),
    re.compile(r"\b(?:TODO|TBD)\b", re.IGNORECASE),
)
REQUIRED_HEADINGS = {
    "spec.md": (
        "目標與可觀察結果",
        "來源與範圍",
        "用戶旅程與狀態",
        "功能行為",
        "異常與恢復",
        "驗收標準",
        "開放問題",
    ),
    "plan.md": (
        "現有上下文與複用",
        "影響範圍",
        "實現方案",
        "實施順序",
        "依賴與風險",
        "回退策略",
        "驗收映射",
    ),
    "tasks.md": ("任務規則", "任務清單", "Task 數量複核", "執行記錄"),
}


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


def csv_ids(value: str, pattern: str) -> set[str]:
    return set(re.findall(pattern, value))


def section_body(text: str, heading: str) -> str:
    match = re.search(
        rf"(?ms)^##[ \t]+[^\n]*{re.escape(heading)}[^\n]*\n(.*?)(?=^##[ \t]+|\Z)", text
    )
    return match.group(1) if match else ""


def validate_open_questions(text: str, label: str, errors: list[str]) -> None:
    for line in text.splitlines():
        if not re.match(r"^\|[ \t]*OQ-\d{3}[ \t]*\|", line):
            continue
        cells = [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip()[1:].removesuffix("|"))]
        identity = f"{label}/{cells[0]}"
        if len(cells) < 5 or any(not cell for cell in cells[:5]):
            errors.append(f"{identity} must declare question, blocking flag, verification plan and status")
            continue
        blocking, status = cells[2].lower(), cells[4].lower()
        if blocking not in {"是", "阻塞", "blocking", "否", "非阻塞", "non-blocking"}:
            errors.append(f"{identity} has unknown blocking flag: {cells[2]}")
        if status in {"closed", "已解決", "已關閉"}:
            if len(cells) < 6 or not cells[5]:
                errors.append(f"{identity} closed question must include resolution and supporting evidence")
        elif status in {"open", "待確認", "處理中"}:
            if blocking in {"是", "阻塞", "blocking"}:
                errors.append(f"{identity} is a blocking open question")
        else:
            errors.append(f"{identity} has unknown question status: {cells[4]}")


def prd_definitions(text: str) -> set[str]:
    return set(re.findall(r"(?m)^\|\s*((?:REQ|NFR)-\d{3})\s*\|", text))


def prd_acceptance_ids(text: str) -> set[str]:
    return set(re.findall(r"(?m)^###\s+(AC-\d{3})\b", text))


def product_contract_definitions(text: str) -> set[str]:
    return set(re.findall(r"(?m)^\|\s*(PSC-\d{3})\s*\|", text))


def feature_rows(text: str, errors: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.lstrip().startswith("|"):
            continue
        content = line.strip().removeprefix("|").removesuffix("|")
        cells = [cell.strip() for cell in re.split(r"(?<!\\)\|", content)]
        if not cells or not FEATURE_ID.fullmatch(cells[0]):
            continue
        if len(cells) != 8:
            errors.append(f"feature-map line {number} must contain exactly 8 columns")
            continue
        rows.append(
            dict(
                id=cells[0],
                directory=cells[1].strip("`"),
                name=cells[2],
                outcome=cells[3],
                sources=cells[4],
                dependencies=cells[5],
                priority=cells[6],
                status=cells[7],
            )
        )
    return rows


def find_cycle(graph: dict[str, set[str]]) -> list[str] | None:
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        if node in visiting:
            start = stack.index(node)
            return stack[start:] + [node]
        if node in visited:
            return None
        visiting.add(node)
        stack.append(node)
        for dependency in graph.get(node, set()):
            cycle = visit(dependency)
            if cycle:
                return cycle
        stack.pop()
        visiting.remove(node)
        visited.add(node)
        return None

    for node in graph:
        cycle = visit(node)
        if cycle:
            return cycle
    return None


def acceptance_blocks(text: str, feature_id: str) -> list[tuple[str, str]]:
    pattern = re.compile(rf"(?m)^###\s+(AC-{feature_id}-\d{{3}})\b[^\n]*$")
    matches = list(pattern.finditer(text))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        candidates = [matches[index + 1].start()] if index + 1 < len(matches) else []
        next_section = re.search(r"(?m)^##\s+", text[match.end() :])
        if next_section:
            candidates.append(match.end() + next_section.start())
        end = min(candidates) if candidates else len(text)
        blocks.append((match.group(1), text[match.end() : end]))
    return blocks


def task_blocks(text: str) -> list[dict[str, object]]:
    matches = list(TASK_HEADER.finditer(text))
    tasks: list[dict[str, object]] = []
    for index, match in enumerate(matches):
        candidates = [matches[index + 1].start()] if index + 1 < len(matches) else []
        next_section = re.search(r"(?m)^##\s+", text[match.end() :])
        if next_section:
            candidates.append(match.end() + next_section.start())
        end = min(candidates) if candidates else len(text)
        tasks.append(
            {
                "checked": match.group(1).lower() == "x",
                "id": match.group(2),
                "title": match.group(3).strip(),
                "block": text[match.end() : end],
            }
        )
    return tasks


def task_field(block: str, label: str) -> str | None:
    match = re.search(rf"(?m)^[ \t]+-[ \t]*{re.escape(label)}[：:][ \t]*([^\n]*)$", block)
    return match.group(1).strip() if match else None


def validate_feature_docs(
    root: Path,
    row: dict[str, str],
    known_requirements: set[str],
    known_prd_acceptance: set[str],
    known_product_contracts: set[str],
    require_ready: bool,
    require_complete: bool,
    errors: list[str],
    warnings: list[str],
) -> set[str]:
    feature_id = row["id"]
    directory = root / "docs/specs" / row["directory"]
    if not directory.is_dir():
        errors.append(f"{feature_id} missing directory docs/specs/{row['directory']}")
        return set()

    texts: dict[str, str] = {}
    for name, document in (
        ("spec.md", "feature-spec"),
        ("plan.md", "feature-plan"),
        ("tasks.md", "feature-tasks"),
    ):
        path = directory / name
        if not path.is_file():
            errors.append(f"{feature_id} missing {name}")
            continue
        text = path.read_text(encoding="utf-8")
        texts[name] = text
        frontmatter = parse_frontmatter(text)
        if frontmatter.get("document") != document:
            errors.append(f"{feature_id}/{name} must declare document: {document}")
        if frontmatter.get("feature") != feature_id:
            errors.append(f"{feature_id}/{name} frontmatter feature must equal {feature_id}")
        if not re.search(rf"(?m)^#\s+{feature_id}\b", text):
            errors.append(f"{feature_id}/{name} title must start with {feature_id}")
        for heading in REQUIRED_HEADINGS[name]:
            if not re.search(rf"(?m)^##\s+.*{re.escape(heading)}.*$", text):
                errors.append(f"{feature_id}/{name} missing heading: {heading}")
        if require_ready and any(pattern.search(text) for pattern in PLACEHOLDERS):
            errors.append(f"{feature_id}/{name} still contains template placeholders")
        if require_ready:
            validate_open_questions(text, f"{feature_id}/{name}", errors)

    if set(texts) != {"spec.md", "plan.md", "tasks.md"}:
        return set()

    spec_text = texts["spec.md"]
    plan_text = texts["plan.md"]
    tasks_text = texts["tasks.md"]
    spec_status = parse_frontmatter(spec_text).get("status")
    plan_status = parse_frontmatter(plan_text).get("status")
    tasks_status = parse_frontmatter(tasks_text).get("status")
    if spec_status not in {"draft", "ready"}:
        errors.append(f"{feature_id}/spec.md status must be draft or ready")
    if plan_status not in {"draft", "ready"}:
        errors.append(f"{feature_id}/plan.md status must be draft or ready")
    if tasks_status not in {"draft", "planned", "in-progress", "completed"}:
        errors.append(f"{feature_id}/tasks.md has invalid status")
    if require_ready and (spec_status != "ready" or plan_status != "ready" or tasks_status == "draft"):
        errors.append(f"{feature_id} must have ready spec/plan and planned-or-later tasks")
    expected_tasks_status = {
        "planned": "planned",
        "in-progress": "in-progress",
        "completed": "completed",
        "deferred": "planned",
    }.get(row["status"])
    if require_ready and expected_tasks_status and tasks_status != expected_tasks_status:
        errors.append(
            f"{feature_id} feature-map status {row['status']} does not match "
            f"tasks.md status {tasks_status}; expected {expected_tasks_status}"
        )

    map_requirements = csv_ids(row["sources"], r"\b(?:REQ|NFR)-\d{3}\b")
    map_contracts = csv_ids(row["sources"], r"\bPSC-\d{3}\b")
    for source in sorted(map_requirements | map_contracts):
        if source not in spec_text:
            errors.append(f"{feature_id}/spec.md does not carry mapped source {source}")

    blocks = acceptance_blocks(spec_text, feature_id)
    ac_ids = [item[0] for item in blocks]
    feature_acceptance_sources: set[str] = set()
    feature_acceptance_contracts: set[str] = set()
    mapped_prd_acceptance: set[str] = set()
    duplicates = duplicate_ids(ac_ids)
    if duplicates:
        errors.append(f"{feature_id} duplicate AC definitions: {', '.join(duplicates)}")
    if not blocks:
        errors.append(f"{feature_id}/spec.md must define at least one AC-{feature_id}-NNN")
    for acceptance_id, block in blocks:
        source_match = re.search(r"(?m)^\s*-\s*來源[：:]\s*(.+)$", block)
        sources = (
            csv_ids(source_match.group(1), r"\b(?:REQ|NFR)-\d{3}\b")
            if source_match
            else set()
        )
        contracts = (
            csv_ids(source_match.group(1), r"\bPSC-\d{3}\b")
            if source_match
            else set()
        )
        if not sources or not contracts:
            errors.append(f"{acceptance_id} must declare 來源 with both REQ/NFR and PSC IDs")
        unknown = sorted(sources - known_requirements)
        unknown_contracts = sorted(contracts - known_product_contracts)
        if unknown:
            errors.append(f"{acceptance_id} references unknown requirements: {', '.join(unknown)}")
        if unknown_contracts:
            errors.append(
                f"{acceptance_id} references unknown Product Spec contracts: "
                f"{', '.join(unknown_contracts)}"
            )
        outside_feature = sorted(sources - map_requirements)
        outside_contracts = sorted(contracts - map_contracts)
        if outside_feature:
            errors.append(
                f"{acceptance_id} references requirements outside {feature_id} Map sources: "
                f"{', '.join(outside_feature)}"
            )
        if outside_contracts:
            errors.append(
                f"{acceptance_id} references PSC outside {feature_id} Map sources: "
                f"{', '.join(outside_contracts)}"
            )
        feature_acceptance_sources.update(sources & map_requirements)
        feature_acceptance_contracts.update(contracts & map_contracts)

        prd_acceptance_match = re.search(
            r"(?m)^\s*-\s*對應 PRD 驗收[：:]\s*(.+)$", block
        )
        prd_acceptance = (
            csv_ids(prd_acceptance_match.group(1), r"\bAC-\d{3}\b")
            if prd_acceptance_match
            else set()
        )
        if not prd_acceptance:
            errors.append(f"{acceptance_id} must declare 對應 PRD 驗收 with AC-NNN IDs")
        unknown_prd_acceptance = sorted(prd_acceptance - known_prd_acceptance)
        if unknown_prd_acceptance:
            errors.append(
                f"{acceptance_id} references unknown PRD acceptance criteria: "
                f"{', '.join(unknown_prd_acceptance)}"
            )
        mapped_prd_acceptance.update(prd_acceptance & known_prd_acceptance)
        for keyword in ("Given", "When", "Then"):
            step = re.search(rf"(?mi)^[ \t]*-[ \t]*{keyword}\b([^\n]*)$", block)
            if not step or not step.group(1).strip():
                errors.append(f"{acceptance_id} missing non-empty {keyword}")

    uncovered_feature_sources = sorted(map_requirements - feature_acceptance_sources)
    if uncovered_feature_sources:
        errors.append(
            f"{feature_id} mapped requirements without Feature AC coverage: "
            f"{', '.join(uncovered_feature_sources)}"
        )
    uncovered_feature_contracts = sorted(map_contracts - feature_acceptance_contracts)
    if uncovered_feature_contracts:
        errors.append(
            f"{feature_id} mapped PSC without Feature AC coverage: "
            f"{', '.join(uncovered_feature_contracts)}"
        )
    planned_ac = set(re.findall(rf"\bAC-{feature_id}-\d{{3}}\b", plan_text))
    if require_ready:
        planned_ac = set()
        for line in section_body(plan_text, "驗收映射").splitlines():
            if not line.lstrip().startswith("|"):
                continue
            cells = [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip()[1:].removesuffix("|"))]
            references = csv_ids(cells[0], r"\bAC-F\d{3}-\d{3}\b")
            if not references:
                continue
            if len(cells) < 4 or any(not cell for cell in cells):
                errors.append(f"{feature_id}/plan.md acceptance mapping needs non-empty result, method and evidence")
            if references - set(ac_ids):
                errors.append(f"{feature_id}/plan.md maps unknown Feature AC: {', '.join(sorted(references - set(ac_ids)))}")
            planned_ac.update(references)
    missing_plan_acceptance = sorted(set(ac_ids) - planned_ac)
    if missing_plan_acceptance:
        errors.append(
            f"{feature_id}/plan.md does not map Feature AC: {', '.join(missing_plan_acceptance)}"
        )

    has_forbidden_task_label = bool(FORBIDDEN_TASK_LABELS.search(tasks_text))
    if has_forbidden_task_label:
        errors.append(f"{feature_id}/tasks.md contains forbidden FE/BE/INT or Pack labels")
    tasks = task_blocks(tasks_text)
    if not has_forbidden_task_label and any(
        FORBIDDEN_TASK_TITLE_PREFIX.search(str(task["title"])) for task in tasks
    ):
        errors.append(f"{feature_id}/tasks.md contains forbidden FE/BE/INT or Pack labels")
    task_ids = [str(task["id"]) for task in tasks]
    duplicates = duplicate_ids(task_ids)
    if duplicates:
        errors.append(f"{feature_id} duplicate task IDs: {', '.join(duplicates)}")
    if not tasks:
        errors.append(f"{feature_id}/tasks.md must define at least one TNNN task")
        return mapped_prd_acceptance

    known_tasks = set(task_ids)
    task_sources: set[str] = set()
    task_acceptance: set[str] = set()
    task_graph: dict[str, set[str]] = {}
    titles: list[str] = []
    for task in tasks:
        task_id = str(task["id"])
        title = str(task["title"])
        block = str(task["block"])
        titles.append(title)
        fields = {label: task_field(block, label) for label in ("來源", "依賴", "修改", "完成證據", "驗證")}
        missing = [label for label, value in fields.items() if not value]
        if missing:
            errors.append(f"{feature_id}/{task_id} missing fields: {', '.join(missing)}")
            continue
        if require_ready and any(pattern.search(title + "\n" + block) for pattern in PLACEHOLDERS):
            errors.append(f"{feature_id}/{task_id} still contains template placeholders")

        sources = csv_ids(fields["來源"] or "", r"\b(?:REQ|NFR)-\d{3}\b")
        acceptances = csv_ids(fields["來源"] or "", rf"\bAC-{feature_id}-\d{{3}}\b")
        if not sources or not acceptances:
            errors.append(f"{feature_id}/{task_id} must source both REQ/NFR and {feature_id} AC")
        unknown_sources = sorted(sources - known_requirements)
        unknown_ac = sorted(acceptances - set(ac_ids))
        if unknown_sources:
            errors.append(f"{feature_id}/{task_id} references unknown requirements: {', '.join(unknown_sources)}")
        if unknown_ac:
            errors.append(f"{feature_id}/{task_id} references unknown AC: {', '.join(unknown_ac)}")
        outside_feature = sorted(sources - map_requirements)
        if outside_feature:
            errors.append(
                f"{feature_id}/{task_id} references requirements outside Map sources: "
                f"{', '.join(outside_feature)}"
            )
        task_sources.update(sources)
        task_acceptance.update(acceptances)

        dependencies_text = fields["依賴"] or ""
        dependencies = csv_ids(dependencies_text, r"\bT\d{3}\b")
        if dependencies_text.lower() not in {"無", "none"} and not dependencies:
            errors.append(f"{feature_id}/{task_id} dependency field must be 無 or TNNN IDs")
        unknown_dependencies = sorted(dependencies - known_tasks)
        if unknown_dependencies:
            errors.append(f"{feature_id}/{task_id} has unknown dependencies: {', '.join(unknown_dependencies)}")
        if task_id in dependencies:
            errors.append(f"{feature_id}/{task_id} cannot depend on itself")
        task_graph[task_id] = dependencies

    duplicate_titles = duplicate_ids(titles)
    if duplicate_titles:
        errors.append(f"{feature_id} contains duplicate task outcomes: {', '.join(duplicate_titles)}")
    cycle = find_cycle(task_graph)
    if cycle:
        errors.append(f"{feature_id} task dependency cycle: {' -> '.join(cycle)}")
    uncovered_ac = sorted(set(ac_ids) - task_acceptance)
    if uncovered_ac:
        errors.append(f"{feature_id} AC without task coverage: {', '.join(uncovered_ac)}")
    uncovered_sources = sorted(map_requirements - task_sources)
    if uncovered_sources:
        errors.append(f"{feature_id} mapped requirements without task coverage: {', '.join(uncovered_sources)}")

    count = len(tasks)
    if count < 6:
        warnings.append(f"{feature_id} has {count} tasks; review whether each task is independently verifiable")
    if count > 18:
        review_match = re.search(
            r"(?ms)^##\s+Task 數量複核\s*$\n(.*?)(?=^##\s+|\Z)",
            tasks_text,
        )
        reason_match = (
            re.search(r"(?m)^-\s*原因[：:]\s*(.+)$", review_match.group(1))
            if review_match
            else None
        )
        reason = reason_match.group(1).strip() if reason_match else ""
        if not reason or reason.startswith("不適用") or any(pattern.search(reason) for pattern in PLACEHOLDERS):
            errors.append(f"{feature_id} has more than 18 tasks without a concrete Task 數量複核 reason")

    if require_complete:
        if row["status"] != "completed":
            errors.append(f"{feature_id} feature-map status must be completed")
        if tasks_status != "completed":
            errors.append(f"{feature_id}/tasks.md status must be completed")
        incomplete = [str(task["id"]) for task in tasks if not bool(task["checked"])]
        if incomplete:
            errors.append(f"{feature_id} has incomplete tasks: {', '.join(incomplete)}")

    return mapped_prd_acceptance


def validate_project(
    project: Path,
    require_ready: bool = False,
    require_complete: bool = False,
    selected_features: set[str] | None = None,
) -> dict[str, object]:
    project = project.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    prd_path = project / "docs/PRD.md"
    product_spec_path = project / "docs/specs/product-spec.md"
    map_path = project / "docs/specs/feature-map.md"
    if not prd_path.is_file():
        errors.append("missing docs/PRD.md")
    if not product_spec_path.is_file():
        errors.append("missing docs/specs/product-spec.md")
    if not map_path.is_file():
        errors.append("missing docs/specs/feature-map.md")
    if errors:
        return {"ok": False, "project": str(project), "errors": errors, "warnings": warnings}

    prd_text = prd_path.read_text(encoding="utf-8")
    prd_meta = parse_frontmatter(prd_text)
    if prd_meta.get("document") != "product-prd" or prd_meta.get("status") != "confirmed":
        errors.append("docs/PRD.md must be a confirmed product-prd")
    known_requirements = prd_definitions(prd_text)
    if not known_requirements:
        errors.append("docs/PRD.md does not define REQ/NFR table rows")
    known_prd_acceptance = prd_acceptance_ids(prd_text)
    if not known_prd_acceptance:
        errors.append("docs/PRD.md does not define AC-NNN acceptance criteria")

    product_spec_text = product_spec_path.read_text(encoding="utf-8")
    product_spec_meta = parse_frontmatter(product_spec_text)
    if (
        product_spec_meta.get("document") != "product-spec"
        or product_spec_meta.get("status") != "confirmed"
    ):
        errors.append("docs/specs/product-spec.md must be a confirmed product-spec")
    known_product_contracts = product_contract_definitions(product_spec_text)
    if not known_product_contracts:
        errors.append("docs/specs/product-spec.md does not define PSC-NNN contract rows")

    map_text = map_path.read_text(encoding="utf-8")
    map_meta = parse_frontmatter(map_text)
    if map_meta.get("document") != "feature-map":
        errors.append("feature-map.md must declare document: feature-map")
    if map_meta.get("prd") != "docs/PRD.md":
        errors.append("feature-map.md must declare prd: docs/PRD.md")
    if map_meta.get("product_spec") != "docs/specs/product-spec.md":
        errors.append(
            "feature-map.md must declare product_spec: docs/specs/product-spec.md"
        )
    map_status = map_meta.get("status")
    if map_status not in {"draft", "confirmed"}:
        errors.append("feature-map.md status must be draft or confirmed")
    if (require_ready or require_complete) and map_status != "confirmed":
        errors.append("feature-map.md must have status: confirmed")
    if (require_ready or require_complete) and any(pattern.search(map_text) for pattern in PLACEHOLDERS):
        errors.append("confirmed feature-map.md still contains template placeholders")
    if require_ready or require_complete:
        validate_open_questions(map_text, "feature-map.md", errors)

    rows = feature_rows(map_text, errors)
    ids = [row["id"] for row in rows]
    directories = [row["directory"] for row in rows]
    for label, values in (("Feature ID", ids), ("Feature directory", directories)):
        duplicates = duplicate_ids(values)
        if duplicates:
            errors.append(f"duplicate {label}: {', '.join(duplicates)}")
    if not rows:
        errors.append("feature-map.md must define at least one Feature row")

    known_features = set(ids)
    assigned_requirements: set[str] = set()
    assigned_contracts: set[str] = set()
    graph: dict[str, set[str]] = {}
    for row in rows:
        if (require_ready or require_complete) and any(not value for value in row.values()):
            errors.append(f"{row['id']} Feature Map fields must be non-empty")
        match = FEATURE_DIR.fullmatch(row["directory"])
        if not match or match.group(1) != row["id"]:
            errors.append(f"{row['id']} has invalid directory {row['directory']}")
        sources = csv_ids(row["sources"], r"\b(?:REQ|NFR)-\d{3}\b")
        if not sources:
            errors.append(f"{row['id']} must map at least one REQ/NFR")
        unknown_sources = sorted(sources - known_requirements)
        if unknown_sources:
            errors.append(f"{row['id']} maps unknown requirements: {', '.join(unknown_sources)}")
        assigned_requirements.update(sources & known_requirements)
        contracts = csv_ids(row["sources"], r"\bPSC-\d{3}\b")
        if not contracts:
            errors.append(f"{row['id']} must map at least one PSC")
        unknown_contracts = sorted(contracts - known_product_contracts)
        if unknown_contracts:
            errors.append(
                f"{row['id']} maps unknown Product Spec contracts: "
                f"{', '.join(unknown_contracts)}"
            )
        assigned_contracts.update(contracts & known_product_contracts)
        dependencies = csv_ids(row["dependencies"], r"\bF\d{3}\b")
        if row["dependencies"].lower() not in {"無", "none"} and not dependencies:
            errors.append(f"{row['id']} dependency field must be 無 or FNNN IDs")
        unknown_dependencies = sorted(dependencies - known_features)
        if unknown_dependencies:
            errors.append(f"{row['id']} has unknown Feature dependencies: {', '.join(unknown_dependencies)}")
        if row["id"] in dependencies:
            errors.append(f"{row['id']} cannot depend on itself")
        graph[row["id"]] = dependencies
        if row["status"] not in {"planned", "in-progress", "completed", "deferred"}:
            errors.append(f"{row['id']} has invalid status {row['status']}")

    uncovered = sorted(known_requirements - assigned_requirements)
    if uncovered:
        errors.append(f"PRD requirements missing from Feature Map: {', '.join(uncovered)}")
    uncovered_contracts = sorted(known_product_contracts - assigned_contracts)
    if uncovered_contracts:
        errors.append(
            "Product Spec contracts missing from Feature Map: "
            + ", ".join(uncovered_contracts)
        )
    cycle = find_cycle(graph)
    if cycle:
        errors.append(f"Feature dependency cycle: {' -> '.join(cycle)}")

    selected = selected_features or known_features
    unknown_selected = sorted(selected - known_features)
    if unknown_selected:
        errors.append(f"requested unknown Features: {', '.join(unknown_selected)}")
    if require_complete:
        row_statuses = {row["id"]: row["status"] for row in rows}
        for feature_id in sorted(selected & known_features):
            incomplete_dependencies = sorted(
                dependency
                for dependency in graph.get(feature_id, set())
                if row_statuses.get(dependency) != "completed"
            )
            if incomplete_dependencies:
                errors.append(
                    f"{feature_id} cannot be complete before Feature dependencies: "
                    f"{', '.join(incomplete_dependencies)}"
                )

    mapped_prd_acceptance: set[str] = set()
    for row in rows:
        if row["id"] not in selected:
            continue
        mapped_prd_acceptance.update(
            validate_feature_docs(
                project,
                row,
                known_requirements,
                known_prd_acceptance,
                known_product_contracts,
                require_ready or require_complete,
                require_complete,
                errors,
                warnings,
            )
        )
    if (require_ready or require_complete) and selected == known_features:
        uncovered_prd_acceptance = sorted(known_prd_acceptance - mapped_prd_acceptance)
        if uncovered_prd_acceptance:
            errors.append(
                "PRD acceptance criteria missing from Feature specs: "
                + ", ".join(uncovered_prd_acceptance)
            )

    return {
        "ok": not errors,
        "project": str(project),
        "feature_map_status": map_status,
        "features": len(rows),
        "product_contracts": len(known_product_contracts),
        "validated_features": sorted(selected & known_features),
        "errors": errors,
        "warnings": warnings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--feature", action="append", default=[], help="Validate only this FNNN; repeatable")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selected = set(args.feature) if args.feature else None
    result = validate_project(
        args.project,
        require_ready=args.require_ready,
        require_complete=args.require_complete,
        selected_features=selected,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
