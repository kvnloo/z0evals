"""Offline behavioral tests. UNIT data is never authorized for a model."""
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
CONTRACT = Path(os.environ.get("DSH_STUDY_CONTRACT", str(HERE.parent / "executable-cohort.v1.json")))


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def unit_plan():
    contract = json.loads(CONTRACT.read_text())
    sources = {slot: {"slot": slot, "source_id": "UNIT:" + slot,
                     "source_version": "sha256:" + "1" * 64, "trust_class": "UNIT-untrusted",
                     "locator": "UNIT:message:0", "origin_harness": "UNIT-foreign",
                     "origin_session_id": "UNIT-session", "key": "UNIT-key-" + slot,
                     "text": "UNIT literal {{no_interpolation}} " + slot}
               for slot in contract["source_slots"]}
    cases = []
    for q in contract["questions"]:
        prompt = q["prompt_template"]
        for slot, e in sources.items():
            prompt = prompt.replace("{" + slot + ".fact.key}", e["key"])
        prompt += "\n\n" + contract["response_instruction"]
        missing = ["identifier"] if q["question_id"] == "missing-evidence" else []
        cases.append({"question_id": q["question_id"], "variant": "canonical", "prompt": prompt,
                      "prompt_id": q["question_id"] + ":" + hashlib.sha256(prompt.encode()).hexdigest(),
                      "evidence": [sources[s] for s in q["required_source_slots"] if s not in missing],
                      "intentional_missing_slots": missing, "answer_slots": q["answer_slots"],
                      "oracle": {"NEVER_SEND": "UNIT_ORACLE_SECRET_SENTINEL"},
                      "expected_behavioral_outcome": "UNIT_EXPECTED_SENTINEL"})
    return {"schema": "z0eval.unified_memory_run_plan.v1", "preflight_passed": True,
            "cohort_id": contract["cohort_id"], "contract_sha256": digest(contract),
            "binding_sha256": "2" * 64, "binding_id": "UNIT-binding",
            "source_versions": {s: e["source_version"] for s, e in sources.items()}, "cases": cases}


def load_runner():
    spec = importlib.util.spec_from_file_location("dsh_study_runner", HERE / "runner.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def approval_for(plan):
    return {"schema": "z0eval.dsh_approval.v1", "preflight_passed": True,
            "plan_sha256": digest(plan), "contract_sha256": plan["contract_sha256"],
            "binding_sha256": plan["binding_sha256"], "binding_id": plan["binding_id"],
            "runtime_pin_sha256": "3" * 64, "question_ids": [c["question_id"] for c in plan["cases"][:6]],
            "source_versions": plan["source_versions"]}


class AdmissionTests(unittest.TestCase):
    def test_parent_frozen_contract_revision_is_explicitly_hash_bound(self):
        runner = load_runner()
        contract = json.loads(CONTRACT.read_text())
        contract["response_instruction"] += "\nUNIT reviewed contract revision."
        plan = unit_plan()
        plan["contract_sha256"] = digest(contract)
        for case in plan["cases"]:
            case["prompt"] += "\nUNIT reviewed contract revision."
            case["prompt_id"] = case["question_id"] + ":" + hashlib.sha256(case["prompt"].encode()).hexdigest()
        approval = approval_for(plan)
        payload = runner.validate_plan(plan, approval, "3" * 64, contract)
        self.assertEqual(payload["contract_sha256"], digest(contract))
        contract["response_instruction"] += " unapproved drift"
        with self.assertRaises(runner.Refusal):
            runner.validate_plan(plan, approval, "3" * 64, contract)

    def test_resealed_malformed_cohorts_are_rejected(self):
        runner = load_runner()
        def remove_case(p): p["cases"].pop()
        def bad_prompt(p): p["cases"][0]["prompt"] += "UNIT leaky extra instruction"
        def bad_source(p): p["cases"][0]["evidence"][0]["source_version"] = "sha256:" + "9" * 64
        def missing_without_omission(p): p["cases"][0]["evidence"] = []
        def extra_slot(p): p["cases"][4]["evidence"] = p["cases"][0]["evidence"]
        def duplicate_case(p): p["cases"].append(p["cases"][0])
        for mutation in (remove_case, bad_prompt, bad_source, missing_without_omission, extra_slot, duplicate_case):
            with self.subTest(mutation=mutation.__name__):
                plan = unit_plan()
                mutation(plan)
                with self.assertRaises(runner.Refusal):
                    runner.validate_plan(plan, approval_for(plan), "3" * 64, json.loads(CONTRACT.read_text()))

    def test_fake_source_preflight_cannot_unlock_run(self):
        runner = load_runner()
        self.assertTrue(hasattr(runner, "validate_source_preflight"), "source-preflight gate missing")
        plan = unit_plan()
        payload = runner.validate_plan(plan, approval_for(plan), "3" * 64, json.loads(CONTRACT.read_text()))
        with self.assertRaises(runner.Refusal):
            runner.validate_source_preflight({"preflight_passed": True}, payload, "3" * 64, "4" * 64)

    def test_mutation_variants_use_only_canonical_evidence(self):
        runner = load_runner()
        plan = unit_plan()
        old = copy.deepcopy(plan["cases"][1])
        old.update(variant="supersession-old-only", evidence=old["evidence"][:1], intentional_missing_slots=["state_new"])
        new = copy.deepcopy(plan["cases"][1])
        new["variant"] = "supersession-after-new"
        missing = copy.deepcopy(plan["cases"][0])
        missing.update(variant="missing-evidence-mutation", evidence=[], intentional_missing_slots=["identifier"])
        plan["controls"] = [old, new, missing]
        payload = runner.validate_plan(plan, approval_for(plan), "3" * 64, json.loads(CONTRACT.read_text()))
        self.assertEqual([c["variant"] for c in payload["cases"][6:]],
                         ["supersession-old-only", "supersession-after-new", "missing-evidence-mutation"])
        self.assertEqual([e["slot"] for e in payload["cases"][6]["evidence"]], ["state_old"])
        self.assertEqual(payload["cases"][-1]["evidence"], [])

    def test_approved_six_case_payload_excludes_all_oracle_data(self):
        runner = load_runner()
        self.assertTrue(hasattr(runner, "validate_plan"), "approved six-case gate is missing")
        plan = unit_plan()
        approval = {"schema": "z0eval.dsh_approval.v1", "preflight_passed": True,
                    "plan_sha256": digest(plan), "contract_sha256": plan["contract_sha256"],
                    "binding_sha256": plan["binding_sha256"], "binding_id": plan["binding_id"],
                    "runtime_pin_sha256": "3" * 64,
                    "question_ids": [c["question_id"] for c in plan["cases"]],
                    "source_versions": plan["source_versions"]}
        payload = runner.validate_plan(plan, approval, "3" * 64, json.loads(CONTRACT.read_text()))
        self.assertEqual(len(payload["cases"]), 6)
        self.assertEqual(payload["cases"][0]["evidence"], plan["cases"][0]["evidence"])
        self.assertNotIn("UNIT_ORACLE_SECRET_SENTINEL", json.dumps(payload))
        self.assertNotIn("UNIT_EXPECTED_SENTINEL", json.dumps(payload))
        self.assertNotIn("oracle", json.dumps(payload))

    def test_preflight_boolean_alone_never_launches_bun(self):
        with tempfile.TemporaryDirectory(prefix="dsh-unit-", dir=os.environ["TMPDIR"]) as tmp:
            root = Path(tmp)
            plan = root / "plan.json"
            plan.write_text(json.dumps({"preflight_passed": True, "cases": []}))
            p = subprocess.run([sys.executable, str(HERE / "runner.py"),
                                "--plan", str(plan), "--dsh-root", "/nonexistent-UNIT-source",
                                "--out", str(root / "out")], capture_output=True, text=True)
            self.assertEqual(p.returncode, 2)
            self.assertIn('"code": "APPROVAL_REQUIRED"', p.stdout,
                          "missing fail-closed study launcher")
            self.assertFalse((root / "out").exists())


class SourceSeamTests(unittest.TestCase):
    def test_pinned_six_case_no_model_preflight_and_policy_refusal(self):
        with tempfile.TemporaryDirectory(prefix="dsh-six-unit-", dir=os.environ["TMPDIR"]) as tmp:
            root = Path(tmp).resolve()
            def launch(*args):
                return subprocess.run([sys.executable, str(HERE / "runner.py"), "--dsh-root", "/home/kvn/tmp/dsh",
                                       "--task-cwd", str(root), *args], capture_output=True, text=True, timeout=60)
            seam = root / "seam"
            self.assertEqual(launch("--mode", "seam", "--out", str(seam)).returncode, 0)
            pin = json.loads((seam / "runtime-manifest.json").read_text())
            plan = unit_plan()
            binding = {"UNIT": "offline-not-an-AgentsView-binding"}
            plan["binding_sha256"] = digest(binding)
            approval = approval_for(plan)
            approval["runtime_pin_sha256"] = digest(pin)
            for name, obj in (("plan", plan), ("binding", binding), ("approval", approval), ("pin", pin)):
                (root / (name + ".json")).write_text(json.dumps(obj))
            args = ["--plan", str(root / "plan.json"), "--binding", str(root / "binding.json"),
                    "--contract", str(CONTRACT), "--approval", str(root / "approval.json"),
                    "--approved-approval-sha256", digest(approval), "--runtime-pin", str(root / "pin.json")]
            out = root / "whole-six"
            result = launch(*args, "--out", str(out))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            summary = json.loads((out / "summary.json").read_text())
            self.assertEqual(len(summary["cases"]), 6)
            self.assertEqual(summary["native_fetch_calls"], 0)
            self.assertEqual(summary["neutral_requests"], 0)
            self.assertNotIn("UNIT_ORACLE_SECRET_SENTINEL", (out / "runtime-input.json").read_text())
            runner = load_runner()
            payload = runner.validate_plan(plan, approval, digest(pin), json.loads(CONTRACT.read_text()))
            runner.validate_source_preflight(summary, payload, digest(pin), digest(approval))
            bad_proof = copy.deepcopy(summary)
            bad_proof["fetch_boundary_calls"] = 1
            with self.assertRaises(runner.Refusal):
                runner.validate_source_preflight(bad_proof, payload, digest(pin), digest(approval))
            fake = root / "fake-source-preflight.json"
            fake.write_text(json.dumps({"preflight_passed": True}))
            refused_run = launch(*args, "--mode", "run", "--source-preflight", str(fake),
                                 "--approved-source-preflight-sha256", digest({"preflight_passed": True}),
                                 "--out", str(root / "never-created"))
            self.assertEqual(refused_run.returncode, 2)
            self.assertFalse((root / "never-created").exists())
            bad_plan = copy.deepcopy(plan)
            bad_plan["cases"][0]["prompt"] += "UNIT tamper"
            (root / "plan.json").write_text(json.dumps(bad_plan))
            self.assertEqual(launch(*args, "--out", str(root / "tamper-refusal")).returncode, 2)
            self.assertFalse((root / "tamper-refusal").exists())
            (root / "plan.json").write_text(json.dumps(plan))
            pin["policy"]["selection"]["reasoningEffort"] = "off"
            approval["runtime_pin_sha256"] = digest(pin)
            (root / "pin.json").write_text(json.dumps(pin))
            (root / "approval.json").write_text(json.dumps(approval))
            args[args.index("--approved-approval-sha256") + 1] = digest(approval)
            bad = root / "policy-refusal"
            result = launch(*args, "--out", str(bad))
            self.assertNotEqual(result.returncode, 0, "changed pinned policy was accepted")
            refused = json.loads((bad / "summary.json").read_text())
            self.assertEqual(refused["native_fetch_calls"], 0)
            self.assertEqual(refused["error_code"], "RUNTIME_PIN_MISMATCH")

    def test_source_case_error_captures_are_not_passes(self):
        self.source_case(error=True)

    def test_source_case_capture_and_retained_agent_replay_offline(self):
        self.source_case(error=False)

    def source_case(self, error):
        with tempfile.TemporaryDirectory(prefix="dsh-unit-source-", dir=os.environ["TMPDIR"]) as tmp:
            program = (HERE / "runtime.mjs").read_text() + "\n" + (HERE / "tests/source-case.mjs").read_text()
            env = {**os.environ, "NODE_PATH": "/usr/lib/node_modules/@deepseek-ai/dsh/node_modules",
                   "BUN_RUNTIME_TRANSPILER_CACHE_PATH": "0", "DSH_UNIT_OUT": tmp}
            env.pop("DSH_STUDY_INPUT", None)
            if error:
                env["DSH_UNIT_ERROR"] = "1"
            import resource
            p = subprocess.run(["/home/kvn/.bun/bin/bun", "-e", program], cwd="/home/kvn/tmp/dsh", env=env,
                               capture_output=True, text=True, timeout=60,
                               preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_CORE, (0, 0)))
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr + "\n" + "\n".join(f.read_text() for f in Path(tmp).glob("*stage.json")) + "\n" + "\n".join(f.read_text() for f in Path(tmp).glob("turn-end.json")))
            result = json.loads(p.stdout)
            self.assertEqual(result["provider_network_calls"], 0)
            self.assertEqual(result["fixture_calls"], 1)

    def test_real_source_agent_assembles_then_denies_before_request(self):
        with tempfile.TemporaryDirectory(prefix="dsh-seam-test-", dir=os.environ["TMPDIR"]) as tmp:
            out = Path(tmp).resolve() / "capture"
            p = subprocess.run([sys.executable, str(HERE / "runner.py"), "--mode", "seam",
                                "--dsh-root", "/home/kvn/tmp/dsh", "--out", str(out),
                                "--task-cwd", tmp], capture_output=True, text=True, timeout=60)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr + ((out / "summary.json").read_text() if (out / "summary.json").exists() else ""))
            result = json.loads((out / "summary.json").read_text())
            self.assertEqual(result["mode"], "seam")
            self.assertEqual(result["native_fetch_calls"], 0)
            self.assertEqual(result["neutral_requests"], 0)
            self.assertEqual(result["cases"][0]["turn_end_kind"], "blocked")
            self.assertEqual(result["cases"][0]["assembly_calls"], 1)
            self.assertEqual(result["cases"][0]["system_admissions"], 0)
            manifest = json.loads((out / "runtime-manifest.json").read_text())
            self.assertFalse(manifest["lockfile_parity"])
            self.assertGreater(len(manifest["loaded_files"]), 30)
            self.assertTrue(any(f["kind"] == "borrowed-third-party" for f in manifest["loaded_files"]))
            self.assertEqual(out.stat().st_mode & 0o777, 0o700)
            for file in out.rglob("*"):
                if file.is_file():
                    self.assertEqual(file.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
