# SLM Router v0

Status: **draft**

This study freezes the first local tool-calling / model-routing experiment for the Zer0 stack.

## Questions

1. Which local SLM is most effective for bounded tool/model routing on the target RTX 3080 Ti?
2. How much safety and reliability comes from the model versus the deterministic compiler/legal-action filter?
3. Where does a dedicated tool-calling specialist beat a larger general model?
4. What benchmark is still required to validate Nemotron-Orchestrator for its intended multi-turn orchestration role?
5. Can these receipts become a training corpus for a progressively distilled Q-Route policy?

## Planned evidence

The initial DSH run already produced candidate evidence for local serving, adversarial tool-choice fixtures, schema-valid versus trajectory-correct outcomes, compiler-first safety comparison, the Evolution Lab composition harness, role-specific routing conclusions, and explicit missing experiments.

The public study will import only artifacts explicitly selected from pinned local commits.

## Directory contract

```text
manifest.yaml   immutable source/provenance metadata once frozen
data/           public machine-readable results / fixtures
analysis/       scripts used to derive tables/claims
figures/        generated public figures
notes.md        working interpretation and limitations
```

Do not put mutable runtime state here.
