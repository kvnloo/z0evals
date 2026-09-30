"""Source-reported contrasts must not silently become causal credit."""
import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('causal', ROOT / 'scripts/analyze_causal_ablation.py')
causal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(causal)


def cohort():
    return {'runId': 'synthetic-test-only', 'states': [
        {'id': 'work-a', 'arms': {
            'compiler+model': {'runs': [{'correct': True, 'decisionMs': 2, 'tokensIn': 3, 'tokensOut': 1, 'costUsd': None}]},
            'unfiltered+model': {'runs': [{'correct': False, 'decisionMs': 1, 'tokensIn': 2, 'tokensOut': 1, 'costUsd': None}]},
        }},
        {'id': 'work-b', 'arms': {
            'compiler+model': {'runs': [{'correct': False, 'decisionMs': 4, 'tokensIn': 3, 'tokensOut': 2, 'costUsd': None}]},
            'unfiltered+model': {'runs': [{'correct': True, 'decisionMs': 3, 'tokensIn': 2, 'tokensOut': 2, 'costUsd': None}]},
        }},
    ]}


class CausalAblationTests(unittest.TestCase):
    def test_source_success_does_not_assign_causal_credit(self):
        report = causal.analyze(cohort())
        self.assertEqual(report['attribution_evidence_level'], 'observational')
        self.assertEqual(report['attribution_status'], 'unresolved')
        self.assertIsNone(report['independent_outcome']['verifier_identity'])
        self.assertIsNone(report['label_generator_identity'])
        self.assertFalse(report['supports_causal_credit'])

    def test_contrasts_use_the_same_sorted_groups(self):
        report = causal.analyze(cohort())
        row = report['contrasts'][0]
        self.assertEqual(row['group_ids'], ['work-a', 'work-b'])
        self.assertEqual(row['source_correctness_delta'], 0)
        self.assertEqual(row['unit_of_analysis'], 'state_id')

    def test_input_reordering_does_not_change_report(self):
        original = cohort()
        changed = copy.deepcopy(original)
        changed['states'].reverse()
        self.assertEqual(causal.analyze(original), causal.analyze(changed))

    def test_missing_comparison_group_fails_instead_of_cherry_picking(self):
        changed = cohort()
        del changed['states'][1]['arms']['unfiltered+model']
        with self.assertRaisesRegex(ValueError, 'same groups'):
            causal.analyze(changed)

    def test_duplicate_groups_are_rejected(self):
        changed = cohort()
        changed['states'].append(copy.deepcopy(changed['states'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            causal.analyze(changed)

    def test_repetitions_do_not_become_independent_groups(self):
        changed = cohort()
        changed['states'][0]['arms']['compiler+model']['runs'] *= 5
        row = causal.analyze(changed)['contrasts'][0]
        self.assertEqual(row['group_count'], 2)
        self.assertEqual(row['with_compiler']['source_correctness_macro'], 0.5)
        self.assertEqual(row['with_compiler']['attempts'], 6)

    def test_unknown_cost_stays_unknown_with_measurement_coverage(self):
        row = causal.analyze(cohort())['contrasts'][0]['with_compiler']
        self.assertIsNone(row['cost']['cost_usd']['total'])
        self.assertEqual(row['cost']['cost_usd']['known'], 0)
        self.assertEqual(row['cost']['cost_usd']['expected'], 2)
        self.assertEqual(row['cost']['tokens_in']['total'], 6)
        self.assertIsNone(row['independently_verified_success_rate'])

    def test_partial_cost_does_not_report_a_complete_total(self):
        changed = cohort()
        changed['states'][0]['arms']['compiler+model']['runs'][0]['costUsd'] = 0.5
        row = causal.analyze(changed)['contrasts'][0]['with_compiler']['cost']['cost_usd']
        self.assertIsNone(row['total'])
        self.assertEqual(row['known'], 1)

    def test_empty_attempts_cannot_claim_coverage(self):
        changed = cohort()
        changed['states'][0]['arms']['compiler+model']['runs'] = []
        with self.assertRaisesRegex(ValueError, 'empty'):
            causal.analyze(changed)

    def test_negative_and_nonfinite_measurements_rejected(self):
        for value in [-1, float('nan'), float('inf'), True]:
            with self.subTest(value=value):
                changed = cohort()
                changed['states'][0]['arms']['compiler+model']['runs'][0]['decisionMs'] = value
                with self.assertRaisesRegex(ValueError, 'measurement'):
                    causal.analyze(changed)

    def test_quality_is_a_boolean_source_label_not_truthy_text(self):
        changed = cohort()
        changed['states'][0]['arms']['compiler+model']['runs'][0]['correct'] = 'false'
        with self.assertRaisesRegex(ValueError, 'correct'):
            causal.analyze(changed)


if __name__ == '__main__':
    unittest.main()
