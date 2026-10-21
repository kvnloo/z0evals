# Protocol: harness-speed-v1

Written 2026-10-21 before any counted run. Diagnostic smoke runs (one request per arm, to check
parsers) are stored under `data/smoke/` and never enter the analysis.

## Question

With the model held fixed, how much do the coding-agent harnesses **Hermes, fx (libfx), pi and
omp** differ in (a) request latency and (b) small-task success, wall time, tokens and tool calls?
Inside each harness, what does one plugin/tool configuration change do?

## Single-variable design

Control, identical for every arm: provider = OpenAI ChatGPT subscription through each harness's
own Codex/OpenAI OAuth sign-in, model = `gpt-6.1-sol`, reasoning effort = `low`, host = MBP
(`kvn@mbp`, 8 cores, 15 GB, Linux), one request at a time, fresh empty working directory (latency)
or a fresh git copy of the task repo (tasks), no session persistence where the harness allows it.

| comparison | variable | arms (everything else fixed) |
| --- | --- | --- |
| C1 harness | harness, each at its minimal baseline (plugins/extensions/skills/rules/MCP off, file+shell tools only) | `hermes-base`, `fx-base`, `omp-base`, `pi-base` |
| C2 Hermes config | default toolsets + user config/plugins vs safe-mode minimal | `hermes-base` vs `hermes-default` |
| C3 omp config | user config (extensions, MCP, skills, rules, LSP) vs off | `omp-base` vs `omp-default` |
| C4 pi efficiency plugins | one extension added to `pi-base` | `pi-base` vs `pi-solpi` (SoL-Pi, conservative config: actionFusion + observationPack) vs `pi-rlm` (@shift-labs/pi-rlm, `--rlm`) |
| C5 model (after C1-C4) | model only, on one fixed harness arm | `omp-base` gpt-6.1-sol vs `omp-base` claude-opus-5-5 (small arm; claude lane is near its weekly budget) |

omp has no RLM variant installed (checked `~/.omp/agent/extensions`, config, `omp --help`), so there
is no `omp-rlm` arm. An fx CLI arm is not run: fx 0.0.8 on the MBP is not signed in to any provider
(`fx status --json`: `auth: missing`); signing in needs the owner. The fx arm is therefore the libfx
0.0.14 engine (the engine behind the fx CLI) driven by `harness/fx_run.ts` with four host tools that
mirror pi's (read, write, edit, bash) and a three-sentence system prompt. This is a known confound:
fx's own CLI system prompt and tools are not what is measured.

Arm commands are the `arm_cmd()` table in `harness/bench.py` (exact argv, frozen with this file).

## Workloads

**W1 latency microbench (cold).** Prompt `What is 17 * 23? Reply with only the number.`; correct
iff the reply contains `391` and the process exits 0. One fresh process per request. Order: one
warm-up block (all arms once, excluded) then 32 blocks; inside each block every arm runs once in a
seeded random order (seed 20261021), so drift and host noise are spread across arms (ABAB-style
interleaving). Metrics, timed by the parent runner from `spawn`: TTFT = first assistant text
event on stdout; total = process exit. Harness-reported TTFT/duration are kept as secondary fields.
"Cold" here means cold harness process with a warm OS page cache (the warm-up block primes disk);
Hermes's CLI talks to the already-resident Hermes gateway on the host, which is how Hermes ships,
so its "cold" path is partly warm by design. This is recorded, not corrected.

**W2 latency microbench (warm), where the harness exposes a long-lived session.** Same prompt;
one long-lived harness process per arm (pi/omp `--mode rpc`, fx `fx_run.ts --serve`), fresh
conversation per request (`new_session` / new engine), 1 excluded warm-up request then 30, arms
interleaved round-robin in seeded random order per round. Hermes warm is not measured: its ACP
server takes the model from the profile config and switching models over ACP is known to wedge the
session, and changing the owner's profile config is out of scope. Its cold path already reuses the
resident gateway.

**W3 coding tasks.** Eight fixed tasks in `tasks/` (Python stdlib only, ~10-40 lines each): fix
an off-by-one, implement slugify, CSV quoting, add a CLI flag, LRU cache, duration parser,
multi-file rename, deep merge. Each has visible tests (in the repo) and hidden tests (only the
verifier sees them). Verifier `harness/verify.py` restores the original visible tests, adds the
hidden ones and runs `python3 -m unittest`; success = all pass. Verifier validity was checked before
any run: every original repo fails and every reference solution passes. Two reps per (arm, task);
inside each (rep, task) cell arms run in seeded random order. Timeout 600 s per run (counts as a
failure). Metrics: success, wall time (spawn to exit), tokens in/out (cache reads separated),
tool calls, model requests (exact for omp/pi from assistant messages; estimated for Hermes/fx as
tool batches + final answer), cost estimate.

**Cost estimate.** Turns run on a ChatGPT subscription (no marginal dollars). For comparability one
list-price table is applied to every arm: $2.00/M uncached input, $0.10/M cached input, $10.00/M
output (omp's catalog price for gpt-6.1-sol, read from its own per-message cost fields). Token
semantics differ per harness and are normalized in `bench.py` (`input_total` includes cache reads).

## Analysis (fixed before running)

- Per arm: n, success/correct count, median and bootstrap 95% CI of the median (10,000 resamples,
  percentile method, seed 7) for TTFT, total and task wall time; p90 reported as descriptive only.
- Pairwise comparisons only for the planned contrasts C1-C5: bootstrap 95% CI of the difference in
  medians and a two-sided Mann-Whitney U p-value (normal approximation). A difference is called only
  if its CI excludes 0. With several contrasts, treat p values as descriptive (no correction claimed).
- Success rates: k/n with Wilson 95% interval. Task wall time is reported over all runs and over
  passing runs only.
- Failed or timed-out requests are counted and reported; latency medians use correct requests only,
  with the error count next to them.

## Confounds known in advance

- Harnesses differ in system prompt size, tool schemas and default context; that is part of the
  harness variable in C1, not controlled.
- fx arm = libfx engine + bench-owned tools and prompt, not the fx CLI (see above).
- Hermes reaches the model through its resident gateway; pi/omp/fx call the provider in-process.
- One provider account for all arms; provider-side load is shared and spread by interleaving.
- pi needs an owner sign-in on the MBP (`pi` -> `/login`). If pi is unavailable when the other arms
  run, pi arms are run in a later session together with a bridging re-run of `omp-base` and
  `fx-base` in the same interleaved blocks, so pi is compared only with arms measured in its own
  session. The session id is stored on every row.
- n is small for tasks (16 runs per arm); success-rate CIs will be wide.

## Not claimed

No claim about other models, long tasks, large repos, multi-turn chats, concurrency, or any host
other than the MBP. Hermes on the MBP is v0.22.1 (`ca069e1`), not the groot build (`c9dce2c`).
