"""Consumer-visible efficiency decisions; all fixtures are explicitly synthetic."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('engineering_eval', ROOT / 'scripts/engineering_eval.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def observation(value, state='complete'):
    return {'value': value, 'measurement_state': state, 'attribution': 'trace_total',
            'evidence_ref': 'synthetic:owned-clock'}


def study():
    result = {'schema': 'tokenomics.paired_cost_study.v1', 'study_id': 'owned-test',
              'evidence_origin': 'synthetic', 'baseline_arm': 'baseline', 'treatment_arm': 'candidate',
              'work_items': [{'work_item_id': 'one', 'task_snapshot_id': 'frozen-one'},
                             {'work_item_id': 'two', 'task_snapshot_id': 'frozen-two'}],
              'runs': [], 'engineering': {'wall_time_scope': 'request_through_verification', 'arms': {}}}
    for arm, wall in [('baseline', 100), ('candidate', 50)]:
        result['engineering']['arms'][arm] = {
            'setup_wall_ms': observation(0), 'optimization_wall_ms': observation(0),
            'cohort_time_scope': 'setup_through_last_verification',
            'cohort_elapsed_ms': observation(wall * 2)}
        for i, item in enumerate(result['work_items']):
            prefix = arm + str(i)
            number = 1 + i + (2 if arm == 'candidate' else 0)
            result['runs'].append({**item, 'arm_id': arm, 'revision': 'a' * 40,
                'token_measurement_state': 'complete', 'frontier_event_ids': [],
                'events': [{'schema': 'tokenomics.event.v0', 'trace_id': f'{number:032x}',
                            'span_id': f'{number:016x}', 'event_id': prefix, 'ts': 1,
                            'kind': 'verification', 'name': 'owned-verifier',
                            'outcome': {'verified_success': True, 'verification_source': 'owned-oracle'}}],
                'cost_observations': {'wall_time_ms': observation(wall)}})
    return result


class EngineeringEfficiencyTests(unittest.TestCase):
    def test_success_adjusted_time_and_observed_batch_throughput(self):
        r = module.analyze(study())
        self.assertEqual(r['arms']['candidate']['work_ms_per_verified_result'], 50)
        self.assertEqual(r['comparison']['work_time_reduction_fraction'], 0.5)
        self.assertEqual(r['arms']['candidate']['observed_verified_results_per_hour'], 72000)
        self.assertEqual(r['arms']['candidate']['workflow_latency_ms']['p50'], 50)
        self.assertEqual(r['comparison']['finding'], 'synthetic_control_only')

    def test_failure_work_stays_in_denominator_and_blocks_speed_claim(self):
        s = study()
        s['runs'][-1]['events'][0]['outcome'] = {'verified_success': False,
                                               'verification_source': 'owned-oracle'}
        r = module.analyze(s)
        self.assertEqual(r['arms']['candidate']['verified_results'], 1)
        self.assertEqual(r['arms']['candidate']['work_ms_per_verified_result'], 100)
        self.assertEqual(r['comparison']['finding'], 'quality_regression')

    def test_execution_completion_cannot_supply_verified_result(self):
        s = study()
        for row in s['runs']:
            row['events'][0]['outcome'] = {'execution_completed': True}
        r = module.analyze(s)
        self.assertIsNone(r['arms']['candidate']['work_ms_per_verified_result'])
        self.assertIsNone(r['comparison']['work_time_reduction_fraction'])
        self.assertEqual(r['comparison']['finding'], 'insufficient_measurement')

    def test_missing_setup_is_not_zero_or_a_speedup(self):
        s = study()
        del s['engineering']['arms']['candidate']['setup_wall_ms']
        r = module.analyze(s)
        self.assertIsNone(r['arms']['candidate']['work_ms_per_verified_result'])
        self.assertEqual(r['arms']['candidate']['trace_work_ms']['total'], 100)
        self.assertEqual(r['comparison']['finding'], 'insufficient_measurement')

    def test_search_cost_can_reverse_apparent_inference_speedup(self):
        s = study()
        s['engineering']['arms']['candidate']['optimization_wall_ms'] = observation(200)
        r = module.analyze(s)
        self.assertEqual(r['arms']['candidate']['work_ms_per_verified_result'], 150)
        self.assertEqual(r['comparison']['work_time_reduction_fraction'], -0.5)
        self.assertIsNone(r['arms']['candidate']['observed_verified_results_per_hour'])

    def test_cohort_clock_must_explicitly_include_setup_and_optimization(self):
        s = study()
        del s['engineering']['arms']['candidate']['cohort_time_scope']
        r = module.analyze(s)
        self.assertIsNone(r['arms']['candidate']['observed_verified_results_per_hour'])

    def test_partial_time_suppresses_headline_and_quantiles(self):
        s = study()
        s['runs'][-1]['cost_observations']['wall_time_ms'] = observation(50, 'partial')
        r = module.analyze(s)
        self.assertEqual(r['arms']['candidate']['trace_work_ms']['observed_total'], 100)
        self.assertIsNone(r['arms']['candidate']['work_ms_per_verified_result'])
        self.assertIsNone(r['arms']['candidate']['workflow_latency_ms']['p95'])

    def test_inference_only_timing_cannot_be_time_to_verified_result(self):
        s = study()
        s['engineering']['wall_time_scope'] = 'inference_only'
        r = module.analyze(s)
        self.assertIsNone(r['arms']['candidate']['work_ms_per_verified_result'])
        self.assertEqual(r['comparison']['finding'], 'insufficient_measurement')

    def test_missing_run_remains_in_expected_cohort(self):
        s = study()
        s['runs'].pop()
        r = module.analyze(s)
        self.assertEqual(r['arms']['candidate']['expected_work_items'], 2)
        self.assertEqual(r['arms']['candidate']['observed_work_items'], 1)
        self.assertIsNone(r['arms']['candidate']['work_ms_per_verified_result'])
        self.assertIsNone(r['arms']['candidate']['observed_verified_results_per_hour'])

    def test_invalid_overhead_is_refused(self):
        for bad in [-1, True, float('nan'), float('inf')]:
            with self.subTest(bad=bad):
                s = study()
                s['engineering']['arms']['candidate']['optimization_wall_ms'] = observation(bad)
                with self.assertRaises(ValueError):
                    module.analyze(s)

    def test_public_summary_excludes_raw_trace_and_private_observation_refs(self):
        import json
        s = study()
        s['runs'][0]['events'][0]['trace_id'] = '0123456789abcdef' * 2
        s['runs'][0]['cost_observations']['wall_time_ms']['evidence_ref'] = '/private/native/path'
        text = json.dumps(module.analyze(s))
        self.assertNotIn('0123456789abcdef' * 2, text)
        self.assertNotIn('/private/native/path', text)

    def test_observed_pair_reports_latency_not_causal_or_adoption_credit(self):
        s = study()
        s['evidence_origin'] = 'observed'
        r = module.analyze(s)
        self.assertEqual(r['comparison']['finding'], 'lower_observed_work_time')
        self.assertIs(r['causal_claim'], False)
        self.assertEqual(r['promotion_decision'], 'not_computed')

    def test_zero_baseline_has_no_infinite_speedup(self):
        s = study()
        s['evidence_origin'] = 'observed'
        for row in s['runs']:
            if row['arm_id'] == 'baseline':
                row['cost_observations']['wall_time_ms'] = observation(0)
        r = module.analyze(s)
        self.assertIsNone(r['comparison']['work_time_reduction_fraction'])
        self.assertEqual(r['comparison']['finding'], 'no_observed_speedup')


if __name__ == '__main__':
    unittest.main()
