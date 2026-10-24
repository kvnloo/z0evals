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

## Study results and policy posts

The policy flow has one direction:

```text
manifest.yaml + analysis/summary.json
  -> tools/emit_result.py -> studies/<id>/result.json (z0eval.result.v1)
  -> z0intelligence ingest -> append-only findings (z0.finding.v1)
  -> deterministic compiler -> content-addressed policy (z0.decision_policy.v1)
  -> runtime policy load -> stamped decision receipt
  -> policy changelog -> tools/policy_post.py -> posts/policy/<date>-<version>.md
```

z0evals certifies evidence. It does not promote an arm or authorize a route.
Posts are outputs, never inputs to the policy compiler.

### Emit a study result

Install the dependencies from `requirements.txt`.
Add an explicit `result` object to `analysis/summary.json`.
The emitter does not select a metric from a legacy summary or infer an arm from prose.

The result contract is [`schemas/z0eval.result.v1.json`](schemas/z0eval.result.v1.json).
The synthetic fixture in [`tests/test_emit_result.py`](tests/test_emit_result.py) shows the complete input shape.
Supply these fields:

- `suite_revision`, `system_revision` and `baseline_revision`: full, immutable, 40-character Git revisions.
- `verdict`: `KEEP`, `DISCARD` or `PARTIAL`.
- `gates`: `contract`, `authority`, `quality_noninferiority` and `latency_tail`.
  Each gate is `pass`, `fail` or `not_run`.
  Every gate must pass for `KEEP`.
- `evidence`: arrays named `tokenomics_artifacts`, `source_artifacts` and `result_hashes`.
  At least one array must contain a reference.
  Every reference has a study-relative file `path` and its lowercase `sha256`.
  An optional `url` links to the public, frozen artifact.
- `limitations`: an array of scope limits, including negative or incomplete results.
- `family`, `job`, `scope_note` and `ts`: the decision family, job, scope and observation time.
  Use an ISO 8601 timestamp with a timezone.
- `arm`: explicit `kind`, `model`, `quant`, `engine`, `backend` and `device`.
  Use a revision-qualified model and engine.
  Use an explicit value such as `not_applicable` when a field does not apply.
- `metric`: `name`, `value`, positive integer `n`, `ci_low`, `ci_high`, `ci_method` and `higher_is_better`.
  Name the confidence method, such as `wilson95` or `bootstrap95`.
  Missing confidence intervals and `ci_method: none` are not valid.
- `evidence_class`: `measured`, `replayed_L1`, `replayed_L2`, `canary`, `published` or `inference`.
  `inference` never supplies promotion evidence.
- Optional `baseline`: `{arm, value}`.
  Optional `expires_at`: the evidence expiry timestamp.

Retain explicit promotion metadata when the study measured it.
Use `metric.live_shadow` for live shadow labels.
Use `metric.divergence` and `metric.aa_noise_floor` for replay comparisons.
Use `metric.outcome_ledger_verified` for verified task outcomes.
Do not invent these fields to satisfy a promotion gate.

Hash each allowlisted evidence file before emission:

```bash
sha256sum studies/my-study/data/rows.jsonl
python tools/emit_result.py studies/my-study
```

Replace `my-study` with the manifest ID.
The directory name must match that ID.
The emitter checks the manifest and receipt schemas, confidence interval order, finite numbers and every supplied evidence hash.
It refuses directory references, external paths, escaped symlinks and self-references to `result.json`.
It also binds the manifest and summary with computed hashes.
It writes the receipt only after these checks pass.

The emitter derives `schema`, `suite_id` and the one-item `findings` consumer view.
Do not supply `findings` in the summary.
The consumer view copies the explicit subject, arm, metric, scope, evidence class and timestamps.
This prevents the ingester from guessing what a result means.

### From a finding to a decision

z0intelligence binds each finding to the receipt path and SHA-256.
It appends findings to its hash-chained ledger.
The compiler applies the `none → shadow → canary → live` stage machine.
Evidence controls each transition, not the publication status or a `KEEP` verdict alone.
Failed or incomplete certification must not become positive promotion evidence.

Runtime consumers load the policy at decision time.
Each decision records `policy_version`, `policy_sha256`, `rule_id` and `stage`.
An absent or broken policy falls back to stage `none` and frontier/Jev without a turn failure.
O11 requires evidence-bound routes.
O12 requires offload for a healthy live arm unless the receipt records an eligible abstain.
The guard checks receipts and offload obligations.

### Publish the policy output

First allowlist the evidence and exact policy artifact for public release.
Never publish private traces, local paths, credentials or complete worktree copies.
Use immutable HTTPS links to the released evidence and the policy version.

For a Markdown changelog:

```bash
z0int policy changelog --from "$FROM_VERSION" --to "$TO_VERSION" > /tmp/policy-changelog.md
python tools/policy_post.py /tmp/policy-changelog.md \
  --from-version "$FROM_VERSION" --to-version "$TO_VERSION" \
  --policy-url "$PUBLIC_POLICY_URL" \
  --evidence-url "$LOCAL_EVIDENCE_PATH=$PUBLIC_EVIDENCE_URL" \
  --date 2026-10-24
```

The tool also accepts `-` for standard input.
It reads `From:` and `To:` hashes from the native Markdown when present.
Explicit flags must agree with those hashes.
For local `file://` links, supply one `LOCAL_PATH=HTTPS_URL` override per path.
The tool replaces local paths and link labels with public evidence links.
It refuses unmapped local links.
For Markdown with public evidence links already present, the evidence override is not necessary.

For the native JSON diff:

```bash
z0int policy changelog --from "$FROM_VERSION" --to "$TO_VERSION" --json > /tmp/policy-diff.json
python tools/policy_post.py /tmp/policy-diff.json \
  --policy-url "$PUBLIC_POLICY_URL" \
  --evidence-url "$FINDING_ID=$PUBLIC_EVIDENCE_URL"
```

The JSON contract has `from_version`, `to_version`, `changes` and `evidence`.
Each change has `rule_id`, `from`, `to` and `because` finding IDs.
Each evidence entry has `id` and `url`.
The native diff may also contain a private `path`, which the post never copies.
Use a `FINDING_ID=HTTPS_URL` override if an evidence URL is local.
Every referenced finding needs an evidence URL.
Both policy versions must be full SHA-256 values.
The publisher retains missing-endpoint warnings from Markdown.
For JSON, it renders top-level `serving_missing` rule IDs and per-change `serving_missing: true` in a separate warning section.

The output path is `posts/policy/YYYY-MM-DD-<first 12 version characters>.md`.
Front matter records both versions, the policy URL, evidence URLs and the changelog SHA-256.
The tool preserves Markdown stage entries or renders JSON stage entries.
Repeated identical input produces the same post.
A different post at the same path is an error, not a silent overwrite.
These Markdown files are publication artifacts.
The current site builder only selects top-level posts, so this command does not deploy them to Pages.

### Existing study: harness-speed-v1

The default branch contains the study post, not the study directory.
The frozen study remains on `study/harness-speed-v1` at `1ec7c67e36cd6dfa57416b7afdd63ada2805158a`.
Its summary already has sample counts and bootstrap intervals for latency.
It lacks the explicit `result` object, certification verdict and gates, selected policy family and canonical arm/metric metadata.
It also lacks a complete result revision triplet and receipt-shaped evidence references with per-file SHA-256 values.
The manifest lists several artifact directories rather than hashed files.
Do not fabricate a quality gate from the all-passing task results.
Select and scope a measured result, freeze its file hashes, and add certification metadata before emission.

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
