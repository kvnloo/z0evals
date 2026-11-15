# Recorded speed measurements

This draft reanalyzes existing benchmark receipts. It does not rerun inference or independently certify the original measurements.

## Inputs and exclusions

[data/provenance.json](data/provenance.json) records SHA-256 hashes of each original file and inspected runner. The export copies named fields only. It omits response text, prompts, errors, headers, credentials, and private host paths.

- [Warm latency](data/warm.jsonl) retains all 13 rows from `lat-final.jsonl`, including repetition `-1`. The analysis excludes that warmup. The recorded profile is `ttft`. The receipt does not pin a model build.
- [Harness windows](data/runs.jsonl) retain the timing, arm, kind, repetition, and outcome fields from the A/B run. [Wire receipts](data/wire.jsonl) retain HTTP status, timing, model, streaming flag, and provider-reported usage counts. Failed receipts remain in the export.
- [Parallel completions](data/parallel.jsonl) retain identifiers, lane, model, completion flags, attempts, and timing from `bench-20261105T041047.jsonl`. [Run metadata](data/parallel-run.json) retains the planned count, wall time, unit outcomes, and lane attempt counters.
- `speed.jsonl` is excluded. The inspected `probe_all.py`, line 67, substitutes `chars // 4` when usage is missing. Its rows do not identify which counts came from that estimate.
- All parallel token fields are excluded. The original parallel runner and token-count method were not independently established. Recorded token totals do not prove that the counts are measured rather than estimated.

## Metric definitions

[Method excerpts](data/methods.json) freeze the inspected source lines cited below. They document code present at capture, not proof that those exact bytes ran in the original experiment.

The inspected `hermes_latency.py`, lines 63-79, times an ACP prompt from send until the first nonblank `agent_message_chunk`. It creates a fresh conversation in a long-lived process. Session creation occurs before the timer starts. Its recorded correctness flag checks whether the response contains `391`, not exact equality. This is a repeated arithmetic microbenchmark, not a general quality evaluation.

The inspected `fx-ab/wire_proxy.py`, lines 170-175 and 204-207, takes completion counts from the streamed usage object. It records decode rate as `completion_tokens / (last_delta_time - first_delta_time)`. Content, reasoning, and tool-call deltas can start the interval. This is not visible-text-only throughput. The source stores only the rounded rate, not the first and last clocks, so the analysis reproduces the median, not the underlying clock ratio.

The decode analysis selects non-warmup harness rows with `kind=decode`. It joins wire requests by lane and the source's wall-clock window rule. It requires a completion path, HTTP 200, streaming, more than 250 provider-reported completion tokens, an available duration, and an available decode rate. Models and harness arms remain separate. The source's summarizer uses the same time-window join and token threshold. No token estimate is substituted for missing usage.

Parallel wall time comes from the run metadata. Completion rate is the count of rows marked `ok` divided by that wall time. This measures completed units per second, not tokens per second or correct answers per second. Zero failed units does not mean zero failed attempts. Rate-limit attempt counters remain visible.

The interval diagnostic treats `t` as elapsed completion time and `s` as call duration. It reconstructs intervals as `[t-s, t)`. Source values have millisecond precision. The maximum reconstructed overlap is not a certified instantaneous concurrency limit. Rounding can make adjacent intervals overlap.

## Recompute

Run `python3 studies/speed-measurements-v0/analyze.py --check` from the repository root. Run the test suite through `fleet-build`, per the owner's compute policy. [summary.json](summary.json) contains only recorded metrics and deterministic arithmetic.

## Limits

The operation files were not versioned at capture. Their hashes identify the inspected bytes, not an immutable experiment Git revision. The manifest remains `draft`. The source repository SHA identifies publication tooling only. Hardware configuration, host interference, clock synchronization, runtime versions, and model revisions were not independently established. Separate warm-latency, A/B decode, and parallel runs are not controlled contrasts.

No aggregate token-rate comparison, universal harness ranking, subscription billing claim, or quality ranking follows from this study. Publication remains a separate owner-controlled action.
