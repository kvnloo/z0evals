"""Re-derive the headline contrasts of claude-code-savings-v1 from the public per-trial table.

data/trials.csv and data/results.json are imported unchanged from kvnloo/z0intelligence
study/claude-code-savings-v1 @ 0948bc1 (benchmarks/claude_code_v1/results/). The pre-registered
analysis (Wilcoxon, Holm, task-cluster bootstrap) lives in that repo's analyze.py; this script only
recomputes ratio-of-totals, paired-cheaper counts and success from the CSV (stdlib only) and checks
them against results.json.

    python studies/claude-code-savings-v1/summarize.py > studies/claude-code-savings-v1/data/summary.json
"""
import csv
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTRASTS = {'C1': ('stock', 'lean+packet+obspack'), 'C2': ('stock', 'lean'), 'C3': ('lean', 'lean+packet'),
             'C4': ('lean+packet', 'lean+packet+obspack'), 'S1': ('stock', 'lean+packet')}
STRATA = {
    'pooled': lambda r: True,
    'qa': lambda r: r['suite'] == 'qa',
    'repo': lambda r: r['suite'] == 'repo',
    'repo_cold': lambda r: r['suite'] == 'repo' and r['rep'] == '0',
    'repo_warm': lambda r: r['suite'] == 'repo' and r['rep'] != '0',
    'long_horizon': lambda r: r['family'] == 'long_horizon_recall',
}


def main():
    rows = list(csv.DictReader((HERE / 'data' / 'trials.csv').open()))
    ref = json.loads((HERE / 'data' / 'results.json').read_text())
    idx = {(r['suite'], r['task'], r['rep'], r['arm']): r for r in rows}
    out = {'schema': 'z0evals.claude-code-savings.summary.v1', 'n_trials': len(rows), 'contrasts': {}, 'checks': []}
    for sname, pred in STRATA.items():
        out['contrasts'][sname] = {}
        for cid, (a, b) in CONTRASTS.items():
            ps = [(r, idx[(r['suite'], r['task'], r['rep'], b)]) for r in rows
                  if r['arm'] == a and pred(r) and (r['suite'], r['task'], r['rep'], b) in idx]
            ta = sum(int(x['billed_total']) for x, _ in ps)
            tb = sum(int(y['billed_total']) for _, y in ps)
            ca = sum(float(x['cost_usd']) for x, _ in ps)
            cb = sum(float(y['cost_usd']) for _, y in ps)
            pct = [int(y['billed_total']) / int(x['billed_total']) - 1 for x, y in ps]
            c = {'A': a, 'B': b, 'n_pairs': len(ps), 'tokens_change': round(tb / ta - 1, 4),
                 'tokens_median_paired_change': round(statistics.median(pct), 4),
                 'pairs_B_cheaper': sum(p < 0 for p in pct), 'cost_change': round(cb / ca - 1, 4),
                 'success_A': sum(x['verified'] == '1' for x, _ in ps), 'success_B': sum(y['verified'] == '1' for _, y in ps)}
            r = ref['contrasts'][sname][cid]
            for k in ('ci95_cluster_boot', 'wilcoxon_p_logratio', 'wilcoxon_p_holm', 'quality_guard'):
                src = 'tokens_change_ci95_cluster_boot' if k == 'ci95_cluster_boot' else k
                if src in r:
                    c[k] = r[src]
            ok = c['n_pairs'] == r['n_pairs'] and abs(c['tokens_change'] - r['tokens_change_ratio_of_totals']) < 1e-3
            out['checks'].append({'stratum': sname, 'contrast': cid, 'matches_results_json': ok})
            out['contrasts'][sname][cid] = c
    out['arms'] = ref['arms']
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
