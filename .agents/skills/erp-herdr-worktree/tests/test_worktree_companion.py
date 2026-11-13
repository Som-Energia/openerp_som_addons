#!/usr/bin/env python3
"""Isolated CLI regression tests; never contact the user's app or ERP."""
from __future__ import absolute_import, division

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
MOCK = r'''#!/usr/bin/env python3
import json
import os
import shlex
import sys

path = os.environ['MOCK_STATE']
with open(path) as stream:
    state = json.load(stream)
kind = os.path.basename(sys.argv[0])
args = sys.argv[1:]
state['calls'].append([kind] + args)
result = {}
if state.get('fail') == kind:
    with open(path, 'w') as stream:
        json.dump(state, stream)
    sys.exit(1)
if kind == 'app':
    if args == ['ls']:
        result = {'spaces': [{'id': 's1', 'machine': state.get('machine'),
                  'tabs': state['tabs']}]}
    elif args == ['status']:
        result = state['status']
    elif args[0] == 'do':
        name, values = args[1], json.loads(args[2])
        if name == 'pane.split':
            state['tabs'][0]['terminals'].append(
                {'terminal': 't9', 'pane': 'p9'})
            state['infos']['t9'] = {
                'state': 'live', 'cwd': '/stale', 'labels': {},
                'foreground': {'cwd': values['argv'][4]}}
            if state.get('slow_start'):
                state['infos']['t9']['foreground'] = None
            result = {'pane': 'p9', 'terminal': 't9'}
        elif name == 'pane.focus':
            if state.get('fail_focus'):
                with open(path, 'w') as stream:
                    json.dump(state, stream)
                sys.exit(1)
            state['status']['focused_pane'] = values['pane']
            result = {'ok': True}
        else:
            raise AssertionError(args)
    else:
        raise AssertionError(args)
elif kind == 'core':
    if args[0] == 'get':
        result = state['infos'][args[1]]
    elif args[0] == 'label':
        if state.get('fail_label'):
            with open(path, 'w') as stream:
                json.dump(state, stream)
            sys.exit(1)
        labels = state['infos'][args[1]].setdefault('labels', {})
        labels.update(item.split('=', 1) for item in args[2:])
    else:
        raise AssertionError(args)
elif kind == 'legacy':
    action = args[1]
    if action == 'current':
        result = {'result': {'pane': {'tab_id': 'tab1'}}}
    elif action == 'list':
        result = {'result': {'panes': state['panes']}}
    elif action == 'split':
        result = {'result': {'pane': {'pane_id': 'p9'}}}
    elif action == 'process-info':
        result = {'result': {'process_info': {
            'shell_pid': 10, 'foreground_processes': [{
                'pid': 10, 'name': state.get('process_name', 'bash'),
                'cwd': state.get('foreground_cwd', '/old')}]}}}
    elif action == 'run':
        state['foreground_cwd'] = shlex.split(args[3])[2]
    elif action not in ('rename', 'report-metadata'):
        raise AssertionError(args)
else:
    raise AssertionError(kind)
with open(path, 'w') as stream:
    json.dump(state, stream)
print(json.dumps(result))
'''


class CompanionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "primary ' ; $(not-run)"
        self.repo.mkdir()
        self.git('init', '-q', '-b', 'main')
        self.git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                 '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'initial',
                 '--allow-empty')
        self.git('remote', 'add', 'origin', str(self.repo))
        self.scripts = self.repo / '.agents/skills/erp-herdr-worktree/scripts'
        shutil.copytree(SCRIPTS, self.scripts)
        self.state_path = self.root / 'state.json'
        self.state = {
            'calls': [],
            'tabs': [{'id': 'tab1', 'terminals': [
                {'terminal': 't1', 'pane': 'p1'}]}],
            'status': {'tab': 'tab1', 'focused_pane': 'p1'},
            'infos': {'t1': {'address': 't1', 'state': 'live',
                             'cwd': str(self.repo),
                             'foreground': {'cwd': str(self.repo)},
                             'labels': {'herdr.space': 's1',
                                        'herdr.tab': 'tab1'}}},
            'panes': [{'pane_id': 'p1', 'tab_id': 'tab1', 'cwd': '/workspace'}],
        }
        self.env = dict(os.environ)
        for key in ('HERDR_ENV', 'HERDR_PANE_ID', 'HC_TERMINAL_ID'):
            self.env.pop(key, None)
        self.env['HC_TERMINAL_ID'] = 't1'
        self.env['MOCK_STATE'] = str(self.state_path)
        for name, variable in [('app', 'HERDR_APP_BIN_PATH'),
                               ('core', 'HC_BIN_PATH'),
                               ('legacy', 'HERDR_BIN_PATH')]:
            binary = self.root / name
            binary.write_text(MOCK)
            binary.chmod(0o755)
            self.env[variable] = str(binary)

    def git(self, *args):
        command = ['git', '-C', str(self.repo)] + list(args)
        return subprocess.check_output(command, stderr=subprocess.STDOUT)

    def run_wrapper(self, *args, **kwargs):
        self.state_path.write_text(json.dumps(self.state))
        result = subprocess.run(
            ['bash', str(self.scripts / 'erp-herdr-worktree.sh')] + list(args),
            env=self.env, text=True, capture_output=True, timeout=15)
        self.state = json.loads(self.state_path.read_text())
        self.assertEqual(result.returncode, kwargs.get('code', 0),
                         result.stdout + result.stderr)
        return result

    def open(self, code=0):
        return self.run_wrapper('open', str(self.repo), code=code)

    def add_terminal(self, terminal='t2', cwd=None, labeled=False, tab=0):
        self.state['tabs'][tab]['terminals'].append(
            {'terminal': terminal, 'pane': 'p' + terminal[1:]})
        self.state['infos'][terminal] = {
            'state': 'live', 'cwd': '/stale-launch-cwd',
            'foreground': {'cwd': cwd or str(self.repo)},
            'labels': {'erp.role': 'worktree-companion'} if labeled else {}}

    def app_actions(self):
        return [call[2] for call in self.state['calls']
                if call[:2] == ['app', 'do']]

    def legacy(self):
        self.env.update(HERDR_ENV='1', HERDR_PANE_ID='p1')

    def test_app_creates_explicit_split_quotes_path_and_restores_focus(self):
        self.state['status']['focused_pane'] = 'p-other'
        result = self.open()
        self.assertIn('Created worktree companion: t9', result.stdout)
        self.assertEqual(self.app_actions(), ['pane.split', 'pane.focus'])
        split = next(call for call in self.state['calls']
                     if call[:3] == ['app', 'do', 'pane.split'])
        values = json.loads(split[3])
        self.assertEqual(values['pane'], 'p1')
        self.assertEqual(values['argv'][4], str(self.repo))
        self.assertEqual(values['argv'][2], 'cd -- "$1" && exec "$2"')
        self.assertEqual(self.state['status']['focused_pane'], 'p-other')
        self.assertEqual(self.state['infos']['t1']['labels']['erp.companion'],
                         't9')
        self.assertFalse(any(call[0] == 'legacy'
                             for call in self.state['calls']))

    def test_app_repeated_open_reuses_without_split(self):
        self.open()
        self.state['calls'] = []
        result = self.open()
        self.assertIn('Reusing worktree companion: t9', result.stdout)
        self.assertEqual(self.app_actions(), [])

    def test_app_reuses_foreground_not_launch_cwd(self):
        self.add_terminal()
        self.assertIn('Reusing worktree companion: t2', self.open().stdout)
        self.assertEqual(self.app_actions(), [])

    def test_app_does_not_reuse_launch_cwd(self):
        self.add_terminal(cwd='/somewhere-else')
        self.state['infos']['t2']['cwd'] = str(self.repo)
        self.assertIn('Created worktree companion: t9', self.open().stdout)

    def test_app_does_not_reuse_other_tabs(self):
        self.state['tabs'].append({'id': 'tab2', 'terminals': []})
        self.add_terminal(tab=1)
        self.assertIn('Created worktree companion: t9', self.open().stdout)

    def test_app_refuses_labeled_companion_at_another_cwd(self):
        self.add_terminal(cwd='/old', labeled=True)
        self.assertIn('Cannot safely retarget', self.open(code=1).stderr)
        self.assertEqual(self.app_actions(), [])
        self.assertFalse(any(call[1] in ('send', 'keys', 'kill')
                             for call in self.state['calls']))

    def test_app_refuses_unknown_foreground(self):
        self.add_terminal(labeled=True)
        self.state['infos']['t2']['foreground'] = None
        self.open(code=1)
        self.assertEqual(self.app_actions(), [])

    def test_app_refuses_mismatched_core_session(self):
        self.state['infos']['t1']['labels']['herdr.tab'] = 'another-session'
        self.assertIn('identity mismatch', self.open(code=1).stderr)
        self.assertEqual(self.app_actions(), [])

    def test_app_refuses_conflicting_labeled_companion(self):
        self.add_terminal(cwd='/old', labeled=True)
        self.add_terminal(terminal='t3')
        self.assertIn('Ambiguous', self.open(code=1).stderr)
        self.assertEqual(self.app_actions(), [])

    def test_app_refuses_multiple_matches(self):
        self.add_terminal()
        self.add_terminal(terminal='t3')
        self.assertIn('Ambiguous', self.open(code=1).stderr)
        self.assertEqual(self.app_actions(), [])

    def test_app_refuses_hidden_caller_before_creating_git_worktree(self):
        self.state['tabs'][0]['terminals'] = []
        target = self.root / 'openerp_som_addons-worktrees/new'
        self.run_wrapper('create', str(target), 'FIX_test', code=1)
        self.assertFalse(target.exists())
        self.assertEqual(self.git('branch', '--list', 'FIX_test'), b'')
        self.assertEqual(self.app_actions(), [])

    def test_app_refuses_remote_space(self):
        self.state['machine'] = 'remote'
        self.assertIn('remote app space', self.open(code=1).stderr)
        self.assertEqual(self.app_actions(), [])

    def test_app_does_not_select_another_tab(self):
        self.state['status']['tab'] = 'tab2'
        self.open(code=1)
        self.assertEqual(self.app_actions(), [])

    def test_app_core_unavailable_does_not_mutate_layout(self):
        self.state['fail'] = 'core'
        self.open(code=1)
        self.assertEqual(self.app_actions(), [])

    def test_app_failure_does_not_fall_back_to_legacy(self):
        self.state['fail'] = 'app'
        self.open(code=1)
        self.assertFalse(any(call[0] == 'legacy'
                             for call in self.state['calls']))

    def test_slow_start_records_companion_and_does_not_duplicate(self):
        self.state['slow_start'] = True
        self.open(code=1)
        self.state['calls'] = []
        self.open(code=1)
        self.assertEqual(self.app_actions(), [])

    def test_focus_failure_records_companion_before_retry(self):
        self.state.update(slow_start=True, fail_focus=True)
        self.open(code=1)
        self.assertEqual(self.app_actions(), ['pane.split', 'pane.focus'])
        labels = self.state['infos']['t9']['labels']
        self.assertEqual(labels['erp.role'], 'worktree-companion')
        self.assertEqual(labels['erp.owner'], 't1')
        self.assertEqual(labels['erp.worktree'], str(self.repo))
        self.assertEqual(self.state['infos']['t1']['labels']['erp.companion'],
                         't9')

        self.state['fail_focus'] = False
        self.state['calls'] = []
        self.assertIn('Cannot safely retarget', self.open(code=1).stderr)
        self.assertEqual(self.app_actions(), [])
        self.assertEqual(len(self.state['tabs'][0]['terminals']), 2)

        self.state['infos']['t9']['foreground'] = {'cwd': str(self.repo)}
        self.state['calls'] = []
        self.assertIn('Reusing worktree companion: t9', self.open().stdout)
        self.assertEqual(self.app_actions(), [])

    def test_registration_failure_still_restores_focus(self):
        self.state['fail_label'] = True
        self.open(code=1)
        self.assertEqual(self.app_actions(), ['pane.split', 'pane.focus'])

    def test_app_create_then_open_new_registered_worktree(self):
        target = self.root / 'openerp_som_addons-worktrees/new'
        result = self.run_wrapper('create', str(target), 'FIX_test')
        self.assertIn('Created worktree companion', result.stdout)
        self.assertEqual(subprocess.check_output(
            ['git', '-C', str(target), 'branch', '--show-current']),
            b'FIX_test\n')
        self.assertEqual(self.git('rev-parse', 'origin/main'),
                         subprocess.check_output(
                             ['git', '-C', str(target), 'rev-parse', 'HEAD']))

    def test_no_environment_refuses(self):
        self.env.pop('HC_TERMINAL_ID')
        self.open(code=1)
        self.assertEqual(self.state['calls'], [])

    def test_legacy_split_with_both_environments_prefers_tui(self):
        self.legacy()
        self.open()
        self.assertTrue(all(call[0] == 'legacy'
                            for call in self.state['calls']))
        split = next(call for call in self.state['calls']
                     if call[1:3] == ['pane', 'split'])
        self.assertIn('--no-focus', split)
        self.assertEqual(split[split.index('--cwd') + 1], str(self.repo))

    def test_legacy_reuses_existing_same_tab(self):
        self.legacy()
        self.state['panes'].append(
            {'pane_id': 'p2', 'tab_id': 'tab1', 'cwd': str(self.repo)})
        self.assertIn('Reusing worktree companion: p2', self.open().stdout)
        self.assertFalse(any(call[1:3] == ['pane', 'split']
                             for call in self.state['calls']))

    def test_legacy_caller_itself_is_not_a_companion(self):
        self.legacy()
        self.state['panes'][0]['cwd'] = str(self.repo)
        self.assertIn('Created worktree companion: p9', self.open().stdout)

    def test_legacy_retargets_idle_shell(self):
        self.legacy()
        self.state['panes'].append({'pane_id': 'p2', 'tab_id': 'tab1',
                                    'cwd': '/old', 'label': 'worktree · old'})
        self.assertIn('Retargeted worktree companion: p2', self.open().stdout)
        self.assertEqual(self.state['foreground_cwd'], str(self.repo))

    def test_legacy_refuses_busy_shell(self):
        self.legacy()
        self.state['panes'].append({'pane_id': 'p2', 'tab_id': 'tab1',
                                    'cwd': '/old', 'label': 'worktree · old'})
        self.state['process_name'] = 'pytest'
        self.open(code=1)
        self.assertFalse(any(call[1:3] in (['pane', 'run'], ['pane', 'split'])
                             for call in self.state['calls']))

    def test_legacy_missing_pane_does_not_fall_back_to_app(self):
        self.legacy()
        self.env.pop('HERDR_PANE_ID')
        self.open(code=1)
        self.assertEqual(self.state['calls'], [])

    def test_legacy_failed_preflight_does_not_create_worktree(self):
        self.legacy()
        self.state['fail'] = 'legacy'
        target = self.root / 'openerp_som_addons-worktrees/new'
        self.run_wrapper('create', str(target), 'FIX_test', code=1)
        self.assertFalse(target.exists())
        self.assertTrue(all(call[0] == 'legacy'
                            for call in self.state['calls']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
