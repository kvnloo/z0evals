#!/usr/bin/env python3
"""Frozen coding probes; run tests and inference through fleet-build, never on groot."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "harness-speed-v1"
TIERS = ("S", "M", "L")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def load_policy():
    policy = json.loads((HERE / "policy.json").read_text())
    if tuple(policy["tiers"]) != TIERS or policy["repetitions"] != 1:
        raise ValueError("v0 requires ordered S/M/L tiers and one repetition")
    tasks = [task for tier in policy["tiers"].values() for task in tier["tasks"]]
    models = [model["id"] for model in policy["models"]]
    if len(tasks) != len(set(tasks)) or len(models) != len(set(models)):
        raise ValueError("duplicate task or model")
    costs = json.loads((HERE / "free-cost-evidence.json").read_text())["models"]
    for model in policy["models"]:
        if model["funding"] == "free-catalog-zero":
            cost = costs[model["id"].split("/", 1)[1]]["cost"]
            if cost.get("input") != 0 or cost.get("output") != 0 or any(cost.values()):
                raise ValueError("nonzero or missing model cost evidence")
    expected = json.loads((HERE / "source-sha256.json").read_text())
    actual = {path: digest(SOURCE / path) for path in expected}
    if actual != expected:
        raise ValueError("source fixtures/verifier differ from the frozen source")
    return policy


def process(argv, cwd, seconds, env=None):
    start = time.monotonic()
    try:
        child = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 text=True, start_new_session=True)
    except OSError as exc:
        return {"exit": None, "timeout": False, "stdout": "", "stderr": str(exc),
                "seconds": time.monotonic() - start}
    timed_out = False
    try:
        stdout, stderr = child.communicate(timeout=seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(child.pid, signal.SIGKILL)
        stdout, stderr = child.communicate()
    return {"exit": child.returncode, "timeout": timed_out, "stdout": stdout,
            "stderr": stderr, "seconds": time.monotonic() - start}


def minimal_env(home):
    return {"PATH": os.environ.get("PATH", os.defpath), "HOME": str(home),
            "LANG": "C.UTF-8", "TERM": "dumb"}


def preflight(model, out):
    adapter = model["adapter"]
    result = {"model": model["id"], "ready": False}
    if adapter == "unavailable":
        return result | {"reason": "no verified zero-spend subscription adapter"}
    executable = shutil.which(adapter)
    if not executable:
        return result | {"reason": f"missing executable: {adapter}"}
    result["executable"] = executable
    if adapter == "opencode":
        if model["funding"] != "free-catalog-zero":
            return result | {"reason": "free label has no matching zero-price catalog evidence"}
        # Anonymous free route only. Never load the owner's API keys or provider config.
        home = out / "anonymous-home"
        home.mkdir(exist_ok=True)
        env = minimal_env(home)
        env.update({"XDG_CONFIG_HOME": str(home / "config"),
                    "XDG_DATA_HOME": str(home / "data"),
                    "XDG_CACHE_HOME": str(home / "cache")})
        probe = process([executable, "models", "--standalone"], out, 45, env)
        save(out / "preflight.json", probe)
        listed = model["id"] in probe["stdout"].splitlines()
        return result | {"ready": probe["exit"] == 0 and listed,
                         "reason": "" if probe["exit"] == 0 and listed else
                         "anonymous model inventory unavailable or model absent"}
    argv = ([executable, "--provider", "codex", "status", "--json"] if adapter == "fx"
            else [executable, "auth", "status"])
    probe = process(argv, out, 30)
    try:
        status = json.loads(probe["stdout"])
    except (ValueError, TypeError):
        status = {}
    ready = (status.get("auth") == "Codex subscription" if adapter == "fx" else
             status.get("loggedIn") is True and status.get("authMethod") == "claude.ai"
             and status.get("subscriptionType") in ("max", "pro"))
    # Retain only routing facts, not account identity or credential material.
    result.update(ready=probe["exit"] == 0 and ready,
                  reason="" if probe["exit"] == 0 and ready else "subscription route unverified")
    return result


def command(model, prompt):
    adapter, name = model["adapter"], model["id"].split("/", 1)[1]
    if adapter == "fx":
        return ["fx", "--provider", "codex", "--no-additional-dirs", "--context-limit",
                "skill_catalog_bytes=0", "ask", "--auto", "--no-save", "--json",
                "--model", name, "--effort", "low", "--no-fast", "--no-ultrafast", prompt]
    if adapter == "opencode":
        return ["opencode", "run", "--standalone", "--auto", "--format", "json",
                "--model", model["id"], prompt]
    if adapter == "claude":
        return ["claude", "--print", "--safe-mode", "--model", name, "--output-format", "json",
                "--tools", "Read,Edit,Write,Bash", "--allowedTools", "Read,Edit,Write,Bash",
                "--max-budget-usd", "0", "--no-session-persistence", prompt]
    raise ValueError(f"unsupported adapter: {adapter}")


def safe_copy(source, target):
    # Do not follow a submitted symlink into the verifier or outside the task directory.
    if source.is_symlink():
        raise ValueError("submission directory is a symlink")
    for entry in source.rglob("*"):
        if entry.is_symlink():
            raise ValueError(f"symlink in submission: {entry.relative_to(source)}")
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", ".git"))


def grade(task, submitted, out):
    grading = out / "grading"
    try:
        safe_copy(submitted, grading)
    except ValueError as exc:
        return {"pass": False, "tests_modified": False, "summary": str(exc)}
    home = out / "grader-home"
    home.mkdir()
    check = process([sys.executable, str(SOURCE / "harness/verify.py"),
                     str(SOURCE / "tasks" / task), str(grading)], out, 70, minimal_env(home))
    save(out / "verifier-process.json", check)
    try:
        verdict = json.loads(check["stdout"])
    except ValueError:
        verdict = {"pass": False, "tests_modified": False, "summary": "verifier crashed"}
    verdict["pass"] = check["exit"] == 0 and not check["timeout"] and verdict.get("pass") is True
    return verdict


def probe_task(model, task, tier, seconds, out):
    out.mkdir(parents=True)
    work = out / "submission"
    shutil.copytree(SOURCE / "tasks" / task / "repo", work)
    prompt = (SOURCE / "tasks" / task / "prompt.txt").read_text().strip()
    prompt += ("\nWork only in this task directory. Do not access other directories, credentials,"
               " network services, or reference/hidden solutions. Do not delegate."
               " Do not modify, remove, skip, or replace tests. Finish within the time limit.")
    env = None
    if model["adapter"] == "opencode":
        home = out.parents[1] / "anonymous-home"
        env = minimal_env(home)
        env.update({"XDG_CONFIG_HOME": str(home / "config"),
                    "XDG_DATA_HOME": str(home / "data"),
                    "XDG_CACHE_HOME": str(home / "cache")})
    argv = command(model, prompt)
    execution = process(argv, work, seconds, env)
    save(out / "agent-process.json", execution | {"argv": argv})
    # Keep the original submission, independently grade a separate copy.
    verification = grade(task, work, out)
    passed = (execution["exit"] == 0 and not execution["timeout"]
              and verification["pass"] and not verification["tests_modified"])
    status = "PASS" if passed else "FAIL"
    reason = ""
    if execution["exit"] != 0 and not execution["timeout"]:
        status, reason = "BLOCKED", "agent CLI failed; no completed coding measurement"
    row = {"model": model["id"], "task": task, "tier": tier, "rep": 0,
           "status": status, "reason": reason, "exit": execution["exit"],
           "seconds": execution["seconds"], "timeout": execution["timeout"],
           "verified": verification, "artifact": str(out.name),
           "submission_sha256": {str(p.relative_to(work)): digest(p)
                                 for p in work.rglob("*") if p.is_file() and not p.is_symlink()
                                 and "__pycache__" not in p.parts}}
    save(out / "result.json", row)
    return row


def summarize(policy, rows):
    known_models = {model["id"] for model in policy["models"]}
    task_tiers = {task: tier for tier, rule in policy["tiers"].items() for task in rule["tasks"]}
    for row in rows:
        if (row["model"] not in known_models or row["rep"] != 0
                or task_tiers.get(row["task"]) != row["tier"]
                or row["status"] not in ("PASS", "FAIL", "BLOCKED")):
            raise ValueError("result does not belong to this frozen evaluation")
    cells = []
    for model in policy["models"]:
        required = []
        for tier in TIERS:
            required += policy["tiers"][tier]["tasks"]
            relevant = [r for r in rows if r["model"] == model["id"] and r["task"] in required]
            keys = [(r["task"], r["rep"]) for r in relevant]
            if len(keys) != len(set(keys)):
                raise ValueError("duplicate results cannot grant a license")
            passed = sum(r["status"] == "PASS" for r in relevant)
            failed = any(r["status"] == "FAIL" for r in relevant)
            status = "FAIL" if failed else ("PASS" if passed == len(required) else "BLOCKED")
            cells.append({"model": model["id"], "tier": tier, "status": status,
                          "passed": passed, "required": len(required),
                          "licensed": status == "PASS"})
    return cells


def write_table(policy, rows, out):
    cells = summarize(policy, rows)
    save(out / "matrix.json", cells)
    lines = ["# coding-license-v0 results", "", "PASS grants this study's probe license only.",
             "BLOCKED means not evaluated, not a code failure. No runtime policy was changed.", "",
             "| Model | S | M | L |", "| --- | --- | --- | --- |"]
    for model in policy["models"]:
        values = [f"{c['status']} {c['passed']}/{c['required']}" for c in cells if c["model"] == model["id"]]
        lines.append("| " + " | ".join([model["id"], *values]) + " |")
    (out / "matrix.md").write_text("\n".join(lines) + "\n")
    return cells


def run(policy, out):
    # Exclusive output directory: retries never overwrite evidence or silently reuse rows.
    out.mkdir(parents=True, exist_ok=False)
    save(out / "run.json", {"study": policy["id"], "source_commit": policy["source_commit"],
                           "host": socket.gethostname(), "started_unix": time.time(),
                           "python": sys.version, "runner_sha256": digest(__file__),
                           "policy_sha256": digest(HERE / "policy.json"),
                           "source_hashes_sha256": digest(HERE / "source-sha256.json")})
    rows = []
    try:
        for number, model in enumerate(policy["models"]):
            model_out = out / f"model-{number:02d}"
            model_out.mkdir()
            ready = preflight(model, model_out)
            save(model_out / "route.json", ready)
            for tier, rule in policy["tiers"].items():
                for task in rule["tasks"]:
                    if not ready["ready"]:
                        row = {"model": model["id"], "task": task, "tier": tier, "rep": 0,
                               "status": "BLOCKED", "reason": ready["reason"]}
                    else:
                        row = probe_task(model, task, tier, rule["seconds"], model_out / "tasks" / task)
                    rows.append(row)
                    with (out / "rows.jsonl").open("a") as handle:
                        handle.write(json.dumps(row) + "\n")
                    print(json.dumps(row), flush=True)
    finally:
        cells = write_table(policy, rows, out)
    return 0 if all(c["status"] == "PASS" for c in cells) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    return run(load_policy(), args.out.resolve())


if __name__ == "__main__":
    sys.exit(main())
