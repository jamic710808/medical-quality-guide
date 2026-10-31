from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "validate_prd.py"
SPEC = importlib.util.spec_from_file_location("validate_prd", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def valid_prd(status: str = "confirmed") -> str:
    headings = "\n".join(f"## {heading}\n\n內容。" for heading in MODULE.REQUIRED_HEADINGS)
    return (
        "---\n"
        "document: product-prd\n"
        f"status: {status}\n"
        'updated: "2026-08-12"\n'
        "---\n\n"
        "# Example PRD\n\n"
        f"{headings}\n\n"
        "| REQ-001 | P0 | 用戶完成任務 | 觸發 | 狀態變化 | 結果 | 恢復 |\n"
        "| NFR-001 | 性能 | 一秒內完成 | 全鏈路 |\n\n"
        "### AC-001 · 完成任務\n\n"
        "- 來源：REQ-001, NFR-001\n"
        "- Given 用戶已進入產品\n"
        "- When 用戶提交任務\n"
        "- Then 一秒內看到完成結果\n"
    )


class ValidatePrdTests(unittest.TestCase):
    def make_project(self, text: str) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        (root / "docs").mkdir()
        (root / "docs/PRD.md").write_text(text, encoding="utf-8")
        return temp, root

    def validate(self, text: str) -> dict[str, object]:
        temp, root = self.make_project(text)
        self.addCleanup(temp.cleanup)
        return MODULE.validate_prd(root)

    def test_confirmed_prd_passes(self) -> None:
        temp, root = self.make_project(valid_prd())
        self.addCleanup(temp.cleanup)
        result = MODULE.validate_prd(root, require_confirmed=True)
        self.assertTrue(result["ok"], result["errors"])

    def test_draft_is_valid_but_not_confirmed(self) -> None:
        temp, root = self.make_project(valid_prd("draft"))
        self.addCleanup(temp.cleanup)
        self.assertTrue(MODULE.validate_prd(root)["ok"])
        result = MODULE.validate_prd(root, require_confirmed=True)
        self.assertFalse(result["ok"])
        self.assertIn("docs/PRD.md must have status: confirmed", result["errors"])

    def test_missing_acceptance_coverage_fails(self) -> None:
        text = valid_prd().replace("REQ-001, NFR-001", "REQ-001")
        temp, root = self.make_project(text)
        self.addCleanup(temp.cleanup)
        result = MODULE.validate_prd(root)
        self.assertFalse(result["ok"])
        self.assertTrue(any("NFR-001" in item for item in result["errors"]))

    def test_prd_requires_a_non_functional_baseline(self) -> None:
        text = valid_prd().replace("| NFR-001 | 性能 | 一秒內完成 | 全鏈路 |\n", "").replace(
            "REQ-001, NFR-001", "REQ-001"
        )
        temp, root = self.make_project(text)
        self.addCleanup(temp.cleanup)
        result = MODULE.validate_prd(root)
        self.assertFalse(result["ok"])
        self.assertIn("docs/PRD.md must define at least one NFR-NNN table row", result["errors"])

    def test_confirmed_placeholder_fails(self) -> None:
        temp, root = self.make_project(valid_prd() + "\n【待填寫】\n")
        self.addCleanup(temp.cleanup)
        result = MODULE.validate_prd(root)
        self.assertFalse(result["ok"])
        self.assertIn(
            "confirmed docs/PRD.md still contains template placeholders",
            result["errors"],
        )

    def test_blank_acceptance_steps_fail(self) -> None:
        steps = {
            "Given": "用戶已進入產品",
            "When": "用戶提交任務",
            "Then": "一秒內看到完成結果",
        }
        for keyword, content in steps.items():
            for blank in ("", "   ", "\t"):
                with self.subTest(keyword=keyword, blank=repr(blank)):
                    text = valid_prd().replace(f"- {keyword} {content}", f"- {keyword}{blank}")
                    result = self.validate(text)
                    self.assertFalse(result["ok"])
                    self.assertIn(f"AC-001 missing non-empty {keyword}", result["errors"])

    def test_empty_or_incomplete_requirement_rows_fail_when_confirmed(self) -> None:
        rows = (
            ("| REQ-001 | P0 | 用戶完成任務 | 觸發 | 狀態變化 | 結果 | 恢復 |", 7),
            ("| NFR-001 | 性能 | 一秒內完成 | 全鏈路 |", 4),
        )
        for original, count in rows:
            cells = [cell.strip() for cell in original[1:-1].split("|")]
            replacements = [f"| {cells[0]} |"]
            for index in range(1, count):
                empty = cells.copy()
                empty[index] = "  "
                replacements.append("| " + " | ".join(empty) + " |")
            for replacement in replacements:
                with self.subTest(row=replacement):
                    result = self.validate(valid_prd().replace(original, replacement))
                    self.assertFalse(result["ok"])
                    self.assertTrue(any(f"{cells[0]} must contain" in item for item in result["errors"]))

    def test_draft_keeps_unfilled_requirement_cells(self) -> None:
        text = valid_prd("draft").replace(
            "| REQ-001 | P0 | 用戶完成任務 | 觸發 | 狀態變化 | 結果 | 恢復 |",
            "| REQ-001 | P0 | 【待填寫】 | | | | |",
        )
        self.assertTrue(self.validate(text)["ok"])

    def test_extended_requirement_rows_pass_with_evidence_and_trace(self) -> None:
        text = valid_prd().replace(
            "| REQ-001 | P0 | 用戶完成任務 | 觸發 | 狀態變化 | 結果 | 恢復 |",
            "| REQ-001 | P0 | 用戶完成任務 | 觸發 | 狀態變化 | 結果 | 恢復 | "
            "用戶指令 DEC-001 已確認 | GOAL-001 / J-001 | 核心任務 |",
        ).replace(
            "| NFR-001 | 性能 | 一秒內完成 | 全鏈路 |",
            "| NFR-001 | 性能 | 一秒內完成 | 全鏈路 | DEC-001 已確認 | GOAL-001 |",
        )
        result = self.validate(text)
        self.assertTrue(result["ok"], result["errors"])
        empty_evidence = text.replace("DEC-001 已確認 | GOAL-001 |", " | GOAL-001 |")
        self.assertFalse(self.validate(empty_evidence)["ok"])

    def test_escaped_pipe_does_not_create_an_empty_cell(self) -> None:
        text = valid_prd().replace("| 結果 |", r"| 顯示 A \|\| B 文本 |")
        result = self.validate(text)
        self.assertTrue(result["ok"], result["errors"])

    def test_duplicate_requirement_ids_still_fail(self) -> None:
        for row in (
            "| REQ-001 | P0 | 重複需求 | 觸發 | 行為 | 輸出 | 恢復 |",
            "| NFR-001 | 安全 | 權限邊界 | 全產品 |",
        ):
            with self.subTest(row=row):
                result = self.validate(valid_prd() + "\n" + row)
                self.assertFalse(result["ok"])
                self.assertTrue(any("duplicate" in error for error in result["errors"]))

    def test_unresolved_blocking_questions_fail_in_chinese_and_english(self) -> None:
        for status in ("open", "待確認", "處理中"):
            with self.subTest(status=status):
                text = valid_prd() + f"\n| OQ-001 | 核心範圍未確認 | 是 | 實施前由產品負責人確認 | {status} | |\n"
                result = self.validate(text)
                self.assertFalse(result["ok"])
                self.assertIn("confirmed docs/PRD.md still contains a blocking open question", result["errors"])

    def test_nonblocking_assumption_with_verification_plan_passes(self) -> None:
        for status in ("open", "待確認", "處理中"):
            with self.subTest(status=status):
                text = valid_prd() + f"\n| OQ-001 | 假設試用量足夠，影響基線採樣 | 否 | 試用一週後統計樣本量 | {status} | |\n"
                result = self.validate(text)
                self.assertTrue(result["ok"], result["errors"])

    def test_closed_questions_require_resolution_evidence(self) -> None:
        for status in ("closed", "已解決", "已關閉"):
            for ending in ("", "   |"):
                with self.subTest(status=status, ending=ending):
                    text = valid_prd() + f"\n| OQ-001 | 範圍確認 | 是 | 實施前確認 | {status} |{ending}\n"
                    result = self.validate(text)
                    self.assertFalse(result["ok"])
                    self.assertTrue(any("resolution and supporting evidence" in error for error in result["errors"]))
            text = valid_prd() + f"\n| OQ-001 | 範圍確認 | 是 | 實施前確認 | {status} | 用戶在 DEC-001 確認保留原範圍 |\n"
            result = self.validate(text)
            self.assertTrue(result["ok"], result["errors"])

    def test_unknown_question_status_or_blocking_flag_cannot_bypass_gate(self) -> None:
        for flag, status in (("是", "done"), ("是/否", "open"), ("未知", "已解決")):
            with self.subTest(flag=flag, status=status):
                text = valid_prd() + f"\n| OQ-001 | 範圍確認 | {flag} | 實施前確認 | {status} | 見 DEC-001 |\n"
                result = self.validate(text)
                self.assertFalse(result["ok"])
                self.assertTrue(any("unknown" in error for error in result["errors"]))

    def test_nonblocking_question_still_requires_verification_plan(self) -> None:
        text = valid_prd() + "\n| OQ-001 | 假設待驗證 | 否 |   | 待確認 | |\n"
        result = self.validate(text)
        self.assertFalse(result["ok"])
        self.assertTrue(any("verification plan" in error for error in result["errors"]))

    def test_requirement_count_alone_does_not_trigger_warning(self) -> None:
        text = valid_prd()
        ids = [f"REQ-{index:03d}" for index in range(2, 14)]
        text += "\n" + "\n".join(
            f"| {requirement} | P1 | 配套需求 | 觸發 | 行為 | 輸出 | 恢復 |" for requirement in ids
        )
        text = text.replace("- 來源：REQ-001, NFR-001", "- 來源：REQ-001, NFR-001, " + ", ".join(ids))
        result = self.validate(text)
        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual(result["requirements"], 13)
        self.assertEqual(result["warnings"], [])


if __name__ == "__main__":
    unittest.main()
