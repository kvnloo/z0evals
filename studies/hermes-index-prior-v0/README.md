# hermes-index-prior-v0

The [Hermes Index](https://portal.nousresearch.com/bench) is Nous Research's agentic leaderboard: each model runs four suites inside Hermes Agent (Hermes Bench, TerminalBench 4, TerminalBench Science, SkillsBench), pass@1, reasoning effort high where offered. The Index is the mean score and the mean cost per task across the four.

This study does two things:

1. **Snapshot the table as an external prior.** `data/snapshots/hermes-index-<ts>.json` records every row (index, cost per task, four suite scores and costs, the provisional flags, SkillsBench clean vs raw), the capture time and the raw page sha256. It is *source-reported*: we did not measure it.
2. **Record what we can run ourselves**, with a bounded adapter.

## How the prior is used

`scripts/to_benchmark_rows.py` turns a snapshot into the `--benchmark` input of z0intelligence's model-routing catalog generator (`operations/model-routing/generate_catalog.py`, PR kvnloo/z0intelligence#222). Rows land in `models[].benchmarks` with basis `external_benchmark`, the capture-stamped source URL and `floor: null`. **They never set `p_accept`.** That generator sets task-class acceptance only from canonical measured findings (see `../free-taskfit-v0`). A Hermes Index score is evidence about agentic coding in Hermes in general; O14 needs acceptance on a specific task class, so the Index stays a prior a human or a later calibrated model can read, not a routing input.

`data/identity-map.json` maps display names to catalog `(provider, model)` rows by exact family. Batch/fast/pro/region variants are excluded; free variants are mapped separately and labelled. "Nemotron Super 3.5" is left unmapped: the catalog only lists `nemotron-3.5-super-vl` and the page doesn't say which checkpoint it ran.

Refresh: `python3 scripts/snapshot_hermes_index.py --out data/snapshots/hermes-index-$(date -u +%Y%m%dT%H%MZ).json`. The parser fails closed if the column set changes, ranks are not contiguous, or an Index value differs from its four-suite mean by more than 0.06.

## What is runnable (checked 2026-11-03)

| Suite | Public? | Harness command | License |
|---|---|---|---|
| Hermes Bench (150 tasks) | **No.** No task set, grader or runner is published. `NousResearch` has no bench repo; the GitHub "hermesbench" repos are third-party. hermes-agent removed its Atropos benchmark envs (TB2, TBLite, YC-Bench) in 5af672c7, and `git log -G 'hermes[ _-]?bench'` over its Python history finds no Hermes Bench source. | none | n/a |
| TerminalBench 4 (66 tasks; the Index runs it without the 4 GPU tasks) | Yes | `harbor run -d terminal-bench/terminal-bench@4.0.0 -a hermes -m <model>` | Harbor/TB: Apache-2.0 |
| TerminalBench Science (~70 tasks) | Yes | `harbor run -d terminal-bench-science/terminal-bench-science@latest -a hermes -m <model>` | Apache-2.0 |
| SkillsBench | Yes | `bench eval run --tasks-dir tasks/<task> --agent <agent> --sandbox docker` (BenchFlow CLI, github.com/benchflow-ai/skillsbench) | Apache-2.0 |

Harbor (0.25.0) ships a built-in `hermes` installed agent: it installs hermes-agent from `main` inside the task container, runs `hermes --yolo chat -q <instruction> -Q`, and routes `openrouter/<id>` models with `OPENROUTER_API_KEY`. That is the same harness the Index uses, so a TB4/TB-Science number from this path is comparable in harness, though not in model route, effort or attempt count.

## Free-lane pilot adapter

`scripts/harbor_pilot.sh <dataset@version> <task> <openrouter/<id>:free> <jobs-dir> [max_turns] [timeout_mult]` runs one task, one attempt, on Docker, with these fail-closed guards: the model must be an OpenRouter `:free` id; the OpenRouter key must report a 0 USD credit limit (so no auxiliary call can bill); a turn cap and an agent-timeout multiplier are always set; toolsets are `terminal,file,todo`. Keys come from the environment only (run it under `dsh-env-exec`). Run it on a node with Docker and spare CPU (the MBP), not on a memory-starved host.

A one-task pilot proves the path runs and grades. It is not a score: one trial, a capped turn budget and a shortened timeout make any reward a lower bound for that model.
