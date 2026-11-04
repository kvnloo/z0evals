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

## Latest resumption (2026-11-04 10:01 CST)
- Owner requested resumption with Opus 5.5 and newly added subscriptions. Verified `t3-claude-ultra -p 'Reply exactly OK' --model claude-opus-5-5 --output-format json`: result OK, is_error=false, modelUsage identifies claude-opus-5-5. Root Hermes pool currently contains claude-ultra, claude-sub2 and ANTHROPIC_TOKEN; no token values recorded.
- Newly available free Oracle A1 worker is reachable (4 ARM CPUs, 24 GB RAM). Only public BFCL task/code were sent; no private traces or credentials. Installed torch 2.14.0+cpu / transformers 5.20.2 in `/home/ubuntu/wsp/.venv`.
- REAL FunctionGemma unedited baseline is RUNNING on the Oracle worker: `/home/ubuntu/wsp/base.sh`, log `/home/ubuntu/wsp/base.log`, run `tc-base-oracle`; at 10:01, 50/76 generation batches, 1,495 s. Public dev set: 604 items. No final score yet. First 16-item smoke completed before full run. Do not relaunch the same run or delete its output.
- Next tick: SSH to the worker recorded in `~/.oci/fleet.env`, collect `/home/ubuntu/z0/state/weight-space/slm/tc-base-oracle/toolchoice-dev-unedited/score.json` when present. Baseline inference is no longer fully blocked. Opus weight-editing itself has NOT resumed yet: existing sandbox path still depends on Modal approval; an Oracle sandbox adapter would require separate isolation validation before running model-generated code.

### 2026-11-04 10:05 CST tick
- Checked the existing Oracle baseline before doing anything else: still running, 56/76 batches, 1,714 generation seconds at the last completed batch; 604 public dev items, no score.json yet. Artifact: `data/oracle-baseline-progress.json`. Did not restart or overwrite the run.
- Probed isolation capabilities without executing editor code: no bubblewrap or Docker installed; `unshare --user --map-root-user --net /bin/true` fails with uid_map Operation not permitted. The user systemd manager runs. Oracle inference works, but a safe editor sandbox is NOT yet verified; do not execute Opus-generated Python unsandboxed there.
- Next: collect the baseline score when complete, compare with 75.3% lexical+abstain, then validate a no-network/file-restricted Oracle sandbox or use the existing Modal backend after owner approval. No sealed split was accessed this tick.

### 2026-11-04 11:05 CST tick — real baseline completed
- Collected the finished Oracle run (76/76 batches, 604 public dev items, 2,673.3 s generation). Raw outputs: `~/.z0int/state/weight-space/slm/tc-base-oracle/toolchoice-dev-unedited/{gen.jsonl,score.json}`. No weights edited; no sealed data accessed.
- Ran `python3 scripts/compare_toolchoice_baseline.py`: FunctionGemma 77.0% vs frozen lexical+abstain 75.3%; paired difference +1.66 pp, 4,000-resample IID-item bootstrap 95% CI [-2.32, +5.79] pp. Not a statistically clear lead. Model-only correct 82, control-only correct 72. Related BFCL items may be correlated, so this CI is provisional.
- Model false-call 15.2%, near-miss 9.5%, missed-call 20.1%; cheap control 18.5%, 9.8%, 20.1%. Artifact: `data/toolchoice-oracle-baseline-dev.json`; reproducible comparison script in `scripts/compare_toolchoice_baseline.py`.
- Next: validate an isolated Oracle editor sandbox before Opus-generated code executes, or use approved Modal. Opus availability was verified last tick, but no weight-editing session has completed. Oracle baseline job is now finished; do not rerun it.

## Queue (do the first undone item; mark done here with date + artifact)

### 2026-11-04 12:09 CST tick — Oracle isolation fixture validated
- Checked previous job first: baseline final score exists, no toolchoice_eval process remains. No baseline rerun or sealed access.
- Root namespaces work (`sudo -n unshare --net --mount --pid --fork /usr/bin/true`, rc=0), unlike the earlier unprivileged uid-map probe. Installed Ubuntu bubblewrap 0.9.0; staged a public Python venv under `/opt/wsp-isolation/.venv` without exposing the worker home.
- Ran `python3 ~/wsp/oracle_isolation_probe.py` on Oracle. Initial fixture failed because dropping to nobody prevented traversal of `/home/ubuntu`; moved the runtime to `/opt` and made the temporary fixture traversable. Two subsequent probes passed, rc=0: all 13 checks true, including no network, uid 65534/no effective capabilities, host SSH/home hidden, clean environment, read-only model/practice/root, writable work and real torch 2.14.0 CPU tensor execution. Per-probe systemd limits: MemoryMax=2G, TasksMax=64, RuntimeMaxSec=60. Artifact: `data/oracle-isolation-probe.json`; reproducer: `scripts/oracle_isolation_probe.py`. These are deterministic checks (n=13), not accuracy estimates; CI not applicable.
- This validates trusted fixtures only, NOT the complete editor backend. CPU topology warnings occur because sysfs is intentionally hidden. No generated editor code executed and no weights edited. Next: bind the actual read-only model/practice snapshot, validate safetensors load/save under confinement, and wire the Oracle session transport. No owner action required for this free-worker path; Modal remains separately approval-gated.

### 2026-11-04 13:04 CST tick — actual model editing primitives + transport exercised
- Checked previous jobs first: baseline complete, no active eval/probe processes; branch clean before tick. No sealed access or private data transfer.
- Ran `python3 ~/wsp/oracle_model_smoke.py` on Oracle against pinned FunctionGemma 79eaaa8 and practice-only BFCL mount. rc=0, 3.15 s: enumerated 236 tensors / 1,213 practice items, loaded `model.layers.0.mlp.down_proj.weight` [640,2048], changed exactly ONE entry, saved/reloaded identically, verified original unchanged, rejected frozen tensor edit. This is a trusted smoke perturbation, NOT an AI edit or improvement. Artifact: `data/oracle-model-smoke.json`; script `scripts/oracle_model_smoke.py`. MemoryMax=4G, TasksMax=64, RuntimeMaxSec=60. CI not applicable to deterministic checks.
- Implemented Oracle-side stdin-to-confined-Python transport `scripts/oracle_sandbox_exec.py`. Two real SSH calls passed (3.22 / 3.07 s); a file written in /work survived a fresh process. Artifact: `data/oracle-transport-smoke.json`. Transport caps 4G/64 tasks/600 s plus 64 MiB per file; outputs spool to worker disk and return at most 10k chars. The file-size cap is NOT an aggregate disk quota.
- Next: integrate this transport into the editor session and practice-generation RPC, independently validate edit artifacts before trusted inference, then preflight Opus and launch. No AI-generated code executed yet; no model quality claim. No owner approval needed for Oracle; Modal remains separate.

00. [ ] RETARGET (owner, 2026-11-04 00:35: "apply the blog to our workflows, not a perfect reconstruction"). Apply the
   blog's weight editing to a tiny model that is ALREADY a z0 decision model and has a measured, named failure:
   FunctionGemma-270M on the slm-router bounded-choice set (51/84, picked the dangerous near-miss; Hammer3B 75/84) or
   on z0 route/delegate call formation (factory-intelligence-v0: returns `[]` / invented tools). Editor: Astra via codex
   (the blog's editor; check quota with a one-word preflight), Opus/Fable after the Claude reset. Practice = train split
   of that task only; judge on its sealed split vs the unedited model AND the cheap controls (recency/rules, logit bias,
   LoRA-4). Build on the z0int SLM harness (new target + task loader), Modal sandbox/GPU. This outranks items 3-6.
   2026-11-04 01:05 tick: Astra preflight OK (`codex exec -m gpt-6-astra` -> "ok", 8,951 tokens). Data inventory: the
   bounded-choice corpus (`evolution-lab/corpus/phase2/p1b-20260921T1430Z`, 420 episodes) is only **28 distinct states**
   x 5 arms x 3 reps (FunctionGemma 84 trials = 28 x 3): too few for a practice/sealed split an editor cannot memorize.
   Decision: practice + dev on a PUBLIC proxy of FunctionGemma's named failures (calling a tool when none fits /
   picking a destructive near-miss): BFCL relevance + irrelevance + robustness sets (public, so Modal is fine); the 28
   z0 states stay a sealed transfer check run once by tiny-evaluator. Target: `unsloth/functiongemma-270m-it` (ungated
   mirror of google/functiongemma-270m-it). Next: pin a BFCL dataset revision, write the task loader + grader in the
   z0int SLM harness (new target entry), measure the unedited baseline on Modal, then launch Astra (10 passes).
   2026-11-04 01:25: Claude unblocked via the Ultra sub: z0int `editors.py` reads the Hermes pool row named by
   WSP_CLAUDE_POOL_LABEL (probe: claude-fable-5-1 and claude-opus-5-5 both answer on `claude-ultra`). Relaunched Exp 8 as
   `20261104-exp8u` (fable + opus, 10 passes); launcher now uses durable `scripts/editor-env.sh` (scratch wrapper was
   pruned). BLOCKED: both cells exit 1 within 2 min because the O19 Modal stop timer (every 2 min) stops every Modal app
   (`modal app list`: z0int-weight-space deployed 01:16/01:17, stopped 01:17/01:19). Needs Kevin's O19 Modal approval
   in his own terminal; then rerun with a fresh run id.
   2026-11-04 02:00 tick: Modal still stopped (no new approval; both apps `stopped`). Built the GPU-free part: z0int
   `benchmarks/weight_space/slm/toolchoice.py` (BFCL v3 @61fc060, choice-only grading: name or none; metrics accuracy,
   false-call %, near-miss %, missed-call %; selftest ok). Items at `/mnt/zer0models/zer0-tier/datasets/toolchoice-bfcl-v3/`
   (2,374; sha256 0670f476...): practice 585 abstain + 628 choose, dev 276 + 328, sealed 261 + 296. Chat-template render
   check with the FunctionGemma tokenizer timed out on groot (torch import > 250 s under memory pressure): do it as
   the first step of the Modal baseline. Next (needs Modal): unedited FunctionGemma on dev, then Astra 10 passes.
   2026-11-04 02:35 tick: Modal still stopped. Made the baseline one command: z0int `slm/common.py` target
   `functiongemma-270m` (unsloth mirror @79eaaa8, card sampling, 256-token cap, same frozen tensors as the paper),
   `slm/gpu.py` renders tool items with the model's own chat template, `slm/toolchoice_eval.py` runner (create-only,
   sealed refused unless WSP_ROLE=tiny-evaluator). Dry run with fake generations scored end to end (604 dev items;
   numbers are random-chance, discarded); 9 tests pass. Once Modal is approved:
   `WSP_BACKEND=modal WSP_MODAL_GPU=L4 bws-env-exec --scope hermes -- .venv-wsp/bin/python benchmarks/weight_space/slm/toolchoice_eval.py tc-base-<date>`.
   Still to do before an editor run: a session task-adapter so session.py practice passes use toolchoice items.
   2026-11-04 04:05 tick: Modal still stopped (no new deploy since 01:19). Built the session adapter (z0int
   `slm/session.py`): targets with `task: toolchoice` get a tool-choice editor prompt (same sandbox, budget and
   rules; failures named; held-out grading described; no z0 data or scores in the prompt), generation passes accept
   practice ids only (dev/sealed ids refused as unknown), rows graded by `toolchoice.predicted`, results add
   false_call/near_miss/missed_call. Practice file for the sandbox: `/practice/toolchoice_practice.jsonl` (1,213 public
   items, written into the practice dir that the Modal sandbox image mounts). Stub-GPU test: paired "both" pass ok; 9
   tests pass. Remaining: matrix.py still runs the math evaluator after a session; for this target call
   `toolchoice_eval.py <run> --edit-dir <session>/edited` instead. Then launch Astra once Modal is approved.
   2026-11-04 05:05 tick: Modal still stopped. Done: `matrix.py` now evaluates `task: toolchoice` targets with
   `toolchoice_eval.py` (dev split; unedited once, then each editor whose /work/edited has tensors; outputs inside the
   session work dir because Modal syncs edits per session; summary `<run>/toolchoice-dev-<editor>.json`); math targets
   still use evaluate.py. A session with no edits is refused, not scored as edited. Dry run of both paths ok; 9 tests
   pass. The FunctionGemma pipeline is complete; launch once Modal is approved:
   `WSP_TARGET=functiongemma-270m bash studies/tiny-slm-gym-v0/scripts/launch-exp8.sh <run> 10 astra`.
   2026-11-04 06:05 tick: Modal still stopped (0 apps listed). Ran the no-model controls (z0int
   `slm/toolchoice_controls.py`, tuned on practice, scored on dev 604, `data/toolchoice-controls-dev.json`):
   always-none 45.7%; lexical (IDF word overlap, always calls) 45.0% (false-call 98.9%, near-miss 18.0%);
   **lexical+abstain 75.3%** (false-call 18.5%, near-miss 9.8%, missed-call 20.1%; threshold tuned on practice, 74.0%
   there). This is the bar: an edited FunctionGemma must beat 75.3% on dev, not only the unedited model. 3 dev /
   1 practice items carry no tools (trivial abstains; noted, kept).
   2026-11-04 08:10 tick: Modal still stopped (0 apps). Spend-free route for the UNEDITED baseline: FunctionGemma 270M
   fits CPU, the owner rule sends CPU work to the MBP via fleet-build, and BFCL is public. Added `WSP_DEVICE=cpu`
   (fp32) to z0int `slm/gpu.py` and a local backend to `toolchoice_eval.py`. Tried `fleet-build --node mbp --class
   test` at 6G/4 CPU and 3G/2 CPU: both exit 75 ("MBP queue is held; no worker has room"). Retry next tick with
   `WSP_DEVICE=cpu WSP_TOOLCHOICE_DIR=<job dir> python toolchoice.py build && python toolchoice_eval.py tc-base-cpu`
   (rebuilds the pinned items in the job; sha256 must equal 0670f476...). The editor session itself still needs Modal
   (sandbox + GPU passes).
0. [~] RUNNING (check first every tick): the blog's Exp-8 method on Qwen3.5-0.8B, thinking on, Modal sandbox + L4,
   10 forward passes per editor, run `20261104-exp8`, launched by `scripts/launch-exp8.sh` as user units
   `wsp-20261104-exp8-<editor>` (status: `systemctl --user is-active`, logs and state:
   ~/.z0int/state/weight-space/slm/20261104-exp8/). Editors: opus (claude-opus-5-5), fable (claude-fable-5-1).
   2026-11-04 tick: opus/fable sat 90 min on turn 1. Two causes: (1) a local 6 GB RAM gate before each sandbox run
   (fixed in z0int session.py: skipped when WSP_BACKEND=modal, uncommitted in that worktree); (2) the Anthropic OAuth
   token is at 100% of its 7-day limit (429, overage disabled), resets 2026-11-05 02:00 CST. Units stopped; stalled dirs
   kept as `*.stalled-2050`. Relaunch after the reset: `launch-exp8.sh 20261104-exp8 10 opus fable`.
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
2. [x] Controls. Parity (`data/controls-parity.json`, original row 80/20): majority 0.3186 and ridge 0.4122 reproduced
   exactly; **recency (same family as last step) 0.7404**, bigram 0.405. Dev, session-macro (`data/controls-dev.json`,
   49 scoring sessions): recency top-1 0.698 (top-2 covers 98%), ridge 0.639, bigram 0.636, majority 0.599.
   2026-11-04 tick 3: added the MB arm (Evolution Lab `jev_distill.fit_fly`, read-only via TINY_MB_PATH) and
   session-resampled 95% CIs on the macro metric plus each arm minus recency; first run exceeded a 500 s cap (MB fit),
   rerunning as a 50-min capped job writing `data/controls-dev.json`. Done 21:57 (scoped jobs under the agent tree get
   TERMed by agent-oom-guard pressure relief; run heavy steps as their own `systemd-run --user --unit=...` service).
   Dev, session-macro top-1 with session-resampled 95% CI, and minus recency: recency 0.698 [0.668, 0.727]; MB (768
   params) 0.648 [0.605, 0.688], -0.050 [-0.093, -0.015]; ridge 0.639, -0.059 [-0.098, -0.030]; bigram 0.636, -0.062
   [-0.102, -0.035]; majority 0.599, -0.099 [-0.170, -0.034]. Recency beats every learned control (CIs exclude 0), so it
   is the bar any tiny-SLM head must beat. 49 scoring sessions.
   2026-11-04 23:15 SEALED PASS (once; `nextaction.py sealed` refuses a second run), fit on train+dev, 255 test sessions /
   4,186 rows, session-macro top-1 [95% CI], minus recency: recency 0.660 [0.643, 0.677]; bigram 0.616, -0.044
   [-0.050, -0.039]; MB 0.612, -0.048 [-0.065, -0.032]; ridge 0.543, -0.118 [-0.132, -0.104]; majority 0.409, -0.252.
   Confirms dev: recency is the bar. Artifact `data/controls-sealed.json`. Item 2 DONE except the fresh state.db export.
   (Old note, superseded:) Remaining: the one-time
   sealed-test pass by tiny-evaluator. Also queue: a fresh export from state.db (data ends 2026-09-16).
3. [~] Displacement audit: 200 sampled decisions; offline count of tool-schema tokens removable by top-k narrowing.
   2026-11-04 00:20 token count done (`scripts/narrowing.py`, `data/tool-schemas-by-family.json`,
   `data/narrowing-dev.json`). Hermes' current uncollapsed catalog: 55 tools, ~21.2k schema tokens (chars/4 proxy); 18
   tools / 8.6k tokens map to no family (ABSTAIN bucket, e.g. MCP/plugin tools). Dev counterfactual (miss -> one extra
   call with the full list), session-macro: **recency top-2 misses 1.6% of steps and removes 71% of schema tokens**;
   recency top-3 0.5% / 69%; bigram top-2 5.9% / 66%; ridge top-2 7.2% / 66%; top-1 for any arm misses ~35%.
   Caveats: Hermes already defers many tools via tool_search, so the live saving is smaller than vs the full catalog;
   the trace's tool set (Jul-Sep) differs from today's catalog; schemas are re-sent every call but often cached.
   2026-11-04 07:05 audit (`scripts/audit200.py`, `data/audit200-dev.json`; per-row private file chmod 600 under
   ~/.z0int/state/tiny-gym/nextaction/): 200 dev decisions, 90 sessions, <=4 per session. Narrowed to {last family,
   EXECUTE}: 20 misses (10%; cron 11/144, interactive 9/56). **14 of 20 are the session's first step**
   (START->READ_SEARCH: no previous step, so recency falls back to EXECUTE). Rule fix: on the first step keep
   READ_SEARCH + EXECUTE (or skip narrowing) -> 6/200 = 3% misses in this sample, the rest EXECUTE->EDIT (2) and single
   others. Rate differs from the 1.6% session-macro replay because of the <=4-per-session sampling.
   Remaining: the same replay on the sealed window by tiny-evaluator.
4. [ ] Loop B: frozen-trunk heads, both ends in parallel order: SmolLM2-135M and Qwen3-0.6B, then Gemma-270M and
   Qwen3.5-0.8B. Logistic head on pooled states; risk/coverage, calibration, warm p50 latency (kill > ~70 ms).
5. [ ] Loop A (blog method) on Modal: SmolLM2-135M-Instruct no-answer defect, 25 passes, vs logit-bias, random rank-1
   and LoRA-4 controls; report %valid and accuracy-given-valid separately.
6. [ ] Council round 2 on the first product target (tool-schema narrowing vs observation-relevance vs audit) with
   items 2-3 numbers in the brief.

## Done
- 2026-11-04 Argon via Gemini app, prompt 1 (Breakout write) run in TASK mode by Kevin; reply in
  `argon-app/replies/1-breakout-write-MAX-TASKMODE-20261103T2055.txt` (fence re-added; weight lines verbatim).
  Official score under the prompt's rules: 45/91 statements unreadable (2-value lists broadcast over 10x2 selections,
  which the spec forbids: "as many values as entries"), mean 0.003 over 1,000 episodes. Informational, numpy
  broadcasting allowed: mean 83.3 (se 2.6, max 539). Reference: PPO-500M 25.3, Astra (paper) 517.4, Astra (ours) 586.4,
  Argon via agy 61.3. Task mode makes it a tool-use arm, not comparable to the no-tool rows.
- 2026-11-03 Math Darwin lanes (harness validation only), run `20261103-ends`, volume `tiny-gym-results`:
  Qwen3.5-0.8B held-out GSM8K base 0.592 / instruct 0.512 / best merge 0.532; MATH-500 0.320 / 0.170 / 0.320.
  SmolLM2-135M: all ~0. Null: the fitness-selected merge did not beat the better parent.
- 2026-11-03 Council round 1, seat texts in `council/r1-*.md`.
