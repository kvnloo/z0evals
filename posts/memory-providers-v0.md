---
title: perfect recall, stale first
subtitle: three native retrieval surfaces found the fixture. none put the new fact first.
study: memory-providers-v0
status: draft
author: zer0 research
date: october 21, 2026
mock_data: false
toc:
- id: question
  label: what we asked
- id: method
  label: the same small fixture
- id: results
  label: the results
- id: ordering
  label: retrieval is not resolution
- id: limits
  label: what this does not prove
---

<div class="lede">
we wanted a same-corpus comparison of memory providers. we got a smaller result: three measured native surfaces, a stale-first update query, and two missing arms. that is still worth keeping.
</div>

<div class="hero-rule"></div>

## what we asked {#question}

can native retrieval recover the planted answer? after an update, does the latest document rank first? these are retrieval questions. no model generated an answer from the results.

## the same small fixture {#method}

eight synthetic documents. ten fixed queries. five repetitions per query. nine answerable queries contribute to recall@5 and truncated mrr@5. the absent-answer query is scored separately. the repetitions are warm samples, not independent work items.

we used each provider's native surface. ctx includes cli process overhead. hermes runs in process. tencentdb uses its local conversation/search surface. the timings include those differences.

## the results {#results}

| native surface | recall@5 | mrr@5 | p50 ms | p95 ms | newest document top-1 |
|---|---:|---:|---:|---:|---:|
| ctx 2.2.8 lexical cli | 1.000 | 0.944 | 17.896 | 35.190 | 0/5 |
| hermes session_search / fts5 | 1.000 | 0.944 | 0.666 | 2.043 | 0/5 |
| tencentdb local conversation/search | 1.000 | 0.944 | 1.267 | 16.221 | 0/5 |
| graphrag | not run | not run | not run | not run | not run |
| supermemory | key unavailable | not run | not run | not run | not run |

all measured surfaces returned no result for the absent-evidence query. the three measured arms tie on these retrieval scores. that does not select a provider.

## retrieval is not resolution {#ordering}

all three returned both versions of the updated fact, with the old document first. the new document also mentions the old value. substring scoring would make that look more reassuring than it is. document identity, rank and version matter.

supermemory was staged disabled. no hosted credential was available, so no live test or private upload happened. the vendor's local-server capabilities are source-reported, not reproduced here. graphrag's earlier extraction results are not a substitute for retrieval measurements.

## what this does not prove {#limits}

this fixture is tiny and easy. no representative accuracy, five-way winner or activation recommendation follows. newest-document rank is not an answer-quality or contradiction-resolution verdict.

tencentdb's embedding service was disabled. this is its conversation layer, not semantic extraction across its memory layers. it also replaces supplied message timestamps with ingestion time, so historical-date fidelity was not established.

ctx's source revision and the running tencentdb gateway build were not exposed. the native-surface timing differences are not engine-only rankings. ingest/setup includes different work in each arm.

cost per query is unmeasured, not zero. there was no hosted per-call invoice, but hardware, energy and background extraction were not metered. we read the frozen result and scorer during this harvest; we did not recollect provider calls.

source for the fixture, population and rounded table: [study readme](https://github.com/kvnloo/z0evals/blob/13480b1635fdd19f88da7c9910a5b59cf28f0eb2/studies/memory-providers-v0/README.md). exact stored measurements: [results](https://github.com/kvnloo/z0evals/blob/13480b1635fdd19f88da7c9910a5b59cf28f0eb2/studies/memory-providers-v0/results.json). scoring contract: [scorer](https://github.com/kvnloo/z0evals/blob/13480b1635fdd19f88da7c9910a5b59cf28f0eb2/studies/memory-providers-v0/score.py). missing arms and draft state: [pr #114](https://github.com/kvnloo/z0evals/pull/114).
