---
title: "same model, four harnesses"
subtitle: "the fast profile matters. so does the difference between an engine and its cli."
study: harness-speed-v1
status: evidence-local
author: "zer0 research"
date: "october 21, 2026"
mock_data: false
toc:
  - id: question
    label: what we held still
  - id: latency
    label: cold is not warm
  - id: tasks
    label: all passing is not a quality ranking
  - id: excluded
    label: the failed attempt stays visible
  - id: limits
    label: what this does not prove
---

## what we held still {#question}

we started from the [branch write-up](https://github.com/kvnloo/z0evals/blob/1ec7c67e36cd6dfa57416b7afdd63ada2805158a/posts/harness-speed-v1.md). the main arms use `gpt-6.1-sol`, low reasoning effort, the same subscription and the same build laptop. requests are interleaved. the separate model contrast is not part of that same-model comparison.

`fx-base` is a custom libfx host with bench-authored tools and prompt. `fx-cli` is the actual cli. we cannot give the cli credit for the engine arm. design and amendments: [protocol](https://github.com/kvnloo/z0evals/blob/1ec7c67e36cd6dfa57416b7afdd63ada2805158a/studies/harness-speed-v1/protocol.md); installed revisions: [manifest](https://github.com/kvnloo/z0evals/blob/1ec7c67e36cd6dfa57416b7afdd63ada2805158a/studies/harness-speed-v1/manifest.yaml).

## cold is not warm {#latency}

same-session s3 results from the [frozen analysis](https://github.com/kvnloo/z0evals/blob/1ec7c67e36cd6dfa57416b7afdd63ada2805158a/studies/harness-speed-v1/analysis/summary.md). cold first-token medians, with bootstrap confidence intervals:

| arm | first token s | total s |
|---|---:|---:|
| fx-base | 2.00 [1.94, 2.08] | 2.11 |
| fx-cli | 2.22 [2.03, 2.38] | 2.22 |
| pi-base | 2.09 [1.96, 2.15] | 5.17 |
| omp-base | 4.07 [3.79, 4.25] | 4.22 |
| hermes-base | 11.13 [10.79, 11.58] | 12.98 |
| hermes-default-ft | 6.17 [5.91, 6.45] | 6.78 |
| hermes-speed-guided | 5.61 [5.44, 5.96] | 6.03 |
| hermes-speed | 3.18 [3.03, 3.30] | 3.67 |

all cold arms were 32/32 correct. the isolated speed profile drops safe mode and instruction-driven arithmetic tool use, among other configuration. those are separate contrasts, not an additive breakdown of the total gap.

warm hermes-speed through acp reached 1.83 s [1.74, 1.93], with 30/30 correct. that is a long-lived process and a fresh conversation, not the interactive tui. the cold ranking does not survive unchanged.

## all passing is not a quality ranking {#tasks}

the [frozen analysis](https://github.com/kvnloo/z0evals/blob/1ec7c67e36cd6dfa57416b7afdd63ada2805158a/studies/harness-speed-v1/analysis/summary.md) reports these task medians:

| arm | small tasks: wall s / passed | harder tasks: wall s / passed |
|---|---:|---:|
| fx-base | 18.1 / 16/16 | 34.4 / 12/12 |
| pi-base | 22.2 / 16/16 | 40.6 / 12/12 |
| fx-cli | 29.5 / 16/16 | 54.7 / 12/12 |
| hermes-speed | 31.7 / 16/16 | 51.4 / 12/12 |
| hermes-speed-guided | 31.3 / 16/16 | 57.5 / 12/12 |
| hermes-base | 45.0 / 16/16 | 67.7 / 12/12 |

all 168 counted task runs passed the runtime verifier. visible tests were restored and hidden tests added. none of this separates quality. it separates the work spent reaching an easy passing result.

## the failed attempt stays visible {#excluded}

the [manifest](https://github.com/kvnloo/z0evals/blob/1ec7c67e36cd6dfa57416b7afdd63ada2805158a/studies/harness-speed-v1/manifest.yaml) retains 19 aborted task rows, including 3 failures, excluded together after working-directory contamination. the counted rerun starts from restored fixtures. work copies were deleted by the original runner. later checks can audit the receipts and verifier, but cannot independently replay each submitted patch.

## what this does not prove {#limits}

we did not reproduce the inference runs for this draft. these are source-reported local measurements, not new independent results. one build laptop, short synthetic tasks and a shared provider account do not establish a general harness winner. host interference was not continuously measured. compare arms within sessions, not across them. list-price estimates are not subscription bills. provenance and these limits are in the [manifest](https://github.com/kvnloo/z0evals/blob/1ec7c67e36cd6dfa57416b7afdd63ada2805158a/studies/harness-speed-v1/manifest.yaml).

