#!/usr/bin/env python3
"""Score frozen retrieval receipts, never assign scores to unrun backends."""
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).parent


def percentile(values, q):
    return sorted(values)[max(0, math.ceil(len(values) * q) - 1)]


def score(fixture, result):
    labels = {q['id']: q for q in fixture['queries']}
    recalls, reciprocal, abstention, updated = [], [], [], []
    for r in result['rows']:
        q = labels[r['query_id']]
        ids = r['ids'][:result['k']]
        if q['relevant']:
            recalls.append(len(set(ids) & set(q['relevant'])) / len(q['relevant']))
            reciprocal.append(next((1 / (i + 1) for i, x in enumerate(ids) if x in q['relevant']), 0))
        else:
            abstention.append(not ids)
        if q['kind'] == 'supersession':
            updated.append(bool(ids) and ids[0] in q['relevant'])
    latency = [r['latency_ms'] for r in result['rows']]
    return {'provider': result['provider'], 'corpus': result['corpus'],
            'n_observations': len(latency), 'unique_queries': len({r['query_id'] for r in result['rows']}),
            'recall_at_5': statistics.mean(recalls), 'mrr_at_5': statistics.mean(reciprocal),
            'abstention_retrieval_rate': statistics.mean(abstention),
            'updated_document_top1_rate': statistics.mean(updated),
            'p50_ms': statistics.median(latency), 'p95_ms': percentile(latency, .95),
            'ingest_seconds': result['ingest_seconds'],
            'cost_per_1k_queries_usd': None,
            'cost_note': 'No per-call local API invoice; hardware, energy and background extraction unmetered.'}


def main():
    fixture = json.loads((ROOT / 'data/synthetic.json').read_text())
    results = [score(fixture, json.loads(p.read_text())) for p in sorted((ROOT / 'data').glob('*.json'))
               if p.stem in ('ctx', 'hermes', 'tencent')]
    data = {'schema': 'memory-provider-results.v1', 'status': 'incomplete',
            'results': results, 'not_run': {
                'supermemory': 'Hosted credential unavailable; no uploads attempted.',
                'graphrag': 'Existing extraction benchmark is not a labelled retrieval benchmark. No equivalent retrieval run.'}}
    (ROOT / 'results.json').write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps(data, indent=2))


if __name__ == '__main__':
    main()
