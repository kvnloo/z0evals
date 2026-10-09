"""Export fixtures only: none of these tests executes or certifies OMP."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import omp_capture as capture


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        (self.repo / 'helper.py').write_text('pass\n')
        subprocess.run(['git', '-C', str(self.repo), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.repo), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture'], check=True)
        self.commit = capture.git(self.repo, 'rev-parse', 'HEAD')
        self.spec = {'version': 1, 'evidence_kind': 'synthetic_fixture', 'sources': [
            {'repo': 'example/fixture', 'root': str(self.repo), 'commit': self.commit}], 'files': {}}
        for role in capture.ROLES:
            path = self.root / (role + '.txt')
            path.write_text('fixture only\n')
            self.spec['files'][role] = {'path': str(path), 'sha256': capture.sha256(path)}
        self.metadata = {'correctness': 'unknown', 'first_turn': 'unknown', 'owning_tests_passed': None,
                         'latency_ms': None, 'tokens': {'input': None, 'output': None, 'cache_read': None, 'reasoning': None},
                         'provider_api_key': 'sk-private-fixture-secret', 'prompt': 'private personal text'}
        self.set_metadata(self.metadata)
        self.manifest = self.root / 'private.json'
        self.export = self.root / 'public.json'

    def set_metadata(self, data):
        path = Path(self.spec['files']['run_metadata']['path'])
        path.write_text(json.dumps(data))
        self.spec['files']['run_metadata']['sha256'] = capture.sha256(path)

    def test_export_and_replay_are_identical_and_do_not_certify_omp(self):
        capture.capture(self.spec, self.manifest, self.export)
        before = self.export.read_bytes()
        replay = self.root / 'replay.json'
        capture.replay(self.manifest, replay)
        self.assertEqual(before, replay.read_bytes())
        data = json.loads(before)
        self.assertEqual(data['actual_omp_run'], 'not_executed_by_exporter')
        self.assertEqual(data['measurement_status'], 'source_reported_unverified')
        self.assertIsNone(data['metrics']['latency_ms'])

    def test_public_export_omits_all_private_text_and_paths(self):
        capture.capture(self.spec, self.manifest, self.export)
        text = self.export.read_text()
        for secret in ('sk-private-fixture-secret', 'private personal text', str(self.root), 'provider_api_key'):
            self.assertNotIn(secret, text)
        self.assertEqual(self.manifest.stat().st_mode & 0o777, 0o600)

    def test_missing_role_fails_without_outputs(self):
        del self.spec['files']['witness']
        with self.assertRaises(ValueError): capture.capture(self.spec, self.manifest, self.export)
        self.assertFalse(self.manifest.exists())
        self.assertFalse(self.export.exists())

    def test_bad_hash_fails_without_outputs(self):
        self.spec['files']['witness']['sha256'] = '0' * 64
        with self.assertRaises(ValueError): capture.capture(self.spec, self.manifest, self.export)
        self.assertFalse(self.manifest.exists())

    def test_replay_rejects_tampering(self):
        capture.capture(self.spec, self.manifest, self.export)
        Path(self.spec['files']['witness']['path']).write_text('changed')
        with self.assertRaises(ValueError): capture.replay(self.manifest, self.root / 'bad.json')

    def test_rejects_short_or_missing_commit(self):
        for pin in (self.commit[:7], '0' * 40):
            self.spec['sources'][0]['commit'] = pin
            with self.assertRaises(ValueError): capture.capture(self.spec, self.manifest, self.export)

    def test_rejects_symlink_input(self):
        link = self.root / 'link'
        link.symlink_to(self.spec['files']['witness']['path'])
        self.spec['files']['witness']['path'] = str(link)
        with self.assertRaises(ValueError): capture.capture(self.spec, self.manifest, self.export)

    def test_rejects_unlisted_roles(self):
        self.spec['files']['credentials'] = self.spec['files']['witness']
        with self.assertRaises(ValueError): capture.capture(self.spec, self.manifest, self.export)

    def test_no_overwrite_of_source_or_existing_output(self):
        source = Path(self.spec['files']['witness']['path'])
        before = source.read_bytes()
        with self.assertRaises(ValueError): capture.capture(self.spec, source, self.export)
        self.assertEqual(before, source.read_bytes())

    def test_invalid_measurements_cannot_smuggle_secrets(self):
        for field, value in [('latency_ms', 'sk-secret'), ('correctness', 'private'), ('owning_tests_passed', True), ('latency_ms', float('nan')), ('latency_ms', -1)]:
            data = copy.deepcopy(self.metadata)
            data[field] = value
            self.set_metadata(data)
            with self.assertRaises(ValueError): capture.capture(self.spec, self.manifest, self.export)

    def test_unknown_metrics_must_be_explicit(self):
        data = copy.deepcopy(self.metadata)
        del data['tokens']['output']
        self.set_metadata(data)
        with self.assertRaises(ValueError): capture.capture(self.spec, self.manifest, self.export)

    def test_metadata_hash_is_checked_before_parsing(self):
        Path(self.spec['files']['run_metadata']['path']).write_text('{}')
        with self.assertRaises(ValueError): capture.capture(self.spec, self.manifest, self.export)

    def test_checkout_changes_fail_replay(self):
        capture.capture(self.spec, self.manifest, self.export)
        (self.repo / 'helper.py').write_text('changed')
        with self.assertRaises(ValueError): capture.replay(self.manifest, self.root / 'bad.json')

    def test_fresh_run_rejects_dirty_source(self):
        self.spec['evidence_kind'] = 'fresh_run'
        (self.repo / 'helper.py').write_text('changed')
        with self.assertRaises(ValueError): capture.capture(self.spec, self.manifest, self.export)

    def test_archival_capture_labels_dirty_source(self):
        self.spec['evidence_kind'] = 'archival_run'
        (self.repo / 'helper.py').write_text('changed')
        capture.capture(self.spec, self.manifest, self.export)
        data = json.loads(self.export.read_text())
        self.assertTrue(data['sources'][0]['worktree_dirty'])
        self.assertEqual(data['repository_identity'], 'operator_asserted_not_verified')

    def test_symlink_output_is_rejected(self):
        self.export.symlink_to(self.root / 'absent')
        with self.assertRaises(ValueError): capture.capture(self.spec, self.manifest, self.export)
        self.assertFalse(self.manifest.exists())

    def test_cli_malformed_json_is_generic_and_fail_closed(self):
        spec = self.root / 'spec.json'
        spec.write_text('{"secret": "sk-sensitive-do-not-print"')
        run = subprocess.run([sys.executable, capture.__file__, 'capture', '--spec', str(spec),
                              '--manifest', str(self.manifest), '--export', str(self.export)],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertNotIn('sk-sensitive', run.stderr)
        self.assertNotIn(str(self.root), run.stderr)
        self.assertFalse(self.manifest.exists())

    def test_duplicate_json_keys_are_rejected(self):
        spec = self.root / 'duplicate.json'
        spec.write_text('{"version": 1, "version": 2}')
        with self.assertRaises(ValueError): capture.read_json(spec)

    def test_symlink_parent_input_is_rejected(self):
        alias = self.root / 'alias'
        alias.symlink_to(self.repo, target_is_directory=True)
        with self.assertRaises(ValueError): capture.plain_file(str(alias / 'helper.py'))

    def test_same_output_paths_are_rejected(self):
        with self.assertRaises(ValueError): capture.capture(self.spec, self.manifest, self.manifest)
        self.assertFalse(self.manifest.exists())


if __name__ == '__main__': unittest.main()
