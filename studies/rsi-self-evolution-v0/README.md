# RSI-inspired skill selection

This pilot asks whether outcome-prediction-guided candidate selection improves Hermes skill search at a fixed external-evaluation allowance. It compares native GEPA, guided selection, and random selection across three seeds.

Measurement is in progress. An invalid Groq attempt and an interrupted NIM attempt remain evidence of provider and integration failures, not quality measurements. No evolved skill is deployed.

The [experiment implementation](https://github.com/kvnloo/hermes-agent-self-evolution/pull/3) adds an opt-in optimizer and a small static-review fixture. It does not change the existing CLI. That CLI is incompatible with current DSPy and cannot extract optimized body text, so the working baseline uses native GEPA through an explicit text adapter.

The predictor is a sparse embedding regressor, not the paper's JEPA model. The primary metric is the repository's keyword-overlap fitness. A separate structured-verdict audit is narrower than full agent correctness. The study will not describe a higher keyword score as verified skill improvement.

See [the protocol](protocol.md) for budgets, sealing, deviations, and reporting limits. Frozen aggregate artifacts and final conclusions will replace this progress note after verification.
