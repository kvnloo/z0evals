#!/usr/bin/env python3
"""Run the scenario x arm x rep matrix, interleaving arms, one live session per run.

python harness/run.py --run-id <id> --reps 5 [--arms omp-live,z0live-realtime] [--scenarios a,b]
Raw per-run artifacts go to $VOICE_EVAL_ROOT/<run-id>/ (private, mode 0700). Each run is a
separate subprocess under `nice -n 10` (live sessions are network/IO-bound, so they do not take the host heavy.lock;
pass --heavy-lock to serialize anyway), gated on >= 4 GiB available memory,
with --gap-s seconds between runs to respect provider limits.
"""
import argparse
import json
import os
import platform
import random
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
SCRATCH = Path(os.environ.get("VOICE_EVAL_SCRATCH", str(Path.home() / ".hermes/profiles/clean/cache/scratch/voice-eval")))
ROOT = Path(os.environ.get("VOICE_EVAL_ROOT", "/mnt/zer0models/workspace/zer0/data/operations/voice-eval"))
LOCK = Path(os.environ.get("HEAVY_LOCK", str(Path.home() / ".hermes/profiles/clean/cache/scratch/heavy.lock")))


def avail_gib():
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) / 1024 / 1024
    return 0.0


def git_head(path):
    try:
        return subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--arms", default=None)
    ap.add_argument("--scenarios", default=None)
    ap.add_argument("--gap-s", type=float, default=4.0)
    ap.add_argument("--timeout-s", type=int, default=300)
    ap.add_argument("--assets", default=str(ROOT / "assets-v1/norm"))
    ap.add_argument("--z0live-worktree", default=str(SCRATCH / "z0live-d1130f9"))
    ap.add_argument("--z0live-data", default=str(ROOT / "broker-data"))
    ap.add_argument("--z0live-base", default="http://127.0.0.1:18791")
    ap.add_argument("--bidi-worktree", default="")
    ap.add_argument("--bidi-data", default="")
    ap.add_argument("--bidi-base", default="")
    ap.add_argument("--seed", type=int, default=20261020)
    ap.add_argument("--heavy-lock", action="store_true")
    a = ap.parse_args()
    os.umask(0o077)
    arms_cfg = json.loads((STUDY / "arms.json").read_text())
    spec = json.loads((STUDY / "scenarios.json").read_text())
    arms = a.arms.split(",") if a.arms else [k for k, v in arms_cfg["arms"].items() if v.get("enabled")]
    scenarios = a.scenarios.split(",") if a.scenarios else [s["id"] for s in spec["scenarios"]]
    out = ROOT / a.run_id
    out.mkdir(parents=True, exist_ok=True)
    asound = SCRATCH / "asound-null.conf"
    if not asound.exists():
        asound.write_text("pcm.!default { type null }\nctl.!default { type hw card 0 }\n")
    omp_pkg = Path.home() / ".bun/install/global/node_modules/@oh-my-pi/pi-coding-agent/package.json"
    run_meta = {
        "run_id": a.run_id,
        "reps": a.reps,
        "arms": arms,
        "scenarios": scenarios,
        "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "host": platform.node(),
        "kernel": platform.release(),
        "cpu_count": os.cpu_count(),
        "omp_version": json.loads(omp_pkg.read_text())["version"] if omp_pkg.exists() else None,
        "z0live_broker_sha": git_head(a.z0live_worktree),
        "z0live_bidi_broker_sha": git_head(a.bidi_worktree) if a.bidi_worktree else None,
        "eval_sha": git_head(STUDY),
        "assets": json.loads((Path(a.assets) / "assets.json").read_text()),
        "scenario_version": spec["version"],
        "gap_s": a.gap_s,
    }
    (out / "run.json").write_text(json.dumps(run_meta, indent=2))
    fmt = {"assets": a.assets, "z0live_worktree": a.z0live_worktree, "z0live_data": a.z0live_data, "z0live_base": a.z0live_base, "asound_null": str(asound), "bidi_worktree": a.bidi_worktree, "bidi_data": a.bidi_data, "bidi_base": a.bidi_base}
    rng = random.Random(a.seed)
    index = out / "index.jsonl"
    for rep in range(1, a.reps + 1):
        order = scenarios[:]
        rng.shuffle(order)
        for sc in order:
            arm_order = arms[:] if (rep % 2) else arms[::-1]
            for arm in arm_order:
                run_dir = out / f"{arm}__{sc}__r{rep}"
                if (run_dir / "meta.json").exists():
                    continue
                while avail_gib() < 4.0:
                    print(f"waiting for memory ({avail_gib():.1f} GiB available)", flush=True)
                    time.sleep(15)
                cfg = arms_cfg["arms"][arm]
                cmd = [c.format(scenario=sc, run_dir=str(run_dir), **fmt) for c in cfg["cmd"]]
                env = dict(os.environ, **{k: v.format(**fmt) for k, v in cfg.get("env", {}).items()})
                t = time.time()
                try:
                    prefix = ["flock", str(LOCK)] if a.heavy_lock else []
                    p = subprocess.run([*prefix, "nice", "-n", "10", *cmd], cwd=STUDY, env=env, capture_output=True, text=True, timeout=a.timeout_s)
                    rc, tail = p.returncode, (p.stdout.strip().splitlines() or [""])[-1]
                    err_tail = p.stderr.strip()[-600:]
                except subprocess.TimeoutExpired:
                    rc, tail, err_tail = "timeout", "", ""
                rec = {"arm": arm, "scenario": sc, "rep": rep, "rc": rc, "wall_s": round(time.time() - t, 1), "summary": tail[:400]}
                if rc != 0 and err_tail:
                    (run_dir).mkdir(parents=True, exist_ok=True)
                    (run_dir / "stderr.txt").write_text(err_tail)
                if not (run_dir / "meta.json").exists():
                    run_dir.mkdir(parents=True, exist_ok=True)
                    (run_dir / "meta.json").write_text(json.dumps({"arm": arm, "scenario": sc, "error": f"driver rc={rc}"}))
                with index.open("a") as f:
                    f.write(json.dumps(rec) + "\n")
                print(json.dumps(rec), flush=True)
                time.sleep(a.gap_s)
    run_meta["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    (out / "run.json").write_text(json.dumps(run_meta, indent=2))


if __name__ == "__main__":
    main()
