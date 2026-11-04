# tiny-slm-gym-v0: program (the scheduled loop reads this file each tick)

Goal: find out whether tiny SLMs (<1B), run through Southpaw's profile scaffold, can remove measurable frontier work in
z0intelligence decisions. Plan source: council round 1 (`council/`, 2026-11-03), all four seats converged.

## Rules (hard)
- Private Hermes data (state.db, ~/.z0int/episodes) stays on groot. Modal only for public stand-in tasks.
- Only `tiny-evaluator` reads the sealed test window. The trainer never iterates on sealed scores.
- A tiny model is promoted (to shadow) only if it beats max(majority, recency, bigram, ridge, MB) with a CI on the
  sealed window AND an offline counterfactual shows frontier tokens/calls removed. Otherwise ship the simple control.
- groot heavy work: one capped job at a time (`systemd-run --user --scope -p MemoryMax=4G`), skip if MemAvailable < 3 GB
  and count the skip. No pkill -f.
- Every result: command, artifact path, n, CI. Failures and nulls are logged, not dropped.

## Queue (do the first undone item; mark done here with date + artifact)
1. [ ] Loop C export: next_action rows with decision-time-only features, session/lineage grouping, time split with a
   purge gap, gym/council sessions excluded; sealed test hash in `data/splits.json`; data stays under ~/.z0int.
2. [ ] Controls on the export: majority (expect ~0.319), recency/last-family, bigram, ridge (~0.412), MB (~0.397):
   top-1, top-3, Brier, k for 98% coverage. Write `data/controls.json` (counts and rates only).
3. [ ] Displacement audit: 200 sampled decisions; offline count of tool-schema tokens removable by top-k narrowing.
4. [ ] Loop B: frozen-trunk heads, both ends in parallel order: SmolLM2-135M and Qwen3-0.6B, then Gemma-270M and
   Qwen3.5-0.8B. Logistic head on pooled states; risk/coverage, calibration, warm p50 latency (kill > ~70 ms).
5. [ ] Loop A (blog method) on Modal: SmolLM2-135M-Instruct no-answer defect, 25 passes, vs logit-bias, random rank-1
   and LoRA-4 controls; report %valid and accuracy-given-valid separately.
6. [ ] Council round 2 on the first product target (tool-schema narrowing vs observation-relevance vs audit) with
   items 2-3 numbers in the brief.

## Done
- 2026-11-03 Math Darwin lanes (harness validation only), run `20261103-ends`, volume `tiny-gym-results`:
  Qwen3.5-0.8B held-out GSM8K base 0.592 / instruct 0.512 / best merge 0.532; MATH-500 0.320 / 0.170 / 0.320.
  SmolLM2-135M: all ~0. Null: the fitness-selected merge did not beat the better parent.
- 2026-11-03 Council round 1, seat texts in `council/r1-*.md`.
