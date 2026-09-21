# SLM Router v0

Status: **draft publication backed by a locally frozen Phase 1B run**

Run: `p1b-20260921T1430Z`

External inference spend: **$0.00**. The reported Phase 1B calls ran through the local `z0int cognition serve` supervisor.

## Current evidence

Phase 1B densified the bounded-choice evidence from a sparse Phase 1 matrix into 370 measured state/arm cells and 1,102 raw receipts. Of those cells, 362 have at least three observations and none remain at n=1.

The study currently records:

- bounded-choice success, confidence intervals, warm latency, and dangerous selections;
- cold-load, model-swap, and warm-invocation residency measurements;
- the frozen 12-scenario orchestration reproduction and expanded orchestration results;
- corrected true-composition results;
- compiler-contract safety discrimination;
- Q-Route feature analysis and the proposed first Phase 2 corpus-generation slice;
- the gate decision and its named caveats.

The public machine-readable summary is `data/phase1b-summary.json`.

## Current conclusions

For the bounded-choice family, `compiler -> Hammer2.1-3B` is the measured default path. Qwen3.5-4B ties it on bounded-choice success but is much slower there; its measured role is orchestration, where it solved 31/40 expanded scenarios. Qwen3.5-9B retains a narrow bounded-choice niche and stronger stopping behavior, at much higher latency.

JEV remains useful as a recorded calibrated distribution, but the measured pre-composition chains did not improve the downstream Qwen4B decision. FunctionGemma remains extremely fast but did not establish a quality niche in this phase. Nemotron-Orchestrator did not establish a measured niche on the tasks evaluated here.

The compiler is a first-class part of the result, not a prompt convention: compiler-first arms recorded zero dangerous selections, while unfiltered Hammer2.1-3B selected six dangerous actions in 84 trials.

## Gate status

The Phase 1B evidence gate **passed** for bounded-choice corpus preparation, with two sampling caveats:

- eight cells remain at n=2 in `compiler+jev+qwen3.5_4b`;
- no cell reached n>=10.

Two additional gate semantics issues were exposed and intentionally not repaired inside the frozen run: the `tool_fails` latency utility tie and the difference between selected-danger rate and exposed-danger safety.

No router or specialist was trained, no threshold was tuned, and nothing was promoted.

## Reproducibility status

The run id is immutable and the source trees were reported clean, but the two source commits are still local-only:

- z0intelligence `feat/local-cognition-portfolio` at `f721f8c`
- evolution-lab `experiment/q-route-v0` at `659b5a8`

The study therefore remains `draft`. Once those exact commits and their allowlisted artifacts are pushed, use the z0evals importer to copy the canonical raw evidence, replace abbreviated SHAs with full 40-character commits, add artifact hashes, validate twice, and only then change the study to `frozen`.

## Directory contract

```text
manifest.yaml   source/provenance metadata and evidence claims
data/           public machine-readable results
analysis/       scripts used to derive tables/claims
figures/        generated public figures
notes.md        working interpretation and limitations
```

Do not put mutable runtime state here.
