---
title: "offline fan-out is not a phone fleet"
subtitle: "the git rollback was real. the screens and preview failures were synthetic."
study: turbo-app-fanout
status: evidence-local
author: "zer0 research"
date: "october 22, 2026"
mock_data: false
toc:
  - id: scope
    label: what the prototype did
  - id: smoke
    label: real git, simulated product
  - id: ownership
    label: freeze the prototype, not the architecture
  - id: limits
    label: what this does not prove
---

## what the prototype did {#scope}

we have an open draft, not a live lane. the [pinned documentation](https://github.com/kvnloo/z0intelligence/blob/5d284b9634bbcb246ddab3d9fc419940807a2c75/docs/turbo-app-fanout.md) specifies admission bounds, uncertain-send reservations, stop behavior and candidate harvesting. these are client policy controls, not measured provider capacity.

the [draft pr](https://github.com/kvnloo/z0intelligence/pull/193) reports 64 passed in 2.00s. we did not rerun that suite for this article.

## real git, simulated product {#smoke}

the [pr receipt](https://github.com/kvnloo/z0intelligence/pull/193) reports synthetic launches with real waits of at least 20 seconds. the smoke exercised actual temporary git worktrees, patch application, fast-forward and revert. the success reached `now_testing`; the injected preview error reached `reverted`, restoring the original tree.

the build was a stub. the preview log was fake. the screen fixtures were synthetic. no live app launch, send, inference or actual preview change was performed. the [documentation](https://github.com/kvnloo/z0intelligence/blob/5d284b9634bbcb246ddab3d9fc419940807a2c75/docs/turbo-app-fanout.md) explicitly leaves selectors, multiline paste, quotas and physical refresh unqualified.

## freeze the prototype, not the architecture {#ownership}

the [later issue decision](https://github.com/kvnloo/z0intelligence/issues/191#issuecomment-6353523941) keeps this as a source prototype and separates lane-eligibility cognition from worker coordination, device execution and preview integration. that is a migration proposal, not a completed transfer.

we keep the historical test receipt without presenting the old component boundary as the deployment plan.

## what this does not prove {#limits}

offline state-machine evidence is not live phone evidence, physical preview acceptance or sustained throughput. owner opt-in is not a platform-terms clearance. no measured fan-out speedup, unlimited quota or safe unattended consumer-app automation follows from this draft.

