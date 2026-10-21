# Human Capability Loop: synthetic conformance slice

Owner: [z0evals #104](https://github.com/kvnloo/z0evals/issues/104). Product brief: [humanity-vault #1](https://github.com/kvnloo/humanity-vault/issues/1), [roadmap draft #2](https://github.com/kvnloo/humanity-vault/pull/2). This is the **first contract-fixture slice**, not a complete protected benchmark, empirical study or learned policy.

## Run

Python 3.10+ standard library only, from repository root:

```sh
python -m unittest discover -s studies/hcl-eval-v0 -p 'test_*.py' -v
python studies/hcl-eval-v0/validate.py studies/hcl-eval-v0/synthetic.json
```

The first command exercises 14 test methods with multiple negative vectors. The second reports one observed control outcome and one missing candidate outcome. It does **not** compute a difference, fill the missing candidate with zero, or choose a winner. Output is always `CONTRACT_ONLY`, `human_benefit=NOT_EVALUATED`, `can_promote=false` on accepted input. Invalid input exits 2 with a stable error code rather than echoing its content.

## Deliberately narrow contract

`hcl-conformance-v0` is a provisional fixture format within this directory, **not** an adopted AODL/NOOP schema. Existing repository study manifests and protected evaluators remain unchanged; there is intentionally no frozen/published `manifest.yaml` for this pre-study work.

The declaration requires synthetic data, contract-only claims, 40-character source/evaluator revision shapes, timezone-aware registration and analysis times, and bounded rows. Synthetic `a...`/`b...` revision strings and 2030 timestamps are intentionally invented fixture values, not actual code provenance or prospective registrations. The real implementation revision belongs in the PR/test receipt.

Rows separate choice (`YES/NO/SKIP/UNKNOWN`), observation (`OBSERVED/MISSING/SKIPPED/NOT_DUE`), measurement class (self-report/objective-task/physiology-proxy/simulation), assistance, assignment arm/probability and grouped search/evaluation split. A choice is **not** proof that an exposure was delivered. `exposure_at` is the declared comparison-window anchor; delivery/adherence provenance is not implemented in this slice. The declared primary outcome is a point observation due no earlier than `outcome_due`; interval outcomes and tolerances need a later reviewed profile.

Checks reject late/equal registration relative to the exposure anchor, future exposure at analysis time, early/future observations, unzoned clocks, missing data encoded numerically, nonfinite/coerced numbers, duplicate IDs/JSON keys, extra fields, mixed splits for one declared group, placeholder all-zero revisions and unbounded rows/input bytes. Offset times are normalized to UTC. A skip can be recorded before an outcome is due; missing cannot. No mean, capability score or effect is estimated across heterogeneous measurements.

## What passing does NOT establish

- A `synthetic` label cannot prove actual data are synthetic or anonymous. Do not run this on private health histories, conversations or identifiable human records, and do not treat it as a privacy scrubber.
- Timestamp shape/order is not durable preregistration evidence. Revision shape is not source existence, integrity, consent or authentic execution proof.
- Group consistency only checks supplied group IDs; it cannot detect undisclosed related items, deduplicated people or covert training leakage.
- This does not test consent enforcement, revoked permissions, source-owned imports, user experience, end-to-end Anki/NOOP operation, hardware or human learning. Those remain owner issues.
- No statistical power, causal effect, clinical conclusion, optimum policy, verified benefit or automatic promotion is produced.

## Next independent work

1. Map this fixture vocabulary to existing AODL #47 and source-native outcome contracts without creating a second event store.
2. Evolution Lab #41 owns simulator/candidate generation. z0evals retains its separately frozen evaluator and contradictory/missingness fixtures.
3. Add blinded unit-specific endpoints, source/consent attestations, grouped chronological holdouts, coverage and predeclared uncertainty/burden criteria before any real-study evaluator.
4. Demonstrate the selected source-to-Anki-to-delayed-test vertical with explicit user permission; actual delayed outcomes are collected only when due, never synthesized as human efficacy.

## Verification receipt at preparation

Local Linux, Python 3.13.5: `python -m unittest -v test_validate` passed **14/14 test methods**; CLI fixture produced the limited output above. These are synthetic contract tests, not the full repository suite or hosted CI. The dedicated read-only GitHub Actions job runs the same discovery command; its outcome must be fetched at the exact PR head before claiming hosted success.

Tested Git blobs: validator `553666e94875968ffc1d73505874d13cf7bfab84`, tests `cc8f24256cecd891d66793bd982e3198d002c577`, fixture `2247b22119f1df8041f868e87d7479747b1d5f3c`. Publication readback must match them. No main/preview/nightly merge or policy cutover is requested.
