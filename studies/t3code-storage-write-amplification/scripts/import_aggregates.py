#!/usr/bin/env python3
"""Import aggregate-only results of the T3 Code storage experiments into data/.

Usage: python3 scripts/import_aggregates.py <experiment-ops-dir>

The ops dir holds the raw experiment outputs (raw/<experiment>/...). This script
reads a fixed allowlist of files from it and writes only aggregates: byte totals
per class, medians, counts and bootstrap intervals. It drops every thread id,
title, message text, file path, host name and provider instance name. Provider
instances are folded into provider families before anything is written.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
OUT = HERE / "data"
MIB = 2**20

# provider driver -> public provider family; ACP instances are named by the user, so match on the agent
FAMILY = {
    "grok": "acp-other",
    "codex": "codex",
    "codex-import": "codex-import",
    "claudeAgent": "claude",
    "claude-import": "claude-import",
    "opencode": "opencode",
    "antigravity": "none",
    "none": "none",
}


def family(instance: str) -> str | None:
    if instance.startswith("acpRegistry/"):
        return "acp-hermes" if "hermes" in instance else "acp-other"
    return FAMILY.get(instance)


CLASSES = [
    "message-text", "reasoning-text", "tool-input", "tool-output", "duplicate",
    "t3-owned", "metadata", "fts", "index", "cell-overhead", "slack", "free",
]


def write(name: str, obj: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, indent=1, sort_keys=False) + "\n", encoding="utf-8")
    print(f"wrote data/{name}")


def accounting(ops: Path) -> None:
    a = json.loads((ops / "raw/01-accounting/accounting.json").read_text())
    dbs = {}
    for key, label in [("base", "base"), ("doctor", "doctor"), ("policyD", "D"), ("policyA", "A"), ("policyB", "B")]:
        d = a[key]
        t = a["durable"][key]["threadSummary"]
        dbs[label] = {
            "file_bytes": d["fileBytes"],
            "page_size": d["pageSize"],
            "bytes_by_class": {c: int(d["totals"].get(c, 0)) for c in CLASSES},
            "threads": {k: t[k] for k in ("count", "p50", "p90", "max")},
        }
        if "counts" in d:
            dbs[label]["tombstone_counts"] = d["counts"]
    fam: dict[str, dict[str, int]] = {}
    for inst, classes in a["doctor"]["bytesByProvider"].items():
        f = family(inst)
        if f is None:
            raise SystemExit(f"unmapped provider instance; add it to FAMILY before importing")
        bucket = fam.setdefault(f, {})
        for c, v in classes.items():
            bucket[c] = bucket.get(c, 0) + int(v)
    write("bytes-by-class.json", {
        "source": {"repo": "kvnloo/t3code", "branch": "exp/poh/01-byte-accounting", "commit": a["sha"]},
        "definitions": {
            "base": "seed after the measured build's migrations, VACUUMed",
            "doctor": "base after `t3 doctor --fix` (shipped compaction)",
            "D": "doctor + drop superseded snapshot bodies (no provider needed), tombstoned",
            "A": "D + evict tool output (keep all text)",
            "B": "provider owns every transcript byte",
        },
        "dbs": dbs,
        "doctor_bytes_by_provider_family": fam,
    })


def fold(ops: Path) -> None:
    s = json.loads((ops / "raw/02-dedupe-r3/seed-equivalence.json").read_text())
    out: dict[str, object] = {"source": {"repo": "kvnloo/t3code", "branch": "exp/poh/02-snapshot-dedupe", "commit_tests": "bb7fde1c"}}
    for arm in ("off", "on"):
        r = s[arm]
        out[arm] = {
            "compaction_deleted_events": r["compacted"]["deletedEventCount"],
            "folded": r["folded"],
            "fold_ms_unpaced": r["foldMillis"],
            "size": r["size"],
            "events": {k: r["events"][k] for k in ("rows", "payloadBytes")},
            "verification_valid": r["verification"]["valid"],
        }
    tables = s["tables"]
    out["projection_tables"] = len(tables)
    out["projection_tables_equal_on_off"] = sum(1 for t in tables.values() if t.get("onEqualsOff"))
    write("snapshot-fold-seed.json", out)


def page_size(ops: Path) -> None:
    rows = json.loads((ops / "raw/03b-page-writes/where-bytes.json").read_text())
    arms: dict[str, list[dict]] = {}
    for r in rows:
        arms.setdefault(r["run"].rsplit("-", 1)[-1], []).append(r)
    tap = {}
    for arm, rs in arms.items():
        med = lambda k: statistics.median(r[k] for r in rs)
        tap[arm] = {
            "turns": len(rs),
            "page_size": rs[0]["pageSize"],
            "commits_p50": med("commits"),
            "wal_frames_p50": med("frames"),
            "distinct_pages_p50": med("distinctPages"),
            "wal_bytes_p50": med("walBytes"),
            "copyback_bytes_p50": med("dbBytes"),
        }
    durable = {}
    ledger_tap: dict[str, dict[str, float]] = {}
    for arm in ("ps8k", "ps16k", "ps16kc", "ps16kj"):
        for line in (ops / f"raw/03b-page-writes/ab-ledger-{arm}.jsonl").read_text().splitlines():
            r = json.loads(line)
            who = "off" if r["flag"].endswith("=unset") else arm
            if r["metric"] == "durable.db_file.bytes":
                durable[who] = int(r["p50"])
            elif r["metric"].startswith("turn.sim.tap."):
                ledger_tap.setdefault(who, {})[r["metric"].removeprefix("turn.sim.tap.")] = r["p50"]
    write("page-size.json", {
        "source": {"repo": "kvnloo/t3code", "branch": "exp/poh/03b-page-writes", "commit_ab": "9b199744"},
        "note": "per-turn values are medians over tapped turns of the server process (write syscalls on the db and wal files); durable bytes are the doctor-compacted seed at each page size",
        "tap_per_turn": tap,
        "tap_ledger_p50": ledger_tap,
        "durable_file_bytes": durable,
    })


def group_commit(ops: Path) -> None:
    ab = json.loads((ops / "raw/04-commit-batching/ab-final.json").read_text())
    write("group-commit-ab.json", {
        "source": {"repo": "kvnloo/t3code", "branch": "exp/poh/04-commit-batching", "pooled_shas": ab["sha"]},
        "arms_meaning": {
            "off": "no flags",
            "w25": "T3CODE_EXPERIMENTAL_COMMIT_WINDOW_MS=25",
            "idx": "no flags; seed with the correlation index dropped and the command index partial",
            "w150": "150 ms window (pilot only, rejected)",
        },
        "note": "n is tapped turns per arm (2 per boot); p50/p95 over turns; deltaVsOff is the median shift with a bootstrap 95% interval",
        "arms": ab["arms"],
    })


def ledger(ops: Path) -> None:
    counts: dict[str, int] = {}
    for line in (ops / "ledger.jsonl").read_text().splitlines():
        if line.strip():
            e = json.loads(line)["experiment"].split(":")[0]
            counts[e] = counts.get(e, 0) + 1
    write("ledger-summary.json", {"rows": sum(counts.values()), "rows_by_experiment": dict(sorted(counts.items()))})


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    ops = Path(sys.argv[1])
    accounting(ops)
    fold(ops)
    page_size(ops)
    group_commit(ops)
    ledger(ops)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
