---
title: "Small Models Calling the Shots"
subtitle: "Phase 1B: what actually routes best on a local RTX 3080 Ti?"
study: slm-router-v0
status: evidence-local
mock_data: false
author: "Zer0 Research"
date: "September 21, 2026"
toc:
  - id: evidence
    label: Evidence
  - id: bounded
    label: Bounded choice
  - id: residency
    label: Residency
  - id: orchestration
    label: Orchestration
  - id: composition
    label: Composition
  - id: compiler
    label: Compiler
  - id: gate
    label: Gate
  - id: phase2
    label: Phase 2
---

<div class="evidence-banner">
  <strong>REAL PHASE 1B DATA</strong>
  <span>Run <code>p1b-20260921T1430Z</code> is immutable and the reported measurements are real. External inference spend was $0.00: every measured call ran through the local <code>z0int cognition serve</code> supervisor. The source commits are still local-only, so this publication remains a draft until those exact commits and raw artifacts are pushed and imported.</span>
</div>

<div class="lede">
The first sparse run told us which small models looked promising. Phase 1B asked the harder question: after repeating the same state/arm cells enough times to make the comparison readable, does the cheap path still win, where does escalation actually earn its latency, and does composing multiple “smart” routers help at all?
</div>

<div class="hero-rule"></div>

## The evidence got dense enough to argue with {#evidence}

Phase 1 had 522 measured cells, but 460 of them had only one observation. Phase 1B reduced the matrix to the 370 cells that matter for the current bounded-choice decision and collected **1,102 raw receipts**. **362/370 cells now have n≥3, and zero remain at n=1.**

<div class="metric-grid">
  <div class="metric"><span class="metric-label">raw receipts</span><strong>1,102</strong><small>Tokenomics projection: 0 missing required keys</small></div>
  <div class="metric"><span class="metric-label">measured cells</span><strong>370</strong><small>362 at n≥3</small></div>
  <div class="metric"><span class="metric-label">external inference spend</span><strong>$0</strong><small>local supervisor only</small></div>
</div>

The frozen 12-scenario orchestration cohort also reproduced the original Phase 1 result exactly: solved counts remained **9/12, 9/12, 6/12**, while correct-stop counts remained **5/12, 7/12, 7/12** for Qwen3.5-4B, Qwen3.5-9B, and Nemotron-8B respectively.

<a href="../data/slm-router-v0/phase1b-summary.json">Machine-readable Phase 1B summary ↗</a>

## The bounded-choice default is much smaller than expected {#bounded}

<table class="result-table">
<thead><tr><th>arm</th><th>success</th><th>95% CI</th><th>warm p50</th><th>dangerous</th></tr></thead>
<tbody>
<tr class="primary"><td>compiler + Hammer2.1-3B</td><td><strong>75/84</strong></td><td>[0.81, 0.94]</td><td><strong>195 ms</strong></td><td>0</td></tr>
<tr><td>compiler + Qwen3.5-4B</td><td>75/84</td><td>[0.81, 0.94]</td><td>1,993 ms</td><td>0</td></tr>
<tr><td>compiler + Qwen3.5-9B</td><td><strong>78/84</strong></td><td>[0.84, 0.96]</td><td>3,603 ms</td><td>0</td></tr>
<tr><td>compiler + Hammer2.1-7B</td><td>72/84</td><td>[0.77, 0.92]</td><td>319 ms</td><td>0</td></tr>
<tr><td>compiler + Nemotron-8B</td><td>52/84</td><td>[0.51, 0.71]</td><td>2,475 ms</td><td>0</td></tr>
<tr><td>compiler + FunctionGemma-270M</td><td>51/84</td><td>[0.50, 0.70]</td><td>66 ms</td><td>0</td></tr>
<tr><td>compiler + JEV</td><td>45/84</td><td>[0.43, 0.64]</td><td>31 ms</td><td>0</td></tr>
<tr class="warning"><td>unfiltered + Hammer2.1-3B</td><td>69/84</td><td>[0.72, 0.89]</td><td>186 ms</td><td><strong>6</strong></td></tr>
</tbody>
</table>

<div class="figure-card wide">
  <div class="figure-head"><div><span class="eyebrow">Figure 1 · measured</span><h3>Success and latency are not the same ranking</h3></div><span class="mock-chip" style="border-color:#8aa58c;background:#eef5ed;color:#315b35">Phase 1B</span></div>
  <p class="figure-copy">Switch between success rate, warm p50 latency, and dangerous selections. Values are loaded from the published Phase 1B summary artifact rather than embedded in this page.</p>
  <div class="tabs" role="tablist">
    <button class="tab active" data-phase-metric="success">success</button>
    <button class="tab" data-phase-metric="latency">warm p50</button>
    <button class="tab" data-phase-metric="danger">danger</button>
  </div>
  <div id="phase1bChart" class="route-bars" data-source="../data/slm-router-v0/phase1b-summary.json"></div>
  <div class="figure-foot">Run p1b-20260921T1430Z · 84 trials per listed arm.</div>
</div>

The practical default is **compiler → Hammer2.1-3B**. It ties Qwen3.5-4B at 75/84 while being roughly ten times faster on warm p50. Qwen3.5-9B reaches the highest aggregate bounded-choice success at 78/84, but at roughly eighteen times Hammer3B's warm p50. Its measured advantage is narrow: it is the unique best arm on exactly one state, `tool_fails`, and it is best-success on 27/28 states when latency is ignored.

<div class="finding-grid">
  <div class="finding"><strong>Hammer3B owns the hot path.</strong><span>Best measured success on 26/28 states with 195 ms warm p50 and zero dangerous selections behind the compiler.</span></div>
  <div class="finding"><strong>Qwen4B did not earn bounded escalation.</strong><span>Exact 75/84 tie with Hammer3B at 1,993 ms warm p50. Its value appears elsewhere.</span></div>
  <div class="finding"><strong>Qwen9B earned one narrow niche.</strong><span>78/84 overall and the unique best arm on <code>tool_fails</code>, but 3.6 s warm p50.</span></div>
  <div class="finding"><strong>Nemotron did not establish a measured niche.</strong><span>52/84 bounded success and weaker expanded orchestration than the Qwen tiers on the tasks tested here.</span></div>
</div>

## Residency is a system-level routing feature {#residency}

The largest latency surprise was not model generation. It was **getting the right model resident at all**.

<div class="metric-grid">
  <div class="metric"><span class="metric-label">cold load p50</span><strong>13.9 s</strong><small>measured</small></div>
  <div class="metric"><span class="metric-label">model swap p50</span><strong>12.9 s</strong><small>measured</small></div>
  <div class="metric"><span class="metric-label">warm invocation p50</span><strong>1.76 s</strong><small>across the measured serving path</small></div>
</div>

FunctionGemma's measured cold total was about **3.1 s**. Qwen3.5-9B's was about **17.2 s**. That means Qwen9B can spend longer becoming resident than Hammer3B spends on an entire 28-state warm sweep.

This changes the routing problem. “Which model is best for this state?” is incomplete unless the router also knows **what is already resident, what a swap costs, and whether the quality delta is worth paying that cost now**. Residency belongs in the state seen by Q-Route and in Kerdoios' placement economics.

## Bounded choice and orchestration are different jobs {#orchestration}

Qwen3.5-4B did not beat Hammer3B on bounded choice, but it **did** earn a role in orchestration: **31/40 solved**, the highest reported solved count in the expanded orchestration run and the fastest measured orchestrator among the Qwen tiers.

Qwen3.5-9B showed a different advantage: **27/40 correct stops** versus 23/40 for Qwen4B. Both Qwen tiers had only **3/40 failures to escalate**, while Nemotron recorded **12/40**.

The result is not “smallest always wins.” It is more specific:

<div class="pullquote">Use the smallest mechanism that preserves the behavior required by the current state family.</div>

For bounded legal-action choice, that mechanism is currently Hammer3B. For orchestration, Qwen4B and Qwen9B earn work that their bounded-choice latency would not justify.

## Composition made the downstream model worse {#composition}

The strongest negative result in Phase 1B is that the intuitive cascade did not help.

<div class="compare-grid">
  <div class="compare good">
    <span class="eyebrow">Qwen4B alone</span>
    <strong>18/28</strong>
    <span>correct states</span>
  </div>
  <div class="compare bad">
    <span class="eyebrow">Qwen4B + JEV artifact</span>
    <strong>13/28</strong>
    <span>hurt 8 · helped 0</span>
  </div>
</div>

The JEV artifact was actually delivered and consumed on **26/28 states**, so this is not an integration failure disguised as a model result. The downstream model received the extra signal and became worse.

The Hammer3B pre-composition was worse again: **6/28 correct**, hurting 13 states and helping none.

JEV by itself was **45/84 at 31 ms**. In front of Qwen4B it was statistically indistinguishable from the direct path while only about 17% faster on the relevant comparison, and the corrected composition evidence showed no downstream benefit. The calibrated distribution remains worth recording for learning and analysis; it does **not** currently justify another runtime tier.

The first composition pass at `max_tokens=512` is preserved separately as a failure case: every Qwen stage returned empty content because thinking consumed the output budget. The corrected run used a larger budget.

## The compiler is doing real safety work {#compiler}

Compiler-first legal-action filtering did not merely make the prompt easier. It changed the observed safety behavior.

<div class="compare-grid">
  <div class="compare bad">
    <span class="eyebrow">unfiltered Hammer3B</span>
    <strong>6/84</strong>
    <span>dangerous selections</span>
  </div>
  <div class="compare good">
    <span class="eyebrow">compiler-first arms</span>
    <strong>0</strong>
    <span>dangerous selections in the bounded table</span>
  </div>
</div>

The new compiler-contract slice passed **26/26** fixtures, with one exposure explicitly documented as outside the current contract's reach. On the tempting near-miss, FunctionGemma selected the dangerous action; all five other tested models declined it.

That supports a sharper architecture claim than “the model behaved safely”: **the runtime should remove illegal actions before learned routing sees them.**

## The gate passed, and also exposed two bugs in itself {#gate}

Phase 1B passed the evidence gate for bounded-choice corpus preparation: 362/370 cells reached n≥3, label disagreement was only **1.35% (5/370)**, the frozen orchestration cohort reproduced exactly, and the remaining routing error localized to three feature collisions classified as `insufficient_features`.

The measured next feature is **`budget_units`**, with a +0.071 ceiling improvement. `authority_breadth` / `legal_family_count` follows at +0.036. Fixture-family one-hots score similarly, but they are not runtime-observable and therefore are not valid router inputs.

Two gate defects are now visible precisely because the evidence got denser.

First, on `tool_fails`, the only correct arm exceeds the frozen 4,000 ms budget. The gate assigns the correct-but-slow arm and the wrong-but-fast arm the same **−1.000** utility, so it retains the cheap wrong owner.

Second, the safety clause reads selected `dangerous_rate`, not `exposed_dangerous`. That allows the known unfiltered Hammer3B arm with 6/84 dangerous selections to own four regions. FunctionGemma and Hammer3B also share the same `tiny_specialist` rung, so the current gate never compares the 0.61 arm against the 0.89 arm directly.

Those are reported defects in the frozen gate, not tuned away after seeing the result.

### Sampling caveats

Eight cells remain at n=2 in `compiler+jev+qwen3.5_4b`, and no cell reached n≥10. Neither blocked the Phase 1B corpus-preparation decision, but both remain explicit caveats.

## Phase 2 stops before training {#phase2}

The proposed first Phase 2 slice is intentionally conservative.

<div class="pipeline">
  <div><b>420 episodes</b><span>5 compiler-first arms × 28 states × 3 reps</span></div><i>→</i>
  <div><b>100% gold labels</b><span>no teacher inference</span></div><i>→</i>
  <div><b>+ budget_units</b><span>one measured runtime feature</span></div><i>→</i>
  <div><b>70 / 15 / 15</b><span>chronological, sealed by task</span></div><i>→</i>
  <div><b>stop</b><span>digest-stamped corpus, no training</span></div>
</div>

The OOD families are `abstention`, `dependencies`, `parallelism`, and `uncertainty`. The frozen gate and thresholds stay untouched. The exit condition is a written, disjoint, digest-stable corpus with a 100% gold-label census.

**Nothing was trained in Phase 1B.** No router or specialist was updated, no threshold was tuned, nothing was promoted, and Evolution Lab received no training artifact.

## Reproducibility and current publication status

The Phase 1B source trees were reported clean. z0intelligence finished on `feat/local-cognition-portfolio` at `f721f8c`; Evolution Lab finished on `experiment/q-route-v0` at `659b5a8`. Those commits are still local-only.

The reported checks were:

| check | result |
| --- | --- |
| z0intelligence | 390 passed, 1 known pre-existing failure at `decider.py:177` |
| Evolution Lab | 238 passed, 1 skipped |
| artifact SHA verification | 24/24 OK |
| production release | 0 llama-server processes, GPU 788 MiB, no orphaned VRAM |

This post therefore distinguishes **measured** from **fully published/reproducible**. The numbers above are measured results from the immutable local run. The study remains a draft until the exact source commits and canonical raw artifacts are pushed, imported, hashed, and validated by z0evals.

<div class="method-card">
  <span class="eyebrow">Evidence contract</span>
  <h3>The post is downstream of the run, not the other way around.</h3>
  <p>The current public JSON is a transcription of the Phase 1B handoff for UI and review. Once the local commits are pushed, the raw receipts and generated decision artifact become the canonical evidence, source SHAs expand to full immutable commits, and the study can move from draft to frozen.</p>
  <a href="../data/slm-router-v0/phase1b-summary.json">Inspect the published summary ↗</a>
</div>
