# Hermes stage timeline (diagnostic, not counted)

One request each, `What is 17 * 23? Reply with only the number.`, MBP, 2026-10-21 00:36-00:37 CDT, Hermes
v0.22.1 (`ca069e1`). Seconds from the parent's spawn (t0). Event times come from the CLI's `--format stream-json`
stdout (parent clock) and from `~/.hermes/logs/agent.log` / `~/.hermes/profiles/speed/logs/agent.log` (same host
clock, millisecond stamps). Diagnostic only: n = 1 per row; the counted decomposition is contrasts C6-C9 in s3.

## `hermes -p speed chat -q ... --format stream-json` (new minimal profile, guidance off)

| t (s) | event |
| --- | --- |
| 0.00 | spawn |
| 1.72 | CLI prints `system/init` (Python start, CLI imports, plugin discovery in the client) |
| 1.97 | gateway accepts the CLI's websocket |
| 1.97-2.26 | gateway: `session.create`, tool registry availability checks |
| 2.26 | inbound message admitted |
| 2.40 | agent built, OpenAI client created |
| 2.66 | Codex stream request sent |
| 3.26 | first parsed SSE event |
| 3.88 | first substantive text; CLI prints `text 391` |
| 3.97 | API call done (`in=5321 out=5`, latency 1.3 s), turn ended, no tool |
| 4.16 | `result` event; process exit 4.30 |

Breakdown: CLI process start 2.0 s, gateway prep 0.7 s, model 1.3 s, teardown 0.3 s.

## `hermes chat --safe-mode -t terminal,file ...` (= arm `hermes-base`)

| t (s) | event |
| --- | --- |
| 1.91 | CLI `system/init`; gateway accepts the websocket |
| 1.94-7.19 | **safe mode starts a separate managed worker process** (cold Python start, agent build on its `MainThread`, Nous auxiliary lookups that fail) |
| 7.19-10.31 | worker attach: ~20 short websocket connect/close cycles, session registration |
| 10.31 | conversation turn starts |
| 12.38 | Codex stream request sent (title generation and auxiliary setup in between) |
| 14.99 | API call #1 done (`in=4243 out=29`, 2.5 s): **a `terminal` tool call for `17 * 23`** |
| 15.49-15.88 | `tool_use` / `tool_result` (`python3 -c 'print(17 * 23)'`) |
| 17.27 | text `391` (API call #2, 1.4 s) |
| 19.28 | `result`; exit 19.37 |

Breakdown: CLI start 1.9 s, managed worker ~8.4 s, pre-request 2.1 s, model 2.5 + 1.4 s, tool 0.8 s, tail 2.1 s.

## `hermes chat -t <19 default toolsets> ...` (= arm `hermes-default`, no safe mode)

| t (s) | event |
| --- | --- |
| 2.71 | CLI `system/init` (more client plugins than the speed profile) |
| 3.05 | tool_search: 31 visible tools, 28 deferred (~13.6k tokens) |
| 3.30 | plugin discovery in the gateway for this session (58 found, 53 enabled) |
| 4.25 | Codex stream request sent |
| 6.41 | API call #1 done (`in=22824 out=29`, 2.2 s): terminal tool call |
| 6.47-6.74 | tool |
| 8.73 | API call #2 done (2.0 s), text `391` at 8.59 |
| 9.12 | exit |

## Where the extra time goes (summary of the three rows)

1. `--safe-mode` (used by `hermes-base`) moves the turn into a freshly spawned managed worker: about 8 s per cold
   request before the first model call. The default and speed paths run the turn inside the resident gateway.
2. `agent.execution_guidance: auto` injects `<mandatory_tool_use>` "Arithmetic, math, calculations -> use terminal
   or execute_code" for gpt models (`agent/prompt_builder.py`, `OPENAI_MODEL_EXECUTION_GUIDANCE`). That is why
   Hermes ran a shell for `17 * 23` in 97% of s1 requests: one extra model round trip plus the tool, about 2.5-4 s.
3. The default toolsets add about 17k input tokens per call (22.8k vs 5.3k), worth a few hundred ms per call.
4. The Hermes CLI client itself costs about 1.7-2.7 s before it can talk to the gateway (Python start, imports,
   plugin discovery). Only the warm ACP path (`hermes -p speed acp`) avoids it.
