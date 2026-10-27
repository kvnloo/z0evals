#!/usr/bin/env python3
"""Regenerate the live status block of posts/cua-trycua-contributions.md.

Reads studies/cua-trycua/{tracked.json,receipts.jsonl}, refreshes each tracked GitHub
issue/PR state (GITHUB_TOKEN optional; 10 s timeout per call) and writes
web/data/generated/cua-status.md. build_posts.py splices that file between the post's
<!-- generated:cua-status --> markers. Any item GitHub does not answer keeps its
committed snapshot state and is marked as such, so the site build never fails here.
Usage: build_cua_status.py [--offline]
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STUDY = ROOT / "studies/cua-trycua"
OUT = ROOT / "web/data/generated/cua-status.md"


def fetch_state(item: dict, token: str | None) -> str | None:
    kind = "pulls" if item["kind"] == "pr" else "issues"
    req = urllib.request.Request(f"https://api.github.com/repos/{item['repo']}/{kind}/{item['number']}",
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "z0evals-cua-status"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
    except (OSError, ValueError):
        return None
    if item["kind"] == "pr" and data.get("merged_at"):
        return "MERGED"
    return str(data.get("state", "")).upper() or None


def link(item: dict) -> str:
    path = "pull" if item["kind"] == "pr" else "issues"
    return f"[{item['repo']}#{item['number']}](https://github.com/{item['repo']}/{path}/{item['number']})"


def build(offline: bool = False) -> str:
    tracked = json.loads((STUDY / "tracked.json").read_text(encoding="utf-8"))
    runs = [json.loads(line) for line in (STUDY / "receipts.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    token = os.environ.get("GITHUB_TOKEN")
    stale = 0
    items = []
    for item in tracked["items"]:
        live = None if offline else fetch_state(item, token)
        stale += live is None
        items.append({**item, "state": live or item["state"], "live": live is not None})

    upstream = [i for i in items if i["repo"] == tracked["upstream_repo"]]
    merged = [i for i in upstream if i["kind"] == "pr" and i["state"] == "MERGED"]
    in_review = [i for i in upstream if i["role"] == "review" and i["state"] == "OPEN"]
    rfcs = [i for i in items if i["role"] == "rfc"]
    experiments = [i for i in items if i["role"] == "experiment"]
    results = Counter(r["result"] for r in runs)
    seconds = sum(r["seconds"] for r in runs)
    dollars = sum(r["dollars"] for r in runs)
    latest = max((r["date"] for r in runs), default="—")

    lines = [
        "| where things stand | |",
        "|---|---:|",
        f"| upstream prs merged into trycua/cua | {len(merged)} |",
        f"| upstream prs open for review | {len(in_review)} |",
        f"| rfcs (upstream + downstream) | {len(rfcs)} ({sum(i['state'] == 'OPEN' for i in rfcs)} open) |",
        f"| downstream experiments tracked | {len(experiments)} |",
        f"| remote experiment runs | {len(runs)} ({results.get('pass', 0)} pass, {results.get('partial', 0)} partial, {results.get('blocked', 0)} blocked), latest {latest} |",
        f"| remote compute so far | {seconds / 60:.1f} min, ${dollars:.4f} |",
        "",
        "**latest runs**",
        "",
        "| run | date | class | result | what it showed |",
        "|---|---|---|---|---|",
    ]
    for r in sorted(runs, key=lambda r: (r["date"], r["run"]), reverse=True)[:8]:
        lines.append(f"| {r['run']} | {r['date']} | {r['evidence_class'].lower()} | {r['result']} | {r['summary']} |")
    lines += ["", "**open review and experiments**", "", "| item | role | state | credit |", "|---|---|---|---|"]
    for i in [*in_review, *experiments, *(i for i in items if i["role"] == "collaboration")]:
        lines.append(f"| {link(i)} {i['title']} | {i['role']} | {i['state'].lower()} | {i['credit']} |")
    note = ("all states read live from github at build time" if not stale else
            f"{len(items) - stale} of {len(items)} states read live at build time; the rest show the {tracked['snapshot_at']} snapshot")
    lines += ["", f"<p class=\"small\">{note}. runs are counted from studies/cua-trycua/receipts.jsonl.</p>"]
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(offline="--offline" in sys.argv), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
