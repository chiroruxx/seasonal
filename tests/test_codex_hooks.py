"""Exercise real temporary repositories and subprocess checks, without Android or npm."""
import fcntl
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('hooks', Path(__file__).parents[1] / 'scripts/codex_hooks.py')
hooks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hooks)


class HookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.command('config', 'user.email', 'test@example.invalid')
        self.command('config', 'user.name', 'Test')
        (self.root / '.codex/hooks').mkdir(parents=True)
        (self.root / '.gitignore').write_text('.quality-results/\n')
        (self.root / 'note.md').write_text('initial\n')
        self.write_registry([self.check()])
        self.command('add', '.')
        self.command('commit', '-qm', 'initial')

    def command(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True)

    def check(self, exit_code=0):
        return {'id': 'example', 'paths': ['**/*.md'], 'status': 'connected',
                'commands': [{'all': ['python3', '-c', f'raise SystemExit({exit_code})']}]}

    def write_registry(self, checks):
        (self.root / '.codex/hooks/checks.json').write_text(json.dumps({'checks': checks}))

    def run_hook(self, event='PostToolUse', **extra):
        return hooks.run(self.root, {'hook_event_name': event, **extra})

    def report(self, result):
        return json.loads((self.root / result['report']).read_text())

    def test_clean_repo_does_not_run_checks(self):
        self.assertEqual(self.run_hook()['status'], 'unchanged')

    def test_changed_untracked_and_deleted_files_are_detected(self):
        (self.root / 'note.md').unlink()
        (self.root / 'new.md').write_text('new')
        result = self.run_hook()
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(self.report(result)['paths'], ['new.md', 'note.md'])
        self.assertEqual(self.run_hook()['status'], 'unchanged')

    def test_failures_are_not_cached_as_success(self):
        self.write_registry([self.check(7)])
        (self.root / 'note.md').write_text('changed')
        result = self.run_hook('Stop')
        self.assertEqual(result['status'], 'incomplete')
        cached = self.run_hook('Stop')
        self.assertEqual(cached['status'], 'incomplete')
        self.assertTrue(cached['cached'])
        self.assertEqual(hooks.feedback(cached, {'hook_event_name': 'Stop'})['decision'], 'block')
        self.assertNotIn('decision', hooks.feedback(cached, {'hook_event_name': 'Stop', 'stop_hook_active': True}))

    def test_missing_command_is_unavailable_even_in_full_mode(self):
        check = self.check()
        check.update(status='pending', commands=None)
        self.write_registry([check])
        result = hooks.run(self.root, {'hook_event_name': 'Stop'}, full=True)
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual(result['checks']['example'], 'unavailable')

    def test_formatter_state_does_not_trigger_recursive_checks(self):
        check = self.check()
        check['commands'] = [{'formatter': True, 'all': ['python3', '-c', "from pathlib import Path; Path('note.md').write_text('formatted')"]}]
        self.write_registry([check])
        (self.root / 'note.md').write_text('unformatted')
        self.assertEqual(self.run_hook()['status'], 'passed')
        self.assertEqual(self.run_hook()['status'], 'unchanged')

    def test_commit_change_invalidates_full_evidence(self):
        (self.root / 'note.md').write_text('changed')
        result = hooks.run(self.root, {'hook_event_name': 'Stop'}, full=True)
        old_head = self.report(result)['head']
        self.command('add', '.')
        self.command('commit', '-qm', 'second')
        result = hooks.run(self.root, {'hook_event_name': 'Stop'}, full=True)
        self.assertNotEqual(self.report(result)['head'], old_head)

    def test_unrelated_mutation_is_incomplete(self):
        check = self.check()
        check['commands'] = [{'all': ['python3', '-c', "from pathlib import Path; Path('other.md').write_text('concurrent')"]}]
        self.write_registry([check])
        (self.root / 'note.md').write_text('changed')
        result = self.run_hook()
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual(result['concurrent_changes'], ['other.md'])

    def test_overlapping_hook_does_not_claim_success(self):
        out = self.root / hooks.RESULTS
        out.mkdir(parents=True)
        with (out / 'lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(self.run_hook()['status'], 'busy')

    def test_check_mutation_of_in_scope_file_invalidates_evidence(self):
        check = self.check()
        check['commands'] = [{'all': ['python3', '-c', "from pathlib import Path; p=Path('note.md'); p.write_text(p.read_text()+'concurrent')"]}]
        self.write_registry([check])
        (self.root / 'note.md').write_text('changed')
        result = self.run_hook('Stop')
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual(result['concurrent_changes'], ['note.md'])
        state = json.loads((self.root / hooks.RESULTS / 'state.json').read_text())
        self.assertNotIn('full_key', state)
        self.assertIn('note.md', state['pending'])
        self.assertNotEqual(self.run_hook('Stop')['report'], result['report'])

    def test_head_change_during_check_invalidates_evidence(self):
        check = self.check()
        check['commands'] = [{'all': ['git', 'commit', '--allow-empty', '-qm', 'concurrent commit']}]
        self.write_registry([check])
        (self.root / 'note.md').write_text('changed')
        result = self.run_hook('Stop')
        self.assertEqual(result['status'], 'incomplete')
        report = self.report(result)
        self.assertNotEqual(report['head'], report['final_head'])
        state = json.loads((self.root / hooks.RESULTS / 'state.json').read_text())
        self.assertNotIn('full_key', state)
        self.assertIn('note.md', state['pending'])

    def test_busy_post_tool_use_preserves_tool_result_without_claiming_success(self):
        result = {'status': 'busy', 'reason': 'Another check is running'}
        feedback = hooks.feedback(result, {'hook_event_name': 'PostToolUse'})
        self.assertNotIn('decision', feedback)
        self.assertIn('still running', feedback['systemMessage'])
        self.assertEqual(hooks.feedback(result, {'hook_event_name': 'Stop'})['decision'], 'block')

    def test_explicit_full_uses_full_command_without_changing_normal_stop(self):
        check = self.check()
        check['commands'][0]['full'] = ['python3', '-c', 'raise SystemExit(9)']
        self.write_registry([check])
        (self.root / 'note.md').write_text('changed')
        self.assertEqual(self.run_hook('Stop')['status'], 'passed')
        result = hooks.run(self.root, {'hook_event_name': 'Stop'}, full=True)
        self.assertEqual(result['status'], 'incomplete')
        self.assertTrue(self.report(result)['explicit_full'])
        self.assertEqual(self.report(result)['checks'][0]['commands'][0]['exit_code'], 9)
        normal = self.run_hook('Stop')
        self.assertIn(normal['status'], ('passed', 'unchanged'))
        self.assertNotIn('cached', normal)

    def test_payload_cannot_supply_a_command(self):
        (self.root / 'note.md').write_text('changed')
        self.run_hook(tool_input={'command': "touch injected"}, cwd='/')
        self.assertFalse((self.root / 'injected').exists())


if __name__ == '__main__':
    unittest.main()
