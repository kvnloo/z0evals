#!/usr/bin/env python3
"""Local-only, read-only overnight forensics. Never emit transcript text."""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
from zoneinfo import ZoneInfo

PROVISIONAL = True
ZONE = ZoneInfo("America/Chicago")
OVERNIGHT_START_HOUR = 22
OVERNIGHT_END_HOUR = 5
MIN_RUNNING_SECONDS = 3600
STALL_SECONDS = 7200
RESTART_SECONDS = 12 * 3600
MIN_CELL = 15
SUCCESS_OUTCOMES = {"completed", "success", "succeeded"}
NORMAL_TERMINATIONS = {"clean", "normal", "completed"}
FAILED_TERMINATIONS = {"killed", "timeout", "timed_out", "idle_timeout", "startup_orphan_reap", "ws_orphan_reap"}
ACCEPTANCE_RE = re.compile(r"acceptance|test|done when|\bDoD\b|\[[ xX]\]", re.I)
OPEN_ENDED_RE = re.compile(r"make everything|all night|keep going|work all night|super good", re.I)
RESUME_RE = re.compile(r"\b(resume|resuming|continue|continuation)\b", re.I)
MENTIONS = {k: re.compile(v, re.I) for k, v in {
    "branch": r"\bbranch\b", "pr": r"\bPR\b|pull request",
    "checkpoint": r"\bcheckpoint\b", "resume": RESUME_RE.pattern,
}.items()}
HARNESSES = {"hermes", "omp", "claude", "codex", "opencode", "pi", "chatgpt", "cursor", "cursor-ide", "gemini", "kimi", "grok", "antigravity-cli", "deepseek-harness", "measure", "omo"}
OUTPUT = Path.home() / ".local/state/overnight-forensics"


def timestamp(value):
    if value is None or value == "":
        return None
    try:
        if isinstance(value, (float, int)):
            return float(value)
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        # Naive timestamps have no trustworthy local/UTC interpretation.
        return dt.timestamp() if dt.tzinfo else None
    except (ValueError, TypeError, OverflowError):
        return None


def night_key(start):
    local = datetime.fromtimestamp(start, ZONE)
    return (local.date() - timedelta(days=local.hour < 12)).isoformat()


def overnight(start, activity_end, terminated_end=None):
    """Clock-only, [22:00,05:00); observed activity interval spans 03:00."""
    if start is None or activity_end is None or activity_end < start:
        return False
    local = datetime.fromtimestamp(start, ZONE)
    alive_until = max(activity_end, terminated_end or activity_end)
    if (local.hour >= OVERNIGHT_START_HOUR or local.hour < OVERNIGHT_END_HOUR) and alive_until - start >= MIN_RUNNING_SECONDS:
        return True
    day = local.date()
    last = datetime.fromtimestamp(activity_end, ZONE).date()
    while day <= last:
        boundary = datetime(day.year, day.month, day.day, 3, tzinfo=ZONE).timestamp()
        if start <= boundary <= activity_end:
            return True
        day += timedelta(days=1)
    return False


def prompt_features(prompt):
    if prompt is None:
        return {"prompt_length": None, "acceptance": None, "open_ended": None,
                **{f"mentions_{k}": None for k in MENTIONS}}
    return {"prompt_length": len(prompt), "acceptance": bool(ACCEPTANCE_RE.search(prompt)),
            "open_ended": bool(OPEN_ENDED_RE.search(prompt)),
            **{f"mentions_{k}": bool(v.search(prompt)) for k, v in MENTIONS.items()}}


def labels(outcome, termination, end, last_event, needed_owner=None):
    completed = None
    stalled = None
    if termination in FAILED_TERMINATIONS:
        stalled = True
        completed = False
    elif end is not None and last_event is not None and end - last_event >= STALL_SECONDS:
        stalled = True
        completed = False
    elif termination in NORMAL_TERMINATIONS and outcome in SUCCESS_OUTCOMES:
        completed = True
        stalled = False
    if needed_owner is True:
        completed = False
    return {"completed_unattended": completed, "stalled": stalled, "needed_owner": needed_owner}


def private_directory(path):
    path = Path(path).expanduser()
    if path.is_symlink():
        raise ValueError("output directory cannot be a symlink")
    path = path.resolve()
    # No private export inside any Git worktree, including linked worktrees.
    if any((p / ".git").exists() for p in [path, *path.parents]):
        raise ValueError("private output cannot be inside a Git worktree")
    if path.is_symlink():
        raise ValueError("output directory cannot be a symlink")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.chmod(0o700)
    return path


def private_write(path, data):
    if path.is_symlink():
        raise ValueError("output file cannot be a symlink")
    tmp = path.with_name(path.name + ".new")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        path.chmod(0o600)
    finally:
        tmp.unlink(missing_ok=True)


def connect(path):
    conn = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    conn.execute("PRAGMA cache_size=-4096")
    conn.execute("BEGIN")
    return conn


def columns(conn, table):
    return {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')}


def digest(value):
    return hashlib.sha256(str(value).encode()).hexdigest()


def inventory(path):
    s = path.stat()
    return {"bytes": s.st_size, "mtime_ns": s.st_mtime_ns,
            "wal_present": Path(str(path) + "-wal").exists(),
            "shm_present": Path(str(path) + "-shm").exists()}


def extract_sessions(path, source, seen, rows, manifest, cutoff=None):
    before = inventory(path)
    conn = connect(path)
    try:
        sc, mc = columns(conn, "sessions"), columns(conn, "messages")
        if not {"id", "started_at"} <= sc or not {"session_id", "role", "content", "timestamp"} <= mc:
            manifest.append({"source": source, "status": "unsupported_schema"})
            return
        schema = "\n".join(r[0] or "" for r in conn.execute("SELECT sql FROM sqlite_master ORDER BY name"))
        n = duplicates = scanned = 0
        excluded = Counter()
        for raw in conn.execute('SELECT * FROM sessions ORDER BY started_at, id'):
            scanned += 1
            r = dict(raw)
            start = timestamp(r["started_at"])
            if start is None:
                excluded["invalid_start"] += 1
                continue
            if r.get("deleted_at"):
                excluded["deleted"] += 1
                continue
            if cutoff is not None and start > cutoff:
                excluded["future_start"] += 1
                continue
            harness = r.get("agent") if source == "agentsview" else "hermes"
            native = r.get("source_session_id") or r["id"]
            # AgentsView Hermes IDs are profile-prefixed; first match exact native
            # source IDs, then cross-source aliases collected by the caller.
            aliases = {str(native), str(r["id"])}
            existing = next((seen[(harness, alias)] for alias in aliases if (harness, alias) in seen), None)
            if existing is not None:
                duplicates += 1
                if source == "hermes":
                    # Enrich the indexed mirror with an independent native exit;
                    # keep one unit, never count the same session twice.
                    end = timestamp(r.get("ended_at"))
                    termination = r.get("end_reason")
                    if termination in {"agent_close", "cli_close", "cron_complete", "tui_close", "tui_shutdown"}:
                        termination = "normal"
                    if end is not None and (existing["end"] is None or end >= existing["end"]):
                        existing["end"] = end
                        existing["native_exit_enriched"] = True
                        existing["termination_failed"] = termination in FAILED_TERMINATIONS
                        existing["labels"] = labels(existing["reported_outcome"], termination, end, existing["activity_end"])
                        # Mutable source outcomes have no historical raised-at
                        # event. Read time is a conservative availability bound,
                        # not a claim that the outcome was known at native exit.
                        existing["outcome_observed_at"] = datetime.now(timezone.utc).timestamp()
                        existing["overnight"] = overnight(existing["start"], existing["activity_end"], end)
                continue
            order = "ordinal" if "ordinal" in mc else "id"
            user = conn.execute(f"SELECT content,timestamp FROM messages WHERE session_id=? AND role='user' ORDER BY {order} LIMIT 1", (r["id"],)).fetchone()
            prompt = user[0] if user else None
            # Do not read later prompts. First user message may be a wrapper;
            # preserve that limitation rather than mining post-dispatch text.
            if prompt is not None and not isinstance(prompt, str):
                prompt = None
            prompt_time = timestamp(user[1]) if user else None
            # Missing/late first prompts are not dispatch-time observations.
            prompt_valid = prompt_time is not None and start <= prompt_time <= start + 60
            features = prompt_features(prompt if prompt_valid else None)
            last = conn.execute("SELECT max(timestamp) FROM messages WHERE session_id=?", (r["id"],)).fetchone()[0]
            last = timestamp(last)
            av = source == "agentsview"
            end = timestamp(r.get("ended_at"))
            # AgentsView ended_at is a transcript timestamp, NOT an exit event.
            terminated_end = None if av else end
            activity_end = last
            termination = r.get("termination_status") if av else r.get("end_reason")
            outcome = r.get("outcome") if av else None
            project = r.get("project") if av else (r.get("git_repo_root") or r.get("cwd"))
            record = {"id": digest((harness, native)), "source": source,
                      "start": start, "activity_end": activity_end, "end": terminated_end,
                      "project": digest(project) if project else None,
                      "parent": digest((harness, r["parent_session_id"])) if r.get("parent_session_id") else None,
                      "night": night_key(start), "overnight": overnight(start, activity_end, terminated_end),
                      "features": {"start_hour": datetime.fromtimestamp(start, ZONE).hour,
                                   "weekday": datetime.fromtimestamp(start, ZONE).weekday(),
                                   "harness": harness if harness in HARNESSES else "other",
                                   # Session model/provider fields are mutable lifetime
                                   # summaries, not immutable dispatch configuration.
                                   "model": None, "provider": None,
                                   "is_automated": bool(r["is_automated"]) if av and r.get("is_automated") is not None else None,
                                   **features},
                      "labels": labels(outcome, termination, terminated_end, last),
                      "outcome_observed_at": datetime.now(timezone.utc).timestamp(),
                      "termination_failed": termination in FAILED_TERMINATIONS,
                      "reported_outcome": outcome if outcome in SUCCESS_OUTCOMES | {"unknown", "abandoned"} else None,
                      "signals": {k: r.get(k) for k in ["health_score", "runaway_tool_loop_count", "compaction_count", "tool_failure_signal_count"]} if av else {},
                      "restart_observable": prompt_valid,
                      "_native": str(native), "_aliases": aliases, "_harness": harness,
                      "_parent_native": r.get("parent_session_id")}
            rows.append(record)
            for alias in aliases:
                seen[(harness, alias)] = record
            n += 1
        manifest.append({"source": source, "rows": n, "duplicates": duplicates,
                         "scanned": scanned, "excluded": dict(excluded),
                         "schema_sha256": digest(schema), "before": before,
                         "after": inventory(path), "status": "read_only_transaction"})
    finally:
        conn.close()


def enrich_blocked(path, rows, manifest):
    """Only exact task-session links and timestamped blocked events; no text joins."""
    conn = connect(path)
    try:
        if not {"session_id", "id"} <= columns(conn, "tasks"):
            manifest.append({"source": "kanban", "status": "unsupported_schema"})
            return
        lookup = defaultdict(list)
        for r in rows:
            if r["_harness"] == "hermes":
                for alias in r["_aliases"]:
                    lookup[alias].append(r)
        event_columns = columns(conn, "task_events")
        run_sessions = {}
        if {"run_id", "payload"} <= event_columns:
            for event in conn.execute("SELECT run_id,payload FROM task_events WHERE kind='owner_admitted' AND run_id IS NOT NULL"):
                try:
                    payload = json.loads(event["payload"] or "{}")
                    if payload.get("session_id"):
                        run_sessions[event["run_id"]] = payload["session_id"]
                except (ValueError, TypeError):
                    continue
        linked = blocked = 0
        run_column = "e.run_id" if "run_id" in event_columns else "NULL"
        for event in conn.execute(f"SELECT t.session_id,e.created_at,{run_column} AS run_id FROM task_events e JOIN tasks t ON t.id=e.task_id WHERE e.kind='blocked'"):
            when = timestamp(event["created_at"])
            session = run_sessions.get(event["run_id"], event["session_id"])
            for r in lookup.get(session, []):
                linked += 1
                end = r["end"] or r["activity_end"]
                if when is not None and end is not None and r["start"] <= when <= end:
                    r["labels"]["needed_owner"] = True
                    r["labels"]["completed_unattended"] = False
                    # Retain the conservative snapshot bound if already known;
                    # never backdate other outcome evidence to the block event.
                    r["outcome_observed_at"] = max(r.get("outcome_observed_at") or when, when)
                    blocked += 1
        manifest.append({"source": "kanban", "status": "exact_links_only", "linked_events": linked, "blocked_during_run": blocked,
                         "limitation": "Current task-session linkage can omit earlier attempts; no negative owner label inferred."})
    finally:
        conn.close()


def inspect_needs_owner(path, manifest):
    if not path or not path.exists():
        manifest.append({"source": "needs_owner", "status": "unavailable"})
        return
    # Inspect only the nominated snapshot and matching adjacent history JSON.
    files = sorted(set([path, *path.parent.glob("needs-kevin*.json"), *path.parent.glob("needs-kevin*.jsonl")]))
    items = joinable = 0
    for file in files:
        if file.stat().st_size > 16 * 1024 * 1024:
            continue
        try:
            with file.open() as f:
                documents = (json.loads(line) for line in f if line.strip()) if file.suffix == ".jsonl" else [json.load(f)]
                for doc in documents:
                    values = doc.get("items", []) if isinstance(doc, dict) else doc if isinstance(doc, list) else []
                    for value in values:
                        if isinstance(value, dict):
                            items += 1
                            joinable += bool(value.get("session_id") and timestamp(value.get("created_at")))
        except (ValueError, OSError):
            continue
    manifest.append({"source": "needs_owner", "files": len(files), "items": items, "potential_join_keys": joinable,
                     "status": "not_joined", "limitation": "Snapshots are not raised-during-run events; no identity/time inference from goal, worker, or prose."})


def relationships(rows, cutoff):
    rows.sort(key=lambda r: (r["start"], r["id"]))
    starts = sorted(r["start"] for r in rows)
    projects = defaultdict(list)
    for r in rows:
        t = r["start"]
        for minutes in (30, 60):
            r["features"][f"preceding_{minutes}"] = bisect_left(starts, t) - bisect_left(starts, t - minutes * 60)
        if r["project"]:
            projects[r["project"]].append(r)
        r["labels"]["restarted_not_resumed"] = None
        r["evening_cut_never_resumed"] = None
        r["group"] = r["id"]
    # Conservatively group project chains <=12h for fold purging. This can
    # overgroup unrelated tasks; never claim project equality proves same work.
    for group in projects.values():
        previous = None
        for r in group:
            if previous and r["start"] - previous["start"] <= RESTART_SECONDS:
                r["group"] = previous["group"]
            previous = r
        times = [r["start"] for r in group]
        for r in group:
            end = r["end"] or r["activity_end"]
            if end is None or end + RESTART_SECONDS > cutoff:
                continue
            i = bisect_left(times, end)
            stop = bisect_right(times, end + RESTART_SECONDS)
            candidates = [s for s in group[i:stop] if s["id"] != r["id"]]
            if candidates:
                s = candidates[0]
                if s["restart_observable"]:
                    r["labels"]["restarted_not_resumed"] = not s["features"]["mentions_resume"]
            elif r["restart_observable"]:
                r["labels"]["restarted_not_resumed"] = False
            end_hour = datetime.fromtimestamp(end, ZONE).hour
            if r["termination_failed"] and 17 <= end_hour < 23:
                r["evening_cut_never_resumed"] = not any(s["features"]["mentions_resume"] is True for s in candidates) if all(s["restart_observable"] for s in candidates) else None
    # Explicit parent chains also remain out of both train and test together.
    by_id = {r["id"]: r for r in rows}
    roots = {r["group"]: r["group"] for r in rows}
    def find(group):
        while roots[group] != group:
            roots[group] = roots[roots[group]]
            group = roots[group]
        return group
    for r in rows:
        parent = by_id.get(r["parent"])
        if parent:
            left, right = find(r["group"]), find(parent["group"])
            roots[max(left, right)] = min(left, right)
    for r in rows:
        r["group"] = find(r["group"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agentsview", type=Path)
    parser.add_argument("--hermes-root", type=Path, default=Path.home() / ".hermes")
    parser.add_argument("--kanban", type=Path)
    parser.add_argument("--needs-owner", type=Path, help="Explicit local snapshot path; never inferred from telemetry")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    out = private_directory(args.output)
    cutoff = datetime.now(timezone.utc).timestamp()
    rows, manifest, seen = [], [], {}
    av = args.agentsview
    if av is None:
        av = next((p for p in [Path.home() / ".agentsview/sessions.db", Path.home() / ".local/share/agentsview/sessions.db", Path.home() / ".config/agentsview/sessions.db"] if p.exists()), None)
    if av:
        extract_sessions(av, "agentsview", seen, rows, manifest, cutoff)
    else:
        manifest.append({"source": "agentsview", "status": "unavailable"})
    # Prefer AgentsView for mirrored sessions; no duplicate source-session IDs.
    paths = {p.resolve() for p in args.hermes_root.glob("profiles/*/state.db")}
    if (args.hermes_root / "state.db").exists():
        paths.add((args.hermes_root / "state.db").resolve())
    for path in sorted(paths):
        extract_sessions(path, "hermes", seen, rows, manifest, cutoff)
    kanban = args.kanban or args.hermes_root / "kanban.db"
    if kanban.exists():
        enrich_blocked(kanban, rows, manifest)
    inspect_needs_owner(args.needs_owner, manifest)
    for r in rows:
        parent = seen.get((r["_harness"], r["_parent_native"]))
        if parent:
            r["parent"] = parent["id"]
    relationships(rows, cutoff)
    for r in rows:
        for key in list(r):
            if key.startswith("_"):
                del r[key]
    # Stream serialization; no private prompts, titles, or source paths stored.
    data_path = out / "runs.jsonl"
    tmp = data_path.with_name("runs.jsonl.new")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    sha = hashlib.sha256()
    with os.fdopen(fd, "w") as f:
        for r in rows:
            line = json.dumps(r, sort_keys=True) + "\n"
            sha.update(line.encode())
            f.write(line)
    if data_path.is_symlink():
        raise ValueError("output file cannot be a symlink")
    os.replace(tmp, data_path)
    code_sha = subprocess.check_output(["git", "-C", str(Path(__file__).resolve().parents[2]), "rev-parse", "HEAD"], text=True).strip()
    receipt = {"provisional": PROVISIONAL, "cutoff": cutoff, "code_commit": code_sha,
               "extract_script_sha256": digest(Path(__file__).read_text()),
               "runs_sha256": sha.hexdigest(), "sources": manifest,
               "counts": {"all_runs": len(rows), "overnight": sum(r["overnight"] for r in rows)},
               "limits": ["Per-source read transactions, not one cross-database snapshot.",
                          "AgentsView end is last transcript activity, not process termination.",
                          "Success plus clean termination is source-reported completion, not independently verified success or proof of no owner intervention.",
                          "First prompt features require timestamp within 60 seconds of start; wrappers remain a confound.",
                          "Session model/provider fields are mutable: dispatch values unavailable and excluded.",
                          "is_automated is source metadata, not independently verified dispatch state.",
                          "Mutable outcome/termination availability is conservatively bounded by extraction read time, not backdated to exit.",
                          "Long conversations can span several nights; unit remains one session."]}
    private_write(out / "extraction.json", json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt["counts"]))


if __name__ == "__main__":
    main()
