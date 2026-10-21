"""Synthetic boundary fixtures; not human-study evidence."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from validate import Invalid, unique_object, validate


def fixture():
    row = {
        "id": "fixture-1", "group": "synthetic-session-1", "split": "evaluation",
        "arm": "control", "assignment_probability": 0.5,
        "exposure_at": "2030-01-01T10:00:00Z", "outcome_due": "2030-01-02T10:00:00Z",
        "choice": "YES", "status": "OBSERVED", "measurement": "objective_task",
        "assistance": "none", "value": 0.0, "observed_at": "2030-01-02T11:00:00Z",
    }
    return {
        "schema_version": "hcl-conformance-v0", "data_kind": "synthetic",
        "claim": "contract_only", "source_revision": "a" * 40,
        "evaluator_revision": "b" * 40, "registered_at": "2030-01-01T09:00:00Z",
        "as_of": "2030-01-03T10:00:00Z", "rows": [row],
    }


class ConformanceTests(unittest.TestCase):
    def rejected(self, document, code):
        with self.assertRaises(Invalid) as caught:
            validate(document)
        self.assertEqual(str(caught.exception), code)

    def test_observed_zero_stays_observed_not_missing(self):
        result = validate(fixture())
        self.assertEqual(result["by_arm"]["control"]["OBSERVED"], 1)
        self.assertEqual(result["human_benefit"], "NOT_EVALUATED")
        self.assertFalse(result["can_promote"])

    def test_no_mutation_and_deterministic_order(self):
        document = fixture()
        document["rows"].append(dict(document["rows"][0], id="fixture-2", arm="candidate"))
        before = copy.deepcopy(document)
        first = validate(document)
        self.assertEqual(document, before)
        document["rows"].reverse()
        self.assertEqual(validate(document), first)

    def test_missing_skip_unknown_and_no_are_separate(self):
        document = fixture()
        document["rows"] = [dict(document["rows"][0], id=f"fixture-{i}", choice=choice,
                                  status="MISSING", value=None, observed_at=None)
                            for i, choice in enumerate(("NO", "SKIP", "UNKNOWN", "YES"))]
        result = validate(document)
        self.assertEqual(result["choices"], {"NO": 1, "SKIP": 1, "UNKNOWN": 1, "YES": 1})
        self.assertEqual(result["by_arm"]["control"]["MISSING"], 4)
        for status in ("SKIPPED", "NOT_DUE"):
            document = fixture()
            row = document["rows"][0]
            row.update(status=status, value=None, observed_at=None)
            if status == "NOT_DUE":
                row["outcome_due"] = "2030-01-10T10:00:00Z"
            self.assertEqual(validate(document)["by_arm"]["control"][status], 1)

    def test_root_boundary_negatives(self):
        cases = [
            ("data_kind", "human", "SYNTHETIC_ONLY"),
            ("claim", "verified_human_gain", "CLAIM_BOUNDARY"),
            ("source_revision", "main", "REVISION_SHAPE"),
            ("evaluator_revision", "abc1234", "REVISION_SHAPE"),
            ("evaluator_revision", "0" * 40, "REVISION_PLACEHOLDER"),
            ("as_of", "2030-01-01T08:00:00Z", "ANALYSIS_BEFORE_LOCK"),
            ("registered_at", "2030-01-01T09:00:00", "TIMESTAMP_ZONE"),
            ("rows", [], "ROW_COUNT"),
        ]
        for key, value, code in cases:
            with self.subTest(key=key, value=value):
                document = fixture()
                document[key] = value
                self.rejected(document, code)

    def test_numeric_invalids_and_no_coercion(self):
        for value in (None, True, "0", float("nan"), float("inf"), -float("inf"), 10 ** 400):
            with self.subTest(value=value):
                document = fixture()
                document["rows"][0]["value"] = value
                self.rejected(document, "OBSERVED_VALUE")
        for value in (0, -0.1, 1.1, True, "0.5", float("nan")):
            with self.subTest(probability=value):
                document = fixture()
                document["rows"][0]["assignment_probability"] = value
                self.rejected(document, "ASSIGNMENT_PROBABILITY")

    def test_absence_cannot_be_numeric_zero(self):
        for status in ("MISSING", "SKIPPED", "NOT_DUE"):
            document = fixture()
            document["rows"][0].update(status=status, value=0, observed_at=None)
            self.rejected(document, "ABSENT_NOT_ZERO")

    def test_temporal_negatives(self):
        cases = [
            ({"exposure_at": "2030-01-01T09:00:00Z"}, "PROSPECTIVE_ORDER"),
            ({"outcome_due": "2029-12-31T10:00:00Z"}, "PROSPECTIVE_ORDER"),
            ({"observed_at": "2030-01-02T09:59:59Z"}, "OBSERVATION_WINDOW"),
            ({"observed_at": "2030-01-04T10:00:00Z"}, "OBSERVATION_WINDOW"),
            ({"status": "NOT_DUE", "value": None, "observed_at": None}, "ALREADY_DUE"),
            ({"status": "MISSING", "value": None, "observed_at": None,
              "outcome_due": "2030-01-10T10:00:00Z"}, "NOT_YET_MISSING"),
        ]
        for patch, code in cases:
            with self.subTest(patch=patch):
                document = fixture()
                document["rows"][0].update(patch)
                self.rejected(document, code)

    def test_future_exposure_is_not_an_observed_trial(self):
        document = fixture()
        document["rows"][0].update(exposure_at="2030-01-10T10:00:00Z",
                                  outcome_due="2030-01-11T10:00:00Z")
        self.rejected(document, "FUTURE_EXPOSURE")

    def test_all_evidence_classes_remain_distinct(self):
        document = fixture()
        kinds = ("self_report", "objective_task", "physiological_proxy", "simulation")
        document["rows"] = [dict(document["rows"][0], id=f"row-{i}", measurement=kind)
                            for i, kind in enumerate(kinds)]
        self.assertEqual(validate(document)["measurement_classes"], dict.fromkeys(kinds, 1))

    def test_offset_comparison_is_not_lexical(self):
        document = fixture()
        document["rows"][0]["exposure_at"] = "2030-01-01T05:00:00-05:00"
        self.assertEqual(validate(document), validate(fixture()))

    def test_duplicate_and_split_leakage(self):
        document = fixture()
        document["rows"].append(copy.deepcopy(document["rows"][0]))
        self.rejected(document, "DUPLICATE_ID")
        document["rows"][1].update(id="fixture-2", split="search")
        self.rejected(document, "GROUP_LEAKAGE")

    def test_unknown_fields_and_enums_rejected(self):
        document = fixture()
        document["private_transcript"] = "not allowed"
        self.rejected(document, "DOCUMENT_FIELDS")
        document = fixture()
        document["rows"][0]["medical_note"] = "not allowed"
        self.rejected(document, "ROW_FIELDS")
        document = fixture()
        document["rows"][0]["status"] = "NO"
        self.rejected(document, "ENUM_STATUS")

    def test_duplicate_json_keys(self):
        with self.assertRaisesRegex(Invalid, "DUPLICATE_JSON_KEY"):
            json.loads('{"claim":"contract_only","claim":"other"}', object_pairs_hook=unique_object)

    def test_cli_accepts_fixture_rejects_invalid_without_echo(self):
        script = str(Path(__file__).with_name("validate.py"))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "fixture.json"
            path.write_text(json.dumps(fixture()), encoding="utf-8")
            result = subprocess.run([sys.executable, script, str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "CONTRACT_ONLY")
            path.write_text('{"secret":"should-not-echo"}', encoding="utf-8")
            result = subprocess.run([sys.executable, script, str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("should-not-echo", result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["code"], "DOCUMENT_FIELDS")


if __name__ == "__main__":
    unittest.main()
