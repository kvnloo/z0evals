"""Aggregate the pinned z0intelligence sources for local-offload-and-authority-v0 into a public summary.

Only aggregates leave the machine: no prompts, transcripts, commands, item text, hosts or paths.

usage: python summarize.py --groot-bench DIR --z0int REPO > data/summary.json

  DIR   the private groot bench outputs (one JSONL per backend: id, gold_id, pred_id, probabilities, ms)
  REPO  a z0intelligence clone that contains the pinned commits below (read with `git show`, never checked out)
"""
import argparse, json, math, statistics as st, subprocess
from pathlib import Path

BENCH = [  # (file stem, label, host, accelerator)
    ('mbp-radeon-qwen3-0.6b-q8', 'qwen3-0.6b-q8', 'mbp', 'Radeon R9 M370X, Vulkan'),
    ('groot_qwen3_06b_q8', 'qwen3-0.6b-q8', 'groot', 'RTX 3080 Ti, CUDA'),
    ('groot_qwen3_17b_q4', 'qwen3-1.7b-q4km', 'groot', 'RTX 3080 Ti, CUDA'),
    ('groot_qwen3_4b_q4', 'qwen3-4b-q4km', 'groot', 'RTX 3080 Ti, CUDA'),
    ('groot_qwen3_8b_q4', 'qwen3-8b-q4km', 'groot', 'RTX 3080 Ti, CUDA'),
]
PINS = {
    'orchestrator_results': ('eb7c7d323c29cb6d647db57589804be073528a3e', 'benchmarks/orchestrator_router/results_v0.json'),
    'orchestrator_a1_local_order': ('336cb478f818db7c9e2f36702ba9fa9c14b5df70', 'benchmarks/orchestrator_router/results_a1_local_order.json'),
    'effect_v0_heldout': ('f6406c11091915e479cf8f1c3d4e1d0ebdd77f40', 'benchmarks/effect_inference/results_v0_heldout.json'),
    'effect_v0_live': ('f6406c11091915e479cf8f1c3d4e1d0ebdd77f40', 'benchmarks/effect_inference/results_v0_live_cohort.json'),
    'effect_v1_heldout': ('3187f46f1de304c83e987ff9ec8956988619f6cd', 'benchmarks/effect_inference/results_v1_heldout.json'),
    'effect_v1_dev': ('3187f46f1de304c83e987ff9ec8956988619f6cd', 'benchmarks/effect_inference/results_v1_dev.json'),
    'effect_v1_live': ('3187f46f1de304c83e987ff9ec8956988619f6cd', 'benchmarks/effect_inference/results_v1_live_cohort.json'),
    'action_authority': ('a3243fa03be2b26f5538112f39ea098afd046545', 'benchmarks/action_authority/results_v0.json'),
}


def pct(xs, q):
    xs = sorted(xs)
    k = (len(xs) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def bench(d: Path):
    out = []
    for stem, model, host, accel in BENCH:
        rows = [json.loads(l) for l in (d / f'{stem}.jsonl').read_text().splitlines() if l.strip()]
        ms = [r['ms'] for r in rows]
        wrong = [r for r in rows if r['pred_id'] != r['gold_id']]
        out.append({'model': model, 'host': host, 'accelerator': accel, 'n': len(rows),
                    'correct': len(rows) - len(wrong),
                    'confident_errors_ge_0_9': sum(max(r['probabilities'].values()) >= 0.9 for r in wrong),
                    'median_ms': round(st.median(ms), 1), 'p90_ms': round(pct(ms, 0.9), 1),
                    'first_item_ms': round(ms[0], 1)})
    return out


def show(repo, sha, path):
    return json.loads(subprocess.run(['git', '-C', repo, 'show', f'{sha}:{path}'], check=True,
                                     capture_output=True, text=True).stdout)


def counts(d):
    """Keep only integer count tables (and linked/unlinked n); drop free text and source paths."""
    out = {}
    for k, v in d.items():
        if isinstance(v, int) and not isinstance(v, bool):
            out[k] = v
        elif isinstance(v, dict):
            sub = counts(v)
            if sub:
                out[k] = sub
    return out


def scalars(d):
    return {k: v for k, v in d.items() if not isinstance(v, (dict, list))}


ap = argparse.ArgumentParser()
ap.add_argument('--groot-bench', required=True, type=Path)
ap.add_argument('--z0int', required=True)
a = ap.parse_args()
src = {k: show(a.z0int, *v) for k, v in PINS.items()}

orch = src['orchestrator_results']
out = {
    'schema': 'z0evals.local-offload-and-authority.summary.v0',
    'pins': {k: {'commit': v[0], 'path': v[1]} for k, v in PINS.items()},
    'offload_tier': {
        'set': 'evidence_sufficiency (frozen 48 evidence_interpretation test items; 3-way supported/insufficient/contradicted)',
        'reference': {'jev': '46/48 (source-reported)', 'proposed_admission_bar': '>=44/48'},
        'backends': bench(a.groot_bench),
    },
    'orchestrator_router': {
        'sets': orch['sets'],
        'arms_pooled_labeled': {k: {**{m: (round(x, 4) if isinstance(x, float) else x)
                                       for m, x in v['pooled_labeled'].items()}}
                                for k, v in orch['arms'].items() if 'pooled_labeled' in v},
        'strongest_s1_only': {m: (round(x, 4) if isinstance(x, float) else x)
                              for m, x in orch['arms']['strongest']['S1'].items()},
        'latency_ms': {k: {'p50': round(v['latency']['p50_ms']), 'p95': round(v['latency']['p95_ms'])}
                       for k, v in orch['arms'].items() if v.get('latency')},
        'orch_think_proposals': orch['arms']['orch_think']['proposal_distribution'],
        'tests': orch['tests'],
        'vram_mib': orch['vram_mib'],
    },
    'orchestrator_router_a1_local_order': {
        'prereg_commit': '0e9005314061a78e3b54345cff497fb5c3ae550d',
        'frozen_input_check': src['orchestrator_a1_local_order']['frozen_input_check'],
        'policy_local_order': src['orchestrator_a1_local_order']['policy_local_order'],
        's1_deterministic_choice_distribution': src['orchestrator_a1_local_order']['s1_deterministic_choice_distribution'],
        'arms_a1': {a: {s: {m: (round(x, 4) if isinstance(x, float) else x) for m, x in r.items()} for s, r in v.items()}
                    for a, v in src['orchestrator_a1_local_order']['arms_a1'].items()},
        'reading': src['orchestrator_a1_local_order']['reading'],
        'exploratory_orch_think_vs_a1_deterministic': src['orchestrator_a1_local_order']['exploratory_orch_think_vs_a1_deterministic'],
    },
    'effect_inference': {
        'v0_heldout': {k: scalars(v['all']) for k, v in src['effect_v0_heldout']['arms'].items()},
        'v0_live_cohort': counts(src['effect_v0_live']),
        'v1_heldout': {k: scalars(v['all']) for k, v in src['effect_v1_heldout']['arms'].items()},
        'v1_dev': {k: scalars(v['all']) for k, v in src['effect_v1_dev']['arms'].items()},
        'v1_live_cohort': counts(src['effect_v1_live']),
    },
    'action_authority': {k: v for k, v in src['action_authority'].items() if k != 'schema'},
    'resource_posture': {'status': 'pre-registered; no results', 'prereg_commit': '083b99d0c495e104f6e21a01fcc02304d802b541'},
}
print(json.dumps(out, indent=1))
