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
plan = _load(FT / "scripts/plan_taskfit.py", "plan_taskfit")
runner = _load(FT / "scripts/run_taskfit.py", "run_taskfit")
PILOT = FT / "data/runs/pilot-20261103/rows.jsonl"
GROQ = "groq/openai/gpt-oss-20b"
OR_FREE = "openrouter/nvidia/nemotron-3.5-super-vl:free"

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


def _row(model, task, family, *, ok=True, text=None, at=1793750000.0, correct=None, rep=0, **extra):
    row = {"model": model, "provider": model.split("/")[0], "task": task, "family": family, "rep": rep, "at": at,
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


def _pilot_rows():
    return [json.loads(line) for line in PILOT.read_text().splitlines() if line.strip()]


def test_certify_regrades_from_text_and_ignores_runner_flag(tmp_path):
    rows = [_row(GROQ, "weekday", "reason", text="Thursday", correct=False),
            _row(GROQ, "weekday", "reason", text="Monday", correct=True, rep=1),
            _row(GROQ, "math-word", "reason", ok=False, error="HTTPError 429 HTTP Error 429: Too Many Requests")]
    tasks = cert.load_tasks()
    expected = sum(bool(tasks["weekday"]["grade"](t)) for t in ("Thursday", "Monday"))
    result = cert.certify([_write(tmp_path, rows)], "t")
    acc = next(f for f in result["findings"] if f["metric"]["name"] == "acceptance_rate")
    assert acc["metric"]["n"] == 3 and acc["metric"]["accepted"] == expected
    assert acc["metric"]["failed_calls"] == 1  # a per-minute 429 on an eligible request is an ordinary failure
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
        cert.certify([_write(tmp_path, [_row(GROQ, "weekday", "reason", text="Monday", task_set_sha256="0" * 64)])], "t")
    result = cert.certify([_write(tmp_path, [_row(GROQ, "weekday", "reason", text="Monday"),
                                             _row(GROQ, "weekday", "reason", sample="Mon", rep=1)])], "t")
    assert result["gates"]["contract"] == "fail"
    assert result["evidence"]["grading_audit"]["rejected"][0]["reason"] == "no full text to re-grade"


# --- limits guards: the 2026-11-03 pilot sent 32k needles to Groq (8K TPM) and counted 413s as wrong answers ---

def test_certify_fails_a_run_with_a_413_row_and_names_limits_json(tmp_path):
    rows = [_row(GROQ, "weekday", "reason", text="Monday"),
            _row(GROQ, "math-word", "reason", ok=False, error="HTTPError 413 HTTP Error 413: Payload Too Large")]
    with pytest.raises(cert.CertifyError, match=r"frozen/limits\.json"):
        cert.certify([_write(tmp_path, rows)], "t")


def test_certify_fails_the_real_pilot_on_its_413_and_ruled_out_rows():
    with pytest.raises(cert.CertifyError, match=r"12 row\(s\).*frozen/limits\.json.*8 came back 413"):
        cert.certify([PILOT], "free-taskfit-pilot-20261103")


def test_not_eligible_rows_leave_the_denominator_and_are_reported(tmp_path):
    rows = [_row(GROQ, "needle-8k", "longctx", text="x", ok=True),
            _row(GROQ, "needle-32k", "longctx", ok=False, status="not_eligible:request_tokens_28366_gt_tpm_8000"),
            _row(GROQ, "weekday", "reason", ok=False, status="quota_exhausted", error="CallError 429 per day (RPD)"),
            _row(OR_FREE, "needle-32k", "longctx", text="x")]
    with pytest.raises(cert.CertifyError):  # needle-8k on Groq is ruled out too (10178 > 8000 TPM)
        cert.certify([_write(tmp_path, rows)], "t")
    result = cert.certify([_write(tmp_path, rows[1:])], "t")
    acc = {(f["arm"]["model"], f["subject"]["task"]): f["metric"] for f in result["findings"]
           if f["metric"]["name"] == "acceptance_rate"}
    assert ("openai/gpt-oss-20b", "taskfit.longctx") not in acc  # p_accept stays unknown, not 0
    assert ("openai/gpt-oss-20b", "taskfit.reason") not in acc
    assert acc[("nvidia/nemotron-3.5-super-vl:free", "taskfit.longctx")]["n"] == 1
    audit = result["evidence"]["grading_audit"]
    assert (audit["not_eligible"], audit["quota_stopped"], audit["failed_calls"]) == (1, 1, 0)
    report = {(r["model"], r["family"]): r["reasons"] for r in result["evidence"]["not_eligible"]}
    assert report[(GROQ, "longctx")] == {"not_eligible:request_tokens_28366_gt_tpm_8000": 1}


def test_planner_plans_out_exactly_the_pilot_rows_groq_could_not_take():
    bad = plan.replay(_pilot_rows(), {t["id"]: t for t in runner.TASKS}, plan.load_limits())
    assert {(b["model"], b["task"]) for b in bad} == {
        (m, t) for m in ("groq/openai/gpt-oss-20b", "groq/openai/gpt-oss-120b")
        for t in ("needle-8k", "needle-32k", "hard-needle-multi")}
    sent_413 = {(r["model"], r["task"], r["rep"]) for r in _pilot_rows() if " 413 " in (r.get("error") or "")}
    assert len(sent_413) == 8 and sent_413 <= {(b["model"], b["task"], b["rep"]) for b in bad}


def test_plan_never_schedules_an_over_limit_request_and_floors_reasoning_max_tokens():
    limits = plan.load_limits()
    items = plan.plan([GROQ, OR_FREE, "groq/unknown-model"], runner.TASKS, 1, limits, max_tokens=512)
    by = {(i["model"], i["task"]): i for i in items}
    assert by[(GROQ, "needle-32k")]["status"].startswith("not_eligible:request_tokens_")
    assert by[(OR_FREE, "needle-32k")]["status"] == "send"
    assert by[("groq/unknown-model", "weekday")]["status"] == "not_eligible:no_limits_entry"
    assert {i["max_tokens"] for i in items if i["model"] == GROQ} == {plan.REASONING_MAX_TOKENS_FLOOR}
    for i in items:
        if i["status"] == "send":
            cap = limits["lanes"][i["model"]]
            assert all(cap.get(d) is None or i["est_request_tokens"] <= cap[d]
                       for d in ("tpm", "context", "max_request_tokens"))


def test_plan_respects_shared_daily_budgets():
    items = plan.plan([OR_FREE, "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free"], runner.TASKS, 2,
                      plan.load_limits())
    assert sum(i["status"] == "send" for i in items) == 50  # one key, 50 :free requests/day across models


def test_plan_refuses_to_re_probe_a_measured_lane_unless_forced(tmp_path):
    run = tmp_path / "r1"; run.mkdir()
    (run / "result.json").write_text(json.dumps({"run_id": "r1", "gates": {"contract": "pass"}, "findings": [
        {"expires_at": "2099-01-01T00:00:00Z", "arm": {"transport": "groq", "model": "openai/gpt-oss-20b"},
         "subject": {"task": "taskfit.reason"}, "metric": {"name": "acceptance_rate"}}]}))
    measured = plan.measured_pairs(tmp_path)
    assert measured == {(GROQ, "reason"): "r1"}
    items = plan.plan([GROQ], runner.TASKS, 1, plan.load_limits(), measured=measured)
    reason = [i for i in items if i["family"] == "reason"]
    assert reason and all(i["status"] == "skipped:already_measured:r1" for i in reason)
    forced = plan.plan([GROQ], runner.TASKS, 1, plan.load_limits(), measured=measured, force=True)
    assert all(i["status"] == "send" for i in forced if i["family"] == "reason")


def test_runner_stops_a_lane_on_daily_quota_and_never_sends_planned_out_rows(tmp_path, monkeypatch):
    sent = []

    def fake_call(provider, model, prompt, max_tokens, timeout=180):
        sent.append((model, len(prompt), max_tokens))
        raise runner.CallError(429, "Rate limit reached for model on requests per day (RPD): Limit 1000, Used 1000")

    monkeypatch.setattr(runner, "call", fake_call)
    monkeypatch.setattr(runner.time, "sleep", lambda s: None)
    monkeypatch.setattr(runner.planner, "measured_pairs", lambda *a, **k: {})
    out = tmp_path / "rows.jsonl"
    assert runner.main(["--only", GROQ, "--repeats", "1", "--out", str(out)]) == 0
    rows = [json.loads(l) for l in out.read_text().splitlines()]
    assert len(sent) == 1 and sent[0][2] >= plan.REASONING_MAX_TOKENS_FLOOR
    assert [r["status"] for r in rows if not r["status"].startswith("not_eligible")] == ["quota_exhausted"]
    assert {r["task"] for r in rows if r["status"].startswith("not_eligible")} == {
        "needle-8k", "needle-32k", "hard-needle-multi"}


def test_runner_sends_a_browser_like_user_agent():
    assert runner.USER_AGENT.startswith("Mozilla/5.0") and "urllib" not in runner.USER_AGENT


def test_frozen_limits_pin_their_source():
    limits = plan.load_limits()
    src = {s["path"]: s for s in limits["sources"]}
    assert src["deploy/vllm-sr/limits.json"]["repo"] == "kvnloo/z0intelligence"
    assert len(src["deploy/vllm-sr/limits.json"]["commit"]) == 40
    assert limits["lanes"][GROQ]["tpm"] == 8000


def test_free_taskfit_workflow_is_dispatch_only_and_serialized():
    import yaml
    wf = yaml.safe_load((REPO / ".github/workflows/free-taskfit.yml").read_text())
    triggers = wf.get("on", wf.get(True))
    assert set(triggers) == {"workflow_dispatch", "schedule"}  # never pull_request (fork PRs must not see keys)
    assert wf["concurrency"]["cancel-in-progress"] is False and "free-taskfit" in wf["concurrency"]["group"]
    text = (REPO / ".github/workflows/free-taskfit.yml").read_text()
    for name in ("GROQ_API_KEY", "OPENROUTER_API_KEY", "NVIDIA_API_KEY"):
        assert f"secrets.{name}" in text
    assert "actions/upload-artifact" in text
