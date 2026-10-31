from __future__ import annotations

import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "init_project.py"
PRD_VALIDATOR = SCRIPT.parents[2] / "product-prd/scripts/validate_prd.py"
EXPECTED_LOGO_SHA256 = "522944bbaee48d98190c8c5a0a0ac80f05b71b1975838807742a782e2aeceedc"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class InitProjectTest(unittest.TestCase):
    def run_script(self, project: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(project),
                "--public-name",
                "FF - 測試產品",
                "--summary",
                "幫助用戶完成一個可觀察任務。",
                *extra,
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_creates_standard_skeleton_and_renders_product_facts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "AgenticRAG"
            result = self.run_script(project)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["project_directory_name"], "AgenticRAG")
            self.assertIn("frontend", report["created_directories"])
            self.assertIn("backend", report["created_directories"])
            self.assertTrue((project / "docs/verification").is_dir())
            self.assertTrue((project / "docs/specs/feature-map.md").is_file())
            self.assertTrue((project / "docs/specs/product-spec.md").is_file())
            logo = project / "frontend/public/brand/ff-logo.png"
            self.assertTrue(logo.is_file())
            self.assertEqual(sha256(logo), EXPECTED_LOGO_SHA256)
            self.assertIn(
                "frontend/public/brand/ff-logo.png",
                report["created_files"],
            )
            self.assertFalse((project / "docs/plans/implementation-plan.md").exists())
            self.assertEqual((project / "CLAUDE.md").read_text(), "@AGENTS.md\n")
            agents = (project / "AGENTS.md").read_text()
            self.assertIn("FF - 測試產品", agents)
            self.assertIn("AgenticRAG", agents)
            self.assertIn("frontend/public/brand/ff-logo.png", agents)
            self.assertIn(EXPECTED_LOGO_SHA256, agents)
            self.assertIn("@賦範空間 獨家研發", agents)
            self.assertIn("@賦範空間 獨家研發", (project / "README.md").read_text())
            self.assertNotIn("{{PUBLIC_NAME}}", (project / "docs/PRD.md").read_text())
            self.assertIn(
                "Feature Map",
                (project / "docs/specs/feature-map.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "產品總規格",
                (project / "docs/specs/product-spec.md").read_text(encoding="utf-8"),
            )
            draft_validation = subprocess.run(
                [sys.executable, str(PRD_VALIDATOR), str(project)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(draft_validation.returncode, 0, draft_validation.stdout)
            confirmed_validation = subprocess.run(
                [sys.executable, str(PRD_VALIDATOR), str(project), "--require-confirmed"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(confirmed_validation.returncode, 0)

    def test_keeps_existing_files_on_repeat_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "OcrPlatform"
            first = self.run_script(project)
            self.assertEqual(first.returncode, 0, first.stderr)
            readme = project / "README.md"
            readme.write_text("user-owned\n", encoding="utf-8")

            second = self.run_script(project)
            self.assertEqual(second.returncode, 0, second.stderr)
            report = json.loads(second.stdout)
            self.assertIn("README.md", report["kept_files"])
            self.assertIn("frontend/public/brand/ff-logo.png", report["kept_files"])
            self.assertEqual(readme.read_text(encoding="utf-8"), "user-owned\n")

    def test_refuses_to_overwrite_a_different_logo_before_other_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "AgenticRAG"
            logo = project / "frontend/public/brand/ff-logo.png"
            logo.parent.mkdir(parents=True)
            logo.write_bytes(b"user-owned-logo")

            result = self.run_script(project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("refusing to overwrite", result.stderr)
            self.assertEqual(logo.read_bytes(), b"user-owned-logo")
            self.assertFalse((project / "README.md").exists())

    def test_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "AgenticRAG"
            result = self.run_script(project, "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(project.exists())

    def test_occupied_paths_fail_before_any_generated_files(self) -> None:
        for relative, directory in (("backend", False), ("docs", False),
                                    ("docs/PRD.md", True), ("CLAUDE.md", True)):
            for dry_run in (False, True):
                with self.subTest(relative=relative, dry_run=dry_run), tempfile.TemporaryDirectory() as temp:
                    project = Path(temp) / "Project"
                    occupied = project / relative
                    occupied.parent.mkdir(parents=True, exist_ok=True)
                    if directory:
                        occupied.mkdir()
                    else:
                        occupied.write_text("user-owned")
                    before = sorted(str(path.relative_to(project)) for path in project.rglob("*"))
                    result = self.run_script(project, *(('--dry-run',) if dry_run else ()))
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("occupied", result.stderr)
                    self.assertEqual(before, sorted(str(path.relative_to(project)) for path in project.rglob("*")))
                    if not directory:
                        self.assertEqual(occupied.read_text(), "user-owned")

    def test_linked_directory_outside_project_is_rejected_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "Project"
            outside = Path(temp) / "Outside"
            project.mkdir()
            outside.mkdir()
            (project / "docs").symlink_to(outside, target_is_directory=True)
            result = self.run_script(project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("outside project", result.stderr)
            self.assertFalse((project / "frontend").exists())
            self.assertEqual(list(outside.iterdir()), [])

    def test_rejects_non_pascal_case_project_folder_without_writing(self) -> None:
        invalid_names = ("agentic-rag", "agentic_rag", "ocrPlatform", "中文項目")
        with tempfile.TemporaryDirectory() as temp:
            for invalid_name in invalid_names:
                with self.subTest(invalid_name=invalid_name):
                    project = Path(temp) / invalid_name
                    result = self.run_script(project)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("PascalCase", result.stderr)
                    self.assertFalse(project.exists())


if __name__ == "__main__":
    unittest.main()
