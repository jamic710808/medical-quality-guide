from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "validate_product_spec.py"
SPEC = importlib.util.spec_from_file_location("validate_product_spec", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def prd() -> str:
    return (
        "---\ndocument: product-prd\nstatus: confirmed\n---\n"
        "| REQ-001 | P0 | 需求 |\n"
        "| NFR-001 | 安全 | 要求 |\n"
        "### AC-001 · 產品驗收\n"
    )


def product_spec(status: str = "confirmed") -> str:
    headings = "\n".join(f"## {heading}\n\n內容。" for heading in MODULE.REQUIRED_HEADINGS)
    headings = headings.replace(
        "## 跨 Feature 不變量與共享行為\n\n內容。",
        "## 跨 Feature 不變量與共享行為\n\n- [PSC-001] 所有功能遵守統一狀態與安全合同。",
    )
    return (
        "---\n"
        "document: product-spec\n"
        f"status: {status}\n"
        "prd: docs/PRD.md\n"
        "---\n\n"
        "# 產品總規格\n\n"
        f"{headings}\n\n"
        "| PSC-001 | 不變量 | REQ-001, NFR-001 | AC-001 | 統一合同 | 第 5 節 | 全產品 |\n"
    )


class ValidateProductSpecTests(unittest.TestCase):
    def make_project(self, spec_text: str) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        (root / "docs/specs").mkdir(parents=True)
        (root / "docs/PRD.md").write_text(prd(), encoding="utf-8")
        (root / "docs/specs/product-spec.md").write_text(spec_text, encoding="utf-8")
        return temp, root

    def test_confirmed_product_spec_passes(self) -> None:
        temp, root = self.make_project(product_spec())
        self.addCleanup(temp.cleanup)
        result = MODULE.validate_product_spec(root, require_confirmed=True)
        self.assertTrue(result["ok"], result["errors"])

    def test_draft_is_valid_but_not_confirmed(self) -> None:
        temp, root = self.make_project(product_spec("draft"))
        self.addCleanup(temp.cleanup)
        self.assertTrue(MODULE.validate_product_spec(root)["ok"])
        result = MODULE.validate_product_spec(root, require_confirmed=True)
        self.assertFalse(result["ok"])
        self.assertIn("product-spec.md must have status: confirmed", result["errors"])

    def test_missing_prd_coverage_fails(self) -> None:
        text = product_spec().replace("REQ-001, NFR-001", "REQ-001")
        temp, root = self.make_project(text)
        self.addCleanup(temp.cleanup)
        result = MODULE.validate_product_spec(root)
        self.assertFalse(result["ok"])
        self.assertTrue(any("NFR-001" in item for item in result["errors"]))

    def test_duplicate_contract_id_fails(self) -> None:
        text = product_spec() + "\n| PSC-001 | 安全 | REQ-001 | AC-001 | 重複 | 第 7 節 | 全產品 |\n"
        temp, root = self.make_project(text)
        self.addCleanup(temp.cleanup)
        result = MODULE.validate_product_spec(root)
        self.assertFalse(result["ok"])
        self.assertTrue(any("duplicate PSC" in item for item in result["errors"]))

    def test_confirmed_placeholder_fails(self) -> None:
        temp, root = self.make_project(product_spec() + "\n【待填寫】\n")
        self.addCleanup(temp.cleanup)
        result = MODULE.validate_product_spec(root)
        self.assertFalse(result["ok"])
        self.assertIn(
            "confirmed product-spec.md still contains template placeholders",
            result["errors"],
        )

    def test_index_or_change_log_mentions_do_not_replace_contract_body(self) -> None:
        text = product_spec().replace(
            "- [PSC-001] 所有功能遵守統一狀態與安全合同。", "無"
        ).replace("第 5 節", "PSC-001") + "\n變更記錄：更新 PSC-001。\n"
        temp, root = self.make_project(text)
        self.addCleanup(temp.cleanup)
        result = MODULE.validate_product_spec(root, require_confirmed=True)
        self.assertFalse(result["ok"])
        self.assertTrue(any("detailed contract section" in error for error in result["errors"]))

    def test_confirmed_empty_contract_fields_fail(self) -> None:
        for value in ("統一合同", "第 5 節", "全產品"):
            with self.subTest(field=value):
                temp, root = self.make_project(product_spec().replace(f"| {value} |", "|   |"))
                self.addCleanup(temp.cleanup)
                result = MODULE.validate_product_spec(root, require_confirmed=True)
                self.assertFalse(result["ok"])
                self.assertTrue(any("non-empty" in error for error in result["errors"]))

    def test_escaped_pipe_in_contract_is_valid(self) -> None:
        temp, root = self.make_project(product_spec().replace("統一合同", r"顯示 A \| B"))
        self.addCleanup(temp.cleanup)
        result = MODULE.validate_product_spec(root, require_confirmed=True)
        self.assertTrue(result["ok"], result["errors"])

    def test_open_question_states_and_resolution(self) -> None:
        for status, blocking, conclusion, expected in (
            ("open", "是", "", False), ("待確認", "是", "", False),
            ("處理中", "是", "", False), ("待確認", "否", "", True),
            ("已解決", "是", "", False), ("done", "是", "已處理", False),
            ("已關閉", "是", "見 PSD-001，用戶確認原約定", True),
        ):
            with self.subTest(status=status, blocking=blocking, conclusion=conclusion):
                text = product_spec() + f"\n| OQ-001 | 對象規則待確認 | {blocking} | 實施前核對 PSD-001 | {status} | {conclusion} |\n"
                temp, root = self.make_project(text)
                self.addCleanup(temp.cleanup)
                result = MODULE.validate_product_spec(root, require_confirmed=True)
                self.assertEqual(result["ok"], expected, result)


if __name__ == "__main__":
    unittest.main()
