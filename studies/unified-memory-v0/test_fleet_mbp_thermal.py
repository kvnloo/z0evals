"""Public frozen variant integrity. No inference, host operation or live receipts."""

from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import unittest

import yaml
from jsonschema import Draft202012Validator

STUDY = Path(__file__).resolve().parent
ROOT = STUDY.parents[1]


def read_json(filename: str) -> dict:
    return json.loads((STUDY / filename).read_text(encoding="utf-8"))


class FleetMbpThermalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.case = read_json("fleet-mbp-thermal.case.json")
        cls.receipts = read_json("fleet-mbp-thermal.receipts.json")
        cls.manifest = yaml.safe_load((STUDY / "manifest.yaml").read_text(encoding="utf-8"))
        cls.receipt_schema = read_json("receipt.schema.json")

    def test_actual_study_loader_registers_public_artifacts(self) -> None:
        manifest_schema = json.loads((ROOT / "schemas/study-manifest.schema.json").read_text())
        Draft202012Validator.check_schema(manifest_schema)
        Draft202012Validator(manifest_schema).validate(self.manifest)
        registered = {row["path"]: row["kind"] for row in self.manifest["artifacts"]}
        self.assertEqual(registered["fleet-mbp-thermal.case.json"], "fixture")
        self.assertEqual(registered["fleet-mbp-thermal.receipts.json"], "receipt")
        self.assertEqual(registered["fleet-mbp-thermal.protocol.md"], "other")
        # Exercise scripts/validate.py's real study-loader path, including existence
        # and manifest schema validation of all registered study artifacts.
        spec = importlib.util.spec_from_file_location("study_loader", ROOT / "scripts/validate.py")
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        loader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loader)
        with contextlib.redirect_stdout(io.StringIO()):
            loader.main()

    def test_labelled_variant_not_a_pure_user_pair(self) -> None:
        v = self.case["variant"]
        self.assertEqual(v["freeze_status"], "FROZEN_VARIANT")
        self.assertEqual(v["execution_status"], "NOT_RUN")
        self.assertEqual(v["pure_user_to_user_variant"], "BLOCKED")
        self.assertFalse(v["earlier_user_d1_verified"])
        self.assertTrue(v["bounded_history_search_not_proof_of_absence"])
        self.assertIn("AGENT-CODIFIED", v["label"])
        self.assertIn("USER CORRECTION", v["label"])

    def test_exact_source_identifiers_and_cpu_non_supersession(self) -> None:
        d1 = self.case["sources"]["d1"]
        self.assertEqual(d1["speaker"], "agent-codified policy")
        self.assertFalse(d1["user_origin_verified"])
        self.assertEqual(d1["commit"], "79b6c8494fb2709e8231ff87246e9debb9e4e558")
        self.assertEqual(d1["git_blob_sha"], "dc9359dd87d0879d7b08a34c914135880ad8747e")
        self.assertEqual(d1["policy"]["defaults.health.max_temp_c"], 95)
        self.assertEqual(d1["policy"]["nodes.mbp.health.max_temp_c"], "INHERITED")
        self.assertEqual(d1["policy"]["defaults.lane.cpu_quota"], "600%")
        self.assertEqual(d1["policy"]["nodes.mbp.lane.cpu_quota"], "600%")
        d2 = self.case["sources"]["d2"]
        self.assertEqual(d2["speaker"], "user")
        self.assertTrue(d2["steering"])
        self.assertEqual(d2["native_session_id"], "01a16527-824c-7714-8205-9a2d0d5eff38")
        self.assertEqual(d2["native_message_id"], "95d71187")
        self.assertEqual(d2["timestamp"], "2026-10-23T02:59:41.618Z")
        self.assertEqual(d2["native_json_bytes"], 539)
        self.assertEqual(d2["native_json_sha256"], "56a0afb51f98f929fcc0d4643f775efaa167771d12d0ad2e9f3423af6e0e8c32")
        self.assertEqual(d2["raw"], "PRIVATE_LOCAL_NOT_PUBLISHED")
        self.assertFalse(d2["original_verified_in_this_run"])
        codified = d2["codification"]
        self.assertEqual(codified["commit"], "4ca98802004b18f93693db722bb1892da1ae7817")
        self.assertEqual(codified["git_blob_sha"], "7e1f2bd539c084518993dba03113ec822a23f2e0")
        self.assertEqual(codified["value_c"], 110)
        self.assertFalse(codified["user_verbatim_value"])
        self.assertFalse(codified["live_host_activation_verified"])
        gold = self.case["gold"]
        self.assertEqual(gold["supersedes_only"], "mbp thermal max_temp_c")
        self.assertFalse(gold["cpu_correction"])
        self.assertIn("unrelated", gold["cpu_note"])
        self.assertEqual(set(gold["unaffected_gates"]), {"CPU quota", "memory", "disk", "battery"})

    def test_fresh_client_input_cannot_be_an_answer_key(self) -> None:
        scope = self.case["scope"]
        self.assertEqual(scope["repository"], "kvnloo/.files")
        self.assertEqual(scope["domain"], "fleet/host-intent")
        self.assertEqual(scope["node"], "mbp")
        self.assertFalse(scope["execution_permission"])
        self.assertFalse(scope["other_nodes_authorized"])
        fresh = self.case["fresh_client_input"]
        self.assertEqual(set(fresh), {"workstream_id", "question"})
        self.assertEqual(fresh["workstream_id"], scope["workstream_id"])
        self.assertEqual(fresh["question"],
            "What thermal admission policy currently applies to this workstream's node, what superseded it and why, and what is the next permitted read-only step?")
        serialized = json.dumps(fresh)
        for leakage in ("95", "110", "D1", "D2", "01a16527", "95d71187", "4ca988"):
            self.assertNotIn(leakage, serialized)
        public_case = json.dumps(self.case)
        for local_path in ("/home/", "/mnt/", "/Users/", "/tmp/", "tailnet_ip"):
            self.assertNotIn(local_path, public_case)

    def test_safe_gold_and_read_only_permission(self) -> None:
        gold = self.case["gold"]
        self.assertEqual(gold["expected_action"], "ANSWER_READ_ONLY")
        self.assertEqual(len(gold["required_sources"]), 3)
        self.assertIn("READ_ONLY", gold["next_permitted_step"])
        self.assertIn("OBSERVE", gold["next_permitted_step"])
        self.assertTrue(gold["no_execution_permission"])
        self.assertTrue(gold["no_hardware_safety_claim"])
        self.assertTrue(gold["no_host_activation_claim"])
        self.assertTrue(gold["no_other_node_propagation"])
        self.assertIn("User said 110 C verbatim", gold["forbidden"])

    def test_negative_cases_deny_or_observe_without_leakage(self) -> None:
        neg = {c["id"]: c for c in self.case["negative_cases"]}
        self.assertEqual(set(neg), {
            "sibling-scope", "unknown-scope", "same-metadata-new-bytes",
            "missing-required-original", "required-source-outage",
            "quoted-old-approval", "duplicate-restart", "other-node-propagation"
        })
        self.assertTrue(all(c["status"] == "NOT_RUN" for c in neg.values()))
        for name in ("sibling-scope", "unknown-scope"):
            self.assertEqual(neg[name]["expected"],
                             {"decision": "DENY", "metadata_bytes": 0, "payload_bytes": 0})
        for name in ("same-metadata-new-bytes", "missing-required-original",
                     "required-source-outage"):
            self.assertEqual(neg[name]["expected"]["decision"], "OBSERVE")
        self.assertEqual(neg["same-metadata-new-bytes"]["expected"]["required_check"],
                         "CONTENT_DIGEST")
        self.assertFalse(neg["same-metadata-new-bytes"]["expected"]["stale_answer_allowed"])
        self.assertFalse(neg["quoted-old-approval"]["expected"]["execution_permission"])
        replay = neg["duplicate-restart"]["expected"]
        self.assertEqual(replay["decision"], "RETAIN_D2")
        self.assertEqual(replay["effective_c"], 110)
        self.assertFalse(replay["duplicate_admission"])
        self.assertFalse(replay["duplicate_injection"])
        self.assertFalse(neg["other-node-propagation"]["expected"]["propagation"])

    def test_separate_not_run_receipts_for_both_matched_arms(self) -> None:
        r = self.receipts
        self.assertEqual(r["case_id"], self.case["case_id"])
        self.assertEqual(r["execution_status"], "NOT_RUN")
        self.assertEqual(r["admission_qualification"], "NOT_QUALIFIED")
        self.assertEqual(r["model_input_qualification"], "NOT_QUALIFIED")
        self.assertEqual(r["existing_result_schema"], "receipt.schema.json")
        self.assertEqual(r["harness_receipts"], [])
        self.assertEqual({x["name"] for x in r["arms"]},
                         {"memory_enabled", "memory_disabled_control"})
        expected = ["capture", "retrieve", "exact_source_verify",
                    "actual_model_input", "use", "independent_check"]
        for arm in r["arms"]:
            self.assertEqual(arm["execution_status"], "NOT_RUN")
            self.assertEqual(arm["admission_qualification"], "NOT_QUALIFIED")
            self.assertEqual(arm["model_input_qualification"], "NOT_QUALIFIED")
            self.assertIsNone(arm["model_revision"])
            self.assertIsNone(arm["prompt_hash"])
            self.assertIsNone(arm["budget_tokens"])
            self.assertEqual([slot["stage"] for slot in arm["stage_receipts"]], expected)
            for slot in arm["stage_receipts"]:
                self.assertEqual(slot["execution_status"], "NOT_RUN")
                self.assertFalse(slot["verified"])
                self.assertIsNone(slot["receipt_ref"])
                self.assertEqual(slot["evidence_refs"], [])
                self.assertIsNone(slot["measured_at"])
        self.assertEqual({x["case_id"] for x in r["negative_executions"]},
                         {x["id"] for x in self.case["negative_cases"]})
        self.assertTrue(all(x["status"] == "NOT_RUN" and x["receipt_ref"] is None
                            for x in r["negative_executions"]))

    def test_harness_rows_use_existing_receipt_json_schema(self) -> None:
        schema = self.receipt_schema
        Draft202012Validator.check_schema(schema)
        self.assertEqual(schema["properties"]["schema"]["const"],
                         "z0eval.unified_memory_receipt.v0")
        self.assertFalse(schema["additionalProperties"])
        # This is a schema-only probe, not a frozen measurement or execution row.
        probe = {
            "schema": "z0eval.unified_memory_receipt.v0", "harness": "omp",
            "question_id": self.case["case_id"],
            "session_id": "SCHEMA_PROBE", "trace_id": "SCHEMA_PROBE",
            "harness_revision": "ef97f8743ec115fec28238c7a4d4eea2c049158e",
            "retrieval_capability": "SCHEMA_PROBE",
            "retrieval_ok": False, "injected": False, "answer_supported": False,
            "verified": False, "abstained": False, "duplicate_injection": False,
            "evidence_refs": [], "latency_ms": 0, "context_bytes": 0,
            "raw_source_reads": 0
        }
        validator = Draft202012Validator(schema)
        self.assertEqual(list(validator.iter_errors(probe)), [])
        broken = copy.deepcopy(probe)
        broken["injected"] = "NOT_RUN"
        self.assertTrue(list(validator.iter_errors(broken)))
        broken = copy.deepcopy(probe)
        broken["parallel_new_evaluator_field"] = True
        self.assertTrue(list(validator.iter_errors(broken)))


if __name__ == "__main__":
    unittest.main()
