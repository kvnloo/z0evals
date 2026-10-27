#!/usr/bin/env python3
"""Live read-only S22+ experiment: phone_goal (Jev flat / flat+BT) vs a compiled GUI macro
vs a deterministic non-GUI read, on the same three navigate-and-read goals.

Safety: read-only Settings navigation only (no taps on switches, no typing, no sign-in).
Every run holds the shared S22 UI lock (flock) for its whole duration and releases it
between runs. Device selection is passed per subprocess env, never exported.
The verifier is independent of the GUI path: the truth value is read by `adb shell getprop`
/ `dumpsys battery` and must appear in the run's final screen text. For arm D the verifier
and the method are the same source; it is a deterministic control, not a GUI result.

    python3 harness/live_s22.py --reps 3 --out data/live/s22-r1.jsonl
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

PG = Path(os.environ.get("PHONE_GOAL_REPO", "/mnt/zer0models/hermes-phone-goal"))
sys.path.insert(0, str(PG))
from goalkit.runner import Worker, child_env  # noqa: E402
from goalkit.tree import package_of, parse_xml  # noqa: E402

SERIAL = "adb-RFCTA1RZAQY-ZyDAxx._adb-tls-connect._tcp"
SOCK = "tcp:127.0.0.1:5038"
LOCK = "/home/kvn/.hermes/profiles/clean/cache/scratch/s22-ui.lock"
WS = Path("/home/kvn/.hermes/profiles/clean/plugin-data/phone-harness/agent-workspace")
SCHEMA = "z0evals.gui_scripting_speed.live_run.v1"

GOALS = {
    "android-version": {"goal": "Open Settings and read the Android version",
                        "truth": ["getprop", "ro.build.version.release"]},
    "battery-level": {"goal": "Open Settings > Battery and report the battery level",
                      "truth": ["dumpsys", "battery"], "truth_re": r"level:\s*(\d+)", "fmt": "{}%"},
    "model-name": {"goal": "Open Settings > About phone and read the model name",
                   "truth": ["getprop", "ro.product.model"]},
}


def adb(*args, timeout=20):
    env = dict(os.environ, ADB_SERVER_SOCKET=SOCK)
    p = subprocess.run(["adb", "-s", SERIAL, *args], capture_output=True, text=True, timeout=timeout, env=env)
    return p.stdout


def truth(gid):
    g = GOALS[gid]
    out = adb("shell", *g["truth"])
    if g.get("truth_re"):
        m = re.search(g["truth_re"], out)
        v = m.group(1) if m else None
    else:
        v = out.strip() or None
    return (g.get("fmt", "{}").format(v) if v else None), v


def texts(nodes):
    out = []
    for n in nodes:
        for k in ("text", "desc", "label"):
            v = n.get(k) if isinstance(n, dict) else getattr(n, k, None)
            if v:
                out.append(str(v))
    return out


def node_center(nodes, label):
    for n in nodes:
        t = (n.get("text") if isinstance(n, dict) else getattr(n, "text", "")) or ""
        if t.strip() == label and n.get("w") and n.get("h"):
            return n["x"], n["y"]
    return None


class Locked:
    def __enter__(self):
        self.f = open(LOCK, "a")
        t0 = time.perf_counter()
        fcntl.flock(self.f, fcntl.LOCK_EX)
        self.wait_ms = (time.perf_counter() - t0) * 1000
        return self

    def __exit__(self, *a):
        fcntl.flock(self.f, fcntl.LOCK_UN)
        self.f.close()


def arm_phone_goal(gid, chooser):
    g = GOALS[gid]
    cmd = [sys.executable, "-m", "goalkit.cli", "--goal", g["goal"], "--app", "Settings", "--fresh", "--restore",
           "--max-steps", "15", "--chooser", chooser, "--serial", SERIAL, "--adb-server-socket", SOCK, "--json"]
    t0 = time.perf_counter()
    p = subprocess.run(cmd, cwd=str(PG), capture_output=True, text=True, timeout=600)
    wall = (time.perf_counter() - t0) * 1000
    try:
        r = json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"status": "no_json", "wall_ms": wall, "stderr_tail": p.stderr[-300:]}, []
    calls = r.get("jev_calls") or []
    return {"status": r.get("status"), "wall_ms": wall, "total_ms": r.get("total_ms"), "steps": r.get("steps"),
            "model_calls": len(calls), "model_ms": sum(c.get("ms", 0) for c in calls),
            "phone_actions": sum(1 for t in r.get("transcript", []) if t.get("kind") not in ("observe", "done")),
            "restored": bool(r.get("restored_app")), "restore_error": r.get("restore_error")}, \
        list(r.get("final_screen") or [])


def arm_macro(gid):
    """Compiled script: intent jump, fixed 0.35 s settle, one fast-tree read, guarded tap."""
    t0 = time.perf_counter()
    w = Worker(sys.executable, child_env(WS, SERIAL, SOCK), cwd=str(WS))
    steps, guard = 0, None
    try:
        if not w.hello.get("ok"):
            return {"status": "device_not_ready", "wall_ms": (time.perf_counter() - t0) * 1000}, []
        first = parse_xml(w.call("observe")["xml"])
        initial = package_of(first) or None
        if gid == "battery-level":
            # cached per-app UI map: on this Samsung build POWER_USAGE_SUMMARY opens the usage graph,
            # not the level page, so the macro names the component directly
            adb("shell", "am", "start", "-W", "-n",
                "com.samsung.android.lool/com.samsung.android.sm.battery.ui.BatteryActivity")
        else:
            adb("shell", "am", "start", "-W", "-a", "android.settings.DEVICE_INFO_SETTINGS")
        steps += 1
        time.sleep(0.35)
        nodes = parse_xml(w.call("observe")["xml"])
        if gid == "android-version":
            c = node_center(nodes, "Software information")
            if c is None:                       # guard: one scroll, then give up
                w.call("act", kind="scroll", params={"direction": "down"}); steps += 1
                time.sleep(0.35)
                nodes = parse_xml(w.call("observe")["xml"])
                c = node_center(nodes, "Software information")
            if c is None:
                guard = "software_information_not_found"
            else:
                w.call("act", kind="tap", params={"x": c[0], "y": c[1]}); steps += 1
                time.sleep(0.35)
                nodes = parse_xml(w.call("observe")["xml"])
                if not any("Android version" in t for t in texts(nodes)):   # re-read once if mid-animation
                    time.sleep(0.3)
                    nodes = parse_xml(w.call("observe")["xml"])
        final = texts(nodes)
        wall = (time.perf_counter() - t0) * 1000
        restored = False
        if initial and initial != "com.android.settings":
            try:
                w.call("act", kind="open_app", params={"app": initial}); restored = True
            except Exception:  # noqa: BLE001
                pass
        return {"status": "done" if guard is None else "guard_failed", "guard": guard, "wall_ms": wall,
                "steps": steps, "model_calls": 0, "model_ms": 0, "phone_actions": steps, "restored": restored}, final
    finally:
        try:
            w.close()
        except Exception:  # noqa: BLE001
            pass


def arm_deterministic(gid):
    t0 = time.perf_counter()
    disp, _ = truth(gid)
    return {"status": "done", "wall_ms": (time.perf_counter() - t0) * 1000, "steps": 0, "model_calls": 0,
            "model_ms": 0, "phone_actions": 0, "verifier_same_source": True}, [disp or ""]


ARMS = {"A": ("phone_goal:flat", lambda g: arm_phone_goal(g, "flat")),
        "B": ("phone_goal:flat+bt", lambda g: arm_phone_goal(g, "flat+bt")),
        "C": ("compiled_macro", arm_macro),
        "D": ("deterministic_adb", arm_deterministic)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--goals", default=",".join(GOALS))
    ap.add_argument("--arms", default="ABCD")
    ap.add_argument("--out", required=True)
    ap.add_argument("--run-id", default=time.strftime("live-%Y%m%dT%H%M%S"))
    a = ap.parse_args()
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    for rep in range(1, a.reps + 1):
        order = list(a.arms) if rep % 2 else list(reversed(a.arms))     # ABCD / DCBA blocks
        for gid in a.goals.split(","):
            for arm in order:
                name, fn = ARMS[arm]
                with Locked() as lk:
                    disp, raw = truth(gid)
                    try:
                        res, final = fn(gid)
                    except Exception as e:  # noqa: BLE001
                        res, final = {"status": "error", "error": f"{type(e).__name__}: {str(e)[:200]}"}, []
                ok = bool(disp) and any(disp == t.strip() or (raw and t.strip() == raw) or
                                        (raw and re.search(rf"(^|\D){re.escape(raw)}(\D|$)", t) and gid != "battery-level")
                                        or (gid == "battery-level" and t.strip() == disp) for t in final)
                row = {"schema": SCHEMA, "run_id": a.run_id, "rep": rep, "goal_id": gid, "arm": name,
                       "block_order": "".join(order), "lock_wait_ms": round(lk.wait_ms, 1),
                       "verified": ok, "evidence_class": ("executed_live_read_only" if arm != "D"
                                                          else "deterministic_control_same_source"),
                       **{k: (round(v, 1) if isinstance(v, float) else v) for k, v in res.items()},
                       "ts": time.time()}
                with out.open("a") as f:
                    f.write(json.dumps(row) + "\n")
                print(rep, gid, name, row.get("status"), ok, res.get("wall_ms"), "ms",
                      res.get("model_calls"), "calls", flush=True)
                time.sleep(0.5)


if __name__ == "__main__":
    main()
