#!/usr/bin/env python3
"""harness-speed-v1 warm runner: one long-lived harness process per arm, a fresh conversation per
request, arms interleaved round-robin in seeded random order per round.

    python3 warm.py --arms omp-base,fx-base,pi-base --rounds 30 --warmup 1 --out DIR

pi/omp: `--mode rpc` with `new_session` before each `prompt`. fx: `fx_run.ts --serve` (new engine
per request in the same process). Hermes (s3): `hermes -p <profile> acp` (ACP over stdio), `session/new`
before each `session/prompt`; the model, provider and effort come from that profile's config.
Time is measured from writing the prompt command to stdin.
"""
import argparse
import json
import os
import random
import subprocess
import tempfile
import threading
import queue
import time

import bench

LAT_PROMPT, EXPECT = bench.LATENCY_PROMPT, bench.LATENCY_EXPECT


HERMES_ACP_PROFILES = {"hermes-speed": "speed", "hermes-speed-guided": "speed-guided"}


def argv_for(arm):
    fam = bench.family(arm)
    if fam == "hermes":
        return ["hermes", "-p", HERMES_ACP_PROFILES[arm], "acp"]
    cmd = bench.arm_cmd(arm, "__P__")
    if fam == "fx":
        i = cmd.index("--prompt")
        return cmd[:i] + ["--serve"]
    cmd = [c for c in cmd if c not in ("__P__", "--")]
    for flag in ("-p",):
        cmd.remove(flag)
    i = cmd.index("--mode")
    cmd[i + 1] = "rpc"
    if fam == "omp":
        cmd = [c for c in cmd if c not in ("--max-time", "600")]
    return cmd


class Proc:
    def __init__(self, arm, cwd):
        self.arm, self.fam = arm, bench.family(arm)
        self.p = subprocess.Popen(argv_for(arm), cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, start_new_session=True)
        self.q = queue.Queue()
        threading.Thread(target=self._pump, daemon=True).start()
        self.n = 0
        self.cwd = cwd
        if self.fam == "hermes":
            _t, r = self.rpc("initialize", {"protocolVersion": 1, "clientCapabilities": {
                "fs": {"readTextFile": False, "writeTextFile": False}, "terminal": False}}, 120)
            self.acp_ok = bool(r and "result" in r)

    def rpc(self, method, params, timeout, on_note=None):
        """One ACP JSON-RPC call; agent->client requests (permissions) are answered allow-once."""
        self.n += 1
        rid = f"a{self.n}"
        self.send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        end = time.perf_counter() + timeout
        while True:
            t, d = self.wait_for(lambda d: True, max(0.01, end - time.perf_counter()))
            if d is None or d.get("type") == "__eof__":
                return t, None
            if d.get("id") == rid and ("result" in d or "error" in d):
                return t, d
            if "method" in d and "id" in d:
                res = {"outcome": {"outcome": "selected", "optionId": "allow_once"}} if "permission" in d["method"] else None
                self.send({"jsonrpc": "2.0", "id": d["id"], "result": res})
            elif on_note:
                on_note(t, d)

    def _pump(self):
        for raw in iter(self.p.stdout.readline, b""):
            try:
                self.q.put((time.perf_counter(), json.loads(raw)))
            except Exception:
                pass
        self.q.put((time.perf_counter(), {"type": "__eof__"}))

    def send(self, obj):
        self.p.stdin.write((json.dumps(obj) + "\n").encode())
        self.p.stdin.flush()

    def drain(self):
        while not self.q.empty():
            self.q.get_nowait()

    def wait_for(self, pred, timeout):
        end = time.perf_counter() + timeout
        while True:
            left = end - time.perf_counter()
            if left <= 0:
                return None, None
            try:
                t, d = self.q.get(timeout=left)
            except queue.Empty:
                return None, None
            if d.get("type") == "__eof__" or pred(d):
                return t, d

    def request(self, cwd, timeout=120):
        if self.fam == "hermes":
            return self.request_acp(cwd, timeout)
        self.n += 1
        rid = f"r{self.n}"
        if self.fam in ("pi", "omp"):
            self.drain()
            self.send({"id": f"ns{self.n}", "type": "new_session"})
            _t, resp = self.wait_for(lambda d: d.get("type") == "response" and d.get("id") == f"ns{self.n}", 30)
            ns_ok = bool(resp and resp.get("success"))
            time.sleep(0.2)
            self.drain()
            t0 = time.perf_counter()
            self.send({"id": rid, "type": "prompt", "message": LAT_PROMPT})
            ttft, text, usage, err = None, "", {}, None
            deadline = t0 + timeout
            while True:
                t, d = self.wait_for(lambda d: True, max(0.01, deadline - time.perf_counter()))
                if d is None:
                    err = "timeout"
                    break
                typ = d.get("type")
                if typ == "__eof__":
                    err = "eof"
                    break
                if typ == "message_update" and (d.get("assistantMessageEvent") or {}).get("type") == "text_delta" and ttft is None:
                    ttft = (t - t0) * 1000
                if typ == "message_end" and (d.get("message") or {}).get("role") == "assistant":
                    m = d["message"]
                    text = "".join(c.get("text", "") for c in m.get("content") or [] if c.get("type") == "text")
                    usage = m.get("usage") or {}
                if typ == "response" and d.get("id") == rid and not d.get("success"):
                    err = str(d.get("error"))[:200]
                    break
                if typ == "agent_end":
                    end = (t - t0) * 1000
                    return {"ttft_ms": ttft, "total_ms": end, "text": text, "new_session_ok": ns_ok,
                            "tokens": {"input_total": (usage.get("input") or 0) + (usage.get("cacheRead") or 0),
                                       "output": usage.get("output") or 0, "cache_read": usage.get("cacheRead") or 0},
                            "error": None}
            return {"ttft_ms": ttft, "total_ms": (time.perf_counter() - t0) * 1000, "text": text, "error": err,
                    "new_session_ok": ns_ok, "tokens": {}}
        # fx --serve
        self.drain()
        t0 = time.perf_counter()
        self.send({"id": rid, "prompt": LAT_PROMPT, "cwd": cwd})
        ttft = None
        while True:
            t, d = self.wait_for(lambda d: d.get("id") == rid, timeout)
            if d is None or d.get("type") == "__eof__":
                return {"ttft_ms": ttft, "total_ms": (time.perf_counter() - t0) * 1000, "text": "", "error": "timeout/eof", "tokens": {}}
            if d.get("type") == "first_text" and ttft is None:
                ttft = (t - t0) * 1000
            if d.get("type") == "error":
                return {"ttft_ms": ttft, "total_ms": (t - t0) * 1000, "text": "", "error": d.get("message"), "tokens": {}}
            if d.get("type") == "result":
                u = d.get("usage") or {}
                return {"ttft_ms": ttft, "total_ms": (t - t0) * 1000, "text": d.get("text", ""), "error": None,
                        "tokens": {"input_total": u.get("inputTokens") or 0, "output": u.get("outputTokens") or 0,
                                   "cache_read": u.get("cacheReadTokens") or 0}}

    def request_acp(self, cwd, timeout):
        self.drain()
        _t, r = self.rpc("session/new", {"cwd": cwd, "mcpServers": []}, 60)
        sid = ((r or {}).get("result") or {}).get("sessionId")
        if not sid:
            return {"ttft_ms": None, "total_ms": None, "text": "", "error": f"session/new failed: {str(r)[:200]}",
                    "new_session_ok": False, "tokens": {}}
        time.sleep(0.2)
        self.drain()
        first, text = [None], []

        def note(t, d):
            u = (d.get("params") or {}).get("update") or {}
            if u.get("sessionUpdate") == "agent_message_chunk":
                if first[0] is None:
                    first[0] = t
                text.append((u.get("content") or {}).get("text", ""))
        t0 = time.perf_counter()
        t, r = self.rpc("session/prompt", {"sessionId": sid, "prompt": [{"type": "text", "text": LAT_PROMPT}]}, timeout, note)
        if r is None or "error" in r:
            return {"ttft_ms": (first[0] - t0) * 1000 if first[0] else None, "total_ms": (time.perf_counter() - t0) * 1000,
                    "text": "".join(text), "error": str((r or {}).get("error", "timeout/eof"))[:200], "new_session_ok": True,
                    "tokens": {}}
        u = (r.get("result") or {}).get("usage") or {}
        return {"ttft_ms": (first[0] - t0) * 1000 if first[0] else None, "total_ms": (t - t0) * 1000, "text": "".join(text),
                "error": None, "new_session_ok": True,
                # ACP inputTokens excludes cached reads (checked in smoke: 3401 + 1920 cached = 5321)
                "tokens": {"input_total": (u.get("inputTokens") or 0) + (u.get("cachedReadTokens") or 0),
                           "output": u.get("outputTokens") or 0, "cache_read": u.get("cachedReadTokens") or 0}}

    def close(self):
        try:
            self.p.stdin.close()
            self.p.wait(timeout=15)
        except Exception:
            os.killpg(self.p.pid, 15)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", required=True)
    ap.add_argument("--rounds", type=int, default=30)
    ap.add_argument("--warmup", type=int, default=1)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=20261022)
    ap.add_argument("--session", default="s1")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rng = random.Random(a.seed)
    arms = a.arms.split(",")
    cwd = tempfile.mkdtemp(prefix="hsb-warm-")
    procs = {arm: Proc(arm, cwd) for arm in arms}
    time.sleep(10)  # let every process finish startup before the first request
    out = os.path.join(a.out, "warm.jsonl")
    for rnd in range(-a.warmup, a.rounds):
        order = arms[:]
        rng.shuffle(order)
        for pos, arm in enumerate(order):
            r = procs[arm].request(cwd)
            r.update({"kind": "latency", "mode": "warm", "arm": arm, "family": bench.family(arm), "block": rnd, "pos": pos,
                      "phase": "warmup" if rnd < 0 else "run", "session": a.session, "at": time.time(),
                      "correct": EXPECT in (r.get("text") or "") and not r.get("error")})
            with open(out, "a") as f:
                f.write(json.dumps(r) + "\n")
            print(json.dumps({k: r.get(k) for k in ("block", "arm", "ttft_ms", "total_ms", "correct", "error")}), flush=True)
    for p in procs.values():
        p.close()


if __name__ == "__main__":
    main()
