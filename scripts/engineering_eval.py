"""Evaluate engineering efficiency over an existing Tokenomics paired cost study.

No model calls, routing, training, protected truth, or new event store. Canonical
Tokenomics owns usage, missingness, matching, and negative-dominates outcomes.
This consumer adds full-workflow timing, setup/search overhead, and an actionable
comparison. Its descriptive findings never grant promotion or causal credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from tokenomics.cost_displacement import build_cost_displacement_report

SCHEMA = 'z0eval.engineering_efficiency.v1'
TIME_SCOPE = 'request_through_verification'
STATES = {'complete', 'partial', 'unsupported', 'failed', 'unknown'}


def _observation(raw: dict | None) -> dict:
    """Read one supplementary whole-arm clock observation, never infer zero."""
    if raw is None:
        return {'value': None, 'observed_value': None, 'measurement_state': 'unknown'}
    if not isinstance(raw, dict) or raw.get('measurement_state') not in STATES:
        raise ValueError('overhead needs an explicit measurement_state')
    value = raw.get('value')
    if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))
                              or not math.isfinite(value) or value < 0):
        raise ValueError('clock observations must be finite nonnegative numbers')
    state = raw['measurement_state']
    if state == 'complete' and value is None:
        raise ValueError('complete clock observation needs an explicit value')
    if raw.get('attribution') != 'trace_total' or not isinstance(raw.get('evidence_ref'), str) or not raw['evidence_ref'].strip():
        raise ValueError('clock observation needs trace_total attribution and evidence_ref')
    return {'value': value if state == 'complete' else None,
            'observed_value': value, 'measurement_state': state}


def _quantiles(values: list[float], expected: int, full_scope: bool) -> dict:
    complete = full_scope and len(values) == expected
    ordered = sorted(values)
    return {'method': 'nearest_rank', 'n_observed': len(values), 'n_expected': expected,
            **{f'p{p}': ordered[math.ceil(len(ordered) * p / 100) - 1] if complete else None
               for p in (50, 95, 99)}}


def analyze(study: dict) -> dict:
    canonical = build_cost_displacement_report(study)
    engineering = study.get('engineering', {})
    if not isinstance(engineering, dict) or not isinstance(engineering.get('arms', {}), dict):
        raise ValueError('engineering metadata and arms must be objects')
    full_scope = engineering.get('wall_time_scope') == TIME_SCOPE
    arms = {}
    for name, source in canonical['arms'].items():
        clocks = engineering.get('arms', {}).get(name, {})
        if not isinstance(clocks, dict):
            raise ValueError('engineering arm clocks must be an object')
        setup = _observation(clocks.get('setup_wall_ms'))
        optimization = _observation(clocks.get('optimization_wall_ms'))
        elapsed = _observation(clocks.get('cohort_elapsed_ms'))
        trace_work = source['costs']['wall_time_ms']
        components = [trace_work['total'], setup['value'], optimization['value']]
        work = sum(components) if full_scope and all(v is not None for v in components) else None
        verified = source['n_verified']
        complete_runs = source['n_observed'] == source['n_expected']
        wall_values = [r['costs']['wall_time_ms']['value'] for r in canonical['runs']
                       if r['arm_id'] == name and r['costs']['wall_time_ms']['value'] is not None]
        elapsed_scope = clocks.get('cohort_time_scope') == 'setup_through_last_verification'
        elapsed_minimum = max(wall_values, default=0) + sum(v for v in (setup['value'], optimization['value']) if v is not None)
        valid_elapsed = elapsed_scope and elapsed['value'] is not None and elapsed['value'] >= elapsed_minimum
        arms[name] = {
            'expected_work_items': source['n_expected'], 'observed_work_items': source['n_observed'],
            'verified_results': verified, 'verification_rate': source['verification_rate'],
            'not_verified_work_items': source['n_expected'] - verified,
            'trace_work_ms': trace_work, 'setup_wall_ms': setup, 'optimization_wall_ms': optimization,
            'total_work_ms': work, 'work_ms_per_verified_result': work / verified if work is not None and verified else None,
            'workflow_latency_ms': _quantiles(wall_values, source['n_expected'], full_scope),
            'cohort_elapsed_ms': elapsed,
            'cohort_clock_consistent': valid_elapsed,
            'observed_verified_results_per_hour': verified * 3_600_000 / elapsed['value']
                if full_scope and complete_runs and valid_elapsed and elapsed['value'] and work is not None else None,
            'costs': {k: v for k, v in source['costs'].items() if k != 'wall_time_ms'},
        }
    baseline, treatment = study['baseline_arm'], study['treatment_arm']
    a, b = arms[baseline], arms[treatment]
    quality_delta = b['verification_rate'] - a['verification_rate']
    a_time, b_time = a['work_ms_per_verified_result'], b['work_ms_per_verified_result']
    reduction = 1 - b_time / a_time if a_time and b_time is not None else None
    reused = any(r['reused_or_ineligible_evidence'] for r in canonical['runs'])
    if quality_delta < 0:
        finding = 'quality_regression'
    elif a_time is None or b_time is None or reused or canonical['evidence_origin'] in {'unknown', 'replay'}:
        finding = 'insufficient_measurement'
    elif canonical['evidence_origin'] == 'synthetic':
        finding = 'synthetic_control_only'
    elif quality_delta > 0:
        finding = 'quality_latency_tradeoff'
    elif reduction is not None and reduction > 0:
        finding = 'lower_observed_work_time'
    else:
        finding = 'no_observed_speedup'
    study_bytes = json.dumps(study, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return {
        'schema': SCHEMA, 'study_id': canonical['study_id'],
        'study_sha256': hashlib.sha256(study_bytes).hexdigest(),
        'evidence_origin': canonical['evidence_origin'], 'evidence_level': canonical['evidence_level'],
        'causal_claim': False, 'promotion_decision': 'not_computed',
        'unit_of_analysis': canonical['unit_of_analysis'], 'wall_time_scope': engineering.get('wall_time_scope', 'unknown'),
        'arms': arms,
        'comparison': {'baseline': baseline, 'treatment': treatment,
                       'verification_rate_delta': quality_delta,
                       'work_time_reduction_fraction': reduction, 'finding': finding,
                       'canonical_cost_findings': {f: sum(p['finding'] == f for p in canonical['pairs'])
                                                  for f in sorted({p['finding'] for p in canonical['pairs']})}},
        'limitations': [
            'Observed clocks and verifier identities are supplied by the producer, not authenticated by this reducer.',
            'All failed attempts and recovery belong in their work-item trace; do not split retries into independent items.',
            'Trace work is additive resource demand, not parallel cohort makespan; throughput uses a separately measured whole-arm clock.',
            'Setup/search/training time is charged in full for this cohort; no assumed future amortization.',
            'Small-cohort quantiles and observed results/hour are not sustained-throughput or population-tail estimates.',
            'No monetary, energy, human-attention, safety non-inferiority, or protected-holdout claim follows from a time comparison.',
            'Raw traces and private evidence references are deliberately omitted; retain canonical source artifacts privately.',
        ],
    }


def _reject_constant(value: str):
    raise ValueError('nonfinite JSON constant: ' + value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('study', type=Path, help='existing tokenomics.paired_cost_study.v1 JSON')
    parser.add_argument('--out', type=Path, help='create-only aggregate JSON; stdout if omitted')
    args = parser.parse_args(argv)
    try:
        study = json.loads(args.study.read_text(encoding='utf-8'), parse_constant=_reject_constant)
        text = json.dumps(analyze(study), indent=2, allow_nan=False) + '\n'
        if args.out:
            with args.out.open('x', encoding='utf-8') as stream:
                stream.write(text)
        else:
            print(text, end='')
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, f'engineering evaluation refused: {type(exc).__name__}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
