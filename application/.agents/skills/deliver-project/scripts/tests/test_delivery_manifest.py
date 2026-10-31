"""Behavioral checks use isolated local files and never touch a user project."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "delivery_manifest.py"
SPEC = importlib.util.spec_from_file_location("delivery_manifest", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DeliveryManifestTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="delivery-skill-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "項目"
        self.root.mkdir()
        self.write("src/query.py", "def query():\n    return {'status': 'waiting'}\n")
        self.write("docs/spec.md", "AC-01：訂單查詢返回當前狀態。\n")
        self.write("docs/verification.md", "AC-01：pass；目標環境接手：not_run。\n")
        self.write("docs/delivery/README.md", "# 交付\n本地查詢已驗收，目標環境接手和用戶簽收未發生。\n")
        self.manifest = "docs/delivery/delivery-manifest.json"
        self.definition = {
            "schema_version": 1, "project": "訂單協同", "release": "v1-review",
            "scope": "訂單查詢本地交付",
            "inputs": [{"path": "src/query.py", "role": "實現"},
                       {"path": "docs/spec.md", "role": "規格"},
                       {"path": "docs/verification.md", "role": "驗證"}],
            "artifacts": [{"id": "D-01", "title": "交付入口",
                           "path": "docs/delivery/README.md", "audience": "recipient"}],
            "omissions": [{"id": "D-02", "title": "目標環境接手記錄",
                           "reason": "目標環境尚未提供", "next_step": "由運維提供環境後執行接手檢查"}],
        }
        self.save(self.definition)

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def save(self, definition):
        self.write(self.manifest, json.dumps(definition, ensure_ascii=False))

    def run_operation(self, operation):
        return MODULE.process(operation, self.root, self.manifest)

    def snapshot(self):
        result = self.run_operation("snapshot")
        self.assertTrue(result["ok"], result)

    def test_snapshot_and_readonly_check_keep_omissions_and_no_signoff(self):
        original = (self.root / "src/query.py").read_bytes()
        self.snapshot()
        manifest = self.root / self.manifest
        before = manifest.read_bytes()
        result = self.run_operation("check")
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["omissions"], 1)
        self.assertEqual(result["behavior"], "not_evaluated")
        self.assertEqual(result["recipient_signoff"], "not_evaluated")
        self.assertEqual(manifest.read_bytes(), before)
        self.assertEqual((self.root / "src/query.py").read_bytes(), original)
        saved = json.loads(before)
        self.assertEqual(saved["inputs"][0]["sha256"], hashlib.sha256(original).hexdigest())

    def test_source_and_artifact_drift_are_detected(self):
        self.snapshot()
        self.write("src/query.py", "def query():\n    return {'status': 'done'}\n")
        self.write("docs/delivery/README.md", "# 未核實的更新\n")
        result = self.run_operation("check")
        self.assertFalse(result["ok"])
        self.assertEqual(len(result["errors"]), 2)
        self.assertIn("src/query.py", " ".join(result["errors"]))
        self.assertIn("docs/delivery/README.md", " ".join(result["errors"]))

    def test_missing_file_preserves_existing_manifest(self):
        self.snapshot()
        before = (self.root / self.manifest).read_bytes()
        (self.root / "docs/spec.md").unlink()
        for operation in ("snapshot", "check"):
            result = self.run_operation(operation)
            self.assertFalse(result["ok"], result)
            self.assertEqual((self.root / self.manifest).read_bytes(), before)

    def test_outside_paths_directories_and_self_reference_are_rejected(self):
        for path in ("../outside.txt", "/etc/hosts", "C:/outside.txt", "docs", self.manifest):
            with self.subTest(path=path):
                definition = copy.deepcopy(self.definition)
                definition["inputs"][0]["path"] = path
                self.save(definition)
                self.assertFalse(self.run_operation("snapshot")["ok"])

    def test_external_symlink_is_rejected(self):
        outside = Path(self.temporary.name) / "outside.txt"
        outside.write_text("must not be read", encoding="utf-8")
        (self.root / "outside-link").symlink_to(outside)
        self.definition["inputs"][0]["path"] = "outside-link"
        self.save(self.definition)
        self.assertFalse(self.run_operation("snapshot")["ok"])

    def test_missing_hash_does_not_pass_as_verified(self):
        result = self.run_operation("check")
        self.assertFalse(result["ok"])
        self.assertIn("SHA-256", " ".join(result["errors"]))

    def test_empty_deliverable_is_rejected_but_empty_source_is_valid(self):
        self.write("src/query.py", "")
        self.snapshot()
        self.write("docs/delivery/README.md", "")
        self.assertFalse(self.run_operation("snapshot")["ok"])

    def test_duplicate_delivery_and_omission_id_is_rejected(self):
        self.definition["omissions"][0]["id"] = "D-01"
        self.save(self.definition)
        self.assertFalse(self.run_operation("snapshot")["ok"])

    def test_invalid_schema_and_audience_fail_without_overwrite(self):
        for update in ({"schema_version": True}, {"inputs": []}, {"omissions": "none"}):
            with self.subTest(update=update):
                self.save(dict(self.definition, **update))
                before = (self.root / self.manifest).read_bytes()
                self.assertFalse(self.run_operation("snapshot")["ok"])
                self.assertEqual((self.root / self.manifest).read_bytes(), before)
        self.definition["artifacts"][0]["audience"] = "public"
        self.save(self.definition)
        self.assertFalse(self.run_operation("snapshot")["ok"])

    def test_invalid_json_returns_error_without_echoing_contents(self):
        self.write(self.manifest, '{"private-value": not-valid-json}')
        result = self.run_operation("snapshot")
        self.assertFalse(result["ok"])
        self.assertNotIn("private-value", json.dumps(result))

    def test_cli_exit_status_and_movable_project(self):
        command = [sys.executable, "-B", str(SCRIPT), "snapshot", "--project", str(self.root),
                   "--manifest", self.manifest]
        snapshot = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(snapshot.returncode, 0, snapshot.stdout + snapshot.stderr)
        moved = self.root.with_name("接手項目")
        self.root.rename(moved)
        command[3] = "check"
        command[5] = str(moved)
        checked = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        (moved / "src/query.py").write_text("changed", encoding="utf-8")
        changed = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(changed.returncode, 1)
        self.assertFalse(json.loads(changed.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
