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
