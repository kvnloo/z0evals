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
