---
title: "Same model, four harnesses"
subtitle: "Hermes, fx, pi and omp on gpt-6.1-sol, one variable at a time"
study: harness-speed-v1
status: evidence-local
mock_data: false
author: "Zer0 Research"
date: "October 21, 2026"
---

<div class="evidence-banner">
Draft. Local measurements on one host (a 2014 MacBook Pro running Linux), a main same-model comparison,
eight small tasks and six harder tasks. An earlier, separate model contrast is retained. Protocol committed before the runs; raw rows in <code>studies/harness-speed-v1/data/</code>.
</div>

## What we changed and what we held still

Every arm used the same model (`gpt-6.1-sol`, reasoning effort low) on the same ChatGPT
subscription, on the same machine, one request at a time. Arms ran interleaved in seeded random
order, so network and provider drift hit all of them equally. The four harnesses each ran at a
minimal baseline: plugins, skills, rules and MCP off, and only file and shell tools. Then we
changed one thing inside a harness at a time.

The original `fx-base` arm is the libfx 0.0.14 engine with four tools and a three-sentence
system prompt that we wrote. The follow-up session s3 also measures the signed-in fx CLI as
`fx-cli`. These are different arms: the engine's small token counts are not the CLI's.

## Latency: a one-line arithmetic question

Each request started a new process (cold), 32 interleaved blocks. Medians, with 95% bootstrap CIs:

| arm | first token (s) | done (s) | notes |
| --- | --- | --- | --- |
| fx-base | 2.13 [2.06, 2.41] | 2.23 [2.17, 2.57] | |
| pi-base | 2.13 [2.03, 2.27] | 5.23 [5.15, 5.40] | the process exits about 3.1 s after the answer |
| omp-base | 3.70 [3.58, 3.95] | 3.82 [3.70, 4.13] | about 2.3 s of startup before the request |
| hermes-default | 7.19 [6.93, 7.86] | 7.88 [7.68, 8.49] | ran a tool in 97% of requests |
| hermes-base | 11.06 [10.85, 11.30] | 12.89 [12.53, 13.35] | ran a tool in 97% of requests |

When the harness process is already running (warm, with a new conversation per request), fx, pi
and omp are within about 0.2 s of each other, at 1.7 to 1.8 s to first token. Hermes was not
measured warm in s1; s3 below adds ACP. Much of the cold gap between fx, pi and omp is process
startup and shutdown, not the agent loop.

Hermes also ran a shell command to multiply 17 by 23 in almost every s1 request. Removing its
shell and file tools in exploratory s2 reduced first token by 3.4 s (paired median, CI [2.2, 4.3]).
The remaining safe-mode overhead was unexplained at that point. The follow-up below identifies
managed-worker startup and instruction-driven tool use; the original baseline is not a minimal
fast Hermes configuration.

## Eight small coding tasks

Fix an off-by-one, implement slugify, handle CSV quoting, add a CLI flag, write an LRU cache,
parse durations, rename a function across three files, deep-merge dicts. The verifier restores the
original tests and adds hidden ones. Two runs per arm per task:

| arm | passed | wall time median (s) | input tokens | tool calls |
| --- | --- | --- | --- | --- |
| pi-solpi | 16/16 | 13.7 [13.4, 15.3] | 6,534 | 3 |
| fx-base | 16/16 | 15.1 [13.8, 17.2] | 3,157 | 4 |
| pi-rlm | 16/16 | 15.5 [14.4, 17.4] | 10,258 | 3 |
| pi-base | 16/16 | 15.5 [14.2, 17.2] | 7,445 | 4.5 |
| omp-base | 16/16 | 21.5 [19.5, 22.7] | 35,644 | 6 |
| omp-default | 16/16 | 27.0 [25.1, 28.8] | 115,562 | 7.5 |
| hermes-base | 16/16 | 30.4 [28.5, 33.4] | 32,744 | 6.5 |
| hermes-default | 16/16 | 32.9 [31.5, 35.2] | 185,896 | 9 |

Every arm passed every task, so these tasks do not separate the harnesses on quality. They are too
easy for that. What they do separate is how much work each harness does to get there. fx and pi
finish in about half the time Hermes takes, and with a tenth to a quarter of the input tokens.

## One change at a time

- **Hermes, default config vs safe mode:** about 5.7 times the input tokens per task and 2.5 more
  tool calls. Wall time was not measurably different.
- **omp, your config vs off:** about 0.8 s more cold latency, 0.3 s more warm, 5.5 s more per
  task, and 3.2 times the input tokens.
- **pi + SoL-Pi:** about 900 fewer input tokens per task (paired CI [650, 1,180]) and one fewer
  tool call. Wall time was 1.9 s lower. That passes our preregistered test (CI of the difference in
  medians [−3.4, −0.1]), but the paired-by-task analysis we added later does not confirm it
  ([−1.8, +0.3]), so treat it as weak. Latency was unchanged.
- **pi + pi-rlm:** 1.5 fewer tool calls but about 3,200 more input tokens per task. Wall time and
  latency were unchanged.
- **pi `--offline`:** did not remove the 3 s exit delay.
- **Model (omp-base, gpt-6.1-sol vs claude-opus-5-5):** latency was the same within noise. On the
  tasks, Opus finished in 13.0 s against 22.1 s, with half the tool calls. Both passed 8 of 8. At
  omp's own list prices, Opus cost about 2.9 times as much ($0.41 vs $0.14 for the eight runs).
  That is one run per task, in a session where the host was busier.

## Follow-up: fx CLI and a fast Hermes profile (s3)

The s3 amendment was committed before its runs. No earlier rows were replaced. Each cold arm
has 32/32 correct requests; each warm arm 30/30. Same-session cold medians:

| arm | first token s [95% CI] | total s |
| --- | --- | --- |
| fx-base (custom libfx host) | 2.00 [1.94, 2.08] | 2.11 |
| fx-cli | 2.22 [2.03, 2.38] | 2.22 |
| pi-base | 2.09 [1.96, 2.15] | 5.17 |
| omp-base | 4.07 [3.79, 4.25] | 4.22 |
| hermes-base (safe mode) | 11.13 [10.79, 11.58] | 12.98 |
| hermes-default-ft (same file/terminal toolsets, no safe mode) | 6.17 [5.91, 6.45] | 6.78 |
| hermes-speed-guided | 5.61 [5.44, 5.96] | 6.03 |
| hermes-speed | 3.18 [3.03, 3.30] | 3.67 |

`speed` is an isolated Blank Slate profile: file/terminal only, no plugins, skills, MCP,
memory, compression, fallback or auxiliary title upgrade; low reasoning, execution guidance
and tool-use enforcement off. `speed-guided` differs only in retaining those two guidance settings.
Turning guidance on adds 2.43 s to the median first token (unpaired CI [2.20, 2.79]): it induces
a shell call for arithmetic. Dropping safe mode saves 4.96 s (CI [4.52, 5.50]) in C8.
The whole speed configuration saves 7.95 s against the original safe-mode baseline (CI [7.60, 8.43]).
These are separate contrasts, not an additive decomposition of medians.

A diagnostic timeline (one request per configuration, not counted) shows safe mode starting a
cold managed worker and attaching it before any model request. That example costs 8.4 s for
worker startup/attach; the counted safe-mode contrast above is smaller. CLI startup still costs
roughly 1.7–2.7 s in those diagnostic examples. With a long-lived ACP process, Hermes-speed
reaches first token in 1.83 s [1.74, 1.93], versus pi 1.70, omp 1.74 and libfx 1.97 s. That
warm result is for ACP, not an interactive TUI or an established multi-turn conversation.
See `data/diag/hermes-stage-timeline.md` for the diagnostic timings.

The `invalid_params` startup error was traced in the prior diagnostic run to forwarding the
unavailable Linear MCP toolset into gateway session creation; explicit file/terminal toolsets
worked. `hermes doctor` is not a clean bill of health: it still reports missing optional provider
configuration and upstream dependency advisories, while Codex auth is logged in. This follow-up
made no owner/default-profile changes and did not refresh or copy credentials again.

### More task work, still no quality separation

| arm | small tasks pass | small wall s [95% CI] | harder pass | harder wall s [95% CI] |
| --- | --- | --- | --- | --- |
| fx-base | 16/16 | 18.1 [16.6, 22.3] | 12/12 | 34.4 [29.8, 40.7] |
| pi-base | 16/16 | 22.2 [18.2, 27.1] | 12/12 | 40.6 [37.6, 45.0] |
| fx-cli | 16/16 | 29.5 [24.8, 32.1] | 12/12 | 54.7 [48.0, 58.5] |
| hermes-speed | 16/16 | 31.7 [27.0, 34.8] | 12/12 | 51.4 [46.4, 59.5] |
| hermes-speed-guided | 16/16 | 31.3 [29.3, 33.3] | 12/12 | 57.5 [53.2, 63.7] |
| hermes-base | 16/16 | 45.0 [37.7, 48.0] | 12/12 | 67.7 [62.4, 76.8] |

The six harder fixtures cover reservations, config includes/interpolation, wildcard events,
money allocation, an expression parser and CLI word stats. All 168 counted task runs passed
visible plus hidden tests without changing visible tests. That still does not establish quality
equivalence: just two runs per task, short synthetic workloads and wide pass-rate intervals.
Turning guidance off did not measurably improve small-task wall time (difference CI crosses zero).
The actual fx CLI is slower and uses more input than the bench-authored libfx host; it is not
valid to transfer the engine arm's token-efficiency claim to the CLI. fx CLI cache reads are
unreported, so its computed list-price cost is an upper bound.

The first s3 task attempt is preserved separately: 19 rows, three failed verifications and
sixteen passes, excluded as a whole after a secondary-profile working-directory bug caused
source contamination. The counted rerun pins the bench profiles' terminal directory per request;
it starts from restored fixtures. Output work copies were deleted by the runner, so later checks
can audit rows and verifier validity but cannot independently re-run each submitted patch.

## What this does not show

One old CPU, short synthetic tasks, one shared provider account for the main comparison; the
separate s2 model arm uses Anthropic. No claims about long tasks, big repos, multi-turn chats,
concurrency or other hosts. Interleaving spreads drift; it does not guarantee equal interference.
A concurrent Java build was observed at about 01:37 CDT (255% CPU, load 8.08) during the aborted
attempt; counted tasks restarted at load 3.90, falling to 0.57 at small-task completion and 0.77
at harder-task completion. There was no continuous temperature or throttling trace, so residual
thermal interference is unknown. s2 also had load up to 7.2. Compare arms only within sessions.
No inference reruns or heavy builds were launched during this retrieval/validation follow-up.
