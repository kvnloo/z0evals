#!/usr/bin/env python3
"""Tests for the routing-evidence studies (hermes-index-prior-v0, free-taskfit-v0).

    python3 -m pytest tests/test_routing_evidence.py -q
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HI = REPO / "studies/hermes-index-prior-v0"
FT = REPO / "studies/free-taskfit-v0"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


snap = _load(HI / "scripts/snapshot_hermes_index.py", "snapshot_hermes_index")
rowsmod = _load(HI / "scripts/to_benchmark_rows.py", "to_benchmark_rows")
cert = _load(FT / "scripts/certify.py", "certify_taskfit")

HEADER = ["Columns (8/8)", "#", "Model", "Hermes Index", "↓", "$ / task", "↕", "Hermes Bench", "↕",
          "TerminalBench 4", "↕", "TerminalBench Science", "↕", "SkillsBench", "↕"]


def _page(rows: list[list[str]]) -> bytes:
    cells = HEADER + [c for row in rows for c in row] + ["* Provisional: partial run or cost estimate, pending a full rerun."]
    return ("<html><body>" + "".join(f"<div>{c}</div><div>////</div><div>x</div>" for c in cells) + "</body></html>").encode()


ROW1 = ["01", "Model A", "Vendor", "63.31", "$4.99", "*", "76.73", "$0.516", "54.0", "$6.27*", "52.9", "$12.65", "69.6", "$0.51"]
ROW2 = ["02", "Model B", "Vendor", "57.09", "$1.19", "73.93", "$0.26", "50.8", "$1.62", "51.4", "$2.46", "52.3", "$0.417 · 53.0 raw"]


def test_parser_reads_provisional_and_clean_raw_cells():
    data = snap.snapshot(_page([ROW1, ROW2]), "2026-11-03T20:32:51Z")
    a, b = data["rows"]
    assert (a["hermes_index"], a["usd_per_task"], a["cost_provisional"]) == (63.31, 4.99, True)
    assert a["suites"]["terminalbench_4"] == {"score": 54.0, "usd_per_task": 6.27, "provisional": True}
    assert b["cost_provisional"] is False
    assert b["suites"]["skillsbench"] == {"score": 52.3, "usd_per_task": 0.417, "provisional": False, "raw_score": 53.0}
    assert data["z0evals_measured"] is False and data["evidence_status"] == "source-reported"
    assert len(data["raw_sha256"]) == 64


def test_parser_fails_closed_when_a_column_shifts():
    shifted = ROW2[:6] + ["99.0"] + ROW2[7:]  # Hermes Bench score no longer matches the index mean
    with pytest.raises(snap.ParseError):
        snap.snapshot(_page([ROW1, shifted]), "2026-11-03T20:32:51Z")
    with pytest.raises(snap.ParseError):
        snap.snapshot(b"<html>layout changed</html>", "2026-11-03T20:32:51Z")


def test_committed_snapshot_is_internally_consistent():
    data = json.loads((HI / "data/snapshots/hermes-index-20261103T2032Z.json").read_text())
    assert len(data["rows"]) == 18 and data["rows"][0]["model"] == "Claude Opus 5.5"
    for row in data["rows"]:
        mean = sum(s["score"] for s in row["suites"].values()) / 4
        assert abs(mean - row["hermes_index"]) <= 0.06


def test_benchmark_rows_never_claim_acceptance_and_drop_free_variant_costs():
    data = json.loads((HI / "data/snapshots/hermes-index-20261103T2032Z.json").read_text())
    idmap = json.loads((HI / "data/identity-map.json").read_text())
    rows, skipped = rowsmod.rows_for(data, idmap)
    assert {s["model"] for s in skipped} == {"Nemotron Super 3.5"}
    assert all(r["task_class"].startswith("external.") for r in rows)
    assert all("p_accept" not in r for r in rows)
    free = [r for r in rows if "free variant" in r["benchmark"]]
    assert free and all(r["unit"] == "percent" for r in free)
    free_ids = {tuple(a) for fam in idmap["families"].values() for a in fam.get("free_variants", [])}
    assert not [r for r in rows if r["unit"] == "USD_per_task" and (r["provider"], r["model"]) in free_ids]
    opus_cost = [r for r in rows if r["model"] == "claude-opus-5-5" and r["task_class"] == "external.hermes_index.mean"
                 and r["unit"] == "USD_per_task"]
    assert opus_cost[0]["benchmark"].endswith("[provisional]")


def _row(model, task, family, *, ok=True, text=None, at=1793750000.0, correct=None, **extra):
    row = {"model": model, "provider": model.split("/")[0], "task": task, "family": family, "rep": 0, "at": at,
           "ok": ok, "task_set_sha256": cert.FROZEN_SHA256, "ttft_s": 0.3, "total_s": 0.5,
           "usage": {"completion_tokens": 50}, **extra}
    if text is not None:
        row["text"] = text
    if correct is not None:
        row["correct"] = correct
    return row


def _write(tmp_path, rows):
    path = tmp_path / "rows.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


def test_certify_regrades_from_text_and_ignores_runner_flag(tmp_path):
    rows = [_row("groq/openai/gpt-oss-20b", "weekday", "reason", text="Thursday", correct=False),
            _row("groq/openai/gpt-oss-20b", "weekday", "reason", text="Monday", correct=True),
            _row("groq/openai/gpt-oss-20b", "math-word", "reason", ok=False, error="HTTPError 413")]
    tasks = cert.load_tasks()
    expected = sum(bool(tasks["weekday"]["grade"](t)) for t in ("Thursday", "Monday"))
    result = cert.certify([_write(tmp_path, rows)], "t")
    acc = next(f for f in result["findings"] if f["metric"]["name"] == "acceptance_rate")
    assert acc["metric"]["n"] == 3 and acc["metric"]["accepted"] == expected
    assert acc["metric"]["failed_calls"] == 1
    truth = [bool(tasks["weekday"]["grade"](t)) for t in ("Thursday", "Monday")]
    assert result["evidence"]["grading_audit"]["runner_disagreed"] == (truth[0] is not False) + (truth[1] is not True)
    assert result["verdict"] == "PARTIAL" and acc["metric"]["promotion_eligible"] is False
    assert acc["subject"] == {"family": "model.routing.acceptance", "task": "taskfit.reason", "job": "ShadowEvals",
                              "study": "free-taskfit-v0"}
    assert acc["arm"]["kind"] == "frontier" and acc["evidence_kind"] == "proxy"
    low, high = cert.wilson(expected, 3)
    assert (acc["metric"]["ci_low"], acc["metric"]["ci_high"]) == (low, high)


def test_certify_refuses_other_task_sets_and_truncated_rows(tmp_path):
    with pytest.raises(cert.CertifyError):
        cert.certify([_write(tmp_path, [_row("groq/x", "weekday", "reason", text="Monday", task_set_sha256="0" * 64)])], "t")
    result = cert.certify([_write(tmp_path, [_row("groq/x", "weekday", "reason", text="Monday"),
                                             _row("groq/x", "weekday", "reason", sample="Mon")])], "t")
    assert result["gates"]["contract"] == "fail"
    assert result["evidence"]["grading_audit"]["rejected"][0]["reason"] == "no full text to re-grade"


def test_committed_pilot_receipt_matches_its_rows():
    run = FT / "data/runs/pilot-20261103"
    fresh = cert.certify([run / "rows.jsonl"], "free-taskfit-pilot-20261103")
    committed = json.loads((run / "result.json").read_text())
    assert fresh["findings"] == committed["findings"]
    assert fresh["evidence"] == committed["evidence"]
