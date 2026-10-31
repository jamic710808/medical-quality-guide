import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


SCRIPT = Path(__file__).resolve().parents[1] / "inspect_inputs.py"
spec = importlib.util.spec_from_file_location("inspect_inputs", SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class InputProbeTests(unittest.TestCase):
    def test_csv_keeps_identifiers_and_quoted_record_boundaries(self):
        data = '\ufeff編號,備註\r\n00123,"第一行\n第二行"\r\n00007,NA\r\n'.encode("utf-8")
        result = probe.text_profile(data, ".csv", False, 25)
        self.assertEqual(result["sample_records"], 3)
        self.assertEqual(result["sample_column_counts"], [2])
        self.assertIn("00123", result["preview"])
        self.assertIn("00007", result["preview"])
        self.assertEqual(result["first_record"], ["編號", "備註"])

    def test_partial_json_is_not_called_invalid(self):
        result = probe.text_profile(b'{"items": [1,', ".json", True, 25)
        self.assertEqual(result["json_validation"], "not_checked_incomplete_sample")
        complete = probe.text_profile(b'{"items": [1,', ".json", False, 25)
        self.assertEqual(complete["json_validation"], "invalid")

    def test_truncated_utf8_character_does_not_change_encoding(self):
        data = '記錄末尾漢'.encode("utf-8")[:-1]
        text, encoding = probe.decode_sample(data, True)
        self.assertEqual(encoding, "utf-8-sig")
        self.assertEqual(text, "記錄末尾")

    def test_jsonl_checks_only_complete_sample_records(self):
        result = probe.text_profile(b'{"id":"001"}\nnot-json\n{"id":', ".jsonl", True, 25)
        self.assertEqual(result["jsonl_checked_records"], 2)
        self.assertEqual(result["jsonl_invalid_lines"], [2])

    def test_inventory_excludes_links_hidden_files_and_reports_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.csv").write_text("id\n001\n")
            (root / "b.txt").write_text("two")
            (root / ".env").write_text("SECRET=do-not-read")
            (root / "alias.csv").symlink_to(root / "a.csv")
            files, skipped, truncated = probe.inventory([root], 10)
            self.assertEqual({p.name for p in files}, {"a.csv", "b.txt"})
            self.assertFalse(truncated)
            self.assertEqual({r["reason"] for r in skipped},
                             {"hidden_or_protected_path", "symlink_not_followed"})
            files, _, truncated = probe.inventory([root], 1)
            self.assertEqual(len(files), 1)
            self.assertTrue(truncated)

    def test_container_type_comes_from_contents_without_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "misnamed.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("word/document.xml", "<document/>")
            result = probe.inspect_file(path, 65536, 25, 3)
            self.assertEqual(result["format"], "docx_container")
            self.assertFalse(result["content"]["business_content_read"])
            self.assertEqual([p.name for p in path.parent.iterdir()], ["misnamed.zip"])

    def test_cli_reports_missing_inputs_and_does_not_modify_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = b'id,amount\n00123,19.50\n'
            data = root / "records.csv"
            data.write_bytes(original)
            result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(data),
                                     str(root / "missing.csv")], capture_output=True, text=True, check=True)
            report = json.loads(result.stdout)
            self.assertEqual(report["files_selected"], 1)
            self.assertEqual(report["skipped"][0]["reason"], "missing")
            self.assertEqual(data.read_bytes(), original)
            self.assertEqual([p.name for p in root.iterdir()], ["records.csv"])


if __name__ == "__main__":
    unittest.main()
