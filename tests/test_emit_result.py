"""Synthetic receipt/publication tests. No provider, policy store or private traces."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import yaml
from jsonschema import ValidationError

ROOT = Path(__file__).resolve().parents[1]


def load_tool(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


emitter = load_tool("emit_result")
publisher = load_tool("policy_post")


class EmitResultTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.study = Path(self.temp.name) / "studies" / "synthetic-v1"
        (self.study / "analysis").mkdir(parents=True)
        (self.study / "data").mkdir()
        (self.study / "data/rows.jsonl").write_text('{"correct":true}\n')
        self.manifest = {
            "schema_version": "z0eval.study.v1", "id": "synthetic-v1",
            "title": "Synthetic fixture", "status": "draft", "created": "2026-10-24",
            "sources": [{"repo": "example/fixture", "commit": "a" * 40}],
            "questions": ["Does the fixture emit a receipt?"],
            "artifacts": [{"path": "data/rows.jsonl", "kind": "dataset"}],
        }
        (self.study / "manifest.yaml").write_text(yaml.safe_dump(self.manifest))
        self.result = {
            "suite_revision": "a" * 40, "system_revision": "b" * 40,
            "baseline_revision": "c" * 40, "verdict": "KEEP",
            "gates": {key: "pass" for key in ("contract", "authority", "quality_noninferiority", "latency_tail")},
            "evidence": {
                "tokenomics_artifacts": [], "source_artifacts": [],
                "result_hashes": [{"path": "data/rows.jsonl", "sha256": emitter.digest(self.study / "data/rows.jsonl")}],
            },
            "limitations": ["Synthetic fixture. Not real measured evidence."],
            "family": "omp.tool", "job": "fixture bounded choice",
            "arm": {"kind": "slm", "model": "fixture@rev1", "quant": "Q4_0",
                    "engine": "fixture@rev1", "backend": "cpu", "device": "fixture"},
            "metric": {"name": "acc_at_conf", "value": 0.98, "n": 100,
                       "ci_low": 0.93, "ci_high": 0.995, "ci_method": "wilson95",
                       "higher_is_better": True},
            "evidence_class": "inference", "scope_note": "Synthetic fixture only.",
            "ts": "2026-10-24T12:00:00Z",
        }

    def emit(self):
        (self.study / "analysis/summary.json").write_text(json.dumps({"result": self.result}))
        return emitter.emit_result(self.study)

    def test_valid_receipt_is_deterministic_and_hash_bound(self):
        path = self.emit()
        first = path.read_bytes()
        result = json.loads(first)
        self.assertEqual(path, self.study / "result.json")
        self.assertEqual(result["schema"], "z0eval.result.v1")
        self.assertEqual(result["suite_id"], "synthetic-v1")
        self.assertEqual(result["findings"], [emitter.finding_view(result)])
        self.assertEqual(result["evidence_class"], "inference")
        for ref in result["evidence"]["source_artifacts"]:
            self.assertEqual(ref["sha256"], emitter.digest(self.study / ref["path"]))
        self.assertEqual({r["path"] for r in result["evidence"]["source_artifacts"]},
                         {"manifest.yaml", "analysis/summary.json"})
        self.assertEqual(self.emit().read_bytes(), first)

    def test_refuses_missing_sample_size_ci_method_and_hash(self):
        original = copy.deepcopy(self.result)
        for container, key in (("metric", "n"), ("metric", "ci_low"),
                               ("metric", "ci_high"), ("metric", "ci_method")):
            with self.subTest(key=key):
                self.result = copy.deepcopy(original)
                del self.result[container][key]
                with self.assertRaises(ValidationError):
                    self.emit()
                self.assertFalse((self.study / "result.json").exists())
        self.result = copy.deepcopy(original)
        del self.result["evidence"]["result_hashes"][0]["sha256"]
        with self.assertRaises(ValidationError):
            self.emit()

    def test_refuses_invalid_numbers_and_intervals(self):
        original = copy.deepcopy(self.result)
        for key, value in (("n", 0), ("n", True), ("n", 1.5), ("ci_method", "none"),
                           ("ci_low", None), ("ci_low", 2), ("value", float("nan")),
                           ("ci_high", float("inf"))):
            with self.subTest(key=key, value=value):
                self.result = copy.deepcopy(original)
                self.result["metric"][key] = value
                with self.assertRaises((ValueError, ValidationError)):
                    self.emit()

    def test_refuses_missing_empty_or_incorrect_evidence(self):
        self.result["evidence"]["result_hashes"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            self.emit()
        self.result["evidence"]["result_hashes"] = []
        with self.assertRaises(ValidationError):
            self.emit()

    def test_refuses_external_and_missing_evidence(self):
        outside = Path(self.temp.name) / "outside.json"
        outside.write_text("synthetic outside file")
        for path in (str(outside), "../../outside.json", "data/missing.json"):
            with self.subTest(path=path):
                self.result["evidence"]["result_hashes"] = [{"path": path, "sha256": emitter.digest(outside)}]
                with self.assertRaises(ValueError):
                    self.emit()
        (self.study / "data/link").symlink_to(outside)
        self.result["evidence"]["result_hashes"][0]["path"] = "data/link"
        with self.assertRaises(ValueError):
            self.emit()

    def test_does_not_replace_previous_receipt_on_failure(self):
        output = self.emit()
        original = output.read_bytes()
        self.result["metric"]["n"] = 0
        with self.assertRaises(ValidationError):
            self.emit()
        self.assertEqual(output.read_bytes(), original)

    def test_refuses_unpinned_revision_and_unjustified_keep(self):
        self.result["suite_revision"] = "main"
        with self.assertRaises(ValidationError):
            self.emit()
        self.result["suite_revision"] = "a" * 40
        self.result["gates"]["authority"] = "not_run"
        with self.assertRaisesRegex(ValueError, "KEEP"):
            self.emit()
        self.result["verdict"] = "PARTIAL"
        self.assertEqual(json.loads(self.emit().read_text())["verdict"], "PARTIAL")

    def test_no_guess_from_legacy_summary_or_mismatched_manifest(self):
        (self.study / "analysis/summary.json").write_text('{"latency":{"n":100}}')
        with self.assertRaisesRegex(ValueError, "explicit result"):
            emitter.emit_result(self.study)
        self.manifest["id"] = "wrong-id"
        (self.study / "manifest.yaml").write_text(yaml.safe_dump(self.manifest))
        with self.assertRaisesRegex(ValueError, "manifest id"):
            self.emit()

    def test_consumer_view_cannot_disagree(self):
        result = json.loads(self.emit().read_text())
        result["findings"][0]["metric"]["n"] = 1000
        with self.assertRaisesRegex(ValueError, "must match"):
            emitter.validate_result(result)

    def test_promotion_metadata_is_explicit_and_preserved(self):
        self.result["metric"].update(live_shadow=True, divergence=0.01,
                                     aa_noise_floor=0.02, outcome_ledger_verified=True)
        self.result["baseline"] = {"arm": "synthetic-baseline", "value": 0.97}
        self.result["expires_at"] = "2026-11-07T12:00:00Z"
        result = json.loads(self.emit().read_text())
        self.assertEqual(result["findings"][0]["metric"], self.result["metric"])
        self.assertEqual(result["findings"][0]["baseline"], self.result["baseline"])
        self.assertEqual(result["findings"][0]["expires_at"], self.result["expires_at"])

    def test_synthetic_receipt_marker_reaches_finding(self):
        self.result["synthetic"] = True
        result = json.loads(self.emit().read_text())
        self.assertIs(result["synthetic"], True)
        self.assertIs(result["findings"][0]["synthetic"], True)
        self.result["synthetic"] = "true"
        with self.assertRaises(ValidationError):
            self.emit()


class PolicyPostTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.args = {"from_version": "a" * 64, "to_version": "b" * 64,
                     "policy_url": "https://example.org/policies/" + "b" * 64 + ".json",
                     "post_date": "2026-10-24", "root": self.root}

    def test_markdown_links_front_matter_and_idempotence(self):
        body = "## Changes\n\n[Finding](https://example.org/findings/123) supports shadow.\n"
        output = publisher.policy_post(body, **self.args)
        self.assertEqual(output.relative_to(self.root).as_posix(), "posts/policy/2026-10-24-bbbbbbbbbbbb.md")
        source = output.read_text()
        meta = yaml.safe_load(source.split("---\n")[1])
        self.assertEqual(meta["policy_version"], "b" * 64)
        self.assertIn(self.args["policy_url"], source)
        self.assertIn(body, source)
        self.assertIn("does not authorize or change routes", source)
        self.assertEqual(publisher.policy_post(body, **self.args), output)
        with self.assertRaisesRegex(ValueError, "different content"):
            publisher.policy_post(body + "Changed.\n", **self.args)

    def test_json_diff_links_every_finding(self):
        diff = {"from_version": "a" * 64, "to_version": "b" * 64,
                "policy_url": self.args["policy_url"],
                "evidence": [{"id": "finding-1", "url": "https://example.org/findings/1"}],
                "changes": [{"rule_id": "F-omp.tool-1", "from": "none", "to": "shadow", "because": ["finding-1"]}]}
        output = publisher.policy_post(json.dumps(diff), root=self.root, post_date="2026-10-24")
        self.assertIn("none → shadow", output.read_text())
        diff["changes"][0]["because"] = ["missing"]
        with self.assertRaisesRegex(ValueError, "needs an evidence URL"):
            publisher.policy_post(json.dumps(diff), root=self.root)

    def test_rejects_missing_or_unsafe_links_versions_and_dates(self):
        for override in ({"to_version": "main"}, {"policy_url": "file:///private/policy.json"},
                         {"policy_url": "https://user:secret@example.org/policy"},
                         {"post_date": "2026-99-01"}):
            with self.subTest(override=override):
                with self.assertRaises(ValueError):
                    publisher.policy_post("Change.", evidence_urls=["https://example.org/evidence"],
                                          **(self.args | override))
        with self.assertRaisesRegex(ValueError, "evidence URL"):
            publisher.policy_post("Change without evidence.", **self.args)
        self.assertFalse((self.root / "posts").exists())

    def test_json_and_cli_must_agree(self):
        with self.assertRaisesRegex(ValueError, "disagree"):
            publisher.policy_post(json.dumps({"to_version": "c" * 64}), **self.args)

    def test_native_markdown_replaces_private_links_and_reads_versions(self):
        source = (
            "# Decision policy changelog\n\n"
            + "From: `" + "a" * 64 + "`\nTo: `" + "b" * 64 + "`\n\n"
            + "- `F-omp.tool-1`: **none → shadow**\n"
            + "  finding-1 [/private/fixture.json](file:///private/fixture.json)\n"
        )
        args = {"root": self.root, "policy_url": self.args["policy_url"], "post_date": "2026-10-24"}
        with self.assertRaisesRegex(ValueError, "explicit public URL override"):
            publisher.policy_post(source, **args)
        output = publisher.policy_post(
            source, evidence_urls=["/private/fixture.json=https://example.org/evidence/fixture.json"], **args
        )
        rendered = output.read_text()
        self.assertNotIn("/private", rendered)
        self.assertNotIn("file://", rendered)
        self.assertIn("https://example.org/evidence/fixture.json", rendered)
        with self.assertRaisesRegex(ValueError, "disagree"):
            publisher.policy_post(source, from_version="c" * 64, **args)

    def test_native_json_requires_public_evidence_override(self):
        diff = {
            "from_version": "a" * 64, "to_version": "b" * 64,
            "changes": [{"rule_id": "F-omp.tool-1", "family": "omp.tool", "scope": {},
                         "from": "none", "to": "shadow", "because": ["finding-1"], "reason": "measured"}],
            "evidence": [{"id": "finding-1", "path": "/private/fixture.json", "url": "file:///private/fixture.json"}],
        }
        args = {"root": self.root, "policy_url": self.args["policy_url"], "post_date": "2026-10-24"}
        with self.assertRaisesRegex(ValueError, "public HTTPS"):
            publisher.policy_post(json.dumps(diff), **args)
        output = publisher.policy_post(
            json.dumps(diff), evidence_urls=["finding-1=https://example.org/evidence/fixture.json"], **args
        )
        self.assertNotIn("/private", output.read_text())
        self.assertIn("finding-1", output.read_text())

    def test_serving_warnings_survive_both_changelog_formats(self):
        diff = {
            "changes": [{"rule_id": "F-omp.tool-1", "from": "canary", "to": "live",
                         "because": ["finding-1"], "serving_missing": True}],
            "serving_missing": ["F-router.model-1"],
        }
        body = publisher.change_markdown(diff)
        self.assertIn("## Missing serving endpoints", body)
        self.assertIn("`F-omp.tool-1` has no matching serving endpoint.", body)
        self.assertIn("`F-router.model-1` has no matching serving endpoint.", body)
        output = publisher.policy_post(body, evidence_urls=["https://example.org/evidence/1"], **self.args)
        self.assertIn(body, output.read_text())

    def test_synthetic_json_post_is_not_a_real_promotion(self):
        diff = {
            "synthetic": True, "changes": [],
            "evidence": [{"id": "fixture", "url": "https://example.org/fixture"}],
        }
        output = publisher.policy_post(json.dumps(diff), **self.args)
        source = output.read_text()
        self.assertIs(yaml.safe_load(source.split("---\n")[1])["synthetic"], True)
        self.assertIn("does not report a real experiment promotion", source)
        diff["synthetic"] = "false"
        with self.assertRaisesRegex(ValueError, "must be a boolean"):
            publisher.policy_post(json.dumps(diff), **self.args)

    def test_native_markdown_synthetic_marker_sets_front_matter(self):
        body = (
            "# Decision policy changelog\n\n"
            + publisher.SYNTHETIC_MARKER + "\n\n"
            + "[Fixture](https://example.org/fixture)\n"
        )
        output = publisher.policy_post(body, **self.args)
        source = output.read_text()
        self.assertIs(yaml.safe_load(source.split("---\n")[1])["synthetic"], True)
        self.assertIn("does not report a real experiment promotion", source)


if __name__ == "__main__":
    unittest.main()
