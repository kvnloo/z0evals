"""Aggregate the pinned sources for factory-intelligence-v0 into a public summary.

Only aggregates leave the machine: no prompts, request text, episode text, titles, branches, paths,
per-item rows, per-event rows or private-repo SHAs. Every input is read with `git show <sha>:<path>`
from a clone that contains the pinned (pushed) commits; nothing is checked out.

usage: python summarize.py --z0int REPO --evolab REPO > data/summary.json

  --z0int   a kvnloo/z0intelligence clone containing 1f9473f and 11506a9
  --evolab  a kvnloo/evolution-lab clone containing ebb2e71

Three parts:
  1. tool-calling SLM portfolio (z0intelligence#20): source-reported aggregates, plus a reproduction of
     each arm's pooled exact count and the exact McNemar test vs qwen3_8b from the committed per-item
     pass flags (rows_v0.jsonl; no text in that file).
  2. T3b recovery action space v1 (evolution-lab): source-reported test metrics and bootstrap CIs.
  3. promotion replay simulator v0: source-reported holdout table, plus a re-scoring of the pinned
     dataset.json with the pinned policy definitions (re-implemented here) to check the holdout table
     and to compute the exploratory (post-holdout, NOT pre-registered) rules. Repository names are
     reported only for public repos; the private repo is reported as `private_repo_1`.
"""
import argparse, json, math, subprocess
from collections import Counter, defaultdict

PINS = {
    'tc_results': ('z0int', '1f9473ff4c82d0435f526624418afa8c098d6ce8', 'benchmarks/tool_calling_portfolio/results_v0.json'),
    'tc_rows': ('z0int', '1f9473ff4c82d0435f526624418afa8c098d6ce8', 'benchmarks/tool_calling_portfolio/rows_v0.jsonl'),
    't3b_eval': ('evolab', 'ebb2e7188f04bc9e08ee45d648e5228331c9b0c2', 'results/t3b-v1as-eval.json'),
    't3b_labels': ('evolab', 'ebb2e7188f04bc9e08ee45d648e5228331c9b0c2', 'results/t3b-v1as-label-stats.json'),
    't3b_audit': ('evolab', 'ebb2e7188f04bc9e08ee45d648e5228331c9b0c2', 'results/t3b-v1as-audit.json'),
    'ps_prereg': ('z0int', '11506a959ffb3e1f8b7eba9a03666069fd9b2430', 'benchmarks/promotion_sim/prereg.json'),
    'ps_results': ('z0int', '11506a959ffb3e1f8b7eba9a03666069fd9b2430', 'benchmarks/promotion_sim/results_holdout.json'),
    'ps_dataset': ('z0int', '11506a959ffb3e1f8b7eba9a03666069fd9b2430', 'benchmarks/promotion_sim/dataset.json'),
}
PUBLIC_REPOS = {'z0evals', 'evolution-lab', 'z0intelligence', 'kerdoios', 'aodl', 'tokenomics', 'verified-oss-loop', 'z0'}


def show(repo, sha, path):
    return subprocess.run(['git', '-C', repo, 'show', f'{sha}:{path}'], check=True,
                          capture_output=True, text=True).stdout


def r4(x):
    return round(x, 4) if isinstance(x, float) else x


# ----------------------------------------------------------------------------- 1. tool calling
def mcnemar(a_only, b_only):
    n = a_only + b_only
    if n == 0:
        return 1.0
    p = sum(math.comb(n, k) for k in range(0, min(a_only, b_only) + 1)) / 2 ** n * 2
    return float(f'{min(1.0, p):.3g}')


def tool_calling(res, rows_text):
    rows = [json.loads(l) for l in rows_text.splitlines() if l.strip()]
    by = defaultdict(dict)
    for r in rows:
        by[r['arm']][r['id']] = r
    comp = res['comparator']
    arms = {}
    for arm, a in res['arms'].items():
        keep = {k: a[k] for k in ('n', 'exact', 'exact_acc', 'irrelevance_rejection', 'args_valid', 'args_valid_n',
                                  'parse_paths', 'errors', 'finish_length', 'latency_ms') if k in a}
        keep['z0_route'] = a['z0_route']
        keep['bfcl'] = a['bfcl']
        keep['action_selector'] = {k: a['action_selector'][k] for k in ('n', 'exact', 'by_category', 'pred_counts')}
        keep['posthoc_sensitivity_not_preregistered'] = {k: v for k, v in a['posthoc_sensitivity'].items() if k != 'note'}
        keep['serving'] = {k: a['serving'][k] for k in ('cold_start_ms', 'bench_vram_loaded_mib',
                                                         'bench_vram_peak_sampled_mib', 'model') if k in a['serving']}
        if 'vs_comparator' in a:
            keep['vs_comparator'] = a['vs_comparator']
            keep['eligibility'] = a['eligibility']
        # reproduction from per-item pass flags
        mine, ref = by[arm], by[comp]
        ids = sorted(ref)
        rep = {'pooled_exact': sum(mine[i]['exact'] for i in ids)}
        if arm != comp:
            ao = sum(mine[i]['exact'] and not ref[i]['exact'] for i in ids)
            co = sum(ref[i]['exact'] and not mine[i]['exact'] for i in ids)
            rep.update({'arm_only': ao, 'comparator_only': co, 'mcnemar_p': mcnemar(ao, co)})
        rw = [r for r in mine.values() if r['category'] == 'route_worker']
        rep['route_worker_items'] = {'n': len(rw), 'tool_ok': sum(r['tool_ok'] for r in rw),
                                     'no_call': sum(r['n_calls'] == 0 for r in rw)}
        rep['matches_source'] = (rep['pooled_exact'] == a['exact'] and
                                 (arm == comp or (rep['arm_only'] == a['vs_comparator']['pooled']['arm_only'] and
                                                  rep['comparator_only'] == a['vs_comparator']['pooled']['comparator_only'])))
        keep['reproduced_from_rows'] = rep
        arms[arm] = keep
    return {
        'comparator': comp,
        'items': {'pooled': 184, 'z0_route': 48, 'z0_route_route_worker': 43, 'z0_route_delegate_worker': 5,
                  'bfcl_v4_subset': 125, 'action_selector': 11},
        'arms': arms,
        'decision_rule_outcome': {
            'better_than_comparator_rule1': [k for k, v in arms.items() if v.get('eligibility', {}).get('better_pooled')],
            'shadow_eligible': [k for k, v in arms.items() if v.get('eligibility', {}).get('shadow_eligible')],
        },
    }


# ----------------------------------------------------------------------------- 2. T3b
def t3b(ev, labels, audit):
    def block(part):
        p = ev[part]
        models = {}
        for k, m in p['models'].items():
            t = m['test']
            models[k] = {'test': {x: r4(t[x]) for x in ('n', 'cost', 'acc', 'macro_f1', 'balanced_acc', 'n_pred_abort')},
                         'test_pred_dist': t['pred_dist'], 'test_recall': t['recall']}
            if 'test_cost_seeds' in m:
                models[k]['test_cost_seeds'] = m['test_cost_seeds']
            b = p['bootstrap'].get(k, {})
            models[k]['cost_ci95'] = b.get('cost_ci95')
            for c in ('best_constant', 'rule'):
                if f'dcost_vs_{c}_ci95' in b:
                    models[k][f'dcost_vs_{c}_ci95'] = b[f'dcost_vs_{c}_ci95']
        pairs = {k: v for k, v in p['bootstrap'].items() if '__minus__' in k}
        return {'n': p['n'], 'label_dist': p['label_dist'], 'models': models, 'paired_differences': pairs,
                'primary_endpoint': p['primary_endpoint'], 'secondary_mb_vs_mlp': p['secondary_mb_vs_mlp']}
    return {
        'actions': ev['actions'],
        'cost_matrix_true_x_pred': ev['cost_matrix'],
        'n_features': ev['n_features'],
        'labels': {k: labels[k] for k in ('n_episodes', 'primary_labels', 'behavioral', 'by_rule', 'per_split_primary',
                                          'action_x_recovered', 'error_class_x_primary_label', 'source_x_action',
                                          'episodes_in_new_lineages_dropped') if k in labels},
        'structural_blind_audit': audit['structural-blind'],
        'content_owner_audit': 'not done',
        'primary_filtered': block('primary_filtered'),
        'sensitivity_behavioral': block('sensitivity_behavioral'),
    }


# ----------------------------------------------------------------------------- 3. promotion sim
AUTO, HUMAN, BLOCK = 'AUTO', 'HUMAN', 'BLOCK'


def is_bad(e):
    return bool(e.get('reverted')) or bool(e.get('ci_broke')) or bool(e.get('fix_3d'))


def pa_v0(e):
    return BLOCK if e['pa_v0'] == 'ABSTAIN' else HUMAN


def pa_v0_auto(e):
    if e['pa_v0'] == 'ABSTAIN':
        return BLOCK
    clean = (e['pa_v0'] == 'ASK' and e['wired'] == 'observed' and e['tested_static'] == 'observed'
             and e['receipt'] in ('observed', 'n/a') and e['ci_code'] == 'green')
    return AUTO if clean else HUMAN


def auto_on_green(e):
    return AUTO if e['ci_all'] == 'green' else HUMAN


def auto_on_code_green(e):
    return AUTO if e['ci_code'] == 'green' else HUMAN


def decision7(e):
    return auto_on_code_green(e) if (e['tier'] != 'default' and e['agent'] == 'agent') else pa_v0(e)


def pick(e):  # auto[all,<=inf,nonsrc]
    if e.get('docs_only') and e['ci_all'] != 'red':
        return AUTO
    if not e.get('touches_src') and e['ci_all'] != 'red':
        return AUTO
    return AUTO if e['ci_all'] == 'green' else HUMAN


def docs_only_not_red(green):
    return lambda e: AUTO if (e.get('docs_only') and e['ci_' + green] != 'red') else HUMAN


def pa_auto_abstain_human_plus_docs(green):
    def pol(e):
        if e.get('docs_only') and e['ci_' + green] != 'red':
            return AUTO
        r = pa_v0_auto(e)
        return HUMAN if r == BLOCK else r
    return pol


def wilson(k, n, z=1.96):
    if n == 0:
        return [0.0, 1.0]
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def score(evs, pol):
    c = Counter()
    for e in evs:
        r, b = pol(e), is_bad(e)
        c[r] += 1
        c[('bad' if b else 'good', r)] += 1
    n_bad = sum(c[('bad', r)] for r in (AUTO, HUMAN, BLOCK))
    return {'n': len(evs), 'bad': n_bad, 'auto': c[AUTO], 'human': c[HUMAN], 'blocked': c[BLOCK],
            'bad_auto': c[('bad', AUTO)], 'bad_through': c[('bad', AUTO)] + c[('bad', HUMAN)],
            'good_blocked': c[('good', BLOCK)],
            'auto_bad_rate': round(c[('bad', AUTO)] / c[AUTO], 4) if c[AUTO] else None,
            'auto_bad_rate_ci95': wilson(c[('bad', AUTO)], c[AUTO]),
            'auto_share': round(c[AUTO] / len(evs), 4) if evs else 0.0}


def promotion_sim(prereg, res, ds):
    events = sorted(ds['events'], key=lambda e: e['t'])
    scorable = [e for e in events if e.get('observed_days', 0) >= 3]
    k = int(round(len(scorable) * 0.7))
    train, hold = scorable[:k], scorable[k:]
    pols = {'human_all': lambda e: HUMAN, 'pa_v0': pa_v0, 'pa_v0_auto': pa_v0_auto, 'auto_on_green': auto_on_green,
            'auto_on_code_green': auto_on_code_green, 'decision7_draft': decision7, 'auto[all,<=inf,nonsrc]': pick}
    rescored = {name: {'train': score(train, p), 'holdout': score(hold, p)} for name, p in pols.items()}
    check = all(rescored[n]['holdout'][f] == res['table'][n][f] for n in pols for f in ('auto', 'bad_auto', 'bad_through', 'blocked'))
    check = check and all(rescored[n]['train'][f] == prereg['train'][n][f] for n in pols for f in ('auto', 'bad_auto'))
    explo = {}
    for g in ('all', 'code'):
        for name, p in ((f'docs_only_not_red[{g}]', docs_only_not_red(g)),
                        (f'pa_v0_auto_abstain_to_human_plus_docs_only[{g}]', pa_auto_abstain_human_plus_docs(g))):
            explo[name] = {'train': score(train, p), 'holdout': score(hold, p), 'all_scorable': score(scorable, p)}
    explo['auto_on_code_green'] = {'all_scorable': score(scorable, auto_on_code_green)}
    explo['pa_v0_auto'] = {'all_scorable': score(scorable, pa_v0_auto)}
    abst = [e for e in scorable if e['pa_v0'] == 'ABSTAIN']
    repo_counts = Counter(e['repo'] if e['repo'] in PUBLIC_REPOS else 'private_repo_1' for e in events)
    hold_repo = Counter(e['repo'] if e['repo'] in PUBLIC_REPOS else 'private_repo_1' for e in hold)
    green_all = [e for e in hold if e['kind'] == 'pr' and e['ci_all'] == 'green']
    green_all_sc = [e for e in scorable if e['kind'] == 'pr' and e['ci_all'] == 'green']
    return {
        'events': {'n': len(events), 'by_kind': dict(Counter(e['kind'] for e in events)),
                   'by_repo': dict(repo_counts.most_common()), 'scorable_3d_window': len(scorable),
                   'agent_tagged': sum(e['agent'] == 'agent' for e in events),
                   'by_author_kind': dict(Counter(e['agent'] for e in events))},
        'labels_scorable': {'bad_3d': sum(is_bad(e) for e in scorable),
                            'reverted': sum(bool(e.get('reverted')) for e in scorable),
                            'ci_broke': sum(bool(e.get('ci_broke')) for e in scorable),
                            'ci_observed': sum(bool(e.get('ci_observed')) for e in scorable),
                            'fix_3d': sum(bool(e.get('fix_3d')) for e in scorable),
                            'fixfile_3d': sum(bool(e.get('fixfile_3d')) for e in scorable)},
        'split': prereg['split'],
        'holdout_by_repo': dict(hold_repo.most_common()),
        'holdout_green_all_prs': {'n': len(green_all), 'with_no_code_check': sum(e['ci_code'] == 'none' for e in green_all)},
        'holdout_pick_bad_auto_by_repo': dict(Counter(e['repo'] if e['repo'] in PUBLIC_REPOS else 'private_repo_1'
                                                      for e in hold if pick(e) == AUTO and is_bad(e)).most_common()),
        'scorable_green_all_prs': {'n': len(green_all_sc), 'with_no_code_check': sum(e['ci_code'] == 'none' for e in green_all_sc)},
        'preregistration': {k: prereg[k] for k in ('label', 'criterion', 'pick', 'pick_rule', 'holdout_pass',
                                                    'hypotheses', 'decision7_if_pass', 'decision7_if_fail',
                                                    'written_before_holdout', 'events_file_sha')},
        'train_table_source': {k: {f: r4(v[f]) for f in ('n', 'bad', 'auto', 'bad_auto', 'auto_bad_rate', 'auto_share')}
                               for k, v in prereg['train'].items()},
        'holdout_source': {'n': res['n_holdout'], 'base_bad_rate': res['base_bad_rate'], 'pass': res['pass'],
                           'hypotheses': res['hypotheses'], 'pa_v0_abstain': res['pa_v0_abstain'],
                           'table': {k: {f: v[f] for f in ('n', 'bad', 'auto', 'human_reviews', 'blocked', 'bad_auto',
                                                          'bad_through', 'good_blocked', 'auto_bad_rate',
                                                          'auto_bad_rate_ci95', 'auto_share')}
                                     for k, v in res['table'].items()}},
        'h1_bar_holdout': {'auto_bad_rate_max': round(0.5 * res['base_bad_rate'], 4), 'auto_share_min': 0.2,
                           'bad_auto_max': 0.5 * res['table']['human_all']['bad_through']},
        'rescored_from_dataset': {'matches_source_tables': check, 'policies': rescored},
        'pa_v0_abstain_all_scorable': {'n': len(abst), 'bad': sum(is_bad(e) for e in abst)},
        'exploratory_not_preregistered': explo,
    }


ap = argparse.ArgumentParser()
ap.add_argument('--z0int', required=True)
ap.add_argument('--evolab', required=True)
a = ap.parse_args()
repos = {'z0int': a.z0int, 'evolab': a.evolab}
raw = {k: show(repos[r], sha, p) for k, (r, sha, p) in PINS.items()}
src = {k: (v if k == 'tc_rows' else json.loads(v)) for k, v in raw.items()}

out = {
    'schema': 'z0evals.factory-intelligence.summary.v0',
    'pins': {k: {'repo': {'z0int': 'kvnloo/z0intelligence', 'evolab': 'kvnloo/evolution-lab'}[r], 'commit': sha, 'path': p}
             for k, (r, sha, p) in PINS.items()},
    'tool_calling_portfolio': tool_calling(src['tc_results'], src['tc_rows']),
    't3b_action_space_v1': t3b(src['t3b_eval'], src['t3b_labels'], src['t3b_audit']),
    'promotion_sim': promotion_sim(src['ps_prereg'], src['ps_results'], src['ps_dataset']),
}
print(json.dumps(out, indent=1))
