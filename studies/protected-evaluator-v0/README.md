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

Before accepting optimizer queries, the evaluator owner runs `freeze` with the
fixed manifest and private state directory. This existing evaluator command reads
and validates all cohorts once, then records their exact byte digests. Scoring
reads only the requested cohort and checks its frozen digest. It never opens
development or future truth as a side effect of a confirmation query.

Every truth row carries a nonempty `group` for the originating work item. Retries,
continuations and branches stay in one cohort. Preparation refuses cross-cohort
item-ID overlap even under renamed groups, and compares group aliases after
Unicode normalization, case folding and removal of format characters. These
checks catch inconsistent labels; they cannot authenticate native source lineage.
The evaluator owner must independently verify source identity and fold membership.

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

Adaptive state binds the complete manifest and cohort bytes during owner
preparation, before the first query or refused attempt. Later configuration or
requested-cohort edits refuse credit. Fresh unregistered state returns
NOT_COMPARABLE with no score or sealed credit and does not read truth. Historical
queried state cannot be registered retroactively; rotate the suite explicitly
while preserving its audit. Registered input refusals consume the query budget
and append a content-free refusal record. The prediction hash
also describes the bytes actually scored, rather than a later file reread.
Historical unbound state is not silently upgraded; rotate explicitly to a new
suite/version with a new private state directory. Hashes remain in private
state/audit, with no raw truth or filesystem paths added to public output.

For no-skill/candidate comparisons, the evaluator owner first pins
`baseline_revision` and `baseline_predictions_sha256` in the comparison cohort's
manifest. The baseline must come from an independently executed incumbent under
comparable conditions. A digest binds supplied bytes; it does not prove execution
or comparability. No real incumbent registration is added by this repair.

Pass `score --baseline-predictions FILE
--baseline-revision FULL_GIT_SHA` alongside the existing candidate arguments.
Both vectors must cover exactly the same frozen cohort and use the same metric;
one paired comparison consumes one adaptive query. The aggregate receipt binds
the baseline revision and scored prediction hash and reports its score and
candidate-minus-baseline delta. Promotion decisions and deltas use exact fractions;
float conversion occurs only for aggregate output. A registered tie or regression
is DISCARD, and positive lift cannot bypass the absolute threshold. A high score
without the pinned incumbent, with altered baseline bytes/revision, or with the
same candidate and baseline revision is NOT_COMPARABLE with no sealed credit.
An absolute failure remains DISCARD; it also has no sealed comparison credit
without a trusted incumbent. Metadata and malformed-row refusals count as query
attempts and remain in the audit. KEEP only means the supplied
predictions clear these gates; it does not prove native model execution,
repeatability, safe tool behavior, measurement completeness or adoption approval.

## Drill

`tests/test_protected_eval.py` creates temporary protected truth outside the repository
and covers normal scoring, repeated adaptive queries, query-budget exhaustion,
contamination, supersession, future-cohort refusal, and verifier independence.

This is a contract drill. Production needs the existing trusted runner to own the
manifest/state and expose only scoring to optimizers. Owner commands such as
`freeze`, contamination and rotation must not be available to the optimizer.
Same-user access to owner files is not an independent evaluation boundary. The
synthetic tests do not certify real cohort provenance or candidate behavior.

## First factory diagnostic

The first native comparison consumed one private proposal from
[Evolution Lab PR35](https://github.com/kvnloo/evolution-lab/pull/35), frozen at
`6443ea336be0a4f927c9e053cc7734461689fb68`; its integrity CLI was independently
tested at `c7009db5f6813ded46ff9e23183f38d5c4d8cd13` (23 refusal tests).
The original ai-data-extraction fork remained unchanged at
`9176c2dd81c8a101b52debd4cec88573284e2b30`. Raw corpus, draft text, protected
questions/labels and native transcripts remain private.

Two new read-only work items used independent production oracles from
z0intelligence `e1c6596de51e2a05eb0fcb8065b75b109ddf8b04` and Evolution Lab
`0212fee31a78cdba506f4d2684813962bfe0efb0`. They are a bounded source-identification
transfer diagnostic, not an implementation-reuse benchmark, representative
capability battery or unseen-code certification. All nine source sessions remain
one exposed development family; retries and branches supply no extra credit.

Both arms used real OMP 18.8.1, the frozen SDK tree
`1744f67c2f25241fad2a993e499875edce999699` and native addon 18.8.1, with local
Qwen2.5-Coder 7B Q4_K_M weights. A temporary parameter-only alias raised runtime
context to 32768 without new weights, daemon or global-default changes; its
manifest digest was
`cf0e39a496ed6a66b219be2d822bf4380478fc6a15306c0a72d7472580c60d47`.
The exact reviewed proposal hash was
`7b3b31f4b0e2c8cf3c1777bdbcce8ef7963281adbf5a3fb4f5e444b316ee4969`.
Native file ingestion delivered that body explicitly; no skill was installed.
The task prompts, source revisions, tools and permissions were otherwise the
same. Cold/warm cache conditions were not matched, so latency is not comparable.

| Condition | Correct work items | Actual inspection calls | Group-macro score |
| --- | ---: | ---: | ---: |
| No-skill baseline | 0 / 2 | 0 | 0.0 |
| Explicit first-proposal body | 0 / 2 | 0 | 0.0 |

The existing production scorer returned **DISCARD**, delta 0.0, query 1 at
manifest version `2026-10-10.3`. Its aggregate result digest is
`349af6745d37b8e9c1c73578c56a284ec6e49ecdf8b04ceaa7ec9e6d62210215`;
the serialized public result file SHA-256 is
`3a396dc5cadf9d702098bbc4582917071b04315799017e9cd217dae00e5c33fd`.
This is observed incorrect native behavior, not an unexecuted test or a positive
adoption result. `sealed_credit` in the score receipt describes its protected
scoring provenance; it does not override DISCARD or certify agent behavior.

Negative setup evidence remains separate: the initial native prompts were
truncated by a 4096-context provider; an unsupported model-config API silently
fell back; pointing discovery at a single skill folder loaded no proposal;
availability alone did not make the model read it; print mode did not expand a
literal skill slash command. These attempts cannot be credited as body-efficacy
comparisons. The second, write-oriented proposal remains unexecuted and
unqualified. Privacy/redistribution/installation gates remain in force; no
learning gain, safety certification, savings or production adoption is claimed.
