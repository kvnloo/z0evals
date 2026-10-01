# Governed AODL golden trace v1

This is the next lane of z0evals#78 / #58.

The collector joins one stable root trace across canonical local evidence:

1. host-governed request preparation;
2. AODL structural admission;
3. dispatch claim/completion;
4. provider admission/release;
5. physical execution receipt and measured token usage;
6. structural-gate Tokenomics latency;
7. independently joined verified outcome, when one exists.

The first live canary is expected to prove stages 1–6. Stage 7 is allowed to
remain missing: a completed provider response is not task success.

Run against the output/state directory produced by the governed live proof:

```bash
python studies/aodl-admission-v1/collect_golden.py \
  --receipts /path/state/receipts/decisions.jsonl \
  --outcomes /path/state/receipts/outcomes.jsonl \
  --tokenomics /path/state/tokenomics/events.jsonl \
  --trace-id remote-public-proof \
  --require-verified \
  --out studies/aodl-admission-v1/results/golden-trace.json
```

For the public `CANONICAL_OK` canary, `--require-verified` requires both
the structural/execution/usage chain and the independently joined deterministic
exact-output verifier. Without that flag, the collector can still be used for
structural-only traces and reports verification separately.

No stage is inferred from another stage. Missing evidence stays missing.


## Importing a completed canary

After the live wrapper produces a passing bundle, import only its sanitized
artifacts:

```bash
python studies/aodl-admission-v1/import_golden.py \
  --bundle-dir /tmp/aodl-golden-canary
```

The importer validates both frozen JSON Schemas, exact z0intelligence revision,
root-trace identity, and full completion flags. It scans the five sanitized JSON
files for credential-shaped keys and the live OpenRouter secret when available.

Only these files are copied:

- `bundle.json`
- `golden-trace.json`
- `summary.json`
- `health.json`
- `omp-governed.json`

`raw/` is never traversed or imported. The destination also gets
`index.json` containing SHA-256 hashes of every imported file and
`raw_state_imported: false`.
