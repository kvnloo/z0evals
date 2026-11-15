---
title: "three different meanings of fast"
subtitle: "recorded first-token latency, usage-backed decode rates, and parallel completions without invented token counts"
study: speed-measurements-v0
status: evidence-local
author: "zer0 research"
date: "november 6, 2026"
mock_data: false
toc:
  - id: scope
    label: what was measured
  - id: ttft
    label: first text in a warm process
  - id: decode
    label: single-request decode rate
  - id: parallel
    label: parallel completions are not tokens per second
  - id: limits
    label: what remains unknown
---

## what was measured {#scope}

These are source-reported benchmark measurements, not simulated estimates and not independently rerun inference. The [draft study](https://github.com/kvnloo/z0evals/blob/9d3267b18f98b5ecfff98de56409a01f4f1d2213/studies/speed-measurements-v0/README.md) separates three runs and their clocks. The [provenance record](https://github.com/kvnloo/z0evals/blob/9d3267b18f98b5ecfff98de56409a01f4f1d2213/studies/speed-measurements-v0/data/provenance.json) hashes the original files and records exclusions. The experiment's original Git revision is unknown, so this is not a fully pinned experiment release.

## first text in a warm process {#ttft}

The recorded `ttft` profile has a median first-text latency of **0.4084 seconds** over 12 counted requests. One warmup remains in the file but is excluded. All 12 recorded responses passed the source's substring check for `391`. [Warm receipts](https://github.com/kvnloo/z0evals/blob/9d3267b18f98b5ecfff98de56409a01f4f1d2213/studies/speed-measurements-v0/data/warm.jsonl) and [recomputed summary](https://github.com/kvnloo/z0evals/blob/9d3267b18f98b5ecfff98de56409a01f4f1d2213/studies/speed-measurements-v0/summary.json).

The timer starts after conversation creation, when the ACP prompt is sent. It stops at the first nonblank agent-message chunk. This measures a warm process, not cold CLI startup, exact-answer correctness, or broad task quality. [Timing and verification method](https://github.com/kvnloo/z0evals/blob/9d3267b18f98b5ecfff98de56409a01f4f1d2213/studies/speed-measurements-v0/data/methods.json).

## single-request decode rate {#decode}

The A/B wire receipts report these median decode rates. Each cell uses three successful streaming requests with more than 250 provider-reported completion tokens, joined to the corresponding decode workload. [Summary](https://github.com/kvnloo/z0evals/blob/9d3267b18f98b5ecfff98de56409a01f4f1d2213/studies/speed-measurements-v0/summary.json), [wire receipts](https://github.com/kvnloo/z0evals/blob/9d3267b18f98b5ecfff98de56409a01f4f1d2213/studies/speed-measurements-v0/data/wire.jsonl), and [harness windows](https://github.com/kvnloo/z0evals/blob/9d3267b18f98b5ecfff98de56409a01f4f1d2213/studies/speed-measurements-v0/data/runs.jsonl).

| Recorded model label | fx tok/s | Hermes tok/s |
|---|---:|---:|
| local-qwen3.5-4b | 143.5 | 146.8 |
| nim-nemotron-lightning | 85.1 | 100.7 |
| kilo-nemotron-lightning | 73.8 | 90.0 |
| cohere-command-a-plus | 144.6 | 27.5 |

The wire collector divides provider-reported completion tokens by the interval between first and last qualifying deltas. Those deltas can include reasoning and tool calls. This is not visible-text-only throughput. The original endpoint clocks are absent, so this reanalysis reproduces medians of recorded rates rather than independently checking their clock ratios. The table does not isolate a causal harness effect. [Method and limits](https://github.com/kvnloo/z0evals/blob/9d3267b18f98b5ecfff98de56409a01f4f1d2213/studies/speed-measurements-v0/README.md).

The export retains failed receipts, including HTTP 429 and local rate-limit rejections. Decode medians exclude those failures. Another probe is excluded entirely because its code silently substitutes `characters / 4` for missing usage without marking estimated rows. [Status counts](https://github.com/kvnloo/z0evals/blob/9d3267b18f98b5ecfff98de56409a01f4f1d2213/studies/speed-measurements-v0/summary.json) and [excluded probe method](https://github.com/kvnloo/z0evals/blob/9d3267b18f98b5ecfff98de56409a01f4f1d2213/studies/speed-measurements-v0/data/methods.json).

## parallel completions are not tokens per second {#parallel}

The parallel run records 401 completed units in 184.48 seconds, or 2.1737 units per second. It planned 5,000 units and left 4,599 unrun. Its completed rows span three local lanes. Reconstructed request intervals overlap, which supports parallel execution but does not certify an instantaneous concurrency limit. [Completion rows](https://github.com/kvnloo/z0evals/blob/9d3267b18f98b5ecfff98de56409a01f4f1d2213/studies/speed-measurements-v0/data/parallel.jsonl), [run metadata](https://github.com/kvnloo/z0evals/blob/9d3267b18f98b5ecfff98de56409a01f4f1d2213/studies/speed-measurements-v0/data/parallel-run.json), and [interval method](https://github.com/kvnloo/z0evals/blob/9d3267b18f98b5ecfff98de56409a01f4f1d2213/studies/speed-measurements-v0/README.md).

The run reports zero failed units but eight rate-limited attempts on other lanes. Completion is not independently verified quality. Aggregate token throughput is withheld because the original runner and its token-count method were not independently established. It would be wrong to compare these units per second with a single stream's tokens per second. [Run metadata](https://github.com/kvnloo/z0evals/blob/9d3267b18f98b5ecfff98de56409a01f4f1d2213/studies/speed-measurements-v0/data/parallel-run.json) and [exclusion record](https://github.com/kvnloo/z0evals/blob/9d3267b18f98b5ecfff98de56409a01f4f1d2213/studies/speed-measurements-v0/data/provenance.json).

## what remains unknown {#limits}

Hardware interference, historical runtime revisions, model builds, and the parallel token-count method remain unverified. The warm, decode, and parallel runs are separate workloads, not controlled comparisons. The [manifest](https://github.com/kvnloo/z0evals/blob/9d3267b18f98b5ecfff98de56409a01f4f1d2213/studies/speed-measurements-v0/manifest.yaml) remains `draft`. The [offline analyzer](https://github.com/kvnloo/z0evals/blob/9d3267b18f98b5ecfff98de56409a01f4f1d2213/studies/speed-measurements-v0/analyze.py) recomputes the recorded summary with `--check`, without network calls or inference.
