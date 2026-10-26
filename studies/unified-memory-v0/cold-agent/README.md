# Cold-agent recall arm (cohort v1)

Owner acceptance test for unified memory: drop a fresh agent with no context into a
harness and ask it a specific question about a past workflow that happened in a
*different* harness or on a *different* host. "MCP configured" is not a pass; a
correct answer is.

## What the arm controls

- Fresh Claude Code agent: `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`,
  `--setting-sources ""` (no hooks, plugins or user settings), `--tools ""` (no file or shell
  access), `--strict-mcp-config` with only the memory MCP, `--no-session-persistence`
  (eval runs never enter the index they are scored against), empty working directory.
- The only evidence path is the memory MCP (`search`, `fetch`).
- Scoring is deterministic substring matching on gold `must` groups. No judge model.
- Recorded per question: `correct`, `said_unknown`, `false_confident` (wrong and not
  `UNKNOWN`), `cites_gold` (answer names the gold session id), seconds, turns, cost.

## Question file (private, never committed here)

```json
{"id": "q01", "source_harness": "codex", "source_host": "<alias>",
 "handle": "<harness>:<session id>", "q": "...", "must": [["alt1", "alt2"], ["second fact"]]}
```

Admission rule: a question counts only when every `must` group appears verbatim in the
transcript named by `handle` (checked before the run). Gold text and questions come from
private transcripts and stay on the private host; this directory holds the harness and
scrubbed aggregate results only.

## Run

```sh
COLD_MCP_CONFIG=/path/to/memory-mcp.json PAR=3 python3 run_cold.py questions.json results.json
```

## Results (scrubbed aggregates)

| Run | Index state | Correct | False-confident | Cites gold handle |
|---|---|---|---|---|
| 2026-10-26 before | laptop-host history not indexed; grants cover 10 projects | 8/25 (32%) | 1 | 3 |
| 2026-10-26 after ingest | laptop host indexed (claude, codex, omp, hermes); grants widened to 32 projects | 11/25 (44%) | 1 | 6 |
| 2026-10-26 after ranking fix | + search ranked across grants (z0intelligence#243) | 15/25 (60%) | 2 | 10 |

Question mix: 17 from the laptop host (6 Claude Code, 6 Codex, 5 OMP), 7 from the
server host (3 Hermes, 2 Codex, 1 Claude Code, 1 OMP), 1 from the ChatGPT app. Every question is
asked in Claude Code, so 18 of 25 cross a harness boundary. The agent runs on the laptop host and reaches the memory index on the server host through the MCP over SSH.

After the ranking fix, 13 of the 15 questions whose source project is inside the 32 granted
scopes are correct (87%). 8 of the 10 failures sit in projects outside the grants: the policy
allows at most 32 explicit project grants and no wildcard, so long-tail projects stay invisible.
Widening that is an owner decision, not a harness change.

After the ranking fix: p50 87 s, p90 146 s, median 9 turns per answer (v1 targets: p50 60 s, p90 180 s, 8 turns).
