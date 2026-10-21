#!/usr/bin/env python3
"""Analysis for harness-speed-v1 (rules fixed in protocol.md).

    python3 analyze.py DATA_DIR... --out ANALYSIS_DIR
"""
import argparse
import glob
import json
import math
import os
import random

B = 10_000
RNG_SEED = 7


def median(xs):
    s = sorted(xs)
    n = len(s)
    if not n:
        return None
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def pct(xs, p):
    s = sorted(xs)
    if not s:
        return None
    k = (len(s) - 1) * p
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def boot_median(xs, rng):
    if len(xs) < 2:
        return [None, None]
    ms = sorted(median([rng.choice(xs) for _ in xs]) for _ in range(B))
    return [ms[int(0.025 * B)], ms[int(0.975 * B) - 1]]


def boot_diff(a, b, rng):
    """CI of median(b) - median(a)."""
    if len(a) < 2 or len(b) < 2:
        return [None, None]
    ds = sorted(median([rng.choice(b) for _ in b]) - median([rng.choice(a) for _ in a]) for _ in range(B))
    return [ds[int(0.025 * B)], ds[int(0.975 * B) - 1]]


def boot_paired(diffs, rng):
    if len(diffs) < 2:
        return [None, None]
    ms = sorted(median([rng.choice(diffs) for _ in diffs]) for _ in range(B))
    return [ms[int(0.025 * B)], ms[int(0.975 * B) - 1]]


def mann_whitney(a, b):
    if not a or not b:
        return None
    allv = sorted([(v, 0) for v in a] + [(v, 1) for v in b])
    ranks = [0.0] * len(allv)
    i = 0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1][0] == allv[i][0]:
            j += 1
        for k in range(i, j + 1):
            ranks[k] = (i + j) / 2 + 1
        i = j + 1
    r1 = sum(r for r, (_v, g) in zip(ranks, allv) if g == 0)
    n1, n2 = len(a), len(b)
    u = r1 - n1 * (n1 + 1) / 2
    mu, sd = n1 * n2 / 2, math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    if sd == 0:
        return 1.0
    z = (u - mu) / sd
    return math.erfc(abs(z) / math.sqrt(2))


def wilson(k, n):
    if n == 0:
        return [None, None]
    z = 1.96
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [max(0, c - h), min(1, c + h)]


def load(dirs):
    rows = []
    for d in dirs:
        for f in glob.glob(os.path.join(d, "*.jsonl")):
            for line in open(f):
                if line.strip():
                    rows.append(json.loads(line))
    return rows


def arm_key(r):
    if "@" in r["arm"]:
        return r["arm"]
    m = r.get("model", "")
    tag = "" if m.endswith("gpt-6.1-sol") or not m else "@" + m.split("/")[-1]
    return r["arm"] + tag


CONTRASTS = [
    ("C1", "hermes-base", "fx-base"), ("C1", "hermes-base", "omp-base"), ("C1", "hermes-base", "pi-base"),
    ("C1", "fx-base", "omp-base"), ("C1", "fx-base", "pi-base"), ("C1", "omp-base", "pi-base"),
    ("C2", "hermes-base", "hermes-default"), ("C3", "omp-base", "omp-default"),
    ("C4", "pi-base", "pi-solpi"), ("C4", "pi-base", "pi-rlm"),
    ("C5", "omp-base", "omp-base@claude-opus-5-5"),
    ("X1", "pi-base", "pi-base-offline"), ("X2", "hermes-base", "hermes-base-clarify"),
]


def summarize(rows):
    rng = random.Random(RNG_SEED)
    out = {"latency": {}, "tasks": {}, "contrasts": []}
    lat = [r for r in rows if r.get("kind") == "latency" and r.get("phase") == "run"]
    tasks = [r for r in rows if r.get("kind") == "task"]
    groups = {}
    for r in lat:
        groups.setdefault((r["mode"], arm_key(r), r.get("session")), []).append(r)
    for (mode, arm, sess), rs in sorted(groups.items()):
        ok = [r for r in rs if r.get("correct") and r.get("ttft_ms") is not None]
        tt = [r["ttft_ms"] / 1000 for r in ok]
        tot = [r["total_ms"] / 1000 for r in ok]
        out["latency"][f"{mode}|{arm}|{sess}"] = {
            "mode": mode, "arm": arm, "session": sess, "n": len(rs), "correct": len(ok),
            "ttft_s": {"median": median(tt), "ci95": boot_median(tt, rng), "p90": pct(tt, 0.9)},
            "total_s": {"median": median(tot), "ci95": boot_median(tot, rng), "p90": pct(tot, 0.9)},
            "tool_call_rate": sum(1 for r in rs if (r.get("tool_calls") or 0) > 0) / len(rs),
            "input_tokens_median": median([(r.get("tokens") or {}).get("input_total", 0) for r in rs]),
            "_tt": tt, "_tot": tot,
            "_byblock": {r["block"]: (r["ttft_ms"] / 1000, r["total_ms"] / 1000) for r in ok},
        }
    tg = {}
    for r in tasks:
        tg.setdefault((arm_key(r), r.get("session")), []).append(r)
    for (arm, sess), rs in sorted(tg.items()):
        k = sum(1 for r in rs if r["verified"].get("pass"))
        wall = [r["total_ms"] / 1000 for r in rs]
        wall_pass = [r["total_ms"] / 1000 for r in rs if r["verified"].get("pass")]
        tin = [r["tokens"]["input_total"] for r in rs]
        tout = [r["tokens"]["output"] for r in rs]
        out["tasks"][f"{arm}|{sess}"] = {
            "arm": arm, "session": sess, "n": len(rs), "pass": k, "pass_rate": k / len(rs), "pass_ci95": wilson(k, len(rs)),
            "timeouts": sum(1 for r in rs if r.get("timed_out")), "tests_modified": sum(1 for r in rs if r["verified"].get("tests_modified")),
            "wall_s": {"median": median(wall), "ci95": boot_median(wall, rng), "p90": pct(wall, 0.9)},
            "wall_pass_s_median": median(wall_pass),
            "input_tokens": {"median": median(tin), "ci95": boot_median(tin, rng)},
            "output_tokens": {"median": median(tout), "ci95": boot_median(tout, rng)},
            "cache_read_share": (sum(r["tokens"]["cache_read"] for r in rs) / max(1, sum(tin))),
            "tool_calls_median": median([r["tool_calls"] for r in rs]),
            "model_requests_median": median([r["model_requests"] for r in rs]),
            "cost_est_usd_median": median([r["cost_est_usd"] for r in rs]),
            "cost_est_usd_total": sum(r["cost_est_usd"] for r in rs),
            "per_task_pass": {t: sum(1 for r in rs if r["task"] == t and r["verified"].get("pass")) for t in sorted({r["task"] for r in rs})},
            "_wall": wall,
            "_bycell": {(r["task"], r["rep"]): r["total_ms"] / 1000 for r in rs},
        }
    # contrasts: only within one session (pi is compared inside its own session)
    for cid, a, b in CONTRASTS:
        for mode in ("cold", "warm"):
            for sess in sorted({v["session"] for v in out["latency"].values()}):
                ka, kb = f"{mode}|{a}|{sess}", f"{mode}|{b}|{sess}"
                if ka in out["latency"] and kb in out["latency"]:
                    A, Bv = out["latency"][ka], out["latency"][kb]
                    for idx, (metric, key) in enumerate((("ttft_s", "_tt"), ("total_s", "_tot"))):
                        common = sorted(set(A["_byblock"]) & set(Bv["_byblock"]))
                        pd = [Bv["_byblock"][k][idx] - A["_byblock"][k][idx] for k in common]
                        out["contrasts"].append({
                            "paired_n": len(pd), "paired_median_diff": median(pd), "paired_ci95": boot_paired(pd, rng),
                            "id": cid, "workload": f"latency-{mode}", "session": sess, "metric": metric, "a": a, "b": b,
                            "median_a": A[metric]["median"], "median_b": Bv[metric]["median"],
                            "diff_b_minus_a": (Bv[metric]["median"] - A[metric]["median"]) if A[metric]["median"] is not None and Bv[metric]["median"] is not None else None,
                            "diff_ci95": boot_diff(A[key], Bv[key], rng), "mw_p": mann_whitney(A[key], Bv[key])})
        for sess in sorted({v["session"] for v in out["tasks"].values()}):
            ka, kb = f"{a}|{sess}", f"{b}|{sess}"
            if ka in out["tasks"] and kb in out["tasks"]:
                A, Bv = out["tasks"][ka], out["tasks"][kb]
                common = sorted(set(A["_bycell"]) & set(Bv["_bycell"]))
                pd = [Bv["_bycell"][k] - A["_bycell"][k] for k in common]
                out["contrasts"].append({
                    "paired_n": len(pd), "paired_median_diff": median(pd), "paired_ci95": boot_paired(pd, rng),
                    "id": cid, "workload": "tasks", "session": sess, "metric": "wall_s", "a": a, "b": b,
                    "median_a": A["wall_s"]["median"], "median_b": Bv["wall_s"]["median"],
                    "diff_b_minus_a": Bv["wall_s"]["median"] - A["wall_s"]["median"],
                    "diff_ci95": boot_diff(A["_wall"], Bv["_wall"], rng), "mw_p": mann_whitney(A["_wall"], Bv["_wall"]),
                    "pass_a": f'{A["pass"]}/{A["n"]}', "pass_b": f'{Bv["pass"]}/{Bv["n"]}'})
    for v in list(out["latency"].values()) + list(out["tasks"].values()):
        for k in [k for k in v if k.startswith("_")]:
            del v[k]
    return out


def f(x, d=2):
    return "-" if x is None else f"{x:.{d}f}"


def ci(c, d=2):
    return "-" if not c or c[0] is None else f"[{c[0]:.{d}f}, {c[1]:.{d}f}]"


def markdown(s):
    L = ["# harness-speed-v1 results", "", "Model gpt-6.1-sol (effort low) on every arm unless the arm name carries `@model`. Host MBP.",
         "Medians with bootstrap 95% CI of the median. Latency medians use correct requests only.",
         "Paired differences pair latency requests by interleaved block and task runs by (task, rep).", "",
         "## Latency", "", "| mode | arm | session | correct/n | TTFT s median [CI] | p90 | total s median [CI] | tool-call rate | input tok median |",
         "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for v in s["latency"].values():
        L.append(f'| {v["mode"]} | {v["arm"]} | {v["session"]} | {v["correct"]}/{v["n"]} | {f(v["ttft_s"]["median"])} {ci(v["ttft_s"]["ci95"])} | {f(v["ttft_s"]["p90"])} | '
                 f'{f(v["total_s"]["median"])} {ci(v["total_s"]["ci95"])} | {f(v["tool_call_rate"])} | {f(v["input_tokens_median"], 0)} |')
    L += ["", "## Coding tasks", "", "| arm | session | pass/n [Wilson CI] | timeouts | wall s median [CI] | wall s (passing) | in tok median | out tok median | cache-read share | tool calls | model requests | est. $/run |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for v in s["tasks"].values():
        L.append(f'| {v["arm"]} | {v["session"]} | {v["pass"]}/{v["n"]} {ci(v["pass_ci95"])} | {v["timeouts"]} | {f(v["wall_s"]["median"], 1)} {ci(v["wall_s"]["ci95"], 1)} | {f(v["wall_pass_s_median"], 1)} | '
                 f'{f(v["input_tokens"]["median"], 0)} | {f(v["output_tokens"]["median"], 0)} | {f(v["cache_read_share"])} | {f(v["tool_calls_median"], 1)} | {f(v["model_requests_median"], 1)} | {f(v["cost_est_usd_median"], 3)} |')
    L += ["", "## Planned contrasts (b minus a; called only if the CI excludes 0)", "",
          "| id | workload | metric | a | b | median a | median b | b-a | 95% CI | paired median diff [CI] (n) | MW p | pass a / b |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for c in s["contrasts"]:
        L.append(f'| {c["id"]} | {c["workload"]} ({c["session"]}) | {c["metric"]} | {c["a"]} | {c["b"]} | {f(c["median_a"])} | {f(c["median_b"])} | {f(c["diff_b_minus_a"])} | {ci(c["diff_ci95"])} | {f(c.get("paired_median_diff"))} {ci(c.get("paired_ci95"))} ({c.get("paired_n")}) | {f(c["mw_p"], 3)} | {c.get("pass_a", "")} {c.get("pass_b", "")} |')
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    s = summarize(load(a.dirs))
    json.dump(s, open(os.path.join(a.out, "summary.json"), "w"), indent=1)
    open(os.path.join(a.out, "summary.md"), "w").write(markdown(s))
    print(markdown(s))
