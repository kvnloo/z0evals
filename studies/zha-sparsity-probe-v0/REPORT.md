# ZHA: local feasibility results, not a reproduction

## Decision

**Worth further research; not ready for production promotion.** Training-free
hierarchical masking preserved the dense model's answer correctness on this small
retrieval pilot while selecting fewer decode keys. This does not validate trained
ZHA, coding/reasoning quality, prefill sparsity, latency, or million-token scaling.

## What ran

- z0intelligence's pinned **Qwen3-0.6B base-model lane**, revision
  `c1899de289a04d12100db370d81485cdf75e47ca`, BF16 on a 12GB CUDA GPU.
  This is not a NanoJev-trained checkpoint or the current Laya fast path.
- **720 generations:** 90 seeded four-key needle tasks, each evaluated with
  all eight routers. 30 tasks each at nominal 4K, 8K and 16K. The exact
  tokenized prompt length is retained per row.
- **82,824 scaling rows:** three public-domain books, two segments/book;
  29 log-spaced causal query positions from 256 to 32,768, 28 attention
  layers, 16 query heads, 17 configurations. Heads, layers and overlapping
  prefixes are dependent measurements, not 82,824 independent experiments.
- **5/5 CUDA unit tests passed**, including all-key masked GQA versus SDPA,
  oracle mass coverage, ragged trees, top-p selection and window control.
- 4B loading was stopped under shared-host RAM/swap pressure before any
  measurements. There are **no 4B results**. All experiment services are stopped.

## Paired retrieval results

| Router | Correct | Mean selected decode keys | Dense-correct cases lost |
|---|---:|---:|---:|
| dense | 62/90 | 100.00% | 0 |
| flat64-p0.9 | 61/90 | 23.05% | 1 |
| flat64-p0.99 | 62/90 | 57.53% | 0 |
| tree4x3-p0.95 | 60/90 | 7.24% | 2 |
| tree4x3-p0.99 | 62/90 | 21.64% | 0 |
| tree4x6-p0.99 | 62/90 | 20.75% | 0 |
| tree4x6-p0.999 | 62/90 | 49.03% | 0 |
| window-only | 2/90 | 1.90% | 60 |

The six-level p=.99 tree and dense had identical correct/incorrect labels on all
90 tasks. That is **not proof of equivalence**. The dense accuracy's 95% Wilson
interval is 58.72%–77.51%; this is a small, single-seed,
single-model pilot. The aggressive three-level p=.95 tree lost two dense-correct
cases. The window control failed almost every task, so passing is not explained
by the unmodified dense first token alone.

| Nominal length | Router | Correct | Mean selected decode keys |
|---|---|---:|---:|
| 16384 | dense | 20/30 | 100.00% |
| 16384 | tree4x3-p0.95 | 18/30 | 5.71% |
| 16384 | tree4x6-p0.99 | 20/30 | 17.58% |
| 16384 | window-only | 0/30 | 0.81% |
| 4096 | dense | 26/30 | 100.00% |
| 4096 | tree4x3-p0.95 | 26/30 | 9.14% |
| 4096 | tree4x6-p0.99 | 26/30 | 24.37% |
| 4096 | window-only | 1/30 | 3.26% |
| 8192 | dense | 16/30 | 100.00% |
| 8192 | tree4x3-p0.95 | 16/30 | 6.86% |
| 8192 | tree4x6-p0.99 | 16/30 | 20.28% |
| 8192 | window-only | 1/30 | 1.62% |

The pooled key fraction equally weights the 90 trials. Each trial averages its
fraction over full-attention decode steps, heads and layers; it is not a
wall-clock-weighted or token-count-weighted speed metric.

## Attention support and tree error

An oracle sorts actual dense attention weights to find the smallest top-p token
set. It is a full scan and **not an efficient router**. Its support shrinks as a
fraction of sequence length in this finite range:

| Keys available | Oracle p=.90 support | Oracle p=.95 support | Six-level p=.99 selected | Six-level retained dense mass |
|---|---:|---:|---:|---:|
| 1024 | 7.44% | 12.84% | 50.71% | 98.38% |
| 4096 | 4.52% | 8.49% | 32.52% | 97.68% |
| 16384 | 3.00% | 5.87% | 19.34% | 96.73% |
| 32768 | 2.30% | 4.55% | 14.95% | 96.24% |

The descriptive log-log fit of mean p=.90 support over 1K–32K has exponent
**0.661**. This is consistent with finite-range sublinear support in
these books, not an asymptotic guarantee. Only three source documents are used;
no independent-document confidence interval or universal scaling claim is made.
The six-level tree's loss of dense mass with longer context motivates testing
trained summaries and depth-dependent thresholds rather than blindly fixing p.

## What this method is — and is not

The paper uses **learned reference queries distilled from dense attention**.
This probe uses arithmetic key centroids plus a log-count bias, followed by
per-level top-p selection. The original full KV cache is retained. Tree routers
also retain four sink tokens and the most recent 128 keys. All prompt prefill
and the first generated token remain dense, and cached values were computed
using dense context. Only subsequent decode attention is masked.

The Python reference implementation builds every centroid and computes dense
score matrices before masking. Its `scored` fields are **idealized selected-node
plus selected-key counts**, excluding construction, sorting and memory traffic.
They are not measured FLOPs or speedups; the oracle's field only counts support.
No GPU latency, end-to-end speedup, memory reduction, or prefill saving is claimed.
In particular, fewer selected keys does **not** imply a smaller full KV cache.

Zyphra's 35× at 10M and roughly 400× at 1B tokens are **source-reported roofline
projections**, not results reproduced here. No ZHA code/checkpoint link was
found in the checked blog/paper links or the two recorded GitHub searches;
this does not prove that no implementation exists elsewhere.

## Fit for z0intelligence

Keep this as an experimental benchmark. Do not replace Laya, NanoJev adapters,
production attention or memory retrieval with it. Next discriminating evidence
would be trained-reference-query routing on the actual bounded decision tasks,
with a paired frozen holdout, sparse-prefill quality, measured construction +
routing + attention latency and peak memory. A ready-to-run upstream checkpoint
would be preferable to an unvalidated reimplementation.

## Reproduction and evidence

- `scripts/zha_probe.py`: model pins and full experimental harness. Mirrored in
  z0intelligence `benchmarks/zha_feasibility/`; archived after execution with
  documentation-only clarifications to the initial harness.
- `scripts/import_results.py`: explicit raw-file allowlist; rejects duplicate or
  incomplete runs; computes segment means, trial results and Wilson intervals.
- `scripts/figures.py --check`: recomputes this report and chart from summary data.
- `data/provenance.json`: raw-file hashes, model/base revisions, public text hashes,
  software versions, seed and limitations. Raw source rows stay external;
  aggregates are recomputable with the original raw files or by rerunning.
- `data/niah-trials.json`: all 720 public synthetic-task outcomes.
- `data/scaling-segments.json`: 2,958 segment/position/router aggregates.
- `data/summary.json`: derived figures, paired errors and finite-range fits.
- `data/run-status.json`: completed, stopped and unreproduced scopes.
- `data/unit-tests.txt`: actual CUDA test execution output.

[Announcement](https://x.com/ZyphraAI/status/2117377426242367669) ·
[Paper v1](https://arxiv.org/abs/2610.42112v1) ·
[Release blog](https://zyphra.com/our-work/zyphra-hierarchical-attention)

**Local artifacts only. No commit, push, PR, publication or production change.**
