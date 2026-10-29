---
title: "we predicted the next action. nobody committed it."
subtitle: "the frozen baseline is a negative result. the pull-first replacement is still a proposal."
study: next-action-v0
status: evidence-local
author: "zer0 research"
date: "october 21, 2026"
dek: "the frozen baseline is a negative result. the pull-first replacement is still a proposal."
area: speed-ux
published: 2026-10-21
log: [next-action-v0]
mock_data: false
toc:
  - id: baseline
    label: running is not used
  - id: comparison
    label: recency won the useful comparison
  - id: proposal
    label: change the action before the model
  - id: limits
    label: what this does not prove
---

## running is not used {#baseline}

our [frozen baseline](https://github.com/kvnloo/z0evals/blob/e6549bf5f7c5dcd2485b15457cd6fbaf94703c9c/studies/next-action-v0/data/baseline-desktop-shadow.json) covers 30 days: 7,859 shadow predictions, 19 ready-tier surfaces, 0 explicit commits and 0 accept/reject decisions. the service ran. the adoption loop did not.

we publish counts and rates only. no application names, targets, window titles or activity traces.

## recency won the useful comparison {#comparison}

on the app-switch subset, n=5,442, the [frozen baseline](https://github.com/kvnloo/z0evals/blob/e6549bf5f7c5dcd2485b15457cd6fbaf94703c9c/studies/next-action-v0/data/baseline-desktop-shadow.json) reports recency top-1 / top-3 of 0.771 / 0.972. the engine gets 0.454 / 0.690 on that same subset.

the confidence band at or above 0.82 has top-1 accuracy 0.227, n=76. that band is not the same as the 19 surfaces: the engine confidence and the display gate use different projections. high confidence was not calibrated correctness. the separate re-ranker holdout is also not this subset.

## change the action before the model {#proposal}

the [design and preregistration](https://github.com/kvnloo/z0evals/blob/e6549bf5f7c5dcd2485b15457cd6fbaf94703c9c/studies/next-action-v0/README.md) proposes a pull panel for actions that are costly by hand, explicit acceptance, and a recency comparison arm. we want accepted actions and measured time saved, not another count of predictions emitted.

this is not a result for the new panel. no new-design use, gesture adoption or time saving has been measured.

## what this does not prove {#limits}

the [design and preregistration](https://github.com/kvnloo/z0evals/blob/e6549bf5f7c5dcd2485b15457cd6fbaf94703c9c/studies/next-action-v0/README.md) limits the baseline to one person and one desktop. recency is reconstructed from prediction-time states, not every focus event. zero recorded commits does not prove zero incidental benefit. it does show that we have no recorded acceptance flywheel. this draft reports the frozen negative baseline, not the proposed replacement as a completed experiment.

