#!/usr/bin/env python3
"""A bounded Python coding probe using pinned harness-speed-v1 fixtures."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
UPSTREAM_SHA = "1ec7c67e36cd6dfa57416b7afdd63ada2805158a"
UPSTREAM = HERE.parent / "harness-speed-v1"
TASKS = UPSTREAM / "tasks"
TIERS = {
    "S": ("t01-paginate", "t02-slugify", "t04-cliflag", "t06-duration"),
    "M": ("t03-csvsum", "t05-lru", "t07-rename", "t08-merge"),
    "L": ("h01-reserve", "h02-config", "h03-bus", "h04-money", "h05-calc", "h06-wordstats"),
}


def decode_response(text):
    """Accept plain JSON, a fenced JSON answer, or fx's documented final_output."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        blocks = re.findall(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
        if len(blocks) != 1:
            raise ValueError("Expected one JSON response or one JSON code block")
        data = json.loads(blocks[0])
    if isinstance(data, dict) and "final_output" in data:
        return decode_response(data["final_output"])
    if not isinstance(data, dict) or set(data) != {"files"} or not isinstance(data["files"], dict):
        raise ValueError("Response must contain only a files object")
    return data


def apply_files(repo, files):
    if not files or len(files) > 32:
        raise ValueError("Submit between 1 and 32 production Python files")
    pending = []
    for name, content in files.items():
        if not isinstance(name, str) or not isinstance(content, str):
            raise ValueError("File paths and contents must be strings")
        rel = PurePosixPath(name)
        target = repo / name
        if (not name or rel.is_absolute() or "\\" in name or rel.as_posix() != name
                or any(p in (".", "..") or p.startswith(".") for p in rel.parts)
                or rel.suffix != ".py" or rel.name.startswith("test_") or rel.stem.endswith("_test")
                or rel.name in ("conftest.py", "sitecustomize.py", "usercustomize.py")
                or len(content.encode()) > 100_000):
            raise ValueError(f"Disallowed file: {name}")
        if (not target.parent.is_dir() or target.is_symlink()
                or any(p.is_symlink() for p in target.parents if p != repo and repo in p.parents)
                or not target.resolve().is_relative_to(repo.resolve())
                or (not target.exists() and target.parent == repo)):
            raise ValueError(f"File must stay in an existing production directory: {name}")
        pending.append((target, content))
    for target, content in pending:
        target.write_text(content, encoding="utf-8")


def verify_task(task, repo):
    path = UPSTREAM / "harness" / "verify.py"
    spec = importlib.util.spec_from_file_location("harness_speed_verifier", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.verify(str(TASKS / task), str(repo))
    result["pass"] = result["pass"] and not result["tests_modified"]
    return result


def tier_results(rows, reps):
    if reps < 1:
        raise ValueError("reps must be positive")
    indexed = {}
    for row in rows:
        key = (row["task"], row["rep"])
        if key in indexed:
            raise ValueError(f"Duplicate attempt: {key}")
        indexed[key] = row["status"]
    results = {}
    required = []
    for tier, tasks in TIERS.items():
        required.extend((task, rep) for task in tasks for rep in range(reps))
        statuses = [indexed.get(key) for key in required]
        if "FAIL" in statuses:
            results[tier] = "FAIL"
        elif not any(statuses):
            results[tier] = "NOT_RUN"
        elif all(status == "PASS" for status in statuses):
            results[tier] = "PASS"
        else:
            results[tier] = "INCOMPLETE"
    return results


def validate_command(model, command):
    if command.count("{prompt}") != 1:
        raise ValueError("Command needs exactly one standalone {prompt} argument")
    if ("gpt" in model.lower() or "openai" in model.lower()) and Path(command[0]).name != "fx":
        raise ValueError("GPT probes must use fx")


def prompt_for(task):
    root = TASKS / task
    visible = {str(p.relative_to(root / "repo")): p.read_text()
               for p in sorted((root / "repo").rglob("*.py"))}
    return json.dumps({
        "task": task,
        "instruction": (root / "prompt.txt").read_text().strip(),
        "repo": visible,
        "response_contract": 'Return only JSON: {"files":{"relative/path.py":"complete source"}}. '
                             'Include changed production Python files only. Do not modify tests. '
                             'New files must be inside existing package directories. '
                             'Do not read hidden tests or reference solutions. Do not use tools. '
                             'This is a text-response probe, not an interactive editing task.',
    })


def check_sources():
    manifest = json.loads((HERE / "upstream-files.json").read_text())
    if manifest["source_sha"] != UPSTREAM_SHA:
        raise ValueError("Fixture source revision does not match the protocol")
    expected_tasks = {name for name in manifest["git_blobs"] if name.startswith("studies/harness-speed-v1/tasks/")}
    actual_tasks = {str(path.relative_to(HERE.parent.parent)) for path in TASKS.rglob("*")
                    if path.is_file() and "__pycache__" not in path.parts}
    if actual_tasks != expected_tasks:
        raise ValueError("Fixture file set differs from the pinned source")
    for name, expected in manifest["git_blobs"].items():
        data = (HERE.parent.parent / name).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if actual != expected:
            raise ValueError(f"Pinned upstream file changed: {name}")


def fingerprint():
    paths = [Path(__file__)] + sorted((UPSTREAM / "tasks").rglob("*")) + [UPSTREAM / "harness" / "verify.py"]
    digest = hashlib.sha256()
    for path in paths:
        if path.is_file() and "__pycache__" not in path.parts:
            digest.update(str(path.relative_to(HERE.parent)).encode())
            digest.update(b"\0")
            digest.update(path.read_bytes())
    return digest.hexdigest()


def write_summary(out, model, provider, billing, rows, reps, digest, timeout):
    tiers = tier_results(rows, reps)
    qualifying = reps == 2 and timeout == 180
    result = {"study": "coding-license-v0", "model": model, "provider": provider,
              "billing_attestation": billing, "upstream_sha": UPSTREAM_SHA,
              "probe_sha256": digest, "reps": reps, "timeout": timeout, "tiers": tiers,
              "qualifying_protocol": qualifying,
              "license_granted": {tier: qualifying and status == "PASS" for tier, status in tiers.items()}}
    (out / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = ["| Model | Provider | S | M | L |", "|---|---|---|---|---|"]
    cells = [model, provider] + list(result["tiers"].values())
    lines.append("| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in cells) + " |")
    (out / "summary.md").write_text("\n".join(lines) + "\n")
    return result


def run(args):
    command = args.command
    if command[:1] == ["--"]:
        command = command[1:]
    validate_command(args.model, command)
    if args.reps < 1 or args.timeout < 1:
        raise ValueError("reps and timeout must be positive")
    check_sources()
    out = args.out.resolve()
    # Exclusive output directories prevent accidental overwrites and mixed runs.
    out.mkdir(parents=True, exist_ok=False)
    digest = fingerprint()
    rows = []
    write_summary(out, args.model, args.provider, args.billing, rows, args.reps, digest, args.timeout)
    for tier, tasks in TIERS.items():
        for task in tasks:
            for rep in range(args.reps):
                attempt = out / "attempts" / f"{task}-{rep}"
                repo = attempt / "repo"
                shutil.copytree(TASKS / task / "repo", repo)
                prompt = prompt_for(task)
                (attempt / "prompt.json").write_text(prompt)
                argv = [prompt if part == "{prompt}" else part for part in command]
                (attempt / "command.json").write_text(json.dumps(command) + "\n")
                row = {"model": args.model, "provider": args.provider, "tier": tier,
                       "task": task, "rep": rep, "status": "ERROR", "process_exit": None,
                       "attempt": str(attempt.relative_to(out)), "started_at": time.time()}
                start = time.monotonic()
                try:
                    with (attempt / "response.txt").open("w") as stdout, (attempt / "stderr.txt").open("w") as stderr:
                        proc = subprocess.run(argv, cwd=repo, stdin=subprocess.DEVNULL,
                                              stdout=stdout, stderr=stderr, timeout=args.timeout)
                    row["process_exit"] = proc.returncode
                    if proc.returncode != 0:
                        raise ValueError("Model CLI failed; see stderr.txt")
                    answer = decode_response((attempt / "response.txt").read_text())
                    # Retain tool edits as evidence. Only the JSON submission receives a score.
                    repo.rename(attempt / "cli-repo")
                    shutil.copytree(TASKS / task / "repo", repo)
                    apply_files(repo, answer["files"])
                    verified = verify_task(task, repo)
                    (attempt / "verification.json").write_text(json.dumps(verified) + "\n")
                    row["verified"] = verified
                    row["status"] = "PASS" if verified["pass"] else "FAIL"
                except subprocess.TimeoutExpired:
                    row["error"] = "Model CLI timeout"
                except (OSError, ValueError, TypeError, KeyError) as error:
                    row["error"] = str(error)
                row["elapsed_seconds"] = round(time.monotonic() - start, 3)
                with (out / "results.jsonl").open("a") as stream:
                    stream.write(json.dumps(row) + "\n")
                rows.append(row)
                write_summary(out, args.model, args.provider, args.billing, rows, args.reps, digest, args.timeout)
                print(json.dumps(row), flush=True)
                # Do not burn quota by repeating auth, transport, or response failures.
                if row["status"] == "ERROR":
                    return 2
    result = write_summary(out, args.model, args.provider, args.billing, rows, args.reps, digest, args.timeout)
    return 0 if all(value == "PASS" for value in result["tiers"].values()) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="kind", required=True)
    run_parser = commands.add_parser("run")
    run_parser.add_argument("--model", required=True)
    run_parser.add_argument("--provider", required=True)
    run_parser.add_argument("--billing", choices=("free", "subscription"), required=True,
                            help="Operator attestation, not a billing check. Metered calls are forbidden.")
    run_parser.add_argument("--reps", type=int, default=2)
    run_parser.add_argument("--timeout", type=int, default=180)
    run_parser.add_argument("--out", type=Path, required=True)
    run_parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        return run(args)
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    sys.exit(main())
