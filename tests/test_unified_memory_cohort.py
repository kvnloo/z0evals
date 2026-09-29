"""Executable cohort tests. Synthetic inputs here are UNIT controls, never live evidence."""

import copy
import hashlib
import importlib.util
import json
import pathlib
import tempfile
import unittest
from contextlib import contextmanager
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE = ROOT / "studies/unified-memory-v0/cohort_contract.py"


def load_cohort():
    if not MODULE.exists():
        raise AssertionError("executable cohort preflight is missing")
    spec = importlib.util.spec_from_file_location("cohort_contract", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def unit_source(slot="identifier", value="UNIT-ID-1", key="unit.identifier"):
    text = f"Recorded {key} for scope unit-only with validity unit-only = {value}."
    digest = hashlib.sha256(text.encode()).hexdigest()
    ordinal = [
        "identifier",
        "state_old",
        "state_new",
        "foreign",
        "conflict_a",
        "conflict_b",
    ].index(slot)
    session_component = "unit-session".encode("utf-8").hex()
    source = {
        "source_id": f"agentsview:{session_component}:{ordinal}",
        "source_version": f"sha256:{digest}",
        "trust_class": "conversation-evidence",
        "locator": f"agentsview://sessions/{session_component}/messages/{ordinal}",
        "origin": {"harness": "codex", "session_id": "unit-session"},
        "observed_at": "2026-01-01T00:00:00Z",
        "fact": {
            "key": key,
            "value": value,
            "scope": "unit-only",
            "validity": "unit-only",
        },
        "retrieval": {
            "session_id": "unit-session",
            "ordinal": ordinal,
            "message_sha256": digest,
        },
        "extractor": {
            "kind": "literal-span-v1",
            "quote": text,
            "key_start": text.index(key),
            "key_end": text.index(key) + len(key),
            "scope_start": text.index("unit-only"),
            "scope_end": text.index("unit-only") + len("unit-only"),
            "validity_start": text.rindex("unit-only"),
            "validity_end": text.rindex("unit-only") + len("unit-only"),
            "value_start": text.rindex(value),
            "value_end": text.rindex(value) + len(value),
        },
    }
    record = {
        "text": text,
        "session_id": "unit-session",
        "origin_harness": "codex",
        "ordinal": ordinal,
        "observed_at": source["observed_at"],
    }
    return source, record


def unit_binding(directory):
    values = {
        "identifier": ("UNIT-ID-1", "unit.identifier"),
        "state_old": ("disabled", "unit.mode"),
        "state_new": ("enabled", "unit.mode"),
        "foreign": ("UNIT-FOREIGN-1", "unit.foreign"),
        "conflict_a": ("yes", "unit.policy"),
        "conflict_b": ("no", "unit.policy"),
    }
    sources, records = {}, {}
    for slot, (value, key) in values.items():
        source, record = unit_source(slot, value, key)
        if slot == "state_new":
            source["observed_at"] = record["observed_at"] = "2026-02-01T00:00:00Z"
        sources[slot], records[slot] = source, record
    raw = directory / "authoritative-unit-only.jsonl"
    raw.write_text(
        "\n".join(r["text"] for r in records.values()) + "\n", encoding="utf-8"
    )
    for record in records.values():
        record["source_path"] = str(raw)
    data = raw.read_bytes()
    for record in records.values():
        record["source_file_sha256"] = hashlib.sha256(data).hexdigest()
        record["source_file_bytes"] = len(data)
    binding = {
        "schema": "z0eval.unified_memory_source_binding.v1",
        "binding_id": "unit-not-live",
        "retrieval": {
            "capability": "agentsview.session.messages",
            "data_dir": str(directory),
            "agentsview_revision": "unit000",
        },
        "slots": sources,
        "full_source_baseline": {
            "policy": "authoritative-source-files-utf8-v1",
            "sources": [
                {
                    "path": str(raw),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "bytes": len(data),
                    "source_slots": list(sources),
                }
            ],
        },
    }
    return binding, records


def replace_unit_quote(source, record, quote):
    """Rebind synthetic UNIT text only; this is not a live source authoring path."""
    record["text"] = source["extractor"]["quote"] = quote
    for field, value in source["fact"].items():
        start = quote.rindex(value) if field == "value" else quote.index(value)
        source["extractor"][field + "_start"] = start
        source["extractor"][field + "_end"] = start + len(value)


def refresh_unit_file(binding, records):
    """Refresh an actual synthetic file after a UNIT-only source change."""
    for slot, record in records.items():
        digest = hashlib.sha256(record["text"].encode("utf-8")).hexdigest()
        binding["slots"][slot]["source_version"] = f"sha256:{digest}"
        binding["slots"][slot]["retrieval"]["message_sha256"] = digest
    item = binding["full_source_baseline"]["sources"][0]
    path = pathlib.Path(item["path"])
    path.write_text(
        "\n".join(r["text"] for r in records.values()) + "\n", encoding="utf-8"
    )
    data = path.read_bytes()
    item["sha256"] = hashlib.sha256(data).hexdigest()
    item["bytes"] = len(data)
    for record in records.values():
        record["source_file_sha256"] = hashlib.sha256(data).hexdigest()
        record["source_file_bytes"] = len(data)


@contextmanager
def memory_unit_binding():
    """Zero source artifacts: all authoritative UNIT file I/O stays in memory."""
    files = {}

    def write_text(path, text, encoding):
        files[path.resolve()] = text.encode(encoding)
        return len(text)

    def read_bytes(path):
        return files[path.resolve()]

    with (
        mock.patch.object(pathlib.Path, "write_text", write_text),
        mock.patch.object(pathlib.Path, "read_bytes", read_bytes),
    ):
        binding, records = unit_binding(ROOT / "never-written-unit-source")
        yield binding, records, files


def unit_answer(case):
    """Known response for unit controls only; never used by a live runner."""
    keys = (
        "slot",
        "source_id",
        "source_version",
        "locator",
        "origin_harness",
        "origin_session_id",
    )
    needed = [
        slot for slot in case["oracle"] if slot not in case["intentional_missing_slots"]
    ]
    return {
        "status": case["expected_behavioral_outcome"],
        "facts": [
            {
                "key": case["oracle"][slot]["key"],
                "value": case["oracle"][slot]["value"],
                "source_slots": [slot],
            }
            for slot in case["answer_slots"]
        ],
        "provenance": [
            {key: case["oracle"][slot][key] for key in keys} for slot in needed
        ],
        "superseded": [
            {
                "key": case["oracle"]["state_old"]["key"],
                "value": case["oracle"]["state_old"]["value"],
                "source_slot": "state_old",
            }
        ]
        if case["oracle_type"] == "ordered-supersession"
        else [],
        "missing_slots": case["intentional_missing_slots"],
    }


class CohortContractTests(unittest.TestCase):
    def test_source_oracle_executes_against_pinned_retrieval(self):
        cohort = load_cohort()
        source, record = unit_source()
        self.assertTrue(
            hasattr(cohort, "resolve_source"),
            "source-backed executable oracle is missing",
        )
        evidence = cohort.resolve_source("identifier", source, record)
        self.assertEqual(evidence["text"], record["text"])
        self.assertEqual(evidence["value"], "UNIT-ID-1")

    def test_forged_locator_and_source_id_rejected(self):
        cohort = load_cohort()
        for forged_fields in (("source_id",), ("locator",), ("source_id", "locator")):
            source, record = unit_source()
            forged = {
                "source_id": "agentsview:6e6f6e6578697374656e74:999",
                "locator": "agentsview://sessions/6e6f6e6578697374656e74/messages/999",
            }
            for field in forged_fields:
                source[field] = forged[field]
            with self.assertRaisesRegex(cohort.PreflightError, "native coordinates"):
                cohort.resolve_source("identifier", source, record)

    def test_native_locator_encoding_is_unambiguous(self):
        cohort = load_cohort()
        for session in ("a:b/c%#é", "A", "a", "..", "%2e%2e"):
            source, record = unit_source()
            component = session.encode("utf-8").hex()
            source["origin"]["session_id"] = session
            source["retrieval"]["session_id"] = record["session_id"] = session
            source["source_id"] = f"agentsview:{component}:0"
            source["locator"] = f"agentsview://sessions/{component}/messages/0"
            resolved = cohort.resolve_source("identifier", source, record)
            self.assertEqual(resolved["source_id"], f"agentsview:{component}:0")
            self.assertEqual(resolved["locator"], source["locator"])
            source["locator"] += "/../1"
            with self.assertRaisesRegex(cohort.PreflightError, "native coordinates"):
                cohort.resolve_source("identifier", source, record)

    def test_unrelated_source_key_cannot_support_claimed_key(self):
        cohort = load_cohort()
        source, record = unit_source("state_new", "enabled", "a.different.mode")
        source["fact"]["key"] = "unit.mode"
        with self.assertRaisesRegex(cohort.PreflightError, "key.*support"):
            cohort.resolve_source("state_new", source, record)

    def test_source_scope_cannot_be_relabelled_as_conflict(self):
        cohort = load_cohort()
        source, record = unit_source("conflict_a", "yes", "unit.policy")
        source["fact"]["scope"] = "PROJECT-B"
        with self.assertRaisesRegex(cohort.PreflightError, "scope.*support"):
            cohort.resolve_source("conflict_a", source, record)

    def test_source_validity_cannot_be_relabelled_as_conflict(self):
        cohort = load_cohort()
        source, record = unit_source("conflict_b", "no", "unit.policy")
        source["fact"]["validity"] = "another-period"
        with self.assertRaisesRegex(cohort.PreflightError, "validity.*support"):
            cohort.resolve_source("conflict_b", source, record)

    def test_every_claim_field_requires_an_exact_checked_span(self):
        cohort = load_cohort()
        for field in ("key", "scope", "validity", "value"):
            for corruption in ("missing", "wrong", "out-of-range", "boolean"):
                source, record = unit_source()
                if corruption == "missing":
                    del source["extractor"][field + "_start"]
                elif corruption == "wrong":
                    source["extractor"][field + "_start"] += 1
                elif corruption == "out-of-range":
                    source["extractor"][field + "_end"] = len(record["text"]) + 1
                else:
                    source["extractor"][field + "_start"] = True
                with self.assertRaisesRegex(cohort.PreflightError, "support"):
                    cohort.resolve_source("identifier", source, record)

    def test_changed_source_bytes_fail_before_injection(self):
        cohort = load_cohort()
        source, record = unit_source()
        record["text"] += " changed"
        self.assertTrue(
            hasattr(cohort, "resolve_source"),
            "source-backed executable oracle is missing",
        )
        with self.assertRaisesRegex(cohort.PreflightError, "revision"):
            cohort.resolve_source("identifier", source, record)

    def test_fake_origin_is_rejected(self):
        cohort = load_cohort()
        source, record = unit_source()
        record["origin_harness"] = "other"
        self.assertTrue(
            hasattr(cohort, "resolve_source"),
            "source-backed executable oracle is missing",
        )
        with self.assertRaisesRegex(cohort.PreflightError, "origin"):
            cohort.resolve_source("identifier", source, record)

    def test_preflight_instantiates_exactly_six_cases_with_intentional_gap(self):
        cohort = load_cohort()
        self.assertTrue(
            hasattr(cohort, "preflight"), "six-case executable preflight is missing"
        )
        with tempfile.TemporaryDirectory() as directory:
            binding, records = unit_binding(pathlib.Path(directory))
            contract = json.loads(
                (MODULE.parent / "executable-cohort.v1.json").read_text()
            )
            plan = cohort.preflight(
                contract, binding, lambda slot, source: records[slot]
            )
        self.assertEqual(
            [c["question_id"] for c in plan["cases"]],
            [
                "exact-identifier",
                "supersession",
                "cross-harness",
                "contradiction",
                "missing-evidence",
                "minimal-context",
            ],
        )
        missing = plan["cases"][4]
        self.assertEqual(missing["evidence"], [])
        self.assertEqual(missing["intentional_missing_slots"], ["identifier"])
        self.assertTrue(all(c["prompt_id"] and c["prompt"] for c in plan["cases"]))
        self.assertEqual(
            plan["cases"][5]["baseline"]["evidence_subset"], ["identifier", "foreign"]
        )

    def test_accidentally_missing_binding_is_not_intentional_abstention(self):
        cohort = load_cohort()
        self.assertTrue(
            hasattr(cohort, "preflight"), "six-case executable preflight is missing"
        )
        with tempfile.TemporaryDirectory() as directory:
            binding, records = unit_binding(pathlib.Path(directory))
            del binding["slots"]["identifier"]
            contract = json.loads(
                (MODULE.parent / "executable-cohort.v1.json").read_text()
            )
            with self.assertRaisesRegex(cohort.PreflightError, "required source slot"):
                cohort.preflight(contract, binding, lambda slot, source: records[slot])

    def test_preflight_rejects_unordered_or_unrelated_supersession(self):
        cohort = load_cohort()
        contract = json.loads((MODULE.parent / "executable-cohort.v1.json").read_text())
        for field, value in (
            ("key", "different.fact"),
            ("scope", "other-object"),
            ("value", "disabled"),
            ("observed_at", "2025-01-01T00:00:00Z"),
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                binding, records = unit_binding(pathlib.Path(directory))
                if field == "observed_at":
                    binding["slots"]["state_new"][field] = records["state_new"][
                        field
                    ] = value
                else:
                    binding["slots"]["state_new"]["fact"][field] = value
                with self.assertRaises(cohort.PreflightError):
                    cohort.preflight(
                        contract, binding, lambda slot, source: records[slot]
                    )

    def test_preflight_rejects_not_genuinely_incompatible_evidence(self):
        cohort = load_cohort()
        contract = json.loads((MODULE.parent / "executable-cohort.v1.json").read_text())
        for field, value in (
            ("key", "different.fact"),
            ("scope", "other-object"),
            ("validity", "another-period"),
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                binding, records = unit_binding(pathlib.Path(directory))
                binding["slots"]["conflict_b"]["fact"][field] = value
                with self.assertRaisesRegex(cohort.PreflightError, "incompatible"):
                    cohort.preflight(
                        contract, binding, lambda slot, source: records[slot]
                    )

    def test_same_consumer_origin_cannot_be_claimed_cross_harness(self):
        cohort = load_cohort()
        with tempfile.TemporaryDirectory() as directory:
            binding, records = unit_binding(pathlib.Path(directory))
            contract = json.loads(
                (MODULE.parent / "executable-cohort.v1.json").read_text()
            )
            with self.assertRaisesRegex(cohort.PreflightError, "cross-harness"):
                cohort.preflight(
                    contract,
                    binding,
                    lambda slot, source: records[slot],
                    consumer="codex",
                )

    def test_minimum_subset_must_have_two_distinct_needed_facts(self):
        cohort = load_cohort()
        with tempfile.TemporaryDirectory() as directory:
            binding, records = unit_binding(pathlib.Path(directory))
            binding["slots"]["foreign"]["fact"]["key"] = binding["slots"]["identifier"][
                "fact"
            ]["key"]
            contract = json.loads(
                (MODULE.parent / "executable-cohort.v1.json").read_text()
            )
            with self.assertRaisesRegex(cohort.PreflightError, "minimal-context"):
                cohort.preflight(contract, binding, lambda slot, source: records[slot])

    def test_minimum_rejects_same_native_message_with_separate_quotes(self):
        cohort = load_cohort()
        with tempfile.TemporaryDirectory() as directory:
            binding, records = unit_binding(pathlib.Path(directory))
            identifier, foreign = (
                binding["slots"][s] for s in ("identifier", "foreign")
            )
            combined = records["identifier"]["text"] + " " + records["foreign"]["text"]
            records["identifier"]["text"] = records["foreign"]["text"] = combined
            for field in ("source_id", "locator"):
                foreign[field] = identifier[field]
            foreign["retrieval"]["ordinal"] = records["foreign"]["ordinal"] = 0
            refresh_unit_file(binding, records)
            contract = json.loads(
                (MODULE.parent / "executable-cohort.v1.json").read_text()
            )
            with self.assertRaisesRegex(cohort.PreflightError, "minimal-context"):
                cohort.preflight(contract, binding, lambda slot, source: records[slot])

    def test_minimum_rejects_identical_excerpts_at_distinct_coordinates(self):
        cohort = load_cohort()
        with tempfile.TemporaryDirectory() as directory:
            binding, records = unit_binding(pathlib.Path(directory))
            combined = records["identifier"]["text"] + " " + records["foreign"]["text"]
            for slot in ("identifier", "foreign"):
                replace_unit_quote(binding["slots"][slot], records[slot], combined)
            refresh_unit_file(binding, records)
            contract = json.loads(
                (MODULE.parent / "executable-cohort.v1.json").read_text()
            )
            with self.assertRaisesRegex(cohort.PreflightError, "minimal-context"):
                cohort.preflight(contract, binding, lambda slot, source: records[slot])

    def test_minimum_rejects_distinct_but_cross_supporting_excerpts(self):
        cohort = load_cohort()
        for slot, other in (("identifier", "foreign"), ("foreign", "identifier")):
            with tempfile.TemporaryDirectory() as directory:
                binding, records = unit_binding(pathlib.Path(directory))
                quote = (
                    records[slot]["text"]
                    + " Also "
                    + binding["slots"][other]["fact"]["value"]
                )
                replace_unit_quote(binding["slots"][slot], records[slot], quote)
                refresh_unit_file(binding, records)
                contract = json.loads(
                    (MODULE.parent / "executable-cohort.v1.json").read_text()
                )
                with self.assertRaisesRegex(cohort.PreflightError, "minimal-context"):
                    cohort.preflight(
                        contract, binding, lambda slot, source: records[slot]
                    )

    def test_minimum_rejects_distinct_keys_with_the_same_value(self):
        cohort = load_cohort()
        with tempfile.TemporaryDirectory() as directory:
            binding, records = unit_binding(pathlib.Path(directory))
            foreign = binding["slots"]["foreign"]
            old = foreign["fact"]["value"]
            foreign["fact"]["value"] = binding["slots"]["identifier"]["fact"]["value"]
            replace_unit_quote(
                foreign,
                records["foreign"],
                records["foreign"]["text"].replace(old, foreign["fact"]["value"]),
            )
            refresh_unit_file(binding, records)
            contract = json.loads(
                (MODULE.parent / "executable-cohort.v1.json").read_text()
            )
            with self.assertRaisesRegex(cohort.PreflightError, "minimal-context"):
                cohort.preflight(contract, binding, lambda slot, source: records[slot])

    def test_refreshed_unrelated_baseline_rejected_without_source_artifacts(self):
        cohort = load_cohort()
        contract = json.loads((MODULE.parent / "executable-cohort.v1.json").read_text())
        with memory_unit_binding() as (binding, records, files):
            self.assertTrue(
                cohort.preflight(contract, binding, lambda slot, source: records[slot])[
                    "preflight_passed"
                ]
            )
            item = binding["full_source_baseline"]["sources"][0]
            unrelated = b"unrelated\n"
            files[pathlib.Path(item["path"]).resolve()] = unrelated
            item["sha256"] = hashlib.sha256(unrelated).hexdigest()
            item["bytes"] = len(unrelated)
            with self.assertRaisesRegex(
                cohort.PreflightError, "retrieval-side.*revision"
            ):
                cohort.preflight(contract, binding, lambda slot, source: records[slot])

    def test_retrieval_file_pin_required_without_source_artifacts(self):
        cohort = load_cohort()
        contract = json.loads((MODULE.parent / "executable-cohort.v1.json").read_text())
        for field, bad in (("source_file_sha256", "0" * 64), ("source_file_bytes", 1)):
            for missing in (True, False):
                with memory_unit_binding() as (binding, records, files):
                    if missing:
                        del records["identifier"][field]
                    else:
                        records["identifier"][field] = bad
                    with self.assertRaisesRegex(
                        cohort.PreflightError, "retrieval-side.*revision"
                    ):
                        cohort.preflight(
                            contract, binding, lambda slot, source: records[slot]
                        )

    def test_baseline_path_and_manifest_pins_still_fail_closed(self):
        cohort = load_cohort()
        contract = json.loads((MODULE.parent / "executable-cohort.v1.json").read_text())
        for corrupt in ("path", "sha256", "bytes", "duplicate", "coverage"):
            with memory_unit_binding() as (binding, records, files):
                item = binding["full_source_baseline"]["sources"][0]
                if corrupt == "path":
                    records["identifier"]["source_path"] += ".wrong"
                elif corrupt == "sha256":
                    item["sha256"] = "0" * 64
                elif corrupt == "bytes":
                    item["bytes"] += 1
                elif corrupt == "duplicate":
                    binding["full_source_baseline"]["sources"].append(
                        copy.deepcopy(item)
                    )
                else:
                    item["source_slots"].remove("identifier")
                with self.assertRaises(cohort.PreflightError):
                    cohort.preflight(
                        contract, binding, lambda slot, source: records[slot]
                    )

    def test_prompts_ignore_answer_bearing_binding_keys(self):
        cohort = load_cohort()
        contract = json.loads((MODULE.parent / "executable-cohort.v1.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            binding, records = unit_binding(pathlib.Path(directory))
            before = cohort.preflight(
                contract, binding, lambda slot, source: records[slot]
            )
            source = binding["slots"]["identifier"]
            old_key = source["fact"]["key"]
            source["fact"]["key"] += "." + source["fact"]["value"]
            quote = records["identifier"]["text"].replace(
                old_key, source["fact"]["key"]
            )
            replace_unit_quote(source, records["identifier"], quote)
            refresh_unit_file(binding, records)
            after = cohort.preflight(
                contract, binding, lambda slot, source: records[slot]
            )
        self.assertNotIn(source["fact"]["value"], after["cases"][4]["prompt"])
        self.assertEqual(
            [c["prompt"] for c in before["cases"]],
            [c["prompt"] for c in after["cases"]],
        )
        self.assertEqual(
            [c["prompt_id"] for c in before["cases"]],
            [c["prompt_id"] for c in after["cases"]],
        )

    def test_prompt_language_and_response_instruction_are_frozen(self):
        cohort = load_cohort()
        for target in (*range(6), "response_instruction"):
            with memory_unit_binding() as (binding, records, files):
                contract = json.loads(
                    (MODULE.parent / "executable-cohort.v1.json").read_text()
                )
                if target == "response_instruction":
                    contract[target] += " Extra instruction."
                else:
                    contract["questions"][target]["prompt_template"] += (
                        " Extra instruction."
                    )
                with self.assertRaisesRegex(cohort.PreflightError, "frozen prompt"):
                    cohort.preflight(
                        contract, binding, lambda slot, source: records[slot]
                    )

    def test_withheld_value_in_fixed_prompt_rejects_preflight(self):
        cohort = load_cohort()
        contract = json.loads((MODULE.parent / "executable-cohort.v1.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            binding, records = unit_binding(pathlib.Path(directory))
            source = binding["slots"]["identifier"]
            quote = records["identifier"]["text"].replace(
                source["fact"]["value"], "Recover"
            )
            source["fact"]["value"] = "Recover"
            replace_unit_quote(source, records["identifier"], quote)
            refresh_unit_file(binding, records)
            with self.assertRaisesRegex(cohort.PreflightError, "withheld value"):
                cohort.preflight(contract, binding, lambda slot, source: records[slot])

    def test_missing_mutation_rejects_prompt_and_metadata_leaks(self):
        cohort = load_cohort()
        contract = json.loads((MODULE.parent / "executable-cohort.v1.json").read_text())
        with memory_unit_binding() as (binding, records, files):
            plan = cohort.preflight(
                contract, binding, lambda slot, source: records[slot]
            )
        for field in ("prompt", "prompt_id", "model_metadata"):
            corrupt = copy.deepcopy(plan)
            value = corrupt["cases"][0]["oracle"]["identifier"]["value"]
            corrupt["cases"][0][field] = (
                {"nested": [value]} if field == "model_metadata" else value
            )
            with self.assertRaisesRegex(cohort.PreflightError, "withheld value"):
                cohort.mutation_cases(corrupt)

    def test_abstention_cannot_pass_with_a_disclosed_withheld_value(self):
        cohort = load_cohort()
        contract = json.loads((MODULE.parent / "executable-cohort.v1.json").read_text())
        with memory_unit_binding() as (binding, records, files):
            case = cohort.preflight(
                contract, binding, lambda slot, source: records[slot]
            )["cases"][4]
        for field in ("prompt", "prompt_id", "model_metadata"):
            corrupt = copy.deepcopy(case)
            value = corrupt["oracle"]["identifier"]["value"]
            corrupt[field] = {"nested": [value]} if field == "model_metadata" else value
            result = cohort.verify_answer(corrupt, unit_answer(case))
            self.assertFalse(result["verified"])
            self.assertIn("withheld-value-disclosed", result["errors"])

    def test_verifier_rejects_altered_evidence_text(self):
        cohort = load_cohort()
        contract = json.loads((MODULE.parent / "executable-cohort.v1.json").read_text())
        with memory_unit_binding() as (binding, records, files):
            case = cohort.preflight(
                contract, binding, lambda slot, source: records[slot]
            )["cases"][0]
        answer = unit_answer(case)
        case["evidence"][0]["text"] = "This message contains no identifier."
        result = cohort.verify_answer(case, answer)
        self.assertFalse(result["verified"])
        self.assertFalse(result["answer_supported"])
        self.assertIn("evidence-projection-mismatch", result["errors"])

    def test_verifier_checks_every_evidence_field_against_oracle(self):
        cohort = load_cohort()
        contract = json.loads((MODULE.parent / "executable-cohort.v1.json").read_text())
        with memory_unit_binding() as (binding, records, files):
            case = cohort.preflight(
                contract, binding, lambda slot, source: records[slot]
            )["cases"][0]
        for field in sorted(case["evidence"][0]):
            corrupt = copy.deepcopy(case)
            corrupt["evidence"][0][field] += " changed"
            result = cohort.verify_answer(corrupt, unit_answer(case))
            self.assertFalse(result["verified"])
            self.assertIn("evidence-projection-mismatch", result["errors"])

    def test_verifier_rejects_duplicate_extra_or_malformed_evidence(self):
        cohort = load_cohort()
        contract = json.loads((MODULE.parent / "executable-cohort.v1.json").read_text())
        with memory_unit_binding() as (binding, records, files):
            case = cohort.preflight(
                contract, binding, lambda slot, source: records[slot]
            )["cases"][0]
        for kind in (
            "duplicate",
            "extra-field",
            "unknown-slot",
            "not-a-list",
            "not-an-object",
        ):
            corrupt = copy.deepcopy(case)
            if kind == "duplicate":
                corrupt["evidence"].append(copy.deepcopy(corrupt["evidence"][0]))
            elif kind == "extra-field":
                corrupt["evidence"][0]["value"] = case["oracle"]["identifier"]["value"]
            elif kind == "unknown-slot":
                corrupt["evidence"][0]["slot"] = "not-bound"
            elif kind == "not-a-list":
                corrupt["evidence"] = {}
            else:
                corrupt["evidence"] = [None]
            result = cohort.verify_answer(corrupt, unit_answer(case))
            self.assertFalse(result["verified"])
            self.assertIn("evidence-projection-mismatch", result["errors"])

    def test_verifier_rejects_unapproved_omission_of_history_evidence(self):
        cohort = load_cohort()
        contract = json.loads((MODULE.parent / "executable-cohort.v1.json").read_text())
        with memory_unit_binding() as (binding, records, files):
            case = cohort.preflight(
                contract, binding, lambda slot, source: records[slot]
            )["cases"][1]
        answer = unit_answer(case)
        case["evidence"] = [e for e in case["evidence"] if e["slot"] == "state_new"]
        answer["provenance"] = [
            e for e in answer["provenance"] if e["slot"] == "state_new"
        ]
        result = cohort.verify_answer(case, answer)
        self.assertFalse(result["verified"])
        self.assertIn("evidence-projection-mismatch", result["errors"])

    def test_executable_oracle_checks_answer_values_and_all_provenance(self):
        cohort = load_cohort()
        self.assertTrue(
            hasattr(cohort, "verify_answer"), "independent answer oracle missing"
        )
        with tempfile.TemporaryDirectory() as directory:
            binding, records = unit_binding(pathlib.Path(directory))
            contract = json.loads(
                (MODULE.parent / "executable-cohort.v1.json").read_text()
            )
            plan = cohort.preflight(
                contract, binding, lambda slot, source: records[slot]
            )
        for case in plan["cases"]:
            answer = unit_answer(case)
            with self.subTest(case=case["question_id"]):
                self.assertTrue(cohort.verify_answer(case, answer)["verified"])
                corrupt = copy.deepcopy(answer)
                if corrupt["facts"]:
                    corrupt["facts"][0]["value"] = "UNSUPPORTED"
                else:
                    corrupt["facts"] = [
                        {"key": "guess", "value": "UNSUPPORTED", "source_slots": []}
                    ]
                self.assertFalse(cohort.verify_answer(case, corrupt)["verified"])
                if answer["provenance"]:
                    corrupt = copy.deepcopy(answer)
                    corrupt["provenance"][0]["source_version"] = "made-up"
                    self.assertFalse(cohort.verify_answer(case, corrupt)["verified"])

    def test_oracle_rejects_silent_conflict_winner_and_lost_old_provenance(self):
        cohort = load_cohort()
        self.assertTrue(
            hasattr(cohort, "verify_answer"), "independent answer oracle missing"
        )
        with tempfile.TemporaryDirectory() as directory:
            binding, records = unit_binding(pathlib.Path(directory))
            contract = json.loads(
                (MODULE.parent / "executable-cohort.v1.json").read_text()
            )
            plan = cohort.preflight(
                contract, binding, lambda slot, source: records[slot]
            )
        conflict, temporal = plan["cases"][3], plan["cases"][1]
        answer = unit_answer(conflict)
        answer["status"] = "supported"
        self.assertFalse(cohort.verify_answer(conflict, answer)["verified"])
        answer = unit_answer(temporal)
        answer["superseded"] = []
        self.assertFalse(cohort.verify_answer(temporal, answer)["verified"])
        answer = unit_answer(temporal)
        answer["provenance"] = answer["provenance"][:1]
        self.assertFalse(cohort.verify_answer(temporal, answer)["verified"])

    def test_model_context_does_not_include_expected_answer_projection(self):
        cohort = load_cohort()
        with tempfile.TemporaryDirectory() as directory:
            binding, records = unit_binding(pathlib.Path(directory))
            contract = json.loads(
                (MODULE.parent / "executable-cohort.v1.json").read_text()
            )
            plan = cohort.preflight(
                contract, binding, lambda slot, source: records[slot]
            )
        for case in plan["cases"]:
            for evidence in case["evidence"]:
                self.assertNotIn("value", evidence)
                self.assertIn("text", evidence)

    def test_mutations_reuse_the_same_prompt_and_real_bound_sources(self):
        cohort = load_cohort()
        self.assertTrue(
            hasattr(cohort, "mutation_cases"), "executable mutations missing"
        )
        with tempfile.TemporaryDirectory() as directory:
            binding, records = unit_binding(pathlib.Path(directory))
            contract = json.loads(
                (MODULE.parent / "executable-cohort.v1.json").read_text()
            )
            plan = cohort.preflight(
                contract, binding, lambda slot, source: records[slot]
            )
        variants = cohort.mutation_cases(plan)
        old, new, missing = variants
        self.assertEqual(old["prompt_id"], plan["cases"][1]["prompt_id"])
        self.assertEqual(new["prompt_id"], old["prompt_id"])
        self.assertEqual([e["slot"] for e in old["evidence"]], ["state_old"])
        self.assertEqual(
            [e["slot"] for e in new["evidence"]], ["state_old", "state_new"]
        )
        self.assertEqual(missing["prompt"], plan["cases"][0]["prompt"])
        self.assertEqual(missing["evidence"], [])
        for variant in variants:
            self.assertTrue(
                cohort.verify_answer(variant, unit_answer(variant))["verified"]
            )
        self.assertFalse(cohort.verify_answer(new, unit_answer(old))["verified"])
        self.assertFalse(
            cohort.verify_answer(missing, unit_answer(plan["cases"][0]))["verified"]
        )

    def test_strict_json_oracle_rejects_duplicate_keys(self):
        cohort = load_cohort()
        with tempfile.TemporaryDirectory() as directory:
            binding, records = unit_binding(pathlib.Path(directory))
            contract = json.loads(
                (MODULE.parent / "executable-cohort.v1.json").read_text()
            )
            case = cohort.preflight(
                contract, binding, lambda slot, source: records[slot]
            )["cases"][0]
        raw = json.dumps(unit_answer(case))
        raw = raw.replace(
            '"status": "supported"', '"status": "abstain", "status": "supported"'
        )
        self.assertFalse(cohort.verify_answer(case, raw)["verified"])

    def test_incomplete_case_definition_cannot_pass_preflight(self):
        cohort = load_cohort()
        for change in (
            "answer_slots",
            "required_source_slots",
            "expected_behavioral_outcome",
        ):
            with (
                self.subTest(change=change),
                tempfile.TemporaryDirectory() as directory,
            ):
                binding, records = unit_binding(pathlib.Path(directory))
                contract = json.loads(
                    (MODULE.parent / "executable-cohort.v1.json").read_text()
                )
                contract["questions"][0][change] = (
                    [] if change.endswith("slots") else "abstain"
                )
                with self.assertRaises(cohort.PreflightError):
                    cohort.preflight(
                        contract, binding, lambda slot, source: records[slot]
                    )

    def test_minimal_subset_oracle_rejects_every_leave_one_out(self):
        cohort = load_cohort()
        with tempfile.TemporaryDirectory() as directory:
            binding, records = unit_binding(pathlib.Path(directory))
            contract = json.loads(
                (MODULE.parent / "executable-cohort.v1.json").read_text()
            )
            minimal = cohort.preflight(
                contract, binding, lambda slot, source: records[slot]
            )["cases"][-1]
        for slot in ("identifier", "foreign"):
            partial = copy.deepcopy(minimal)
            partial["evidence"] = [e for e in partial["evidence"] if e["slot"] != slot]
            for remaining in partial["evidence"]:
                self.assertNotIn(minimal["oracle"][slot]["value"], remaining["text"])
            self.assertFalse(
                cohort.verify_answer(partial, unit_answer(minimal))["verified"]
            )

    def test_preflight_plan_and_mutations_are_consumable_by_dsh_unchanged(self):
        """Exercise the study adapter, not another synthetic plan implementation."""
        cohort = load_cohort()
        path = MODULE.parent / "dsh/runner.py"
        spec = importlib.util.spec_from_file_location("dsh_cohort_consumer", path)
        assert spec is not None and spec.loader is not None
        consumer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(consumer)
        contract = json.loads((MODULE.parent / "executable-cohort.v1.json").read_text())
        with memory_unit_binding() as (binding, records, _):
            plan = cohort.preflight(
                contract, binding, lambda slot, source: records[slot]
            )
        plan["controls"] = cohort.mutation_cases(plan)
        runtime_hash = (
            "3" * 64
        )  # UNIT validation only; never an actual runtime approval.
        approval = {
            "schema": "z0eval.dsh_approval.v1",
            "preflight_passed": True,
            "plan_sha256": cohort.digest_json(plan),
            "contract_sha256": plan["contract_sha256"],
            "binding_sha256": plan["binding_sha256"],
            "binding_id": plan["binding_id"],
            "runtime_pin_sha256": runtime_hash,
            "source_versions": plan["source_versions"],
            "question_ids": list(cohort.QUESTION_IDS),
        }
        payload = consumer.validate_plan(plan, approval, runtime_hash, contract)
        self.assertEqual(len(payload["cases"]), 9)
        self.assertEqual(
            [case["variant"] for case in payload["cases"][6:]],
            [
                "supersession-old-only",
                "supersession-after-new",
                "missing-evidence-mutation",
            ],
        )
        self.assertEqual(
            payload["cases"][6]["intentional_missing_slots"], ["state_new"]
        )
        for variant in plan["controls"]:
            self.assertTrue(
                cohort.verify_answer(variant, unit_answer(variant))["verified"]
            )
        self.assertNotIn('"oracle"', json.dumps(payload))

    def test_preflight_rejects_binding_without_recorded_source_version(self):
        cohort = load_cohort()
        self.assertIsNotNone(cohort, "executable cohort preflight is missing")
        with self.assertRaisesRegex(cohort.PreflightError, "source_version"):
            cohort.validate_source({"source_id": "unit:example"}, "identifier")


if __name__ == "__main__":
    unittest.main()
