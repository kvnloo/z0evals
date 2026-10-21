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
Draft. Local measurements on one host (a 2014 MacBook Pro running Linux), one model, eight small
tasks. Protocol committed before the runs; raw rows in <code>studies/harness-speed-v1/data/</code>.
</div>

## What we changed and what we held still

Every arm used the same model (`gpt-6.1-sol`, reasoning effort low) on the same ChatGPT
subscription, on the same machine, one request at a time. Arms ran interleaved in seeded random
order, so network and provider drift hit all of them equally. The four harnesses each ran at a
minimal baseline: plugins, skills, rules and MCP off, and only file and shell tools. Then we
changed one thing inside a harness at a time.

The fx arm is the libfx 0.0.14 engine, the engine behind the fx CLI, with four tools and a
three-sentence system prompt that we wrote. The fx CLI on this host was not signed in, so we did
not measure the CLI itself. Keep that in mind when you read fx's token counts.

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
measured warm. So most of the cold gap between fx, pi and omp is process startup and shutdown,
not the agent loop.

Hermes is slower, and the time is inside the turn Hermes itself reports (11.7 s median for the
base arm, about 1.2 s more for the CLI). Hermes also chose to run a shell command to multiply 17 by
23 in almost every request. When we took its shell and file tools away (exploratory arm, second
session), first token fell by 3.4 s (paired median, CI [2.2, 4.3]), but the turn was still
about 10 s. We did not find the cause of the rest. The safe-mode baseline was slower than Hermes's
default configuration (11.1 s vs 7.2 s to first token). That is the opposite of what we expected,
and we have no explanation for it yet.

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

## What this does not show

One host, an old CPU, one model, small tasks that every harness solves. We did not test long
tasks, big repos, multi-turn chats, concurrency, or the fx CLI. The fx arm's prompt and tools are
ours, so its small token counts say more about our minimal setup than about fx. The second session
ran with a busier host (load average up to 7). Its numbers are compared only with arms from the
same session.
