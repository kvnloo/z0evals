#!/usr/bin/env python3
"""Snapshot the published Hermes Index table (https://portal.nousresearch.com/bench).

This is an EXTERNAL, source-reported prior. z0evals did not run these
evaluations. The snapshot records exactly what the page showed at capture time,
with the raw page sha256, so a later change on the page is a new snapshot, not
an edit of this one.

Usage:
  snapshot_hermes_index.py --out data/snapshots/hermes-index-<date>.json            # fetch live
  snapshot_hermes_index.py --from-html page.html --captured-at 2026-11-03T20:32:51Z --out ...

Stdlib only. No credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import html as htmllib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone

URL = "https://portal.nousresearch.com/bench"
SCHEMA = "z0eval.external-benchmark-snapshot.v1"
SUITES = ("hermes_bench", "terminalbench_4", "terminalbench_science", "skillsbench")
SUITE_LABELS = ("Hermes Bench", "TerminalBench 4", "TerminalBench Science", "SkillsBench")
_SCORE = re.compile(r"^-?\d+(?:\.\d+)?$")
_COST = re.compile(r"^\$(\d+(?:\.\d+)?)(\*)?(?: · (\d+(?:\.\d+)?) raw)?$")


class ParseError(ValueError):
    pass


def page_lines(raw: str) -> list[str]:
    text = re.sub(r"<script.*?</script>", "", raw, flags=re.S)
    text = re.sub(r"<style.*?</style>", "", text, flags=re.S)
    text = htmllib.unescape(re.sub(r"<[^>]+>", "\n", text))
    lines = [line.strip() for line in text.split("\n")]
    # Drop empty lines, the decorative bar rows ("////...") and the bar "x" glyph.
    return [line for line in lines if line and not set(line) <= {"/"} and line != "x"]


def _cost(token: str) -> tuple[float, bool, float | None]:
    match = _COST.match(token)
    if not match:
        raise ParseError(f"expected a $ cost cell, got {token!r}")
    return float(match.group(1)), bool(match.group(2)), (float(match.group(3)) if match.group(3) else None)


def parse(lines: list[str]) -> dict:
    try:
        start = lines.index("Columns (8/8)")
    except ValueError as exc:
        raise ParseError("leaderboard header 'Columns (8/8)' not found; page layout changed") from exc
    header = lines[start + 1:start + 17]
    for label in ("Model", "Hermes Index", "$ / task", *SUITE_LABELS):
        if label not in header:
            raise ParseError(f"leaderboard column {label!r} missing; page layout changed")
    i = start + 1
    while not re.fullmatch(r"\d{2}", lines[i]):
        i += 1
    rows = []
    while i < len(lines) and re.fullmatch(r"\d{2}", lines[i]):
        rank = int(lines[i]); name = lines[i + 1]; vendor = lines[i + 2]
        if not _SCORE.match(lines[i + 3]):
            raise ParseError(f"row {rank}: index score missing")
        index = float(lines[i + 3]); j = i + 4
        cost, provisional, _ = _cost(lines[j]); j += 1
        if j < len(lines) and lines[j] == "*":  # provisional marker rendered as its own cell
            provisional = True; j += 1
        suites = {}
        for key in SUITES:
            if not _SCORE.match(lines[j]):
                raise ParseError(f"row {rank} {name}: {key} score missing, got {lines[j]!r}")
            score = float(lines[j]); suite_cost, suite_prov, raw = _cost(lines[j + 1]); j += 2
            suites[key] = {"score": score, "usd_per_task": suite_cost, "provisional": suite_prov}
            if raw is not None:
                suites[key]["raw_score"] = raw
        rows.append({"rank": rank, "model": name, "vendor": vendor, "hermes_index": index,
                     "usd_per_task": cost, "cost_provisional": provisional, "suites": suites})
        i = j
    if not rows:
        raise ParseError("no leaderboard rows parsed")
    if [r["rank"] for r in rows] != list(range(1, len(rows) + 1)):
        raise ParseError("leaderboard ranks are not contiguous; parse is incomplete")
    for row in rows:
        mean = sum(row["suites"][k]["score"] for k in SUITES) / len(SUITES)
        # The page defines the index as the mean of the four suite scores; keep the
        # check so a silent column shift fails closed instead of producing a table.
        if abs(mean - row["hermes_index"]) > 0.06:
            raise ParseError(f"{row['model']}: index {row['hermes_index']} != suite mean {mean:.2f}")
    notes = [line for line in lines if line.startswith(("All evaluations are pass@1", "* Provisional",
             "Clean / raw", "TerminalBench 4 runs without", "Hermes Index is the mean"))]
    return {"rows": rows, "page_notes": sorted(set(notes))}


def snapshot(raw: bytes, captured_at: str, url: str = URL) -> dict:
    parsed = parse(page_lines(raw.decode("utf-8", errors="replace")))
    return {
        "schema": SCHEMA,
        "benchmark": "Hermes Index",
        "source_url": url,
        "publisher": "Nous Research",
        "captured_at": captured_at,
        "published_at": None,
        "published_at_note": "The page shows no publication or update date; captured_at is the only time bound.",
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "evidence_status": "source-reported",
        "z0evals_measured": False,
        "harness": "Hermes Agent (reasoning effort high where offered), pass@1, per the page notes",
        "suites": dict(zip(SUITES, SUITE_LABELS)),
        "suite_public_status": {
            "hermes_bench": "not public: no task set, grader or harness command published by Nous Research",
            "terminalbench_4": "public: Harbor dataset terminal-bench/terminal-bench@4.0.0",
            "terminalbench_science": "public: Harbor dataset terminal-bench-science/terminal-bench-science",
            "skillsbench": "public: github.com/benchflow-ai/skillsbench (Apache-2.0), BenchFlow CLI",
        },
        "use_rule": ("Prior only. A Hermes Index or suite score is never p_accept for a routing task class; "
                     "it is an external_benchmark row with its source and capture time."),
        **parsed,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-html")
    ap.add_argument("--captured-at", help="ISO-8601 UTC capture time (required with --from-html)")
    ap.add_argument("--url", default=URL)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    if args.from_html:
        if not args.captured_at:
            ap.error("--captured-at is required with --from-html")
        raw = open(args.from_html, "rb").read(); captured = args.captured_at
    else:
        req = urllib.request.Request(args.url, headers={"User-Agent": "Mozilla/5.0 (z0evals snapshot)"})
        raw = urllib.request.urlopen(req, timeout=60).read()
        captured = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data = snapshot(raw, captured, args.url)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, sort_keys=False)
        fh.write("\n")
    print(f"{len(data['rows'])} rows, raw sha256 {data['raw_sha256'][:16]}, captured {captured}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
