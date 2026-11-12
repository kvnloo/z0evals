import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rp06", ROOT / "scripts/rp06_measurements.py")
rp06 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp06)


class MeasurementsTest(unittest.TestCase):
    def test_warmup_excluded_but_tail_retained(self):
        rows = [dict(rep=-1, ttft_s=99, correct=True)] + [
            dict(rep=i, ttft_s=t, correct=True)
            for i, t in enumerate([0.3, 0.4, 13.5])
        ]
        result = rp06.latency(rows)
        self.assertEqual(result["n"], 3)
        self.assertEqual(result["median_s"], 0.4)
        self.assertEqual(result["max_s"], 13.5)

    def test_failed_latency_sample_is_not_silently_dropped(self):
        result = rp06.latency([dict(rep=0, ttft_s=None, correct=False)])
        self.assertEqual(result["n"], 1)
        self.assertEqual(result["timed"], 0)
        self.assertEqual(result["correct"], 0)

    def test_parallel_totals_and_unrun_work(self):
        rows = [dict(id=0, ok=True, completion_tokens=100, t=1.0, s=1.0)]
        summary = dict(units=5, ok=1, failed=0, not_run=4,
                       wall_s=2.0, completion_tokens=100, aggregate_tok_s=50.0)
        result = rp06.parallel(rows, summary)
        self.assertEqual(result["not_run"], 4)
        self.assertEqual(result["recorded_tok_s"], 50.0)
        self.assertEqual(result["token_count_provenance"], "unverified")

    def test_mismatched_total_rejected(self):
        rows = [dict(id=0, ok=True, completion_tokens=99, t=1.0, s=1.0)]
        summary = dict(units=1, ok=1, failed=0, not_run=0,
                       wall_s=2.0, completion_tokens=100, aggregate_tok_s=50.0)
        with self.assertRaises(ValueError):
            rp06.parallel(rows, summary)

    def test_frozen_data_and_hash_gate(self):
        path = ROOT / "docs/drafts/RP06/measurements.json"
        result = rp06.verify(path)
        self.assertEqual(len(result["parallel"]), 3)
        self.assertEqual(result["latency"]["n"], 12)
        data = rp06.load(path)
        changed = copy.deepcopy(data)
        changed["sources"][0]["data"][0]["rep"] = 999
        with self.assertRaises(ValueError):
            rp06.verify_data(changed)


if __name__ == "__main__":
    unittest.main()
