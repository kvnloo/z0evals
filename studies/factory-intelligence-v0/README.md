# factory-intelligence-v0

Three pre-registered experiments from 2026-09-30 on how the z0 factory should make small decisions
without the frontier model or a human: which small local model should form z0's own tool calls, what a
learned controller should do after a tool call fails, and which promotions could merge without review.
Every source is pinned by a pushed commit; only aggregates are published; failed bars are reported as failures.

## Findings

| experiment | pre-registered bar | result | verdict |
| --- | --- | --- | --- |
| Tool-calling SLM portfolio, z0intelligence#20 (6d56416 -> 01c6dd9 -> b3a5fb0, note fix 1f9473f) | rule 1: better than qwen3_8b (higher, McNemar p<0.05); rule 2: cheaper substitute (pooled within 5, irrelevance >=0.80, z0 form >=0.90, args >=0.95, less VRAM, p50 <=) | qwen3_8b 152/184; qwen3_14b 150 (p=0.86), nemotron 148 (p=0.39); qwen3.5_4b 137, qwen3.5_9b 121, hammer2.1_7b 86, hammer2.1_3b 81, functiongemma 63 (all p<0.05 worse) | **null**: no candidate better, none eligible; z0 form gate unreachable (gold defect) |
| T3b recovery action space v1 (3cb0e50 -> 4b1015b -> ebb2e71) | primary: MB cost-decoded beats best constant (CI upper < 0); secondary: MB vs MLP upper < 0.05 | MB 0.288 vs constant 0.368, delta [-0.131, -0.030]; MB vs MLP [-0.069, +0.056]; ridge 0.252; a-priori rule 0.433 | **primary pass**, secondary **fail** by 0.006; ask/abort untested (n=1 each) |
| Promotion replay simulator v0 (37b5678 -> fa8de23 -> 11506a9) | H1: pick's holdout auto bad rate <= 0.5 x base, auto share >= 20%, bad auto <= 0.5 x human_all bad through | pick auto[all,<=inf,nonsrc]: 65/91 auto, 11 bad (0.169 vs bar 0.115) | **H1 fail**; H2 true; H3 unscorable; H4 true (pa_v0_auto 0/14) |

## Reproduction checks in this study

- Tool calling: each arm's pooled exact count and its exact McNemar discordant pairs vs qwen3_8b are
  re-derived from the committed per-item pass flags (`rows_v0.jsonl`) and match `results_v0.json`.
- Promotion sim: all seven compared policies are re-implemented and re-scored on the pinned `dataset.json`;
  train and holdout counts match `prereg.json` and `results_holdout.json`. The exploratory rules in the
  post are computed the same way from the same data and are labelled as exploratory.
- T3b: numbers are source-reported from `results/t3b-v1as-eval.json` (the training run needs the private
  episode store).

## Deviations

- Tool calling: two adapter fixes from the smoke run (FunctionGemma turn boundary; Hammer Python-literal
  lists), committed in 01c6dd9 before the scored run. A delegate_worker gold defect was found while
  scoring; the post-hoc sensitivity is labelled and changes no verdict. 1f9473f corrects one count in the
  prose note only.
- T3b: the val-only dry run was stopped part-way under machine load; the harness was committed (4b1015b)
  before the single test read and no code changed after it.
- Promotion sim: none in the scored run. The rule the operator now recommends (pa_v0_auto plus docs-only)
  was chosen after the holdout was seen, and goes further than the pre-registered fail branch ("keep human
  merge for source changes; at most auto-merge docs-only").

## Threats to validity

Single principal throughout; partly author-labelled tool-calling gold with one known defect; single-sample,
thinking-off tool-calling runs on a shared GPU; T3b labels from a structural rule with no content audit yet
and almost no ask/abort data; promotion outcomes that rest on an SZZ fix-within-3-days label (0 reverts,
2 CI breaks) over four weeks dominated by one site sprint. See `manifest.yaml` `limitations`.

Aggregate data: `data/summary.json`. Regenerate with
`python summarize.py --z0int Z0INTELLIGENCE_CLONE --evolab EVOLUTION_LAB_CLONE > data/summary.json`.
