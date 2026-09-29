"""Study-only executable cohort validation. No model calls or memory implementation."""

import copy
import hashlib
import json
from datetime import datetime
from pathlib import Path

import jsonschema


class PreflightError(ValueError):
    """A cohort is incomplete or its evidence does not meet the frozen contract."""


def validate_source(source, slot):
    if (
        not isinstance(source.get("source_version"), str)
        or not source["source_version"]
    ):
        raise PreflightError(f"{slot}: source_version must be recorded")
    for field in ("source_id", "trust_class", "locator", "observed_at"):
        if not isinstance(source.get(field), str) or not source[field]:
            raise PreflightError(f"{slot}: {field} must be recorded")
    for field, required in (
        ("origin", ("harness", "session_id")),
        ("fact", ("key", "value", "scope", "validity")),
    ):
        if not isinstance(source.get(field), dict) or any(
            not isinstance(source[field].get(k), str) or not source[field][k]
            for k in required
        ):
            raise PreflightError(f"{slot}: complete {field} required")
    try:
        observed = datetime.fromisoformat(source["observed_at"].replace("Z", "+00:00"))
        if observed.tzinfo is None:
            raise ValueError("timezone missing")
    except (ValueError, TypeError) as exc:
        raise PreflightError(f"{slot}: invalid observed_at") from exc


def resolve_source(slot, source, record):
    """Execute literal support oracle against retrieved bytes and native origin."""
    validate_source(source, slot)
    text = record.get("text")
    if not isinstance(text, str):
        raise PreflightError(f"{slot}: source text unavailable")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    retrieval = source.get("retrieval", {})
    if (
        source["source_version"] != f"sha256:{digest}"
        or retrieval.get("message_sha256") != digest
    ):
        raise PreflightError(f"{slot}: source revision changed")
    origin = source["origin"]
    if (
        record.get("session_id") != origin["session_id"]
        or retrieval.get("session_id") != origin["session_id"]
        or record.get("origin_harness") != origin["harness"]
    ):
        raise PreflightError(f"{slot}: origin does not match retrieved session")
    if (
        record.get("ordinal") != retrieval.get("ordinal")
        or type(retrieval.get("ordinal")) is not int
        or type(record.get("ordinal")) is not int
        or record["ordinal"] < 0
    ):
        raise PreflightError(f"{slot}: message ordinal mismatch")
    # Frozen v1 identity: lowercase UTF-8 hex session component, decimal ordinal.
    session_component = record["session_id"].encode("utf-8").hex()
    source_id = f"agentsview:{session_component}:{record['ordinal']}"
    locator = f"agentsview://sessions/{session_component}/messages/{record['ordinal']}"
    if source["source_id"] != source_id or source["locator"] != locator:
        raise PreflightError(f"{slot}: provenance does not match native coordinates")
    if record.get("observed_at") != source["observed_at"]:
        raise PreflightError(f"{slot}: observed_at does not match source")
    extractor = source.get("extractor", {})
    quote = extractor.get("quote")
    if (
        extractor.get("kind") != "literal-span-v1"
        or not isinstance(quote, str)
        or not quote
        or text.count(quote) != 1
    ):
        raise PreflightError(f"{slot}: support quote absent or ambiguous")
    for field in ("key", "scope", "validity", "value"):
        start, end = extractor.get(field + "_start"), extractor.get(field + "_end")
        if (
            type(start) is not int
            or type(end) is not int
            or not 0 <= start < end <= len(quote)
            or quote[start:end] != source["fact"][field]
        ):
            raise PreflightError(
                f"{slot}: expected {field} not supported by executable span oracle"
            )
    return {
        "slot": slot,
        "source_id": source_id,
        "source_version": source["source_version"],
        "trust_class": source["trust_class"],
        "locator": locator,
        "origin_harness": origin["harness"],
        "origin_session_id": origin["session_id"],
        "key": source["fact"]["key"],
        "value": source["fact"]["value"],
        "text": quote,
    }


QUESTION_IDS = (
    "exact-identifier",
    "supersession",
    "cross-harness",
    "contradiction",
    "missing-evidence",
    "minimal-context",
)
ORACLES = (
    "exact-supported",
    "ordered-supersession",
    "origin-supported",
    "incompatible-assertions",
    "intentional-missing-source",
    "minimum-sufficient-subset",
)
HERE = Path(__file__).resolve().parent
# Pins exact answer-independent prompt language, not binding-selected templates.
FROZEN_PROMPT_SHA256 = (
    "255394eb3432345a83275dffa09358589daa1f182141ade3d3e5de7ba447cbdd"
)


def digest_json(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def preflight(contract, binding, reader, consumer="dsh"):
    """Instantiate all six cases before any model call. Reader is real source retrieval."""
    if contract.get("schema") != "z0eval.unified_memory_case_contract.v1":
        raise PreflightError("unsupported executable contract")
    questions = contract.get("questions", [])
    if tuple(q.get("question_id") for q in questions) != QUESTION_IDS:
        raise PreflightError("canonical six question IDs/order required")
    if tuple(q.get("oracle_type") for q in questions) != ORACLES:
        raise PreflightError("oracle is not executable for canonical case")
    if (
        digest_json(
            {
                "prompts": [q.get("prompt_template") for q in questions],
                "response_instruction": contract.get("response_instruction"),
            }
        )
        != FROZEN_PROMPT_SHA256
    ):
        raise PreflightError("frozen prompt language changed")
    required_sets = (
        ["identifier"],
        ["state_old", "state_new"],
        ["foreign"],
        ["conflict_a", "conflict_b"],
        ["identifier"],
        ["identifier", "foreign"],
    )
    answer_sets = (
        ["identifier"],
        ["state_new"],
        ["foreign"],
        ["conflict_a", "conflict_b"],
        [],
        ["identifier", "foreign"],
    )
    outcomes = (
        "supported",
        "newest-supported",
        "supported",
        "explicit-conflict",
        "abstain",
        "supported",
    )
    for question, required, answers, outcome in zip(
        questions, required_sets, answer_sets, outcomes
    ):
        if (
            question.get("required_source_slots") != required
            or question.get("answer_slots") != answers
            or question.get("expected_behavioral_outcome") != outcome
            or not isinstance(question.get("prompt_template"), str)
            or not question["prompt_template"].strip()
            or not question.get("verification_rules")
        ):
            raise PreflightError("incomplete or incoherent canonical case definition")
    if contract.get("source_slots") != [
        "identifier",
        "state_old",
        "state_new",
        "foreign",
        "conflict_a",
        "conflict_b",
    ] or not contract.get("response_instruction"):
        raise PreflightError("canonical source slots and response contract required")
    slots = binding.get("slots", {})
    for slot in contract["source_slots"]:
        if slot not in slots:
            raise PreflightError(f"required source slot absent: {slot}")
        validate_source(slots[slot], slot)
    try:
        jsonschema.Draft202012Validator(
            json.loads((HERE / "source-binding.schema.v1.json").read_text()),
            format_checker=jsonschema.FormatChecker(),
        ).validate(binding)
    except jsonschema.ValidationError as exc:
        raise PreflightError(f"local binding schema: {exc.message}") from exc
    records = {slot: reader(slot, slots[slot]) for slot in contract["source_slots"]}
    old, new = slots["state_old"], slots["state_new"]
    if (
        any(old["fact"][k] != new["fact"][k] for k in ("key", "scope"))
        or old["fact"]["value"] == new["fact"]["value"]
        or datetime.fromisoformat(old["observed_at"].replace("Z", "+00:00"))
        >= datetime.fromisoformat(new["observed_at"].replace("Z", "+00:00"))
    ):
        raise PreflightError(
            "supersession requires ordered old/new changed states of the same fact/scope"
        )
    left, right = slots["conflict_a"], slots["conflict_b"]
    if (
        any(left["fact"][k] != right["fact"][k] for k in ("key", "scope", "validity"))
        or left["fact"]["value"] == right["fact"]["value"]
        or left["source_id"] == right["source_id"]
    ):
        raise PreflightError(
            "contradiction requires incompatible single-valued assertions of the same fact/scope/validity"
        )
    if slots["foreign"]["origin"]["harness"] == consumer:
        raise PreflightError(
            "cross-harness source must originate in a different harness"
        )
    minimum = questions[-1]
    if (
        minimum.get("sufficient_evidence_subset") != ["identifier", "foreign"]
        or minimum["required_source_slots"] != ["identifier", "foreign"]
        or minimum["answer_slots"] != ["identifier", "foreign"]
        or slots["identifier"]["fact"]["key"] == slots["foreign"]["fact"]["key"]
    ):
        raise PreflightError(
            "minimal-context requires the defined two distinct necessary facts"
        )
    resolved = {
        slot: resolve_source(slot, slots[slot], records[slot])
        for slot in contract["source_slots"]
    }
    first, second = resolved["identifier"], resolved["foreign"]
    if (
        first["source_id"] == second["source_id"]
        or first["text"] == second["text"]
        or first["value"] == second["value"]
        or first["value"] in second["text"]
        or second["value"] in first["text"]
    ):
        raise PreflightError(
            "minimal-context requires distinct native messages, excerpts and values; "
            "each omission must remove literal fact support"
        )
    baseline = binding["full_source_baseline"]
    baseline_sources, seen, covered = [], set(), set()
    for item in baseline["sources"]:
        path = Path(item["path"]).resolve()
        if path in seen:
            raise PreflightError("full-source baseline repeats a file")
        seen.add(path)
        try:
            data = path.read_bytes()
            data.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise PreflightError(
                "full-source baseline unavailable or not UTF-8"
            ) from exc
        file_sha256 = hashlib.sha256(data).hexdigest()
        if len(data) != item["bytes"] or file_sha256 != item["sha256"]:
            raise PreflightError("full-source baseline revision changed")
        for slot in item["source_slots"]:
            if (
                slot not in records
                or Path(records[slot].get("source_path", "")).resolve() != path
            ):
                raise PreflightError(
                    f"baseline source does not bind retrieved slot: {slot}"
                )
            record = records[slot]
            if (
                record.get("source_file_sha256") != file_sha256
                or type(record.get("source_file_bytes")) is not int
                or record["source_file_bytes"] != len(data)
            ):
                raise PreflightError(
                    f"{slot}: retrieval-side authoritative file revision mismatch"
                )
            covered.add(slot)
        baseline_sources.append(
            {
                "sha256": item["sha256"],
                "bytes": len(data),
                "source_slots": item["source_slots"],
            }
        )
    if not {"identifier", "foreign"}.issubset(covered):
        raise PreflightError("minimal-context full-source baseline is incomplete")
    cases = []
    for question in questions:
        q = dict(question)
        required = q["required_source_slots"]
        if any(slot not in resolved for slot in required):
            raise PreflightError("case references an unknown required source slot")
        missing = []
        if q["question_id"] == "missing-evidence":
            mutation = q.get("mutation", {})
            missing = mutation.get("omit_slots", [])
            if (
                mutation.get("operation") != "omit-source-binding"
                or missing != required
                or missing != ["identifier"]
            ):
                raise PreflightError(
                    "missing-evidence must intentionally omit the correct required source"
                )
        prompt = q["prompt_template"] + "\n\n" + contract["response_instruction"]
        evidence = []
        for slot in required:
            if slot not in missing:
                evidence.append(
                    {k: v for k, v in resolved[slot].items() if k != "value"}
                )
        case = {
            "question_id": q["question_id"],
            "prompt_id": q["question_id"]
            + ":"
            + hashlib.sha256(prompt.encode()).hexdigest(),
            "prompt": prompt,
            "oracle_type": q["oracle_type"],
            "expected_behavioral_outcome": q["expected_behavioral_outcome"],
            "evidence": evidence,
            "intentional_missing_slots": missing,
            "oracle": {slot: resolved[slot] for slot in required},
            "answer_slots": q["answer_slots"],
            "variant": "canonical",
            "verification_rules": q["verification_rules"],
        }
        if q["question_id"] == "minimal-context":
            case["baseline"] = {
                "policy": baseline["policy"],
                "evidence_subset": q["sufficient_evidence_subset"],
                "full_source_bytes": sum(
                    s["bytes"]
                    for s in baseline_sources
                    if set(s["source_slots"]) & set(required)
                ),
                "sources": [
                    s
                    for s in baseline_sources
                    if set(s["source_slots"]) & set(required)
                ],
            }
        check_withheld_values(case)
        cases.append(case)
    return {
        "schema": "z0eval.unified_memory_run_plan.v1",
        "cohort_id": contract["cohort_id"],
        "contract_sha256": digest_json(contract),
        "binding_sha256": digest_json(binding),
        "binding_id": binding["binding_id"],
        "preflight_passed": True,
        "source_versions": {
            slot: source["source_version"] for slot, source in slots.items()
        },
        "cases": cases,
    }


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def check_withheld_values(case, omitted=None):
    """Conservative literal guard over every case field except the private oracle."""

    def contains(value, payload):
        if isinstance(payload, dict):
            return any(
                contains(value, k) or contains(value, v) for k, v in payload.items()
            )
        if isinstance(payload, list):
            return any(contains(value, v) for v in payload)
        return value in str(payload)

    visible = {k: v for k, v in case.items() if k != "oracle"}
    for slot in case["intentional_missing_slots"] if omitted is None else omitted:
        if contains(case["oracle"][slot]["value"], visible):
            raise PreflightError(
                "withheld value disclosed by model-visible prompt or metadata"
            )


def mutation_cases(plan):
    """Controls change only evidence availability, not prompts or source facts."""
    if not plan.get("preflight_passed"):
        raise PreflightError("mutations require complete cohort preflight")
    canonical = {case["question_id"]: case for case in plan["cases"]}
    old = copy.deepcopy(canonical["supersession"])
    old.update(
        variant="supersession-old-only",
        oracle_type="exact-supported",
        expected_behavioral_outcome="supported",
        answer_slots=["state_old"],
        intentional_missing_slots=["state_new"],
    )
    old["evidence"] = [e for e in old["evidence"] if e["slot"] == "state_old"]
    check_withheld_values(old, ["state_new"])
    new = copy.deepcopy(canonical["supersession"])
    new["variant"] = "supersession-after-new"
    missing = copy.deepcopy(canonical["exact-identifier"])
    missing.update(
        variant="missing-evidence-mutation",
        oracle_type="intentional-missing-source",
        expected_behavioral_outcome="abstain",
        answer_slots=[],
        evidence=[],
        intentional_missing_slots=["identifier"],
    )
    check_withheld_values(missing)
    return [old, new, missing]


def verify_answer(case, answer):
    """Strict, source-backed structured oracle; never consult a model for verification."""
    errors = []
    try:
        check_withheld_values(case)
    except PreflightError:
        errors.append("withheld-value-disclosed")
    if isinstance(answer, str):
        try:
            answer = json.loads(answer, object_pairs_hook=unique_object)
        except (json.JSONDecodeError, ValueError):
            answer = None
    fields = {"status", "facts", "provenance", "superseded", "missing_slots"}
    if (
        not isinstance(answer, dict)
        or set(answer) != fields
        or any(not isinstance(answer[k], list) for k in fields - {"status"})
    ):
        return {
            "verified": False,
            "answer_supported": False,
            "abstained": False,
            "errors": ["invalid-structured-response"],
        }
    if answer["status"] != case["expected_behavioral_outcome"]:
        errors.append("unexpected-behavioral-outcome")
    if answer["missing_slots"] != case["intentional_missing_slots"]:
        errors.append("missing-slot-mismatch")
    oracle = case["oracle"]
    expected_evidence = [
        {k: v for k, v in evidence.items() if k != "value"}
        for slot, evidence in oracle.items()
        if slot not in case["intentional_missing_slots"]
    ]
    if not isinstance(case["evidence"], list) or sorted(
        map(digest_json, case["evidence"])
    ) != sorted(map(digest_json, expected_evidence)):
        return {
            "verified": False,
            "answer_supported": False,
            "abstained": answer["status"] == "abstain",
            "errors": errors + ["evidence-projection-mismatch"],
        }
    supplied = {e["slot"] for e in case["evidence"]}
    expected_facts = [
        {
            "key": oracle[slot]["key"],
            "value": oracle[slot]["value"],
            "source_slots": [slot],
        }
        for slot in case["answer_slots"]
    ]
    if sorted(map(digest_json, answer["facts"])) != sorted(
        map(digest_json, expected_facts)
    ):
        errors.append("unsupported-or-missing-fact")
    if any(slot not in supplied for slot in case["answer_slots"]):
        errors.append("answer-source-not-injected")
    provenance_fields = (
        "slot",
        "source_id",
        "source_version",
        "locator",
        "origin_harness",
        "origin_session_id",
    )
    expected_provenance = [
        {field: oracle[slot][field] for field in provenance_fields} for slot in supplied
    ]
    if sorted(map(digest_json, answer["provenance"])) != sorted(
        map(digest_json, expected_provenance)
    ):
        errors.append("provenance-mismatch")
    old = oracle.get("state_old")
    expected_history = (
        [{"key": old["key"], "value": old["value"], "source_slot": "state_old"}]
        if case["oracle_type"] == "ordered-supersession"
        else []
    )
    if answer["superseded"] != expected_history:
        errors.append("supersession-history-mismatch")
    verified = not errors
    return {
        "verified": verified,
        "answer_supported": verified and answer["status"] != "abstain",
        "abstained": answer["status"] == "abstain",
        "errors": errors,
    }
