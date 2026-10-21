#!/usr/bin/env python3
"""Independent task verifier. Restores the task's original visible tests over whatever the agent
left, adds the hidden tests, and runs stdlib unittest. Pass = every test passes.

    python3 verify.py <task_dir> <work_repo>   -> prints one JSON line
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest() if os.path.exists(path) else None


def verify(task_dir, work):
    repo = os.path.join(task_dir, "repo")
    tests_modified = False
    for root, _dirs, files in os.walk(repo):
        for name in files:
            if name.startswith("test_") and name.endswith(".py"):
                rel = os.path.relpath(os.path.join(root, name), repo)
                if sha(os.path.join(work, rel)) != sha(os.path.join(repo, rel)):
                    tests_modified = True
                os.makedirs(os.path.dirname(os.path.join(work, rel)), exist_ok=True)
                shutil.copyfile(os.path.join(repo, rel), os.path.join(work, rel))
    shutil.copyfile(os.path.join(task_dir, "hidden", "test_hidden.py"), os.path.join(work, "test_hidden.py"))
    env = {k: v for k, v in os.environ.items() if k in ("PATH", "HOME", "LANG")}
    try:
        p = subprocess.run([sys.executable, "-m", "unittest", "discover", "-p", "test_*.py"], cwd=work,
                           capture_output=True, text=True, timeout=60, env=env)
        tail = p.stderr.strip().splitlines()[-1:] if p.stderr else []
        ok = p.returncode == 0
    except subprocess.TimeoutExpired:
        ok, tail = False, ["timeout"]
    return {"pass": ok, "tests_modified": tests_modified, "summary": tail[0] if tail else ""}


if __name__ == "__main__":
    print(json.dumps(verify(sys.argv[1], sys.argv[2])))
