# ZHA sparsity feasibility probe v0

Read [REPORT.md](REPORT.md) for the result, paired outcomes and limits.
The measured method is **not trained ZHA**. It is a centroid-tree comparator on
z0intelligence's pinned Qwen3-0.6B base-model lane. No production settings changed.
The 4B attempt was stopped during loading; it has no measured result.

## Reproduce

Use Python 3.12, PyTorch 2.11.0+cu128, Transformers 5.20.1 and Accelerate 1.15.0,
with one CUDA GPU exposed. Use an isolated environment. Do not co-load the two
models on 12GB. Book text, weights and external raw outputs stay outside git.

1. Download UTF-8 texts from the Gutenberg URLs in `data/provenance.json` into
   `$OPS/texts/`, preserving filenames. Compare their SHA-256 hashes; the URLs are
   mutable, so a changed file is a new dataset version, not the original run.
2. Run to **fresh, non-existing output paths** (the writer is append-only and
   cannot safely resume):

   ```sh
   mkdir -p "$OPS/raw"
   python scripts/zha_probe.py scaling --texts "$OPS/texts" \
     --out "$OPS/raw/scaling-qwen3-0.6b.jsonl" --length 32768 --windows 2
   python scripts/zha_probe.py niah --texts "$OPS/texts" \
     --out "$OPS/raw/niah-qwen3-0.6b.jsonl" \
     --lengths 4096 8192 16384 --n 30 --seed 20261103
   (cd scripts && python -m unittest -v test_zha_probe)
   ```

3. Import only when runs have exited successfully:

   ```sh
   python scripts/import_results.py --ops "$OPS" --study .
   python scripts/figures.py
   python scripts/figures.py --check
   ```

The importer rejects duplicate or incomplete rows and unexpected sizes. It uses
an explicit filename allowlist, never imports book text or personal traces, and
records raw-file hashes. It will also accept a **complete** optional 4B scaling
run at 8192 with one window/book; none was completed in this study.

## Evidence status

Local, uncommitted draft. Repository base revisions identify the starting tree;
they do not claim that these new files already exist at those commits. Artifact
hashes in `manifest.yaml` identify the local harness and results. The harness is
mirrored into the separate z0intelligence worktree's
`benchmarks/zha_feasibility/`; script and tests are byte-identical. No commit,
push, PR or website publication is part of this delivery.

## What is not shown

No trained-ZHA result, reference-query distillation, production-decision eval,
Laya or NanoJev scorer eval, RULER/LongBench reproduction, sparse-prefill quality,
GPU speedup, lower KV storage, or extrapolation beyond 32K. A finite-range power
law does not establish asymptotic complexity. Sample labels and selected-mask
fractions do not establish latency improvements or statistical equivalence.
