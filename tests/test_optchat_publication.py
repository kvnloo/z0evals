"""Frozen-data and publication contracts. No model calls; no recall certification."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('optchat_publication', ROOT / 'scripts/validate_optchat_publication.py')
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.summary = json.loads((ROOT / validator.STUDY / 'summary.json').read_text())
        self.turns = json.loads((ROOT / validator.STUDY / 'turns.json').read_text())

    def test_frozen_artifact_integrity(self):
        validator.validate_repository(ROOT)

    def test_truncated_trajectory_is_rejected(self):
        with self.assertRaises(ValueError):
            validator.validate_values(self.summary, self.turns[:-1])

    def test_final_summary_drift_is_rejected(self):
        self.summary['final_view_bytes'] += 1
        with self.assertRaises(ValueError):
            validator.validate_values(self.summary, self.turns)

    def test_reordered_turns_are_rejected(self):
        self.turns[0], self.turns[1] = self.turns[1], self.turns[0]
        with self.assertRaises(ValueError):
            validator.validate_values(self.summary, self.turns)

    def test_zero_denominator_is_rejected(self):
        self.turns[0]['raw_bytes'] = 0
        with self.assertRaises(ValueError):
            validator.validate_values(self.summary, self.turns)

    def test_boolean_is_not_a_byte_count(self):
        self.turns[0]['view_bytes'] = True
        with self.assertRaises(ValueError):
            validator.validate_values(self.summary, self.turns)

    def test_nan_is_rejected(self):
        self.turns[0]['ratio'] = float('nan')
        with self.assertRaises(ValueError):
            validator.validate_values(self.summary, self.turns)

    def test_ratio_drift_is_rejected(self):
        self.turns[0]['ratio'] = 0.99
        with self.assertRaises(ValueError):
            validator.validate_values(self.summary, self.turns)

    def test_nonadvancing_message_count_is_rejected(self):
        self.turns[1]['messages'] = self.turns[0]['messages']
        with self.assertRaises(ValueError):
            validator.validate_values(self.summary, self.turns)

    def test_recorded_message_count_jump_is_preserved(self):
        # The source records 144, not 141, messages at turn 47. Do not normalize
        # this observation away to make it fit a three-messages-per-turn model.
        self.assertEqual(self.turns[46]['messages'], 144)
        validator.validate_values(self.summary, self.turns)

    def test_corrupted_bytes_are_rejected_before_render(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / validator.STUDY
            target.mkdir(parents=True)
            (target / 'turns.json').write_text('[]\n')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                validator.validate_repository(root)

    def test_route_uses_shared_shell_and_frozen_data(self):
        source = (ROOT / 'web/app/optchat-long-horizon-v0/page.tsx').read_text()
        self.assertIn('return <StoryShell', source)
        self.assertIn('@/data/optchat-long-horizon-v0.json', source)
        builder = (ROOT / 'scripts/build_site_data.py').read_text()
        self.assertIn('OPTCHAT_SOURCE', builder)
        self.assertIn('OPTCHAT_SITE_OUT', builder)
        self.assertIn('optchat-long-horizon-v0', builder)
        self.assertIn('status: "unscored"', source)
        self.assertIn('source-reported', source)
        self.assertIn('uncommitted', source)
        self.assertIn('not a measurement of the tokens', source)
        self.assertIn('Victor Taelin', source)
        self.assertNotIn('"use client"', source)  # keep canonical file data on the server

    def test_home_and_shared_navigation_reach_article(self):
        root = (ROOT / 'web/app/page.tsx').read_text()
        shared = (ROOT / 'web/components/StoryShell.tsx').read_text()
        self.assertIn('href="./optchat-long-horizon-v0/"', root)
        self.assertIn('href="../optchat-long-horizon-v0/"', shared)

    def test_export_requires_optchat_page(self):
        audit = (ROOT / 'scripts/audit_web_export.py').read_text()
        self.assertIn('"optchat": root / "optchat-long-horizon-v0" / "index.html"', audit)
        self.assertIn('("routing", "research", "memory", "optchat")', audit)

    def test_live_smoke_checks_article_title(self):
        workflow = (ROOT / '.github/workflows/pages.yml').read_text()
        self.assertIn('check "optchat-long-horizon-v0/" "does optchat stay small after fifty tool calls?"', workflow)


if __name__ == '__main__':
    unittest.main()
