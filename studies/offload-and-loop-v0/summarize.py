"""Aggregate the pinned sources for offload-and-loop-v0 into a public summary.

Only aggregates leave the machine: no prompts, task text, model outputs, judge rows, transcript excerpts,
test strings, session ids or per-item rows. Every pinned input is read with `git show <sha>:<path>` from a
clone that contains the pinned (pushed) commits; nothing is checked out.

usage: python summarize.py --z0int REPO --evolab REPO > data/summary.json

  --z0int   a kvnloo/z0intelligence clone containing 2c0c339, 9b8289c, b6abbd2 and 5bc290f
  --evolab  a kvnloo/evolution-lab clone containing 1b80a4e

Five parts:
  1. speed-first offload v0: the task-class registry's equivalence records before (535b8af) and after
     (2c0c339) the demotion; the pre-registered per-class rule is re-applied to the recorded numbers.
  2. summarize faithfulness v0: source-reported arm aggregates and paired bounds; the verdict is
     re-derived from the bounds and the pre-registered margins.
  3. verification density v0: source-reported counts from docs/verification-density.md at the squashed
     commit b6abbd2 (identical to the result commit bd370e6). The counts are hard-coded here and each one
     is checked to appear in the pinned document. Nothing else is read from that branch.
  4. verified loop v0: the evolution-lab result file (metrics and counts only); the sufficiency verdict
     and the weeks-to-gate projection are re-derived from its counts.
  5. utilization v0: the instrument is pinned (5bc290f) but the headline is an operator run on the local
     host; the counts are reported as source-reported and unpinned.
"""
import argparse, json, subprocess

Z0, EL = 'kvnloo/z0intelligence', 'kvnloo/evolution-lab'
PINS = {
    'registry_before': ('z0int', '535b8af088d7a5927115d5f839a3fdaf0ed13390', 'manifests/task_classes.v0.json'),
    'registry_after': ('z0int', '2c0c339ab21003b7984c5427ed2b84e52f4871d5', 'manifests/task_classes.v0.json'),
    'speed_sets': ('z0int', 'd716a38632530e90d95d878d02f1525c61f876f2', 'benchmarks/speed_offload/sets_manifest.json'),
    'faith_results': ('z0int', '9b8289c2b8532a5990f846a213acf801368d32c2', 'benchmarks/summarize_faithfulness/results.v0.json'),
    'density_doc': ('z0int', 'b6abbd202f2ca5c1061d266ae41009df3bdc58bf', 'docs/verification-density.md'),
    'density_prereg': ('z0int', 'b6abbd202f2ca5c1061d266ae41009df3bdc58bf', 'docs/prereg/verification-density-v0.md'),
    'loop_result': ('evolab', '1b80a4e44972a9069248fb58a82ca2926143cde6', 'results/verified-loop-v0.json'),
}


def show(repo, sha, path):
    return subprocess.run(['git', '-C', repo, 'show', f'{sha}:{path}'], check=True,
                          capture_output=True, text=True).stdout


def r4(x):
    return round(x, 4) if isinstance(x, float) else x


# ----------------------------------------------------------------------------- 1. speed-first offload
def rule_status(e):
    """PREREG.md (d716a38) decision rule, re-applied to the recorded aggregates."""
    n, loc = e['n'], e['local']
    rate = loc['pass'] / n
    err = loc['errors'] / n
    lb = e['diff_lower_bound_95']
    lat_cmp = e['frontier'][e['latency_comparator']]['p95_api_ms']
    if lb > -0.10 and rate >= 0.80 and loc['p95_ms'] < lat_cmp and err <= 0.05:
        return 'speed_qualified'
    if lb > -0.15 and rate >= 0.70 and err <= 0.05:
        return 'cost_eligible'
    return 'not_equivalent'


def speed_offload(before, after, sets):
    classes = {}
    for name, c in after['classes'].items():
        e, b = c['equivalence'], before['classes'][name]['equivalence']
        row = {
            'n': e['n'], 'max_context_chars': e['max_context_chars'],
            'local_pass': e['local']['pass'], 'local_errors': e['local']['errors'],
            'local_p50_ms': e['local']['p50_ms'], 'local_p95_ms': e['local']['p95_ms'],
            'frontier': {arm: {k: v[k] for k in ('pass', 'errors', 'p50_api_ms', 'p95_api_ms', 'p95_wall_ms')}
                         for arm, v in e['frontier'].items()},
            'quality_comparator': e['quality_comparator'], 'latency_comparator': e['latency_comparator'],
            'diff_lower_bound_95': e['diff_lower_bound_95'], 'margin': e['margin'], 'speedup_p95': e['speedup_p95'],
            'status_535b8af': b['status'], 'status_2c0c339': e['status'],
            'rule_reapplied_to_recorded_numbers': rule_status(b),
        }
        row['rule_matches_535b8af'] = row['rule_reapplied_to_recorded_numbers'] == b['status']
        if 'demoted_by' in e:
            row['demoted_by'] = e['demoted_by']
        if 'faithfulness' in c:
            row['faithfulness_record'] = {k: c['faithfulness'][k] for k in
                                          ('verdict', 'prereg_commit', 'results_commit', 'hallucination_rate',
                                           'critical_fact_recall')}
        classes[name] = row
    return {
        'local_route': after['local_route'],
        'evidence_file_sha256': after['evidence']['sha256'],
        'set_counts': {k: v['n'] for k, v in sets['classes'].items()},
        'rule': {'source': 'benchmarks/speed_offload/PREREG.md @ d716a38',
                 'speed_qualified': 'lower bound of paired d (local - higher-pass frontier) > -0.10, local pass >= 0.80, '
                                    'local warm p95 < p95 duration_api_ms of the faster frontier arm, local errors <= 5%',
                 'cost_eligible': 'lower bound > -0.15, local pass >= 0.70, errors <= 5%',
                 'bootstrap': '10,000 paired resamples, one-sided 95%'},
        'classes': classes,
        'speed_qualified_after_results': sorted(k for k, v in classes.items() if v['status_535b8af'] == 'speed_qualified'),
        'speed_qualified_after_demotion': sorted(k for k, v in classes.items() if v['status_2c0c339'] == 'speed_qualified'),
        'all_rule_checks_match': all(v['rule_matches_535b8af'] for v in classes.values()),
    }


# ----------------------------------------------------------------------------- 2. summarize faithfulness
def faithfulness(res):
    keep = ('rows', 'errors', 'format_pass', 'critical_recall_mean', 'critical_facts_micro', 'judged',
            'hallucinated_items', 'hallucination_rate', 'contradicted_items', 'unsupported_claims',
            'judge_recall_mean', 'words_p50', 'p50_ms', 'p95_ms', 'latency_basis', 'by_kind')
    arms = {a: {k: v[k] for k in keep} for a, v in res['arms'].items()}
    rule = res['rule']
    comps = {}
    for name, c in res['comparisons'].items():
        h, r = c['hallucination'], c['recall']
        rec = {'hallucination': h, 'recall': r, 'judge_recall_sensitivity': c['judge_recall_sensitivity'],
               'halluc_noninferior_source': c['halluc_noninferior'], 'recall_noninferior_source': c['recall_noninferior'],
               'qualifies_source': c['qualifies']}
        rec['halluc_noninferior_rederived'] = h['hi95_one_sided'] < rule['halluc_margin']
        rec['recall_noninferior_rederived'] = r['lo95_one_sided'] > -rule['recall_margin']
        rec['matches_source'] = (rec['halluc_noninferior_rederived'] == c['halluc_noninferior'] and
                                 rec['recall_noninferior_rederived'] == c['recall_noninferior'])
        comps[name] = rec
    rate_checks = all(abs(v['hallucinated_items'] / v['judged'] - v['hallucination_rate']) < 1e-4 for v in res['arms'].values())
    return {
        'n_items': res['n_items'], 'items_sha256': res['items_sha256'], 'rule': rule, 'verdict': res['verdict'],
        'arms': arms, 'comparisons': comps, 'robustness': res['robustness'], 'deviations_count': len(res['deviations']),
        'checks': {'hallucination_rates_equal_items_over_judged': rate_checks,
                   'noninferiority_rederived_matches_source': all(c['matches_source'] for c in comps.values())},
        'note': 'v0 speed-offload check for this class was format-and-facts (<= 40 words, digit file count, one file '
                'named) on a git-stat-only set; this evaluation is a new 160-item set over pytest/git/build/gh output',
    }


# ----------------------------------------------------------------------------- 3. verification density
DENSITY = {
    'live_turns_window': 31,
    't1_target': 0.20,
    't1_prereg_baseline_no_gh': {'resolved': 2, 'share': 0.065},
    't1': {
        'v0_as_shipped_gh_on': {'resolved': 4, 'share': 0.129, 'not_success': 1},
        'preregistered_t1': {'resolved': 4, 'share': 0.129, 'not_success': 1},
        'exploratory_v0_2_pipe_and_install_aware': {'resolved': 5, 'share': 0.161, 'not_success': 4},
        'hypothetical_density_at_design_confidence_not_claimed': {'resolved': 9, 'share': 0.290, 'not_success': 4},
    },
    't2_bar': 'precision >= 0.90 with n_labelled >= 50 and unsure <= 20%; otherwise demoted to low confidence',
    't2_precision': {
        'checked_later': {'firings': 33, 'holds': 12, 'wrong': 20, 'unsure': 1, 'precision': 0.38, 'wilson_lb95': 0.23},
        'ended_on_error': {'firings': 6, 'holds': 1, 'wrong': 4, 'unsure': 1, 'precision': 0.20, 'wilson_lb95': 0.04},
        'tests_suite_new_tests': {'firings': 4, 'holds': 4, 'wrong': 0, 'unsure': 0, 'precision': 1.00, 'wilson_lb95': 0.51},
        'edit_reverted': {'firings': 0}, 'answer_ungrounded': {'firings': 0},
    },
    'checked_later_wrong_from_piped_test_runs': 15,
    'piped_test_defect_7d_all_cohorts': {'tests_in_turn_plus1_v0': 114, 'tests_in_turn_plus1_fixed': 87,
                                         'tests_in_turn_minus1_v0': 3, 'tests_in_turn_minus1_fixed': 13,
                                         'unknown_v0': 5, 'unknown_fixed': 22},
    'live_turn_types': {'orchestration': 12, 'ops': 9, 'qa': 7, 'edit_untested': 2, 'research': 1},
    't3_resolved_per_week': {'preregistered': 28, 'exploratory_v0_2': 35},
    't4_gh_runtime_s': {'cold': 36, 'warm': 20, 'before_serial': 118, 'targets': {'cold': 60, 'warm': 30}},
}
# Strings that must appear in the pinned document for the hard-coded counts above to stand.
DENSITY_ANCHORS = ['| 4 / 31 | 0.129 | 1 |', '| 5 / 31 | 0.161 | 4 |', '| 9 / 31 | 0.290 | 4 |',
                   '| checked_later (+) | 33 | 12 | 20 | 1 | 0.38 | 0.23 |', '| ended_on_error (-) | 6 | 1 | 4 | 1 | 0.20 | 0.04 |',
                   '| tests_suite_new_tests (+) | 4 | 4 | 0 | 0 | 1.00 | 0.51 |', 'went from 114 to 87',
                   'from 3 to 13', 'unknown from 5 to 22', '15 of its 20 wrong labels were piped test runs',
                   '| orchestration (spawns agents / SendMessage / wakeups) | 12 |', '| ops (mutating shell, no edits) | 9 |',
                   '| qa (no tools) | 7 |', '| edit_untested | 2 |', '| research (read-only tools) | 1 |',
                   'unchanged at **28 resolved/wk**', 'about **35 resolved/wk**', '| cold cache | 36 s |', '| warm cache | 20 s |',
                   '**Target T1 >= 0.20: not met.**']


def density(doc, prereg):
    d = dict(DENSITY)
    p = d['piped_test_defect_7d_all_cohorts']
    d['piped_test_defect_share_of_v0_success'] = r4(1 - p['tests_in_turn_plus1_fixed'] / p['tests_in_turn_plus1_v0'])
    missing = [a for a in DENSITY_ANCHORS if a not in doc]
    d['checks'] = {'anchors_found_in_pinned_doc': len(DENSITY_ANCHORS) - len(missing), 'anchors_total': len(DENSITY_ANCHORS),
                   'missing': missing, 'prereg_baseline_0.065_in_prereg': '0.065' in prereg,
                   'prereg_target_0.20_in_prereg': '>= 0.20' in prereg}
    return d


# ----------------------------------------------------------------------------- 4. verified loop
def loop(res):
    obs = res['primary']['sufficiency']['observed']
    rederived = {'rows>=300': obs['rows'] >= 300, 'not_success>=30': obs['not_success'] >= 30,
                 'groups>=10': obs['groups'] >= 10}
    pops = {}
    for name, p in res['projection']['populations'].items():
        sc = {}
        for s, v in p['scenarios'].items():
            # evolution-lab method: remaining rows / rows-per-week, remaining not-success / not-success-per-week
            w_rows = max(0, 300 - obs['rows']) / v['resolved_per_week']
            w_ns = max(0, 30 - obs['not_success']) / v['not_success_per_week']
            w_pow = max(0, v['rows_for_80pct_power_halving'] - obs['rows']) / v['resolved_per_week']
            sc[s] = {k: r4(v[k]) for k in ('feature_coverage', 'resolved_per_week', 'not_success_per_week',
                                           'sessions_per_week', 'binding_constraint', 'weeks_to_sufficiency_gate',
                                           'rows_for_80pct_power_halving', 'weeks_to_power')}
            sc[s]['rederived_weeks_to_gate'] = r4(max(w_rows, w_ns))
            sc[s]['rederived_weeks_to_power'] = r4(w_pow)
            sc[s]['matches_source'] = (abs(max(w_rows, w_ns) - v['weeks_to_sufficiency_gate']) < 0.01 and
                                       abs(w_pow - v['weeks_to_power']) < 0.01)
        pops[name] = {'turns_per_week': p['turns_per_week'], 'resolved_per_week': p['resolved_per_week'],
                      'resolved_fraction': r4(p['resolved_fraction']), 'not_success_observed': p['not_success_observed'],
                      'planning_not_success_rate': r4(p['planning_not_success_rate']),
                      'planning_rate_source': p['planning_rate_source'],
                      'feature_coverage_since_emission_began': p['feature_coverage_since_emission_began'],
                      'scenarios': sc}
    sens = res['sensitivity_unverified_as_not_success']
    return {
        'table_version': res['table_version'], 'decision': res['primary']['decision'],
        'descriptive_only': res['primary']['descriptive_only'], 'cv': res['primary']['cv'],
        'input': res['input'], 'sufficiency': res['primary']['sufficiency'],
        'sufficiency_rederived': rederived,
        'sufficiency_matches_source': all(rederived[k] == res['primary']['sufficiency']['checks'][k] for k in rederived),
        'gate_descriptive': res['primary']['pooled'],
        'sensitivity_unverified_as_not_success': {'rows': sens['rows'], 'auroc_oof': r4(sens['pooled']['auroc_oof']),
                                                  'decision_if_primary': sens['decision_if_primary']},
        'projection': {'sweep_days': res['projection']['sweep_days'], 'sessions': res['projection']['sessions'],
                       'sessions_by_cohort': res['projection']['sessions_by_cohort'], 'caveat': res['projection']['caveat'],
                       'populations': pops},
        'source_counts': {k: v['rows'] for k, v in res['sources'].items()},
    }


# ----------------------------------------------------------------------------- 5. utilization
UTILIZATION = {
    'instrument': {'repo': Z0, 'commit': '5bc290f143de0767f43ba329dd9e07bd47f6dca8', 'cli': 'z0int utilization --range 24h --json',
                   'definition': 'docs/utilization.md (z0_utilization_v0): U / N over frontier-bound interactive+agent units, all harnesses'},
    'evidence_class': 'source-reported operator run on the local host; not in a pinned commit; raw JSON not published',
    'runs': {
        'baseline_2026-09-30T22': {'utilized': 51, 'units': 194, 'rate': 0.263, 'displaced': 0, 'shortened_obspack': 51,
                                   'improved': 0, 'coverage': 0.634, 'influence': 0.505, 'utilization_within_seen': 0.415,
                                   'eval_units_excluded': 512, 'measurement_state': 'partial'},
        'tick_2026-09-30T23': {'utilized': 56, 'units': 201, 'rate': 0.279},
    },
    'offloads_interactive_agent': {'route_worker_calls': 0, 'completed': 0, 'verified': 0,
                                   'posture': 'BURN in all 9 snapshots of the baseline window (about 0 offloads expected)'},
    'shadow_decisions_interactive': {'n': 21, 'gate_act': 21, 'gate_agrees_with_observed': 19, 'enforced': 0},
}


ap = argparse.ArgumentParser()
ap.add_argument('--z0int', required=True)
ap.add_argument('--evolab', required=True)
a = ap.parse_args()
repos = {'z0int': a.z0int, 'evolab': a.evolab}
raw = {k: show(repos[r], sha, p) for k, (r, sha, p) in PINS.items()}
src = {k: (v if PINS[k][2].endswith('.md') else json.loads(v)) for k, v in raw.items()}

u = UTILIZATION
for r in u['runs'].values():
    r['rate_rederived'] = r4(r['utilized'] / r['units'])

out = {
    'schema': 'z0evals.offload-and-loop.summary.v0',
    'pins': {k: {'repo': {'z0int': Z0, 'evolab': EL}[r], 'commit': sha, 'path': p} for k, (r, sha, p) in PINS.items()},
    'speed_offload_v0': speed_offload(src['registry_before'], src['registry_after'], src['speed_sets']),
    'summarize_faithfulness_v0': faithfulness(src['faith_results']),
    'verification_density_v0': density(src['density_doc'], src['density_prereg']),
    'verified_loop_v0': loop(src['loop_result']),
    'utilization_v0': u,
}
print(json.dumps(out, indent=1))
