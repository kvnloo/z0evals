#!/usr/bin/env python3
"""Free-stack showcase. Phase 1 (menu): TTFT + decode tok/s for every free lane, providers in parallel,
serial within a provider. Phase 2 (orchestra): everything at once, each lane used by the pattern its TTFT suits:
  sprinters (TTFT < 0.6 s, >= 300 tok/s): fan-out of many small tasks (weighted by per-model RPM), drafts, bulk text
  checkers  (TTFT < 1 s, 60-300 tok/s): draft->check verdicts and hedged (raced) calls
  long thinkers (everything slower that answered): background long jobs
Usage: free_stack.py OUTDIR [menu.json]. Keys come from the environment (set -a; . ~/.config/free-stack/keys.env; set +a,
written by onboard.py). Lanes whose key is missing simply fail their probe. Prints no secrets."""
import json, os, random, ssl, sys, threading, time, urllib.request, urllib.error
import concurrent.futures as cf

OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
CTX = ssl.create_default_context()
P = {  # provider: (base, key env or None, min gap between calls in s, billing)
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY", 2.2, "free"),
    "cerebras": ("https://api.cerebras.ai/v1", "CEREBRAS_API_KEY", 0.2, "trial credit"),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", 3.5, "free"),
    "vercel": ("https://ai-gateway.vercel.sh/v1", "AI_GATEWAY_API_KEY", 1.0, "free credit"),
    "nim": ("https://integrate.api.nvidia.com/v1", "NVIDIA_API_KEY", 1.6, "free (dev program)"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai", "GEMINI_API_KEY", 4.5, "free (may train)"),
    "opencode": ("https://opencode.ai/zen/v1", None, 1.0, "free (keyless)"),
}
LANES = [
    ("groq", "openai/gpt-oss-20b", 30), ("groq", "openai/gpt-oss-120b", 30), ("groq", "qwen/qwen3.8-27b", 30),
    ("cerebras", "gpt-oss-120b", 1000), ("cerebras", "qwen-3.8-27b", 450),
    ("openrouter", "nvidia/nemotron-3.5-lightning:free", 20), ("openrouter", "nvidia/nemotron-3.5-super-vl:free", 20),
    ("openrouter", "nvidia/nemotron-3-ultra-550b-a55b:free", 20), ("openrouter", "dots-studio/dots-3-note-preview:free", 20),
    ("openrouter", "google/gemma-4-26b-a4b-it:free", 20), ("openrouter", "thinkingmachines/inkling-small:free", 20),
    ("openrouter", "cohere/north-mini-code:free", 20), ("openrouter", "xingchen-agi/xing4.0-29b-a4b:free", 20),
    ("vercel", "nvidia/nemotron-3.5-lightning-free", 60), ("vercel", "reflection/beam-free", 60),
    ("vercel", "inclusionai/ling-3.1-flash-1019", 60),
    ("nim", "nvidia/nemotron-3.5-lightning-30b-a3b", 40), ("nim", "nvidia/nemotron-3.5-super-vl-120b-a12b", 40),
    ("nim", "nvidia/nemotron-3-ultra-550b-a55b", 40), ("nim", "stepfun-ai/step-5-preview", 40),
    ("gemini", "gemini-3.5-flash-lite", 15),
    ("opencode", "deepseek-v4.1-flash-free", 20), ("opencode", "nemotron-3.5-lightning-free", 20),
]
SHORT = "Classify the sentiment of this review as positive, negative or neutral. Answer with one word. Review: {}"
REVIEWS = ["The battery died after two days.", "Absolutely love the screen.", "It arrived on Tuesday.",
           "Customer support never answered.", "Best purchase this year!", "The box was blue."]
LONG = "Write a 400-word plain-English explanation of how a hash map handles collisions. No code."
gaps = {p: threading.Lock() for p in P}; last = {p: 0.0 for p in P}
log_lock = threading.Lock()


def log(name, row):
    with log_lock, open(os.path.join(OUT, name), "a") as f:
        f.write(json.dumps(row) + "\n")


def call(prov, model, prompt, max_tokens, phase, tag, pace=True, timeout=120):
    base, env, gap, billing = P[prov]
    if pace:  # per-provider spacing so we stay inside free RPM
        with gaps[prov]:
            wait = last[prov] + gap - time.time()
            if wait > 0:
                time.sleep(wait)
            last[prov] = time.time()
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens,
            "stream": True, "stream_options": {"include_usage": True}, "temperature": 0}
    h = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 free-stack/1"}
    if env:
        h["Authorization"] = f"Bearer {os.environ.get(env, '')}"
    t0 = time.time(); first = lastt = None; usage = {}; text = ""; status = None; err = None
    try:
        req = urllib.request.Request(base + "/chat/completions", data=json.dumps(body).encode(), headers=h, method="POST")
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            status = r.status
            for line in r:
                line = line.decode(errors="replace").strip()
                if not line.startswith("data:") or line == "data: [DONE]":
                    continue
                try:
                    d = json.loads(line[5:])
                except ValueError:
                    continue
                usage = d.get("usage") or usage
                for c in d.get("choices") or []:
                    dl = c.get("delta") or {}
                    piece = (dl.get("content") or "") + (dl.get("reasoning") or dl.get("reasoning_content") or "")
                    if piece:
                        now = time.time(); first = first or now; lastt = now
                        text += dl.get("content") or ""
    except urllib.error.HTTPError as e:
        status, err = e.code, e.read()[:200].decode(errors="replace")
    except Exception as e:  # noqa: BLE001
        status, err = "error", str(e)[:200]
    t1 = time.time()
    ct = usage.get("completion_tokens")
    span = (lastt - first) if first and lastt and lastt > first else None
    row = {"phase": phase, "tag": tag, "provider": prov, "model": model, "billing": billing, "status": status,
           "ok": status == 200 and bool(first), "err": err, "t0": t0, "t1": t1,
           "ttft_s": round(first - t0, 3) if first else None, "total_s": round(t1 - t0, 3),
           "completion_tokens": ct, "decode_tok_s": round(ct / span, 1) if ct and span and ct > 20 else None,
           "answer": text.strip()[:600]}
    log(f"{phase}.jsonl", row)
    return row


def menu():
    by = {}
    for prov, model, rpm in LANES:
        by.setdefault(prov, []).append((model, rpm))

    def run_provider(prov):
        rows = []
        for model, rpm in by[prov]:
            s = call(prov, model, SHORT.format(REVIEWS[0]), 2048, "menu", "short")
            lg = call(prov, model, LONG, 1500, "menu", "long") if s["ok"] else None
            rows.append({"provider": prov, "model": model, "rpm": rpm, "billing": P[prov][3], "short": s, "long": lg})
            print(f"menu {prov:10} {model:42} ttft={s['ttft_s']} tok/s={lg and lg['decode_tok_s']} st={s['status']}", flush=True)
        return rows

    with cf.ThreadPoolExecutor(len(by)) as ex:
        res = [r for rows in ex.map(run_provider, by) for r in rows]
    json.dump(res, open(os.path.join(OUT, "menu.json"), "w"), indent=1)
    return res


def orchestra(menu_rows):
    ok = [r for r in menu_rows if r["short"]["ok"] and r["long"] and r["long"]["ok"]]
    def tps(r): return (r["long"] or {}).get("decode_tok_s") or 0
    # TTFT decides short-output work (verdicts, races); tok/s decides long-output work.
    fast = [r for r in ok if r["short"]["ttft_s"] < 0.6 and tps(r) >= 300]          # sprinters: fan-out, drafts, bulk
    medium = [r for r in ok if r not in fast and r["short"]["ttft_s"] < 1.0 and tps(r) >= 60]  # checkers: verdicts, races
    slow = [r for r in ok if r not in fast and r not in medium]                      # long thinkers: background
    plan = {"fast": [(r["provider"], r["model"]) for r in fast], "medium": [(r["provider"], r["model"]) for r in medium],
            "slow": [(r["provider"], r["model"]) for r in slow]}
    print("plan", json.dumps(plan), flush=True)
    jobs = []
    # 1) fan-out: 150 small tasks over fast lanes, weighted by RPM (keeps Groq near its 30/min)
    w = [r["rpm"] for r in fast]
    for i in range(150 if fast else 0):
        r = random.choices(fast, weights=w)[0]
        jobs.append(("fanout", r["provider"], r["model"], SHORT.format(REVIEWS[i % 6]) + f" (#{i})", 512, False))
    # 1b) bulk: 40 medium-length answers on sprinters. Cerebras-weighted: Groq free is 8K TPM per model.
    bw = [r["rpm"] * (0.15 if r["provider"] == "groq" else 1) for r in fast]
    for i in range(40 if fast else 0):
        r = random.choices(fast, weights=bw)[0]
        jobs.append(("bulk", r["provider"], r["model"], f"In about 250 words, explain topic #{i} of: " + ["TCP slow start", "B-trees", "CRDTs", "bloom filters", "Raft leader election", "LSM trees", "consistent hashing", "vector clocks"][i % 8], 1500, False))
    # 4) background: one long job per slow lane
    for r in slow:
        jobs.append(("background", r["provider"], r["model"], LONG, 1500, True))
    t0 = time.time(); rows = []

    def draft_check(i):  # 2) fast lane drafts, a medium lane checks
        d = random.choice(fast) if fast else None
        if not d:
            return []
        a = call(d["provider"], d["model"], f"In 120 words, explain why a hash map lookup is O(1) on average. Variant {i}.", 2048, "orchestra", "draft", pace=False)
        out = [a]
        if medium and a["ok"]:
            c = medium[i % len(medium)]
            out.append(call(c["provider"], c["model"], "Check this explanation for factual errors. Reply PASS or FAIL then one sentence.\n\n" + a["answer"], 2048, "orchestra", "check"))
        return out

    def hedge(i):  # 3) race two medium lanes from different providers, keep the first good answer
        pool = sorted(medium, key=lambda r: r["short"]["ttft_s"])
        if len(pool) < 2:
            return []
        a = pool[i % len(pool)]
        b = next((x for x in pool if x["provider"] != a["provider"]), pool[(i + 1) % len(pool)])
        time.sleep(i * 1.5)  # spread races instead of pacing inside them; both legs start together
        ts = time.time()
        with cf.ThreadPoolExecutor(2) as ex:
            fa = ex.submit(call, a["provider"], a["model"], SHORT.format(REVIEWS[i % 6]), 2048, "orchestra", "hedge", False)
            fb = ex.submit(call, b["provider"], b["model"], SHORT.format(REVIEWS[i % 6]), 2048, "orchestra", "hedge", False)
            ra, rb = fa.result(), fb.result()
        good = [x for x in (ra, rb) if x["ok"]]
        win = min(good, key=lambda x: x["t1"]) if good else None
        log("hedge.jsonl", {"i": i, "a": [ra["model"], ra["total_s"], ra["ok"]], "b": [rb["model"], rb["total_s"], rb["ok"]],
                            "winner_s": win and round(win["t1"] - ts, 3), "both_done_s": round(max(ra["t1"], rb["t1"]) - ts, 3)})
        return [ra, rb]

    with cf.ThreadPoolExecutor(64) as ex:
        futs = [ex.submit(call, p, m, pr, mt, "orchestra", tag, pace) for tag, p, m, pr, mt, pace in jobs]
        futs += [ex.submit(draft_check, i) for i in range(8)]
        futs += [ex.submit(hedge, i) for i in range(6)]
        for f in futs:
            r = f.result(); rows += r if isinstance(r, list) else [r]
    wall = time.time() - t0
    okr = [r for r in rows if r["ok"]]
    toks = sum(r["completion_tokens"] or 0 for r in okr)
    by_tag = {}
    for r in rows:
        t = by_tag.setdefault(r["tag"], {"calls": 0, "ok": 0, "tokens": 0, "lanes": set(), "t0": r["t0"], "t1": r["t1"]})
        t["t0"] = min(t["t0"], r["t0"]); t["t1"] = max(t["t1"], r["t1"])
        t["calls"] += 1; t["ok"] += r["ok"]; t["tokens"] += (r["completion_tokens"] or 0) if r["ok"] else 0
        t["lanes"].add(r["provider"] + "/" + r["model"])
    fan = [r for r in okr if r["tag"] == "fanout"]
    fan_wall = (max(r["t1"] for r in fan) - min(r["t0"] for r in fan)) if fan else None
    summary = {"wall_s": round(wall, 2), "calls": len(rows), "ok": len(okr), "completion_tokens": toks,
               "aggregate_tok_s": round(toks / wall, 1), "providers_used": sorted({r["provider"] for r in okr}),
               "lanes_used": len({r["provider"] + "/" + r["model"] for r in okr}),
               "fanout": {"n": len(fan), "wall_s": fan_wall and round(fan_wall, 2),
                          "tokens": sum(r["completion_tokens"] or 0 for r in fan),
                          "tok_s": fan_wall and round(sum(r["completion_tokens"] or 0 for r in fan) / fan_wall, 1),
                          "serial_estimate_s": round(sum(r["total_s"] for r in fan), 1)},
               "by_tag": {k: {"calls": v["calls"], "ok": v["ok"], "tokens": v["tokens"], "lanes": len(v["lanes"]),
                              "wall_s": round(v["t1"] - v["t0"], 2), "tok_s": round(v["tokens"] / max(v["t1"] - v["t0"], 1e-3), 1)}
                          for k, v in by_tag.items()}, "plan": plan}
    json.dump(summary, open(os.path.join(OUT, "orchestra-summary.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1), flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 2:  # reuse an existing menu.json instead of re-measuring
        orchestra(json.load(open(sys.argv[2])))
    else:
        m = menu()
        time.sleep(61)  # let per-minute buckets refill before the all-at-once run
        orchestra(m)
