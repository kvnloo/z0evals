#!/usr/bin/env python3
"""Audit existing Phase 1B contrasts; never infer causal credit from success.

This is a frozen-evidence analysis, not an experiment runner. State IDs are the
only grouping recorded in the publication corpus; real work-item lineage,
training folds and independent outcome identities remain explicitly unknown.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MATRIX = ROOT / 'studies/slm-router-v0/data/phase1b-matrix.json'


def _measurement(runs, key):
    values = [row.get(key) for row in runs]
    known = [value for value in values if value is not None]
    if any(type(value) not in (int, float) or not math.isfinite(value) or value < 0 for value in known):
        raise ValueError(f'invalid measurement: {key}')
    return {
        'total': sum(known) if len(known) == len(values) else None,
        'known': len(known),
        'expected': len(values),
    }


def _arm(groups):
    rows = [row for runs in groups.values() for row in runs]
    group_rates = []
    for runs in groups.values():
        if not runs:
            raise ValueError('empty group attempts')
        if any(type(row.get('correct')) is not bool for row in runs):
            raise ValueError('correct must be a boolean source label')
        group_rates.append(mean(row['correct'] for row in runs))
    return {
        'attempts': len(rows),
        'groups': len(groups),
        'source_correctness_macro': mean(group_rates),
        'independently_verified_success_rate': None,
        'cost': {
            name: _measurement(rows, key)
            for name, key in [
                ('decision_ms', 'decisionMs'), ('tokens_in', 'tokensIn'),
                ('tokens_out', 'tokensOut'), ('cost_usd', 'costUsd'),
            ]
        },
    }


def analyze(matrix):
    states = matrix['states']
    if not states:
        raise ValueError('empty cohort')
    ids = [state['id'] for state in states]
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate state group')
    arms = sorted({arm for state in states for arm in state['arms']})
    models = sorted(arm.removeprefix('compiler+') for arm in arms
                    if arm.startswith('compiler+') and 'unfiltered+' + arm.removeprefix('compiler+') in arms)
    if not models:
        raise ValueError('no compiler/unfiltered comparison arms')
    contrasts = []
    for model in models:
        names = ['compiler+' + model, 'unfiltered+' + model]
        groups = [{state['id']: state['arms'][name]['runs'] for state in sorted(states, key=lambda row: row['id'])
                   if name in state['arms']} for name in names]
        if set(groups[0]) != set(ids) or set(groups[1]) != set(ids):
            raise ValueError('comparison arms must cover the same groups as the frozen cohort')
        with_compiler, without_compiler = [_arm(group) for group in groups]
        contrasts.append({
            'model': model,
            'arms': names,
            'intervention_axis': 'compiler-first versus unfiltered source-reported routing',
            'unit_of_analysis': 'state_id',
            'group_ids': sorted(ids),
            'group_count': len(ids),
            'group_coverage': 1.0,
            'with_compiler': with_compiler,
            'without_compiler': without_compiler,
            'source_correctness_delta': with_compiler['source_correctness_macro'] - without_compiler['source_correctness_macro'],
        })
    return {
        'schema_version': 'z0eval.causal_ablation_audit.v1',
        'run_id': matrix['runId'],
        'attribution_evidence_level': 'observational',
        'attribution_status': 'unresolved',
        'supports_causal_credit': False,
        'label_generator_identity': None,
        'independent_outcome': {'verifier_identity': None, 'available': False},
        'split': {'group_key': 'state_id', 'work_item_lineage': None, 'training_evaluation_fold': None},
        'contrasts': contrasts,
        'limitations': [
            'Source correct flags are labels, not independently verified task outcomes.',
            'Compiler/unfiltered arms are descriptive contrasts; random assignment and matched attempt counterfactuals are not established.',
            'Repeated state attempts stay within their state group and receive no extra group weight.',
            'Work-item retry/continuation lineage, train/eval folds and contamination controls are not recorded in this corpus.',
            'Label generator and independent verifier identities are unavailable; no sealed-judge independence claim.',
            'Source runtime revisions/configuration pins remain incomplete in the original study manifest.',
            'Missing cost measurements remain null; no zero-cost or verified savings inference.',
            'No evidence retrieval, state, policy, tool, or verifier component receives causal credit from these results.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix', type=Path, default=DEFAULT_MATRIX)
    args = parser.parse_args()
    raw = args.matrix.read_bytes()
    report = analyze(json.loads(raw))
    report['input_sha256'] = hashlib.sha256(raw).hexdigest()
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
