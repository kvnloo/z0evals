# Causal-ablation evidence audit, v0

Issue: https://github.com/kvnloo/z0evals/issues/75

## Finding

**Attribution remains unresolved.** The existing Phase 1B publication contains enough data for four same-model compiler/unfiltered descriptive contrasts, but not for an independent verified-outcome causal study. This audit does not run an experiment or promote any runtime policy.

All four contrasts cover exactly the same 28 state IDs. Each state's repeated attempts stay together and contribute one equally weighted state mean; 84 attempts are not 84 independent work items. A missing arm/state or duplicate state is an error, rather than permission to select a favorable intersection.

Source-reported correctness differences (compiler minus unfiltered):

| Backend | Groups in both arms | Difference |
|---|---:|---:|
| Hammer2.1 3B | 28 | +7.14 percentage points |
| Nemotron Orchestrator 8B | 28 | -10.71 percentage points |
| Qwen3.5 4B | 28 | 0 percentage points |
| Qwen3.5 9B | 28 | 0 percentage points |

These are recomputed source-label contrasts, not reproduced model measurements or independently verified task outcomes. The negative Nemotron contrast and two null contrasts are retained. No statistical significance, independent trial count, randomized assignment, or matched counterfactual is claimed. Equal state IDs alone do not establish shared real-world work-item lineage or absence of training leakage.

## Evidence boundary

The exact input bytes are pinned by SHA-256 in `data/phase1b-audit.json` and by the full z0evals source commit in `manifest.yaml`. Original runtime source revisions/configuration remain incompletely pinned in the older `slm-router-v0` manifest; pinning this publication copy does not repair that missing provenance.

- Unit of this audit: **state ID**, not attempt/repetition
- Actual train/evaluation folds: **unknown**
- Real work-item/retry/continuation lineage: **unknown**
- Label-generator identity: **unknown**; the corpus supplies `correct`/`goldAction`, not a sealed independent judge identity
- Independent verifier and verified task outcome: **unavailable**
- Attribution evidence level: **observational** (descriptive grouping of source-reported labels)
- Money: every compared arm has **0/84 known costUsd readings**; totals remain null
- Decision latency and input/output tokens: recorded separately with known/expected measurement counts; incomplete vectors have null totals
- Quality and coverage: source correctness, 28/28 state coverage, attempt count and unknown independently verified success are separate fields

A successful trajectory cannot upgrade any of these fields. JEV/NanoJev/teacher agreement is not independent truth.

## Smallest next discriminating study

Freeze one public allowlisted work-item cohort before running any arm. The experimental unit is the original `work_item_id`; every retry, correction, continuation, branch, and attempt inherits that group's single fold. A grouped holdout manifest must list those assignments and be hash-pinned before evaluation. Do not use state IDs as substitutes unless lineage is independently established.

| Planned arm | Intervention | What must remain fixed |
|---|---|---|
| Full system | None | Frozen work-item groups, environment, allowed actions, outcome contract |
| Retrieval/state ablation | Remove one retrieval/state contribution at a time | Same policy/model/tool/verifier; log exactly which evidence was withheld |
| Policy/router ablation | Bypass the candidate router with the declared simple policy | Same evidence/state/model/tool/verifier |
| Stronger generic policy | Declared generic-policy baseline | Same groups, allowed actions and total budget |
| Independent outcome control | Re-evaluate all arms using a sealed outcome assessor | Assessor identity/revision, blind inputs, separation from label generation |
| Paired replay, only if valid | Replay the declared counterfactual | Same initial state and external responses; record non-replayable effects |

This is a plan, not six executed arms. Before importing results, require:

1. Full immutable source revisions for runtime, model/checkpoint, policy and verifier; config and cohort hashes; exact intervention definition
2. One group assignment for every related attempt across all arms, with exclusions fixed before outcomes and missing coverage reported
3. Explicit label generator and outcome verifier identities; document whether they share a model, prompt, training data or answer key
4. A contamination audit of train/test lineage and whether evaluation evidence entered retrieval or policy training; unknowns block causal wording
5. Per-group independent outcome (success/failure/inconclusive), coverage and a cost vector with missingness, including retries/escalations
6. Predeclared estimand and assignment/control assumptions; report negative, null and inconclusive effects as readily as positive ones

Credit ladder: observational data support association; a controlled component removal supports a bounded ablation claim; valid matched replay supports a paired counterfactual claim. Causal language additionally requires defended identification assumptions. No automatic numeric credit award is added here. If simple paired ablations settle the actionable question, stop there.

## Reproduce

```bash
python3 scripts/analyze_causal_ablation.py > /tmp/phase1b-audit.json
cmp /tmp/phase1b-audit.json studies/causal-ablation-v0/data/phase1b-audit.json
python3 -m unittest discover -s tests -p 'test_causal_ablation.py' -v
python3 scripts/validate.py
```

Evolution Lab still owns experiment execution/training; Tokenomics owns measurements/outcomes; z0intelligence owns promotion. This repository only audits the frozen public evidence. There are no model calls, production changes, or new training/scheduler systems.
