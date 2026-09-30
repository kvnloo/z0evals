"""Aggregate private run JSONL (z0intelligence benchmarks/claude_code/run_pair.py) into a public summary.

Only aggregates leave the machine: no prompts, transcripts, session ids or paths.
usage: python summarize.py RUN.jsonl [RUN.jsonl ...] > data/summary.json
"""
import json, statistics as st, sys
from pathlib import Path

KEYS = ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens', 'output_tokens')


def med(xs):
    return round(st.median(xs), 6) if xs else None


def sign_p(k, n):
    # two-sided exact sign test
    from math import comb
    tail = sum(comb(n, i) for i in range(0, min(k, n - k) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


out = {'schema': 'z0evals.claude-code-savings.summary.v0', 'runs': []}
for f in sys.argv[1:]:
    rows = [json.loads(l) for l in Path(f).read_text().splitlines() if l.strip()]
    cells = {}
    for r in rows:
        cells.setdefault((r['task'], r['arm']), []).append(r)
    run = {'run': Path(f).stem, 'model': rows[0]['model'], 'effort': rows[0]['effort'], 'cells': []}
    for (task, arm), rs in sorted(cells.items()):
        run['cells'].append({'task': task, 'arm': arm, 'n': len(rs), 'verified': sum(r['verified'] for r in rs),
                             'cost_usd_median': med([r['cost_usd'] for r in rs]),
                             'turns_median': med([r['num_turns'] for r in rs]),
                             **{k + '_median': med([r['usage'][k] for r in rs]) for k in KEYS}})
    arms = sorted({r['arm'] for r in rows})
    if len(arms) == 2:
        a = 'off' if 'off' in arms else arms[0]  # stock Claude Code is always the baseline
        b = next(x for x in arms if x != a)
        pairs = {}
        for r in rows:
            pairs.setdefault((r['task'], r['rep']), {})[r['arm']] = r['cost_usd']
        rel = [p[b] / p[a] - 1 for p in pairs.values() if a in p and b in p]
        k = sum(x < 0 for x in rel)
        run['paired'] = {'baseline': a, 'treatment': b, 'n_pairs': len(rel), 'median_rel_cost': med(rel),
                         'min_rel_cost': round(min(rel), 6), 'max_rel_cost': round(max(rel), 6),
                         'treatment_cheaper': k, 'sign_test_p': round(sign_p(k, len(rel)), 6)}
    out['runs'].append(run)
print(json.dumps(out, indent=1))
