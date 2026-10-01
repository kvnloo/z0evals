# Unified Memory v0

Tracker: https://github.com/kvnloo/z0evals/issues/56

Goal: run the same source-grounded memory/state questions through DSH, Hermes, OMO, and OMP, then compare retrieval, model-visible injection, answer support, provenance, abstention, idempotency, supersession, latency, and context cost.

Stages stay separate:

1. retrieval
2. injection
3. answer use
4. verification

A configured index alone is not a passing harness integration.

Public study artifacts must contain stable question IDs and scrubbed evidence metadata rather than copied conversation history.

Expected outputs:

- `question-contract.json`
- `receipt.schema.json`
- `results/harness-receipts.jsonl`
- `results/summary.json`
- `../../posts/unified-memory-v0.md`

Do not add a new memory database. Use the source systems and provenance contracts already owned by z0intelligence and the harnesses.
