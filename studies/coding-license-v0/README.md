# coding-license-v0

Any model may write code after it passes the coding probe for the task tier.
This study measures that rule. It does not change z0intelligence routing or grant tool permissions.

## Tier spec

[`policy.json`](policy.json) freezes task membership, budgets, model routes, and one attempt per task.
The source is `harness-speed-v1` at `1ec7c67e36cd6dfa57416b7afdd63ada2805158a`.
[`source-sha256.json`](source-sha256.json) pins every fixture, prompt, reference, and verifier file.
The original [runner](../harness-speed-v1/harness/bench.py#L302) copies fixtures and calls the independent [verifier](../harness-speed-v1/harness/verify.py#L19).

| Tier | Task scope | New probes | Pass bar | Time per probe |
| --- | --- | --- | --- | --- |
| S | Bounded utility or CLI change | t01 through t06: pagination, slug, CSV, flag, LRU, duration | 6/6 | 180 seconds |
| M | Cross-file change or parser/pipeline | t07, t08, h05, h06: rename, merge, calculator, word stats | 10/10 including S | 300 seconds |
| L | Package extension with interacting invariants | h01 through h04: stock reservations, config includes, event bus, money | 14/14 including S and M | 600 seconds |

Every probe must exit zero before its budget, pass all original visible and hidden tests, and leave original tests unchanged.
The verifier restores original tests and adds hidden tests in a separate grading copy.
The runner retains the submitted files, their SHA-256 hashes, argv, elapsed time, exit status, and verifier receipt.
A failure denies that tier and every higher tier. Missing or blocked evidence never grants a license.
`BLOCKED` means no measured coding outcome. It is not `FAIL`.
A license applies only to this frozen model, adapter, fixture suite, and budgets. It is not a general ability or production-safety claim.
These public synthetic tasks have no contamination guarantee. One attempt supplies no statistical reliability estimate.
This is a non-adversarial coding eval, not an OS security sandbox. Do not run untrusted adversarial agents here.

## Run on the fleet

Run from the repository root. Use a new output directory for each run. Existing outputs are never overwritten.

```sh
fleet-build --node mbp --local-data --wait 1800 --mem 1G --cpus 1 --timeout 600 --src-include studies/harness-speed-v1 --src-include studies/coding-license-v0 -- python3 -m unittest discover -s studies/coding-license-v0 -p 'test_*.py' -v
fleet-build --node mbp --local-data --wait 1800 --mem 1G --cpus 1 --timeout 14400 --src-include studies/harness-speed-v1 --src-include studies/coding-license-v0 --fetch studies/coding-license-v0/data/run-001 -- python3 studies/coding-license-v0/run.py --out studies/coding-license-v0/data/run-001
```

Exit 0 means all listed models passed all tiers. Exit 1 means at least one model failed or is blocked.
Configuration or provenance errors exit nonzero without issuing a license.
`matrix.md`, `matrix.json`, `rows.jsonl`, `run.json`, and each model's `route.json` form the result bundle.
An interrupted run writes a partial matrix. It cannot pass a tier with missing rows.
Controls in `test_run.py` require all 14 originals to fail and all 14 references to pass.
They are fixture checks, never model measurements. Test tampering, duplicate rows, timeouts, and blocked-route reporting have separate checks.

## Zero-spend routes

GPT runs only through `fx --provider codex`, with Fast and Ultra off and an existing Codex subscription.
Anthropic requires existing Claude subscription metadata. Its command has a zero-dollar budget and no fallback model.
Anonymous OpenCode runs use a fresh HOME and XDG directories, an explicit model, and no inherited provider environment or account config.
Only the two matching zero-price entries in [`free-cost-evidence.json`](free-cost-evidence.json) can reach inference.
That evidence comes from a local cached catalog, not a live billing guarantee. The other free labels lack matching price metadata and remain blocked.
Google's paid-model route has no verified zero-spend adapter. Configured API providers are not treated as free credits.
No credentials are read, copied, or provisioned by the runner. CLI-native subscription use requires a signed-in fleet executor.
Token/tool counts remain in raw CLI output when reported. Unreported metrics and model revisions remain unknown.
