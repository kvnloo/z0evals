# t3code-storage-write-amplification

Where a T3 Code database's bytes and writes go: seven experiments on one real database, run on the fork [kvnloo/t3code](https://github.com/kvnloo/t3code) (`exp/poh/*` branches). The post is [`posts/t3code-storage-write-amplification.md`](../../posts/t3code-storage-write-amplification.md).

## Questions

1. Which byte classes make up a real T3 Code `state.sqlite`, and how much would each eviction policy save?
2. What does folding superseded snapshot bodies save, and how does that relate to upstream's event pruning (pingdotgg/t3code PR 29806 and PR 29811)?
3. Where do a turn's SQLite writes go, and does page size or a group-commit window change them?
4. How much is left for provider-owned history once the event log is pruned?

## Files

| path | what |
|---|---|
| `data/bytes-by-class.json` | experiment 01: bytes by class for five database states (base, doctor, policies D, A, B), per-thread p50/p90/max, bytes by provider family in the doctor DB |
| `data/snapshot-fold-seed.json` | experiment 02 round 3: seed run with and without the fold (event counts, file sizes in place and after VACUUM, transaction count and longest transaction, projection tables equal) |
| `data/page-size.json` | experiment 03b: per-turn tap medians (commits, WAL frames, distinct pages, WAL and copy-back bytes) per arm, the ledger's per-turn SQLite totals, and doctor-compacted file sizes per page size |
| `data/group-commit-ab.json` | experiment 04: pooled A/B (off, w25, idx, w150), p50/p95 per arm and median shift vs off with bootstrap 95% CI |
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
- Turns are simulated with the repo's `devReplay` ACP agent, not live provider turns.
- Small n: page size 10 boots and 10 tapped turns per arm; group commit 16 tapped turns per arm (4 for the 150 ms pilot). Latency ran on a shared, memory-tight host; bytes and counts are the primary evidence.
- The snapshot fold's in-pass turn latency was never measured; the bound is the longest fold transaction (49.8 ms).
- The write tap counts syscalls, not device writes.
- Client decode and render costs were not measured.
