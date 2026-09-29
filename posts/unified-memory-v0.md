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

Results pending. The frozen study will replay the same question IDs through DSH, Hermes, OMO, and OMP and preserve the exact tested revisions.

## Make it fail on purpose {#failures}

The suite includes missing-evidence, duplicate-replay, contradiction, and supersession cases. A useful memory system must know when not to answer.

## Results {#results}

No numbers yet. Tables and figures will be generated only from frozen receipts in `studies/unified-memory-v0/`.

## What this still would not prove {#limits}

A passing v0 would establish cross-harness retrieval and context use on the frozen cases. It would not establish one universal memory backend, perfect long-horizon recall, or permission to treat retrieved text as verified truth.
