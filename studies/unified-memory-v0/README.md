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

## Offline query-outcome replay (first RSI signal, not an answer score)

`memory_query_replay.py` is a **stdlib-only, read-only** local counter for the
sanitized `z0int.memory_query_outcome.v1` rows planned for the existing
z0intelligence read-only MCP `audit.jsonl` (#194). It does not contact a
provider, load a model, hydrate original messages, change memory stores, or
activate a runtime. Only **per-tool/per-outcome retrieval counts** are returned.
Those counts are **NOT answer utility, independently verified use, or causal RSI
gain**. No control/model-input/handoff experiment is run by this script.

Run on a local, operator-approved, sanitized audit file (never upload a live or
private audit log to GitHub or the study):

```bash
python3 studies/unified-memory-v0/memory_query_replay.py --input "$LOCAL_SANITIZED_AUDIT_JSONL"
python3 -m unittest discover -s studies/unified-memory-v0 -p 'test_memory_query_replay.py' -v
python3 -m unittest discover -s studies/unified-memory-v0 -p 'test_*.py' -v
python3 scripts/validate.py
```

Each newline-terminated UTF-8 JSON row must have **exactly** these typed
fields: `schema` = `z0int.memory_query_outcome.v1`, `tool` =
`search|fetch|invalid`, `outcome` =
`hit|miss|denied|unavailable|stale|rate_limited|invalid|error`,
UTC `timestamp`, a 64-character lowercase hexadecimal `query_hmac`, nonnegative integer
`count`, `bytes`, `denied_count` and `unavailable_count`, and an
allowlisted `decision`. Producer outcomes, rather than guesses from
retrieval responses, determine the labels; the reader rejects inconsistent
counter/decision/tool combinations. It also rejects missing/extra keys
(including raw queries, content, locators or secrets), duplicate JSON keys,
unknown schemas, symlinks, changing files, malformed/truncated JSONL, inputs
larger than 8 MiB and rows larger than 4 KiB. No partial summary is printed
on failure, and errors never include a raw row or input pathname.

The producer preserves fixed error codes in `decision`: `outcome: error`
accepts its documented `error` and `byte_limit` decisions. A byte-limited
fetch remains an error, not an invalid query or a retrieval miss. Unknown
decision codes and combinations such as `outcome: error, decision: stale`
remain rejected; classified failures retain their distinct outcomes.

`query_hmac` uses a **per-process random key**: equality is not meaningful
across launches and this tool does not emit identifiers or de-duplicate query
rows. No continuity, causal improvement, latency or source-use measurements
are inferred. The frozen MBP thermal case, its source identities, matched
controls, six **NOT_RUN** stage slots, negative cases, manifest status and
unscored result remain unchanged; run the separate real study gates before
any continuity claim.
