import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).parent
spec = importlib.util.spec_from_file_location('memory_score', ROOT / 'score.py')
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ScoreTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((ROOT / 'data/synthetic.json').read_text())
        self.result = {'provider': 'test', 'corpus': 'synthetic-public', 'k': 5,
                       'ingest_seconds': 1, 'rows': [
                           {'query_id': q['id'], 'ids': q['relevant'], 'latency_ms': i + 1}
                           for i, q in enumerate(self.fixture['queries'])]}

    def test_perfect(self):
        r = module.score(self.fixture, self.result)
        self.assertEqual(r['recall_at_5'], 1)
        self.assertEqual(r['mrr_at_5'], 1)
        self.assertEqual(r['updated_document_top1_rate'], 1)
        self.assertIsNone(r['cost_per_1k_queries_usd'])

    def test_stale_first_is_not_temporal_success(self):
        r = copy.deepcopy(self.result)
        next(x for x in r['rows'] if x['query_id'] == 'updated')['ids'] = ['atlas-old', 'atlas-new']
        s = module.score(self.fixture, r)
        self.assertEqual(s['recall_at_5'], 1)
        self.assertLess(s['mrr_at_5'], 1)
        self.assertEqual(s['updated_document_top1_rate'], 0)

    def test_k_is_enforced(self):
        r = copy.deepcopy(self.result)
        next(x for x in r['rows'] if x['query_id'] == 'exact')['ids'] = ['x'] * 5 + ['atlas-new']
        self.assertLess(module.score(self.fixture, r)['recall_at_5'], 1)

    def test_frozen_population_and_labels(self):
        for name in ['ctx', 'hermes', 'tencent']:
            r = json.loads((ROOT / f'data/{name}.json').read_text())
            self.assertEqual(len(r['rows']), 50)
            self.assertEqual(len({x['query_id'] for x in r['rows']}), 10)
            self.assertEqual(r['corpus'], 'synthetic-public')
        self.assertEqual(module.percentile(list(range(1, 101)), .95), 95)


if __name__ == '__main__':
    unittest.main()
