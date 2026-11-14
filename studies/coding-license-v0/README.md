# Run the coding probe

Read [SPEC.md](SPEC.md) for tier definitions and result limits.
Use an already-configured CLI on an isolated fleet worker. Do not copy credentials into a job.
Confirm that the route has no incremental cost before you run it.

## Check the eval

Run from the repository root:

```bash
fleet-build --local-data --wait 1800 \
  --src-include studies/coding-license-v0 \
  --src-include studies/harness-speed-v1 \
  -- python3 -m unittest discover -s studies/coding-license-v0 -p 'test_*.py' -v
```

The checks require every original fixture to fail and every reference to pass.
The end-to-end control runs all 14 tasks through a synthetic response command.
That control is not evidence that any real model passed.

## Check a model

For a confirmed no-spend GPT subscription route, use fx only:

```bash
fleet-build --node mbp-host --local-data --wait 1800 \
  --src-include studies/coding-license-v0 \
  --src-include studies/harness-speed-v1 \
  --fetch license-results --out /path/to/local/evidence \
  -- python3 studies/coding-license-v0/eval.py run \
  --model ACTUAL_GPT_MODEL_ID --provider openai-codex --billing subscription \
  --out license-results \
  -- fx ask --model ACTUAL_GPT_MODEL_ID --json --no-save --no-color -- '{prompt}'
```

The worker must already have fx and its authorized subscription route.
The runner does not configure that route or obtain credentials.
For a free provider, replace the command after `--` with its existing CLI and use `--billing free`.
The CLI must accept the prompt argument and return the response format in the spec.
No provider-specific free CLI adapter is verified in this revision.
Do not assume that an installed CLI or a catalog entry proves model reachability.

A successful full run exits 0. A scored failure exits 1. An execution error exits 2.
Inspect `summary.md`, `summary.json`, and the attempt evidence before using a result.
A non-default `--reps` or `--timeout` run is diagnostic only.

A14's initial verification was blocked before execution by fleet admission and no-spend worker availability.
The operation folder holds the actual commands, errors, and unrun model inventory.
