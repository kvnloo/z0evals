# AGENTS.md

## Purpose

z0evals is Zer0's public, reproducible evaluation and research-publication layer.

## Hard boundaries

- **Evolution Lab** owns experiment/search/training machinery.
- **Tokenomics** owns neutral runtime measurements and verified-outcome semantics.
- **z0intelligence** owns runtime cognition/promotion policy.
- **Kerdoios** owns resource placement.
- **frontier-kb** owns external research evidence.
- **z0evals** freezes evidence and publishes conclusions.

Do not move production behavior into this repository.

## Evidence invariants

1. Pin every source repository by immutable commit SHA.
2. Public artifacts are allowlisted, never copied recursively from a local worktree.
3. Never publish secrets, credentials, private prompts, personal traces, local env files, or provider tokens.
4. Preserve the distinction between:
   - source-reported result
   - reproduced measurement
   - model prediction
   - execution completion
   - independently verified outcome
5. Keep retries/continuations/branches from one work item in one evaluation fold.
6. Posts must not overclaim beyond the frozen study.
7. Negative and incomplete results remain publishable evidence.

## Normal flow

```text
local experiment commit
  -> import spec with pinned SHA + allowlist
  -> studies/<study>/data
  -> validate
  -> analysis / figures
  -> posts/<study>.md
  -> Pages
```

## Verified OSS Loop

This repository is onboarded with the mature-layout Verified OSS Loop kit under `.verified-oss-loop/`.

- rollout scheme: `rolling`
- worker base: `nightly`
- feature target: `preview`\n- overnight target: `nightly`
- contributors and agents never merge `main`
- exact-head evidence receipts are required on PRs
- independent review precedes maintainer merge

Run `python3 .verified-oss-loop/rollout.py show` before branching. The z0evals evidence/privacy invariants above remain authoritative if the generic kit is less strict.

## Rule -> enforcer

| Rule | Enforced by |
|---|---|
| Never send a free-lane request the known per-model limits (TPM, context, max request, RPD/TPD) reject, and never count its 413/429 as a model failure | `studies/free-taskfit-v0/scripts/plan_taskfit.py` (plans out as `not_eligible`), `certify.py` (fails runs with 413 or ruled-out rows), `tests/test_routing_evidence.py` in CI |
| Don't re-measure a (lane, family) already in an unexpired receipt | `plan_taskfit.measured_pairs` (`--force` to override) |
| Free-model batteries run in GitHub Actions with repo-secret keys, one run at a time | `.github/workflows/free-taskfit.yml`, `scripts/dispatch_taskfit.sh` |
