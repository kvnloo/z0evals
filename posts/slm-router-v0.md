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
  - id: references
    label: References
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
<tr><td>compiler + NanoJev 0.6B</td><td>45/84</td><td>[0.43, 0.64]</td><td>31 ms</td><td>0</td></tr>
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
    <span class="eyebrow">Qwen4B + NanoJev artifact</span>
    <strong>13/28</strong>
    <span>hurt 8 · helped 0</span>
  </div>
</div>

The NanoJev artifact was actually delivered and consumed on **26/28 states**, so this is not an integration failure disguised as a model result. The downstream model received the extra signal and became worse.

The Hammer3B pre-composition was worse again: **6/28 correct**, hurting 13 states and helping none.

NanoJev by itself was **45/84 at 31 ms**. This 45/84 is our local 0.6B scored zero-shot across the full bounded-choice action space, and its upstream checkpoint was trained largely on maze/snake/ViZDoom control decisions. On the compiler's exact matched candidate set, a later experiment showed the same checkpoint can remove ~61% of Hammer3B's calls at 94.1% success-given-covered. In front of Qwen4B it was statistically indistinguishable from the direct path while only about 17% faster on the relevant comparison, and the corrected composition evidence showed no downstream benefit. The calibrated distribution remains worth recording for learning and analysis; it does **not** currently justify another runtime tier.

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

## references & things that shaped this {#references}

this project is obviously not happening in a vacuum. a lot of this came from trying things, stealing good abstractions from other systems, reading other people's evals, and then discovering that some of those ideas behave very differently once you put them on the same local hardware and the same typed decision.

i'm leaving this intentionally broad. these are not all direct dependencies, and i'm definitely not claiming every project below agrees with the architecture we ended up with. some inspired a direction, some gave us a primitive, some gave us an eval pattern, and some were useful specifically because our results disagreed with what i expected going in.

<details>
<summary><strong>closest conceptual references</strong></summary>

- [southbridge — “jev: watching the agents”](https://www.southbridge.ai/blog/jev-watching-the-agents) — the closest conceptual and visual reference for this article. the important idea was not just jev itself, but turning fuzzy agent behavior into typed questions that a cheap observer can answer.
- [jev](https://github.com/southbridgeai/jev) — bounded probabilistic decision-making without generating prose token by token.
- [openjev / z0intelligence](https://github.com/kvnloo/z0intelligence) — our local path for direct logit readout, trainable jev-like heads, nanojev, q-route and the common decision backend.
- [Hermes PR #113020 — probabilistic decision providers for plugins](https://github.com/NousResearch/hermes-agent/pull/113020) — a provider-neutral binary / choice / ordinal decision runtime with full distributions, explicit abstention and replay metrics. this PR is by `fangliquanflq`, not tek.

</details>

<details>
<summary><strong>tek's eval work in hermes</strong></summary>

- [teknium1 — Hermes PR #88663: Browser Use mode A/B benchmark](https://github.com/NousResearch/hermes-agent/pull/88663) — turns a 204-run browser benchmark into a permanent, rerunnable eval with task batteries, multiple arms, reps and recovered baseline scorecards.
- [teknium1 — Hermes PR #79162: reproducible core-toolset A/B eval harness](https://github.com/NousResearch/hermes-agent/pull/79162) — baseline vs fixes, one variable at a time, production-derived trap tasks, trace-based scoring and programmatic success checks.
- [teknium1 — Hermes PR #87326: lean-tail compaction + recall eval](https://github.com/NousResearch/hermes-agent/pull/87326) — especially relevant to the token-savings side of this project: quality and retained tokens measured together instead of celebrating compression by itself.
- [teknium1 — Hermes PR #109903: move living benchmarks into `evals/`](https://github.com/NousResearch/hermes-agent/pull/109903) — a useful repository-architecture reference for treating evals as durable artifacts instead of one-off scripts.

</details>

<details>
<summary><strong>agent harnesses & execution systems</strong></summary>

- [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) — one of the main execution environments behind this work. the skill/plugin surface is what made it possible to insert cheap typed decisions without turning every decision into another model-visible tool call.
- [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) — plugin-first harness architecture, provider-neutral model execution, trajectory views and another environment we are using to test the same zer0 primitives.
- [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi) — a major reference for pushing work down into the harness: persistent workers, extension hooks, context control and the broader idea that the runtime should do more so the model has to do less.
- [Anthropic Model Context Protocol](https://modelcontextprotocol.io/) — one of the surrounding standards for separating model reasoning from external tools/resources.
- [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) — another useful reference point for agent handoffs, tracing and runtime/tool separation.

</details>

<details>
<summary><strong>zer0 architecture</strong></summary>

- [aodl](https://github.com/kvnloo/aodl) — typed intent, constraints and legal-action structure. the most important phase 1b lesson maps directly onto this: illegal actions should disappear before a learned policy sees them.
- [z0intelligence](https://github.com/kvnloo/z0intelligence) — cognition selection, escalation, `DecisionBackend`, nanojev and q-route.
- [kerdoios](https://github.com/kvnloo/kerdoios) — compute placement, residency, provider quota and resource economics. residency turning into a 10+ second system cost is why this cannot be collapsed into the cognition router.
- [evolution-lab](https://github.com/kvnloo/evolution-lab) — experimental search/training for q-route, mushroom-body policies, fly-derived policies and later distillation.
- [tokenomics](https://github.com/kvnloo/tokenomics) — neutral accounting for tokens, context, latency, cost and verified outcomes.
- [z0evals](https://github.com/kvnloo/z0evals) — the publication/certification layer this article lives in.
- [verified-oss-loop](https://github.com/kvnloo/verified-oss-loop) — exact-head evidence, independent verification and separating generation from promotion.
- [frontier-kb](https://github.com/kvnloo/frontier-kb) — research evidence and literature trail used to keep architecture claims separate from implementation state.

</details>

<details>
<summary><strong>models & decision backends we actually cared about</strong></summary>

- [Hammer / Hammer2.1](https://huggingface.co/collections/ibm-granite/hammer) — the 3b and 7b specialists that ended up being much harder to beat on bounded choice than i expected.
- [Qwen](https://github.com/QwenLM/Qwen3) — the 4b/9b family that clarified the bounded-choice vs orchestration split.
- [NVIDIA Nemotron](https://developer.nvidia.com/nemotron) — important mostly because the orchestrator branding made its local result a useful negative test of “model role” claims.
- [Google FunctionGemma](https://huggingface.co/google/functiongemma-270m-it) — the sub-billion lower-bound experiment for tool/decision work.
- [nanojev implementation in z0intelligence](https://github.com/kvnloo/z0intelligence/tree/main/src/z0int/backends) — local non-autoregressive decision backend and calibration surface.

</details>

<details>
<summary><strong>local inference, serving & placement</strong></summary>

- [llama.cpp](https://github.com/ggml-org/llama.cpp) — the local serving substrate behind much of the measured residency/swap behavior.
- [vLLM](https://github.com/vllm-project/vllm) — higher-throughput serving plus the broader lesson that the inference backend itself affects what “cheap” means.
- [LiteLLM](https://github.com/BerriAI/litellm) — useful provider-routing and spend-tracking reference; kerdoios intentionally should not become another full LLM gateway.
- [Groq](https://console.groq.com/docs/overview) — free/fast remote capacity now used as experimental compute and counterfactual-worker capacity.
- [Cerebras Inference](https://inference-docs.cerebras.ai/) — another high-throughput remote path now feeding the experimental inventory.
- [OpenRouter](https://openrouter.ai/docs) — broad provider/model discovery and a useful source of free-tier experimental routes.
- [Kubernetes](https://kubernetes.io/) — optional execution substrate for repeatable local model/services experiments, resource isolation and placement work.

</details>

<details>
<summary><strong>fly, mushroom & tiny learned policies</strong></summary>

- [FlyWire](https://flywire.ai/) — whole-brain drosophila connectomics and useful grounding for the scale/structure of the biological systems we keep borrowing ideas from.
- [“the connectome of an insect brain” / drosophila connectomics work](https://www.science.org/doi/10.1126/science.add9330) — background for thinking about tiny recurrent/sensorimotor circuits as specialists rather than miniature language models.
- [mushroom-body learning literature](https://www.nature.com/articles/nature23455) — inspiration for the sparse plastic specialist direction: cheap associative learning over a structured representation.
- [flyforge research trail](https://github.com/kvnloo/frontier-kb) — our collected fly/mushroom literature, MaleCNS work, TMNF-C references and the distinction between a sensorimotor fly worker and a general SLM.
- [flyforge integration in z0intelligence](https://github.com/kvnloo/z0intelligence/tree/main/omp-extensions) — current shadow/recovery integrations used to turn those ideas into measurable agent decisions.

</details>

<details>
<summary><strong>related “make the model do less” work</strong></summary>

- **AgentRun — “a harness for repetitive knowledge work” by Miguel Ríos Berríos / Grep** — adjacent work that frames the saving differently: compile repeated agent behavior into a workflow, skip work that cannot change the answer, and escalate the odd cases back to an agent.
- [RLM / recursive language-model work](https://arxiv.org/abs/2512.24601) — relevant to the broader context-virtualization/offloading idea: move evidence addressing and repeated context manipulation out of the main model's raw token stream.
- [SWE-agent](https://github.com/SWE-agent/SWE-agent) — useful reference for agent-computer interfaces and how much performance can come from constraining the interaction surface rather than only changing the model.
- [OpenHands](https://github.com/All-Hands-AI/OpenHands) — another strong reference point for separating agent policy, runtime, tools and evaluation.
- [DSPy](https://github.com/stanfordnlp/dspy) — relevant to treating prompts/programs as optimizable components rather than hand-written sacred text.

</details>

<details>
<summary><strong>evaluation & measurement methodology</strong></summary>

- [Brier score](https://en.wikipedia.org/wiki/Brier_score) — useful for bounded probabilistic decisions because top-1 accuracy throws away the thing we actually want from jev/nanojev: calibrated probability.
- [log loss](https://en.wikipedia.org/wiki/Cross-entropy) — another proper scoring rule used when comparing distributions rather than only selected labels.
- [reliability diagrams / calibration](https://scikit-learn.org/stable/modules/calibration.html) — background for the risk/coverage and “when should the cheap policy abstain?” framing.
- [Wilson score interval](https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval#Wilson_score_interval) — the confidence interval used in the bounded-choice result table.
- [OpenTelemetry](https://opentelemetry.io/) — useful surrounding reference for thinking about execution evidence as durable traces rather than ad hoc print statements.
- [MLflow](https://github.com/mlflow/mlflow) and [Weights & Biases](https://wandb.ai/) — general experiment-tracking references; we borrow the lineage mindset while keeping zer0's runtime/eval contracts repo-native.

the methodology i want to keep is basically:

```text
record the real execution
→ replay the same state
→ change one thing
→ verify externally
→ preserve the evidence
```

not:

```text
ask the model whether the new system seems better
```

</details>

<details>
<summary><strong>future directions / not claims of this study</strong></summary>

these are things connected to the architecture that phase 1b did **not** validate directly:

- mushroom-body learned specialists
- fly-derived temporal/recovery policies
- nanojev risk/coverage routing
- q-route progressively compiling expensive decisions into cheaper policies
- kubernetes as an optional execution substrate
- groq/cerebras free-tier capacity as experimental compute
- agentrun-style workflow compilation
- rlm-style context/evidence offloading
- learned residency-aware placement
- cross-harness shadow evaluation across hermes / dsh / omp

the question stays the same for all of them:

> **does this let the expensive model do less without making the system worse?**

if yes, keep digging.

if no, kill it.

</details>

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
