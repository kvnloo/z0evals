---
title: "an agent api that does not steal the foreground"
subtitle: "the bounded phone run worked. that says nothing about the quality of health advice."
study: noop-hermes-agent-api
status: evidence-local
author: "zer0 research"
date: "october 21, 2026"
mock_data: false
toc:
  - id: method
    label: keep the permission boundary
  - id: results
    label: what the run recorded
  - id: defects
    label: the defects were part of the result
  - id: limits
    label: what this does not prove
---

## keep the permission boundary {#method}

we tested an opt-in app api from hermes to a phone. the [study readme](https://github.com/kvnloo/z0evals/blob/6d48cf9082205f022c909f59b26275f48e02c274/studies/noop-hermes-agent-api/README.md) separates the agent transport from installation and verification: agent calls did not use adb, but setup and grant-interface testing did. this was not a fully adb-free experiment.

we publish engineering aggregates only. no health values, dashboard content, personal prompts or advice text.

## what the run recorded {#results}

the [aggregate receipt](https://github.com/kvnloo/z0evals/blob/6d48cf9082205f022c909f59b26275f48e02c274/studies/noop-hermes-agent-api/data/summary.json) and [study readme](https://github.com/kvnloo/z0evals/blob/6d48cf9082205f022c909f59b26275f48e02c274/studies/noop-hermes-agent-api/README.md) report end-to-end checks of 12/12 in each run. wrong authorization and browser-origin calls were refused. detail access without the required scope was refused.

warm `data_freshness` calls, n=20, took 10 ms p50 and 14 ms p95. the first call was about 1.5 s with authorization rechecking and privacy-filter startup. warm timing is not cold timing.

in the second run, `open_screen` reported landed true in 487 ms, with foreground activity checked separately. in the background case it posted a notification, reported landed false, and left the foreground app unchanged. a posted notification is not a completed navigation.

## the defects were part of the result {#defects}

the [study readme](https://github.com/kvnloo/z0evals/blob/6d48cf9082205f022c909f59b26275f48e02c274/studies/noop-hermes-agent-api/README.md) records an audit-log write race and a privacy filter incorrectly redacting a source-kind label. the branch added locking and a closed vocabulary. the aggregate script passing did not mean every action landed in the earlier run; the [aggregate receipt](https://github.com/kvnloo/z0evals/blob/6d48cf9082205f022c909f59b26275f48e02c274/studies/noop-hermes-agent-api/data/summary.json) preserves that distinction.

## what this does not prove {#limits}

the [study readme](https://github.com/kvnloo/z0evals/blob/6d48cf9082205f022c909f59b26275f48e02c274/studies/noop-hermes-agent-api/README.md) limits this to one phone, one night and one grant-scope combination. the installed app was a local integration of in-flight work. a coach flow completed, but nobody evaluated the advice. no medical benefit, general privacy certification or production readiness follows. these are source-reported handset receipts, not a fresh reproduction.

