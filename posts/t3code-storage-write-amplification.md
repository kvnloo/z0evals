---
title: "where a t3 code database's bytes and writes go"
subtitle: "seven experiments on one real 655 MiB database: what upstream's pruning already fixes, and the per-turn write amplification it leaves."
study: t3code-storage-write-amplification
status: draft
author: "zer0 research"
date: "november 3, 2026"
published: '2026-11-03'
area: research
kind: study
tags: [t3code, sqlite, storage]
featured: false
mock_data: false
toc:
  - id: summary
    label: the short version
  - id: setup
    label: what we measured
  - id: bytes
    label: where the bytes sit
  - id: fold
    label: our fold, and the pruning that supersedes it
  - id: writes
    label: where a turn's writes go
  - id: page-size
    label: the page size trade
  - id: group-commit
    label: a 25 ms group-commit window
  - id: provider-history
    label: what is left for provider-owned history
  - id: limits
    label: what this does not show
  - id: sources
    label: sources
---

<div class="lede">
we asked whether t3 code could stop storing transcripts that a provider can serve again. to answer it we accounted for every byte and every write in one real t3 code database. the answer for bytes is mostly no: the transcript is a small slice. upstream's new event pruning already removes the biggest waste we found. what it leaves is per-turn write amplification: about 52 small commits per turn, each rewriting the same hot pages.
</div>

## the short version {#summary}

- **upstream already fixed the biggest byte problem we found.** our experiment 02 folded superseded snapshot bodies in the event log and cut the file 20.1% after `VACUUM`. julius's [pr 29806](https://github.com/pingdotgg/t3code/pull/29806) goes further: projections become the source of truth once applied, and events older than about a day are pruned. [pr 29811](https://github.com/pingdotgg/t3code/pull/29811) returns the freed pages to the filesystem. our fold ran into the same two races that 29806 handles. we read that as independent confirmation of their design, not as a competing proposal.
- **the writes remain.** a simulated turn makes about 52 sqlite commits. at 4 KiB pages each commit writes about 29 wal frames, mostly the same hot pages. 83% of the sqlite bytes a turn writes are wal frames. a turn writes 7.1 MiB to add about a quarter of a MiB to the database.
- **a 25 ms group-commit window** cuts commits per turn by 43% and sqlite bytes per turn by 21%. we saw no latency regression beyond noise at n = 8 slots (16 turns) per arm, but the p95 tails are wide. a 150 ms window saves no more and adds 150 ms of event lag, so we rejected it.
- **page size is a trade, not a win.** 16 KiB pages shrink the file 14.7% and write 3.1× the bytes per turn. 8 KiB pages shrink it 8.4% for 1.67× the writes.
- **provider-owned history is a small byte lever.** tool output is 42.2 MiB of a 619 MiB file. evicting it saves 37.9 MiB (6.1%), and no provider can serve any of it back today. the case for provider-owned history is freshness: turns run in another client would show up in t3 code. it is not bytes.

## what we measured {#setup}

- **one database, one user.** a `VACUUM INTO` copy of one real t3 code database (654.6 MiB after the measured build's migrations, 232 live threads). every run used a copy; the live install was never opened read-write.
- **simulated turns.** turns are the repo's `devReplay` acp agent, which drives the real adapter, orchestration, projections and checkpoints. they are not live provider turns, and real codex, claude or acp turns write a different mix of items.
- **one fork, one branch per experiment.** all code is on [kvnloo/t3code](https://github.com/kvnloo/t3code) under `exp/poh/*`, pinned in [sources](#sources). every change sits behind an opt-in flag, and every a/b runs both arms at the same sha.
- **bytes and counts are the primary evidence.** they are deterministic for a given database and sha. latency ran on a shared, memory-tight host and is noisy. the latency results say "no regression beyond noise", which is weaker than "no regression".
- **1,599 receipt rows** (one per metric per run) back the tables below. the study's [data](https://github.com/kvnloo/z0evals/tree/main/studies/t3code-storage-write-amplification/data) holds the aggregates; no thread ids, titles or message text left the machine.

## where the bytes sit {#bytes}

experiment 01 classified every page of the database: payload by event type and json key, plus indexes and unused space from `dbstat`. it then simulated three eviction policies on copies of the post-doctor database and vacuumed each one.

<figure class="figure">
<!-- figure:bytes-by-class -->
<svg class="chart-svg" viewBox="0 0 420 242" role="img" aria-label="durable bytes by class for five database states"><rect x="96.0" y="8" width="8.9" height="22" fill="#98cf8b"><title>text (messages, reasoning, tool input): 18.6 MiB</title></rect><rect x="104.9" y="8" width="20.2" height="22" fill="#7fb2d9"><title>tool output: 42.2 MiB</title></rect><rect x="125.2" y="8" width="40.9" height="22" fill="#e37f65"><title>superseded snapshot bodies: 85.3 MiB</title></rect><rect x="166.1" y="8" width="7.0" height="22" fill="#c9a0dc"><title>t3-owned state: 14.6 MiB</title></rect><rect x="173.1" y="8" width="114.8" height="22" fill="#d7b986"><title>ids and metadata: 239.4 MiB</title></rect><rect x="287.9" y="8" width="58.7" height="22" fill="#8a8577"><title>indexes (incl. search): 122.3 MiB</title></rect><rect x="346.6" y="8" width="63.4" height="22" fill="#4a4740"><title>page slack: 132.2 MiB</title></rect><text x="0" y="17" font-size="10" fill="#ECE8DF">base · 655 MiB</text><text x="0" y="28" font-size="8.5" fill="#B4AFA3">after migrations</text><rect x="96.0" y="42" width="8.9" height="22" fill="#98cf8b"><title>text (messages, reasoning, tool input): 18.6 MiB</title></rect><rect x="104.9" y="42" width="20.2" height="22" fill="#7fb2d9"><title>tool output: 42.2 MiB</title></rect><rect x="125.2" y="42" width="29.1" height="22" fill="#e37f65"><title>superseded snapshot bodies: 60.6 MiB</title></rect><rect x="154.2" y="42" width="7.0" height="22" fill="#c9a0dc"><title>t3-owned state: 14.5 MiB</title></rect><rect x="161.2" y="42" width="112.7" height="22" fill="#d7b986"><title>ids and metadata: 235.0 MiB</title></rect><rect x="273.9" y="42" width="57.0" height="22" fill="#8a8577"><title>indexes (incl. search): 118.8 MiB</title></rect><rect x="330.9" y="42" width="61.7" height="22" fill="#4a4740"><title>page slack: 128.6 MiB</title></rect><text x="0" y="51" font-size="10" fill="#ECE8DF">doctor · 619 MiB</text><text x="0" y="62" font-size="8.5" fill="#B4AFA3">t3 doctor --fix</text><rect x="96.0" y="76" width="8.9" height="22" fill="#98cf8b"><title>text (messages, reasoning, tool input): 18.6 MiB</title></rect><rect x="104.9" y="76" width="20.2" height="22" fill="#7fb2d9"><title>tool output: 42.2 MiB</title></rect><rect x="125.2" y="76" width="8.6" height="22" fill="#e37f65"><title>superseded snapshot bodies: 18.0 MiB</title></rect><rect x="133.8" y="76" width="7.0" height="22" fill="#c9a0dc"><title>t3-owned state: 14.5 MiB</title></rect><rect x="140.8" y="76" width="112.6" height="22" fill="#d7b986"><title>ids and metadata: 234.7 MiB</title></rect><rect x="253.3" y="76" width="57.0" height="22" fill="#8a8577"><title>indexes (incl. search): 118.8 MiB</title></rect><rect x="310.3" y="76" width="50.9" height="22" fill="#4a4740"><title>page slack: 106.2 MiB</title></rect><text x="0" y="85" font-size="10" fill="#ECE8DF">D · 554 MiB</text><text x="0" y="96" font-size="8.5" fill="#B4AFA3">drop superseded</text><rect x="96.0" y="110" width="8.9" height="22" fill="#98cf8b"><title>text (messages, reasoning, tool input): 18.6 MiB</title></rect><rect x="104.9" y="110" width="1.3" height="22" fill="#7fb2d9"><title>tool output: 2.8 MiB</title></rect><rect x="106.3" y="110" width="8.6" height="22" fill="#e37f65"><title>superseded snapshot bodies: 18.0 MiB</title></rect><rect x="114.9" y="110" width="7.0" height="22" fill="#c9a0dc"><title>t3-owned state: 14.5 MiB</title></rect><rect x="121.9" y="110" width="112.6" height="22" fill="#d7b986"><title>ids and metadata: 234.7 MiB</title></rect><rect x="234.4" y="110" width="57.0" height="22" fill="#8a8577"><title>indexes (incl. search): 118.8 MiB</title></rect><rect x="291.4" y="110" width="51.7" height="22" fill="#4a4740"><title>page slack: 107.8 MiB</title></rect><text x="0" y="119" font-size="10" fill="#ECE8DF">A · 516 MiB</text><text x="0" y="130" font-size="8.5" fill="#B4AFA3">evict tool output</text><rect x="96.0" y="144" width="8.6" height="22" fill="#e37f65"><title>superseded snapshot bodies: 18.0 MiB</title></rect><rect x="104.6" y="144" width="7.0" height="22" fill="#c9a0dc"><title>t3-owned state: 14.5 MiB</title></rect><rect x="111.6" y="144" width="94.9" height="22" fill="#d7b986"><title>ids and metadata: 197.9 MiB</title></rect><rect x="206.5" y="144" width="53.4" height="22" fill="#8a8577"><title>indexes (incl. search): 111.3 MiB</title></rect><rect x="259.9" y="144" width="33.9" height="22" fill="#4a4740"><title>page slack: 70.7 MiB</title></rect><text x="0" y="153" font-size="10" fill="#ECE8DF">B · 413 MiB</text><text x="0" y="164" font-size="8.5" fill="#B4AFA3">provider owns all</text><rect x="0" y="182" width="9" height="9" fill="#98cf8b"/><text x="13" y="190" font-size="9" fill="#B4AFA3">text (messages, reasoning, tool input)</text><rect x="212" y="182" width="9" height="9" fill="#7fb2d9"/><text x="225" y="190" font-size="9" fill="#B4AFA3">tool output</text><rect x="0" y="197" width="9" height="9" fill="#e37f65"/><text x="13" y="205" font-size="9" fill="#B4AFA3">superseded snapshot bodies</text><rect x="212" y="197" width="9" height="9" fill="#c9a0dc"/><text x="225" y="205" font-size="9" fill="#B4AFA3">t3-owned state</text><rect x="0" y="212" width="9" height="9" fill="#d7b986"/><text x="13" y="220" font-size="9" fill="#B4AFA3">ids and metadata</text><rect x="212" y="212" width="9" height="9" fill="#8a8577"/><text x="225" y="220" font-size="9" fill="#B4AFA3">indexes (incl. search)</text><rect x="0" y="227" width="9" height="9" fill="#4a4740"/><text x="13" y="235" font-size="9" fill="#B4AFA3">page slack</text></svg>
<!-- /figure:bytes-by-class -->
<figcaption><span class="fig-n">fig. 1</span>durable bytes by class for the database as migrated, after the shipped <code>t3 doctor --fix</code>, and under three simulated policies, each vacuumed. ids and metadata include record headers. source: <a href="https://github.com/kvnloo/z0evals/blob/main/studies/t3code-storage-write-amplification/data/bytes-by-class.json">bytes-by-class.json</a>.</figcaption>
</figure>

| state | file | vs doctor | per-thread p50 | per-thread max |
|---|---|---|---|---|
| after migrations | 654.6 MiB | +5.7% | 0.99 MiB | 43.6 MiB |
| `t3 doctor --fix` (shipped) | 619.1 MiB | | 0.95 MiB | 43.3 MiB |
| D: drop superseded snapshot bodies (no provider needed) | 553.7 MiB | −10.6% | 0.84 MiB | 37.4 MiB |
| A: D + evict tool output, keep all text | 515.8 MiB | −16.7% | 0.71 MiB | 33.9 MiB |
| B: provider owns every transcript byte | 413.0 MiB | −33.3% | 0.44 MiB | 27.9 MiB |

what the classes say:

- **text is small.** message text, reasoning and tool input together are 18.6 MiB, 3% of the file.
- **duplicates were the biggest waste.** after doctor, 60.6 MiB of superseded snapshot bodies remain: turn items and nodes re-sent with their full ids on every status change. doctor keeps the first and the latest row for each entity. dropping the rest (policy D) saves 65.4 MiB with no provider involved. that is about two thirds of policy A's 103.2 MiB.
- **even full provider ownership leaves two thirds of the file.** in policy B, ids and metadata, indexes and page slack make up 91% of the remaining 413 MiB. the event id alone averages 299 bytes and carries a 30.6 MiB unique index. ids cross the wire (streamed events, receipts, mcp output), so we did not shorten them.

## our fold, and the pruning that supersedes it {#fold}

experiment 02 built policy D for real, behind `T3CODE_EXPERIMENTAL_SNAPSHOT_FOLD`. for each settled entity it moved the newest body into the entity's first row and deleted the rest. it then went through two rounds of adversarial review.

| | without fold | with fold |
|---|---|---|
| events in the log | 97,784 | 65,406 |
| file after `VACUUM` | 617.6 MiB | 493.6 MiB (−20.1%) |
| file in place (`auto_vacuum` none) | 654.6 MiB | 654.6 MiB (no change; used space −100.4 MB) |
| projection tables equal after rebuild | | 18/18 |
| transactions / longest | | 575 / 49.8 ms |

the review found the races any log pruning has to handle:

1. **resume check vs replay read.** a client resumes from a cursor. the server checks the cursor, then reads the replay. a fold that commits between those two steps leaves the client with only the tail, so it misses the final body. the fix re-checks after the read. the same check is needed on the lazy live tail.
2. **a stale cursor needs a snapshot.** a cursor inside a folded range cannot be replayed; it has to load a snapshot. on the largest thread that is a 733 KiB snapshot instead of a 40 KiB replay, and the stale-reconnect p50 went from 8.8 ms to 118 ms. this cost is by design.

[pr 29806](https://github.com/pingdotgg/t3code/pull/29806) makes a stronger maintainer decision: once a projection has applied an event, nothing needs that event again. it prunes everything at or below a day-old mark, except each stream's newest event and a few rows that are always kept. a cursor below the pruned-through sequence loads a snapshot, which is the same fallback we arrived at. on a maintainer's 12.4 GB database, the first pass deletes 92% of events. [pr 29811](https://github.com/pingdotgg/t3code/pull/29811) handles the other thing we hit: on an `auto_vacuum` none database, freed pages are reused but never given back. it converts small databases to incremental on open and leaves large ones to `t3 doctor`.

so experiment 02 is superseded. the fold kept the full log shape; pruning drops it, and that is simpler and saves more. what our fold adds to the record is that two independent attempts landed on the same races and the same snapshot fallback. merged [pr 23211](https://github.com/pingdotgg/t3code/pull/23211) also dropped the unused correlation index. our `idx` arm below tested that index trim, and it showed no measurable per-turn effect.

## where a turn's writes go {#writes}

pruning fixes what the database holds. it does not change what a turn writes. experiment 03b preloaded a small shim that counts the server's write syscalls per file and parses wal frame headers. that gives exact per-turn counts, 10 tapped turns per arm:

| page size | commits | wal frames | frames per commit | distinct pages | wal | checkpoint copy-back | sqlite total |
|---|---|---|---|---|---|---|---|
| 4 KiB (today) | 52 | 1,524 | 29 | 297 | 5.99 MiB | 1.19 MiB | 7.1 MiB |
| 8 KiB | 52 | 1,288 | 25 | 224 | 10.09 MiB | 2.04 MiB | 11.8 MiB |
| 16 KiB | 52 | 1,171 | 23 | 187 | 18.21 MiB | 3.55 MiB | 21.9 MiB |

- **83% of a turn's sqlite bytes are wal frames** at 4 KiB. checkpoint copy-back is the other 17%.
- **each commit rewrites the same hot pages.** these are the right-edge leaf of `orchestration_events` and of each of its indexes (together 42.5% of frames), `sqlite_sequence`, the projection metadata row, the thread row and its `project_updated` index. each is one page, rewritten about 46 times per turn.
- **a turn writes about 29× what it adds.** at 4 KiB it writes 7.1 MiB to grow the database by about 242 KiB.
- **checkpoint tuning cannot fix this.** a smaller checkpoint threshold raises copy-back. a larger one bottoms out at 2.9 MiB of copy-back at 16 KiB, while the wal alone is 18.2 MiB. the lever is the number of commits.

## the page size trade {#page-size}

experiment 03 found that most of the "ids, metadata and indexes" overhead is page slack. at 4 KiB, a 1–3 KiB event row often sits alone on a leaf page. bigger pages pack rows better, but each commit then writes bigger frames:

| page size | file (doctor-compacted) | saved | sqlite writes per turn | vs 4 KiB |
|---|---|---|---|---|
| 4 KiB (today) | 618.8 MiB | | 7.1 MiB | |
| 8 KiB | 566.6 MiB | −8.4% | 11.8 MiB | 1.67× |
| 16 KiB | 527.9 MiB | −14.7% | 21.9 MiB | 3.1× |

wire bytes were identical in every arm, and no latency, rss or cpu metric moved beyond noise for 8 or 16 KiB at n = 10 boots per arm. the cost is ssd write volume. we would keep 8 KiB as an opt-in at most, and only after commit batching. 16 KiB becomes affordable only if turns commit far less often. the flag is `T3CODE_EXPERIMENTAL_PAGE_SIZE`; [design note](https://github.com/kvnloo/t3code/blob/3676fef04b58844605728973ea8c92b6de1236d1/docs/internals/sqlite-page-size.md).

the first page-size a/b measured `/proc` `write_bytes` and reported 2.1× at 16 KiB. on that host's filesystem, that counter had 16 MiB of round-to-round noise. the syscall tap above replaced it, and the tap's noise is under 0.7 MiB.

## a 25 ms group-commit window {#group-commit}

experiment 04 added `T3CODE_EXPERIMENTAL_COMMIT_WINDOW_MS`. provider events that arrive within the window share one commit. we ran four arms at the same sha, interleaved: `off`, `w25` (25 ms), `idx` (no flag, on a seed with the correlation index dropped and the command index partial), and `w150` (150 ms, pilot only). off, w25 and idx each got 8 slots (16 tapped turns). w150 got 2 slots (4 turns).

<figure class="figure">
<!-- figure:group-commit -->
<svg class="chart-svg" viewBox="0 0 420 192" role="img" aria-label="per-turn writes with and without a 25 ms group-commit window"><text x="0" y="13" font-size="10" fill="#ECE8DF">commits per turn</text><rect x="0" y="17" width="330" height="9" fill="#8a8577"/><text x="336" y="25" font-size="9" fill="#B4AFA3">off 51.5</text><rect x="0" y="28" width="189.0" height="9" fill="#d7b986"/><line x1="182.6" x2="195.4" y1="32.5" y2="32.5" stroke="#ECE8DF" stroke-width="1.2"/><text x="336" y="36" font-size="9" fill="#d7b986">25 ms 29.5</text><text x="0" y="57" font-size="10" fill="#ECE8DF">wal frames per turn</text><rect x="0" y="61" width="330" height="9" fill="#8a8577"/><text x="336" y="69" font-size="9" fill="#B4AFA3">off 1580</text><rect x="0" y="72" width="252.2" height="9" fill="#d7b986"/><line x1="233.7" x2="280.7" y1="76.5" y2="76.5" stroke="#ECE8DF" stroke-width="1.2"/><text x="336" y="80" font-size="9" fill="#d7b986">25 ms 1207</text><text x="0" y="101" font-size="10" fill="#ECE8DF">sqlite MiB per turn</text><rect x="0" y="105" width="330" height="9" fill="#8a8577"/><text x="336" y="113" font-size="9" fill="#B4AFA3">off 7.79</text><rect x="0" y="116" width="261.4" height="9" fill="#d7b986"/><line x1="207.2" x2="309.2" y1="120.5" y2="120.5" stroke="#ECE8DF" stroke-width="1.2"/><text x="336" y="124" font-size="9" fill="#d7b986">25 ms 6.17</text><text x="0" y="145" font-size="10" fill="#ECE8DF">live ws frames per turn</text><rect x="0" y="149" width="330" height="9" fill="#8a8577"/><text x="336" y="157" font-size="9" fill="#B4AFA3">off 25</text><rect x="0" y="160" width="290.4" height="9" fill="#d7b986"/><line x1="277.2" x2="303.6" y1="164.5" y2="164.5" stroke="#ECE8DF" stroke-width="1.2"/><text x="336" y="168" font-size="9" fill="#d7b986">25 ms 22</text><text x="0" y="186" font-size="8.5" fill="#B4AFA3">bars are p50 per tapped turn (n = 16 per arm), scaled to off; whisker = bootstrap 95% ci of the shift</text></svg>
<!-- /figure:group-commit -->
<figcaption><span class="fig-n">fig. 2</span>per-turn writes, off vs a 25 ms window. this harness runs 2 tapped turns per boot with no warm phase, so its off baseline (7.79 MiB) differs from the page-size runs (7.1 MiB); compare arms only within one a/b. source: <a href="https://github.com/kvnloo/z0evals/blob/main/studies/t3code-storage-write-amplification/data/group-commit-ab.json">group-commit-ab.json</a>.</figcaption>
</figure>

the median shift vs off, with a bootstrap 95% interval:

| metric | off p50 / p95 | Δ 25 ms | Δ idx | Δ 150 ms |
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
| turn wall (ms) | 5710 / 7260 | −64 [−345, +338] | −90 [−376, +154] | −173 [−407, +618] |
| peak rss (MiB) | 534 / 570 | +24 [−5, +41] | 0 [−14, +24] | −9 [−21, +6] |
| server cpu per turn (s) | 1.10 / 1.81 | −0.27 [−0.67, +0.45] | −0.26 [−0.59, +0.33] | −0.33 [−0.74, +0.59] |
| reconnect replay wire (KiB) | 110 / 112 | 0 [−3, +3] | 0 [−3, +3] | 0 [−3, +3] |

how we read it:

- **25 ms cuts commits by 43%, wal frames by 24% and sqlite bytes by 21%.** reconnect wire bytes do not change.
- **no user-facing latency metric regressed beyond noise.** every interval for first live event, first assistant delta, turn wall, cpu and peak rss includes zero. event lag p50 moves +15.5 ms, and its upper bound (+20 ms) stays under the 25 ms window that caps it by design.
- **the one real shift is expected.** the window merges ws frames, so each turn sends 3 fewer, and the frame gap grows 27.5 ms. assistant text keeps the same cadence.
- **the p95 tails are wide.** the event lag p95 interval spans about ±130 ms. this rules out a p50 regression, not small tail effects.
- **150 ms saves nothing more and adds 150 ms of lag.** that also shows the latency metrics catch a real delay.
- **the index trim has no measurable per-turn effect** at 16 turns. upstream has since merged it for its own reasons ([pr 23211](https://github.com/pingdotgg/t3code/pull/23211)); our data neither argues for nor against it.

## what is left for provider-owned history {#provider-history}

once [pr 29806](https://github.com/pingdotgg/t3code/pull/29806) prunes the log, most of what stays is the projections plus the ids, indexes and page slack around them. the transcript part that a provider could own is small:

- **tool output** is 42.2 MiB of the 619 MiB post-doctor file. evicting it and leaving tombstones saves 37.9 MiB (6.1%).
- **none of it can be re-served today.** no production code calls an adapter's `readThreadSnapshot`. after adapter work, the acp hermes agent (26.7 MiB here) and codex (3.2 MiB) could serve tool results back, at most 71% of the total. the other acp agents in this database (12.2 MiB) have no verified re-serve path.
- **so the argument for provider-owned history is freshness, not bytes.** a user who drives the same session from another client should see those turns on the next open. that is a correctness and drift question, and it needs its own experiment.

what we would bring upstream, in a [new discussion with fresh numbers](DISCUSSION_URL): commit batching per turn, the page-size trade once batching lands, and the freshness case for provider history.

## what this does not show {#limits}

- **one database, one user.** in this database the hermes acp agent owns 63% of tool output. codex- or claude-heavy users will have a different mix. the accounting script reruns on any seed.
- **simulated turns, not live provider turns.** `devReplay` drives the real server paths, but real providers stream different item mixes and timings.
- **n per arm is small.** page size: 10 boots and 10 tapped turns per arm. group commit: 8 slots (16 turns) for off, 25 ms and idx, 2 slots (4 turns) for 150 ms. the host was memory-tight and shared.
- **the fold's in-pass latency was never measured.** the host's memory-pressure guard stopped every bench server before the fold window. the only bound is the longest fold transaction, 49.8 ms.
- **the tap counts write syscalls, not device writes.** filesystem copy-on-write, compression and journaling sit below it and add to every arm.
- **no client-side cost.** browser, desktop and mobile decode and render times were out of scope. wire bytes were identical in every arm, so clients receive the same data.

## sources {#sources}

fork branches on [kvnloo/t3code](https://github.com/kvnloo/t3code), each pinned to the sha the results came from:

| experiment | branch @ sha |
|---|---|
| 00 baseline harness | [`exp/poh/00-baseline` @ 258d7a4e](https://github.com/kvnloo/t3code/tree/258d7a4edc571b0b3aa6d99b81f7dc38bf670dab) |
| 01 byte accounting | [`exp/poh/01-byte-accounting` @ e17f68ce](https://github.com/kvnloo/t3code/tree/e17f68cebb45c95a7d11461b3a3550b3a4d7cbfb) |
| 02 snapshot fold | [`exp/poh/02-snapshot-dedupe` @ e3155fc4](https://github.com/kvnloo/t3code/tree/e3155fc400fce4536f9ad9ec05e881a5adeb144e) |
| 02b rebuild divergence | [`exp/poh/02b-rebuild-divergence` @ 3b263def](https://github.com/kvnloo/t3code/tree/3b263defba036730160a3f2451b84bfd26c3dd4b) |
| 03 ids, indexes, page size | [`exp/poh/03-id-index` @ 93e43918](https://github.com/kvnloo/t3code/tree/93e439187bec68d9229c3c486bc1517e38679bb9) |
| 03b page-size writes | [`exp/poh/03b-page-writes` @ 3676fef0](https://github.com/kvnloo/t3code/tree/3676fef04b58844605728973ea8c92b6de1236d1) |
| 04 commit batching | [`exp/poh/04-commit-batching` @ ea608f37](https://github.com/kvnloo/t3code/tree/ea608f3764b00090e12a10543d3739104a2e2623) |

upstream: [pr 29806](https://github.com/pingdotgg/t3code/pull/29806) (prune events the projections cover), [pr 29811](https://github.com/pingdotgg/t3code/pull/29811) (return freed pages), [pr 23211](https://github.com/pingdotgg/t3code/pull/23211) (drop the unused correlation index, merged), [discussion 6897](https://github.com/pingdotgg/t3code/discussions/6897) (retention and compaction, closed) and [discussion 15122](https://github.com/pingdotgg/t3code/discussions/15122) (archive compression). our new discussion: [DISCUSSION_URL](DISCUSSION_URL).

study files: [manifest](https://github.com/kvnloo/z0evals/blob/main/studies/t3code-storage-write-amplification/manifest.yaml), [readme](https://github.com/kvnloo/z0evals/blob/main/studies/t3code-storage-write-amplification/README.md), [data](https://github.com/kvnloo/z0evals/tree/main/studies/t3code-storage-write-amplification/data), [scripts](https://github.com/kvnloo/z0evals/tree/main/studies/t3code-storage-write-amplification/scripts).
