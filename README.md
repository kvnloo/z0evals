# z0evals

Reproducible evaluations and public research reports for the Zer0 ecosystem.

z0evals is the **frozen evidence/publication layer**. It does not run production routing, own runtime policy, or replace the experiment engines that produce candidate systems.

## Ownership

```text
frontier-kb      external evidence / literature
       │
Evolution Lab    experiment design + execution + training
       │
Tokenomics       neutral measurements / receipts / verified outcomes
       │
z0evals          frozen datasets + analysis + figures + public reports
       │
z0intelligence   promotion / shadow / canary decisions
       │
Kerdoios         resource placement among allowed candidates
```

A study enters z0evals only after its input revisions are pinned and its results can be reproduced or independently inspected.

## First study

`studies/slm-router-v0/` is reserved for the local SLM routing study produced from the September 2026 z0intelligence / Evolution Lab work.

The initial report will investigate:

- compiler-first legal-action filtering
- FunctionGemma, Hammer 2.1, Nemotron-Orchestrator and Qwen routing behavior
- latency / quality / GPU tradeoffs on an RTX 3080 Ti
- bounded tool choice versus authentic orchestration
- the basis for a continuously distilled Q-Route policy

## Layout

```text
studies/    frozen study manifests, analysis notes, public data and figures
posts/      publication-ready narratives derived from studies
schemas/    versioned contracts
scripts/    import, validation and site-generation helpers
site/       generated GitHub Pages output
```

## Importing a local DSH result

Do **not** push a whole local worktree or private trace directory.

Use an import spec that pins the source repository and commit, and explicitly allowlists each artifact to publish:

```bash
python -m pip install -r requirements.txt
python scripts/import_local.py imports/slm-router-v0.local.yaml
python scripts/validate.py
```

See `imports/slm-router-v0.example.yaml`.

## Engineering efficiency, not activity counts

`scripts/engineering_eval.py` evaluates an existing
`tokenomics.paired_cost_study.v1` document. It reuses the original pinned
[Tokenomics cost-displacement report](https://github.com/kvnloo/tokenomics/pull/21);
it does not add routing, a replay store, a trainer, or another protected judge.

```bash
python -m pip install -r requirements.txt
python scripts/engineering_eval.py \
  studies/engineering-throughput-v0/data/iac-collection-v2.study.json
```

The report separates verified-result rate, all work per verified result,
setup/search/training time, p50/p95/p99 workflow latency, tokens, retries,
tool/network calls, human interventions, and measurement coverage. Failed work
stays in the cost numerator. Missing telemetry stays unknown. Additive trace
work is not parallel elapsed time.

For measured end-to-end inputs, set `engineering.wall_time_scope` to
`request_through_verification`. Each named arm supplies `setup_wall_ms`,
`optimization_wall_ms`, and optionally `cohort_elapsed_ms` as explicit
`value`/`measurement_state`/`attribution: trace_total`/`evidence_ref` observations.
Zero must be observed, not inferred. Throughput additionally requires
`cohort_time_scope: setup_through_last_verification` and a coherent elapsed
clock. Unknown optimization costs prevent a first-use efficiency claim.
`--out PATH` creates a new aggregate file and refuses to overwrite it.

The [dogfood study](studies/engineering-throughput-v0/manifest.yaml) retains:

- A faster but rejected all-probe IaC candidate that lost package inventory.
- A repaired service-only concurrent collector with all sixteen probes and
  equivalent fresh package/CPU/mount facts. The original confirmation failed
  against stale host state; retrospective equivalence is not a preregistered
  success. Recorded CLI timing is not independently verified-result latency.
- A distinct prospective v3 confirmation, registered before new observations,
  that preserves the bounded package/CPU/root-mount contract and measures
  request-through-that-verifier latency. Remaining failed component probes
  stay visible; this is not full-host or general engineering non-inferiority.
- A six-call, zero-reported-cost public-code diagnostic across Beam, Laguna XS,
  Solar Mini4 and Step 3.7. Exact-object compliance and factual usefulness are
  distinct; post-hoc checks cannot replace the original result.

The evaluator emits `quality_regression` for the rejected collector,
`insufficient_measurement` for the incomplete/replayed and first-use comparisons,
and `lower_observed_work_time` for the fresh, bounded v3 workflow only.
It does **not** manufacture a KEEP decision, global speedup or adoption approval.

This implements the measurement direction in [#93](https://github.com/kvnloo/z0evals/issues/93),
[the GEPA/RSI/SFT proposal](https://github.com/kvnloo/z0intelligence/issues/143#issuecomment-6139105175),
and [the recurring latency investigation](https://github.com/kvnloo/z0intelligence/issues/139).
Compare deterministic/manual controls before spending on search or training.
Those optimizers remain Evolution Lab's responsibility; protected truth and
PR95's independent custody/lineage gates remain unchanged.

## Rules

1. Every claim in a post should resolve to a frozen study artifact.
2. Source-reported benchmark numbers and our reproduced measurements are different fields.
3. Raw secrets, credentials, personal traces and private prompts never enter this public repository.
4. Training/evaluation splits must preserve work-item lineage.
5. The system that generated a label cannot silently become its own verifier.
6. A study may report an incomplete or negative result. Do not hide failed hypotheses.

## Related repos

- https://github.com/kvnloo/z0
- https://github.com/kvnloo/z0intelligence
- https://github.com/kvnloo/evolution-lab
- https://github.com/kvnloo/tokenomics
- https://github.com/kvnloo/kerdoios
- https://github.com/kvnloo/frontier-kb
