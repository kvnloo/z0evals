#!/usr/bin/env python3
"""Plan a free task-fit run against the frozen per-model limits before any call.

One source of truth for "may this request be sent": run_taskfit.py uses it to
decide what to send, and certify.py uses it to refuse rows that were sent
anyway. Limits come from ../frozen/limits.json (freeze_limits.py, pinned to
z0intelligence deploy/vllm-sr/limits.json); a lane with no entry there is not
eligible, because an unknown limit is never an unlimited one.

  plan_taskfit.py --only groq/openai/gpt-oss-20b,... [--repeats 2] [--max-tokens 4096] [--rows OLD.jsonl]

With --rows it replays a past run's rows through the plan and lists every row
the plan would never have sent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY_DIR = HERE.parent
LIMITS = STUDY_DIR / "frozen" / "limits.json"
RECEIPTS = STUDY_DIR / "data" / "runs"
CHARS_PER_TOKEN = 3.5  # conservative: real tokenizers measured 3.6-4.1 chars/token on this battery
REASONING_MAX_TOKENS_FLOOR = 4096  # below this reasoning models return empty content
DEFAULT_MAX_TOKENS = 4096
NOT_ELIGIBLE = "not_eligible:"
QUOTA_EXHAUSTED = "quota_exhausted"
# A daily cap answers every later call the same way: stop the lane instead of retrying.
DAILY_QUOTA = re.compile(r"free usage limit|free-models-per-day|per day|\bRPD\b|\bTPD\b|daily (?:limit|quota)", re.I)
TOO_LARGE = re.compile(r"^\S+ 413\b|payload too large|request too large|request_too_large|context_length_exceeded|"
                       r"maximum context length", re.I)


def load_limits(path: Path = LIMITS) -> dict:
    data = json.loads(path.read_text())
    data["_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return data


def is_reasoning(spec: str, entry: dict | None) -> bool:
    if entry is not None and "reasoning" in entry:
        return bool(entry["reasoning"])
    return any(t in spec.lower() for t in ("gpt-oss", "nemotron", "qwen3", "deepseek-r", "-r1", "thinking"))


def max_tokens_for(spec: str, entry: dict | None, requested: int = DEFAULT_MAX_TOKENS) -> int:
    return max(requested, REASONING_MAX_TOKENS_FLOOR) if is_reasoning(spec, entry) else requested


def estimate_request_tokens(prompt: str, max_tokens: int) -> int:
    return math.ceil(len(prompt) / CHARS_PER_TOKEN) + max_tokens


def check(spec: str, prompt: str, limits: dict, max_tokens: int) -> tuple[str | None, int]:
    """Return (reason it may not be sent or None, estimated request tokens)."""
    entry = limits["lanes"].get(spec)
    est = estimate_request_tokens(prompt, max_tokens)
    if entry is None:
        return "no_limits_entry", est
    for dim in ("tpm", "context", "max_request_tokens"):
        cap = entry.get(dim)
        if cap is not None and est > cap:
            return f"request_tokens_{est}_gt_{dim}_{cap}", est
    return None, est


def measured_pairs(receipts: Path = RECEIPTS, now: datetime | None = None) -> dict[tuple[str, str], str]:
    """(lane, family) -> run_id for unexpired acceptance findings in committed, contract-passing receipts."""
    now = now or datetime.now(timezone.utc)
    out: dict[tuple[str, str], str] = {}
    for path in sorted(receipts.glob("*/result.json")):
        result = json.loads(path.read_text())
        if result.get("gates", {}).get("contract") != "pass":
            continue
        for f in result.get("findings", []):
            if f.get("metric", {}).get("name") != "acceptance_rate":
                continue
            expires = datetime.fromisoformat(f["expires_at"].replace("Z", "+00:00"))
            if expires > now:
                arm = f["arm"]
                out[(f"{arm['transport']}/{arm['model']}", f["subject"]["task"].removeprefix("taskfit."))] = result["run_id"]
    return out


def plan(specs: list[str], tasks: list[dict], repeats: int, limits: dict, max_tokens: int = DEFAULT_MAX_TOKENS,
         measured: dict | None = None, force: bool = False) -> list[dict]:
    """Every (lane, task, rep) with status `send`, `not_eligible:<reason>` or `skipped:already_measured:<run>`.

    Per-request checks first (tpm, context, max request), then the lane's daily budgets (rpd, tpd) in
    send order, so a plan never schedules more calls or tokens than the lane can take in a day.
    """
    measured = measured or {}
    items = []
    used: dict[str, list[int]] = {}  # budget bucket -> [calls, tokens]; account-wide limits share one bucket
    for spec in specs:
        entry = limits["lanes"].get(spec)
        mt = max_tokens_for(spec, entry, max_tokens)
        bucket = spec if (entry or {}).get("scope", "per model") == "per model" else spec.split("/", 1)[0]
        budget = used.setdefault(bucket, [0, 0])
        for rep in range(repeats):
            for task in tasks:
                reason, est = check(spec, task["prompt"], limits, mt)
                item = {"model": spec, "task": task["id"], "family": task["family"], "rep": rep,
                        "est_request_tokens": est, "max_tokens": mt}
                run = measured.get((spec, task["family"]))
                if run and not force:
                    item["status"] = f"skipped:already_measured:{run}"
                elif reason:
                    item["status"] = NOT_ELIGIBLE + reason
                elif entry.get("rpd") is not None and budget[0] + 1 > entry["rpd"]:
                    item["status"] = NOT_ELIGIBLE + f"rpd_budget_{entry['rpd']}_{bucket}"
                elif entry.get("tpd") is not None and budget[1] + est > entry["tpd"]:
                    item["status"] = NOT_ELIGIBLE + f"tpd_budget_{entry['tpd']}_{bucket}"
                else:
                    item["status"] = "send"
                    budget[0] += 1; budget[1] += est
                items.append(item)
    return items


def replay(rows: list[dict], tasks: dict, limits: dict) -> list[dict]:
    """Rows of a past run that the plan would never have sent, with the reason."""
    bad = []
    for row in rows:
        if str(row.get("status", "")).startswith(NOT_ELIGIBLE) or row.get("task") not in tasks:
            continue
        entry = limits["lanes"].get(row["model"])
        mt = row.get("max_tokens") or max_tokens_for(row["model"], entry)
        reason, est = check(row["model"], tasks[row["task"]]["prompt"], limits, mt)
        if reason:
            bad.append({"model": row["model"], "task": row["task"], "rep": row.get("rep"), "reason": reason,
                        "sent_result": (row.get("error") or "answered")[:40]})
    return bad


def summarize(items: list[dict]) -> list[str]:
    """One line per (lane, status) that is not `send`, naming the tasks it covers."""
    groups: dict[tuple[str, str], list[str]] = {}
    for it in items:
        if it["status"] != "send":
            groups.setdefault((it["model"], it["status"]), []).append(f"{it['task']}#{it['rep']}")
    sent = sum(it["status"] == "send" for it in items)
    return [f"send {sent}/{len(items)}"] + [f"  {m}: {st}: {', '.join(ts)}" for (m, st), ts in groups.items()]


def daily_quota_error(code: int | None, body: str) -> bool:
    return code == 429 and bool(DAILY_QUOTA.search(body or ""))


def too_large_error(text: str, http_status: int | None = None) -> bool:
    """413 or a provider's request-too-large/context-length wording (error rows are `<Type> <code> <body>`)."""
    return http_status == 413 or bool(TOO_LARGE.search(text or ""))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma list of provider/model")
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    ap.add_argument("--rows", type=Path, help="replay a past rows.jsonl through the plan")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    sys.path.insert(0, str(STUDY_DIR / "frozen"))
    from tasks import TASKS  # noqa: PLC0415
    limits = load_limits()
    if a.rows:
        rows = [json.loads(l) for l in a.rows.read_text().splitlines() if l.strip()]
        bad = replay(rows, {t["id"]: t for t in TASKS}, limits)
        for b in bad:
            print(json.dumps(b))
        print(f"{len(bad)}/{len(rows)} rows were sent although frozen/limits.json rules them out", file=sys.stderr)
        return 1 if bad else 0
    items = plan([s for s in a.only.split(",") if s], TASKS, a.repeats, limits, a.max_tokens,
                 measured_pairs(), a.force)
    print("\n".join(summarize(items)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
