#!/usr/bin/env python3
"""harness-speed-v1 cold runner: one fresh harness process per request, same model everywhere.

    python3 bench.py latency --arms a,b,... --blocks 32 --warmup-blocks 1 --out DIR [--seed N]
    python3 bench.py tasks   --arms a,b,... --reps 2 --tasks t01-paginate,... --out DIR [--seed N]

Every request runs in a fresh empty directory (latency) or a fresh copy of the task repo (tasks).
Arm order is shuffled inside each block (latency) or each (rep, task) cell (tasks) with a fixed
seed, so provider drift and host noise spread over all arms. Rows append to DIR/<kind>.jsonl.
Timing is taken here, by the parent, from spawn: first assistant text line seen on stdout, and
process exit. Harness-reported timings are stored next to them but are not the primary metric.
"""
import argparse
import json
import os
import random
import shutil
import signal
import subprocess
import sys
import tempfile
import time

HOME = os.path.expanduser("~")
BENCH = os.path.join(HOME, ".cache", "harness-speed-v1")
TASKS = os.path.join(BENCH, "tasks")
SOLPI = os.path.join(HOME, ".pi/agent/git/github.com/NVlabs/SoL-Pi/src/sol-pi/index.ts")
PIRLM = os.path.join(HOME, ".pi/agent/npm/node_modules/@shift-labs/pi-rlm/src/extension/index.ts")
MODEL = os.environ.get("HSB_MODEL", "gpt-6.1-sol")
EFFORT = "low"
HERMES_DEFAULT_TOOLSETS = ("a2a,browser,clarify,code_execution,computer_use,connections,cronjob,delegation,file,"
                           "image_gen,kanban,memory,session_search,skills,terminal,todo,tts,vision,web")
LATENCY_PROMPT = "What is 17 * 23? Reply with only the number."
LATENCY_EXPECT = "391"
TIMEOUT = {"latency": 120, "tasks": 600}


OMP_MODELS = {"claude-opus-5-5": "anthropic/claude-opus-5-5"}


def split_arm(arm):
    """'omp-base@claude-opus-5-5' -> ('omp-base', 'claude-opus-5-5'); plain arms use MODEL."""
    base, _, model = arm.partition("@")
    return base, (model or None)


def omp_model(arm=""):
    _base, model = split_arm(arm)
    return OMP_MODELS[model] if model else f"openai-codex/{MODEL}"


def arm_cmd(arm, prompt):
    """argv for one request. Model, provider and effort are identical across arms; only the
    harness and its plugin/tool configuration change. `@model` arms (C5) change only the model.
    `-offline` / `-clarify` arms are exploratory follow-ups (session s2), not preregistered."""
    base_arm, model_override = split_arm(arm)
    if model_override and not base_arm.startswith("omp"):
        raise ValueError("model arms are defined for omp only")
    hermes = ["hermes", "chat", "-q", prompt, "--provider", "openai-codex", "-m", MODEL, "--reasoning", EFFORT,
              "--format", "stream-json", "--yolo", "--source", "tool", "--max-turns", "60"]
    omp = ["omp", "-p", "--mode", "json", "--no-session", "--no-title", "--model", omp_model(arm), "--thinking", EFFORT,
           "--auto-approve", "--max-time", "600"]
    pi = ["pi", "-p", "--mode", "json", "--no-session", "--provider", "openai-codex", "--model", MODEL,
          "--thinking", EFFORT]
    pi_base = ["-ne", "-ns", "-np", "-nc", "--no-mcp"]
    table = {
        "hermes-base": hermes + ["--safe-mode", "-t", "terminal,file"],
        "hermes-default": hermes + ["-t", HERMES_DEFAULT_TOOLSETS],
        "fx-base": ["bun", os.path.join(BENCH, "fx", "fx_run.ts"), "--model", MODEL, "--effort", EFFORT, "--prompt", prompt],
        "omp-base": omp + ["--no-extensions", "--no-skills", "--no-rules", "--no-lsp", "--tools", "read,bash,edit,write", prompt],
        "omp-default": omp + [prompt],
        # `--` before the prompt: extension flags such as --rlm otherwise swallow the next argument.
        "pi-base": pi + pi_base + ["--tools", "read,bash,edit,write", "--", prompt],
        "pi-solpi": pi + pi_base + ["-e", SOLPI, "--tools", "read,bash,edit,write", "--", prompt],
        "pi-rlm": pi + pi_base + ["-e", PIRLM, "--rlm", "--", prompt],
        # exploratory (s2): pi-base plus --offline (no startup network operations)
        "pi-base-offline": pi + pi_base + ["--offline", "--tools", "read,bash,edit,write", "--", prompt],
        # exploratory (s2): hermes-base with the clarify toolset only (no shell/file tool to compute with)
        "hermes-base-clarify": hermes + ["--safe-mode", "-t", "clarify"],
    }
    return table[base_arm]


def family(arm):
    return arm.split("-")[0].split("@")[0]


class Parse:
    """Per-harness stdout parser -> uniform fields."""

    def __init__(self, fam):
        self.fam = fam
        self.first_text = None
        self.text = ""
        self.tool_calls = 0
        self.model_requests = 0
        self.tokens = {"input_total": 0, "output": 0, "cache_read": 0}
        self.reported = {}
        self.errors = []
        self._batches = 0
        self._in_batch = False
        self._text_after_batch = False

    def line(self, t, raw):
        try:
            d = json.loads(raw)
        except Exception:
            return
        typ = d.get("type")
        if self.fam == "hermes":
            if typ == "text":
                if self.first_text is None:
                    self.first_text = t
                self._text_after_batch = True
                self.text += d.get("text", "")
            elif typ == "tool_use":
                self.tool_calls += 1
                if not self._in_batch:
                    self._batches += 1
                self._in_batch = True
            elif typ == "tool_result":
                self._in_batch = False
                self._text_after_batch = False
            elif typ == "result":
                tk = d.get("tokens") or {}
                # Hermes reports OpenAI-style input (cached included) plus cache_read.
                self.tokens = {"input_total": tk.get("input", 0), "output": tk.get("output", 0), "cache_read": tk.get("cache_read", 0)}
                self.reported = {"duration_ms": d.get("duration_ms"), "exit_code": d.get("exit_code")}
                self.text = d.get("text") or self.text
            elif typ == "error":
                self.errors.append(str(d)[:300])
        elif self.fam in ("omp", "pi"):
            if typ == "message_update":
                ev = d.get("assistantMessageEvent") or {}
                if ev.get("type") == "text_delta" and self.first_text is None:
                    self.first_text = t
            elif typ == "tool_execution_start":
                self.tool_calls += 1
            elif typ == "message_end":
                m = d.get("message") or {}
                if m.get("role") == "assistant":
                    self.model_requests += 1
                    u = m.get("usage") or {}
                    # pi-ai convention: input excludes cache reads/writes.
                    self.tokens["input_total"] += (u.get("input") or 0) + (u.get("cacheRead") or 0) + (u.get("cacheWrite") or 0)
                    self.tokens["output"] += u.get("output") or 0
                    self.tokens["cache_read"] += u.get("cacheRead") or 0
                    cost = (u.get("cost") or {}).get("total")
                    if cost is not None:
                        self.reported["harness_cost_usd"] = self.reported.get("harness_cost_usd", 0) + cost
                    if m.get("ttft") is not None:
                        self.reported.setdefault("ttft_ms_reported", m.get("ttft"))
                    if m.get("stopReason") == "error" or m.get("errorMessage"):
                        self.errors.append(str(m.get("errorMessage"))[:300])
                    parts = [c.get("text", "") for c in (m.get("content") or []) if c.get("type") == "text"]
                    if parts:
                        self.text = "".join(parts)
        elif self.fam == "fx":
            if typ == "first_text" and self.first_text is None:
                self.first_text = t
            elif typ == "tool_start":
                self.tool_calls += 1
                if not self._in_batch:
                    self._batches += 1
                self._in_batch = True
            elif typ == "tool_end":
                self._in_batch = False
            elif typ == "result":
                u = d.get("usage") or {}
                self.tokens = {"input_total": (u.get("inputTokens") or 0), "output": u.get("outputTokens") or 0, "cache_read": u.get("cacheReadTokens") or 0}
                self.text = d.get("text", "")
                self.reported = {"stop": d.get("stopReason"), "engine_ms": d.get("ms")}
            elif typ == "error":
                self.errors.append(d.get("message", "")[:300])


def run_one(arm, prompt, cwd, timeout):
    argv = arm_cmd(arm, prompt)
    parser = Parse(family(arm))
    errf = tempfile.TemporaryFile()
    t0 = time.perf_counter()
    p = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=errf,
                         start_new_session=True)
    timed_out = False
    deadline = t0 + timeout
    try:
        for raw in iter(p.stdout.readline, b""):
            parser.line((time.perf_counter() - t0) * 1000, raw.decode("utf-8", "replace"))
            if time.perf_counter() > deadline:
                timed_out = True
                break
        p.wait(timeout=max(1, deadline - time.perf_counter()))
    except subprocess.TimeoutExpired:
        timed_out = True
    if timed_out and p.poll() is None:
        os.killpg(p.pid, signal.SIGTERM)  # only this request's own process group
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait()
    total = (time.perf_counter() - t0) * 1000
    if parser.fam in ("hermes", "fx"):
        # Estimated: one model request per tool batch plus the final answer request.
        parser.model_requests = parser._batches + (1 if parser.text else 0)
    errf.seek(0)
    err_tail = errf.read()[-600:].decode("utf-8", "replace")
    tk = parser.tokens
    uncached = max(0, tk["input_total"] - tk["cache_read"])
    cost = uncached * 2e-6 + tk["cache_read"] * 1e-7 + tk["output"] * 1e-5  # uniform list-price estimate
    return {
        "arm": arm, "family": family(arm), "model": MODEL if family(arm) != "omp" else omp_model(arm),
        "ttft_ms": parser.first_text, "total_ms": total, "exit": p.returncode, "timed_out": timed_out,
        "text": parser.text[-400:], "tool_calls": parser.tool_calls, "model_requests": parser.model_requests,
        "tokens": tk, "cost_est_usd": round(cost, 6), "reported": parser.reported, "errors": parser.errors,
        "stderr_tail": "" if p.returncode == 0 and not timed_out else err_tail.replace(HOME, "~"),
    }


def append(path, row):
    with open(path, "a") as f:
        f.write(json.dumps(row) + "\n")


def latency(args):
    rng = random.Random(args.seed)
    arms = args.arms.split(",")
    out = os.path.join(args.out, "latency.jsonl")
    for block in range(-args.warmup_blocks, args.blocks):
        order = arms[:]
        rng.shuffle(order)
        for pos, arm in enumerate(order):
            cwd = tempfile.mkdtemp(prefix="hsb-lat-")
            row = run_one(arm, LATENCY_PROMPT, cwd, TIMEOUT["latency"])
            shutil.rmtree(cwd, ignore_errors=True)
            row.update({"kind": "latency", "mode": "cold", "phase": "warmup" if block < 0 else "run", "block": block,
                        "pos": pos, "session": args.session, "at": time.time(),
                        "correct": LATENCY_EXPECT in (row["text"] or "") and row["exit"] == 0})
            append(out, row)
            print(json.dumps({k: row[k] for k in ("block", "arm", "ttft_ms", "total_ms", "correct")}), flush=True)


def tasks(args):
    rng = random.Random(args.seed)
    arms = args.arms.split(",")
    names = args.tasks.split(",") if args.tasks else sorted(os.listdir(TASKS))
    out = os.path.join(args.out, "tasks.jsonl")
    for rep in range(args.reps):
        order_t = names[:]
        rng.shuffle(order_t)
        for task in order_t:
            order_a = arms[:]
            rng.shuffle(order_a)
            for arm in order_a:
                tdir = os.path.join(TASKS, task)
                work = tempfile.mkdtemp(prefix=f"hsb-{task}-")
                repo = os.path.join(work, "repo")
                shutil.copytree(os.path.join(tdir, "repo"), repo)
                subprocess.run(["git", "init", "-q"], cwd=repo)
                subprocess.run(["git", "add", "-A"], cwd=repo)
                subprocess.run(["git", "-c", "user.name=bench", "-c", "user.email=bench@localhost", "commit", "-qm", "task"], cwd=repo)
                prompt = open(os.path.join(tdir, "prompt.txt")).read().strip()
                row = run_one(arm, prompt, repo, TIMEOUT["tasks"])
                vr = subprocess.run([sys.executable, os.path.join(BENCH, "harness", "verify.py"), tdir, repo],
                                    capture_output=True, text=True)
                try:
                    ver = json.loads(vr.stdout)
                except Exception:
                    ver = {"pass": False, "summary": "verifier crashed"}
                shutil.rmtree(work, ignore_errors=True)
                row.update({"kind": "task", "task": task, "rep": rep, "session": args.session, "at": time.time(),
                            "verified": ver})
                append(out, row)
                print(json.dumps({"rep": rep, "task": task, "arm": arm, "s": round(row["total_ms"] / 1000, 1),
                                  "pass": ver.get("pass"), "tools": row["tool_calls"]}), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["latency", "tasks"])
    ap.add_argument("--arms", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=20261021)
    ap.add_argument("--session", default="s1")
    ap.add_argument("--blocks", type=int, default=32)
    ap.add_argument("--warmup-blocks", type=int, default=1)
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--tasks", default="")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    latency(a) if a.kind == "latency" else tasks(a)
