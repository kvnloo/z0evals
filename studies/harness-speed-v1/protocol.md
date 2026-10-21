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

## Amendments before the counted session (2026-10-21 03:15 UTC)

- A first session `s0` (five non-pi arms) was stopped after 10 latency blocks because the owner
  signed pi in. It is kept as `data/s0-aborted/` and is not analysed. The counted session `s1` runs
  all eight arms in the same interleaved blocks, so the pi bridging rule above is not needed.
- pi arms now pass `--` before the prompt: the extension flag `--rlm` swallowed the next argument
  (pi exited with no turn). Found in diagnostic smoke; no counted data existed.

## Session s2 (declared after s1 latency, before s2 runs)

C5 plus two exploratory follow-ups that s1 latency raised. Exploratory arms (X) were not in the
original plan; they are reported as exploratory and only compared with controls run in s2.

- C5: `omp-base` (gpt-6.1-sol) vs `omp-base@claude-opus-5-5` (omp's Anthropic sign-in, thinking
  low): cold latency 32 blocks + tasks 8 x 1 rep (claude lane near its weekly budget).
- X1: pi exits ~3 s after its answer in cold mode. `pi-base` vs `pi-base-offline` (`--offline`,
  "disable startup network operations"), cold latency 32 blocks.
- X2: Hermes called a tool on ~97% of `17 * 23` requests. `hermes-base` vs `hermes-base-clarify`
  (`-t clarify`, no shell/file tool), cold latency 32 blocks.
- All six arms (`omp-base`, `omp-base@claude-opus-5-5`, `pi-base`, `pi-base-offline`,
  `hermes-base`, `hermes-base-clarify`) share the same interleaved blocks, seed 20261023. C5 cost
  uses omp's own per-message cost fields, since the gpt-6.1-sol price table does not apply.

## Session s3 (declared 2026-10-21 ~05:55 UTC, before any s3 run)

Follow-up asked by the owner: sign the fx CLI in, fix Hermes on the MBP, add a minimal fast Hermes profile,
and find where Hermes's extra time goes. Smoke runs for the new arms are in `data/smoke-s3/` and are not analysed.

Changes on the host before s3 (none touch another harness's arm or the earlier data):

- **fx CLI sign-in.** fx 0.0.8 now reads `~/.fx/chatgpt-auth.json` (`{version:1, access_token, refresh_token,
  expires_at_ms, account_id}`, mode 0600), written by a script from `~/.codex/auth.json`; `fx provider codex`;
  `~/.fx/settings.json` `effort: low`. Hermes, pi and Codex already shared this one OAuth token family, so a refresh
  by any one client rotates the refresh token for all of them (see Confounds).
- **Hermes default profile.** `hermes chat` without `-t` failed with `invalid_params` because the CLI forwarded the
  configured `linear` MCP toolset (OAuth expired, needs a browser) into `session.create`, and the gateway rejects an
  unknown toolset. `mcp_servers.linear.enabled: false` was set in `~/.hermes/config.yaml` (backup kept). No arm
  in s1/s2 depended on it (every Hermes arm passed `-t`).
- **New Hermes profiles** `speed` and `speed-guided` (`hermes profile create <name> --no-skills --no-alias`;
  OAuth is read from the root `auth.json`, nothing copied). Config = Hermes's own "Blank Slate" minimisation
  (`hermes_cli/setup_quick.py`: compression, memory, user profile, checkpoints, smart routing off) with the toolset
  narrowed to `file` + `terminal` (`platform_toolsets.cli` plus every other toolset in `agent.disabled_toolsets`),
  no bundled skills, `plugins.enabled: []`, no MCP servers, no fallback providers, memory/skill nudges 0,
  `auxiliary.title_generation.model_upgrade_enabled: false`, `terminal.cwd: .`,
  `approvals.single_query_mode: approve` (in smoke, `--yolo` did not reach the multiplexed secondary profile and
  `python3 -c` was blocked), model `openai-codex/gpt-6.1-sol`, `agent.reasoning_effort: low`.
  `speed` additionally sets `agent.execution_guidance: false` and `agent.tool_use_enforcement: false`;
  `speed-guided` keeps both at `auto` (on for gpt models). Prompt caching is unchanged (always on).

New arms (exact argv in `bench.py` `arm_cmd()`):

| arm | what |
| --- | --- |
| `fx-cli` | fx CLI 0.0.8: `fx --context-limit skill_catalog_bytes=0 ask --no-save --full-access --no-color`; latency reads the raw text stream (first stdout byte = TTFT); tasks add `--json` (usage, tool calls; no cache split, no streaming) |
| `hermes-speed` | `hermes -p speed chat -q ...` with the same flags as `hermes-base` minus `--safe-mode`/`-t` |
| `hermes-speed-guided` | same on profile `speed-guided` |
| `hermes-default-ft` | default profile, no `--safe-mode`, `-t terminal,file` (latency only) |
| warm `hermes-speed` | `hermes -p speed acp`; `session/new` then `session/prompt` per request (ACP over stdio) |

Contrasts (analysis code `CONTRASTS`): C6 `hermes-base` vs `hermes-speed` (the whole speed profile);
C7 `hermes-speed` vs `hermes-speed-guided` (execution/tool-use guidance only); C8 `hermes-base` vs
`hermes-default-ft` (`--safe-mode` only, latency); C9 `hermes-default-ft` vs `hermes-speed-guided` (default profile
config vs minimal profile, guidance on in both, latency); C10 fx CLI vs `fx-base`, `pi-base`, `hermes-speed`;
C11 `hermes-speed` vs `pi-base`, `fx-base`, `omp-base`. Anchors `pi-base`, `hermes-base`, `fx-base`, `omp-base` are
rerun in the same interleaved blocks; s3 rows are compared only with s3 rows.

Workloads: cold latency 1 warm-up + 32 blocks, 8 arms, seed 20261024; warm 1 + 30 rounds (`hermes-speed` ACP,
`fx-base`, `pi-base`, `omp-base`), seed 20261025; tasks t01-t08 x 2 reps (session `s3`) and six new harder tasks
h01-h06 x 2 reps (session `s3h`), six arms (`pi-base`, `hermes-base`, `fx-base`, `fx-cli`, `hermes-speed`,
`hermes-speed-guided`), seed 20261024. The harder tasks are multi-file feature work with visible and hidden tests
(reservations, config interpolation + includes, event bus with wildcards, money rounding/allocation, expression
parser, CLI word stats); verifier validity re-checked for all 14 tasks (originals fail, references pass).
Runner: `harness/run_s3.sh`.

Confounds added: fx-cli runs fx's own system prompt and tools (the confound noted for `fx-base` is gone for this
arm) but its JSON usage has no cache-read split, so its cost estimate is an upper bound and its task
`model_requests` is `steps + 1` (estimated). fx-cli latency TTFT uses raw text mode, tasks use `--json`.
Hermes speed arms run through the resident multiplexed gateway like every other non-safe-mode Hermes arm.

## Not claimed

No claim about other models, long tasks, large repos, multi-turn chats, concurrency, or any host
other than the MBP. Hermes on the MBP is v0.22.1 (`ca069e1`), not the groot build (`c9dce2c`).
