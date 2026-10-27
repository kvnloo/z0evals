---
title: "the tap was fast. proving it landed cost more."
subtitle: "we kept the lexical matcher and did not ship the on-phone model tier."
study: gui-scripting-speed-z0live-control
status: evidence-local
author: "zer0 research"
date: "october 20, 2026"
mock_data: false
toc:
  - id: question
    label: a tap is not a result
  - id: numbers
    label: the local path
  - id: tiers
    label: a small model was not the cheap answer
  - id: limits
    label: what this does not prove
---

## a tap is not a result {#question}

we wanted phone control to wait for an observed action result instead of reporting a fire-and-forget call as success. the [study readme](https://github.com/kvnloo/z0evals/blob/3809d360790c8e8c2de7c65c796ead9375a77340/studies/gui-scripting-speed/z0live-control/README.md) records a permission failure and missing result feedback behind the original failed interaction. this draft keeps only aggregate engineering evidence, not the session text.

## the local path {#numbers}

from the [study readme](https://github.com/kvnloo/z0evals/blob/3809d360790c8e8c2de7c65c796ead9375a77340/studies/gui-scripting-speed/z0live-control/README.md) and [aggregate data](https://github.com/kvnloo/z0evals/blob/3809d360790c8e8c2de7c65c796ead9375a77340/studies/gui-scripting-speed/z0live-control/data/summary.json): warm in-process tree reads were 9.3 / 104 ms p50 / p95. u2 was 98 / 165 ms. both columns exclude host transport; the u2 path includes its curl startup.

whole `phone_do` was 267 / 477 ms, with 16/16 landed. the decision step was 16.5 / 24 ms. confirmation was 166 / 439 ms. most of the fast path was waiting for evidence, not choosing.

## a small model was not the cheap answer {#tiers}

on the synthetic set in the [study readme](https://github.com/kvnloo/z0evals/blob/3809d360790c8e8c2de7c65c796ead9375a77340/studies/gui-scripting-speed/z0live-control/README.md), the lexical tier acted on 25 cases, escalated 4, and made 0 wrong acts. phone qwen3-1.7b acted right / wrong 16 / 6 at the 0.95 floor, with 765 / 2453 ms p50 / p95. fast enough was not accurate enough; the more accurate phone model was not fast enough.

on 14 held-out real goals, desktop qwen3-4b and jev each got 12/14 top-1. they still produced 2 and 1 wrong acts respectively. consequential actions stay behind explicit confirmation.

## what this does not prove {#limits}

the [study readme](https://github.com/kvnloo/z0evals/blob/3809d360790c8e8c2de7c65c796ead9375a77340/studies/gui-scripting-speed/z0live-control/README.md) calls this an unregistered first iteration. rules and floors were written after seeing the synthetic fixture. there is one shared test phone. landed means an accessibility event or screen-hash change, not goal completion or independent intent verification. no general safety claim follows from the fast timing.

