# coding-license-v0

## Scope

Any model can earn permission to write code for a task tier after it passes that tier's coding probe.
This study records probe results. It does not change production routing or grant broader permissions.
The fixtures test Python only. Tier L means the largest fixtures here, not general large-project competence.

The source is z0evals commit `1ec7c67e36cd6dfa57416b7afdd63ada2805158a`, `studies/harness-speed-v1/tasks/` and `harness/verify.py`.
`upstream-files.json` pins each restored file by Git blob ID.
No historical score counts as a new model result.

## Tiers and pass bars

| Tier | Task scope | Fixtures | Own-tier bar | Cumulative license bar |
|---|---|---|---|---|
| S | Bounded function or CLI repair | paginate, slugify, cliflag, duration | 8 of 8 attempts | 8 of 8 attempts |
| M | State, structured data, or package refactor | csvsum, lru, rename, merge | 8 of 8 attempts | S plus M, 16 of 16 |
| L | Multi-module feature with error and integration contracts | reserve, config, bus, money, calc, wordstats | 12 of 12 attempts | S plus M plus L, 28 of 28 |

`eval.py:TIERS` defines the task IDs. Each task runs twice in a fresh copy, with a 180-second model-process deadline.
The independent verifier runs the original visible tests and the hidden tests, with its existing 60-second deadline.
An attempt passes only if the CLI exits zero, its submitted files pass all tests, and no visible test changed.
Every cumulative prerequisite must pass. There is no partial-credit license.
An explicit `--reps` override is a diagnostic run, not the default two-repetition license.

`FAIL` means a scored submission failed its checks, or a required lower tier failed.
`INCOMPLETE` means an attempted prerequisite has missing or error results.
`NOT_RUN` means no required attempt ran. Neither status grants a license.
A CLI, authentication, quota, timeout, or response-format error stops the run immediately. It never triggers another provider or paid fallback.

## Model and evidence contract

The operator supplies an existing model CLI as an argument vector. One standalone `{prompt}` argument receives the JSON task prompt.
The prompt contains only the instruction, production files, and visible tests.
The model returns `{"files":{"relative/path.py":"complete source"}}` as JSON or one JSON code block.
The runner also accepts the documented fx JSON `final_output` field.
The response can change existing production Python files and add Python files inside existing packages.
The runner rejects traversal, symlinks, test files, startup hooks, and changes outside the fixture.
Tool edits do not receive a score. They remain in `cli-repo/` for inspection.

This is a text-response coding probe. It does not measure interactive tool skill.
The runner is not a hostile-code sandbox. Run it only inside the owner's isolated fleet job without secrets.
Public fixture visibility also prevents claims of benchmark contamination resistance.

Each attempt retains its prompt, raw response, stderr, command template, candidate files, and verification receipt.
`results.jsonl` records actual model ID, provider, process exit, elapsed time, and outcome.
`summary.json` includes the fixture source SHA and probe digest. `summary.md` is the per-model tier table.
Output directories are exclusive. A rerun needs a new directory and cannot overwrite prior evidence.

`--billing free` or `--billing subscription` is an operator attestation, not a price lookup.
Do not run until the existing CLI's route is confirmed to have no incremental cost.
Metered routes are not supported. GPT probes must use `fx`.
No credentials, provider policy, controller, or queue belong in this study.
