"""Synthetic control-flow tests only; canonical private bundle is unavailable."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import omp_local_handoff as local
import omp_capture as capture


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.provider = self.root / 'provider.json'
        self.provider.write_text('SECRET-MUST-NEVER-BE-READ')
        self.provider.chmod(0o600)

    def test_provider_checks_metadata_without_reading(self):
        with patch.object(Path, 'open', side_effect=AssertionError('provider read')):
            local.provider_present(str(self.provider))

    def test_provider_rejects_public_permissions(self):
        self.provider.chmod(0o644)
        with self.assertRaises(ValueError): local.provider_present(str(self.provider))

    def test_provider_rejects_symlink(self):
        link = self.root / 'linked'
        link.symlink_to(self.provider)
        with self.assertRaises(ValueError): local.provider_present(str(link))

    def test_missing_bundle_fails_closed_no_output(self):
        output = self.root / 'public.json'
        self.assertEqual(local.main(['capture', '--release-dir', str(self.root), '--spec', str(self.root / 'absent'), '--provider-config', str(self.provider), '--manifest', str(self.root / 'manifest'), '--export', str(output)]), 2)
        self.assertFalse(output.exists())

    def test_wrong_bundle_rejected_before_spec_read(self):
        (self.root / 'handoff.json').write_text('{}')
        with patch.object(capture, 'read_json', side_effect=AssertionError('should not read')):
            with self.assertRaises(ValueError): local.preflight(self.root, 'absent', self.provider)

    def test_provider_cannot_be_control_spec(self):
        with patch.object(capture, 'sha256', side_effect=AssertionError('must not hash')):
            with self.assertRaises(ValueError): local.preflight(self.root, self.provider, self.provider)

    def test_provider_hardlink_cannot_be_bundle(self):
        os.link(self.provider, self.root / 'handoff.json')
        with patch.object(capture, 'sha256', side_effect=AssertionError('must not hash')):
            with self.assertRaises(ValueError): local.preflight(self.root, self.root / 'spec', self.provider)

    def test_complete_fixture_plumbing_and_negative_gates(self):
        # Deliberately substitute fixture pins only inside this test. This is not
        # a receipt for the unavailable real canonical bundle.
        from test_omp_capture import CaptureTests
        fixture = CaptureTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        spec = fixture.spec
        spec['evidence_kind'] = 'archival_run'
        spec['sources'][0]['repo'] = 'kvnloo/z0intelligence'
        release = self.root / 'release'
        release.mkdir()
        (release / 'handoff.json').write_text('fixture handoff')
        hashes = {}
        for name in local.DEPENDENCIES:
            (release / name).write_text('fixture only ' + name)
            hashes[name] = capture.sha256(release / name)
        for role, name in local.ROLE_FILES.items():
            spec['files'][role] = {'path': str(release / name), 'sha256': hashes[name]}
        spec_path = self.root / 'spec.json'
        def save(): spec_path.write_text(json.dumps(spec))
        save()
        with patch.object(local, 'HANDOFF', capture.sha256(release / 'handoff.json')), patch.object(local, 'DEPENDENCIES', hashes), patch.object(local, 'SOURCE', fixture.commit), patch.object(local, 'REGISTRY', fixture.commit):
            self.assertEqual(local.preflight(release, spec_path, self.provider), spec)
            spec['evidence_kind'] = 'synthetic_fixture'
            save()
            with self.assertRaises(ValueError): local.preflight(release, spec_path, self.provider)
            spec['evidence_kind'] = 'archival_run'
            spec['sources'][0]['repo'] = 'example/wrong-owner'
            save()
            with self.assertRaises(ValueError): local.preflight(release, spec_path, self.provider)
            spec['sources'][0]['repo'] = 'kvnloo/z0intelligence'
            spec['files']['witness']['path'] = str(self.provider)
            save()
            with patch.object(capture, 'validate', side_effect=AssertionError('provider must not reach exporter')):
                with self.assertRaises(ValueError): local.preflight(release, spec_path, self.provider)

    def test_capture_delegates_existing_exporter_only(self):
        spec = {'fixture_control_flow_only': True}
        with patch.object(local, 'preflight', return_value=spec), patch.object(capture, 'capture') as exporter:
            self.assertEqual(local.main(['capture', '--release-dir', 'unused', '--spec', 'unused', '--provider-config', 'unused', '--manifest', 'private', '--export', 'public']), 0)
            exporter.assert_called_once_with(spec, 'private', 'public')

    def test_preflight_never_calls_exporter(self):
        with patch.object(local, 'preflight', return_value={}), patch.object(capture, 'capture') as exporter:
            self.assertEqual(local.main(['preflight', '--release-dir', 'unused', '--spec', 'unused', '--provider-config', 'unused']), 0)
            exporter.assert_not_called()

    def test_no_arbitrary_command_option(self):
        with self.assertRaises(SystemExit):
            local.main(['run', '--command', 'true'])


if __name__ == '__main__': unittest.main()
