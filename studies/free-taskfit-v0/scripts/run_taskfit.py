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

Nothing is sent before plan_taskfit.plan() has checked it against
../frozen/limits.json: a (task, lane) whose estimated request (len/3.5 +
max_tokens) exceeds the lane's TPM, context or max request size is written as
`not_eligible:<reason>` and never sent; (lane, family) pairs already measured
in an unexpired committed receipt are skipped unless --force. A daily-quota
429 stops that lane; a 413 stops it too, because it means limits.json is wrong.

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
import re
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent / "frozen" / "tasks.py"
sys.path.insert(0, str(FROZEN.parent))
from tasks import TASKS  # noqa: E402

sys.path.insert(0, str(HERE))
import plan_taskfit as planner  # noqa: E402

CTX = ssl.create_default_context()
BASES = {
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY", 2.5),
    "nvidia": ("https://integrate.api.nvidia.com/v1", "NVIDIA_API_KEY", 2.0),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", 4.0),
}
REFUSED = {"cerebras": "trial credit, not free", "gemini": "owner rule: Gemini only via agy CLI, never direct API"}
LOCK = threading.Lock()
# Groq/Cloudflare 403s non-browser agents such as Python-urllib.
USER_AGENT = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36 "
              "z0evals-free-taskfit/2")
ORG_ID = re.compile(r"org_[A-Za-z0-9]+")


def task_set_sha256() -> str:
    return hashlib.sha256(FROZEN.read_bytes()).hexdigest()


class CallError(Exception):
    def __init__(self, code: int | None, body: str):
        super().__init__(f"HTTP {code}: {body}")
        self.code = code
        self.body = body


def call(provider: str, model: str, prompt: str, max_tokens: int, timeout: int = 180) -> dict:
    base, env, _ = BASES[provider]
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": True,
            "max_tokens": max_tokens, "temperature": 0, "stream_options": {"include_usage": True}}
    if provider == "openrouter":
        body["provider"] = {"max_price": {"prompt": 0, "completion": 0, "request": 0}, "allow_fallbacks": False}
    req = urllib.request.Request(base + "/chat/completions", data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {os.environ.get(env, 'none')}",
                                          "Content-Type": "application/json", "User-Agent": USER_AGENT})
    t0 = time.time(); ttft = None; text = []; reasoning_chars = 0; usage = None
    try:
        r = urllib.request.urlopen(req, timeout=timeout, context=CTX)
    except urllib.error.HTTPError as e:  # keep a short, redacted body: it says which limit fired
        raise CallError(e.code, ORG_ID.sub("org_<redacted>", e.read()[:300].decode("utf-8", "replace"))) from None
    with r:
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


def worker(spec: str, items: list[dict], out: Path, meta: dict, limits: dict) -> None:
    provider, model = spec.split("/", 1)
    entry = limits["lanes"][spec]
    gap = max(BASES[provider][2], 60.0 / entry["rpm"] if entry.get("rpm") else 0.0)
    tpm = entry.get("tpm")
    window: deque = deque()  # (sent_at, est tokens) inside the last minute, for TPM pacing
    tasks = {t["id"]: t for t in TASKS}
    for item in items:
        task = tasks[item["task"]]
        # Pace on tokens actually used (usage.total_tokens) in the last minute, plus this prompt's estimate.
        # Eligibility above stays conservative (prompt + full max_tokens); pacing on that would cap Groq at 1 RPM.
        prompt_est = item["est_request_tokens"] - item["max_tokens"]
        if tpm:
            while window and time.time() - window[0][0] > 60:
                window.popleft()
            if window and sum(t for _, t in window) + prompt_est > tpm:
                time.sleep(max(0.0, 60 - (time.time() - window[0][0])) + 0.5)
                window.clear()
        sent_at = time.time()
        row = {"model": spec, "provider": provider, "task": task["id"], "family": task["family"], "rep": item["rep"],
               "at": time.time(), "max_tokens": item["max_tokens"], "est_request_tokens": item["est_request_tokens"],
               **meta}
        stop = None
        try:
            r = call(provider, model, task["prompt"], item["max_tokens"])
            row.update({k: r[k] for k in ("ttft_s", "total_s", "reasoning_chars", "usage", "text")})
            row["out_chars"] = len(r["text"])
            row["ok"] = bool(r["text"].strip())
            row["status"] = "answered"
            try:
                row["correct"] = bool(task["grade"](r["text"]))
            except Exception:
                row["correct"] = False
        except Exception as e:  # a failed call is a wrong answer for a router
            code = getattr(e, "code", None)
            body = getattr(e, "body", "") or str(e)
            row.update({"ok": False, "correct": False, "status": "call_failed", "http_status": code,
                        "error": f"{type(e).__name__} {code or ''} {body[:160]}"})
            if planner.daily_quota_error(code, body):
                row["status"] = planner.QUOTA_EXHAUSTED
                stop = "daily quota exhausted; resume after reset (rows are resumable)"
            elif planner.too_large_error(body, code):
                stop = f"request too large although planned eligible: fix {planner.LIMITS.name} via freeze_limits.py"
            elif code == 429:
                time.sleep(gap * 6)
        used = (row.get("usage") or {}).get("total_tokens")
        window.append((sent_at, used if isinstance(used, int) else item["est_request_tokens"]))
        with LOCK, out.open("a") as f:
            f.write(json.dumps(row) + "\n")
        if stop:
            print(f"{spec}: stopping lane: {stop}", file=sys.stderr)
            return
        time.sleep(gap)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--only", required=True, help="comma list of provider/model")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-tokens", type=int, default=planner.DEFAULT_MAX_TOKENS,
                    help=f"floored at {planner.REASONING_MAX_TOKENS_FLOOR} for reasoning models")
    ap.add_argument("--force", action="store_true", help="re-measure (lane, family) pairs already in a receipt")
    ap.add_argument("--plan-only", action="store_true", help="print the plan and send nothing")
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
    limits = planner.load_limits()
    items = planner.plan(specs, TASKS, a.repeats, limits, a.max_tokens, planner.measured_pairs(), a.force)
    print(f"plan against {planner.LIMITS.name} (sha256 {limits['_sha256'][:12]}):", file=sys.stderr)
    print("\n".join(planner.summarize(items)), file=sys.stderr)
    if a.plan_only:
        return 0
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        for line in out.open():
            r = json.loads(line)
            st = r.get("status", "")
            if r.get("ok") or st.startswith(planner.NOT_ELIGIBLE) or (
                    st != planner.QUOTA_EXHAUSTED and "429" not in (r.get("error") or "")):
                done.add((r["model"], r["task"], r["rep"]))
    meta = {"task_set_sha256": task_set_sha256(), "limits_sha256": limits["_sha256"],
            "runner": "z0evals/studies/free-taskfit-v0/scripts/run_taskfit.py"}
    with out.open("a") as f:  # planned-out rows are recorded, never sent
        for it in items:
            if it["status"].startswith(planner.NOT_ELIGIBLE) and (it["model"], it["task"], it["rep"]) not in done:
                f.write(json.dumps({**it, "provider": it["model"].split("/", 1)[0], "at": time.time(), "ok": False,
                                    **meta}) + "\n")
    sends = {s: [it for it in items if it["model"] == s and it["status"] == "send"
                 and (s, it["task"], it["rep"]) not in done] for s in specs}
    threads = [threading.Thread(target=worker, args=(s, sends[s], out, meta, limits)) for s in specs if sends[s]]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
