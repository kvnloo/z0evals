#!/usr/bin/env python3
"""Export public, screen-text-free data and summaries from the private z0live-control raws.

    python3 scripts/export.py PRIVATE_DIR OUT_DIR

PRIVATE_DIR holds the raw runs (never published: real phone screens contain mail subjects,
names and tab titles):
  s22-bench-v1.jsonl, s22-bench-v2.jsonl   on-device runs (tools/zer0/z0live-control-bench.py)
  tiers-v3.json                            groot + Jev on the synthetic labelled set
  laya-cuda.json, laya-cpu4.json           Laya on the same set (bench_laya_tier.py)
  heldout-s22.json, heldout-s22-v2.json    groot + Jev on real S22+ screens (v1, v2)
  phone-{smol360,qwen06,qwen17}.jsonl + phone-reqs/meta.json   on-phone llama.cpp runs

Published rows keep app, spoken goal, statuses, timings and the tapped control's label only
when it is a fixed UI control the bench asked for (expect_hint match); everything else is
dropped. The synthetic labelled set is public already (kvnloo/lawnchair
tools/zer0/fixtures/z0live-control-cases.json).
"""

import json
import math
import statistics
import sys
from pathlib import Path

LETTERS = "ABCDEFGHIJKLMNOP"
# Fixed app-chrome labels seen in the runs (no user content).
UI_CHROME = {"Menu", "Skip", "Close tab", "Customize and control Google Chrome"}


def q(values, p):
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    return round(values[min(len(values) - 1, int(round(p * (len(values) - 1))))], 1)


def safe_target(step):
    target = (step.get("do") or {}).get("target") or {}
    hint = step.get("expect_hint")
    label = target.get("label")
    if label and (label in UI_CHROME or (hint and hint.lower() in label.lower())):
        return label
    return "[redacted]" if label else None


def ondevice(private):
    rows = []
    for version in ("v1", "v2"):
        path = private / f"s22-bench-{version}.jsonl"
        if not path.exists():
            continue
        for line in path.open():
            r = json.loads(line)
            steps = r.get("steps") or [{"goal": r["goal"], "expect_hint": r.get("expect_hint"), "do": r["do"]}]
            out_steps = []
            for st in steps:
                d = st.get("do") or {}
                out_steps.append({
                    "goal": st["goal"], "status": d.get("status"), "landed": d.get("landed"),
                    "evidence": d.get("evidence"), "via": d.get("via"), "target": safe_target(st),
                    "reason": d.get("reason"), "decision": d.get("decision"), "ms": d.get("ms"),
                    "probe_ms": d.get("probe_ms"), "adb_wall_ms": d.get("adb_wall_ms"),
                    "candidates": len(d.get("candidates") or []),
                })
            rows.append({
                "run": version, "app": r["app"], "apk": "1e2ae05b2d" if version == "v1" else "1209e683e0",
                "tree_snapshot_ms": r.get("tree_snapshot_ms"), "tree_probe_ms": r.get("tree_probe_ms"),
                "tree_adb_wall_ms": r.get("tree_adb_wall_ms"),
                "tree_nodes": r.get("tree_nodes") or [len(((r.get("screen") or {}).get("nodes")) or [])],
                "u2_dump": r.get("u2_dump") or [], "steps": out_steps,
            })
    return rows


def latency_summary(rows):
    def warm(series):
        return [x for s in series for x in (s or [])[1:] if x is not None]

    def cold(series):
        return [s[0] for s in series if s and s[0] is not None]

    v2 = [r for r in rows if r["run"] == "v2"]
    snaps = [r["tree_snapshot_ms"] for r in v2]
    probes = [r["tree_probe_ms"] for r in v2]
    walls = [r["tree_adb_wall_ms"] for r in v2]
    u2 = [[d["ms"] for d in r["u2_dump"]] for r in v2 if r["u2_dump"]]
    acts = [st for r in rows for st in r["steps"] if st["status"] == "done" and isinstance(st.get("ms"), dict)]
    decide = [st["decision"]["ms"] for r in rows for st in r["steps"] if st.get("decision") and st["decision"].get("ms") is not None]
    statuses = {}
    for r in rows:
        for st in r["steps"]:
            statuses[st["status"]] = statuses.get(st["status"], 0) + 1
    return {
        "screens_v2": len(v2),
        "z0live_snapshot_ms": {"first_after_launch_p50": q(cold(snaps), .5), "first_after_launch_p95": q(cold(snaps), .95),
                               "warm_p50": q(warm(snaps), .5), "warm_p95": q(warm(snaps), .95)},
        "z0live_probe_ms_warm_p50": q(warm(probes), .5),
        "z0live_over_adb_broadcast_wall_ms_p50": q([x for s in walls for x in s or []], .5),
        "u2_dump_on_phone_ms": {"first_p50": q(cold(u2), .5), "warm_p50": q(warm(u2), .5), "warm_p95": q(warm(u2), .95)},
        "tier0_decide_ms": {"p50": q(decide, .5), "p95": q(decide, .95)},
        "act_ms": {"p50": q([a["ms"]["act"] for a in acts], .5), "p95": q([a["ms"]["act"] for a in acts], .95)},
        "confirm_ms": {"p50": q([a["ms"]["confirm"] for a in acts], .5), "p95": q([a["ms"]["confirm"] for a in acts], .95)},
        "do_total_ms": {"p50": q([a["ms"]["total"] for a in acts], .5), "p95": q([a["ms"]["total"] for a in acts], .95),
                        "n": len(acts)},
        "landed": sum(bool(a["landed"]) for a in acts), "statuses": statuses,
    }


def phone_slm(private):
    meta_path = private / "phone-reqs" / "meta.json"
    if not meta_path.exists():
        return []
    meta = {m["i"]: m for m in json.loads(meta_path.read_text())}
    out = []
    for name, label in (("phone-smol360.jsonl", "SmolLM2-360M Q8_0"), ("phone-qwen06.jsonl", "Qwen3-0.6B Q8_0"),
                        ("phone-qwen17.jsonl", "Qwen3-1.7B Q4_K_M")):
        path = private / name
        if not path.exists():
            continue
        rows = []
        for line in path.open():
            try:
                rows.append(json.loads(line))
            except ValueError:
                pass
        warm = [r for r in rows if r.get("pass") == 2]
        right = total = acted_right = acted_wrong = 0
        compute, full = [], []
        for r in warm:
            m = meta[int(r["file"][:2])]
            ch = r["resp"]["choices"][0]
            pick = ch["message"]["content"][:1]
            letters = LETTERS[: len(m["cands"])]
            probs = {}
            for t in ch["logprobs"]["content"][0]["top_logprobs"]:
                if t["token"] in letters:
                    probs[t["token"]] = probs.get(t["token"], 0) + math.exp(t["logprob"])
            conf = probs.get(pick, 0) / sum(probs.values()) if probs else 0
            pid = m["cands"][letters.index(pick)]["id"] if pick in letters else None
            if m["expect"]:
                total += 1
                right += pid == m["want"]
            if conf >= 0.95:
                if m["expect"] and pid == m["want"]:
                    acted_right += 1
                else:
                    acted_wrong += 1
            tm = r["resp"].get("timings", {})
            compute.append(tm.get("prompt_ms", 0) + tm.get("predicted_ms", 0))
        for r in rows:
            if r.get("pass") == 1:
                tm = r["resp"].get("timings", {})
                full.append(tm.get("prompt_ms", 0) + tm.get("predicted_ms", 0))
        out.append({"model": label, "device": "S22+ CPU (Snapdragon 8 Gen 1), llama.cpp, 4 threads",
                    "cases": len(warm), "top1": round(right / total, 3) if total else None,
                    "acted_right@0.95": acted_right, "acted_wrong@0.95": acted_wrong,
                    "warm_prefix_cached_ms_p50": q(compute, .5),
                    "full_prompt_ms_p50": q(full, .5), "full_prompt_ms_p95": q(full, .95)})
    return out


def main():
    private, out = Path(sys.argv[1]), Path(sys.argv[2])
    (out / "data").mkdir(parents=True, exist_ok=True)
    rows = ondevice(private)
    with (out / "data" / "ondevice-runs.jsonl").open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    summary = {"ondevice": latency_summary(rows), "phone_slm": phone_slm(private), "tiers_fixture": [], "heldout_s22": {}}
    tiers = json.loads((private / "tiers-v3.json").read_text())
    summary["tiers_fixture"] = tiers["tiers"]
    for name in ("laya-cuda.json", "laya-cpu4.json"):
        if (private / name).exists():
            summary["tiers_fixture"].append(json.loads((private / name).read_text())["summary"])
    (out / "data" / "tiers-fixture-rows.json").write_text(json.dumps(tiers["rows"], indent=1))
    held = {}
    for name in ("heldout-s22.json", "heldout-s22-v2.json"):
        if (private / name).exists():
            for tier, rs in json.loads((private / name).read_text()).items():
                tier = "groot:qwen3-4b-q4km" if tier == "groot" else tier
                for x in rs:
                    app, goal = (x["k"] if "k" in x else (x["app"], x["goal"]))
                    held.setdefault(tier, []).append({"set": name.split(".")[0], "app": app, "goal": goal,
                                                      "candidates": x.get("n"), "right": x["right"],
                                                      "conf": x["conf"], "acted": x["acted"], "ms": x["ms"]})
    (out / "data" / "heldout-s22.json").write_text(json.dumps(held, indent=1))
    for tier, rs in held.items():
        summary["heldout_s22"][tier] = {"cases": len(rs), "top1": sum(x["right"] for x in rs),
                                        "acted_right": sum(x["acted"] and x["right"] for x in rs),
                                        "acted_wrong": sum(x["acted"] and not x["right"] for x in rs),
                                        "ms_p50": q([x["ms"] for x in rs], .5)}
    (out / "data" / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
