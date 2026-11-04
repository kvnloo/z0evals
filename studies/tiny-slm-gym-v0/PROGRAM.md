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
0. [~] RUNNING (check first every tick): the blog's Exp-8 method on Qwen3.5-0.8B, thinking on, Modal sandbox + L4,
   10 forward passes per editor, run `20261104-exp8`, launched by `scripts/launch-exp8.sh` as user units
   `wsp-20261104-exp8-<editor>` (status: `systemctl --user is-active`, logs and state:
   ~/.z0int/state/weight-space/slm/20261104-exp8/). Editors: opus (claude-opus-5-5), fable (claude-fable-5-1).
   argon: BLOCKED, agy 429 "Individual quota reached", resets ~2026-11-07 22:50 CST; relaunch then with
   `launch-exp8.sh 20261104-exp8 10 argon` (state marked not-done). When a cell's session ends, matrix runs evaluate.py
   (unedited baseline + edited); report MATH-500/GSM8K, %cut-at-limit, and what the edit was, vs the blog's 10-pass row
   (12.3 / 25.7, 87.2% cut). Never report a cell whose editor made 0 edits as an editor result.
0b. [~] ARGON VIA GEMINI APP (owner runs prompts by hand while agy is quota-blocked). Page:
   http://100.113.138.100:8765/ (unit `argon-relay-page`, `scripts/argon_relay_page.py`); prompts in `argon-app/`, replies
   land in `argon-app/replies/<prompt>-<ts>.txt`. Each tick, process new replies: #1/#2/#3 (exp5 MinAtar writes) score
   with the z0int `run.py` exp5 scorer (1,000 episodes) and compare MAX vs DEFAULT effort on #1/#2; #4 (council seat)
   summarize vs the four seats; #5 (Qwen relay) run its python blocks in the Modal sandbox and forward blocks via
   session.forward on a dedicated work dir `20261104-exp8/qwen35-0.8b__argon-app/`, then write the round-N+1 message as
   `argon-app/5-qwen-weight-edit-relay-roundN.txt` (the page lists it) and tell Kevin. #6 (TASK, tools allowed) score
   like #1 as a separate tool-use arm. #7/#8 (TASK) deliver `apply_edit.py`: audit it first (no training/autograd, no
   network beyond the HF download, only in-scope tensors), run it in a no-network Modal container, then score
   edited vs unedited with the stated protocol (#7: MATH-500 x4, Gemma sampling, 8,192 tokens; #8: the Exp-8 eval).
1. [x] 2026-11-04 Loop C export (`scripts/nextaction.py split`, `data/splits.json`). Source: the frozen
   `next_action.jsonl` (76,970 rows, 1,276 sessions, 2026-07-12..09-16, so no gym/council sessions). Split: 70/10/20 of
   sessions by start time, 6 h purge before each boundary (167 sessions dropped): train 757 sessions / 64,695 rows, dev
   97 / 6,249, sealed test 255 / 4,186 (chmod 600 under ~/.z0int/state/tiny-gym/nextaction/sealed). Same OS user, so
   the seal is convention + hash, not OS-enforced.
   Finding: a few automated sessions dominate rows (train's largest session = 20% of rows; one dev session, a DELEGATE
   loop, = 73% of dev rows). Primary metric is now **session-macro** (each session weighted once).
2. [~] Controls. Parity (`data/controls-parity.json`, original row 80/20): majority 0.3186 and ridge 0.4122 reproduced
   exactly; **recency (same family as last step) 0.7404**, bigram 0.405. Dev, session-macro (`data/controls-dev.json`,
   49 scoring sessions): recency top-1 0.698 (top-2 covers 98%), ridge 0.639, bigram 0.636, majority 0.599.
   Remaining: MB arm (needs `Z0INT_MB_PROVIDER`), per-session bootstrap CIs on the macro metric, and the one-time
   sealed-test pass by tiny-evaluator. Also queue: a fresh export from state.db (data ends 2026-09-16).
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
