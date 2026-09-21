---
title: "Small Models Calling the Shots"
subtitle: "What actually routes best on a local 3080 Ti?"
study: slm-router-v0
status: mock-ui
author: "Zer0 Research"
date: "September 21, 2026"
toc:
  - id: setup
    label: Setup
  - id: routing
    label: Routing
  - id: compiler
    label: Compiler
  - id: latency
    label: Latency
  - id: qroute
    label: Q-Route
---

<div class="mock-banner">
  <strong>MOCK DATA · UI PROTOTYPE</strong>
  <span>The evaluation pipeline is running for real. Numbers and interactive traces on this page are synthetic placeholders while we build and verify the publication UI. Nothing below should be cited as an experimental result.</span>
</div>

<div class="lede">
What happens when you stop asking one large model to make every routing decision? We are building a compiler-first agent stack that can choose between deterministic rules, tiny specialists, bounded scorers, local SLMs and frontier fallbacks. This page is the interface we will use to publish the real evaluation.
</div>

<div class="hero-rule"></div>

## Setup {#setup}

We want routing to be a systems problem before it is a language-model problem. The runtime first compiles the current state into a legal action set. Learned policies only choose among actions that have already passed dependency, budget and capability checks.

<div class="metric-grid">
  <div class="metric"><span class="metric-label">mock trials</span><strong>500</strong><small>synthetic UI data</small></div>
  <div class="metric"><span class="metric-label">candidate routers</span><strong>6</strong><small>illustrative</small></div>
  <div class="metric"><span class="metric-label">target GPU</span><strong>12 GB</strong><small>RTX 3080 Ti</small></div>
</div>

<div class="figure-card">
  <div class="figure-head"><div><span class="eyebrow">Figure 1 · mock</span><h3>One routing decision, six possible futures</h3></div><span class="mock-chip">synthetic</span></div>
  <p class="figure-copy">Drag the state-complexity slider. The chart shows synthetic expected utility for each route. The real version will be generated from frozen receipts.</p>
  <div class="control-row"><label>state complexity <input id="complexity" type="range" min="0" max="100" value="44"></label><output id="complexityOut">44</output></div>
  <div id="routeBars" class="route-bars" aria-label="mock route utilities"></div>
  <div class="figure-foot">Mock values only · interactive behavior is being built before the real eval completes.</div>
</div>

## The routing question {#routing}

A function caller and an orchestrator are not the same thing. A model can emit flawless JSON while choosing the wrong tool, serializing work that should run in parallel, or escalating when a cheaper policy was sufficient.

<div class="pullquote">The router should spend intelligence only where the state still contains meaningful uncertainty.</div>

<div class="figure-card wide">
  <div class="figure-head"><div><span class="eyebrow">Figure 2 · mock</span><h3>Quality is only one axis</h3></div><span class="mock-chip">synthetic</span></div>
  <div class="tabs" role="tablist">
    <button class="tab active" data-metric="quality">quality</button>
    <button class="tab" data-metric="latency">latency</button>
    <button class="tab" data-metric="cost">GPU-ms</button>
  </div>
  <div id="scatter" class="scatter"></div>
  <div class="figure-foot">Synthetic Pareto frontier. Real points will come from z0evals study artifacts.</div>
</div>

## Compiler before model {#compiler}

The safety boundary is intentionally boring. Illegal actions are removed before the model receives its candidate list. The eventual article will compare the exact same routers with and without this compiler gate.

<div class="compare-grid">
  <div class="compare bad">
    <span class="eyebrow">mock · unconstrained</span>
    <strong id="unsafeCount">7</strong>
    <span>unsafe selections / 100 trials</span>
  </div>
  <div class="compare good">
    <span class="eyebrow">mock · compiler-first</span>
    <strong>0</strong>
    <span>unsafe selections / 100 trials</span>
  </div>
</div>

<div class="trace">
  <div class="trace-head"><span>synthetic decision trace</span><button id="replayTrace">replay</button></div>
  <div class="trace-step"><b>01</b><span>intent compiled</span><em>4 candidate actions</em></div>
  <div class="trace-step"><b>02</b><span>capability filter</span><em>destructive action removed</em></div>
  <div class="trace-step"><b>03</b><span>budget + dependency gate</span><em>2 legal actions remain</em></div>
  <div class="trace-step"><b>04</b><span>router</span><em>Hammer-like specialist selected</em></div>
  <div class="trace-step"><b>05</b><span>verifier</span><em>mock success</em></div>
</div>

## Latency changes the answer {#latency}

A model that looks attractive on a leaderboard can be a poor hot-path controller once cold starts, KV pressure, serving runtime and tail latency are included. The publication will therefore expose distributions, not just means.

<div class="figure-card">
  <div class="figure-head"><div><span class="eyebrow">Figure 3 · mock</span><h3>Decision latency distribution</h3></div><span class="mock-chip">synthetic</span></div>
  <div id="latencyPlot" class="latency-plot"></div>
  <div class="legend-row"><span><i class="dot d1"></i>tiny specialist</span><span><i class="dot d2"></i>orchestrator</span><span><i class="dot d3"></i>general local</span></div>
  <div class="figure-foot">Synthetic p50/p95/p99 distribution for layout development only.</div>
</div>

## Toward Q-Route {#qroute}

The follow-up experiment asks whether expensive routing decisions can be continuously distilled into cheaper policies. The training stream can be continuous while promotion remains discrete and gated.

<div class="pipeline">
  <div><b>observe</b><span>real harness state</span></div><i>→</i>
  <div><b>roll out</b><span>candidate routes</span></div><i>→</i>
  <div><b>verify</b><span>independent outcome</span></div><i>→</i>
  <div><b>distill</b><span>cheaper policy</span></div><i>→</i>
  <div><b>canary</b><span>non-inferiority gate</span></div>
</div>

### What is real today?

The **system architecture and evaluation pipeline are real and under active development**. The visualizations and numeric results on this page are mock data until the DSH experiment artifacts are imported into the pinned `slm-router-v0` study and reviewed.

When that happens, this banner stays in the git history but disappears from the published frozen study. Every quantitative claim will resolve to a machine-readable artifact and immutable source commit.

<div class="method-card">
  <span class="eyebrow">Methodology contract</span>
  <h3>No model gets to grade itself.</h3>
  <p>Prediction, execution completion and verified outcome remain separate records. Source-reported benchmarks are also kept separate from measurements reproduced on our own hardware.</p>
  <a href="https://github.com/kvnloo/z0evals">View the evaluation repository ↗</a>
</div>
