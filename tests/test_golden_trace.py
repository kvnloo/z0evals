#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"studies"/"aodl-admission-v1"/"collect_golden.py"
spec=importlib.util.spec_from_file_location("collect_golden",PATH)
G=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(G)

IMPORT_PATH=ROOT/"studies"/"aodl-admission-v1"/"import_golden.py"
_import_spec=importlib.util.spec_from_file_location("import_golden",IMPORT_PATH)
I=importlib.util.module_from_spec(_import_spec)
assert _import_spec.loader is not None
_import_spec.loader.exec_module(I)

ROOT_TRACE="root-trace"
ADMISSION="aodl-admission-x"
DISPATCH="dispatch-x"
PERMIT="admission-provider"
PHYSICAL="physical-x"


def base_rows():
    receipts=[
        {
            "trace_id":"governed-request-x",
            "capability_id":"aodl.governed_request",
            "extra":{"caller_trace_id":ROOT_TRACE},
        },
        {
            "trace_id":ADMISSION,
            "capability_id":"aodl.structural_admission",
            "extra":{
                "caller_trace_id":ROOT_TRACE,
                "aodl_admission":{
                    "allowed":True,
                    "codes":[],
                    "aodl_semantic_fingerprint":"aodl-canon-1:"+"a"*64,
                    "aodl_intent_source_hash":"0"*64,
                },
            },
        },
        {
            "trace_id":DISPATCH,
            "capability_id":"intelligence.dispatch",
            "extra":{
                "caller_trace_id":ROOT_TRACE,
                "aodl_admission_receipt_id":ADMISSION,
                "status":"completed",
                "result":{"ok":True,"trace_id":ROOT_TRACE},
            },
        },
        {
            "trace_id":PERMIT,
            "capability_id":"intelligence.provider_admission",
            "provider":"openrouter",
            "extra":{
                "status":"released",
                "permit_dispatch_id":DISPATCH,
            },
        },
        {
            "trace_id":PHYSICAL,
            "execution":"live",
            "provider":"openrouter",
            "model":"free-model",
            "input_tokens":100,
            "output_tokens":20,
            "extra":{
                "status":"completed",
                "authority_dispatch_id":DISPATCH,
            },
        },
    ]
    tokenomics=[{
        "schema":"z0int.aodl_gate_latency.v1",
        "trace_id":ADMISSION,
        "latency_ms":0.25,
    }]
    return receipts,[],tokenomics


def test_structural_trace_can_pass_without_claiming_verified_success():
    receipts,outcomes,tokenomics=base_rows()
    proof=G.collect(receipts,outcomes,tokenomics,ROOT_TRACE)
    assert proof["structural_execution_complete"] is True
    assert proof["verified_outcome_complete"] is False
    assert proof["checks"]["usage_known"] is True
    assert proof["stages"]["physical_execution"]["input_tokens"]==100
    assert proof["limitations"]==["No gold verified outcome is joined; execution completion is not task success."]


def test_gold_join_is_reported_separately():
    receipts,_,tokenomics=base_rows()
    outcomes=[{
        "trace_id":PHYSICAL,
        "outcome_tier":"gold",
        "outcome":{"verified_success":True,"verification_source":"fixture"},
    }]
    proof=G.collect(receipts,outcomes,tokenomics,ROOT_TRACE)
    assert proof["structural_execution_complete"] is True
    assert proof["verified_outcome_complete"] is True
    assert proof["stages"]["verified_outcome"]["outcome"]["verified_success"] is True
    assert proof["limitations"]==[]


def test_missing_provider_join_fails_structural_only():
    receipts,outcomes,tokenomics=base_rows()
    receipts=[r for r in receipts if r.get("capability_id")!="intelligence.provider_admission"]
    proof=G.collect(receipts,outcomes,tokenomics,ROOT_TRACE)
    assert proof["structural_execution_complete"] is False
    assert proof["checks"]["provider_admission_present"] is False


def test_unknown_usage_fails_structural_trace():
    receipts,outcomes,tokenomics=base_rows()
    physical=next(r for r in receipts if r.get("trace_id")==PHYSICAL)
    physical.pop("output_tokens")
    proof=G.collect(receipts,outcomes,tokenomics,ROOT_TRACE)
    assert proof["structural_execution_complete"] is False
    assert proof["checks"]["usage_known"] is False


@pytest.mark.parametrize("field", ["input_tokens", "output_tokens"])
@pytest.mark.parametrize("value", [True, False, -1, None, 1.5, "4"])
def test_invalid_usage_is_not_measured_usage(field, value):
    receipts, outcomes, tokenomics = base_rows()
    physical = next(r for r in receipts if r.get("trace_id") == PHYSICAL)
    physical[field] = value
    proof = G.collect(receipts, outcomes, tokenomics, ROOT_TRACE)
    assert proof["checks"]["usage_known"] is False
    assert proof["structural_execution_complete"] is False
    assert proof["stages"]["physical_execution"][field] is value


def test_zero_measured_usage_is_valid():
    receipts, outcomes, tokenomics = base_rows()
    physical = next(r for r in receipts if r.get("trace_id") == PHYSICAL)
    physical.update(input_tokens=0, output_tokens=0)
    proof = G.collect(receipts, outcomes, tokenomics, ROOT_TRACE)
    assert proof["checks"]["usage_known"] is True
    assert proof["structural_execution_complete"] is True


def test_negative_gold_remains_complete_evidence():
    receipts, _, tokenomics = base_rows()
    outcomes = [{
        "trace_id": PHYSICAL,
        "outcome_tier": "gold",
        "outcome": {"verified_success": False, "verification_source": "fixture"},
    }]
    proof = G.collect(receipts, outcomes, tokenomics, ROOT_TRACE)
    assert proof["structural_execution_complete"] is True
    assert proof["verified_outcome_complete"] is True
    assert proof["stages"]["verified_outcome"]["outcome"]["verified_success"] is False


def test_generated_proof_matches_frozen_schema():
    import json
    import jsonschema
    receipts,outcomes,tokenomics=base_rows()
    proof=G.collect(receipts,outcomes,tokenomics,ROOT_TRACE)
    schema=json.loads((ROOT/"studies"/"aodl-admission-v1"/"golden-trace.schema.json").read_text())
    jsonschema.validate(proof,schema)


def test_golden_canary_bundle_schema_requires_full_verified_pass():
    import json
    import jsonschema
    bundle={
        "schema":"z0int.aodl_golden_canary_bundle.v1",
        "z0int_revision":"a"*40,
        "z0evals_revision":"b"*40,
        "study_pinned_z0int_revision":"a"*40,
        "root_trace_id":"remote-public-proof",
        "synthetic_fixture":"CANONICAL_OK",
        "provider_execution":True,
        "verified_outcome":True,
        "verification_scope":"exact public synthetic fixture only",
        "structural_execution_complete":True,
        "verified_outcome_complete":True,
        "golden_trace":"golden-trace.json",
        "raw_state":"raw/state",
    }
    schema=json.loads((ROOT/"studies"/"aodl-admission-v1"/"golden-canary-bundle.schema.json").read_text())
    jsonschema.validate(bundle,schema)
    bundle["verified_outcome_complete"]=False
    try:
        jsonschema.validate(bundle,schema)
    except jsonschema.ValidationError:
        pass
    else:
        raise AssertionError("bundle schema accepted incomplete verified outcome")


def complete_golden():
    receipts,_,tokenomics=base_rows()
    outcomes=[{
        "trace_id":PHYSICAL,
        "outcome_tier":"gold",
        "outcome":{"verified_success":True,"verification_source":"exact"},
    }]
    return G.collect(receipts,outcomes,tokenomics,ROOT_TRACE)


def make_bundle(path):
    import json
    pinned=I.pinned_z0int_revision()
    bundle={
        "schema":"z0int.aodl_golden_canary_bundle.v1",
        "z0int_revision":pinned,
        "z0evals_revision":"b"*40,
        "study_pinned_z0int_revision":pinned,
        "root_trace_id":"remote-public-proof",
        "synthetic_fixture":"CANONICAL_OK",
        "provider_execution":True,
        "verified_outcome":True,
        "verification_scope":"exact public synthetic fixture only",
        "structural_execution_complete":True,
        "verified_outcome_complete":True,
        "golden_trace":"golden-trace.json",
        "raw_state":"raw/state",
    }
    golden=complete_golden()
    golden["root_trace_id"]="remote-public-proof"
    files={
        "bundle.json":bundle,
        "golden-trace.json":golden,
        "summary.json":{"synthetic_verified_outcome":True},
        "health.json":{"ready":True},
        "omp-governed.json":{"tool":"z0int_route_worker","parent_model_called":False},
    }
    path.mkdir()
    for name,value in files.items():
        (path/name).write_text(json.dumps(value)+"\n")
    return bundle


def test_importer_accepts_only_sanitized_pinned_bundle(tmp_path):
    bundle_dir=tmp_path/"bundle"
    make_bundle(bundle_dir)
    raw=bundle_dir/"raw"
    raw.mkdir()
    (raw/"secret.txt").write_text("must never be copied")
    bundle,golden,hashes=I.validate_bundle(bundle_dir)
    assert bundle["z0int_revision"]==I.pinned_z0int_revision()
    assert golden["verified_outcome_complete"] is True
    assert set(hashes)==set(I.REQUIRED_FILES)
    assert "raw" not in hashes


def test_archive_validation_preserves_negative_gold_without_rescoring_it(tmp_path):
    import json
    bundle_dir = tmp_path / "bundle"
    make_bundle(bundle_dir)
    path = bundle_dir / "golden-trace.json"
    proof = json.loads(path.read_text())
    proof["stages"]["verified_outcome"]["outcome"]["verified_success"] = False
    path.write_text(json.dumps(proof) + "\n")
    # Archive validation is not a positive canary/promotion decision. Do not
    # discard complete negative evidence or reinterpret its original outcome.
    _, archived, _ = I.validate_bundle(bundle_dir)
    assert archived["verified_outcome_complete"] is True
    assert archived["stages"]["verified_outcome"]["outcome"]["verified_success"] is False


def test_importer_rejects_revision_mismatch(tmp_path):
    import json
    bundle_dir=tmp_path/"bundle"
    bundle=make_bundle(bundle_dir)
    bundle["z0int_revision"]="f"*40
    (bundle_dir/"bundle.json").write_text(json.dumps(bundle)+"\n")
    try:
        I.validate_bundle(bundle_dir)
    except ValueError as exc:
        assert "revision" in str(exc)
    else:
        raise AssertionError("importer accepted a mismatched implementation revision")


def test_importer_rejects_mixed_root_trace_artifacts(tmp_path):
    import json
    bundle_dir=tmp_path/"bundle"
    make_bundle(bundle_dir)
    golden=json.loads((bundle_dir/"golden-trace.json").read_text())
    golden["root_trace_id"]="different-root"
    (bundle_dir/"golden-trace.json").write_text(json.dumps(golden)+"\n")
    try:
        I.validate_bundle(bundle_dir)
    except ValueError as exc:
        assert "root identities" in str(exc)
    else:
        raise AssertionError("importer accepted mixed root trace artifacts")


def test_importer_rejects_credential_shaped_fields(tmp_path):
    import json
    bundle_dir=tmp_path/"bundle"
    make_bundle(bundle_dir)
    (bundle_dir/"summary.json").write_text(json.dumps({"api_key":"should-never-be-here"})+"\n")
    try:
        I.validate_bundle(bundle_dir)
    except ValueError as exc:
        assert "sensitive" in str(exc)
    else:
        raise AssertionError("importer accepted credential-shaped sanitized output")


def test_wrong_dispatch_link_cannot_pass():
    receipts,outcomes,tokenomics=base_rows()
    permit=next(r for r in receipts if r.get("capability_id")=="intelligence.provider_admission")
    permit["extra"]["permit_dispatch_id"]="different-dispatch"
    proof=G.collect(receipts,outcomes,tokenomics,ROOT_TRACE)
    assert proof["structural_execution_complete"] is False
    assert proof["checks"]["provider_admission_present"] is False


def _main():
    tests=[(n,f) for n,f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed=0
    for name,fn in tests:
        try:
            fn();print("PASS",name)
        except Exception as exc:
            failed+=1;print("FAIL",name,type(exc).__name__,exc)
    print(f"{len(tests)-failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__=="__main__":
    raise SystemExit(_main())
