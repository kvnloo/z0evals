---
title: "can four agents remember the same thing?"
subtitle: "i got tired of every harness having its own half-broken version of memory."
study: unified-memory-v0
status: evidence-pending
author: "zer0 research"
date: "september 29, 2026"
mock_data: false
toc:
  - id: question
    label: memory is not one thing
  - id: architecture
    label: one evidence path
  - id: replay
    label: same questions everywhere
  - id: failures
    label: make it fail on purpose
  - id: results
    label: omp finally gave us a number
  - id: limits
    label: what this does not prove
---

<div class="lede">
can four different agent harnesses recover the same prior state without dumping the whole transcript back into the model every time?
</div>

<div class="hero-rule"></div>

## memory is not one thing {#question}

we kept saying “memory worked” when we meant four different things:

```text
retrieval -> model-visible injection -> answer support -> verification
```

configured is not retrieved. retrieved is not injected. injected is not supported. supported is not verified.

annoying distinction. also the whole point of the study.

## one evidence path, four harnesses {#architecture}

```text
conversation / file / git truth
          |
          v
agentsview / exact retrieval / other evidence capability
          |
          v
z0intelligence
evidenceref + minimal state
          |
    +-----+------+-----+
    |            |     |
   dsh         hermes  omo   omp
    |            |     |     |
    +----- comparable receipts +
```

the transcript stays around as audit evidence. the runtime should send the model the tiny piece it actually needs, not replay the whole archaeological dig.

## same questions everywhere {#replay}

the cohort is frozen in `studies/unified-memory-v0/cohort.json`:

- `exact-identifier`
- `supersession`
- `cross-harness`
- `contradiction`
- `missing-evidence`
- `minimal-context`

omp is the first measured lane. dsh has the default-off agentsview stdio transport, but still needs the same frozen model-visible proof. hermes and omo are still pending.

so no, this is not “four-harness memory solved” yet.

## make it fail on purpose {#failures}

the useful cases are the annoying ones: missing evidence, duplicate replay, contradiction, and supersession.

the contradiction case has to show both claims and pick no winner. the missing-evidence case has to abstain. if the memory system cannot say “i do not know,” it is just a confidence generator.

## omp finally gave us a number {#results}

omp pr #107 runs the six frozen question ids through common `z0eval.unified_memory_receipt.v0` rows and passes **16/16** focused tests.

turn 4:

| mode | context bytes | growth |
|---|---:|---:|
| native | **320,075** | **+80,008** |
| donor spill stub | **2,847** | **+701** |
| state packet | **960** | **+0** |

that is **99.70% less context** than the native turn-4 path, about **333.4× smaller**.

very cool. still only a context-shaping result.

agentsview failed closed on the omp host, and we did not invent a hit to make the chart look nice.

| harness | status |
|---|---|
| omp | **measured** |
| dsh | **bounded** — transport exists; frozen model-visible proof pending |
| hermes | **pending** — final cohort receipts not imported |
| omo | **pending** — final cohort receipts not imported |

i am leaving the pending rows pending. once all four lanes produce comparable frozen receipts, then we can aggregate them.

## what this does not prove {#limits}

one omp lane does not establish four-harness equivalence. smaller context does not prove better answers. we also do not need one universal memory database for this to work, and retrieved text is evidence, not automatically truth.

the actual goal is much less magical: same question, same evidence contract, different harness, same supported answer. once that is boring, memory starts looking like infrastructure.
