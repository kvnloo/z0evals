#!/usr/bin/env python3
"""Shadow-Network chooser eval for GUI steps (study gui-scripting-speed).

Every arm sees the SAME compiled legal action set (the case's safety-filtered candidate
table) and records only a hypothetical choice + confidence + latency. Nothing here acts on
a device. Rows are passive-shadow predictions on a frozen, hand-labelled fixture; they are
scored against the fixture's gold set, never against another arm (agreement is not
correctness, z0evals#93).

Arms (one process per arm, because engines live in different venvs):

  jev:flat            incumbent: goalkit JevChooser (jev-latest, 0.65 floor)
  jev:flat+bt         incumbent + Bradley-Terry fallback (goalkit.pairwise)
  z0int:<backend>     z0int DecisionBackend (direct option logits / typed decision):
                      openjev_06b, nanojev, julia_1, decider_2b, laya_421m
  llamacpp:<url>|<alias>   OpenAI-compatible llama.cpp server, JSON-schema enum output
  ollama:<model>      ollama /api/chat with format=json-schema enum

    python harness/shadow_eval.py --arm z0int:openjev_06b --reps 3 --out data/shadow/x.jsonl

Environment: PHONE_GOAL_REPO (goalkit), Z0INT_SRC (z0intelligence/src).
"""
from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
CASES = STUDY / "tasks" / "android-chooser-cases.v1.json"
SCHEMA = "z0evals.gui_scripting_speed.shadow_decision.v1"

INSTRUCTIONS = (
    "You are choosing the single next action for a phone GUI agent. The state holds the goal, "
    "what was already done, and the elements on the current screen. Pick the option that moves "
    "toward the goal right now. Pick 'done' only if the answer to the goal is visible on this "
    "screen. Pick 'abstain' for sign-in, credential or payment screens. Never pick an option "
    "marked Consequential unless the goal explicitly asks for that change. Pick 'reobserve' only "
    "if the screen is still loading."
)


def state_for(case):
    return {
        "goal": case["goal"],
        "history": [f"{h.get('selected_id')}: {h.get('outcome')}" for h in case.get("history", [])][-8:],
        "screen": [f"{r.get('role')}: {r.get('label')}" + ("" if r.get("interactive") else " (text)")
                   for r in case["regions"]],
    }


# ---------------------------------------------------------------- arms ----------
class JevArm:
    def __init__(self, strategy):
        sys.path.insert(0, os.environ.get("PHONE_GOAL_REPO", "/mnt/zer0models/hermes-phone-goal"))
        from goalkit.jev import make_chooser  # noqa
        self.make = make_chooser
        self.strategy = strategy
        self.engine, self.model = "jev-api", "jev-latest"
        self.max_options = 32

    def load(self):
        return 0.0

    def choose(self, case, seed):
        ch = self.make(self.strategy, seed=seed) if self.strategy != "flat" else self.make("flat")
        r = ch(goal=case["goal"], regions=case["regions"], candidates=case["candidates"],
               history=case["history"], observation_id=case["case"])
        d = ch.decisions[-1] if getattr(ch, "decisions", None) else {}
        probs = r.get("probabilities") or {}
        raw = max(probs, key=probs.get) if probs else r.get("id")
        return {"selected_action": r.get("id"), "raw_argmax": raw, "confidence": r.get("confidence"),
                "calls": d.get("jev_calls", 1), "top": sorted(probs.items(), key=lambda kv: -kv[1])[:3]}


class Z0intArm:
    def __init__(self, backend_id):
        sys.path.insert(0, os.environ.get("Z0INT_SRC", "/mnt/zer0models/z0-wt/z0intelligence/src"))
        from z0int.backends.registry import create_backend, register_builtin_backends
        from z0int.backends.base import request_from_mapping
        register_builtin_backends()
        self.req = request_from_mapping
        self.backend = create_backend(backend_id)
        self.engine, self.model = "z0int-transformers", backend_id
        self.max_options = int(self.backend.capabilities.max_choice_options or 16)

    def load(self):
        t0 = time.perf_counter()
        h = self.backend.health(load=True)
        if not getattr(h, "ready", True) and "load" in str(getattr(h, "detail", "")):
            raise RuntimeError(f"load failed: {h.detail}")
        return (time.perf_counter() - t0) * 1000

    def _one(self, case, options):
        raw = {"state": state_for(case), "request_id": case["case"],
               "questions": [{"id": "next", "type": "choice", "instructions": INSTRUCTIONS,
                              "options": [{"id": o["id"], "description": o["description"]} for o in options]}]}
        res = self.backend.evaluate(self.req(raw))
        a = res.answers[0]
        probs = a.probabilities or {}
        return a.value, a.confidence, probs

    def choose(self, case, seed):
        opts = case["candidates"]
        calls = 0
        if len(opts) <= self.max_options:
            v, c, p = self._one(case, opts)
            calls = 1
        else:  # chunked two-stage: winners of each chunk, then a final among winners
            size = self.max_options
            winners = []
            for i in range(0, len(opts), size):
                chunk = opts[i:i + size]
                if len(chunk) == 1:
                    winners.append(chunk[0]); continue
                v, c, p = self._one(case, chunk); calls += 1
                winners.append(next(o for o in chunk if o["id"] == v))
            v, c, p = self._one(case, winners); calls += 1
        return {"selected_action": v, "raw_argmax": v, "confidence": c, "calls": calls,
                "top": sorted(p.items(), key=lambda kv: -kv[1])[:3]}


class OpenAIArm:
    """llama.cpp server (OpenAI-compatible) with a JSON-schema enum, or ollama /api/chat."""

    def __init__(self, spec, kind):
        self.kind = kind
        if kind == "llamacpp":
            self.url, self.model = spec.split("|", 1)
            self.engine = "llama.cpp"
        else:
            self.url, self.model = "http://127.0.0.1:11435", spec
            self.engine = "ollama"
        self.max_options = 64

    def load(self):
        t0 = time.perf_counter()
        self._post(self._body({"case": "warm", "goal": "warm", "history": [], "regions": [],
                               "candidates": [{"id": "reobserve", "description": "look again"},
                                              {"id": "abstain", "description": "stop"}]}))
        return (time.perf_counter() - t0) * 1000

    def _body(self, case):
        ids = [o["id"] for o in case["candidates"]]
        prompt = (INSTRUCTIONS + "\n\nSTATE:\n" + json.dumps(state_for(case), ensure_ascii=False) +
                  "\n\nOPTIONS:\n" + "\n".join(f"- {o['id']}: {o['description']}" for o in case["candidates"]) +
                  '\n\nAnswer with JSON {"id": "<option id>"}.')
        schema = {"type": "object", "properties": {"id": {"type": "string", "enum": ids}}, "required": ["id"]}
        if self.kind == "llamacpp":
            return {"model": self.model, "messages": [{"role": "user", "content": prompt}], "temperature": 0,
                    "max_tokens": 24, "response_format": {"type": "json_schema", "json_schema": {"schema": schema}},
                    "logprobs": True, "top_logprobs": 5}
        return {"model": self.model, "messages": [{"role": "user", "content": prompt}], "stream": False,
                "format": schema, "options": {"temperature": 0, "num_predict": 24}, "keep_alive": "10m"}

    def _post(self, body):
        path = "/v1/chat/completions" if self.kind == "llamacpp" else "/api/chat"
        req = urllib.request.Request(self.url + path, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())

    def choose(self, case, seed):
        out = self._post(self._body(case))
        conf = None
        if self.kind == "llamacpp":
            ch = out["choices"][0]
            txt = ch["message"]["content"]
            # confidence = probability of the whole constrained answer (product of token probs);
            # with a JSON-schema enum, only the id tokens are uncertain
            lp = [t.get("logprob") for t in ((ch.get("logprobs") or {}).get("content") or [])]
            if lp and all(isinstance(x, (int, float)) for x in lp):
                import math
                conf = math.exp(sum(lp))
        else:
            txt = out["message"]["content"]
        try:
            v = json.loads(txt).get("id")
        except Exception:  # noqa: BLE001
            v = None
        return {"selected_action": v, "raw_argmax": v, "confidence": conf, "calls": 1, "top": []}

    def unload(self):
        if self.kind == "ollama":   # do not leave the model resident on the shared GPU
            try:
                req = urllib.request.Request(self.url + "/api/generate", data=json.dumps(
                    {"model": self.model, "keep_alive": 0}).encode(), headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=30).read()
            except Exception:  # noqa: BLE001
                pass


class RuleArm:
    """Zero-model deterministic control (z0evals#93 'cheap deterministic/manual control').

    Designed AFTER seeing the fixture, so it is a post-hoc control that needs a fresh
    confirmation set before any credit. Rules, in order:
      1. a sign-in / password / permission screen -> abstain
      2. a non-interactive screen text that names the goal's target AND carries a value -> done
      3. a non-consequential tap row whose label shares a goal keyword -> tap the best match
      4. scroll-down if offered, else reobserve
    """
    STOP = set("open the and read report a an of to in on settings level name version phone is what".split())

    def __init__(self):
        self.engine, self.model, self.max_options = "deterministic", "rule-lexical-v1", 999

    def load(self):
        return 0.0

    def choose(self, case, seed):
        import re
        goal = case["goal"].lower()
        words = [w for w in re.findall(r"[a-z]+", goal) if w not in self.STOP and len(w) > 2]
        target = [w for w in re.findall(r"[a-z]+", goal.split(">")[-1]) if w not in self.STOP and len(w) > 2]
        labels = " ".join(r["label"].lower() for r in case["regions"])
        ids = {o["id"]: o for o in case["candidates"]}
        if re.search(r"sign in|password|allow .* to access", labels):
            return self._r("abstain" if "abstain" in ids else "reobserve")
        tail = [w for w in re.findall(r"[a-z]+", goal) if w not in ("open", "the", "and", "read", "report", "settings")][-2:]
        for r in case["regions"]:
            lab = r["label"].lower()
            if (not r.get("interactive") or "\u00b7" in r["label"]) and all(t in lab for t in tail[-1:]) and \
                    re.search(r"\d", lab) and "done" in ids:
                return self._r("done")
        best, score = None, 0
        for o in case["candidates"]:
            if not o["id"].startswith("tap-") or "Consequential" in o["description"]:
                continue
            d = o["description"].lower()
            s = sum(2 if w in target else 1 for w in set(words) if w in d)
            if s > score:
                best, score = o["id"], s
        if best:
            return self._r(best)
        return self._r("scroll-down" if "scroll-down" in ids else "reobserve")

    @staticmethod
    def _r(i):
        return {"selected_action": i, "raw_argmax": i, "confidence": None, "calls": 0, "top": []}


def make_arm(spec):
    kind, _, rest = spec.partition(":")
    if kind == "rule":
        return RuleArm()
    if kind == "jev":
        return JevArm(rest)
    if kind == "z0int":
        return Z0intArm(rest)
    if kind in ("llamacpp", "ollama"):
        return OpenAIArm(rest, kind)
    raise SystemExit(f"unknown arm {spec}")


def verdict(pid, gold):
    if pid in gold:
        return "correct"
    if pid is None:
        return "error"
    if pid == "reobserve":
        return "uncertain"
    return "wrong"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--out", required=True)
    ap.add_argument("--run-id", default=time.strftime("%Y%m%dT%H%M%S"))
    a = ap.parse_args()
    cases = json.loads(CASES.read_text())
    arm = make_arm(a.arm)
    err = None
    try:
        cold_ms = arm.load()
    except Exception as e:  # noqa: BLE001
        cold_ms, err = None, f"{type(e).__name__}: {str(e)[:300]}"
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a") as f:
        f.write(json.dumps({"schema": SCHEMA + ".header", "run_id": a.run_id, "arm": a.arm, "engine": arm.engine,
                            "model": arm.model, "cold_load_ms": cold_ms, "load_error": err,
                            "cases_file": CASES.name, "reps": a.reps, "instructions": INSTRUCTIONS,
                            "max_options": arm.max_options, "ts": time.time()}) + "\n")
    if err:
        print("LOAD FAIL", err); return 2
    if not a.arm.startswith("jev:"):          # one excluded warm-up decision
        try:
            arm.choose(cases[0], 0)
        except Exception as e:  # noqa: BLE001
            print("warmup error", e)
    lat = []
    for rep in range(1, a.reps + 1):
        order = list(range(len(cases)))
        random.Random(7919 * rep).shuffle(order)
        if rep % 2 == 0:
            order.reverse()
        for k in order:
            c = cases[k]
            t0 = time.perf_counter()
            e = None
            try:
                r = arm.choose(c, seed=1000 * rep + k)
            except Exception as ex:  # noqa: BLE001
                r, e = {"selected_action": None, "raw_argmax": None, "confidence": None, "calls": 0, "top": []}, \
                    f"{type(ex).__name__}: {str(ex)[:200]}"
            ms = (time.perf_counter() - t0) * 1000
            lat.append(ms)
            row = {"schema": SCHEMA, "run_id": a.run_id, "arm": a.arm, "engine": arm.engine, "model": arm.model,
                   "evidence_class": ("incumbent_prediction_on_frozen_fixture" if a.arm.startswith("jev:")
                                      else "passive_shadow_prediction_on_frozen_fixture"),
                   "trafficEligible": False, "rep": rep, "case": c["case"], "kind": c["kind"], "source": c["source"],
                   "screen": c.get("screen"), "n_legal": len(c["candidates"]),
                   "legal_ids": [o["id"] for o in c["candidates"]], "gold": c["gold"],
                   "selected_action": r["selected_action"], "raw_argmax": r.get("raw_argmax"),
                   "confidence": r["confidence"], "top": r.get("top"), "model_calls": r["calls"],
                   "latency_ms": round(ms, 2), "verdict": verdict(r["selected_action"], c["gold"]),
                   "raw_verdict": verdict(r.get("raw_argmax"), c["gold"]), "error": e, "ts": time.time()}
            with out.open("a") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    if hasattr(arm, "unload"):
        arm.unload()
    lat.sort()
    print(a.arm, "n", len(lat), "p50", round(statistics.median(lat), 1), "p95",
          round(lat[int(0.95 * (len(lat) - 1))], 1), "cold", cold_ms)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
