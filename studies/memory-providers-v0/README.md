# Memory providers v0: incomplete synthetic retrieval probe

This is a frozen small-fixture result, not a five-provider winner selection. Supermemory and GraphRAG have no equivalent retrieval measurement here. No personal history or private corpus is included.

## Scope

Eight synthetic documents, ten fixed queries, five repetitions each. Nine answerable queries contribute to recall@5 and truncated MRR@5; the absent-answer query is scored separately. p50 is median; p95 is nearest-rank over 50 end-to-end calls. Corpus, queries and planted answers are in data/synthetic.json. All implementations receive exactly the same query text. Repetitions are warm samples, not independent work items or a confidence interval.

| Native surface | Recall@5 | MRR@5 | p50 ms | p95 ms | ingest/setup seconds | newest doc top-1 |
|---|---:|---:|---:|---:|---:|---:|
| ctx 2.2.8 lexical CLI | 1.000 | 0.944 | 17.896 | 35.190 | 0.649 | 0/5 |
| Hermes session_search (SQLite FTS5) | 1.000 | 0.944 | 0.666 | 2.043 | 3.376 | 0/5 |
| TencentDB local v3 conversation/search | 1.000 | 0.944 | 1.267 | 16.221 | 0.945 | 0/5 |
| GraphRAG | not run | not run | not run | not run | not run | not run |
| Supermemory | key unavailable | not run | not run | not run | not run | not run |

All measured surfaces return no result for the absent-evidence query. All return both Atlas facts for the update query, with the old document first. This is retrieval ordering, NOT a generated answer or contradiction resolution verdict. The new document itself mentions the old value, so substring-answer scoring would be misleading.

Cost per 1k local queries is unmeasured, not $0: no query API invoice was collected, and hardware/energy/background extraction were not metered. No hosted billing was incurred by this harness.

## Reproduce

Run score.py to recompute results.json from the committed receipts; test_score.py checks labels, k truncation, populations and supersession scoring. run.py calls actual backends, not emulated SQL or token matching. It has no hosted upload path.

    python3 studies/memory-providers-v0/score.py
    python3 studies/memory-providers-v0/test_score.py
    python3 scripts/validate.py

To collect new receipts (use fresh state directories and a clean TencentDB evaluation tenancy; do not append another run to the existing one):

    python3 studies/memory-providers-v0/run.py ctx --state /absolute/private/eval-state/ctx --output /absolute/eval-output/ctx.json
    <Hermes-runtime-python> studies/memory-providers-v0/run.py hermes --state /absolute/private/eval-state/hermes --hermes-source /absolute/pinned/hermes-source --output /absolute/eval-output/hermes.json
    python3 studies/memory-providers-v0/run.py tencent --state /absolute/private/eval-state/tencent --output /absolute/eval-output/tencent.json

Hermes needs its installed runtime dependencies and matching source; clear inherited PYTHONPATH/PYTHONHOME. ctx requires the installed 2.2.8 CLI. The runner explicitly disables automatic source discovery, telemetry, auto-upgrades, and daemon supervision for its isolated ctx root. TencentDB expects a local gateway on loopback port 8420 with local/default service authorization; the fixture writes to a separate synthetic tenancy, never the owner's default tenancy. run.py is a tiny receipt-generation helper, not a production routing or experiment framework.

## Limitations and missing acceptance criteria

- No five-way same-corpus comparison, no full real-corpus comparison, and no Supermemory live integration qualification.
- Historical GraphRAG work measures extraction entity/relationship F1 and model runtimes, not retrieval recall/MRR; those scores are not comparable to this table.
- TencentDB conversation search is L0 only. Its health reports embeddingService=false. L1/L2/L3 extraction and semantic-memory behavior are not evaluated. The API replaces supplied message timestamps with ingestion time; ordered ingestion does not establish historical-date fidelity.
- Ingest includes Python imports, database opening and initial schema setup for Hermes, CLI import for ctx, and eight HTTP writes for TencentDB. It is not isolated steady-state ingestion throughput.
- ctx CLI process cost is included, unlike in-process Hermes. Latencies are native integration surface timings, not engine-only rankings.
- Tiny easy fixture; all corpora fit in a handful of documents. No representative accuracy claim, confidence interval, or profile activation recommendation follows from these numbers.
- Local probes execute beside the installed groot providers; result scoring and validation are offloaded through fleet to the mbp node. No substantial corpus re-indexing is part of the qualified run.
- Initial ctx default-mode attempt unexpectedly started broad local discovery/supervision and timed out. It was stopped; the runner was corrected before the frozen run. No content from that failed attempt is published. Canonical local service registration and identity-verified ownership were restored and checked separately.

## Supermemory staging and self-hosting assessment

The Hermes catalog provider is pinned to supermemoryai/hermes-supermemory 91405dd00fdf2a0b3515b25c25557598f6793299 (v1.0.1). It was downloaded disabled to an isolated Hermes home. Hosted testing stops without SUPERMEMORY_API_KEY. No live profile was activated and no private data was uploaded.

Vendor documentation currently describes a proprietary downloadable local server binary, NOT an open-source server in the public supermemory repository. Linux x64/arm64 and macOS Intel/Apple Silicon are supported; local graph storage and bge-base-en-v1.5 embeddings are embedded. An LLM endpoint is still needed for extraction. Fully local text processing requires a local LLM and disabled telemetry/update checks; webpage ingestion uses Firecrawl. These are source-reported capabilities, not reproduced server tests. The pinned Hermes plugin requires SDK >=3.50.0,<4, while current vendor quickstarts use SDK v5; API/server compatibility must be tested rather than assumed.
