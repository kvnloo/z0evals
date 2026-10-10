#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import protected_eval as P  # noqa: E402


class ProtectedEvaluatorTests(unittest.TestCase):
    def _manifest(self) -> dict:
        return P.load_manifest(REPO / "studies" / "protected-evaluator-v0" / "evaluator.yaml")

    def _write_jsonl(self, path: Path, rows: list[dict]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    def _fixture(self, root: Path) -> tuple[Path, Path, Path]:
        protected = root / "protected"
        development = root / "development"
        self._write_jsonl(
            protected / "confirm.jsonl",
            [
                {"id": "sealed-item-1", "expected": "alpha", "group": "g1"},
                {"id": "sealed-item-2", "expected": "beta", "group": "g2"},
            ],
        )
        self._write_jsonl(
            protected / "future.jsonl",
            [{"id": "future-item-1", "expected": "omega", "group": "future"}],
        )
        self._write_jsonl(
            development / "development.jsonl",
            [{"id": "dev-item-1", "expected": "dev", "group": "dev"}],
        )
        predictions = root / "predictions.jsonl"
        self._write_jsonl(
            predictions,
            [
                {"id": "sealed-item-1", "prediction": "alpha"},
                {"id": "sealed-item-2", "prediction": "wrong"},
            ],
        )
        return protected, development, predictions

    def _env(self, protected: Path, development: Path):
        return patch.dict(
            os.environ,
            {
                "Z0EVAL_PROTECTED_ROOT": str(protected),
                "Z0EVAL_DEVELOPMENT_ROOT": str(development),
            },
            clear=False,
        )

    def test_checked_in_manifest_is_valid_and_future_is_separate(self) -> None:
        manifest = self._manifest()
        self.assertEqual(manifest["schema"], "z0eval.protected.v1")
        self.assertTrue(manifest["cohorts"]["confirm"]["optimizer_queryable"])
        self.assertFalse(manifest["cohorts"]["confirm"]["training_allowed"])
        self.assertFalse(manifest["cohorts"]["future"]["optimizer_queryable"])

    def test_score_output_and_audit_do_not_expose_protected_truth(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            protected, development, predictions = self._fixture(root)
            state_dir = root / "state"
            with self._env(protected, development):
                result = P.score_predictions(
                    self._manifest(),
                    cohort_name="confirm",
                    predictions_path=predictions,
                    candidate_id="candidate-1",
                    candidate_revision="b" * 40,
                    state_dir=state_dir,
                )
            self.assertEqual(result["score"], 0.5)
            self.assertEqual(result["verdict"], "DISCARD")
            public = json.dumps(result, sort_keys=True)
            audit = (state_dir / "queries.jsonl").read_text(encoding="utf-8")
            for protected_value in ("alpha", "beta", "sealed-item-1", "sealed-item-2"):
                self.assertNotIn(protected_value, public)
                self.assertNotIn(protected_value, audit)
            self.assertIn("predictions_sha256", audit)
            self.assertNotIn(str(protected), audit)

    def test_prediction_vector_must_cover_the_complete_cohort(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            protected, development, predictions = self._fixture(root)
            self._write_jsonl(predictions, [{"id": "sealed-item-1", "prediction": "alpha"}])
            with self._env(protected, development):
                with self.assertRaisesRegex(P.ProtectedEvalError, "exactly match"):
                    P.score_predictions(
                        self._manifest(), cohort_name="confirm", predictions_path=predictions,
                        candidate_id="candidate-short", candidate_revision="c" * 40,
                        state_dir=root / "state",
                    )

    def test_repeated_queries_are_counted_and_budget_exhausts(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            protected, development, predictions = self._fixture(root)
            manifest = copy.deepcopy(self._manifest())
            manifest["scoring"]["max_queries"] = 2
            with self._env(protected, development):
                first = P.score_predictions(
                    manifest, cohort_name="confirm", predictions_path=predictions,
                    candidate_id="candidate-a", candidate_revision="d" * 40,
                    state_dir=root / "state",
                )
                second = P.score_predictions(
                    manifest, cohort_name="confirm", predictions_path=predictions,
                    candidate_id="candidate-b", candidate_revision="e" * 40,
                    state_dir=root / "state",
                )
                self.assertEqual((first["query_index"], second["query_index"]), (1, 2))
                with self.assertRaisesRegex(P.ProtectedEvalError, "budget exhausted"):
                    P.score_predictions(
                        manifest, cohort_name="confirm", predictions_path=predictions,
                        candidate_id="candidate-c", candidate_revision="f" * 40,
                        state_dir=root / "state",
                    )

    def test_contamination_invalidates_sealed_credit_without_leaking_reason(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            protected, development, predictions = self._fixture(root)
            manifest = self._manifest()
            state_dir = root / "state"
            status = P.mark_contaminated(
                manifest, state_dir,
                reason="accidental exposure of alpha from sealed-item-1",
                replacement_suite="z0-training-protected-v1",
            )
            self.assertEqual(status["status"], "contaminated")
            self.assertTrue(status["contaminated"])
            self.assertNotIn("alpha", json.dumps(status))
            state_raw = (state_dir / "state.json").read_text(encoding="utf-8")
            self.assertNotIn("sealed-item-1", state_raw)
            with self._env(protected, development):
                with self.assertRaisesRegex(P.ProtectedEvalError, "status=contaminated"):
                    P.score_predictions(
                        manifest, cohort_name="confirm", predictions_path=predictions,
                        candidate_id="candidate-after-leak", candidate_revision="1" * 40,
                        state_dir=state_dir,
                    )

    def test_superseded_suite_cannot_mint_credit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            protected, development, predictions = self._fixture(root)
            manifest = self._manifest()
            state_dir = root / "state"
            status = P.supersede(
                manifest, state_dir, replacement_suite="z0-training-protected-v1"
            )
            self.assertEqual(status["status"], "superseded")
            self.assertEqual(status["superseded_by"], "z0-training-protected-v1")
            with self._env(protected, development):
                with self.assertRaisesRegex(P.ProtectedEvalError, "status=superseded"):
                    P.score_predictions(
                        manifest, cohort_name="confirm", predictions_path=predictions,
                        candidate_id="candidate-old-suite", candidate_revision="2" * 40,
                        state_dir=state_dir,
                    )

    def test_future_cohort_is_not_optimizer_queryable(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            protected, development, predictions = self._fixture(root)
            with self._env(protected, development):
                with self.assertRaisesRegex(P.ProtectedEvalError, "not optimizer-queryable"):
                    P.score_predictions(
                        self._manifest(), cohort_name="future", predictions_path=predictions,
                        candidate_id="candidate-future", candidate_revision="3" * 40,
                        state_dir=root / "state",
                    )

    def test_label_generator_cannot_be_its_own_verifier(self) -> None:
        manifest = copy.deepcopy(self._manifest())
        manifest["verifier"]["id"] = manifest["label_generator"]["id"]
        with self.assertRaisesRegex(P.ProtectedEvalError, "cannot also be the verifier"):
            P.validate_evaluator_manifest(manifest)

    def test_state_and_audit_are_private_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            protected, development, predictions = self._fixture(root)
            state_dir = root / "state"
            with self._env(protected, development):
                P.score_predictions(
                    self._manifest(), cohort_name="confirm", predictions_path=predictions,
                    candidate_id="candidate-private", candidate_revision="4" * 40,
                    state_dir=state_dir,
                )
            self.assertEqual((state_dir / "state.json").stat().st_mode & 0o777, 0o600)
            self.assertEqual((state_dir / "queries.jsonl").stat().st_mode & 0o777, 0o600)
            self.assertEqual((state_dir / "state.lock").stat().st_mode & 0o777, 0o600)

    def test_work_item_lineage_cannot_cross_cohorts(self) -> None:
        for other in ("development", "future"):
            with self.subTest(other=other), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                protected, development, predictions = self._fixture(root)
                target = (development if other == "development" else protected) / f"{other}.jsonl"
                self._write_jsonl(target, [{"id": "branch-item", "expected": "private-value", "group": "g1"}])
                state_dir = root / "state"
                with self._env(protected, development):
                    with self.assertRaisesRegex(P.ProtectedEvalError, "lineage") as raised:
                        P.score_predictions(
                            self._manifest(), cohort_name="confirm", predictions_path=predictions,
                            candidate_id="same-task-other-branch", candidate_revision="a" * 40,
                            state_dir=state_dir,
                        )
                self.assertNotIn("g1", str(raised.exception))
                self.assertNotIn("private-value", str(raised.exception))
                self.assertEqual(P.load_state(state_dir, self._manifest())["query_count"], 0)
                self.assertFalse((state_dir / "queries.jsonl").exists())

    def test_every_truth_row_requires_explicit_lineage(self) -> None:
        for cohort in ("confirm", "development", "future"):
            with self.subTest(cohort=cohort), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                protected, development, predictions = self._fixture(root)
                target = (development if cohort == "development" else protected) / f"{cohort}.jsonl"
                rows = [json.loads(line) for line in target.read_text().splitlines()]
                rows[0].pop("group")
                self._write_jsonl(target, rows)
                with self._env(protected, development):
                    with self.assertRaisesRegex(P.ProtectedEvalError, "lineage"):
                        P.score_predictions(
                            self._manifest(), cohort_name="confirm", predictions_path=predictions,
                            candidate_id="missing-lineage", candidate_revision="a" * 40,
                            state_dir=root / "state",
                        )

    def test_same_group_within_one_cohort_is_permitted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            protected, development, predictions = self._fixture(root)
            self._write_jsonl(protected / "confirm.jsonl", [
                {"id": "sealed-item-1", "expected": "alpha", "group": "one-task"},
                {"id": "sealed-item-2", "expected": "beta", "group": "one-task"},
            ])
            with self._env(protected, development):
                result = P.score_predictions(
                    self._manifest(), cohort_name="confirm", predictions_path=predictions,
                    candidate_id="one-fold", candidate_revision="a" * 40,
                    state_dir=root / "state",
                )
            self.assertEqual(result["score"], 0.5)

    def test_repeated_easy_branches_cannot_inflate_group_macro_credit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            protected, development, predictions = self._fixture(root)
            rows = [{"id": f"retry-{i}", "expected": "alpha", "group": "easy-task"} for i in range(19)]
            rows.append({"id": "hard-task", "expected": "beta", "group": "hard-task"})
            self._write_jsonl(protected / "confirm.jsonl", rows)
            self._write_jsonl(predictions, [
                {"id": row["id"], "prediction": "alpha"} for row in rows
            ])
            manifest = self._manifest()
            manifest["scoring"]["metric"] = "group_macro_exact_match"
            with self._env(protected, development):
                result = P.score_predictions(
                    manifest, cohort_name="confirm", predictions_path=predictions,
                    candidate_id="branch-inflation", candidate_revision="a" * 40,
                    state_dir=root / "state",
                )
            self.assertEqual(result["score"], 0.5)
            self.assertEqual(result["verdict"], "DISCARD")

    def test_group_macro_score_preserves_partial_success_within_each_task(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            protected, development, predictions = self._fixture(root)
            self._write_jsonl(protected / "confirm.jsonl", [
                {"id": "sealed-item-1", "expected": "alpha", "group": "first"},
                {"id": "sealed-item-2", "expected": "beta", "group": "first"},
                {"id": "third", "expected": "gamma", "group": "second"},
            ])
            self._write_jsonl(predictions, [
                {"id": "sealed-item-1", "prediction": "alpha"},
                {"id": "sealed-item-2", "prediction": "wrong"},
                {"id": "third", "prediction": "gamma"},
            ])
            manifest = self._manifest()
            manifest["scoring"]["metric"] = "group_macro_exact_match"
            with self._env(protected, development):
                result = P.score_predictions(
                    manifest, cohort_name="confirm", predictions_path=predictions,
                    candidate_id="group-balanced", candidate_revision="a" * 40,
                    state_dir=root / "state",
                )
            self.assertEqual(result["score"], 0.75)

    def test_manifest_cannot_drift_under_an_existing_suite_identity(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            protected, development, predictions = self._fixture(root)
            manifest = self._manifest()
            state_dir = root / "state"
            with self._env(protected, development):
                first = P.score_predictions(
                    manifest, cohort_name="confirm", predictions_path=predictions,
                    candidate_id="before-drift", candidate_revision="a" * 40, state_dir=state_dir,
                )
                self.assertEqual(first["verdict"], "DISCARD")
                changed = copy.deepcopy(manifest)
                changed["scoring"]["pass_threshold"] = 0.1
                with self.assertRaisesRegex(P.ProtectedEvalError, "manifest"):
                    P.score_predictions(
                        changed, cohort_name="confirm", predictions_path=predictions,
                        candidate_id="after-drift", candidate_revision="b" * 40, state_dir=state_dir,
                    )
            self.assertEqual(P.load_state(state_dir, manifest)["query_count"], 1)

    def test_truth_revision_cannot_change_between_adaptive_queries(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            protected, development, predictions = self._fixture(root)
            manifest = self._manifest()
            state_dir = root / "state"
            with self._env(protected, development):
                first = P.score_predictions(
                    manifest, cohort_name="confirm", predictions_path=predictions,
                    candidate_id="before-label-edit", candidate_revision="a" * 40, state_dir=state_dir,
                )
                self.assertEqual(first["verdict"], "DISCARD")
                rows = [json.loads(line) for line in (protected / "confirm.jsonl").read_text().splitlines()]
                rows[1]["expected"] = "wrong"
                self._write_jsonl(protected / "confirm.jsonl", rows)
                with self.assertRaisesRegex(P.ProtectedEvalError, "cohort revision"):
                    P.score_predictions(
                        manifest, cohort_name="confirm", predictions_path=predictions,
                        candidate_id="after-label-edit", candidate_revision="b" * 40, state_dir=state_dir,
                    )
            self.assertEqual(P.load_state(state_dir, manifest)["query_count"], 1)

    def test_unbound_historical_state_cannot_be_silently_rebound(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            state_dir = Path(td)
            manifest = self._manifest()
            old = P._default_state(manifest)
            old.pop("manifest_sha256", None)
            P._atomic_json(state_dir / "state.json", old)
            with self.assertRaisesRegex(P.ProtectedEvalError, "unbound"):
                P.load_state(state_dir, manifest)

    def test_audit_hash_describes_predictions_actually_scored(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            protected, development, predictions = self._fixture(root)
            original_digest = hashlib.sha256(predictions.read_bytes()).hexdigest()
            original_reader = P._read_jsonl_rows

            def read_then_replace(path, value_key):
                result = original_reader(path, value_key)
                if path == predictions:
                    predictions.write_text("changed after the evaluator read it\n")
                return result

            state_dir = root / "state"
            with self._env(protected, development), patch.object(P, "_read_jsonl_rows", side_effect=read_then_replace):
                result = P.score_predictions(
                    self._manifest(), cohort_name="confirm", predictions_path=predictions,
                    candidate_id="read-snapshot", candidate_revision="a" * 40, state_dir=state_dir,
                )
            self.assertEqual(result["score"], 0.5)
            audit = json.loads((state_dir / "queries.jsonl").read_text())
            self.assertEqual(audit["predictions_sha256"], original_digest)
            state = json.loads((state_dir / "state.json").read_text())
            for name, path in (("confirm", protected / "confirm.jsonl"), ("future", protected / "future.jsonl"),
                               ("development", development / "development.jsonl")):
                self.assertEqual(state["cohort_revisions"][name], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_paired_baseline_requires_lift_on_the_same_complete_cohort(self) -> None:
        for candidate_correct, baseline_correct, verdict in ((True, True, "DISCARD"), (True, False, "KEEP"),
                                                            (False, True, "DISCARD")):
            with self.subTest(candidate=candidate_correct, baseline=baseline_correct), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                protected, development, predictions = self._fixture(root)
                baseline = root / "baseline.jsonl"
                for path, correct in ((predictions, candidate_correct), (baseline, baseline_correct)):
                    self._write_jsonl(path, [
                        {"id": "sealed-item-1", "prediction": "alpha"},
                        {"id": "sealed-item-2", "prediction": "beta" if correct else "wrong"},
                    ])
                with self._env(protected, development):
                    result = P.score_predictions(
                        self._manifest(), cohort_name="confirm", predictions_path=predictions,
                        candidate_id="candidate-skill", candidate_revision="a" * 40,
                        state_dir=root / "state", baseline_predictions_path=baseline,
                        baseline_revision="b" * 40,
                    )
                self.assertEqual(result["verdict"], verdict)
                self.assertEqual(result["baseline"]["score"], 1.0 if baseline_correct else 0.5)
                self.assertEqual(result["baseline"]["score_delta"],
                                 (1.0 if candidate_correct else 0.5) - (1.0 if baseline_correct else 0.5))
                self.assertEqual(result["baseline"]["revision"], "b" * 40)
                self.assertEqual(result["baseline"]["predictions_sha256"], hashlib.sha256(baseline.read_bytes()).hexdigest())
                self.assertEqual(result["query_index"], 1)
                for value in ("sealed-item-1", "sealed-item-2", "alpha", "beta"):
                    self.assertNotIn(value, json.dumps(result))

    def test_incomplete_baseline_cannot_establish_paired_credit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            protected, development, predictions = self._fixture(root)
            baseline = root / "baseline.jsonl"
            self._write_jsonl(baseline, [{"id": "sealed-item-1", "prediction": "alpha"}])
            with self._env(protected, development):
                with self.assertRaisesRegex(P.ProtectedEvalError, "baseline IDs"):
                    P.score_predictions(
                        self._manifest(), cohort_name="confirm", predictions_path=predictions,
                        candidate_id="partial-baseline", candidate_revision="a" * 40,
                        state_dir=root / "state", baseline_predictions_path=baseline, baseline_revision="b" * 40,
                    )


if __name__ == "__main__":
    unittest.main()
