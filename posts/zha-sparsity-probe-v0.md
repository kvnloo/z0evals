---
title: "hierarchical attention on a 0.6b model, with no training"
subtitle: "zyphra's zha routes each query down a tree of key summaries. we tried an untrained version on z0intelligence's local qwen3-0.6b lane: it kept all 62 of 90 dense-correct retrievals and selected 20.7% of decode keys."
study: zha-sparsity-probe-v0
status: draft
author: "zer0 research"
date: "november 3, 2026"
published: '2026-11-03'
area: small-models
kind: study
tags: [attention, sparsity, long-context, qwen3]
featured: false
mock_data: false
toc:
  - id: claim
    label: the claim we checked
  - id: setup
    label: what we ran
  - id: retrieval
    label: retrieval, paired with dense
  - id: support
    label: how sparse dense attention already is
  - id: limits
    label: what this does not show
  - id: next
    label: what would settle it
---

<div class="stat-strip" markdown="0">
<div><b>62/90</b><span>six-level tree, same as dense</span></div>
<div><b>20.7%</b><span>decode keys selected</span></div>
<div><b>0.66</b><span>p=.90 support exponent, 1k–32k</span></div>
<div><b>0</b><span>trained routers tested</span></div>
</div>

## the claim we checked {#claim}

on november 2, zyphra announced [zyphra hierarchical attention](https://x.com/ZyphraAI/status/2117377426242367669) ([paper](https://arxiv.org/abs/2610.42112v1), [blog](https://zyphra.com/our-work/zyphra-hierarchical-attention)). zha summarizes the kv cache into a tree, and each decode query walks it top-down, expanding only the branches that top-p selection keeps. two claims carry the method:

1. in dense models, the set of keys holding a fixed share of attention grows sublinearly with context.
2. a deep tree can find that set without scoring every key.

zha learns its summaries ("reference queries") by distilling from the dense model. we found no released code or checkpoint, so we tested a cheaper question: does an **untrained** tree, where each summary is the plain mean of its keys, already work on the small models z0intelligence runs locally?

## what we ran {#setup}

- model: `Qwen/Qwen3-0.6B` at `c1899de`, the 0.6b lane pinned in z0intelligence's model manifest. bf16, one 12 gb gpu.
- routers: a flat router (64-key chunks, one level), trees of 4-way chunks at depth 3 or 6, and a window-only control. tree routers always keep 4 sink tokens and the last 128 keys. the summary score is `q·mean(k)/√d + log(count)`, with top-p applied at each level.
- retrieval: 90 seeded four-needle tasks, 30 each at 4k, 8k and 16k tokens of public-domain book text. every router ran on every task. prefill and the first output token use dense attention; masking applies to later decode steps.
- attention support: 3 gutenberg books × 2 segments of 32k tokens, 29 log-spaced query positions, every head of all 28 layers. this gives 82,824 rows. heads, layers and overlapping prefixes are correlated, so these are not independent samples.
- correctness: 5/5 cuda unit tests pass, including one that masked attention with every key kept equals sdpa.

the 4b lane (`Qwen3.5-4B`, the same hybrid family as zyphra's qwen3.6 base model) was stopped while loading because the host was short on memory. it produced no results.

## retrieval, paired with dense {#retrieval}


| router | correct | decode keys selected | dense-correct lost |
|---|---:|---:|---:|
| dense | 62/90 | 100% | — |
| flat 64, p=.90 | 61/90 | 23.1% | 1 |
| tree 4×6, p=.99 | 62/90 | 20.7% | 0 |
| tree 4×3, p=.95 | 60/90 | 7.2% | 2 |
| window only | 2/90 | 1.9% | 60 |

the six-level tree got every task right or wrong exactly as dense did. the window-only control failed 60 of dense's 62 correct tasks, so the dense first token is not what carries the answers. pruning harder to 7.2% lost two answers, both at 16k.

at this scale the tree did not beat the flat router. the flat router selected a similar share of keys and lost one task. small model, one seed, 90 tasks: dense accuracy's 95% wilson interval is 58.7–77.5%. a result like this cannot show equivalence or rank the routers.

<details class="more" markdown="1">
<summary>per length</summary>

| length | dense | tree 4×6 p=.99 | keys | tree 4×3 p=.95 | keys |
|---|---:|---:|---:|---:|---:|
| 4k | 26/30 | 26/30 | 24.4% | 26/30 | 9.1% |
| 8k | 16/30 | 16/30 | 20.3% | 16/30 | 6.9% |
| 16k | 20/30 | 20/30 | 17.6% | 18/30 | 5.7% |

</details>

## how sparse dense attention already is {#support}

we also used an oracle: sort the true dense attention weights and keep the smallest set reaching p. this needs a full scan, so it is a ceiling, not a router.

| keys available | oracle p=.90 set | tree 4×6 p=.99 selected | dense mass kept by tree |
|---:|---:|---:|---:|
| 1,024 | 7.4% | 50.7% | 98.4% |
| 4,096 | 4.5% | 32.5% | 97.7% |
| 16,384 | 3.0% | 19.3% | 96.7% |
| 32,768 | 2.3% | 15.0% | 96.2% |

a log-log fit of the mean p=.90 set size over 1k–32k gives an exponent of **0.66** (0.70 at p=.95). that agrees with zyphra's first claim over this short range, on three books. it is a descriptive fit, not an asymptotic result.

the gap between the oracle and the untrained tree is what learned summaries have to close. the tree selects 6–7× more keys than the oracle, and the attention mass it keeps falls slowly as context grows. zyphra reports exactly this compounding loss with depth and handles it with trained reference queries and depth-dependent thresholds.

## what this does not show {#limits}

- this is not zha. no reference queries, no distillation, and no comparison with zyphra's numbers.
- no speedup. the reference code computes dense scores and then masks them. "selected keys" counts the mask; it is not a measure of flops, latency or memory. the full kv cache is kept.
- prefill is dense, so this says nothing about sparse prefill.
- zyphra's 35× at 10m tokens and ~400× at 1b tokens are projections from their roofline model. we did not reproduce them.
- one model, one seed, synthetic retrieval only. no ruler, longbench, reasoning or coding.

## what would settle it {#next}

for z0intelligence, this stays an experimental benchmark. nothing in the decision backends or memory retrieval changes. the next useful evidence: trained reference queries on the 4b hybrid lane, scored on a frozen holdout of z0int's own bounded decision tasks, with measured construction, routing and attention latency. a released zha checkpoint would beat our reimplementation.

data and scripts: [`studies/zha-sparsity-probe-v0/`](https://github.com/kvnloo/z0evals/tree/main/studies/zha-sparsity-probe-v0). `scripts/check_study.py` re-derives every number above from the frozen data.
