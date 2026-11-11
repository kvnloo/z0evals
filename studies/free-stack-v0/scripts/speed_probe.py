#!/usr/bin/env python3
"""Per-model speed probe: TTFT and decode tok/s, streaming, serial, one shared SSL context.
TTFT = request start -> first content OR reasoning delta. Decode tok/s = completion_tokens / (last chunk - first chunk).
Usage: speed_probe.py REPS OUT.jsonl  (keys from env; prints no secrets)"""
import json, os, ssl, sys, time, urllib.request

CTX = ssl.create_default_context()
REPS, OUT = int(sys.argv[1]), sys.argv[2]
MODELS = [
    ("groq", "https://api.groq.com/openai/v1", "GROQ_API_KEY", "openai/gpt-oss-20b"),
    ("groq", "https://api.groq.com/openai/v1", "GROQ_API_KEY", "openai/gpt-oss-120b"),
    ("groq", "https://api.groq.com/openai/v1", "GROQ_API_KEY", "qwen/qwen3.8-27b"),
    ("cerebras", "https://api.cerebras.ai/v1", "CEREBRAS_API_KEY", "gpt-oss-120b"),
    ("cerebras", "https://api.cerebras.ai/v1", "CEREBRAS_API_KEY", "qwen-3.8-27b"),
]
PROMPTS = {
    "short": "Classify the sentiment of this review as positive, negative or neutral. One word. Review: The battery died after two days.",
    "long": "Write a 400-word plain-English explanation of how a hash map handles collisions. No code.",
}


def one(prov, base, env, model, kind):
    body = {"model": model, "messages": [{"role": "user", "content": PROMPTS[kind]}],
            "max_tokens": 1200, "stream": True, "stream_options": {"include_usage": True}, "temperature": 0}
    req = urllib.request.Request(base + "/chat/completions", data=json.dumps(body).encode(), method="POST", headers={
        "Authorization": f"Bearer {os.environ[env]}", "Content-Type": "application/json", "User-Agent": "speed-probe/1"})
    t0 = time.perf_counter(); first = last = None; usage = {}; status = None; err = None
    try:
        with urllib.request.urlopen(req, timeout=90, context=CTX) as r:
            status = r.status
            for line in r:
                line = line.decode().strip()
                if not line.startswith("data:") or line == "data: [DONE]":
                    continue
                d = json.loads(line[5:])
                if d.get("usage"):
                    usage = d["usage"]
                for c in d.get("choices") or []:
                    delta = c.get("delta") or {}
                    if delta.get("content") or delta.get("reasoning") or delta.get("reasoning_content"):
                        now = time.perf_counter(); first = first or now; last = now
    except urllib.error.HTTPError as e:
        status, err = e.code, e.read()[:160].decode(errors="replace")
    except Exception as e:  # noqa: BLE001
        status, err = "error", str(e)[:160]
    total = time.perf_counter() - t0
    ct = usage.get("completion_tokens")
    span = (last - first) if first and last and last > first else None
    return {"provider": prov, "model": model, "kind": kind, "status": status, "err": err,
            "ttft_s": round(first - t0, 3) if first else None, "total_s": round(total, 3),
            "completion_tokens": ct, "decode_tok_s": round(ct / span, 1) if ct and span else None,
            "e2e_tok_s": round(ct / total, 1) if ct else None, "at": time.time()}


with open(OUT, "a") as f:
    for rep in range(REPS):
        for m in MODELS:
            for kind in PROMPTS:
                row = one(*m, kind); row["rep"] = rep
                f.write(json.dumps(row) + "\n"); f.flush()
                print(row["provider"], row["model"], kind, row["status"], row["ttft_s"], row["decode_tok_s"], row["completion_tokens"], flush=True)
                time.sleep(2.5)  # stay well under Groq free 30 RPM per model
