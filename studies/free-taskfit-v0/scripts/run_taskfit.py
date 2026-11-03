#!/usr/bin/env python3
"""Run the frozen free task-fit battery against free model lanes.

The battery is `frozen/tasks.py` (20 deterministic, auto-graded, non-code tasks
in 6 families), copied byte-for-byte from kvnloo/z0intelligence
deploy/vllm-sr/profiles/tasks.py @ f12b926e and pinned by sha256 in
manifest.yaml. Call semantics match that repo's eval_free.py (streaming,
temperature 0, max_tokens 4096, one worker per model, per-provider gap) so the
rows stay comparable, with one difference that matters for certification: each
row keeps the FULL answer text, so certify.py can re-grade every row with the
frozen graders instead of trusting the runner's own `correct` flag.

Free lanes only. Cerebras (trial credit) and the Gemini API (owner rule: never
direct) are refused. OpenRouter calls carry max_price 0 and no fallbacks.

Run under dsh-env-exec so keys never touch argv or logs:
  dsh-env-exec.py --allow GROQ_API_KEY --allow NVIDIA_API_KEY --allow OPENROUTER_API_KEY -- \
    python3 run_taskfit.py --out ../data/runs/<run-id>/rows.jsonl --repeats 2 \
    --only groq/openai/gpt-oss-20b,openrouter/nvidia/nemotron-3.5-super-vl:free
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import ssl
import sys
import threading
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent / "frozen" / "tasks.py"
sys.path.insert(0, str(FROZEN.parent))
from tasks import TASKS  # noqa: E402

CTX = ssl.create_default_context()
BASES = {
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY", 2.5),
    "nvidia": ("https://integrate.api.nvidia.com/v1", "NVIDIA_API_KEY", 2.0),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", 4.0),
}
REFUSED = {"cerebras": "trial credit, not free", "gemini": "owner rule: Gemini only via agy CLI, never direct API"}
LOCK = threading.Lock()


def task_set_sha256() -> str:
    return hashlib.sha256(FROZEN.read_bytes()).hexdigest()


def call(provider: str, model: str, prompt: str, timeout: int = 180) -> dict:
    base, env, _ = BASES[provider]
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": True,
            "max_tokens": 4096, "temperature": 0, "stream_options": {"include_usage": True}}
    if provider == "openrouter":
        body["provider"] = {"max_price": {"prompt": 0, "completion": 0, "request": 0}, "allow_fallbacks": False}
    req = urllib.request.Request(base + "/chat/completions", data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {os.environ.get(env, 'none')}",
                                          "Content-Type": "application/json", "User-Agent": "z0evals-free-taskfit/1"})
    t0 = time.time(); ttft = None; text = []; reasoning_chars = 0; usage = None
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        for raw in r:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                ev = json.loads(data)
            except ValueError:
                continue
            usage = ev.get("usage") or (ev.get("x_groq") or {}).get("usage") or usage
            for ch in ev.get("choices") or []:
                d = ch.get("delta") or {}
                piece = d.get("content") or ""
                rpiece = d.get("reasoning") or d.get("reasoning_content") or ""
                if (piece or rpiece) and ttft is None:
                    ttft = time.time() - t0
                text.append(piece); reasoning_chars += len(rpiece)
    return {"ttft_s": ttft, "total_s": time.time() - t0, "text": "".join(text),
            "reasoning_chars": reasoning_chars, "usage": usage}


def worker(spec: str, repeats: int, out: Path, done: set, meta: dict) -> None:
    provider, model = spec.split("/", 1)
    gap = BASES[provider][2]
    for rep in range(repeats):
        for task in TASKS:
            if (spec, task["id"], rep) in done:
                continue
            row = {"model": spec, "provider": provider, "task": task["id"], "family": task["family"], "rep": rep,
                   "at": time.time(), **meta}
            try:
                r = call(provider, model, task["prompt"])
                row.update({k: r[k] for k in ("ttft_s", "total_s", "reasoning_chars", "usage", "text")})
                row["out_chars"] = len(r["text"])
                row["ok"] = bool(r["text"].strip())
                try:
                    row["correct"] = bool(task["grade"](r["text"]))
                except Exception:
                    row["correct"] = False
            except Exception as e:  # a failed call is a wrong answer for a router
                code = getattr(e, "code", None)
                row.update({"ok": False, "correct": False, "error": f"{type(e).__name__} {code or ''} {str(e)[:120]}"})
                if code == 429:
                    time.sleep(gap * 6)
            with LOCK, out.open("a") as f:
                f.write(json.dumps(row) + "\n")
            time.sleep(gap)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--only", required=True, help="comma list of provider/model")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    specs = [s for s in a.only.split(",") if s]
    for spec in specs:
        provider = spec.split("/", 1)[0]
        if provider in REFUSED:
            ap.error(f"{spec}: refused ({REFUSED[provider]})")
        if provider not in BASES:
            ap.error(f"{spec}: unknown provider")
        if provider == "openrouter" and not spec.endswith(":free"):
            ap.error(f"{spec}: OpenRouter lanes must be :free models")
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        for line in out.open():
            r = json.loads(line)
            if r.get("ok") or "429" not in (r.get("error") or ""):
                done.add((r["model"], r["task"], r["rep"]))
    meta = {"task_set_sha256": task_set_sha256(), "runner": "z0evals/studies/free-taskfit-v0/scripts/run_taskfit.py"}
    threads = [threading.Thread(target=worker, args=(s, a.repeats, out, done, meta)) for s in specs]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
