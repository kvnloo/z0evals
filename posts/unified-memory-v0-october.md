---
title: "the memory study, october update"
subtitle: "the real-source gate stayed closed, the handoff froze, and the replay caught a real error."
study: unified-memory-v0
status: evidence-pending
author: "zer0 research"
date: "october 23, 2026"
dek: "the real-source gate stayed closed, the handoff froze, and the replay caught a real error."
area: memory
published: 2026-10-23
series: memory
log: [unified-memory-v0]
toc:
  - id: source-gate
    label: the real-source gate stayed closed
  - id: handoff
    label: a frozen handoff is not a run
  - id: replay-repair
    label: the replay rejected a real error
  - id: limits
    label: what this does not prove
---

<div class="lede">
an update to <a href="../unified-memory-v0/">can four agents remember the same thing?</a>. the original cohort numbers are unchanged. this adds what happened after october 5.
</div>

## the real-source gate stayed closed {#source-gate}

we then tried to bind the same questions to authentic sources. the readiness record has 4 qualified source slots, 0 instantiated prompts, 0 model calls and 0 valid receipt rows. the contradiction pair is still unbound. the six real-source cases are **NOT RUN**.

the dsh runner reached the real assembly seam without calling a model. the source reports 66 python tests, 41 subtests and 1 bun test. those check the contract and capture machinery. they are not answers from the cohort. we did not turn a partial binding into a passing run.

source: [readiness record](https://github.com/kvnloo/z0evals/blob/667223e8a6e25064c1f21d2e6e3bd8ccc17190fd/studies/unified-memory-v0/READINESS.json) and [executable-source rules](https://github.com/kvnloo/z0evals/blob/667223e8a6e25064c1f21d2e6e3bd8ccc17190fd/studies/unified-memory-v0/README.md).

## a frozen handoff is not a run {#handoff}

the newer correction case freezes an agent-codified policy followed by a user correction. it does not establish an earlier user-to-user policy change. the pure-user variant remains blocked after a bounded history search, not disproved.

the plan separates capture, retrieval, exact-source verification, actual model input, use and independent checking. all six stages in both arms remain **NOT_RUN**. admission and model input remain **NOT_QUALIFIED**. the eight negative controls are also **NOT_RUN**. we keep the private policy details and native source identities out of this draft.

source: [frozen protocol](https://github.com/kvnloo/z0evals/blob/16b0b133df865d46b2b1a789f68936c189d88f41/studies/unified-memory-v0/fleet-mbp-thermal.protocol.md) and [unfilled stage receipts](https://github.com/kvnloo/z0evals/blob/16b0b133df865d46b2b1a789f68936c189d88f41/studies/unified-memory-v0/fleet-mbp-thermal.receipts.json).

## the replay rejected a real error {#replay-repair}

the offline audit reader did produce a narrower result. fixture tests passed, but an independently executed synthetic-source producer path emitted a legitimate byte-limit error that the reader rejected. the repair accepts that documented error without relabelling it as a miss.

the exact-head review reports 19 study tests passed: 11 replay tests and 8 adjacent case tests. the same public producer path then emitted two accepted rows: one hit, one error, zero misses. this is source-reported independent verification in the pr, not a rerun by us during this harvest.

retrieval counts still do not tell us whether the model used the result. no private audit log, real continuity gain or causal improvement was measured here.

source: [replay contract](https://github.com/kvnloo/z0evals/blob/16b0b133df865d46b2b1a789f68936c189d88f41/studies/unified-memory-v0/README.md), [replay implementation](https://github.com/kvnloo/z0evals/blob/16b0b133df865d46b2b1a789f68936c189d88f41/studies/unified-memory-v0/memory_query_replay.py), and the [exact-head verification](https://github.com/kvnloo/z0evals/pull/115#issuecomment-6375672214), for `16b0b133df865d46b2b1a789f68936c189d88f41`.

## what this does not prove {#limits}

one omp lane does not establish four-harness equivalence. smaller context does not prove better answers. we also do not need one universal memory database for this to work, and retrieved text is evidence, not automatically truth.

the actual goal is much less magical: same question, same evidence contract, different harness, same supported answer. once that is boring, memory starts looking like infrastructure.


original context-size table: [published baseline](https://github.com/kvnloo/z0evals/blob/ef97f8743ec115fec28238c7a4d4eea2c049158e/posts/unified-memory-v0.md). the new real-source evidence does not upgrade that table into four-harness equivalence.
