# AODL runtime v1

Stacked runtime acceptance lane for z0evals#78.

This runner uses the real z0intelligence authority, receipt ledger, AODL
admission, drift projection, and Tokenomics projection. Provider validation is
replaced with a deterministic no-op so the study cannot touch credentials,
reserve provider capacity, or make a physical network call.

It proves:

1. admission is fsynced before dispatch-start;
2. structural denial creates no dispatch;
3. the admission→dispatch crash window recovers without duplicate authority;
4. replay is idempotent;
5. drift becomes stateUpdate + observation receipt;
6. authored intent/source lineage remains unchanged;
7. structural evidence cannot mint task success.

Run after installing the AODL revision pinned in `runtime-manifest.yaml`:

```bash
python studies/aodl-admission-v1/run_runtime.py \
  --z0int-root /path/to/z0intelligence \
  --out studies/aodl-admission-v1/results/runtime-proof.json
```

The provider path is deliberately outside this cohort. Real provider admission
belongs to the later golden-network trace in #58 after structural enforcement is
green.
