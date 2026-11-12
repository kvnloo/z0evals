---
title: "Fast first tokens and parallel throughput are different measurements"
status: private-draft
item: RP06
measurement_date: 2026-11-05
publication_date: null
---

# Fast first tokens and parallel throughput are different measurements

This draft rechecks saved November 5 measurements. It does not report a new inference run. The inputs include parent-side Hermes latency events, per-unit parallel results, and recorded wall times. The arithmetic is reproducible from the allowlisted [measurement file](measurements.json) with [the offline checker](../../../scripts/rp06_measurements.py). Original paths and SHA-256 hashes are retained in that file. [S1][S2][S3][S4]

## First-token latency includes a long tail

In one warm Hermes ACP session, the twelve measured requests had a median first-text latency of 0.408 seconds. The slowest took 13.510 seconds. All twelve were marked correct by the producer. The initial warmup request, marked `rep: -1`, is excluded. The slow request is not. These results describe this saved session, not a general latency guarantee. [S1]

The producer sends `What is 17 * 23? Reply with only the number.` It starts the warm-request timer after `session/new` and stops it on the first nonblank `agent_message_chunk`. This is parent-observed first text, not a server-side decode benchmark. The correctness flag checks whether the output contains `391`, not whether it contains only that answer. [S5]

## Parallel work completed, but the queue did not drain

The following rows use recorded completion-token counts divided by the full recorded wall time. They are historical, source-recorded rates, not verified exact token measurements. The token-count provenance is unresolved. [S2][S3][S4]

| Saved run | Completed units | Units not run | Wall time, seconds | Recorded completion tokens | Recorded tokens per second |
|---|---:|---:|---:|---:|---:|
| 033902, cloud-only per the source notes | 598 | 4,402 | 600.02 | 259,726 | 432.9 |
| 040146, cloud plus local per the source notes | 554 | 4,446 | 190.08 | 181,184 | 953.2 |
| 041047, local-only per the source notes | 401 | 4,599 | 184.48 | 104,288 | 565.3 |

The labels come from the existing operating notes, not a fresh inspection of those services. The frozen raw rows independently reconcile the unit and token totals to the saved summaries. Zero terminal failed units in these summaries does not mean zero failed provider attempts. The original summaries retain lane errors and retries. Nor does `ok` establish answer quality. [S2][S3][S4][S7]

The cloud-only summary records **432.9**, not the approximately 434 in the older prose table. The mixed run's per-minute series in the old notes is based on `visible_tokens`, whereas its headline rate uses `completion_tokens`. The draft does not mix those numerators or treat aggregate throughput as one stream's speed. [S2][S3][S7]

No controlled speedup ratio follows from these rows. The runs differ in duration and source-described configuration. Most of the offered 5,000 units were not run. [S2][S3][S4]

## Exact tok/s needs a stronger source record

The saved serial probe's producer uses provider `completion_tokens` when present, but falls back to `characters // 4`. Its rows do not identify which path supplied a count. It also times the first content or reasoning delta, so its TTFT is not the same event as Hermes's first visible text. We therefore withhold its decode rates from an exact tok/s comparison. [S6]

The swarm producer revision was not recovered in this execution. Until its counter implementation or original provider-usage receipts establish that the saved counts contain no estimates, the parallel rates above remain source-recorded and unsuitable for the requested exact-measurement publication. File hashes preserve what was read. They do not establish how tokens were counted. [S8]

## What this draft does not claim

There is no new live benchmark, no simulated capacity estimate, no independently graded answer-quality comparison, and no evidence that the same routes remain available now. The source scripts are not pinned to their execution-time Git revisions. No post URL has been verified, and nothing from this draft has been published. The remaining publication gates are counter provenance, execution-time source revision evidence, and permission to publish. [S8]

## Sources

Paths below are local evidence, not public URLs. The frozen projection strips generated text, error bodies, and organization identifiers. It is deliberately outside `posts/` and `studies/` so existing site generation cannot publish it accidentally. [S8]

- [S1] `/mnt/zer0models/workspace/zer0/data/operations/speed-profiles-20261105/lat-final.jsonl:1-13`.
- [S2] `/mnt/zer0models/workspace/zer0/data/operations/speed-profiles-20261105/swarm-bench/bench-20261105T033902.summary.json:1-24`, paired raw rows `bench-20261105T033902.jsonl:1-598` in the same directory.
- [S3] `/mnt/zer0models/workspace/zer0/data/operations/speed-profiles-20261105/swarm-bench/bench-20261105T040146.summary.json:1-18`, paired raw rows `bench-20261105T040146.jsonl:1-554`.
- [S4] `/mnt/zer0models/workspace/zer0/data/operations/speed-profiles-20261105/swarm-bench/bench-20261105T041047.summary.json:1-18`, paired raw rows `bench-20261105T041047.jsonl:1-401`.
- [S5] `/mnt/zer0models/workspace/zer0/data/operations/speed-profiles-20261105/hermes_latency.py:2-6,11,63-79,87-96`.
- [S6] `/mnt/zer0models/workspace/zer0/data/operations/speed-profiles-20261105/probe_all.py:43-70`.
- [S7] `/mnt/zer0models/workspace/zer0/data/operations/speed-profiles-20261105/README.md:23-41`.
- [S8] Execution evidence: `/mnt/zer0models/workspace/zer0/data/operations/intent-analyzer-20261104/ayo-runs/exec-RP06/REPORT.md`, `verify-fleet-complete.log`, and `PR-BODY.md`. The [checker](../../../scripts/rp06_measurements.py) and [tests](../../../tests/test_rp06_measurements.py) define the offline verification scope.

[S1]: /mnt/zer0models/workspace/zer0/data/operations/speed-profiles-20261105/lat-final.jsonl
[S2]: /mnt/zer0models/workspace/zer0/data/operations/speed-profiles-20261105/swarm-bench/bench-20261105T033902.summary.json
[S3]: /mnt/zer0models/workspace/zer0/data/operations/speed-profiles-20261105/swarm-bench/bench-20261105T040146.summary.json
[S4]: /mnt/zer0models/workspace/zer0/data/operations/speed-profiles-20261105/swarm-bench/bench-20261105T041047.summary.json
[S5]: /mnt/zer0models/workspace/zer0/data/operations/speed-profiles-20261105/hermes_latency.py
[S6]: /mnt/zer0models/workspace/zer0/data/operations/speed-profiles-20261105/probe_all.py
[S7]: /mnt/zer0models/workspace/zer0/data/operations/speed-profiles-20261105/README.md
[S8]: /mnt/zer0models/workspace/zer0/data/operations/intent-analyzer-20261104/ayo-runs/exec-RP06/REPORT.md
