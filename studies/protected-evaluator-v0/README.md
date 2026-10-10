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

The registered scorer uses `group_macro_exact_match`: compute exact-match
accuracy within each work-item group, then average those group accuracies with
equal weight. Nineteen correct retries of an easy task plus one failed distinct
task score 0.5, not 0.95. This prevents branch count from supplying improvement
credit. `exact_match` remains available for explicitly item-weighted controls;
the result names the selected metric. Historical item-weighted scores remain
at their original manifest/version and are not recomputed as new outcomes.

Adaptive query state binds the complete manifest and the exact bytes read for
all cohorts at the first successful query. Later threshold/configuration or
cohort edits under the same suite/version refuse credit. The prediction hash
also describes the bytes actually scored, rather than a later file reread.
Historical unbound state is not silently upgraded; rotate explicitly to a new
suite/version with a new private state directory. Hashes remain in private
state/audit, with no raw truth or filesystem paths added to public output.

For no-skill/candidate comparisons, pass `score --baseline-predictions FILE
--baseline-revision FULL_GIT_SHA` alongside the existing candidate arguments.
Both vectors must cover exactly the same frozen cohort and use the same metric;
one paired comparison consumes one adaptive query. The aggregate receipt binds
the baseline revision and scored prediction hash and reports its score and
candidate-minus-baseline delta. A tie or regression is DISCARD even when the
absolute pass threshold is met. KEEP in this scorer only means the supplied
predictions clear these gates; it does not prove native model execution,
repeatability, safe tool behavior, measurement completeness or adoption approval.

## Drill

`tests/test_protected_eval.py` creates temporary protected truth outside the repository
and covers normal scoring, repeated adaptive queries, query-budget exhaustion,
contamination, supersession, future-cohort refusal, and verifier independence.

This is a contract drill, not a claim that filesystem secrecy alone protects an
evaluator. Production deployment still needs an actual trust boundary (separate
process/service/account or equivalent access control).
