# z0live-v0

Frozen certification wrapper for canonical z0live evidence.

This study deliberately **does not copy z0live fixtures**. Run z0live at the commit pinned in `manifest.yaml`, capture its replay JSON and host/actor identity, then wrap that evidence:

```bash
python -m z0live replay fixtures/core-v1.json --json > /tmp/replay.json

python scripts/certify_z0live.py \
  --replay /tmp/replay.json \
  --identity studies/z0live-v0/identity.example.json \
  --output /tmp/z0live-cert.json
```

Without measured hardware/runtime metrics, the strongest possible decision is `PARTIAL`.

For a full actor comparison, add a metrics JSON object containing independently measured dimensions such as TTFA, interruption-to-silence, deadline misses, long-session jitter, VRAM/RAM, CPU/GPU, and pairwise naturalness. The wrapper preserves these dimensions rather than collapsing them to one score.

Speculative prewarm is separately gated: ≥50 ms p50 useful gain and exactly zero speculative mutations. That gate is evidence about prewarm only; it does not imply actor quality.
