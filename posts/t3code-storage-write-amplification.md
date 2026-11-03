---
title: "a 25 ms commit window for t3 code: 43% fewer sqlite commits per turn"
subtitle: "t3 code commits once per streamed event. grouping plain provider updates for up to 25 ms cut commits per simulated turn by 43%, and a replay of 2 hours of live traffic estimates 41% fewer."
study: t3code-storage-write-amplification
status: draft
author: "zer0 research"
date: "november 3, 2026"
published: '2026-11-03'
area: hermes
kind: study
tags: [t3code, sqlite, storage]
featured: false
mock_data: false
toc:
  - id: summary
    label: the short version
  - id: problem
    label: one commit per event
  - id: change
    label: the change
  - id: group-commit
    label: a/b on simulated turns
  - id: live
    label: live-traffic estimate
  - id: page-size
    label: the page size trade
  - id: background
    label: "background: where the bytes sit"
  - id: limits
    label: what this does not show
  - id: sources
    label: sources
---

<div class="stat-strip" markdown="0">
<div class="stat"><span>commits per turn</span><b>−43%</b><small>51.5 → 29.5, simulated a/b</small></div>
<div class="stat"><span>sqlite bytes per turn</span><b>−21%</b><small>7.79 → 6.17 MiB</small></div>
<div class="stat"><span>live traffic, estimated</span><b>−41%</b><small>commits, replay of 9,292 real events</small></div>
<div class="stat"><span>event lag p50</span><b>+15.5 ms</b><small>[−14, +20], within noise</small></div>
</div>

<div class="callout" markdown="1">
<div class="callout-title">where this stands</div>

we asked the t3 code maintainers whether they want this, opt-in or on by default, in [discussion 29954](https://github.com/pingdotgg/t3code/discussions/29954). if you run t3 code, you can check what it would do for your own traffic with a read-only [script](https://github.com/kvnloo/t3code/blob/45f2edca913aaa03b68ff1c5c8c2a72c78d5ae45/bench/poh/commit_window_estimate.py):

```
python3 commit_window_estimate.py \
  ~/.t3/userdata/statev2.sqlite 2
```

numbers from busy installs are the most useful thing to post there.
</div>

## the short version {#summary}

- **the problem:** the t3 code server commits to sqlite once per streamed event, and each commit rewrites about 29 pages. it is tracked upstream in [issue 24003](https://github.com/pingdotgg/t3code/issues/24003). [pr 24145](https://github.com/pingdotgg/t3code/pull/24145) batched queued snapshots and was closed under the one-problem rule; its reviewer, @simasrazinskas, found live events rarely queue up and suggested grouping commits across threads instead.
- **what we built:** that suggestion, with a time window as the trigger. plain `node`, `message`, `turn-item` and `plan` updates wait up to 25 ms, then commit together. any other write commits the queue first, so order is unchanged.
- **what it costs:** a hard crash can lose up to one window of events that no client had seen yet. in a 4-turn pilot, a 150 ms window saved no more and added 150 ms of lag, so the window has to stay short.
- **how sure we are:** bytes and commit counts are deterministic. latency intervals are wide except event lag. the a/b used simulated turns; the live number is a replay estimate, not an a/b.

## one commit per event {#problem}

experiment 03b preloaded a small shim that counts the server's write syscalls per file and parses wal frame headers. the counts cover the server process only. turns are the repo's `devReplay` acp agent, driven through the real adapter, orchestration, projections and checkpoints. p50 (nearest rank) over 10 tapped turns, on a 618.8 MiB doctor-compacted seed derived from the 654.6 MiB database, at 4 KiB pages:

| per turn | 4 KiB pages |
|---|---|
| commits | 52 |
| wal frames | 1,524 (29 per commit, 297 distinct pages) |
| wal bytes | 5.99 MiB |
| checkpoint copy-back | 1.19 MiB |
| sqlite bytes written | 7.1 MiB, 83% of it wal frames |

- **commits keep rewriting the same pages.** the event table and its indexes account for 42.5% of frames. `sqlite_sequence`, the projection metadata row, the thread row and its `project_updated` index each sit on one page that is rewritten about 46 times per turn.
- **a turn writes about 29× what it adds** (median of the per-turn ratios): about 7.1 MiB written to grow the database by about 242 KiB.
- **checkpoint tuning cannot remove the main cost.** a smaller checkpoint threshold raises copy-back. a larger one lowers copy-back somewhat (modelled), but cannot touch the wal frames, which are paid on every commit. the lever is the number of commits.

## the change {#change}

fork branch [`exp/poh/04-commit-batching`](https://github.com/kvnloo/t3code/tree/ea608f3764b00090e12a10543d3739104a2e2623), based on upstream main `5b9731ce`. the feature is [one commit](https://github.com/kvnloo/t3code/commit/d443d211c9560267902c4f48ff5d95bd000cc39d) behind `T3CODE_EXPERIMENTAL_COMMIT_WINDOW_MS`, off by default.

- **one queue for all runs and threads.** a single `EventSink` queue holds the plain node, message, turn-item and plan updates from every run and thread. it commits as one transaction at most N ms after its first entry.
- **order is preserved.** any other `EventSink` write commits the queue first, so commit order and sequence order stay arrival order. an event whose normalization compares against a pending entity commits that entity first.
- **clients never see unstored events.** publication follows the commit.
- **graceful shutdown flushes the queue.**

the failure modes are the part we asked upstream about:

- **hard crash:** up to one window of events that were never published is lost.
- **batch write fails** (disk full, or a lock timeout that outlasts 2 retries): the error is logged, the window's events are dropped, and that thread's next deferred write fails with the cause. without the flag, the single write fails at its call site.

## a/b on simulated turns {#group-commit}

four arms. pilot slots 1–3 ran all four (a b c d / d c b a) at `fc7cfbeb`; slots 4–8 ran off, 25 ms and idx (a b c / c b a) at `be02c345`; the diff between the two touches only the pooling script, so the slots pool. each slot is one boot with 2 tapped turns.

- `off`: no flags. 8 slots, 16 turns.
- `w25`: 25 ms window. 8 slots, 16 turns.
- `idx`: no flags, on a seed with the correlation index dropped and the command index partial. 8 slots, 16 turns.
- `w150`: 150 ms window. pilot only: 2 slots, 4 turns.

<figure class="figure">
<!-- figure:group-commit -->
<svg class="chart-svg" viewBox="0 0 420 212" role="img" aria-label="per-turn writes with and without a 25 ms group-commit window"><text x="0" y="12" font-size="12" fill="#ECE8DF">commits per turn</text><rect x="0" y="17" width="300" height="12" fill="#8a8577"/><text x="308" y="27" font-size="11" fill="#B4AFA3">off 51.5</text><rect x="0" y="31" width="171.8" height="12" fill="#d7b986"/><line x1="166.0" x2="177.7" y1="37" y2="37" stroke="#ECE8DF" stroke-width="1.5"/><text x="308" y="41" font-size="11" fill="#d7b986">25 ms 29.5</text><text x="0" y="67" font-size="12" fill="#ECE8DF">wal frames per turn</text><rect x="0" y="72" width="300" height="12" fill="#8a8577"/><text x="308" y="82" font-size="11" fill="#B4AFA3">off 1580</text><rect x="0" y="86" width="229.2" height="12" fill="#d7b986"/><line x1="212.4" x2="255.2" y1="92" y2="92" stroke="#ECE8DF" stroke-width="1.5"/><text x="308" y="96" font-size="11" fill="#d7b986">25 ms 1207</text><text x="0" y="122" font-size="12" fill="#ECE8DF">sqlite MiB per turn</text><rect x="0" y="127" width="300" height="12" fill="#8a8577"/><text x="308" y="137" font-size="11" fill="#B4AFA3">off 7.79</text><rect x="0" y="141" width="237.6" height="12" fill="#d7b986"/><line x1="188.3" x2="281.1" y1="147" y2="147" stroke="#ECE8DF" stroke-width="1.5"/><text x="308" y="151" font-size="11" fill="#d7b986">25 ms 6.17</text><text x="0" y="177" font-size="12" fill="#ECE8DF">live ws frames per turn</text><rect x="0" y="182" width="300" height="12" fill="#8a8577"/><text x="308" y="192" font-size="11" fill="#B4AFA3">off 25</text><rect x="0" y="196" width="264.0" height="12" fill="#d7b986"/><line x1="252.0" x2="276.0" y1="202" y2="202" stroke="#ECE8DF" stroke-width="1.5"/><text x="308" y="206" font-size="11" fill="#d7b986">25 ms 22</text></svg>
<!-- /figure:group-commit -->
<figcaption><span class="fig-n">fig. 1</span>per-turn writes, off vs a 25 ms window. bars are the p50 over 16 tapped turns per arm, scaled to off; the white whisker is the bootstrap 95% interval of the shift. this harness runs 2 tapped turns per boot with no warm phase, so its off baseline (7.79 MiB) differs from the 7.1 MiB above; compare arms only within one a/b. source: <a href="https://github.com/kvnloo/z0evals/blob/main/studies/t3code-storage-write-amplification/data/group-commit-ab.json">group-commit-ab.json</a>.</figcaption>
</figure>

<details class="more" markdown="1">
<summary>all 13 metrics: median shift vs off, with a bootstrap 95% interval</summary>

| metric | off p50 / p95 | Δ 25 ms | Δ idx | Δ 150 ms (pilot) |
|---|---|---|---|---|
| sqlite MiB per turn | 7.79 / 8.99 | **−1.62 [−2.90, −0.49]** | −0.76 [−1.90, +0.53] | −1.64 [−3.10, −0.47] |
| commits per turn | 51.5 / 52 | **−22 [−23, −21]** | 0 [−1, +1] | −22 [−23, −21] |
| wal frames per turn | 1580 / 1670 | **−372 [−461, −236]** | −110 [−203, +19] | −370 [−476, −240] |
| first live event (ms) | 68.5 / 398 | −18 [−67, +33] | −10 [−60, +36] | +4 [−57, +278] |
| first assistant delta (ms) | 802 / 1280 | −86 [−222, +145] | −91 [−228, +185] | +38 [−117, +402] |
| event lag p50 (ms) | 17 / 90 | +15.5 [−14, +20] | −1 [−32, +7] | **+150 [+118, +173]** |
| event lag p95 (ms) | 236 / 916 | +47 [−96, +160] | −40 [−180, +31] | −14 [−112, +456] |
| ws frame gap p50 (ms) | 220 / 240 | +27.5 [+17, +38] | +2.5 [−8, +17] | +8.5 [−18, +32] |
| assistant delta gap p50 (ms) | 427 / 492 | −3.5 [−15, +1.5] | −2 [−13, +7.5] | +21 [+9.5, +32] |
| turn wall (ms) | 5710 / 7260 | −64 [−345, +338] | −89.5 [−376, +154] | −173 [−407, +618] |
| peak rss (MiB) | 534 / 570 | +24 [−5, +41] | 0 [−14, +24] | −9 [−21, +6] |
| server cpu per turn (s) | 1.10 / 1.81 | −0.27 [−0.67, +0.45] | −0.26 [−0.59, +0.33] | −0.33 [−0.74, +0.59] |
| reconnect replay wire (KiB) | 110 / 112 | 0 [−3, +3] | 0 [−3, +3] | 0 [−3, +3] |

</details>

how we read it:

- **25 ms cuts commits by 43%, wal frames by 24% and sqlite bytes by 21%.** reconnect replay wire bytes do not change.
- **event lag p50 is the only latency metric with a tight interval.** its median rises from 17 to 32.5 ms; the shift is +15.5 ms [−14, +20], below the 25 ms window that bounds the added wait by design. the other latency intervals (first live event, first assistant delta, turn wall, event lag p95) are wide. they rule out large regressions, not small ones.
- **the window merges ws frames.** each turn sends 3 fewer, and the frame gap grows by 27.5 ms. assistant text keeps the same cadence.
- **150 ms saves no more and adds 150 ms of event lag** in the 4-turn pilot, so the window has to stay short. it also shows the latency metrics catch a real delay.
- **the index trim had no measurable per-turn effect** at 16 turns. upstream has since merged one part of it, the correlation-index removal ([pr 23211](https://github.com/pingdotgg/t3code/pull/23211)); the a/b's seeds predate that.

## live-traffic estimate {#live}

the simulated turns are one agent on one thread. to see what the rule does on real traffic, the [estimator](https://github.com/kvnloo/t3code/blob/45f2edca913aaa03b68ff1c5c8c2a72c78d5ae45/bench/poh/commit_window_estimate.py) replays `orchestration_events` in sequence order, read-only, using the ingestion timestamps (`occurred_at`). it counts commits under the same window rule. the baseline is one commit per event.

one install, 2026-11-03 03:30–05:28 utc, 9,292 events across 21 threads, mostly the hermes acp agent with delegated subagents:

| window | commits | fewer than one per event |
|---|---|---|
| 10 ms | 6,109 | 34.3% |
| 25 ms | 5,471 | 41.1% |
| 50 ms | 5,051 | 45.6% |

this is an estimate. it assumes one commit per event, treats ingestion time as commit time, and does not model the extra flushes forced when a pending entity is compared against. we transcribed these numbers from the [posted discussion](https://github.com/pingdotgg/t3code/discussions/29954); the source database keeps changing, so we did not re-run them for this study ([data](https://github.com/kvnloo/z0evals/blob/main/studies/t3code-storage-write-amplification/data/live-window-estimate.json)).

## the page size trade {#page-size}

the same tap measured bigger pages. they pack the event rows better, but each commit then writes bigger frames:

| page size | file (doctor-compacted) | saved | sqlite writes per turn | vs 4 KiB |
|---|---|---|---|---|
| 4 KiB (default) | 618.8 MiB | | 7.1 MiB | |
| 8 KiB | 566.6 MiB | −8.4% | 11.8 MiB | 1.67× |
| 16 KiB | 527.9 MiB | −14.7% | 21.9 MiB | 3.1× |

wire bytes were identical, and no latency, rss or cpu metric moved beyond noise at n = 10 boots per arm. the cost is ssd write volume, so page size only becomes worth it once turns commit far less often. an earlier a/b measured `/proc` `write_bytes` and reported 2.1× at 16 KiB. on that host's filesystem that counter had 16 MiB of round-to-round noise, so the syscall tap replaced it (noise under 0.7 MiB). flag: `T3CODE_EXPERIMENTAL_PAGE_SIZE`; [design note](https://github.com/kvnloo/t3code/blob/3676fef04b58844605728973ea8c92b6de1236d1/docs/internals/sqlite-page-size.md).

## background: where the bytes sit {#background}

we started from a different question: could the provider own the transcript, with t3 code keeping only a cache? byte accounting on the same 654.6 MiB database said that is the small lever.

<figure class="figure">
<!-- figure:bytes-by-class -->
<svg class="chart-svg" viewBox="0 0 420 348" role="img" aria-label="durable bytes by class for five database states"><text x="0" y="12" font-size="12" fill="#ECE8DF">base · 655 MiB <tspan fill="#B4AFA3" font-size="11">after migrations</tspan></text><rect x="0.0" y="17" width="11.9" height="18" fill="#98cf8b"><title>text (messages, reasoning, tool input): 18.6 MiB</title></rect><rect x="11.9" y="17" width="27.1" height="18" fill="#7fb2d9"><title>tool output: 42.2 MiB</title></rect><rect x="39.0" y="17" width="54.7" height="18" fill="#e37f65"><title>superseded snapshot bodies: 85.3 MiB</title></rect><rect x="93.7" y="17" width="9.4" height="18" fill="#c9a0dc"><title>t3-owned state: 14.6 MiB</title></rect><rect x="103.1" y="17" width="153.6" height="18" fill="#d7b986"><title>ids and metadata: 239.4 MiB</title></rect><rect x="256.7" y="17" width="78.5" height="18" fill="#8a8577"><title>indexes (incl. search): 122.3 MiB</title></rect><rect x="335.2" y="17" width="84.8" height="18" fill="#4a4740"><title>page slack: 132.2 MiB</title></rect><text x="0" y="57" font-size="12" fill="#ECE8DF">doctor · 619 MiB <tspan fill="#B4AFA3" font-size="11">t3 doctor --fix</tspan></text><rect x="0.0" y="62" width="11.9" height="18" fill="#98cf8b"><title>text (messages, reasoning, tool input): 18.6 MiB</title></rect><rect x="11.9" y="62" width="27.1" height="18" fill="#7fb2d9"><title>tool output: 42.2 MiB</title></rect><rect x="39.0" y="62" width="38.9" height="18" fill="#e37f65"><title>superseded snapshot bodies: 60.6 MiB</title></rect><rect x="77.9" y="62" width="9.3" height="18" fill="#c9a0dc"><title>t3-owned state: 14.5 MiB</title></rect><rect x="87.2" y="62" width="150.8" height="18" fill="#d7b986"><title>ids and metadata: 235.0 MiB</title></rect><rect x="238.0" y="62" width="76.2" height="18" fill="#8a8577"><title>indexes (incl. search): 118.8 MiB</title></rect><rect x="314.2" y="62" width="82.5" height="18" fill="#4a4740"><title>page slack: 128.6 MiB</title></rect><text x="0" y="102" font-size="12" fill="#ECE8DF">D · 554 MiB <tspan fill="#B4AFA3" font-size="11">drop superseded</tspan></text><rect x="0.0" y="107" width="11.9" height="18" fill="#98cf8b"><title>text (messages, reasoning, tool input): 18.6 MiB</title></rect><rect x="11.9" y="107" width="27.1" height="18" fill="#7fb2d9"><title>tool output: 42.2 MiB</title></rect><rect x="39.0" y="107" width="11.5" height="18" fill="#e37f65"><title>superseded snapshot bodies: 18.0 MiB</title></rect><rect x="50.6" y="107" width="9.3" height="18" fill="#c9a0dc"><title>t3-owned state: 14.5 MiB</title></rect><rect x="59.9" y="107" width="150.6" height="18" fill="#d7b986"><title>ids and metadata: 234.7 MiB</title></rect><rect x="210.4" y="107" width="76.2" height="18" fill="#8a8577"><title>indexes (incl. search): 118.8 MiB</title></rect><rect x="286.7" y="107" width="68.1" height="18" fill="#4a4740"><title>page slack: 106.2 MiB</title></rect><text x="0" y="147" font-size="12" fill="#ECE8DF">A · 516 MiB <tspan fill="#B4AFA3" font-size="11">evict tool output</tspan></text><rect x="0.0" y="152" width="11.9" height="18" fill="#98cf8b"><title>text (messages, reasoning, tool input): 18.6 MiB</title></rect><rect x="11.9" y="152" width="1.8" height="18" fill="#7fb2d9"><title>tool output: 2.8 MiB</title></rect><rect x="13.7" y="152" width="11.5" height="18" fill="#e37f65"><title>superseded snapshot bodies: 18.0 MiB</title></rect><rect x="25.3" y="152" width="9.3" height="18" fill="#c9a0dc"><title>t3-owned state: 14.5 MiB</title></rect><rect x="34.6" y="152" width="150.6" height="18" fill="#d7b986"><title>ids and metadata: 234.7 MiB</title></rect><rect x="185.2" y="152" width="76.2" height="18" fill="#8a8577"><title>indexes (incl. search): 118.8 MiB</title></rect><rect x="261.4" y="152" width="69.2" height="18" fill="#4a4740"><title>page slack: 107.8 MiB</title></rect><text x="0" y="192" font-size="12" fill="#ECE8DF">B · 413 MiB <tspan fill="#B4AFA3" font-size="11">provider owns all</tspan></text><rect x="0.0" y="197" width="11.5" height="18" fill="#e37f65"><title>superseded snapshot bodies: 18.0 MiB</title></rect><rect x="11.5" y="197" width="9.3" height="18" fill="#c9a0dc"><title>t3-owned state: 14.5 MiB</title></rect><rect x="20.9" y="197" width="127.0" height="18" fill="#d7b986"><title>ids and metadata: 197.9 MiB</title></rect><rect x="147.8" y="197" width="71.4" height="18" fill="#8a8577"><title>indexes (incl. search): 111.3 MiB</title></rect><rect x="219.2" y="197" width="45.4" height="18" fill="#4a4740"><title>page slack: 70.7 MiB</title></rect><rect x="0" y="229" width="11" height="11" fill="#98cf8b"/><text x="17" y="239" font-size="11.5" fill="#B4AFA3">text (messages, reasoning, tool input)</text><rect x="0" y="246" width="11" height="11" fill="#7fb2d9"/><text x="17" y="256" font-size="11.5" fill="#B4AFA3">tool output</text><rect x="0" y="263" width="11" height="11" fill="#e37f65"/><text x="17" y="273" font-size="11.5" fill="#B4AFA3">superseded snapshot bodies</text><rect x="0" y="280" width="11" height="11" fill="#c9a0dc"/><text x="17" y="290" font-size="11.5" fill="#B4AFA3">t3-owned state</text><rect x="0" y="297" width="11" height="11" fill="#d7b986"/><text x="17" y="307" font-size="11.5" fill="#B4AFA3">ids and metadata</text><rect x="0" y="314" width="11" height="11" fill="#8a8577"/><text x="17" y="324" font-size="11.5" fill="#B4AFA3">indexes (incl. search)</text><rect x="0" y="331" width="11" height="11" fill="#4a4740"/><text x="17" y="341" font-size="11.5" fill="#B4AFA3">page slack</text></svg>
<!-- /figure:bytes-by-class -->
<figcaption><span class="fig-n">fig. 2</span>durable bytes by class for the database as migrated, after the shipped <code>t3 doctor --fix</code>, and under three simulated policies, each vacuumed. D drops superseded snapshot bodies, A also evicts tool output, B lets the provider own every transcript byte. source: <a href="https://github.com/kvnloo/z0evals/blob/main/studies/t3code-storage-write-amplification/data/bytes-by-class.json">bytes-by-class.json</a>.</figcaption>
</figure>

- **text is 3% of the file.** messages, reasoning and tool input total 18.6 MiB.
- **tool output is 42.2 MiB (6.8% of the 619.1 MiB post-doctor file).** evicting it saves 37.9 MiB (6.1%), and no adapter can serve it back today. even full provider ownership (policy B) removes only a third. ids and metadata, indexes and page slack are 92% of what remains.
- **superseded snapshot bodies were the biggest waste.** we built a fold for them (experiment 02, flag `T3CODE_EXPERIMENTAL_SNAPSHOT_FOLD`): −20.1% after `VACUUM`, 18/18 projection tables equal after rebuild. its review found one race (resume check vs replay read) that [pr 29806](https://github.com/pingdotgg/t3code/pull/29806) also handles. both fall back to a snapshot for a cursor in removed history. the designs differ: our fold kept a per-thread watermark, while 29806 uses one global pruning boundary, with retention exceptions such as each stream's newest event.
- **29806 and 29811 are open prs.** [29806](https://github.com/pingdotgg/t3code/pull/29806) prunes events the projections already cover. [29811](https://github.com/pingdotgg/t3code/pull/29811) returns freed pages to the filesystem automatically for small existing databases (up to 128 MiB of live data); larger ones still need `t3 doctor`. if they land, they cover most event-log bytes, which is why we dropped the fold. on this database the event log is 408 of 654.6 MiB including indexes. pruning may change the pages each commit touches, so the per-commit cost should be re-measured on top of it.

the case for provider-owned history is freshness: turns run in another client would show up on the next open. it is not bytes.

## what this does not show {#limits}

- **one install, one user, linux, under memory pressure.** bytes and commit counts are deterministic. latency intervals are wide except event lag.
- **simulated turns.** the a/b used `devReplay` turns, not live provider turns. the live number is a replay estimate, not a measured a/b.
- **small n.** 16 tapped turns per arm for off, 25 ms and idx; the 150 ms arm is a 4-turn pilot. page size: 10 tapped turns per arm.
- **different bases.** each experiment was cut from the upstream main of its day (listed in [sources](#sources)); none of these numbers describe a later main.
- **only the sqlite share.** the tap counts the server's write syscalls, not device writes. issue 24003's macos data shows the per-commit cost explains only part of the disk writes there.
- **the fold's in-pass latency was never measured.** host memory pressure stopped every bench server before the fold window; the only bound is the longest fold transaction, 49.8 ms.

## sources {#sources}

fork branches on [kvnloo/t3code](https://github.com/kvnloo/t3code), each pinned to the sha the results came from, with the upstream main it was cut from:

| experiment | branch @ sha | upstream base |
|---|---|---|
| 00 baseline harness | [`exp/poh/00-baseline` @ 258d7a4e](https://github.com/kvnloo/t3code/tree/258d7a4edc571b0b3aa6d99b81f7dc38bf670dab) | `9bcf7533` |
| 01 byte accounting | [`exp/poh/01-byte-accounting` @ e17f68ce](https://github.com/kvnloo/t3code/tree/e17f68cebb45c95a7d11461b3a3550b3a4d7cbfb) | `84537c4d` |
| 02 snapshot fold | [`exp/poh/02-snapshot-dedupe` @ e3155fc4](https://github.com/kvnloo/t3code/tree/e3155fc400fce4536f9ad9ec05e881a5adeb144e) | `6f413648` |
| 02b rebuild divergence | [`exp/poh/02b-rebuild-divergence` @ 3b263def](https://github.com/kvnloo/t3code/tree/3b263defba036730160a3f2451b84bfd26c3dd4b) | `30b9c4a9` |
| 03 ids, indexes, page size | [`exp/poh/03-id-index` @ 93e43918](https://github.com/kvnloo/t3code/tree/93e439187bec68d9229c3c486bc1517e38679bb9) | `065a4335` |
| 03b page-size writes | [`exp/poh/03b-page-writes` @ 3676fef0](https://github.com/kvnloo/t3code/tree/3676fef04b58844605728973ea8c92b6de1236d1) | `065a4335` |
| 04 commit window (a/b code) | [`exp/poh/04-commit-batching` @ ea608f37](https://github.com/kvnloo/t3code/tree/ea608f3764b00090e12a10543d3739104a2e2623) | `5b9731ce` |
| 04 live estimator | [`exp/poh/04-commit-batching` @ 45f2edca](https://github.com/kvnloo/t3code/tree/45f2edca913aaa03b68ff1c5c8c2a72c78d5ae45) | `5b9731ce` |

upstream: [discussion 29954](https://github.com/pingdotgg/t3code/discussions/29954) (our proposal), [issue 24003](https://github.com/pingdotgg/t3code/issues/24003) and [our comment there](https://github.com/pingdotgg/t3code/issues/24003#issuecomment-6596275747), [pr 24145](https://github.com/pingdotgg/t3code/pull/24145) (queued-snapshot batching, closed), [pr 29806](https://github.com/pingdotgg/t3code/pull/29806) and [pr 29811](https://github.com/pingdotgg/t3code/pull/29811) (pruning and page reclaim, open), [pr 23211](https://github.com/pingdotgg/t3code/pull/23211) (unused correlation index, merged), [discussion 6897](https://github.com/pingdotgg/t3code/discussions/6897) (retention and compaction, closed).

study files: [manifest](https://github.com/kvnloo/z0evals/blob/main/studies/t3code-storage-write-amplification/manifest.yaml), [readme](https://github.com/kvnloo/z0evals/blob/main/studies/t3code-storage-write-amplification/README.md), [data](https://github.com/kvnloo/z0evals/tree/main/studies/t3code-storage-write-amplification/data), [scripts](https://github.com/kvnloo/z0evals/tree/main/studies/t3code-storage-write-amplification/scripts).
