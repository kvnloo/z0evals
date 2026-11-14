# RSI-inspired Hermes skill selection

A completed three-seed pilot does not establish a skill-quality gain. Guided selection has slightly higher final keyword fitness, but lower known-answer verdict accuracy than both controls. No evolved skill is promoted or deployed.

## Final results

Each arm uses exactly 28 development task calls and 32 post-search holdout calls per seed. All nine runs are valid. Means below cover seeds 0, 1, and 2 on the same eight unique holdout cases.

| Arm | Keyword fitness, mean | Seed range | Verdict accuracy, mean | Selected-only Spearman, mean |
|---|---:|---:|---:|---:|
| Native GEPA text adapter | 0.579109 | 0.572222–0.591667 | 62.50% | Not measured |
| Prediction-guided | 0.581944 | 0.562500–0.601389 | 58.33% | -0.208690 |
| Random selection | 0.572627 | 0.563715–0.583160 | 62.50% | -0.315120 |

Guided-minus-GEPA keyword differences by seed are +0.008507, -0.009722, and +0.009722; their mean is +0.002836. Guided-minus-random differences are +0.018229, -0.020660, and +0.030382; their mean is +0.009317. Guided verdict accuracy is lower by 4.17 percentage points against either control: one seed has 50% accuracy instead of 62.5%, while the other two tie.

These observations do not establish a useful predictor or an improvement in task correctness. Each correlation uses just six selected development candidates per seed and is selection-biased. Three seeds on eight shared cases do not create 24 independent tasks. No significance claim is made.

## Curves at fixed task-call checkpoints

Mean heldout keyword fitness of the development-selected incumbent:

| Arm | 4 calls | 12 calls | 20 calls | 28 calls |
|---|---:|---:|---:|---:|
| GEPA | 0.603009 | 0.578299 | 0.567766 | 0.579109 |
| Guided | 0.602604 | 0.566146 | 0.569387 | 0.581944 |
| Random | 0.575868 | 0.589236 | 0.563310 | 0.572627 |

Mean development best-so-far keyword fitness:

| Arm | 4 calls | 12 calls | 20 calls | 28 calls |
|---|---:|---:|---:|---:|
| GEPA | 0.628125 | 0.628125 | 0.628125 | 0.628125 |
| Guided | 0.621875 | 0.645833 | 0.668750 | 0.676042 |
| Random | 0.650000 | 0.659375 | 0.659375 | 0.660417 |

GEPA retains the original prompt at every checkpoint. Even unchanged candidate IDs produce different heldout keyword scores across repeated audits. Provider seeds do not guarantee deterministic completions. Heldout curves need not increase: holdout results never choose the incumbent, and no best-of-holdout selection is performed.

## Cost and operations

Nemotron Lightning executes tasks; Nemotron Ultra generates mutations. Both use documented non-thinking mode. The completed run has 252 development calls, 288 holdout calls, 31 generation calls, and no failed attempts or rejected candidates: 571 requests in total. Receipts report 270,465 prompt tokens, 90,357 completion tokens, and zero reasoning tokens. The CLI exits 0 with nine valid and zero invalid runs.

| Arm | Generation calls, all seeds | Prompt tokens, all seeds | Completion tokens, all seeds | Mean search seconds | Mean provider seconds |
|---|---:|---:|---:|---:|---:|
| GEPA | 13 | 103,562 | 26,567 | 118.68 | 120.18 |
| Guided | 9 | 81,442 | 33,057 | 199.50 | 150.08 |
| Random | 9 | 85,461 | 30,733 | 176.88 | 177.56 |

Search time includes pacing but excludes the post-search holdout stage. Provider seconds sum request latency across search, generation, and holdout, excluding pacing. Whole-run wall time is 37.90 minutes. These are sequential hosted-API observations, not a hardware latency benchmark. External task calls are matched; generation compute and proposal distributions are not.

An earlier Groq run is invalid after output truncation and persistent 429s. A Lightning-only attempt was interrupted after native GEPA swallowed malformed proposal failures; a regression and fail-closed adapter fix preceded the completed run. Both attempts remain separate from valid quality measurements. Lightning failed repeated exact-count mutation probes; Ultra passed one- and four-candidate probes. Routing follows these measured roles, not model size alone.

## Evidence and reproduction

- [Protocol and limitations](protocol.md).
- [Paper loop, domains, and source-reported ablations](research.md), explicitly separate from this pilot.
- [Aggregate results and paired differences](data/pilot-v3/summary.json).
- [Per-seed fixed-checkpoint curves](data/pilot-v3/rounds.csv).
- [Actual-receipt verification](data/pilot-v3/verification.json).
- [Invalid Groq aggregate](data/groq-invalid/summary.json) and [interrupted attempt receipt](data/nim-interrupted.json).
- [Pinned sources and imported-artifact hashes](manifest.yaml).

The executed code is pinned at `0c46a34b7b821f20c85f7f72aa38dbad5550c128`. The original checkout is `0a929e3aa20e15cf04dc7c28492a7d41a5139125`. The manifest separately pins the later aggregate-export commit. The export is byte-identical when repeated. Raw output and candidate text remain private; only aggregate fields and raw-file hashes are imported.

An independent Nemotron Ultra evidence audit found no evidenced inconsistencies in the supplied code, aggregates, and conclusions. Reviewer agreement does not replace receipt verification or establish task quality.

The predictor is sparse word-embedding regression, not JEPA. The baseline is an explicit-text adaptation around native GEPA, not a literal run of the repository's broken wrapper. The primary metric is keyword overlap. The handwritten verdict audit is narrower than finding correctness or full-agent verification. This is one adapted static-review skill, not a live Hermes workflow.
