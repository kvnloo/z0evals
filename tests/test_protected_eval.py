#!/usr/bin/env python3
from __future__ import annotations

import copy
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


if __name__ == "__main__":
    unittest.main()
