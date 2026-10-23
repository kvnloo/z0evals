---
title: "the boundary worked. the model study did not run."
subtitle: "deterministic integration evidence is useful. it is not an answer-quality result."
study: agentweb-emma-z0-v0
status: evidence-local
author: "zer0 research"
date: "september 30, 2026"
mock_data: false
toc:
  - id: boundary
    label: what turned green
  - id: blocked
    label: the model path stopped honestly
  - id: promotion
    label: the next sample has to be real
  - id: limits
    label: what this does not prove
---

## what turned green {#boundary}

we kept the real integration boundary and used authored inputs. the [context receipt](https://github.com/kvnloo/z0evals/blob/5ba875d99f9e50bbccfaf00c76498ce80e097562/studies/agentweb-emma-z0-v0/results/context-e2e-20260930.json) contains 18 fixture rows and 0 live rows. privacy, byte-budget, required-term and non-application gates passed. assist-review eligibility stayed false.

the [reliability receipt](https://github.com/kvnloo/z0evals/blob/5ba875d99f9e50bbccfaf00c76498ce80e097562/studies/agentweb-emma-z0-v0/results/reliability-e2e-20260930.json) records 7 observed receipts, a passing summary, no replay failures and no quality-gold violations. duplicate observations could replay without becoming verified-quality labels.

## the model path stopped honestly {#blocked}

the [blocked smoke receipt](https://github.com/kvnloo/z0evals/blob/5ba875d99f9e50bbccfaf00c76498ce80e097562/studies/agentweb-emma-z0-v0/results/model-smoke-blocked-20260930.json) says credentials were unavailable and execution was false. it is a blocker receipt, not passing model evidence. we do not replace the missing model comparison with deterministic green checks.

## the next sample has to be real {#promotion}

the [promotion ladder](https://github.com/kvnloo/z0evals/blob/5ba875d99f9e50bbccfaf00c76498ce80e097562/studies/agentweb-emma-z0-v0/README.md) requires at least 500 real shadow context packets, including at least 100 large-input packets, before context assist review. report and stop decisions need at least 1,000 paired live decisions. authored fixtures cannot satisfy those gates.

we have a completed bounded boundary campaign and an unexecuted model campaign. we do not have an integration-wide promotion.

## what this does not prove {#limits}

these are frozen source receipts, not new reproductions. no customer-quality, live latency or token-economics win was demonstrated. a successful transport call, a completed turn and a safe privacy projection are different things from a useful answer. this is a draft of the negative evidence boundary, not authorization to enable routing.

