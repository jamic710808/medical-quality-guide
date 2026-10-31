from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "validate_feature_specs.py"
SPEC = importlib.util.spec_from_file_location("validate_feature_specs", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def prd() -> str:
    return (
        "---\ndocument: product-prd\nstatus: confirmed\n---\n"
        "| REQ-001 | P0 | 需求 |\n"
        "| NFR-001 | 性能 | 要求 |\n"
        "### AC-001 · 產品驗收\n"
    )


def product_spec(status: str = "confirmed") -> str:
    return (
        "---\ndocument: product-spec\n"
        f"status: {status}\n"
        "prd: docs/PRD.md\n---\n"
        "| PSC-001 | 不變量 | REQ-001, NFR-001 | AC-001 | 合同 | 第 5 節 | 全產品 |\n"
        "- [PSC-001] 全局合同。\n"
    )


def feature_map(status: str = "confirmed", row_status: str = "planned") -> str:
    return (
        f"---\ndocument: feature-map\nstatus: {status}\n"
        "prd: docs/PRD.md\n"
        "product_spec: docs/specs/product-spec.md\n---\n"
        "## Feature Map\n"
        "| Feature ID | 目錄 | Feature | 用戶可觀察結果 | 來源合同 | 依賴 | 優先級 | 狀態 |\n"
        "|---|---|---|---|---|---|---|---|\n"
        f"| F001 | F001-example | 示例 | 用戶看到結果 | REQ-001, NFR-001, PSC-001 | 無 | P0 | {row_status} |\n"
    )


def feature_doc(name: str, status: str, headings: tuple[str, ...], body: str = "") -> str:
    document = {"spec.md": "feature-spec", "plan.md": "feature-plan", "tasks.md": "feature-tasks"}[name]
    rendered = "\n".join(f"## {heading}\n\n內容。" for heading in headings)
    return (
        "---\n"
        f"document: {document}\n"
        "feature: F001\n"
        f"status: {status}\n"
        "---\n\n"
        "# F001 · 示例 Feature\n\n"
        f"{rendered}\n{body}"
    )


def spec_body() -> str:
    return (
        "\n來源需求：REQ-001, NFR-001\n"
        "來源總規格：PSC-001\n"
        "### AC-F001-001 · 可觀察結果\n"
        "- 來源：REQ-001, NFR-001, PSC-001\n"
        "- 對應 PRD 驗收：AC-001\n"
        "- Given 用戶已進入入口\n"
        "- When 用戶執行動作\n"
        "- Then 用戶看到結果\n"
    )


def tasks_body(count: int = 6, checked: bool = False, forbidden: bool = False) -> str:
    rows: list[str] = []
    for number in range(1, count + 1):
        mark = "x" if checked else " "
        label = " [FE]" if forbidden and number == 1 else ""
        dependency = "無" if number == 1 else f"T{number - 1:03d}"
        rows.append(
            f"- [{mark}] T{number:03d} 獨立結果 {number}{label}\n"
            "  - 來源：REQ-001, NFR-001, AC-F001-001\n"
            f"  - 依賴：{dependency}\n"
            f"  - 修改：module/{number}\n"
            f"  - 完成證據：evidence/{number}\n"
            f"  - 驗證：test-{number}\n"
        )
    return "\n" + "\n".join(rows) + "\n- 原因：不適用\n"


class ValidateFeatureSpecsTests(unittest.TestCase):
    def make_project(
        self,
        *,
        task_count: int = 6,
        checked: bool = False,
        task_status: str = "planned",
        row_status: str = "planned",
        forbidden: bool = False,
    ) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        feature_root = root / "docs/specs/F001-example"
        feature_root.mkdir(parents=True)
        (root / "docs/PRD.md").write_text(prd(), encoding="utf-8")
        (root / "docs/specs/product-spec.md").write_text(
            product_spec(), encoding="utf-8"
        )
        (root / "docs/specs/feature-map.md").write_text(
            feature_map(row_status=row_status), encoding="utf-8"
        )
        (feature_root / "spec.md").write_text(
            feature_doc("spec.md", "ready", MODULE.REQUIRED_HEADINGS["spec.md"], spec_body()),
            encoding="utf-8",
        )
        (feature_root / "plan.md").write_text(
            feature_doc(
                "plan.md",
                "ready",
                MODULE.REQUIRED_HEADINGS["plan.md"],
                "\n| AC | 實現結果 | 最窄驗證方法 | 預期證據 |\n"
                "|---|---|---|---|\n"
                "| AC-F001-001 | 用戶得到結果 | 操作入口並核對結果 | 操作記錄 |\n",
            ),
            encoding="utf-8",
        )
        (feature_root / "tasks.md").write_text(
            feature_doc(
                "tasks.md",
                task_status,
                MODULE.REQUIRED_HEADINGS["tasks.md"],
                tasks_body(task_count, checked=checked, forbidden=forbidden),
            ),
            encoding="utf-8",
        )
        return temp, root

    def test_ready_feature_passes_without_technical_labels(self) -> None:
        temp, root = self.make_project()
        self.addCleanup(temp.cleanup)
        result = MODULE.validate_project(root, require_ready=True)
        self.assertTrue(result["ok"], result["errors"])

    def test_fe_label_is_rejected(self) -> None:
        temp, root = self.make_project(forbidden=True)
        self.addCleanup(temp.cleanup)
        result = MODULE.validate_project(root, require_ready=True)
        self.assertFalse(result["ok"])
        self.assertTrue(any("forbidden FE/BE/INT" in item for item in result["errors"]))

        tasks = root / "docs/specs/F001-example/tasks.md"
        tasks.write_text(
            tasks.read_text(encoding="utf-8").replace("獨立結果 1 [FE]", "FE 前端結果 1"),
            encoding="utf-8",
        )
        result = MODULE.validate_project(root, require_ready=True)
        self.assertFalse(result["ok"])
        self.assertTrue(any("forbidden FE/BE/INT" in item for item in result["errors"]))

    def test_dependency_cycle_is_rejected(self) -> None:
        temp, root = self.make_project()
        self.addCleanup(temp.cleanup)
        tasks = root / "docs/specs/F001-example/tasks.md"
        text = tasks.read_text(encoding="utf-8").replace("- 依賴：無", "- 依賴：T006", 1)
        tasks.write_text(text, encoding="utf-8")
        result = MODULE.validate_project(root, require_ready=True)
        self.assertFalse(result["ok"])
        self.assertTrue(any("dependency cycle" in item for item in result["errors"]))

    def test_prd_acceptance_must_be_carried_into_feature_spec(self) -> None:
        temp, root = self.make_project()
        self.addCleanup(temp.cleanup)
        spec = root / "docs/specs/F001-example/spec.md"
        spec.write_text(
            spec.read_text(encoding="utf-8").replace("- 對應 PRD 驗收：AC-001\n", ""),
            encoding="utf-8",
        )
        result = MODULE.validate_project(root, require_ready=True)
        self.assertFalse(result["ok"])
        self.assertTrue(any("對應 PRD 驗收" in item for item in result["errors"]))

    def test_product_spec_contract_must_be_mapped_and_carried(self) -> None:
        temp, root = self.make_project()
        self.addCleanup(temp.cleanup)
        feature_map_path = root / "docs/specs/feature-map.md"
        feature_map_path.write_text(
            feature_map_path.read_text(encoding="utf-8").replace(", PSC-001", ""),
            encoding="utf-8",
        )
        result = MODULE.validate_project(root, require_ready=True)
        self.assertFalse(result["ok"])
        self.assertTrue(any("must map at least one PSC" in item for item in result["errors"]))

    def test_more_than_eighteen_tasks_requires_reason(self) -> None:
        temp, root = self.make_project(task_count=19)
        self.addCleanup(temp.cleanup)
        result = MODULE.validate_project(root, require_ready=True)
        self.assertFalse(result["ok"])
        self.assertTrue(any("more than 18" in item for item in result["errors"]))

        tasks = root / "docs/specs/F001-example/tasks.md"
        tasks.write_text(
            tasks.read_text(encoding="utf-8").replace(
                "## Task 數量複核\n\n內容。",
                "## Task 數量複核\n\n- 任務總數：19\n- 原因：這些任務共同交付一個不可分割的事務結果，並分別驗證獨立失敗邊界。",
            ),
            encoding="utf-8",
        )
        result = MODULE.validate_project(root, require_ready=True)
        self.assertTrue(result["ok"], result["errors"])

    def test_map_and_tasks_status_must_match(self) -> None:
        temp, root = self.make_project(task_status="in-progress", row_status="planned")
        self.addCleanup(temp.cleanup)
        result = MODULE.validate_project(root, require_ready=True)
        self.assertFalse(result["ok"])
        self.assertTrue(any("does not match" in item for item in result["errors"]))

    def test_complete_feature_requires_all_tasks_checked(self) -> None:
        temp, root = self.make_project(task_status="completed", row_status="completed")
        self.addCleanup(temp.cleanup)
        result = MODULE.validate_project(root, require_complete=True, selected_features={"F001"})
        self.assertFalse(result["ok"])
        self.assertTrue(any("incomplete tasks" in item for item in result["errors"]))

        tasks = root / "docs/specs/F001-example/tasks.md"
        tasks.write_text(tasks.read_text(encoding="utf-8").replace("- [ ]", "- [x]"), encoding="utf-8")
        result = MODULE.validate_project(root, require_complete=True, selected_features={"F001"})
        self.assertTrue(result["ok"], result["errors"])

    def test_blank_given_when_then_are_rejected(self) -> None:
        for keyword, value in (("Given", "用戶已進入入口"), ("When", "用戶執行動作"), ("Then", "用戶看到結果")):
            with self.subTest(keyword=keyword):
                temp, root = self.make_project()
                self.addCleanup(temp.cleanup)
                path = root / "docs/specs/F001-example/spec.md"
                path.write_text(path.read_text().replace(f"- {keyword} {value}", f"- {keyword}   "))
                result = MODULE.validate_project(root, require_ready=True)
                self.assertFalse(result["ok"])
                self.assertTrue(any(f"missing non-empty {keyword}" in error for error in result["errors"]))

    def test_empty_task_fields_do_not_consume_the_next_line(self) -> None:
        for label, value in (("修改", "module/1"), ("完成證據", "evidence/1"), ("依賴", "無")):
            with self.subTest(label=label):
                temp, root = self.make_project()
                self.addCleanup(temp.cleanup)
                path = root / "docs/specs/F001-example/tasks.md"
                path.write_text(path.read_text().replace(f"  - {label}：{value}", f"  - {label}：", 1))
                result = MODULE.validate_project(root, require_ready=True)
                self.assertFalse(result["ok"])
                self.assertTrue(any(f"missing fields: {label}" in error for error in result["errors"]))

    def test_plan_requires_actual_acceptance_mapping(self) -> None:
        original = "| AC-F001-001 | 用戶得到結果 | 操作入口並核對結果 | 操作記錄 |"
        for replacement in ("正文提及 AC-F001-001", "| AC-F001-001 | 用戶得到結果 |   | 操作記錄 |"):
            with self.subTest(replacement=replacement):
                temp, root = self.make_project()
                self.addCleanup(temp.cleanup)
                path = root / "docs/specs/F001-example/plan.md"
                path.write_text(path.read_text().replace(original, replacement))
                result = MODULE.validate_project(root, require_ready=True)
                self.assertFalse(result["ok"])
                self.assertTrue(any("plan.md" in error for error in result["errors"]))

    def test_eval_column_and_escaped_pipe_keep_mapping_valid(self) -> None:
        temp, root = self.make_project()
        self.addCleanup(temp.cleanup)
        path = root / "docs/specs/F001-example/plan.md"
        path.write_text(path.read_text().replace(
            "| AC-F001-001 | 用戶得到結果 | 操作入口並核對結果 | 操作記錄 |",
            r"| AC-F001-001 | EV-F001-001 | 顯示 A \| B | 操作入口並核對結果 | 操作記錄 |",
        ))
        result = MODULE.validate_project(root, require_ready=True)
        self.assertTrue(result["ok"], result["errors"])

    def test_blocking_questions_prevent_ready_in_map_spec_and_plan(self) -> None:
        for relative in ("feature-map.md", "F001-example/spec.md", "F001-example/plan.md"):
            with self.subTest(relative=relative):
                temp, root = self.make_project()
                self.addCleanup(temp.cleanup)
                path = root / "docs/specs" / relative
                path.write_text(path.read_text() + "\n| OQ-001 | 核心規則未確認 | 是 | 開發前確認 | 待確認 | |\n")
                result = MODULE.validate_project(root, require_ready=True)
                self.assertFalse(result["ok"])
                self.assertTrue(any("blocking open question" in error for error in result["errors"]))

    def test_nonblocking_and_resolved_questions_can_proceed(self) -> None:
        temp, root = self.make_project()
        self.addCleanup(temp.cleanup)
        path = root / "docs/specs/F001-example/spec.md"
        path.write_text(path.read_text() + "\n| OQ-001 | 試用假設 | 否 | 試用後統計 | 待確認 | |\n"
                        "| OQ-002 | 範圍確認 | 是 | 開發前確認 | 已解決 | 見已確認 DEC-001 |\n")
        result = MODULE.validate_project(root, require_ready=True)
        self.assertTrue(result["ok"], result["errors"])

    def test_map_empty_outcome_or_invalid_dependency_is_rejected(self) -> None:
        for old, new in (("用戶看到結果", "   "), ("| 無 |", "| 稍後再看 |")):
            with self.subTest(field=old):
                temp, root = self.make_project()
                self.addCleanup(temp.cleanup)
                path = root / "docs/specs/feature-map.md"
                path.write_text(path.read_text().replace(old, new))
                result = MODULE.validate_project(root, require_ready=True)
                self.assertFalse(result["ok"])

    def test_selected_feature_does_not_require_other_drafts_ready(self) -> None:
        temp, root = self.make_project()
        self.addCleanup(temp.cleanup)
        path = root / "docs/specs/feature-map.md"
        path.write_text(path.read_text() + "\n| F002 | F002-later | 後續結果 | 後續可觀察結果 | REQ-001, PSC-001 | F001 | P1 | deferred |\n")
        result = MODULE.validate_project(root, require_ready=True, selected_features={"F001"})
        self.assertTrue(result["ok"], result["errors"])


if __name__ == "__main__":
    unittest.main()
