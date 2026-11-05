"""Allowlisted aggregate import of the ZHA feasibility probe. Standard library only.

No book text, private traces, machine paths or environment dumps are imported.
Run after both experiments exit, using --ops INPUT --study OUTPUT.
"""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import statistics as stats


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wilson(k, n):
    z = 1.959963984540054
    p = k / n
    mid = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [mid - half, mid + half]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ops', type=Path, required=True)
    ap.add_argument('--study', type=Path, required=True)
    a = ap.parse_args()
    out = a.study / 'data'
    out.mkdir(parents=True, exist_ok=True)
    provenance = []
    all_scaling = []
    # No recursive glob: import only the two named model runs.
    for model, docs, layers, positions in [('qwen3-0.6b', 6, 28, 29), ('qwen3.5-4b', 3, 8, 21)]:
        src = a.ops / 'raw' / f'scaling-{model}.jsonl'
        if not src.exists():
            continue
        groups = collections.defaultdict(lambda: [[], [], []])
        seen = set()
        rows = 0
        for line in src.open():
            r = json.loads(line)
            identity = (r['doc'], r['n'], r['layer'], r['router'])
            assert identity not in seen, f'duplicate {identity}'
            seen.add(identity)
            assert r['model'] == model
            n = r['n']
            assert len(r['attended']) == len(r['recall']) == len(r['scored']) == 16
            assert all(0 < x <= n for x in r['attended'])
            assert all(-1e-6 <= x <= 1.000001 for x in r['recall'])
            key = (model, r['doc'], n, r['router'])
            g = groups[key]
            g[0].extend(x / n for x in r['attended'])
            g[1].extend(r['recall'])
            g[2].extend(x / n for x in r['scored'])
            rows += 1
        expected = docs * layers * positions * 17
        assert rows == expected, (model, rows, expected, 'partial run is not a completed study')
        provenance.append({'file': src.name, 'sha256': digest(src), 'rows': rows})
        for (model, doc, n, router), (att, recall, ideal) in sorted(groups.items()):
            all_scaling.append({'model': model, 'segment': doc, 'n': n, 'router': router,
                'head_layer_samples': len(att), 'attended_frac': stats.mean(att),
                'attention_mass': stats.mean(recall),
                'attention_mass_p10': sorted(recall)[int(.1 * len(recall))],
                'idealized_selected_node_plus_key_ratio': stats.mean(ideal)})
    assert any(r['model'] == 'qwen3-0.6b' for r in all_scaling)
    (out / 'scaling-segments.json').write_text(json.dumps(all_scaling, indent=1) + '\n')

    src = a.ops / 'raw' / 'niah-qwen3-0.6b.jsonl'
    trials = []
    seen = set()
    for line in src.open():
        r = json.loads(line)
        key = (r['length'], r['i'], r['router'])
        assert key not in seen
        seen.add(key)
        # Output is only a short answer on a public synthetic task. No prompts.
        trials.append({k: r[k] for k in ['model', 'length', 'i', 'depth', 'router', 'correct',
                                       'output', 'attended_frac', 'scored_frac', 'prompt_tokens']})
    assert len(trials) == 720
    assert {r['length'] for r in trials} == {4096, 8192, 16384}
    assert all(0 <= r['i'] < 30 for r in trials)
    provenance.append({'file': src.name, 'sha256': digest(src), 'rows': len(trials)})
    (out / 'niah-trials.json').write_text(json.dumps(trials, indent=1) + '\n')

    summary = {'scope': 'training-free feasibility; NOT a reproduction of trained ZHA',
               'niah': [], 'scaling': [], 'oracle_support_exponent': []}
    dense = {(r['length'], r['i']): r['correct'] for r in trials if r['router'] == 'dense'}
    groups = collections.defaultdict(list)
    for r in trials:
        groups[(r['length'], r['router'])].append(r)
        groups[('pooled', r['router'])].append(r)
    for (length, router), rs in sorted(groups.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
        k, n = sum(r['correct'] for r in rs), len(rs)
        assert n == (90 if length == 'pooled' else 30)
        summary['niah'].append({'length': length, 'router': router, 'correct': k, 'n': n,
            'accuracy': k / n, 'wilson95': wilson(k, n),
            'dense_correct_router_wrong': sum(dense[(r['length'], r['i'])] and not r['correct'] for r in rs),
            'dense_wrong_router_correct': sum(not dense[(r['length'], r['i'])] and r['correct'] for r in rs),
            'attended_frac': stats.mean(r['attended_frac'] for r in rs),
            'idealized_selected_node_plus_key_ratio': stats.mean(r['scored_frac'] for r in rs)})
    groups = collections.defaultdict(list)
    for r in all_scaling:
        groups[(r['model'], r['n'], r['router'])].append(r)
    for (model, n, router), rs in sorted(groups.items()):
        summary['scaling'].append({'model': model, 'n': n, 'router': router, 'segments': len(rs),
            'attended_frac': stats.mean(r['attended_frac'] for r in rs),
            'attention_mass': stats.mean(r['attention_mass'] for r in rs),
            'idealized_selected_node_plus_key_ratio': stats.mean(r['idealized_selected_node_plus_key_ratio'] for r in rs)})
    for model in sorted({r['model'] for r in all_scaling}):
        for router in ['oracle-p0.5', 'oracle-p0.8', 'oracle-p0.9', 'oracle-p0.95']:
            # Descriptive OLS log-log fit of MEAN support, not an asymptotic proof.
            rs = [r for r in summary['scaling'] if r['model'] == model and r['router'] == router and r['n'] >= 1024]
            x = [math.log(r['n']) for r in rs]
            y = [math.log(r['n'] * r['attended_frac']) for r in rs]
            slope, intercept = stats.linear_regression(x, y)
            summary['oracle_support_exponent'].append({'model': model, 'router': router,
                'range': [min(r['n'] for r in rs), max(r['n'] for r in rs)], 'exponent': slope,
                'interpretation': 'descriptive finite-range fit; no asymptotic or generalization claim'})
    (out / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n')
    (out / 'provenance.json').write_text(json.dumps({'raw_inputs': provenance,
        'model_revisions': {'Qwen/Qwen3-0.6B': 'c1899de289a04d12100db370d81485cdf75e47ca',
                            'Qwen/Qwen3.5-4B': '851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a'},
        'base_revisions': {'kvnloo/z0intelligence': '52aed5bb9a41b4986fb77c3017c03d3b2a4573e0',
                           'kvnloo/z0evals': 'f8e7f4321a3fe5d97485bfd7d69695a4da7e09f4'},
        'software': {'torch': '2.11.0+cu128', 'transformers': '5.20.1', 'accelerate': '1.15.0'},
        'books': [{'id': i, 'url': f'https://www.gutenberg.org/cache/epub/{i}/pg{i}.txt',
                   'sha256': digest(a.ops / 'texts' / f'pg{i}.txt')} for i in [1342,2701,98]],
        'seed': 20261103, 'decode': 'greedy, thinking disabled, 16 new tokens max',
        'niah': 'four seven-digit needles per task; one queried; substring exact answer',
        'scaling': 'three books, two segments/book for 0.6B; one/book for 4B; all full-attention heads and layers',
        'caveats': ['heads/layers/overlapping positions are NOT independent trials',
                    'shared dense prefill produces first output token before sparse decode',
                    'centroid routing only; no ZHA reference-query distillation',
                    'scored/scored_frac fields are idealized operation counts, NOT measured work',
                    '4B is a hybrid model: only eight full-attention layers are probed']}, indent=1) + '\n')
    print(json.dumps({'imported_raw_rows': sum(r['rows'] for r in provenance), 'segments':len(all_scaling), 'trials':len(trials)}))


if __name__ == '__main__':
    main()
