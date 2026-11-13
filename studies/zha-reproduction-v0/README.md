# ZHA reproduction v0: training our own hierarchical-attention routers on small models

Zyphra's ZHA ([arXiv:2610.42112v1](https://arxiv.org/abs/2610.42112v1)) has no released code or
weights. This study reimplements the method from the paper's Section III, distills routers for
several small open models on one 12 GB GPU, and reruns the paper's evaluations that fit:

- **RULER-13** from NVIDIA's official generator ([NVIDIA/RULER](https://github.com/NVIDIA/RULER)
  `db43f92`), all 13 tasks, at 4K and 8K tokens with 10 examples per task and length.
- **MMLU-Pro**, a 70-question subset (5 per category), on one model.
- **Dense top-p scaling**, the paper's Fig. 1 protocol on three public-domain books.

The trained routers are published at
[huggingface.co/kvnloo/zha-routers-qwen-small](https://huggingface.co/kvnloo/zha-routers-qwen-small).

## Method as implemented (`scripts/zha.py`)

- **Tree construction (III-A).** Each node stores one tangent per reference query of the
  log-sum-exp of its keys' scores: k̂ = softmax(q̂·K/√d)K and b̂ = LSE − q̂·k̂/√d. The reference
  query is RoPE-rotated to the node's last position. Parents merge their children's tangents
  evaluated at the parent's rotated query. Node score: max over r of (q·k̂_r/√d + b̂_r). Key 0 is
  kept out of the tree and always attended. There is one tree per KV head per full-attention layer.
- **Training (III-B).** Backbone frozen. Only the R=16 reference queries per KV head per layer are
  trained, shared across nodes, levels and the query heads of a GQA group. The loss is the per-level
  KL between dense attention mass pooled into chunks and the softmax of node scores; the current
  incomplete chunk uses its exact log mass. Optimizer: AdamW (0.9, 0.95), ε=1e-15, peak LR 3.2e-2,
  WSD with 20 warmup steps and linear decay over the last 20% to 1%, gradient-norm clip 1.0.
- **Routing (III-C).** Start from the complete top-level nodes. At each level keep the smallest
  score-ordered prefix reaching top-p estimated mass, then expand its children plus the parentless
  complete nodes. The attended set is key 0, the selected leaf chunks and the current incomplete chunk.
- **Geometries.** As in the paper: deep `C4 L6` and wide `C256 L1`, both with R=16.

## Deviations from the paper

| | paper | here |
|---|---|---|
| base models | Qwen3.6-35B-A3B, Nemotron-3.5-Lightning-30B-A3B | Qwen3-0.6B, Qwen3.5-0.8B, Qwen2.5-1.5B, Qwen3-1.7B |
| training data | ~4B tokens, mid-training mixture | 3.3–4.9M tokens, 40 Gutenberg books |
| training context | 32K, document-masked | 8K windows inside single books |
| queries per step | all eligible | 128 random positions per layer per sequence |
| init | not stated | real pre-RoPE queries from the same KV group |
| prefill | ZHA block prefill (appendix) | dense prefill of the prompt except its last token |
| decode | ZHA | ZHA on every generated token, including the first |
| RULER | 256K, 100 examples per task | 4K and 8K, 10 examples per task |
| thinking | on for reasoning evals | off everywhere |

The reference implementation scores every node and then masks, so the decode key share it reports
is real while its latency is not ZHA's. No speedup is claimed.

## Not run, and why

- **SWE-bench Verified, Terminal-Bench 2.1.** Agentic runs with 200K+ contexts; sub-4B models score
  near zero, so a paired dense-vs-ZHA difference would carry no information.
- **AIME 2026.** Needs thinking traces up to 82K tokens × 16 samples; impractical through a Python
  decode loop.
- **LongBench v2.** The paper's subset has contexts ≥128K tokens; our KV and tree memory caps us
  at 8K on a shared 12 GB GPU.
- **GPQA Diamond.** Gated on Hugging Face; the account had not accepted the dataset terms.
- **Qwen3.5-4B.** The base model plus tree memory did not fit next to the GPU's other tenants.

## Reproduce

```sh
bash ops/fetch.sh                       # corpus, RULER essays/QA, NLTK punkt
python scripts/fetch_reasoning.py EVALS # MMLU-Pro (pinned revision)
bash ops/pipeline.sh                    # per model: RULER data, train deep+wide, RULER eval, scaling
python scripts/analyze.py --ops OPS --study .
python scripts/figures.py && python scripts/figures.py --check
python -m unittest -v test_zha          # CUDA
```

`scripts/check_study.py` re-derives every figure in the post from `data/` and checks artifact hashes.
