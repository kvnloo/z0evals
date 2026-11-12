# t3code-storage-write-amplification

A 25 ms group-commit window for T3 Code, and the byte and write accounting behind it: experiments on one real database, run on the fork [kvnloo/t3code](https://github.com/kvnloo/t3code) (`exp/poh/*` branches). The post is [`posts/t3code-storage-write-amplification.md`](../../posts/t3code-storage-write-amplification.md).

## Questions

1. Where do a turn's SQLite writes go, and does a short group-commit window (the direction suggested in pingdotgg/t3code issue 24003) cut them without a latency regression?
2. What would the same window rule save on live traffic (replay estimate)?
3. What does page size trade between file size and writes per turn?
4. Background: which byte classes make up a real T3 Code `state.sqlite`, and how much is left for provider-owned history? (Event-log bytes are handled by the open upstream PRs 29806 and 29811.)

## Files

| path | what |
|---|---|
| `data/bytes-by-class.json` | experiment 01: bytes by class for five database states (base, doctor, policies D, A, B), per-thread p50/p90/max, bytes by provider family in the doctor DB |
| `data/snapshot-fold-seed.json` | experiment 02 round 3: seed run with and without the fold (event counts, file sizes in place and after VACUUM, transaction count and longest transaction, projection tables equal) |
| `data/page-size.json` | experiment 03b: per-turn tap medians (commits, WAL frames, distinct pages, WAL and copy-back bytes) per arm, the ledger's per-turn SQLite totals, and doctor-compacted file sizes per page size |
| `data/group-commit-ab.json` | experiment 04: pooled A/B (off, w25, idx, w150), p50/p95 per arm and median shift vs off with bootstrap 95% CI |
| `data/live-window-estimate.json` | live-traffic replay estimate (10/25/50 ms windows over 2 h, 9,292 events); source-reported, transcribed from pingdotgg/t3code discussion 29954, estimator pinned at kvnloo/t3code `45f2edca` |
| `data/ledger-summary.json` | receipt rows per experiment in the private ledger |
| `data/derived.json` | every number the post cites, computed from the files above |
| `figures/*.svg` | the two figures in the post |
| `scripts/import_aggregates.py` | the sanitizing import: reads an allowlist of raw experiment outputs and writes aggregates only |
| `scripts/figures.py` | computes `derived.json`, draws the figures and splices them into the post; `--check` fails if anything is stale |

## Reproduce

The aggregates were imported from the experiment outputs with:

```bash
python3 scripts/import_aggregates.py <experiment-ops-dir>
python3 scripts/figures.py
python3 scripts/figures.py --check
```

The raw outputs (per-run samples, server logs, the full ledger) are not published, because they contain thread ids, titles and local paths. To regenerate them on your own data, check out the fork branch for an experiment and follow its README under `bench/poh/`. Experiment 01 is `node bench/poh/accounting.ts prepare|analyze|report` on a `VACUUM INTO` copy of your database. Experiment 04 is `bench/poh/p04-run.sh` with `bench/poh/p04-ab.py` for pooling. Never point the harness at a live database.

## Sanitizing

`import_aggregates.py` writes only byte totals, counts, medians and intervals. It drops thread ids, titles, message text, file paths and host names. It folds provider instance names into provider families (`acp-hermes`, `acp-other`, `codex`, `claude`, ...) and refuses to run if it meets an unmapped instance.

## What it does not show

- One database from one user. The provider mix (Hermes ACP holds 63% of tool output here) will differ for other users.
- Turns are simulated with the repo's `devReplay` ACP agent, not live provider turns. The live-traffic number is a replay estimate (one commit per event assumed, ingestion time as commit time), not a measured A/B, and was not re-run for this study.
- Experiments were cut from different upstream main SHAs (9bcf7533, 84537c4d, 6f413648, 30b9c4a9, 065a4335, 5b9731ce); none describe a later main.
- Small n: page size 10 boots and 10 tapped turns per arm; group commit 16 tapped turns per arm (4 for the 150 ms pilot). Latency ran on a shared, memory-tight host; bytes and counts are the primary evidence, and only event lag has a tight interval.
- The snapshot fold's in-pass turn latency was never measured; the bound is the longest fold transaction (49.8 ms).
- The write tap counts syscalls, not device writes.
- Client decode and render costs were not measured.
