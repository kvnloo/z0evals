#!/usr/bin/env python3
"""Derive every number the post cites from data/, draw the two figures, and splice them into the post.

Usage: python3 scripts/figures.py            # write data/derived.json, figures/*.svg, update the post
       python3 scripts/figures.py --check    # fail if any of those would change

Reads only the committed aggregates in data/ (written by import_aggregates.py).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
DATA = HERE / "data"
FIG = HERE / "figures"
POST = HERE.parents[1] / "posts" / "t3code-storage-write-amplification.md"
MIB = 2**20

GROUPS = [  # (label, classes, fill)
    ("text (messages, reasoning, tool input)", ["message-text", "reasoning-text", "tool-input"], "#98cf8b"),
    ("tool output", ["tool-output"], "#7fb2d9"),
    ("superseded snapshot bodies", ["duplicate"], "#e37f65"),
    ("t3-owned state", ["t3-owned"], "#c9a0dc"),
    ("ids and metadata", ["metadata", "cell-overhead"], "#d7b986"),
    ("indexes (incl. search)", ["index", "fts"], "#8a8577"),
    ("page slack", ["slack", "free"], "#4a4740"),
]
DB_LABELS = [("base", "after migrations"), ("doctor", "t3 doctor --fix"), ("D", "drop superseded"),
             ("A", "evict tool output"), ("B", "provider owns all")]


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text())


def mib(b: float) -> float:
    return round(b / MIB, 1)


def derive() -> dict:
    acc, fold, ps, gc, led = (load(n) for n in (
        "bytes-by-class.json", "snapshot-fold-seed.json", "page-size.json", "group-commit-ab.json", "ledger-summary.json"))
    dbs = acc["dbs"]
    doc = dbs["doctor"]["file_bytes"]
    out: dict = {"bytes": {}, "fold": {}, "page_size": {}, "group_commit": {}, "ledger_rows": led["rows"]}
    for key, _ in DB_LABELS:
        d = dbs[key]
        groups = {g: mib(sum(d["bytes_by_class"][c] for c in cs)) for g, cs, _ in GROUPS}
        out["bytes"][key] = {
            "file_mib": mib(d["file_bytes"]),
            "vs_doctor_pct": round(100 * (d["file_bytes"] - doc) / doc, 1),
            "thread_p50_mib": round(d["threads"]["p50"] / MIB, 2),
            "thread_max_mib": mib(d["threads"]["max"]),
            "groups_mib": groups,
        }
    b = dbs["B"]["bytes_by_class"]
    floor = b["metadata"] + b["index"] + b["slack"]
    out["bytes"]["B_floor_share_pct"] = round(100 * floor / dbs["B"]["file_bytes"], 0)
    tool = dbs["doctor"]["bytes_by_class"]["tool-output"]
    out["bytes"]["tool_output_mib"] = mib(tool)
    out["bytes"]["tool_output_pct_of_doctor"] = round(100 * tool / doc, 1)
    a_saving = dbs["D"]["file_bytes"] - dbs["A"]["file_bytes"]
    out["bytes"]["evict_tool_output_saving_mib"] = mib(a_saving)
    out["bytes"]["evict_tool_output_saving_pct_of_doctor"] = round(100 * a_saving / doc, 1)
    out["bytes"]["D_saving_mib"] = mib(doc - dbs["D"]["file_bytes"])
    out["bytes"]["A_saving_mib"] = mib(doc - dbs["A"]["file_bytes"])
    fam = acc["doctor_bytes_by_provider_family"]
    out["bytes"]["tool_output_by_family_mib"] = {f: mib(v.get("tool-output", 0)) for f, v in fam.items() if v.get("tool-output")}

    off, on = fold["off"], fold["on"]
    out["fold"] = {
        "vacuumed_off_mib": mib(off["size"]["vacuumedBytes"]),
        "vacuumed_on_mib": mib(on["size"]["vacuumedBytes"]),
        "vacuumed_saving_pct": round(100 * (on["size"]["vacuumedBytes"] - off["size"]["vacuumedBytes"]) / off["size"]["vacuumedBytes"], 1),
        "in_place_file_delta_bytes": on["size"]["inPlaceFileBytes"] - off["size"]["inPlaceFileBytes"],
        "in_place_used_delta_mb": round((on["size"]["inPlaceUsedBytes"] - off["size"]["inPlaceUsedBytes"]) / 1e6, 1),
        "events_off": off["events"]["rows"], "events_on": on["events"]["rows"],
        "folded_entities": on["folded"]["foldedEntityCount"],
        "transactions": on["folded"]["transactionCount"],
        "longest_txn_ms": round(on["folded"]["longestTransactionMillis"], 1),
        "tables_equal": f'{fold["projection_tables_equal_on_off"]}/{fold["projection_tables"]}',
    }

    tap, dur, lt = ps["tap_per_turn"], ps["durable_file_bytes"], ps["tap_ledger_p50"]
    for arm in ("off", "ps8k", "ps16k"):
        t = tap[arm]
        total = lt[arm]["sqlite_total.bytes"]
        out["page_size"][arm] = {
            "page_kib": t["page_size"] // 1024,
            "durable_mib": mib(dur[arm]),
            "durable_vs_4k_pct": round(100 * (dur[arm] - dur["off"]) / dur["off"], 1),
            "commits": t["commits_p50"],
            "wal_frames": t["wal_frames_p50"],
            "frames_per_commit": round(t["wal_frames_p50"] / t["commits_p50"]),
            "distinct_pages": t["distinct_pages_p50"],
            "wal_mib": round(t["wal_bytes_p50"] / MIB, 2),
            "copyback_mib": round(t["copyback_bytes_p50"] / MIB, 2),
            "sqlite_mib_per_turn": mib(total),
            "wal_share_pct": round(100 * t["wal_bytes_p50"] / (t["wal_bytes_p50"] + t["copyback_bytes_p50"])),
        }
    for arm in ("ps8k", "ps16k"):
        out["page_size"][arm]["writes_x"] = round(lt[arm]["sqlite_total.bytes"] / lt["off"]["sqlite_total.bytes"], 2)

    arms = gc["arms"]
    rows = {}
    for m, scale in [("sqliteBytes", MIB), ("commits", 1), ("frames", 1), ("liveFrames", 1), ("firstEventMs", 1),
                     ("firstAssistantMs", 1), ("lagP50Ms", 1), ("lagP95Ms", 1), ("frameGapP50Ms", 1),
                     ("assistantGapP50Ms", 1), ("turnMs", 1), ("peakRssMiB", 1), ("cpuS", 1), ("replayWsBytes", 1024)]:
        r = {"off": [arms["off"][m]["p50"] / scale, arms["off"][m]["p95"] / scale], "n_turns": {a: arms[a][m]["n"] for a in arms}}
        for a in ("w25", "idx", "w150"):
            x = arms[a][m]
            d = x["deltaVsOff"]
            r[a] = [x["p50"] / scale, x["p95"] / scale]
            r[a + "_delta"] = [d["p50"] / scale, d["ci95"][0] / scale, d["ci95"][1] / scale]
        rows[m] = {k: ([round(v, 2) for v in val] if isinstance(val, list) else val) for k, val in r.items()}
    out["group_commit"] = rows
    for m in ("commits", "frames", "sqliteBytes"):
        out["group_commit"][m]["w25_pct"] = round(100 * arms["w25"][m]["deltaVsOff"]["p50"] / arms["off"][m]["p50"], 1)
    return out


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg_bytes(d: dict) -> str:
    W, left, right, top, row, gap = 420, 96, 410, 8, 22, 12
    scale = (right - left) / d["bytes"]["base"]["file_mib"]
    parts = []
    y = top
    for key, sub in DB_LABELS:
        x = left
        b = d["bytes"][key]
        for (g, _, fill) in GROUPS:
            w = b["groups_mib"][g] * scale
            if w > 0:
                parts.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{row}" fill="{fill}"><title>{esc(g)}: {b["groups_mib"][g]} MiB</title></rect>')
            x += w
        parts.append(f'<text x="0" y="{y + 9}" font-size="10" fill="#ECE8DF">{key} · {b["file_mib"]:.0f} MiB</text>')
        parts.append(f'<text x="0" y="{y + 20}" font-size="8.5" fill="#B4AFA3">{esc(sub)}</text>')
        y += row + gap
    ly = y + 4
    for i, (g, _, fill) in enumerate(GROUPS):
        cx = 0 if i % 2 == 0 else 212
        cy = ly + (i // 2) * 15
        parts.append(f'<rect x="{cx}" y="{cy}" width="9" height="9" fill="{fill}"/>')
        parts.append(f'<text x="{cx + 13}" y="{cy + 8}" font-size="9" fill="#B4AFA3">{esc(g)}</text>')
    H = ly + 4 * 15
    return (f'<svg class="chart-svg" viewBox="0 0 {W} {H}" role="img" aria-label="durable bytes by class for five database states">'
            + "".join(parts) + "</svg>")


def svg_group_commit(d: dict) -> str:
    gc = d["group_commit"]
    rows = [("commits per turn", "commits", "{:.1f}"), ("wal frames per turn", "frames", "{:.0f}"),
            ("sqlite MiB per turn", "sqliteBytes", "{:.2f}"), ("live ws frames per turn", "liveFrames", "{:.0f}")]
    W, left, right, top = 420, 0, 330, 4
    span = right - left
    parts = []
    y = top
    for label, m, fmt in rows:
        r = gc[m]
        off, w25 = r["off"][0], r["w25"][0]
        lo, hi = (off + r["w25_delta"][1]) / off, (off + r["w25_delta"][2]) / off
        parts.append(f'<text x="0" y="{y + 9}" font-size="10" fill="#ECE8DF">{label}</text>')
        y += 13
        parts.append(f'<rect x="{left}" y="{y}" width="{span}" height="9" fill="#8a8577"/>')
        parts.append(f'<text x="{right + 6}" y="{y + 8}" font-size="9" fill="#B4AFA3">off {fmt.format(off)}</text>')
        y += 11
        ww = span * w25 / off
        parts.append(f'<rect x="{left}" y="{y}" width="{ww:.1f}" height="9" fill="#d7b986"/>')
        parts.append(f'<line x1="{left + span * lo:.1f}" x2="{left + span * hi:.1f}" y1="{y + 4.5}" y2="{y + 4.5}" stroke="#ECE8DF" stroke-width="1.2"/>')
        parts.append(f'<text x="{right + 6}" y="{y + 8}" font-size="9" fill="#d7b986">25 ms {fmt.format(w25)}</text>')
        y += 20
    parts.append(f'<text x="0" y="{y + 6}" font-size="8.5" fill="#B4AFA3">bars are p50 per tapped turn (n = 16 per arm), scaled to off; whisker = bootstrap 95% ci of the shift</text>')
    H = y + 12
    return (f'<svg class="chart-svg" viewBox="0 0 {W} {H}" role="img" aria-label="per-turn writes with and without a 25 ms group-commit window">'
            + "".join(parts) + "</svg>")


def splice(text: str, name: str, svg: str) -> str:
    pat = re.compile(rf"(<!-- figure:{name} -->\n)(.*?)(\n<!-- /figure:{name} -->)", re.S)
    if not pat.search(text):
        raise SystemExit(f"post has no figure:{name} block")
    return pat.sub(lambda m: m.group(1) + svg + m.group(3), text)


def main() -> int:
    check = "--check" in sys.argv
    d = derive()
    outputs = {
        DATA / "derived.json": json.dumps(d, indent=1) + "\n",
        FIG / "bytes-by-class.svg": svg_bytes(d) + "\n",
        FIG / "group-commit.svg": svg_group_commit(d) + "\n",
    }
    if POST.exists():
        post = POST.read_text(encoding="utf-8")
        post = splice(post, "bytes-by-class", svg_bytes(d))
        post = splice(post, "group-commit", svg_group_commit(d))
        outputs[POST] = post
    stale = [p for p, c in outputs.items() if not p.exists() or p.read_text(encoding="utf-8") != c]
    if check:
        for p in stale:
            print(f"stale: {p.relative_to(HERE.parents[1])}")
        return 1 if stale else 0
    FIG.mkdir(exist_ok=True)
    for p in stale:
        p.write_text(outputs[p], encoding="utf-8")
        print(f"wrote {p.relative_to(HERE.parents[1])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
