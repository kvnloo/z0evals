---
title: "z0intelligence: From Model Routing to Evidence-Backed Function Routing"
subtitle: "Five days of measurements on whether an automatic router actually executes, actually verifies, and actually saves work — including three falsifications."
study: z0intelligence-function-routing
status: evidence-mixed
mock_data: false
author: "Zer0 Research"
date: "September 27, 2026"
toc:
  - id: false-green
    label: False green
  - id: actual-model
    label: The real model
  - id: nanojev
    label: NanoJev
  - id: functions
    label: Functions, not models
  - id: executes
    label: Physical execution
  - id: saturation
    label: Saturation & k8s
  - id: free-models
    label: Free ≠ useful
  - id: cerebras
    label: Cerebras A/B
  - id: knows
    label: What it knows now
  - id: next
    label: What's next
  - id: methods
    label: Methods
---

<div class="evidence-banner">
  <strong>MIXED EVIDENCE — SOME SOURCES LOCAL-ONLY</strong>
  <span>Verifier quality figures were recomputed from raw per-example JSONL in a pinned revision. Execution, saturation and lifecycle figures are transcribed from frozen receipt cohorts. The router, service and dispatch-authority modules live in an <em>unpublished local revision</em> of z0intelligence (preserved at <code>refs/preserve/20260927/z0intelligence-intelligence-layer-unpublished</code>) and are not yet in canonical main. Provider concurrency caps are <strong>policy inputs</strong>, not reproduced measurements. Every number below is labelled with which of those it is.</span>
</div>

<div class="lede">
We spent five days trying to make z0intelligence pick the right model or function automatically. Most of the value came from things that turned out to be wrong. This is the lab notebook: what we measured, what we falsified, and the one architectural result that survived — that a system should route to an <em>implementation with evidence for an exact function</em>, not to "the best model".
</div>

<div class="hero-rule"></div>

## The false green problem {#false-green}

The first headline to fall was our own.

An earlier automatic-routing batch looked green: outputs came back, the harness reported success, and totals were plausible. Then a fallback serialization bug surfaced in that same batch — and it became clear the harness had been reporting on a path that was not the path that ran.

That batch is still in the evidence set, next to its successor, rather than deleted. The successor (`automatic-routing/20260926T223650Z`) fixed the bug and added the checks the first one lacked: reconcile started and terminal events by call trace id, and verify every output hash against the winning canonical receipt.

The rule we took from it is the spine of everything below:

> **configured ≠ selected ≠ executed ≠ consumed ≠ receipted**

A route being *selected* is not evidence it *executed*. A config entry is not an execution. A model name in a plan is not a provider identity in a receipt.

We use one scale throughout: **SOURCE** (code says the path exists) → **UNIT** (focused test passes) → **RED/GREEN** (fails before, passes after) → **EXECUTION** (a physical call with provider-assigned identity, tokens and latency) → **CONSUMPTION** (a downstream component used the result) → **RECEIPT** (a canonical record exists). A unit test does not prove deployment.

## Testing the actual model from the paper {#actual-model}

Our own first attempt at reproducing the Jev paper tested **proxy models**, not the model the paper used. That is a category error, and stating it is the point: a reproduction of a different system is not a reproduction.

We then ran the real thing: **TypeSafe Jev 1.13.0**, and recomputed from the raw per-example file rather than trusting a shipped summary constant.

| Benchmark | System | n | Family-balanced acc | Macro F1 | ECE (top-1) |
|---|---|---:|---:|---:|---:|
| authored144 | **jev-1.13.0** | 144 | **0.9514** | **0.9518** | **0.0334** |
| authored144 | direct Qwen3.5-4B | 144 | 0.8056 | 0.8002 | 0.0678 |
| authored144 | reranker Qwen3-Reranker-4B | 144 | 0.6319 | 0.5897 | 0.0883 |
| perturbations108 | **jev-1.13.0** | 108 | **1.0000** | **1.0000** | **0.0029** |
| perturbations108 | reranker Qwen3-Reranker-4B | 108 | 0.4907 | 0.4430 | 0.0868 |

The binary abstention slice is where the separation is clearest. Restricting to the `evidence_interpretation` family (n=48, positive = `supported`, score = P(supported)):

| System | n (pos) | AUROC | Balanced accuracy |
|---|---:|---:|---:|
| **jev-1.13.0** | 48 (21) | **0.9982** | **0.9524** |
| direct Qwen3.5-4B | 48 (21) | 0.9894 | 0.8810 |

Those figures reproduce the published report exactly from the raw file. `famBalAcc` and `ECE` likewise reproduce the shipped constants.

**The disclosure that matters.** `perturbations108` scores a perfect 1.0000 — and contains **no `insufficient` gold label at all**. Its gold ids are `contradicted / supported / prohibited / permitted / A / B`. It is therefore missing the hardest class in `authored144` (36 of 144 rows are `insufficient`). A perfect score on a set that omits the hardest case is not evidence of general abstention ability, and we do not present it as such.

**Why the original target was wrong.** We had targeted a **146:4 AbstentionBench slice**. It is not present in this checkout — and it was a poor primary reproduction target anyway: at a 97% majority class, a single accuracy number is dominated by the majority, and the slice does not exercise the three-way `supported / insufficient / contradicted` contract the runtime actually routes on. We abandoned it as the primary target rather than report a flattering number from it.

## Why NanoJev failed {#nanojev}

NanoJev looked like a win: ~31 ms p50 on CPU, interface-compatible with our decision contract, and an initial AUROC that pointed the right way.

It does not work, and the reason is worth keeping.

The checkpoint (`C-Tianyu/NanoJev @ 4a19595e`) was trained on **Maze, Snake, ViZDoom Basic and Predict Position** — action-choice tasks, with a "complete-question categorical cross entropy" over an offered candidate set. The publisher's own model card describes boolean and ordered-score support as an *interface affordance*, never a training objective. The local config corroborates: dataset `research/private_navigation_v3/views/coords_multi.jsonl`, `set_head: "attention"`, objective `teacher`. (The trainer is not in any branch of the repo — we searched every ref and `git log --all -S` — so the objective is established from the publisher's recipe and config, not a local trainer.)

Then the mathematical problem. The `choice` path encodes one candidate text per option and runs the trained attention set head. The **`boolean` path does not**: it builds `candidate_ids = ("false", "true")` with a *single* candidate text, is excluded from the attention head, and pads with a degenerate contrast — the first logit is multiplied by zero:

```python
out.append(F.pad(torch.stack([z[i, 0] * 0, z[i, 0]]), (0, kmax - 2)))
```

`false` is fixed at zero. That is not a measured probability; it is a constant.

**Correcting the contrast removed most of the apparent signal.** The target ordering was inverted. Integration stopped.

> **Fast ≠ suitable objective.** Interface compatibility is not capability equivalence. A model can fit the shape of your API and be trained to answer a different question entirely.

## Functions, not models {#functions}

The architectural conclusion from the falsifications above: stop asking a global question.

A **model router** asks *"which model is best?"* — a question with no stable answer, because "best" depends on the function, and the evidence for one function rarely transfers to another.

z0intelligence now asks:

> **"Which implementation has evidence for this exact function?"**

The chain is `function → capability evidence → candidate implementation → execution`. Concretely, as configured today:

| Function / situation | Route | Basis |
|---|---|---|
| Evidence sufficiency | **Jev** (`JEV_FUNCTION`) | evaluated choice contract on authored144/perturbations108 |
| Experimental fast verification | **Laya** (`LAYA_FUNCTION`) | bounded evidence-sufficiency tests, opt-in only |
| Bounded worker work | provider router (`REMOTE_MODEL`) | free-only allowlist + admission |
| Tiny or unproven task | **`PARENT_ONLY`** | no admissible evidence of benefit |
| Context shaping | SolPi | in-turn, host-side |
| Decomposition | RLM | host-side |

Two entries need their caveats stated in the same breath as their capability:

**Laya** — a 421M model at ~28 ms warm typical latency. It passed the bounded evidence-sufficiency tests, but it has **known paraphrase/generalization caveats**: on three controlled packets across three phrasings it separated supported/ambiguous/unsupported correctly (3/3 phrasings, spread 0.42) but with phrasing sensitivity of ~0.025 and a measured classification distribution that leaves it unsuited to be a universal verifier. It is **FAST_PATH / experimental**, not a general-purpose verifier.

**`PARENT_ONLY`** is a real routing outcome, not a failure. Its recorded reason on a tiny task: *"DO_NOT_DELEGATE: tiny/unknown task size; observed tiny-task offload added 1347 uncached parent tokens."*

## Routing that physically executes {#executes}

Selection is cheap. Execution is the claim that needs proof.

One batch returned **20/20 outputs, with 6 distinct providers completing real work** across **25 physical attempts and 5 successful fallbacks**:

| Provider | Model | Tasks |
|---|---|---:|
| cerebras | qwen-3.8-27b | 7 |
| groq | openai/gpt-oss-20b | 3 |
| deepseek | deepseek-chat | 3 |
| grok | grok-4.20-0309-non-reasoning | 2 |
| nous | inclusionai/ling-3.0-flash-sante:free | 2 |
| nvidia | openai/gpt-oss-20b | 2 |
| local | qwen2.5:3b | 1 |

Measured usage: **2,126 input + 1,440 output tokens**. Five rejected attempts supplied no usage and are excluded from that total rather than silently counted as zero-cost.

Fallbacks are load-bearing and were tested with a real failure: an invalid test-process Groq credential produced a **real HTTP 401**, after which **Cerebras returned the expected output**. OpenRouter and Vercel likewise produced real 403s followed by successful Cerebras calls. Shared credentials were not modified.

**A caution on our own estimate.** That report also computes "estimated Codex-parent tokens avoided: 1775". That is a same-text UTF-8-bytes/4 baseline — **not** a measured counterfactual, not a net saving, and not dollars. We keep it labelled as an estimate because the section below shows why the real measurement can go the other way.

The harness route matrix from the same period, run as four concurrent HTTP clients:

| Client | Route | Provider / model | Receipt latency | Tokens in/out |
|---|---|---|---:|---:|
| codex | `JEV_FUNCTION` | typesafe / jev-1.13.0 | 572.0 ms | 377/48 |
| hermes | `LAYA_FUNCTION` | local / laya_421m | 14141.7 ms | 59/0 |
| dsh | `REMOTE_MODEL` | cerebras / qwen-3.8-27b | 758.9 ms | 133/664 |
| omp | `PARENT_ONLY` | parent / current Codex | 181.4 ms | 0/0 |

Two readings of that table are wrong and we flag them: the Laya receipt latency includes **cold import/load** (its inference alone was 568.9 ms), and `PARENT_ONLY`'s 181.4 ms is **dispatch only** — it does not certify parent completion. The four labels are HTTP clients, not claims of installed integration; installed-integration proof is separate and uses the real extension loaders.

## Provider saturation and Kubernetes {#saturation}

The architecture result that survived everything:

> **many stateless executors → one canonical authority**

One authority owns identity/fingerprint CAS, ordered canonical receipt writes, stored-result replay, and provider admission. Executors hold **no ledger** and cannot take over an uncertain execution. The router consumes a prepared snapshot and stays pure.

Three idempotency rules, all three verified with a real pod replacement:

| Rule | Behaviour | Status |
|---|---|---|
| completed duplicate | **replay** stored result | verified |
| same trace, different request | **reject** (HTTP 400, no second physical execution) | verified |
| uncertain prior execution | **refuse** re-execution | verified |

**Admission control, measured.** 64 concurrent requests from two stateless OS processes against the production authority HTTP protocol: **32 admitted, 32 capped before provider HTTP, peak inflight 32, 32 released.** The fixture is a counted local HTTP server — this is an admission-semantics test, *not* 64 paid provider calls and *not* two Kubernetes replicas.

**Now the honest part about the caps.**

| Provider | Cap | Provenance |
|---|---:|---|
| cerebras / deepseek / jev | 32 | **policy input** |
| groq | 16 | **policy input** |
| nvidia | 12 | **policy input** |
| local | 1 | policy input (serialization behaviour verified separately) |
| openrouter / vercel | 0 → later 1 / 8 | policy input from exported health evidence |

These are **not measurements we reproduced**. The saturation report says it plainly: the caps come from an operator handoff, and *"its referenced ~330-probe report was not independently recovered or reproduced here."* We are repeating that limitation rather than laundering policy inputs into measurements.

Accordingly, per-provider headroom — "Cerebras has large headroom", "Groq hits a wall", "NVIDIA walls lower" — is marked **`UNKNOWN`** in this study's data. The one per-provider concurrency behaviour we did measure is local serialization: **two simultaneous local requests produced one real Ollama call and one refusal before HTTP**, final inflight 0.

**Kubernetes.** The lane is a single replica with a Service/EndpointSlice; the host service is supervised by an enabled user systemd unit, and **SIGKILL recovery restored readiness in 3.28 seconds** (reboot was not tested). A 12-request burst across harness identities returned **4 successes and 8 explicit HTTP 503 backpressure** responses, peak dispatch concurrency 4 — backpressure, not an unbounded queue.

An early state had the pod failing readiness because pod-to-host TCP to `172.19.0.1:11501` timed out. The cause was not a missing listener: the listener was already bound, UFW was active, and the Kind network's first IPAM entry is IPv6 — so selecting entry zero alone would give the wrong address family. One persistent, scoped UFW ingress rule on the Kind bridge fixed it, with a recorded rollback. After the repair the EndpointSlice went `ready=true`.

**Why this matters more than a benchmark number:** scaling z0intelligence without saturation awareness multiplies 429s and 503s. There is no autoscaler here, deliberately — the lane is a proxy to one host process with no Deployment scale target, and KEDA and the metrics API are absent. **Scaling a proxy would not increase model capacity.**

## Free models are not automatically useful {#free-models}

A route being free is not evidence it is useful. We proved the free path executes anyway, because "it's free" is exactly the kind of claim that hides a non-execution.

Real free execution on `openrouter / nvidia/nemotron-3-super-120b-a12b:free`:

| Field | Value |
|---|---|
| Public task | Reply with 42 |
| Returned output | `42` |
| Provider-reported cost | **$0.00** |
| Tokens | 55 input, 38 output (provider usage) |
| Receipt latency | 790.449 ms (one observation) |
| Canonical dispatch receipt | `dispatch-e1ebc20eb79f199391a5826304677e5e85951efa9be042b2acad1c3cece5fccc` |
| Readiness | HTTP 200, Kubernetes Ready, 1/1 replicas |
| Replay | stored output after pod replacement; exactly **one** canonical physical start/completion |
| Conflicting fingerprint | HTTP 400, **no** second physical execution |

This was enforced, not merely configured: `free_only: true` with a single exact provider/model allowlist entry, `provider.max_price` ceilings of 0, provider fallback disabled, and enforcement at candidate selection, immediately before execution, and independently in authority claim/admission. A caller passing `free_only: false` cannot weaken it. A **reported nonzero cost cannot count as successful free execution** — which is precisely why Vercel stayed excluded despite having free credit: a successful response reported $0.00000738. Free credit is not a zero-priced route.

One defect was found and fixed here: the executor initially translated the authority's **correct conflict rejection** into HTTP 503. The authority had refused and did not execute, so no incorrect execution occurred — but a misleading status code is a correctness bug in its own right. It was corrected, tested, and the final proof reused the same trace without another provider call.

Also worth noting: **the automatic decision point being enabled is not the same as automatic offload being enabled.** OMP is the only enabled automatic harness, and its real `ExtensionRunner.emitBeforeAgentStart` path called the service and consumed the decision — returning `PARENT_ONLY` with native behaviour preserved, because there was no eligible integrity-checked quality evidence. Transport validation was deliberately not promoted into function-quality evidence.

## Cerebras: great worker, no token savings yet {#cerebras}

This is the most important negative result we have.

Two cohorts exist, and the difference between them is a configuration failure we preserve rather than hide:

| Cohort | Completed | Outcome |
|---|---:|---|
| default/high reasoning | **4 / 60** | all 4 exhausted the 2048-token completion budget with empty output — **configuration failures, excluded, not pooled** |
| `reasoning_effort=none` | **60 / 60** | the measured cohort below |

On the reasoning-disabled cohort — 30 repeats each of two public implementation tasks, temperature 0, frozen throughout:

| Measure | Parent only (A) | Delegated (B) |
|---|---:|---:|
| Uncached parent input | 325,894 | 396,074 |
| Parent output | 32,681 | 31,065 |
| Cached parent input | 884,480 | 861,056 |
| **Uncached input + output** | **358,575** | **427,139** |
| Worker input / output | 0 / 0 | 15,960 / 44,220 |

The worker itself was excellent: **60/60 raw worker quality, zero required repairs or fallbacks**, physical latency **p50 625 ms / p95 1,149 ms**, paired added latency mean 0.751 s (p50 1.080 s).

**And parent work went up, not down.** The raw aggregate adds **+68,564** parent tokens — but unequal cache hits confound that, so we decomposed it: +46,756 total parent input, −1,616 output, −23,424 cached input. **Removing the cache imbalance algebraically still leaves +45,140 input/output tokens.** That is a sensitivity analysis, not a measured uncached saving.

Stratifying by equal cache state makes the direction unambiguous:

| Task | Equal-cache pairs | Mean parent token delta | Bootstrap 95% |
|---|---:|---:|---|
| Report summary | 12 | **+522.1** | +506.0 to +536.4 |
| Evidence gate | 8 | **+1,008.1** | +959.1 to +1,063.6 |

Both tasks increased parent work. The decision was therefore: **keep automatic generic-worker delegation ineligible.**

Two disclosures we will not smooth over. First, parent final passes were `30/30` on summary but **`30/28` on gate** — the original grader rejected two B-arm outputs for using a numeric `as_integer_ratio`; `grading-v2/` preserves that correction separately and **no inference was rerun**. Second, billing is `trial_or_existing_credit_unverified`: the API did not report cost on the initial calls, so we claim **no measured $0 and no dollar savings**.

The hypothesis that follows:

> **Delegation cannot save parent tokens when the parent still consumes the original task plus a verbose worker response.**

At these task sizes the worker's output is an *addition* to parent context, not a replacement for parent work. That reframes the whole problem: the lever is not a better worker model, it is a **typed or compressed worker artifact** that replaces parent work instead of appending to it.

The same pattern showed up independently with Nemotron (2 pairs): **+501** and **+38** uncached parent input, wall time **+15.73 s** and **+24.17 s**, with the summary requiring parent repair and the gate requiring native fallback. It also remained `eligible=false`. Its worker output did contribute — the reviewed B-arm implementation is what produced its own report — and that is precisely the distinction: **contribution is not savings.**

## What z0intelligence knows now {#knows}

| Dimension | What is established | Evidence level |
|---|---|---|
| Capability (Jev) | 0.9514 famBalAcc / 0.9982 AUROC on binary abstention | recomputed from raw |
| Capability (Laya) | bounded tests pass; paraphrase caveats | unit + controlled packets |
| Routing correctness | function → evidence → implementation, with `PARENT_ONLY` as a first-class outcome | execution |
| Execution | 6 providers, physical calls, canonical receipts | execution + receipt |
| Latency | measured per provider and per route | execution |
| Calibration | Jev ECE 0.0334 / 0.0029; NanoJev falsified | recomputed from raw |
| Token/offload economics | delegation **increased** parent work on both cohorts | measured |
| Concurrency | 32 admitted / 32 capped; 4-success-8×503 backpressure; local serializes | measured |
| Durability | replay, conflict rejection, refusal; SIGKILL recovery 3.28 s | execution |
| Production readiness | **bounded** — local-only router revision, single replica, no autoscaler, unverified billing | — |

`UNKNOWN` in this study, stated rather than filled: per-provider headroom, any task size where delegation reduces parent work, dollar savings, reboot availability, and Nemotron/Laya general quality beyond small samples.

## What we test next {#next}

1. **Typed/compressed worker artifacts.** The measured failure is that verbose worker output adds to parent context. Test whether a typed artifact that *replaces* parent work flips the sign, on a preregistered, size-stratified task set with controlled cache exposure and held-out tasks.
2. **A larger text-worker slice where parent verification is cheap.** Nemotron's own conclusion: demonstrate function quality *and* measured end-to-end benefit before enabling automatic offload.
3. **Router to canonical.** Promote the unpublished intelligence layer through repo policy so these results are reproducible from public commits.
4. **Independently reproduce the provider caps.** Replace policy inputs with measurements, and keep `UNKNOWN` until then.
5. **A held-out abstention set with an `insufficient` class.** `perturbations108` cannot carry that claim.

## Methods and evidence discipline {#methods}

Consolidation work ran alongside the evaluations and changed what we could trust:

- Canonical branches were advanced for **AODL**, **Evolution Lab** (new `trunk` from the real lineage), **z0intelligence** and **Kerdoios**, each through repo-native policy.
- **Preservation preceded consolidation.** Every unique lineage — including untracked files that `git stash create` cannot capture — was pinned to pushed preserve refs and verified byte-for-byte before anything moved.
- **Patch-id plus tree/content comparison, both directions.** Patch equivalence is necessary but not sufficient: a branch read as "genuinely new" by patch-id had in fact already landed under a rewritten SHA *with an extra fix on top*, so no patch-id could ever match.
- **Semantic conflicts exist even when Git merges cleanly.** A skill from an older branch merged without a textual conflict and still violated a newer frontmatter contract.
- **The canonical validation runtime is Python 3.11.** The repository declares `.python-version: 3.11` and `requires-python = ">=3.10,<3.14"`. Earlier suite counts in this programme were taken on **Python 3.14, outside the declared support range, and are not used as final evidence**. On the declared runtime with all requirements installed the suite is **457 passed, 3 skipped, 0 failed**; the five failures seen before that were missing-package gaps, not regressions (four needed `laya`, present in `requirements.txt` but absent from `pyproject.toml` dependencies; one needed `jevkit`, undeclared in both).
- **The repo-native test runner matters.** Running `pytest` against a suite whose declared runner is `unittest` produced 142 errors on a healthy repo. Separately, a schema cross-check in another repo *silently skips* when an optional dependency is absent, reporting success while verifying nothing.
- **Evidence receipts are bound to exact PR heads**, and one repo requires linear history — so a merge commit is not merely discouraged, it is rejected.
- We also corrected a published error of our own: a "reclaimable modules" count from an earlier inventory generalised from a single consumer and ignored the package `__init__` chain. The corrected verdict is that the package is entirely live. It is corrected in place rather than quietly dropped.

Raw sources for every figure above: the frozen receipt cohorts under `/home/kvn/Documents/ChatGPT/z0/receipts/`, the pinned capability-evidence JSONL in the preserved z0intelligence revision, and the transcribed data files in `studies/z0intelligence-function-routing/data/`. Where a receipt disagreed with an earlier prose number, the receipt won.
