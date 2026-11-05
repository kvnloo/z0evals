# Initial execution is blocked

No model inference ran and no coding license was issued. The [matrix](data/run-002/matrix.md) has 39 blocked cells for 13 candidate model routes. The [182 task rows](data/run-002/rows.jsonl) are preflight denials, not measured coding failures.

The evaluated runner is implementation commit `7dce36d753ee0e99e7bde6e3daa9f091becf2e3b`. Both fleet source snapshots pin that commit. [Fleet receipts](data/run-002/fleet-receipts.json) retain the exact commands, source archive hashes, and exit codes. [Run metadata](data/run-002/run.json) records host `mbp` and the runner, policy, and source-manifest SHA-256 hashes.

| Check | Result | Evidence |
| --- | --- | --- |
| Runner/fixture checks on MBP | 14 tests passed, exit 0 | [fixture-checks.log](data/run-002/fixture-checks.log) |
| Negative controls | All 14 original submissions failed | [fixture-checks.log](data/run-002/fixture-checks.log) |
| Positive controls | All 14 reference submissions passed | [fixture-checks.log](data/run-002/fixture-checks.log) |
| Eval execution on MBP | Exit 1, all routes blocked | [rows.jsonl](data/run-002/rows.jsonl), [fleet receipts](data/run-002/fleet-receipts.json) |
| Anonymous OpenCode | Inventory command exits 0 with empty stdout | [Big Pickle preflight](data/run-002/model-01/preflight.json), [Nemotron preflight](data/run-002/model-07/preflight.json) |
| GPT through fx | Executable missing on executor | [route](data/run-002/model-10/route.json) |
| Anthropic subscription | Executable missing on executor | [route](data/run-002/model-11/route.json) |
| Google paid-model candidate | No verified zero-spend adapter or resolved model revision | [route](data/run-002/model-12/route.json) |

Eight other OpenCode free labels lack matching zero-price catalog evidence and never reach inference. Their denials are recorded per model in `data/run-002/model-*/route.json`. The Google name is an unresolved candidate label, not evidence of model availability. Model aliases elsewhere were not resolved by inference either.

To finish A14, a permitted fleet executor needs an existing subscription route for GPT through fx and Anthropic through Claude, plus reachable anonymous free models with current zero-price evidence. Paid API credits are not assumed to be free. Credential provisioning or moving inference onto groot needs a separate owner decision. Runtime promotion remains owned by z0intelligence.
