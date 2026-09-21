---
title: "How z0evals Fits Into Zer0"
subtitle: "A federated evaluation layer built from the fixtures and contracts the rest of the ecosystem already owns."
study: ""
status: architecture
author: "Zer0 Research"
date: "September 21, 2026"
mock_data: false
toc:
  - id: principle
    label: Principle
  - id: ownership
    label: Ownership
  - id: suites
    label: Suites
  - id: ladder
    label: Eval ladder
  - id: leakage
    label: Holdouts
  - id: promotion
    label: Promotion
---

<div class="lede">
z0evals is not another benchmark repository and it is not another runtime. It is the place where independently owned Zer0 contracts, fixtures, holdouts, measurements and system revisions are composed into frozen evaluations that can be reviewed, reproduced and published.
</div>

<div class="hero-rule"></div>

## One rule: do not copy the oracle {#principle}

Every Zer0 repository keeps authority over the behavior it actually owns. z0evals references those sources by immutable revision and composes them into a suite.

<div class="pullquote">The fixture stays with the repo that owns the semantics. z0evals owns the cross-repo question.</div>

That means a safety rule does not become a second JSON fixture in z0evals just because an evaluation needs it. If the rule is structural, it belongs in AODL. If it is about measurement or verified outcomes, it belongs in Tokenomics. If it is a learned-policy benchmark, it belongs in z0intelligence. z0evals pins the exact source revision and asks whether the whole system still satisfies the combined contract.

## Who owns what? {#ownership}

| Repository | Owns | z0evals consumes |
| --- | --- | --- |
| **AODL** | Typed intent, plan legality, authority and compiler rules | valid / invalid / compile-stop fixtures and compiler verdicts |
| **Tokenomics** | Measurement semantics, experiment identity, cost/latency/token fields, verified outcome semantics | event/outcome schemas, conformance fixtures and receipts |
| **z0intelligence** | Model/tool policy, decision backends, model benchmark corpora and row-level outputs | candidate systems, metric contracts and cognition fixtures |
| **Evolution Lab** | Experiment search, training, mutation and locked train/val/confirm/OOD splits | frozen experiment artifacts plus protected confirm/OOD holdouts |
| **Kerdoios** | Compute/provider/resource placement | placement candidate under test and resource observations |
| **OMP / Hermes** | Runtime execution, tool lifecycle, approvals and retries | real execution surface and trace identity |
| **frontier-kb** | External research evidence | references and prior-art context, never runtime truth |
| **z0evals** | Cross-repo suite composition, certification, regression detection and publication | immutable references to all of the above |

<div class="figure-card">
  <div class="figure-head"><div><span class="eyebrow">Architecture</span><h3>One evaluation, many owners</h3></div></div>
  <pre><code>AODL ─────────────┐
Tokenomics ───────┤
z0intelligence ───┤
Evolution Lab ────┤──→ z0evals ──→ frozen result / KEEP · DISCARD · PARTIAL
Kerdoios ─────────┤
OMP / Hermes ─────┘                       │
                                          ├──→ public study / figures
                                          └──→ promotion evidence</code></pre>
  <div class="figure-foot">The arrows are references and evidence flow. They are not ownership transfers.</div>
</div>

## Suites bind exact revisions {#suites}

A reusable suite should be small. It names the upstream repositories, pins each one by immutable SHA, selects the relevant fixture paths, and defines the gates that must pass.

```yaml
schema: z0eval.suite.v1
id: local-router-v1

sources:
  - repo: kvnloo/aodl
    revision: <40-char-sha>
    role: legality
    include:
      - examples/valid/fanout-fanin.json
      - examples/invalid/dependency-cycle.json
      - examples/invalid/hidden-privilege.json

  - repo: kvnloo/tokenomics
    revision: <40-char-sha>
    role: measurement
    include:
      - fixtures/conformance.json
      - fixtures/z0int_receipt.json
      - spec/semantic-conventions.yaml

gates:
  - contract_conformance
  - authority_safety
  - verified_quality_noninferiority
  - latency_tail
```

z0evals materializes those revisions into a local cache or temporary worktrees. The published result records the exact suite revision, system revision, baseline revision, evidence hashes and limitations.

## Evaluation gets progressively more expensive {#ladder}

<div class="metric-grid">
  <div class="metric"><span class="metric-label">L0</span><strong>contracts</strong><small>deterministic conformance</small></div>
  <div class="metric"><span class="metric-label">L2</span><strong>trajectory</strong><small>real cross-stack execution</small></div>
  <div class="metric"><span class="metric-label">L4</span><strong>canary</strong><small>longitudinal regression</small></div>
</div>

**L0 · Contract and conformance.** AODL valid examples compile, invalid or compile-stop examples fail correctly, Tokenomics events validate, treatment hashes stay stable and artifact hashes match.

**L1 · Component behavior.** z0intelligence, Kerdoios, JEV/OpenJev, OMP adapters and other components are evaluated on fixtures owned by their home repository.

**L2 · Cross-stack trajectory.** A legal AODL state flows through policy, placement, execution, Tokenomics and an independent verifier. Schema validity and trajectory correctness remain separate metrics.

**L3 · Frozen confirmation / OOD.** Protected work-item and task-family holdouts form the promotion and regression firewall.

**L4 · Shadow / canary.** The current champion and challenger are compared on real traffic without changing the definition of success underneath them.

## The evaluator must stay outside the training loop {#leakage}

Evolution Lab can continuously learn from training data and real receipts. z0evals should normally certify on protected `confirm` and `ood` groups that are not ordinary training inputs.

<div class="figure-card">
  <div class="figure-head"><div><span class="eyebrow">Anti-overfitting boundary</span><h3>Continuous learning, discrete certification</h3></div></div>
  <pre><code>live receipts + train / val
          │
          ▼
   Evolution Lab
          │
     challenger
          │
          ├──────────────┐
          │              │
          ▼              │
 protected confirm / OOD │
          │              │
          ▼              │
       z0evals            │
          │              │
   KEEP / DISCARD / PARTIAL
          │
          └──→ promotion evidence</code></pre>
  <div class="figure-foot">A failed challenger does not get to repeatedly train on the protected exam it just failed.</div>
</div>

This is especially important for Q-Route and continuous distillation. The router can keep getting cheaper and faster, but the regression firewall must remain sufficiently independent to detect real degradation.

## z0evals certifies; it does not promote {#promotion}

A z0eval run should produce a small result receipt that references the underlying evidence instead of re-defining it.

```yaml
schema: z0eval.result.v1
suite_id: local-router-v1
suite_revision: <sha>
system_revision: <sha>
baseline_revision: <sha>
verdict: KEEP

gates:
  contract: pass
  authority: pass
  quality_noninferiority: pass
  latency_tail: pass

evidence:
  tokenomics_artifacts: [...]
  source_artifacts: [...]
  result_hashes: [...]

limitations: []
```

z0intelligence or Evolution Lab may consume that result when deciding whether a challenger is eligible for shadow, canary or promotion. z0evals itself never becomes production routing authority.

<div class="method-card">
  <span class="eyebrow">Verified OSS Loop</span>
  <h3>Changing the evaluator is changing the oracle.</h3>
  <p>Suite definitions, holdout selection, schemas, adapters and regression thresholds deserve stronger review than presentation-only changes. z0evals uses the rolling Verified OSS Loop channels while keeping dev and main maintainer-gated.</p>
  <a href="https://github.com/kvnloo/z0evals/issues/5">Architecture tracker #5 ↗</a>
</div>
