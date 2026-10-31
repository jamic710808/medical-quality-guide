import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/maintenance.py'
spec = importlib.util.spec_from_file_location('maintenance', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        for name, content in {'ui/app.txt': 'before', 'design/current.md': 'before',
                              'design/unchanged.md': 'keep', 'sources/customer.txt': 'raw'}.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        self.scope = {'id': 'change-1', 'request': 'adjust existing UI', 'sources': ['ui/app.txt'],
                      'documents': [{'path': 'design/current.md', 'action': 'update', 'reason': 'behavior changed'},
                                    {'path': 'design/unchanged.md', 'action': 'keep', 'reason': 'not affected'}],
                      'protected': ['sources'], 'checks': ['behavior']}
        m.begin(self.root, self.scope, 'session-a')

    def tearDown(self):
        self.temp.cleanup()

    def change(self, docs=True):
        (self.root / 'ui/app.txt').write_text('after')
        if docs:
            (self.root / 'design/current.md').write_text('new behavior')

    def run_actual_check(self):
        return m.run_check(self.root, m.read_state(self.root, 'change-1'), 'behavior',
                           [sys.executable, '-c', "from pathlib import Path; assert Path('ui/app.txt').read_text() == 'after'; print('behavior verified')"], [], 10)

    def result(self):
        return m.evaluate(self.root, m.read_state(self.root, 'change-1'))

    def test_real_check_and_document_sync_on_non_course_paths(self):
        self.change()
        self.assertEqual(self.run_actual_check()['status'], 'pass')
        self.assertEqual(self.result()['status'], 'pass')
        self.assertEqual((self.root / '.gitignore').read_text(), '/.codex/maintenance/\n')

    def test_missing_document_cannot_pass_with_successful_code_check(self):
        self.change(docs=False)
        self.run_actual_check()
        result = self.result()
        self.assertEqual(result['status'], 'fail')
        self.assertTrue(any('design/current.md' in item for item in result['issues']))

    def test_changed_source_invalidates_only_prior_evidence(self):
        self.change()
        self.run_actual_check()
        (self.root / 'ui/app.txt').write_text('later change')
        self.assertTrue(any('證據已過期' in item for item in self.result()['issues']))

    def test_changed_linked_directory_input_invalidates_evidence(self):
        self.change()
        (self.root / 'data').mkdir()
        (self.root / 'inputs').mkdir()
        (self.root / 'data/sample.txt').write_text('expected')
        (self.root / 'inputs/shared').symlink_to(self.root / 'data', target_is_directory=True)
        result = m.run_check(self.root, m.read_state(self.root, 'change-1'), 'behavior',
                             [sys.executable, '-c', "from pathlib import Path; assert Path('inputs/shared/sample.txt').read_text() == 'expected'"],
                             ['inputs'], 10)
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(self.result()['status'], 'pass')
        (self.root / 'data/sample.txt').write_text('changed')
        self.assertTrue(any('證據已過期' in item for item in self.result()['issues']))

    def test_cyclic_directory_input_is_rejected(self):
        (self.root / 'inputs').mkdir()
        (self.root / 'inputs/cycle').symlink_to(self.root / 'inputs', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, '循環目錄鏈接'):
            m.fingerprint(self.root, 'inputs')

    def test_authorized_source_removal_can_be_verified(self):
        (self.root / 'ui/app.txt').unlink()
        (self.root / 'design/current.md').write_text('removed feature')
        result = m.run_check(self.root, m.read_state(self.root, 'change-1'), 'behavior',
                             [sys.executable, '-c', "from pathlib import Path; assert not Path('ui/app.txt').exists()"], [], 10)
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(self.result()['status'], 'pass')

    def test_protected_and_kept_documents_are_not_silently_changed(self):
        self.change()
        self.run_actual_check()
        (self.root / 'sources/customer.txt').write_text('overwritten')
        (self.root / 'design/unchanged.md').write_text('unrelated change')
        issues = self.result()['issues']
        self.assertTrue(any('保護路徑' in item for item in issues))
        self.assertTrue(any('應保留' in item for item in issues))

    def test_not_run_and_execution_error_are_not_success(self):
        self.change()
        self.assertEqual(self.result()['status'], 'not_run')
        result = m.run_check(self.root, m.read_state(self.root, 'change-1'), 'behavior',
                             ['/does-not-exist/maintenance-test-tool'], [], 10)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(self.result()['status'], 'error')

    def test_exit_status_overrules_success_words(self):
        self.change()
        result = m.run_check(self.root, m.read_state(self.root, 'change-1'), 'behavior',
                             [sys.executable, '-c', "print('PASS'); raise SystemExit(3)"], [], 10)
        self.assertEqual(result['status'], 'fail')
        self.assertEqual(self.result()['status'], 'fail')

    def test_hook_is_scoped_and_does_not_loop_or_write_business_files(self):
        self.change(docs=False)
        self.run_actual_check()
        before = {p: m.fingerprint(self.root, p) for p in ['ui/app.txt', 'design/current.md', 'sources']}
        self.assertIsNone(m.hook(self.root, {'hook_event_name': 'Stop', 'session_id': 'other-session'}))
        self.assertIsNone(m.hook(self.root, {'hook_event_name': 'Stop', 'session_id': 'session-a', 'cwd': '/another-project'}))
        event = {'hook_event_name': 'Stop', 'session_id': 'session-a'}
        self.assertEqual(m.hook(self.root, event)['decision'], 'block')
        self.assertNotIn('decision', m.hook(self.root, event))
        self.assertNotIn('decision', m.hook(self.root, {**event, 'stop_hook_active': True}))
        self.assertEqual(before, {p: m.fingerprint(self.root, p) for p in before})
        state = m.read_state(self.root, 'change-1')
        state['state'] = 'paused'
        m.write_json(m.state_path(self.root, 'change-1'), state)
        self.assertIsNone(m.hook(self.root, event))

    def test_duplicate_scope_and_outside_paths_do_not_reset_baseline(self):
        with self.assertRaises(ValueError):
            m.begin(self.root, self.scope, 'session-a')
        self.assertEqual(m.read_state(self.root, 'change-1')['before']['ui/app.txt'], m.digest(b'before'))
        with self.assertRaises(ValueError):
            m.begin(self.root, {**self.scope, 'id': 'outside', 'sources': ['../outside.txt']}, 'session-b')


if __name__ == '__main__':
    unittest.main()
