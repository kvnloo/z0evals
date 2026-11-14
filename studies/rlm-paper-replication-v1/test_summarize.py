"""Focused, bounded checks for public aggregation, not upstream scoring.

reuse-checked: unittest, existing study summaries, bench/test_paper_matrix.py.
"""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

import summarize as s


def row(task="a", rep=0, score=1., valid=True, **extra):
    result = dict(task_id=task, rep=rep, family="S-NIAH", size_tokens=4096,
                  arm=s.ARMS[0], root_model=s.ROOT, sub_model=s.MODELS[1], valid=valid,
                  score=score, protocol={"disable_thinking": True}, wall_s=0,
                  accounting={"usage_complete": False, "request_attempts": 2,
                              "requests": [{"role": "root", "prompt_tokens": 0, "completion_tokens": 2, "latency": .25},
                                           {"role": "root", "prompt_tokens": None, "completion_tokens": None}]})
    result.update(extra)
    return result


def audit_row(raw, state="not_applicable_base", collection_valid=None):
    result = deepcopy(raw)
    result.update(audit_version=s.AUDIT_VERSION, audit_adherence=state, audit_reasons=[],
                  audit_source_sha256={"auditor": "a" * 64},
                  collection_valid=raw["valid"] if collection_valid is None else collection_valid)
    return result


class SummaryTests(unittest.TestCase):
    def aggregate(self, rows, name="matrix-v2-sniah.jsonl", **kwargs):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / name
            path.write_text("".join(json.dumps(r) + "\n" for r in rows))
            return s.aggregate([path], **kwargs)

    def selected(self, result):
        return next(g for g in result["primary"] if g["family"] == "S-NIAH" and g["arm"] == s.ARMS[0])

    def test_empty_is_missing_not_zero(self):
        result = s.aggregate()
        self.assertEqual(sum(g["scheduled"] for g in result["primary"]), 300)
        self.assertEqual(sum(g["observed"] for g in result["primary"]), 0)
        group = self.selected(result)
        self.assertIsNone(group["mean_score"])
        self.assertIsNone(group["measurements"]["wall_s"]["sum_known"])
        self.assertEqual(group["missing"], 9)

    def test_invalid_is_not_wrong_and_missing_usage_survives(self):
        group = self.selected(self.aggregate([row(), row("b", valid=False, score=0)]))
        self.assertEqual((group["valid"], group["invalid"], group["missing"]), (1, 1, 7))
        self.assertEqual(group["mean_score"], 1)
        self.assertEqual(group["usage_partial_rows"], 2)
        self.assertEqual(group["measurements"]["root_prompt_tokens"]["sum_known"], 0)
        self.assertEqual(group["measurements"]["root_request_latency_s"]["sum_known"], .5)
        self.assertIsNone(group["measurements"]["tool_calls"]["sum_known"])
        self.assertIsNone(group["measurements"]["root_api_attempts"]["sum_known"])

    def test_unknown_tokens_are_not_zero_filled_ledger_sums(self):
        unknown = row(accounting={"root_prompt_tokens": 0, "requests": [
            {"role": "root", "prompt_tokens": None, "completion_tokens": None}]})
        group = self.selected(self.aggregate([unknown]))
        self.assertIsNone(group["measurements"]["root_prompt_tokens"]["sum_known"])
        self.assertEqual(group["measurements"]["sub_prompt_tokens"]["sum_known"], 0)
        self.assertEqual(group["usage_unknown_rows"], 1)

    def test_task_bootstrap_deterministic_order_independent(self):
        rows = [row(task, rep, value) for task, value in (("a", 0.), ("b", 1.), ("c", .5)) for rep in range(3)]
        first = self.aggregate(rows)
        self.assertEqual(first, self.aggregate(list(reversed(rows))))
        group = self.selected(first)
        self.assertEqual(group["mean_score"], .5)
        self.assertEqual(group["score_ci95"], [0., 1.])
        self.assertEqual(group["score_ci_status"], "descriptive")
        self.assertEqual(group["task_clusters_ge3_valid"], 3)
        self.assertEqual(group["binary_task_outcome"]["status"], "not_applicable")

    def test_one_task_and_partial_repeats_suppress_ci(self):
        one = self.selected(self.aggregate([row(rep=i) for i in range(3)]))
        self.assertIsNone(one["score_ci95"])
        self.assertEqual(one["score_ci_status"], "insufficient_task_clusters")
        partial = self.selected(self.aggregate([row("a", 0, 0.), row("b", 0, 1.)]))
        self.assertEqual(partial["score_ci_status"], "insufficient_repeats")
        self.assertIsNone(partial["score_ci95"])

    def test_wilson_uses_tasks_not_repeats(self):
        rows = [row(task, rep, score) for task, score in (("a", 0.), ("b", 1.), ("c", 1.)) for rep in range(3)]
        binary = self.selected(self.aggregate(rows))["binary_task_outcome"]
        self.assertEqual(binary["eligible_tasks"], 3)
        self.assertEqual(binary["successful_tasks"], 2)
        self.assertEqual(binary["ci95"], s.wilson(2, 3))
        self.assertNotEqual(binary["ci95"], s.wilson(6, 9))

    def test_task_weighting_and_graded_scores(self):
        rows = [row("a", i, .25, family="OOLONG", size_tokens=1024) for i in range(3)]
        rows += [row("b", 0, .75, family="OOLONG", size_tokens=1024)]
        group = next(g for g in self.aggregate(rows)["primary"] if g["family"] == "OOLONG" and g["arm"] == s.ARMS[0])
        self.assertEqual(group["metric"], "graded_score")
        self.assertEqual(group["mean_score"], .5)
        self.assertEqual(group["row_mean_score"], .375)
        self.assertEqual(group["binary_task_outcome"]["status"], "not_applicable")
        pairs = row(family="OOLONG-Pairs", size_tokens=1024, score=.4)
        group = next(g for g in self.aggregate([pairs])["primary"] if g["family"] == "OOLONG-Pairs" and g["arm"] == s.ARMS[0])
        self.assertEqual(group["metric"], "pair_f1")
        self.assertEqual(group["mean_score"], .4)

    def test_reject_duplicate_mixed_or_invalid_inputs(self):
        cases = [[row(), row()], [row(), row("b", protocol={"disable_thinking": True, "max_tokens": 7})],
                 [row(score=float("nan"))], [row(rep=3)], [row(protocol={})]]
        for rows in cases:
            with self.subTest(rows=len(rows)), self.assertRaises(ValueError):
                self.aggregate(rows)
        with self.assertRaises(ValueError):
            self.aggregate([row()], name="matrix-sniah.jsonl")

    def test_separate_smoke_and_pilot(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for name, thinking in (("smoke.jsonl", False), ("matrix-v2-smoke.jsonl", True), ("matrix-sniah.jsonl", False)):
                path = Path(directory) / name
                path.write_text(json.dumps(row(protocol={"disable_thinking": thinking})) + "\n")
                paths.append(path)
            result = s.aggregate(smoke=paths[:2], pilot=paths[2:])
        self.assertEqual(sum(g["observed"] for g in result["primary"]), 0)
        self.assertEqual(len(result["smoke"]), 2)
        self.assertEqual(len(result["pilot"]), 1)
        self.assertEqual({g["cohort"] for g in result["smoke"]}, {"normal-smoke", "thinking-off-smoke"})

    def test_ingress_and_client_hash_separate_primary_protocols(self):
        cli = row(protocol={"disable_thinking": True, "hermes_ingress": "cli"})
        library = row("b", protocol={"disable_thinking": True, "hermes_ingress": "library"})
        self.assertNotEqual(s.fingerprint(s.public_protocol(cli)), s.fingerprint(s.public_protocol(library)))
        with self.assertRaises(ValueError):
            self.aggregate([cli, library])
        changed = deepcopy(library)
        changed["protocol"]["hermes_client_sha256"] = "a" * 64
        self.assertNotEqual(s.fingerprint(s.public_protocol(library)), s.fingerprint(s.public_protocol(changed)))
        with self.assertRaises(ValueError):
            self.aggregate([library, changed])

    def test_library_smoke_is_its_own_five_arm_cohort(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "matrix-v2-smoke-library.jsonl"
            rows = [row(arm=arm, protocol={"disable_thinking": True, "hermes_ingress": "library"}) for arm in s.ARMS]
            path.write_text("".join(json.dumps(r) + "\n" for r in rows))
            result = s.aggregate(smoke=[path])
        self.assertEqual(len(result["smoke"]), 5)
        self.assertEqual(sum(g["valid"] for g in result["smoke"]), 5)
        self.assertEqual({g["cohort"] for g in result["smoke"]}, {"library-thinking-off-smoke"})
        self.assertEqual(sum(g["observed"] for g in result["primary"]), 0)

    def test_closed_states_missing_status_and_invalid_not_missing(self):
        self.assertEqual(s.aggregate()["status"], "ongoing")
        self.assertEqual(s.aggregate(closed=True)["status"], "partial")
        rows = [row(f"{family}-{size}-{task}", rep, None, False,
                    family=family, size_tokens=size, arm=arm)
                for family, size, n in s.PLAN for task in range(n)
                for arm in s.ARMS for rep in range(3)]
        complete = self.aggregate(rows, closed=True)
        self.assertEqual(complete["status"], "bounded_complete")
        self.assertEqual(sum(g["invalid"] for g in complete["primary"]), 300)
        self.assertEqual(self.aggregate(rows[:-1], closed=True)["status"], "partial")
        self.assertEqual(self.aggregate(rows)["status"], "ongoing")
        missing = deepcopy(complete)
        del missing["status"]
        with self.assertRaises(ValueError):
            s.validate_public(missing)
        partial = s.aggregate(closed=True)
        partial["status"] = "bounded_complete"
        with self.assertRaises(ValueError):
            s.validate_public(partial)

    def test_require_audit_rejects_collection_and_incomplete_metadata(self):
        raw = row(collection_valid=True, audit_adherence="adherent")
        with self.assertRaises(ValueError):
            self.aggregate([raw], require_audit=True)
        audited = audit_row(row())
        for key in ("audit_version", "collection_valid", "audit_source_sha256", "audit_reasons"):
            broken = deepcopy(audited)
            del broken[key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.aggregate([broken], require_audit=True)
        with self.assertRaises(ValueError):
            self.aggregate([audited])
        with self.assertRaises(ValueError):
            self.aggregate([audited, row("b")], require_audit=True)
        promoted = audit_row(row(collection_valid=False))
        promoted["collection_valid"] = False
        with self.assertRaises(ValueError):
            self.aggregate([promoted], require_audit=True)

    def test_strict_scores_counts_intervals_and_private_evidence(self):
        rows = [audit_row(row(task, rep, score)) for task, score in (("a", .25), ("b", .75)) for rep in range(3)]
        rejected = audit_row(row("c", score=None, valid=False), state="nonadherent", collection_valid=True)
        rejected.update(audit_reasons=["missing_validated_final"], audit_final={"answer": "PRIVATE-AUDIT-SENTINEL"},
                        collection_answer="PRIVATE-AUDIT-SENTINEL", collection_score=1.)
        result = self.aggregate(rows + [rejected], require_audit=True)
        group = self.selected(result)
        self.assertEqual(result["audit_policy"], "paper_strict_v1")
        self.assertEqual((group["valid"], group["invalid"], group["missing"]), (6, 1, 2))
        self.assertEqual((group["collection_valid"], group["collection_invalid"]), (7, 0))
        self.assertEqual(group["protocol_not_applicable"], 6)
        self.assertEqual(group["protocol_nonadherent"], 1)
        self.assertEqual(group["mean_score"], .5)
        self.assertEqual(group["score_ci95"], [.25, .75])
        self.assertNotIn("PRIVATE-AUDIT-SENTINEL", json.dumps(result))
        self.assertEqual(result, self.aggregate(list(reversed(rows + [rejected])), require_audit=True))
        self.assertIsNone(self.selected(self.aggregate([rejected], require_audit=True))["mean_score"])
        for key in s.AUDIT_COUNTS:
            modified = deepcopy(result)
            modified["primary"][0][key] = "not-a-count"
            with self.assertRaises(ValueError):
                s.validate_public(modified)

    def test_unaudited_adherence_is_unknown_and_provisional(self):
        result = self.aggregate([row(), row("b", valid=False, score=None)])
        group = self.selected(result)
        self.assertEqual(result["audit_policy"], "collection_snapshot")
        self.assertEqual(group["protocol_unknown"], group["observed"])
        self.assertEqual(group["protocol_adherent"], 0)
        self.assertEqual((group["collection_valid"], group["collection_invalid"]), (1, 1))
        self.assertEqual(result["protocols"][0]["audit_version"], "not_audited")
        self.assertIsNone(result["protocols"][0]["auditor_sha256"])
        modified = deepcopy(result)
        modified["audit_policy"] = "paper_strict_v1"
        with self.assertRaises(ValueError):
            s.validate_public(modified)

    def test_audit_hash_is_fingerprinted_and_valid_child_errors_rejected(self):
        first = audit_row(row(arm="released-rlm"), state="adherent")
        second = deepcopy(first)
        second["audit_source_sha256"]["auditor"] = "b" * 64
        self.assertNotEqual(s.fingerprint(s.public_protocol(first)), s.fingerprint(s.public_protocol(second)))
        with self.assertRaises(ValueError):
            self.aggregate([first, second], require_audit=True)
        first["audit_reasons"] = ["child_error"]
        with self.assertRaises(ValueError):
            self.aggregate([first], require_audit=True)
        nano = audit_row(row(arm="nano-rlm", valid=False, score=None), state="unknown", collection_valid=True)
        group = next(g for g in self.aggregate([nano], require_audit=True)["primary"]
                     if g["family"] == "S-NIAH" and g["arm"] == "nano-rlm")
        self.assertEqual(group["protocol_unknown"], 1)
        self.assertEqual(group["valid"], 0)

    def test_privacy_checker_ignores_only_standard_caches(self):
        import check_public
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in check_public.ALLOWED:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('"""reuse-checked: fixture."""\n')
            (root / "data/summary.json").write_text(json.dumps(s.aggregate()))
            for cache in (".ruff_cache", "__pycache__", ".pytest_cache"):
                (root / cache).mkdir()
                (root / cache / "cache-entry").write_text("fixture")
            check_public.main(root)
            (root / "unexpected.jsonl").write_text("{}\n")
            with self.assertRaises(ValueError):
                check_public.main(root)

    def test_closed_privacy_schema(self):
        private = "PRIVATE-CONTEXT-SENTINEL"
        raw = row(answer=private, question=private, gold=private, context_path=private,
                  protocol={"disable_thinking": True, "home_template": private})
        result = self.aggregate([raw])
        self.assertNotIn(private, json.dumps(result))
        for mutation in ("answer", "question", "task_id", "context", "requests", "audit_reasons", "audit_final", "collection_answer"):
            modified = deepcopy(result)
            modified["primary"][0][mutation] = private
            with self.assertRaises(ValueError):
                s.validate_public(modified)
        modified = deepcopy(result)
        modified["primary"][0]["family"] = private
        with self.assertRaises(ValueError):
            s.validate_public(modified)

    def test_require_audit_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory) / "matrix-v2-sniah.jsonl"
            out = Path(directory) / "summary.json"
            raw.write_text(json.dumps(row()) + "\n")
            with self.assertRaises(ValueError):
                s.main(["--raw", str(raw), "--require-audit", "--out", str(out)])
            self.assertFalse(out.exists())
            raw.write_text(json.dumps(audit_row(row())) + "\n")
            s.main(["--raw", str(raw), "--require-audit", "--out", str(out)])
            self.assertEqual(json.loads(out.read_text())["audit_policy"], "paper_strict_v1")
            s.main(["--check", str(out)])

    def test_cli_round_trip_and_check(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory) / "matrix-v2-sniah.jsonl"
            out = Path(directory) / "summary.json"
            raw.write_text(json.dumps(row()) + "\n")
            s.main(["--raw", str(raw), "--out", str(out)])
            first = out.read_bytes()
            s.main(["--raw", str(raw), "--out", str(out)])
            self.assertEqual(first, out.read_bytes())
            s.main(["--check", str(out)])
            s.main(["--raw", str(raw), "--closed", "--out", str(out)])
            self.assertEqual(json.loads(out.read_text())["status"], "partial")


if __name__ == "__main__":
    unittest.main()
