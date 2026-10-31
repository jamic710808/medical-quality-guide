import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "validate_evals.py"
MAINTENANCE = SCRIPT.parents[2] / "maintain-project/scripts/maintenance.py"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_module("project_evals_validator", SCRIPT)
RECORDER = load_module("eval_test_recorder", MAINTENANCE)


class ProjectEvalsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "Project"
        self.root.mkdir()
        self.sources = ["docs/PRD.md", "docs/specs/product-spec.md", "docs/specs/F001-export/spec.md"]
        self.write(self.sources[0], "---\ndocument: product-prd\nstatus: confirmed\n---\n"
                   "### AC-001 · 按權限導出訂單，保留查詢行為\n")
        self.write(self.sources[1], "---\ndocument: product-spec\nstatus: confirmed\n---\n"
                   "| PSC-001 | 權限隔離 |\n| PSC-002 | 查詢與導出狀態一致 |\n")
        self.write(self.sources[2], "---\ndocument: feature-spec\nfeature: F001\nstatus: ready\n---\n"
                   "### AC-F001-001 · 導出篩選結果\n"
                   "### AC-F001-002 · 拒絕未授權導出\n"
                   "### AC-F001-003 · 既有查詢仍返回完整訂單\n")
        self.data = {
            "schema_version": 1, "scope": "F001", "sources": self.sources,
            "cases": [
                {"id": "EV-F001-001", "title": "導出篩選結果", "source_ac": ["AC-F001-001"],
                 "given": "三筆訂單中兩筆待交付，用戶有導出權限", "when": "導出待交付訂單",
                 "expected": ["輸出恰為 O-001 和 O-003 且無重複"], "check_ref": None},
                {"id": "EV-F001-002", "title": "權限", "source_ac": ["AC-F001-002"],
                 "given": "用戶沒有導出權限", "when": "導出訂單", "expected": ["拒絕導出"], "check_ref": None},
                {"id": "EV-F001-003", "title": "保留查詢", "source_ac": ["AC-F001-003"],
                 "given": "三筆訂單", "when": "使用原查詢", "expected": ["仍返回三筆訂單"], "check_ref": None}
            ], "checks": []
        }

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def save(self, name="evals/F001.json"):
        self.write(name, json.dumps(self.data, ensure_ascii=False, indent=2))

    def validate(self, bound=False, name="evals/F001.json"):
        self.save(name)
        return VALIDATOR.validate_project(self.root, [name], bound)

    def bind(self, method="command"):
        for case in self.data["cases"]:
            case["check_ref"] = "F001-order-export"
        self.write("backend/exporter.py", "def query(rows):\n    return rows\n")
        self.write("backend/tests/orders.json", json.dumps([
            {"id": "O-001", "status": "pending"}, {"id": "O-002", "status": "done"},
            {"id": "O-003", "status": "pending"}
        ]))
        self.write("backend/tests/check_export.py", '''import importlib.util
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("exporter", root / "backend/exporter.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
rows = json.loads((root / "backend/tests/orders.json").read_text())
ids = [row["id"] for row in module.export(rows, "pending", True)]
assert sorted(ids) == ["O-001", "O-003"], ids
print("EV-F001-001: pass")
try:
    module.export(rows, "pending", False)
except PermissionError:
    pass
else:
    raise AssertionError("unauthorized export")
print("EV-F001-002: pass")
assert module.query(rows) == rows
print("EV-F001-003: pass")
''')
        check = {"id": "F001-order-export", "method": method,
                 "inputs": ["backend/exporter.py", "backend/tests/check_export.py", "backend/tests/orders.json"]}
        if method == "command":
            check["argv"] = [sys.executable, "-B", "backend/tests/check_export.py"]
        else:
            check.update(procedure="分別執行導出、拒絕未授權導出及舊查詢，逐項對照預期。", evidence="操作記錄與實際輸出文件")
        self.data["checks"] = [check]

    def test_draft_is_valid_but_cannot_claim_bound_or_behavior_pass(self):
        result = self.validate()
        self.assertTrue(result["ok"], result)
        self.assertEqual(len(result["suites"][0]["unbound"]), 3)
        self.assertEqual(result["behavior"], "not_evaluated")
        self.assertFalse(self.validate(bound=True)["ok"])

    def test_missing_ac_coverage_is_rejected(self):
        self.data["cases"].pop()
        result = self.validate()
        self.assertFalse(result["ok"])
        self.assertIn("AC-F001-003", str(result["errors"]))

    def test_mentions_and_fenced_examples_are_not_source_definitions(self):
        path = self.root / self.sources[2]
        path.write_text(path.read_text() + "\n引用 AC-F001-099\n```md\n### AC-F001-098\n```\n")
        self.assertTrue(self.validate()["ok"])
        for value in ["AC-F001-099", "AC-F001-098"]:
            with self.subTest(value=value):
                self.data["cases"][0]["source_ac"] = [value]
                self.assertFalse(self.validate()["ok"])

    def test_duplicate_and_dangling_references_are_rejected(self):
        self.data["cases"][1]["id"] = self.data["cases"][0]["id"]
        self.assertFalse(self.validate()["ok"])
        self.data["cases"][1]["id"] = "EV-F001-002"
        self.data["cases"][0]["check_ref"] = "undefined-check"
        self.assertFalse(self.validate()["ok"])

    def test_bound_checks_track_suite_sources_implementation_tests_and_data(self):
        self.bind()
        result = self.validate(bound=True)
        self.assertTrue(result["ok"], result)
        check = result["suites"][0]["checks"][0]
        self.assertEqual(set(check["effective_inputs"]), set(self.sources + ["evals/F001.json"] + self.data["checks"][0]["inputs"]))
        (self.root / "backend/tests/orders.json").unlink()
        self.assertFalse(self.validate(bound=True)["ok"])

    def test_binding_requires_confirmed_sources(self):
        self.bind()
        path = self.root / self.sources[0]
        path.write_text(path.read_text().replace("status: confirmed", "status: draft"))
        self.assertTrue(self.validate()["ok"])
        self.assertFalse(self.validate(bound=True)["ok"])

    def test_supporting_sources_do_not_define_acceptance_or_contract_ids(self):
        self.data["sources"].append("docs/shared.md")
        self.write("docs/shared.md", "# 輔助說明\n### AC-999 · 討論中的示例\n"
                   "| PSC-001 | 引用已有合同的說明 |\n| PSC-999 | 候選合同 |\n")
        self.bind()
        result = self.validate(bound=True)
        self.assertTrue(result["ok"], result)
        self.data["cases"][0]["source_ac"].append("AC-999")
        self.assertFalse(self.validate(bound=True)["ok"])
        self.data["cases"][0]["source_ac"].pop()
        self.data["cases"][0]["source_psc"] = ["PSC-999"]
        self.assertFalse(self.validate(bound=True)["ok"])

    def test_feature_acceptance_ids_must_match_source_feature(self):
        path = self.root / self.sources[2]
        path.write_text(path.read_text() + "\n### AC-F002-001 · 錯放的驗收\n")
        result = self.validate()
        self.assertFalse(result["ok"])
        self.assertIn("來源文檔類型或 Feature 不符", str(result["errors"]))

    def test_manual_binding_is_not_an_automatic_pass(self):
        self.bind(method="manual")
        result = self.validate(bound=True)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["behavior"], "not_evaluated")
        self.data["checks"][0]["argv"] = ["echo", "PASS"]
        self.assertFalse(self.validate(bound=True)["ok"])

    def test_product_suite_covers_declared_cross_feature_contracts(self):
        self.data.update(scope="product", product_contracts=["PSC-001", "PSC-002"])
        for index, case in enumerate(self.data["cases"]):
            case.update(id=f"EV-PRODUCT-{index + 1:03d}", source_psc=["PSC-001"])
        self.assertFalse(self.validate(name="evals/product.json")["ok"])
        self.data["cases"][2]["source_psc"] = ["PSC-002"]
        self.assertTrue(self.validate(name="evals/product.json")["ok"])

    def test_invalid_commands_and_escaping_inputs_are_rejected(self):
        self.bind()
        self.data["checks"][0]["argv"] = []
        self.assertFalse(self.validate(bound=True)["ok"])
        self.data["checks"][0]["argv"] = ["python3", "backend/tests/check_export.py"]
        self.data["checks"][0]["inputs"].append("../outside")
        self.assertFalse(self.validate(bound=True)["ok"])
        self.data["checks"][0]["inputs"].pop()
        (self.root / "backend/tests/outside").symlink_to(self.root.parent)
        self.data["checks"][0]["inputs"] = ["backend/tests"]
        self.assertFalse(self.validate(bound=True)["ok"])

    def test_cli_is_read_only_and_never_executes_declared_commands(self):
        self.bind()
        self.data["checks"][0]["argv"] = [sys.executable, "-c", "from pathlib import Path; Path('unwanted').touch()"]
        self.save()
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(self.root), "--suite", "evals/F001.json", "--require-bound"],
                                cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["behavior"], "not_evaluated")
        self.assertFalse((self.root / "unwanted").exists())

    def test_real_behavior_failure_fix_and_stale_evidence_with_existing_recorder(self):
        self.bind()
        suite = self.validate(bound=True)
        self.assertTrue(suite["ok"], suite)
        check = suite["suites"][0]["checks"][0]
        RECORDER.begin(self.root, {"id": "export-feature", "request": "實現有權限的篩選導出，保留查詢",
                                  "sources": ["backend/exporter.py"], "checks": [check["id"]]}, None)
        state = RECORDER.read_state(self.root, "export-feature")
        broken = "def query(rows):\n    return rows\n\ndef export(rows, status, authorized):\n    return rows\n"
        self.write("backend/exporter.py", broken)
        self.assertEqual(RECORDER.evaluate(self.root, state)["status"], "not_run")
        failed = RECORDER.run_check(self.root, state, check["id"], check["argv"], check["effective_inputs"], 10)
        self.assertEqual(failed["status"], "fail")
        self.write("backend/exporter.py", "def query(rows):\n    return rows\n\ndef export(rows, status, authorized):\n"
                   "    if not authorized:\n        raise PermissionError('export denied')\n"
                   "    return [row for row in rows if row['status'] == status]\n")
        passed = RECORDER.run_check(self.root, state, check["id"], check["argv"], check["effective_inputs"], 10)
        self.assertEqual(passed["status"], "pass")
        self.assertEqual(RECORDER.evaluate(self.root, state)["status"], "pass")
        output = (self.root / passed["receipt"]["output_path"]).read_text()
        for identity in ["EV-F001-001", "EV-F001-002", "EV-F001-003"]:
            self.assertIn(identity + ": pass", output)
        self.write("backend/tests/orders.json", "[]")
        stale = RECORDER.evaluate(self.root, state)
        self.assertEqual(stale["status"], "fail")
        self.assertTrue(any("證據已過期" in issue for issue in stale["issues"]))
        self.assertIn("/.codex/maintenance/", (self.root / ".gitignore").read_text())


if __name__ == "__main__":
    unittest.main()
