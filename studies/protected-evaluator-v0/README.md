# Protected evaluator v0

This is the first score-only protected-evaluation contract for adaptive Evolution Lab
training loops.

The public repository contains **no protected truth**. The evaluator manifest names
environment-backed roots. A trusted evaluator process resolves those roots, scores a
complete prediction vector, and returns only aggregate score/verdict metadata.

## Boundary

```text
Evolution Lab / Hermes trainer
  -> candidate predictions + candidate revision
  -> protected evaluator broker
       -> protected truth (not returned)
       -> query-budget + contamination state
  <- z0eval.result.v1 aggregate only
```

The query audit contains candidate/revision, prediction/result hashes, aggregate score
and verdict. It does not contain protected labels, protected item IDs, prediction
contents, or a protected filesystem path.

The `future` cohort is deliberately non-queryable by the optimizer. If protected
examples or labels leak, mark the suite contaminated; it immediately stops minting
sealed credit. Rotation uses the explicit supersession path.

Every truth row carries a normalized, nonempty `group`: the trusted evaluator's
originating work-item lineage. Retries, continuations and branches of one task
use the same group and stay in one cohort. Before scoring, the evaluator checks
all declared cohorts and refuses missing groups or any cross-cohort overlap.
Missing cohort files also refuse scoring. Errors do not disclose group values,
labels or source paths, and rejection consumes no scoring query.

The group is supplied by the trusted cohort author, not inferred from arbitrary
candidate text. Native extraction/source references must substantiate that
grouping before a real generated skill is evaluated. This guard alone does not
establish extraction completeness, efficacy or adoption eligibility.

## Drill

`tests/test_protected_eval.py` creates temporary protected truth outside the repository
and covers normal scoring, repeated adaptive queries, query-budget exhaustion,
contamination, supersession, future-cohort refusal, and verifier independence.

This is a contract drill, not a claim that filesystem secrecy alone protects an
evaluator. Production deployment still needs an actual trust boundary (separate
process/service/account or equivalent access control).
