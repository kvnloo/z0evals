#!/usr/bin/env python3
"""Recompute every number the post quotes from the frozen rows. Writes data/summary.json."""
from __future__ import annotations

import json
from pathlib import Path
from statistics import mean, median

DATA = Path(__file__).resolve().parents[1] / "data"


def fmt(rows: list[dict]) -> dict:
    return {
        "runs": len(rows),
        "passed": sum(r["ready"] and r["faithful"] for r in rows),
        "output_tokens_total": sum(r["tokens"]["output"] for r in rows),
        "output_tokens_mean": round(mean(r["tokens"]["output"] for r in rows)),
        "input_tokens_mean": round(mean(r["tokens"]["input"] for r in rows)),
        "artifact_chars_mean": round(mean(r["artifactChars"] for r in rows)),
        "total_s_mean": round(mean(r["totalMs"] for r in rows) / 1000, 1),
        "total_s_median": round(median(r["totalMs"] for r in rows) / 1000, 1),
        "first_text_s_mean": round(mean(r["firstTextMs"] for r in rows) / 1000, 1),
        "after_first_text_s_mean": round(mean(r["totalMs"] - r["firstTextMs"] for r in rows) / 1000, 1),
    }


def main() -> None:
    ab = json.loads((DATA / "ab-rows.json").read_text())
    html = [r for r in ab if r["format"] == "html"]
    openui = [r for r in ab if r["format"] == "openui"]
    h, o = fmt(html), fmt(openui)
    cases = []
    for case in sorted({r["id"] for r in ab}):
        ch = [r for r in html if r["id"] == case]
        co = [r for r in openui if r["id"] == case]
        cases.append({
            "id": case,
            "html_output_tokens_mean": round(mean(r["tokens"]["output"] for r in ch)),
            "openui_output_tokens_mean": round(mean(r["tokens"]["output"] for r in co)),
            "html_total_s_mean": round(mean(r["totalMs"] for r in ch) / 1000, 1),
            "openui_total_s_mean": round(mean(r["totalMs"] for r in co) / 1000, 1),
        })
    gen = json.loads((DATA / "generation-rows.json").read_text())
    by_model = {}
    for model in sorted({r["model"] for r in gen}):
        rows = [r for r in gen if r["model"] == model]
        by_model[model] = {
            "runs": len(rows),
            "passed": sum(r["ready"] and r["faithful"] for r in rows),
            "output_tokens_mean": round(mean(r["tokens"]["output"] for r in rows)),
            "total_s_mean": round(mean(r["totalMs"] for r in rows) / 1000, 1),
        }
    rescore = json.loads((DATA / "generation-rescore.json").read_text())["tally"]
    for model, tally in rescore.items():
        by_model[model]["passed_after_rescore"] = tally["pass"]
    live = json.loads((DATA / "t3-live-verdicts.json").read_text())
    summary = {
        "ab": {
            "model": html[0]["model"],
            "html": h,
            "openui": o,
            "output_token_ratio": round(h["output_tokens_total"] / o["output_tokens_total"], 1),
            "total_time_ratio": round(h["total_s_mean"] / o["total_s_mean"], 1),
            "input_token_overhead_mean": o["input_tokens_mean"] - h["input_tokens_mean"],
            "cases": cases,
        },
        "generation": by_model,
        "t3_live": {"runs": len(live), "passed": sum(r["status"] == "PASS" for r in live)},
    }
    (DATA / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
