# Contributing to z0evals

z0evals is the frozen evidence and publication layer for the Zer0 ecosystem. Project-specific evidence rules in `AGENTS.md` take precedence over generic contributor conventions.

This repository uses the [Verified OSS Loop](https://github.com/kvnloo/verified-oss-loop) with the **stable** rollout scheme.

## Contribution loop

1. Search open issues and pull requests.
2. Work only on a maintainer-triaged `claimable` issue, then take one bounded 24-hour claim.
3. Run `python3 .verified-oss-loop/rollout.py show`. For this repo it should resolve to `worker_base=main` and `feature_target=main`.
4. Use an isolated branch/worktree.
5. Orient before editing. For executable changes, fail then pass. Keep the smallest complete change.
6. Open a PR with the exact-head evidence receipt from `.github/PULL_REQUEST_TEMPLATE.md`.
7. Independent review is required. Workers never merge `main`.

## Evidence rules

A publication or study contribution must preserve the distinction between source-reported claims, reproduced measurements, model predictions, execution completion, and independently verified outcomes.

Public imports must be explicitly allowlisted from immutable source revisions. Do not publish private prompts, credentials, personal traces, local environment files, or raw private runtime directories.

## Commands

```bash
python3 .verified-oss-loop/rollout.py show
python scripts/validate.py
python scripts/build_site.py
```

Mutation testing is `n/a` for the current Python publication/validation surface. Do not invent a mutation score.

Kit skills live under `.verified-oss-loop/skills/` because z0evals keeps its own root `AGENTS.md`.
