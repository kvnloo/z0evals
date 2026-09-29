---
title: "One Memory Plane, Four Agent Harnesses"
subtitle: "A cross-harness test of source-backed recall, minimal state, and provenance."
study: unified-memory-v0
status: evidence-pending
author: "Zer0 Research"
date: "September 29, 2026"
mock_data: false
toc:
  - id: question
    label: Question
  - id: architecture
    label: Architecture
  - id: replay
    label: Replay
  - id: failures
    label: Failure tests
  - id: results
    label: Results
  - id: limits
    label: Limits
---

<div class="lede">
Can four different agent harnesses recover the same prior state without copying an entire transcript into every model call?
</div>

<div class="hero-rule"></div>

## The question {#question}

This study separates four claims that are easy to blur together: evidence was found, evidence reached the model, the answer was supported by that evidence, and an independent check accepted the answer.

No result is published until all four stages have receipts.

## One source-backed path {#architecture}

```text
conversation / file / git truth
          |
          v
AgentsView / exact retrieval / other evidence capability
          |
          v
z0intelligence
EvidenceRef + minimal state
          |
    +-----+------+-----+
    |            |     |
   DSH         Hermes  OMO   OMP
    |            |     |     |
    +----- comparable receipts +
```

The transcript remains an audit source. The runtime should send only the evidence needed for the current decision.

## Same question, four replays {#replay}

The executable cohort is now frozen in `studies/unified-memory-v0/cohort.json`: `exact-identifier`, `supersession`, `cross-harness`, `contradiction`, `missing-evidence`, and `minimal-context`.

OMP is the first public measured lane. DSH has the default-off AgentsView stdio transport overlay, but still needs the same frozen model-visible injection/support proof. Hermes and OMO do not yet have final comparable cohort receipts imported here, so the four-harness result remains pending.

## Make it fail on purpose {#failures}

The suite includes missing-evidence, duplicate-replay, contradiction, and supersession cases. A useful memory system must know when not to answer.

## Results {#results}

### OMP partial result

OMP PR #107 runs the six frozen question IDs through common `z0eval.unified_memory_receipt.v0` rows and passes **16/16** focused tests.

Turn-4 context:

| mode | context bytes | growth |
|---|---:|---:|
| native | **320,075** | **+80,008** |
| donor spill stub | **2,847** | **+701** |
| state packet | **960** | **+0** |

The State Packet is **99.70% smaller** than native turn-4 context, about **333.4× smaller**.

That is a context-shaping measurement, not a four-harness correctness claim. AgentsView search failed closed on the OMP host; no hit was invented.

| harness | status |
|---|---|
| OMP | **MEASURED** |
| DSH | **BOUNDED** — transport exists; frozen model-visible proof pending |
| Hermes | **PENDING** — final cohort receipts not imported |
| OMO | **PENDING** — final cohort receipts not imported |

No cross-harness aggregate is published until comparable frozen receipts exist for all required lanes.

## What this still would not prove {#limits}

A passing v0 would establish cross-harness retrieval and context use on the frozen cases. It would not establish one universal memory backend, perfect long-horizon recall, or permission to treat retrieved text as verified truth.
