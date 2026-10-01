# AODL admission + replay conformance v1

Tracker: https://github.com/kvnloo/z0evals/issues/78

Goal: prove that the AODL intent contract is an enforceable, deterministic
structural authority boundary before broad live-dispatch rollout.

The runtime under test is the plain-Python admission gate in
`kvnloo/z0intelligence#73`. The AODL semantic identity under test is
`aodl-canon-1` from `kvnloo/aodl#39`. Bend is an independent differential
verifier, not the runtime authority.

## Frozen stages

1. validate AODL
2. compute versioned semantic fingerprint
3. construct observed/proposed spawn state
4. decide ALLOW/DENY
5. emit structural admission receipt
6. replay the same input
7. optionally compare the representable case with Bend

Task execution and task-success verification are outside this first cohort.

## Run

Install the exact AODL revision from `manifest.yaml`, then point the runner at
a checkout of the exact z0intelligence revision:

```bash
python studies/aodl-admission-v1/run.py \
  --z0int-root /path/to/z0intelligence \
  --out studies/aodl-admission-v1/results/receipts.jsonl
```

The runner fails if an expected verdict/code changes or if deterministic replay
changes the semantic decision. Latency is recorded but not used as a correctness
oracle.

## Required invariants

- contract authority comes from validated AODL, never from caller-supplied limits;
- `aodl-canon-1` names the exact semantic contract;
- all 101–106 denial families are independently exercised;
- multi-violation cases preserve all applicable reasons;
- malformed/invalid/unavailable contract dependencies fail closed;
- replay of identical inputs preserves verdict, codes and semantic fingerprint;
- admission receipts never contain `success` or `verified_success`;
- runtime/observation mutation must not be confused with authored intent mutation.

## Outputs

- `cases.json` — frozen synthetic structural cohort
- `receipt.schema.json` — public result contract
- `results/receipts.jsonl` — generated, exact-run receipts
- later: Bend differential results and controller restart/drift traces

No aggregate winner score is defined. False allows, false denies, divergence,
replay stability and latency remain separate measurements.
