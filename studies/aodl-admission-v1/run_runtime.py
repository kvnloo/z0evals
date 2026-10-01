#!/usr/bin/env python3
"""Runtime/ledger acceptance proof for z0evals#78."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import tempfile
from pathlib import Path

Z0INT_REVISION = "1ef20610334c39f41e798c30072650fd023ee1b2"
AODL_REVISION = "68231658f0ec0338464c0916a2329b9587444312"


def doc(*, tokens=1000, plan=None):
    value = {
        "specVersion": "0.2",
        "graphId": "runtime-proof",
        "revision": 3,
        "intentGraph": {
            "nodes": [{
                "id": "parent",
                "kind": "task",
                "ports": [{"id": "out", "direction": "out", "schema": "Task"}],
                "capabilities": ["execute"],
                "authorityCeiling": ["execute", "verify"],
                "lifecycle": "declared",
            }],
            "edges": [],
        },
        "policies": {
            "kinds": ["sequence"],
            "fanIn": "all",
            "dynamic": {"allowed": True, "maxChildren": 4, "maxDepth": 2},
        },
        "constraints": {"budgets": {"tokens": tokens}, "termination": {"on": "done"}},
        "provenance": {"source": "z0evals#78", "sourceHash": "0" * 64},
    }
    if plan is not None:
        value["plan"] = plan
    return value


def request(*, trace, document=None, observed=0, proposed=1):
    return {
        "harness": "dsh",
        "trace_id": trace,
        "parent_agent": "parent",
        "function": "cheap_bounded_worker",
        "task": "bounded structural proof",
        "provider": "none",
        "model": "none",
        "reason": "z0evals structural proof",
        "aodl": {
            "document": document or doc(),
            "spawn": {
                "request_revision": 3,
                "parent_node_id": "parent",
                "live_children": 0,
                "parent_depth": 0,
                "observed": {"tokens": observed},
                "proposed": {"tokens": proposed},
                "requested": ["execute"],
            },
        },
    }


def rows(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--z0int-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(args.z0int_root / "src"))
    from z0int import dispatch_authority as authority
    from z0int import aodl_dispatch
    from z0int.aodl_observation import record_drift
    from z0int.receipt import receipts_path
    from z0int.tokenomics_emit import events_path

    # This study isolates the authority/ledger boundary. Provider validation is
    # deliberately replaced so no credential, network, permit or physical call
    # can occur.
    authority.validate_remote = lambda request, enforce_free=False: ({}, {}, {}, {})

    cases = []
    root = Path(tempfile.mkdtemp(prefix="z0eval-aodl-runtime-"))

    def home(name):
        target = root / name
        os.environ["Z0INT_HOME"] = str(target)
        return target

    # 1. ALLOW is durable before dispatch-start; replay never duplicates it.
    home("allow-order")
    req = request(trace="allow-order")
    owner = secrets.token_hex(32)
    claimed = authority.rpc("claim", {"protocol_version": 3, "request": req, "owner": owner})
    ledger = rows(receipts_path())
    trows = rows(events_path())
    ok = (
        claimed.get("claimed") is True
        and [r.get("capability_id") for r in ledger] == ["aodl.structural_admission", "intelligence.dispatch"]
        and ledger[1]["extra"].get("aodl_admission_receipt_id") == ledger[0]["trace_id"]
        and len(trows) == 1
        and trows[0].get("task_success") is None
        and trows[0].get("verified_success") is None
    )
    replay = authority.rpc("claim", {"protocol_version": 3, "request": req, "owner": secrets.token_hex(32)})
    ok = ok and replay["result"].get("execution_status") == "uncertain"
    ok = ok and len(rows(receipts_path())) == 2 and len(rows(events_path())) == 1
    cases.append({"id": "allow-order-replay", "pass": ok, "receipt_count": len(rows(receipts_path()))})

    # 2. DENY never creates a dispatch row.
    home("deny-before-dispatch")
    req = request(trace="deny-budget", document=doc(tokens=10), observed=10, proposed=1)
    denied = authority.rpc("claim", {"protocol_version": 3, "request": req, "owner": secrets.token_hex(32)})
    ledger = rows(receipts_path())
    ok = (
        denied.get("claimed") is False
        and denied["result"].get("execution_status") == "denied"
        and denied["result"]["aodl_admission"].get("numeric_codes") == [105]
        and len(ledger) == 1
        and ledger[0].get("capability_id") == "aodl.structural_admission"
        and not any(str(r.get("trace_id", "")).startswith("dispatch-") for r in ledger)
    )
    cases.append({"id": "deny-before-dispatch", "pass": ok, "receipt_count": len(ledger)})

    # 3. Crash window: allowed admission exists, dispatch-start does not.
    home("restart-window")
    req = request(trace="restart-window")
    key = authority.identity(req)
    with authority.locked(key):
        admission = aodl_dispatch.ensure(req, key, authority.fingerprint(req), required=True)
    before = rows(receipts_path())
    claimed = authority.rpc("claim", {"protocol_version": 3, "request": req, "owner": secrets.token_hex(32)})
    after = rows(receipts_path())
    ok = (
        admission is not None
        and len(before) == 1
        and claimed.get("claimed") is True
        and len(after) == 2
        and after[0]["trace_id"] == claimed.get("aodl_admission_receipt_id")
        and after[1]["extra"].get("aodl_admission_receipt_id") == after[0]["trace_id"]
    )
    cases.append({"id": "restart-after-admission", "pass": ok, "before": len(before), "after": len(after)})

    # 4. Drift changes runtime semantic snapshot, not authored intent lineage.
    home("drift")
    original = doc(plan={"generation": 1})
    original_bytes = json.dumps(original, sort_keys=True)
    first = record_drift(original, trace_id="drift", observation={"worker_status": "failed"})
    second = record_drift(first["document"], trace_id="drift", observation={"worker_status": "failed"})
    receipt = first["receipt"]
    ok = (
        json.dumps(original, sort_keys=True) == original_bytes
        and first["document"]["intentGraph"] == original["intentGraph"]
        and first["aodl_intent_source_hash"] == original["provenance"]["sourceHash"] == "0" * 64
        and first["semantic_fingerprint_before"] != first["semantic_fingerprint_after"]
        and second.get("replayed") is True
        and second.get("receipt_replayed") is True
        and len(rows(receipts_path())) == 1
        and receipt.get("capability_id") == "aodl.observation"
        and "success" not in receipt
        and "verified_success" not in receipt
    )
    cases.append({"id": "drift-immutable-idempotent", "pass": ok, "receipt_count": len(rows(receipts_path()))})

    proof = {
        "schema": "z0eval.aodl_runtime_proof.v1",
        "z0int_revision": Z0INT_REVISION,
        "aodl_revision": AODL_REVISION,
        "provider_execution": False,
        "all_passed": all(case["pass"] for case in cases),
        "cases": cases,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_passed": proof["all_passed"], "cases": len(cases), "out": str(args.out)}))
    return 0 if proof["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
