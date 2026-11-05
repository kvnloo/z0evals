"""Synthetic process-lifecycle contract checks; no model or Oracle qualification."""
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


# Importing the transport must not require a remote model/toolchain.
spec = importlib.util.spec_from_file_location(
    'oracle_transport_under_test', os.environ.get('ORACLE_TRANSPORT_UNDER_TEST',
        str(Path(__file__).with_name('oracle_sandbox_exec.py'))))
transport = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {'sandbox': types.SimpleNamespace(PRELUDE=''),
                              'common': types.SimpleNamespace(TARGETS={})}):
    spec.loader.exec_module(transport)


class LifecycleTests(unittest.TestCase):
    def run_case(self, effects):
        with tempfile.TemporaryFile(mode='w+') as stream:
            with patch.object(transport.subprocess, 'run', side_effect=effects) as run:
                result = transport.run_confined(['sandbox-command'], stream, 'wsp-editor-test.service')
                return result, run.call_args_list

    @staticmethod
    def state(load='not-found', active='inactive', rc=0):
        return subprocess.CompletedProcess([], rc,
            f'LoadState={load}\nActiveState={active}\n', '')

    def test_success_requires_independent_state_check(self):
        result, calls = self.run_case([subprocess.CompletedProcess([], 0),
                                       subprocess.CompletedProcess([], 0), self.state()])
        self.assertEqual(result, (0, {'LoadState': 'not-found', 'ActiveState': 'inactive'}))
        self.assertEqual(calls[1].args[0],
            ['sudo', '-n', 'systemctl', 'stop', 'wsp-editor-test.service'])
        self.assertIn('show', calls[2].args[0])

    def test_failed_editor_can_complete_but_keeps_failure_status(self):
        result, _ = self.run_case([subprocess.CompletedProcess([], 23),
                                   subprocess.CompletedProcess([], 0), self.state('loaded', 'failed')])
        self.assertEqual(result[0], 23)

    def test_timeout_stops_exact_unit_before_query(self):
        result, calls = self.run_case([
            subprocess.TimeoutExpired('sandbox-command', 620),
            subprocess.CompletedProcess([], 0), self.state()])
        self.assertEqual(result[0], 124)
        self.assertEqual(calls[1].args[0],
            ['sudo', '-n', 'systemctl', 'stop', 'wsp-editor-test.service'])
        self.assertIn('show', calls[2].args[0])
        self.assertLessEqual(calls[1].kwargs['timeout'], 30)

    def test_interruption_cleans_up_and_propagates(self):
        with self.assertRaises(KeyboardInterrupt):
            self.run_case([KeyboardInterrupt(), subprocess.CompletedProcess([], 0), self.state()])

    def test_client_start_error_cleans_up_and_propagates(self):
        with self.assertRaises(OSError):
            self.run_case([OSError('client failed'), subprocess.CompletedProcess([], 0), self.state()])

    def test_active_worker_is_not_completion(self):
        for active in ('active', 'activating', 'deactivating', 'reloading'):
            with self.subTest(active=active), self.assertRaisesRegex(RuntimeError, 'not stopped'):
                self.run_case([subprocess.CompletedProcess([], 0),
                               subprocess.CompletedProcess([], 0), self.state('loaded', active)])

    def test_state_query_failure_is_not_completion(self):
        with self.assertRaisesRegex(RuntimeError, 'state unavailable'):
            self.run_case([subprocess.CompletedProcess([], 0),
                           subprocess.CompletedProcess([], 0), self.state(rc=1)])

    def test_missing_state_is_not_completion(self):
        with self.assertRaisesRegex(RuntimeError, 'not stopped'):
            self.run_case([subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 0),
                           subprocess.CompletedProcess([], 0, '', '')])

    def test_unrecognized_load_state_is_not_completion(self):
        with self.assertRaisesRegex(RuntimeError, 'not stopped'):
            self.run_case([subprocess.CompletedProcess([], 0),
                           subprocess.CompletedProcess([], 0), self.state('error', 'inactive')])

    def test_stop_error_is_not_completion(self):
        with self.assertRaisesRegex(RuntimeError, 'stop failed'):
            self.run_case([subprocess.TimeoutExpired('sandbox-command', 620),
                           subprocess.CompletedProcess([], 1), self.state('loaded', 'active')])

    def test_collected_unit_after_stop_race_is_valid(self):
        result, _ = self.run_case([subprocess.TimeoutExpired('sandbox-command', 620),
                                  subprocess.CompletedProcess([], 5), self.state()])
        self.assertEqual(result[0], 124)

    def test_unrelated_stop_failure_is_not_hidden_by_inactive_state(self):
        with self.assertRaisesRegex(RuntimeError, 'stop failed'):
            self.run_case([subprocess.TimeoutExpired('sandbox-command', 620),
                           subprocess.CompletedProcess([], 1), self.state('loaded', 'inactive')])


class ProcessTests(unittest.TestCase):
    def run_process(self, code, timeout=5, stop_status=0):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sudo = root / 'sudo'
            marker = root / 'stopped'
            sudo.write_text('#!' + sys.executable + '\n'
                'import pathlib, sys\n'
                'if sys.argv[3] == "stop":\n'
                f'    pathlib.Path({str(marker)!r}).write_text(sys.argv[4])\n'
                f'    sys.exit({stop_status})\n'
                'print("LoadState=not-found\\nActiveState=inactive")\n')
            sudo.chmod(0o755)
            with patch.dict(os.environ, {'PATH': str(root) + os.pathsep + os.environ['PATH']}):
                with tempfile.TemporaryFile(mode='w+') as stream:
                    result = transport.run_confined([sys.executable, '-c', code], stream,
                                                     'wsp-editor-process-test.service', timeout=timeout)
                    stream.seek(0)
                    output = stream.read()
            self.assertEqual(marker.read_text(), 'wsp-editor-process-test.service')
            return result, output

    def test_real_child_success_receipt_waits_for_cleanup(self):
        result, output = self.run_process('print("child-completed")')
        self.assertEqual(result[0], 0)
        self.assertEqual(output.strip(), 'child-completed')

    def test_real_child_failure_is_preserved(self):
        result, _ = self.run_process('raise SystemExit(17)')
        self.assertEqual(result[0], 17)

    def test_real_child_timeout_cleans_up(self):
        result, _ = self.run_process('import time; time.sleep(60)', timeout=0.1)
        self.assertEqual(result[0], 124)

    def test_real_cleanup_failure_cannot_return_receipt(self):
        with self.assertRaisesRegex(RuntimeError, 'stop failed'):
            self.run_process('print("child-completed")', stop_status=1)


class TransportTests(unittest.TestCase):
    def test_timeout_cli_stops_worker_before_emitting_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model = root / 'model-79eaaa84125b897f5a0ad6638362b864fec813ad'
            model.mkdir()
            (model / 'model.safetensors').touch()
            (root / 'practice').mkdir()
            (root / 'practice/toolchoice_practice.jsonl').touch()
            output = io.StringIO()
            calls = []

            def run(command, **kwargs):
                calls.append(command)
                if 'systemd-run' in command:
                    raise subprocess.TimeoutExpired(command, 620)
                if 'stop' in command:
                    return subprocess.CompletedProcess(command, 0)
                return LifecycleTests.state()

            def path(value):
                return root if value == '/opt/wsp-isolation' else Path(value)

            with patch.object(transport, 'Path', side_effect=path), \
                 patch.object(transport, 'TARGETS', {'functiongemma-270m': {}}), \
                 patch.object(transport.subprocess, 'run', side_effect=run), \
                 patch.object(sys, 'argv', ['oracle_sandbox_exec.py', 'cli-test']), \
                 patch.object(sys, 'stdin', io.StringIO('print("editor")')), \
                 patch.object(sys, 'stdout', output):
                with self.assertRaises(SystemExit) as exit_status:
                    transport.main()
            self.assertEqual(exit_status.exception.code, 124)
            stops = [c for c in calls if 'stop' in c]
            self.assertEqual(len(stops), 1, 'timeout must stop the worker, not just systemd-run')
            receipt = json.loads(output.getvalue())
            self.assertTrue(receipt['worker_stopped'])
            self.assertEqual(stops[0][-1], receipt['unit'])
            self.assertIn('--unit=' + receipt['unit'], calls[0])
            self.assertIn('KillMode=control-group', calls[0])
            self.assertEqual(calls[-1][3], 'show')


if __name__ == '__main__':
    unittest.main(verbosity=2)
