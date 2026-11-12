# offload-and-loop-v0

Five measurements from the night of 2026-09-30 on two questions: can a local groot model take worker
tasks from the frontier at equal quality and lower latency, and is there enough verified data for z0 to
start learning its own gate? Every source is pinned by a pushed commit; only aggregates are published;
failed and insufficient results are reported as such.

The overall lesson: **format checks overstate local equivalence, and the learning loop is data-bound by
coverage and verification density, not by plumbing.**

## Findings

| part | bar | result | verdict |
| --- | --- | --- | --- |
| Speed-first offload v0 (d716a38 -> 535b8af, demotion 2c0c339) | per class: paired lower bound of local - best frontier > -0.10, local pass >= 0.80, local warm p95 < faster frontier p95, errors <= 5% | summarize_tool_output 60/60 vs Haiku 59/60, p95 893 vs 2054 ms; classify_file_type 48/60 (LB -0.267), evidence_sufficiency 31/48 (-0.479), extract_json 8/60 (-0.933), short_rewrite 2/53 (-0.943) | one class **speed_qualified** on a format-and-facts check, four **not_equivalent**; after the faithfulness result **none** |
| Summarize faithfulness v0, decision 20 (2870516 -> 9b8289c) | vs Haiku, paired one-sided 95%: hallucinated-item upper bound < +2 pp, critical-fact recall lower bound > -5 pp | qwen3-8b hallucinated 42/160 (26.3%) vs Haiku 21/159 (13.2%), upper +18.9 pp; recall 0.816 vs 0.893, lower -10.5 pp; qwen3-14b (exploratory) also fails both | **fail** on both margins; class demoted |
| Verified outcomes #54 (17a88ba) + verification density v0 (4431225 -> bd370e6, squashed b6abbd2) | T1 live verified share >= 0.20; T2 per-verifier precision >= 0.90 with n >= 50; T4 gh cold <= 60 s, warm <= 30 s | T1 4/31 = 0.129; checked_later precision 0.38 (n=33), ended_on_error 0.20 (n=6), tests_suite_new_tests 1.00 (n=4); T4 36 s / 20 s | T1 **not met**; T2 every verifier **demoted** to low; T4 met; v0 piped-test defect: ~24% of v0 test-success signals were not passes |
| Verified loop v0 (z0int 5d0a85c; evolution-lab ded915a -> 1b80a4e) | sufficiency: >= 300 rows, >= 30 not-success, >= 10 groups, 5 folds with both classes | 6 analysis rows (of 23), 1 not-success, 1 group; live 217 turns/wk, 28 resolved/wk | **INSUFFICIENT_DATA**; ~24 weeks to the gate, ~30 weeks to 80% power on live volume |
| Utilization v0 baseline (instrument 5bc290f) | none (baseline) | 51/194 = 26.3%, then 56/201 = 27.9%; all ObservationPack shortening; 0 offloads, 0 enforced decisions | **baseline**, source-reported operator run |

## Reproduction checks in this study

- Speed offload: the pre-registered rule is re-applied to the recorded per-class numbers in the pinned
  registry and gives the same status as 535b8af for all five classes; 2c0c339 changes only
  summarize_tool_output, citing the faithfulness result.
- Faithfulness: hallucination rates equal items/judged for every arm, and both non-inferiority calls are
  re-derived from the source's paired bounds and the pre-registered margins.
- Verification density: the hard-coded counts are checked against 20 anchor strings in
  `docs/verification-density.md` at b6abbd2 (byte-identical to bd370e6). Nothing is read from 4431225 or
  bd370e6, whose test fixtures carried paraphrased private prompts.
- Verified loop: the sufficiency checks and the weeks-to-gate and weeks-to-power figures are re-derived
  from the result's counts and match for both populations and both coverage scenarios.
- Utilization: source-reported only; the instrument is pinned, the run is not.

## Deviations

- Speed offload: none in the scored run. The class's v0 check was format-and-facts only, which the
  write-up already flagged; the demotion followed a separately pre-registered evaluation.
- Faithfulness: the first qwen3-14b attempt failed to load on the shared GPU and was re-run; qwen3-14b was
  judged in a separate blinded pool; one Haiku item stayed unjudged and was dropped (1/160).
- Verification density: the pre-registered baseline (0.065) was measured without gh, T1 with gh (v0 is
  0.129 with gh); the pipe and install fixes came after the labels were seen and are exploratory only; no
  verifier reached 50 firings, so the demotion rule applied to all of them.
- Verified loop: none; the run could not do grouped CV (one group) and is descriptive only, as the
  pre-registration says for that case.

## Threats to validity

Single principal and about one day of live data; small synthetic offload sets; a single LLM judge that
is also an arm; density precision samples far below 50; v0 verified labels contaminated by the
piped-test defect until re-verified; a linear one-day volume extrapolation with one observed live
not-success; utilization counts from an unpinned operator run during BURN posture. See `manifest.yaml`
`limitations`.

Aggregate data: `data/summary.json`. Regenerate with
`python summarize.py --z0int Z0INTELLIGENCE_CLONE --evolab EVOLUTION_LAB_CLONE > data/summary.json`.

Branch note: this study was branched from `origin/main` (fb14919), as the recent studies were, because
z0evals `nightly` lags: it does not yet carry the recent study merges on `dev` (factory-intelligence-v0,
claude-code-savings-v1, local-offload-and-authority-v0).
