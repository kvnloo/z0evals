import os, shutil, subprocess, sys, tempfile, json
tasks_dir, verify = sys.argv[1], sys.argv[2]
bad = 0
for t in sorted(os.listdir(tasks_dir)):
    td = os.path.join(tasks_dir, t); res = {}
    for mode in ("original", "reference"):
        w = tempfile.mkdtemp(); repo = os.path.join(w, "repo"); shutil.copytree(os.path.join(td, "repo"), repo)
        if mode == "reference":
            shutil.copytree(os.path.join(td, "reference"), repo, dirs_exist_ok=True)
        out = subprocess.run([sys.executable, verify, td, repo], capture_output=True, text=True).stdout
        res[mode] = json.loads(out)["pass"]; shutil.rmtree(w)
    ok = res == {"original": False, "reference": True}; bad += not ok
    print(t, res, "OK" if ok else "BAD")
sys.exit(bad)
