#!/usr/bin/env python3
"""repo-navigation-v0: which repo layout lets a fresh agent find the factory's tools fastest and correctly.

Same code, four layouts (built from the live tree into a private data dir, never committed):
  L0 asis     loose ops dirs + ~/.local/bin + oss-factory main + feature-branch worktrees (today)
  L1 moved    factory code consolidated into one oss-factory repo, existing prose AGENTS.md only
  L2 moved+map  L1 plus a generated MAP.md (one line per tool: path, purpose, how to run)
  L3 asis+map   L0 plus the same generated MAP.md at the root, pointing at the scattered paths
A fresh Claude Code agent (no user CLAUDE.md, skills, plugins or memory; bwrap with only /work visible)
answers 8 lookup questions whose answers are known. We record correct, turns, tokens and seconds.

  nav_study.py build                 build the layouts under $NAV_DATA
  nav_study.py run [--model haiku] [--reps 2] [--jobs 4] [--layouts L0,L1,L2,L3] [--set v1]
  nav_study.py summary               aggregate runs.jsonl -> ../data/summary.json
"""
from __future__ import annotations

import json, os, re, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HOME = Path.home()
OPS = Path("/mnt/zer0models/workspace/zer0/data/operations")
DATA = Path(os.environ.get("NAV_DATA", OPS / "repo-nav-v0"))
STUDY = Path(__file__).resolve().parent.parent
OSSF = Path(os.environ.get("OSSF_CLONE", "/home/kvn/.hermes/profiles/clean/cache/scratch/ossf"))
F3 = Path("/mnt/zer0models/worktrees/oss-factory-f3-contrib")
VSR = Path("/mnt/zer0models/z0-wt/z0int-vllm-sr-turbo/deploy/vllm-sr")
TEXT = {".py", ".sh", ".md", ".mjs", ".ts", ".js", ".yaml", ".yml", ".toml", ".txt", ""}
SKIP = {".git", "node_modules", ".venv", "venv", "__pycache__", "runs", "replies", "tmp", "repo-nav-v0", "src",
        "worktrees", "dist", "build", "cache"}

QUESTIONS = [
    ("q1", "In the Hermes upstream loop, how many upstream actions are allowed per author within 24 hours, and in which file is that set?",
     [r"planner\.py", r"\b(1|one)\b"]),
    ("q2", "By default, how many ChatGPT app sends per hour are allowed, and which file enforces it?",
     [r"pace\.py", r"\b50\b"]),
    ("q3", "Which command queues GitHub replies that need a recheck or an answer so the upstream loop can follow up on them?",
     [r"gh-feedback-watch", r"followups"]),
    ("q4", "From the command line, how do you call one specific named free-tier backend (for example groq-gpt-oss-20b) through the local router?",
     [r"free_pool\.py", r"\bask\b"]),
    ("q5", "After the DeepSeek app answers 'too frequent', how does the send quota change, and which file does that?",
     [r"ds_pace\.py", r"(quota\s*-\s*2|minus 2|by 2|decrease[sd]? (it )?by two|-2\b|reduc\w* by 2|lower\w* by 2)"]),
    ("q6", "Which file classifies a contribution and decides whether it may go upstream (the F3 contribution gate)?",
     [r"upstream_contrib\.py"]),
    ("q7", "How long are GitHub /notifications responses cached by the local GitHub API cache, and where is that configured?",
     [r"ghcache\.py", r"\b60\b"]),
    ("q8", "Under the factory's human-in-the-loop rules, do worker-authored messages posted from Kevin's GitHub account count as human approval? Name the file that says so.",
     [r"HITL\.md", r"\b(no|not|never|don't|do not)\b"]),
]
# v1: capability questions with no file names in them (how agents actually start: "is there a tool for X?")
QUESTIONS_V1 = [
    ("c1", "I want to send one prompt to several free-tier LLMs at once and compare their answers. Which existing tool should I use, and how?",
     [r"free_pool", r"fanout|ask"]),
    ("c2", "Before posting on GitHub, I want to avoid spamming the same maintainer or posting at night. Which existing code already enforces that, and what are the limits?",
     [r"planner\.py", r"24|quiet"]),
    ("c3", "Our agents keep hitting the GitHub API rate limit. Is there already something that shares and caches GitHub reads between agents? Which file?",
     [r"ghcache"]),
    ("c4", "Is there an existing check that a Bend law proof agrees with its Python twin? Which script runs it?",
     [r"verify\.py"]),
    ("c5", "How does the system decide when the next DeepSeek phone message may be sent? Name the file.",
     [r"ds_pace\.py"]),
    ("c6", "I need to find out quickly when a human replies to one of our GitHub comments. What existing tool does that?",
     [r"gh-feedback-watch"]),
]
PROMPT = ("/work holds the code of a software factory. Answer this question using only files under /work: {q}\n"
          "End with one line `ANSWER: <file path> - <value or command>`.")


# ---------------------------------------------------------------- build

def copy_tree(src: Path, dst: Path, skip=SKIP, exclude=(), cap=None, depth=99):
    """Text files only. cap/depth bound each top-level folder so noise keeps its breadth but stays copyable."""
    n, per = 0, {}
    for root, ds, fs in os.walk(src):
        rel = Path(root).relative_to(src).parts
        ds[:] = [d for d in ds if d not in skip and not d.startswith(".") and os.path.join(root, d) not in exclude
                 and len(rel) < depth]
        top = rel[0] if rel else ""
        for f in fs:
            if cap and per.get(top, 0) >= cap:
                break
            p = Path(root) / f
            if p.suffix not in TEXT or ".bak" in f or p.is_symlink():
                continue
            try:
                if p.stat().st_size > 100_000:
                    continue
                b = p.read_bytes()
            except OSError:
                continue
            if b"\0" in b[:2048]:
                continue
            out = dst / p.relative_to(src)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(b)
            n += 1
            per[top] = per.get(top, 0) + 1
    return n


def git_tree(repo: Path, ref: str, dst: Path):
    dst.mkdir(parents=True, exist_ok=True)
    a = subprocess.run(["git", "-C", str(repo), "archive", ref], capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(dst)], input=a, check=True)


def rewrite(root: Path, pairs: list[tuple[str, str]]):
    for p in root.rglob("*"):
        if p.is_file():
            try:
                s = p.read_text()
            except (UnicodeDecodeError, OSError):
                continue
            t = s
            for a, b in pairs:
                t = t.replace(a, b)
            if t != s:
                p.write_text(t)


def purpose(p: Path) -> str:
    try:
        s = p.read_text(errors="ignore")[:3000]
    except OSError:
        return ""
    if p.suffix == ".md":
        m = re.search(r"^#+\s*(.+)$", s, re.M)
        return m.group(1).strip()[:120] if m else ""
    m = re.search(r'"""\s*(.+?)(?:\n\n|""")', s, re.S) or re.search(r"^(?://|#)(?!!)\s*(\S.+)$", s, re.M)
    return re.sub(r"\s+", " ", m.group(1)).strip()[:140] if m else ""


def gen_map(roots: list[Path], base: Path, title: str) -> str:
    """Deterministic map: one line per tool or doc (path, purpose, how to run). Regenerate, never hand-edit."""
    lines = [f"# MAP: {title}", "", "Generated from file docstrings. One line per tool: `path` - purpose.", ""]
    for r in roots:
        files = []
        for p in sorted(r.rglob("*")):
            if not p.is_file() or "test" in p.name or "/fixtures/" in str(p):
                continue
            exe = p.suffix in {".py", ".sh", ".mjs"} or (p.suffix == "" and os.access(p, os.X_OK))
            doc = p.suffix == ".md" and p.parent == r or p.name.isupper() and p.suffix == ".md"
            if exe or doc:
                files.append(p)
        groups: dict[Path, list[Path]] = {}
        for p in files:
            groups.setdefault(p.parent, []).append(p)
        for d, ps in groups.items():
            if len(ps) > 25:  # generated briefs/fixtures: one line for the folder
                lines.append(f"- `{d.relative_to(base)}/` ({len(ps)} files) - {purpose(ps[0])}")
                continue
            for p in ps:
                run = " (run: `python3 " + str(p.relative_to(base)) + " --help`)" if p.suffix == ".py" and "__main__" in p.read_text(errors="ignore") else ""
                lines.append(f"- `{p.relative_to(base)}` - {purpose(p)}{run}")
    return "\n".join(lines) + "\n"


def build():
    if DATA.exists():
        shutil.rmtree(DATA / "layouts", ignore_errors=True)
    lay = DATA / "layouts"
    cd = OPS / "chatgpt-driver"
    bins = [p for p in (HOME / ".local/bin").iterdir() if p.is_file() and not p.is_symlink()]
    pairs_asis = [(str(OPS), "/work/ops"), (str(HOME / ".local/bin"), "/work/bin"), ("~/.local/bin", "/work/bin"),
                  (str(F3), "/work/worktrees/oss-factory-f3-contrib"),
                  ("/mnt/zer0models/z0-wt/z0int-vllm-sr-turbo", "/work/worktrees/z0int-vllm-sr-turbo")]
    pairs_moved = [(str(cd), "/work/oss-factory/drivers/chatgpt-app"), (str(HOME / ".local/bin/gh-feedback-watch"),
                   "/work/oss-factory/tools/gh-feedback-watch"), ("~/.local/bin/gh-feedback-watch", "/work/oss-factory/tools/gh-feedback-watch"),
                   (str(F3), "/work/oss-factory"), ("/mnt/zer0models/z0-wt/z0int-vllm-sr-turbo", "/work/z0intelligence")] + pairs_asis[:3]

    def common(w: Path, moved: bool):
        n = copy_tree(OPS, w / "ops", exclude={str(cd)}, cap=150, depth=4)  # noise: every ops folder, bounded
        if not moved:
            copy_tree(cd, w / "ops/chatgpt-driver")
        for b in bins:
            if moved and b.name == "gh-feedback-watch":
                continue
            try:
                s = b.read_bytes()
            except OSError:
                continue
            if b"\0" not in s[:2048] and len(s) < 100_000:
                (w / "bin").mkdir(parents=True, exist_ok=True)
                (w / "bin" / b.name).write_bytes(s)
                os.chmod(w / "bin" / b.name, 0o755)
        return n

    for name in ("L0", "L3"):
        w = lay / name
        common(w, False)
        git_tree(OSSF, "origin/main", w / "oss-factory")
        git_tree(OSSF, "origin/wip/factory/integrate-20261020-20261105", w / "worktrees/oss-factory-integrate")
        git_tree(F3, "HEAD", w / "worktrees/oss-factory-f3-contrib")
        copy_tree(VSR, w / "worktrees/z0int-vllm-sr-turbo/deploy/vllm-sr")
        rewrite(w, pairs_asis)
    for name in ("L1", "L2"):
        w = lay / name
        common(w, True)
        git_tree(OSSF, "origin/wip/factory/integrate-20261020-20261105", w / "oss-factory")
        git_tree(F3, "HEAD", w / "oss-factory")  # overlay the F3 gate files
        copy_tree(cd, w / "oss-factory/drivers/chatgpt-app")
        (w / "oss-factory/tools").mkdir(parents=True, exist_ok=True)
        shutil.copy(HOME / ".local/bin/gh-feedback-watch", w / "oss-factory/tools/gh-feedback-watch")
        copy_tree(VSR, w / "z0intelligence/deploy/vllm-sr")
        rewrite(w, pairs_moved)
    w = lay / "L2" / "oss-factory"
    (w / "MAP.md").write_text(gen_map([w, lay / "L2/z0intelligence"], lay / "L2", "oss-factory and the router"))
    ag = w / "AGENTS.md"
    ag.write_text("Start with MAP.md: every tool in this repo, what it does and how to run it.\n\n" + ag.read_text())
    w = lay / "L3"
    roots = [w / "oss-factory", w / "worktrees/oss-factory-integrate", w / "worktrees/oss-factory-f3-contrib",
             w / "worktrees/z0int-vllm-sr-turbo", w / "ops/chatgpt-driver"]
    m = gen_map(roots, w, "factory tools (scattered)")
    m += "- `bin/gh-feedback-watch` - " + purpose(w / "bin/gh-feedback-watch") + "\n"
    (w / "MAP.md").write_text(m)
    for p in sorted(lay.iterdir()):
        print(p.name, sum(1 for _ in p.rglob("*") if _.is_file()), "files")
    for n in ("L2/oss-factory/MAP.md", "L3/MAP.md"):
        print(n, len((lay / n).read_text().splitlines()), "lines")


# ---------------------------------------------------------------- run

def sandbox(layout: Path) -> list[str]:
    ch = HOME / ".claude"
    real = ch.resolve()
    exe = (HOME / ".local/bin/claude").resolve()
    a = ["bwrap", "--ro-bind", "/usr", "/usr", "--symlink", "usr/lib", "/lib", "--symlink", "usr/lib64", "/lib64",
         "--symlink", "usr/bin", "/bin", "--symlink", "usr/bin", "/sbin", "--ro-bind", "/etc", "/etc",
         "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--tmpfs", str(HOME),
         "--bind", str(real), str(real), "--symlink", str(real), str(ch),
         "--bind", str(HOME / ".claude.json"), str(HOME / ".claude.json"),
         "--ro-bind", str(exe), str(exe), "--ro-bind", str(layout), "/work", "--chdir", "/work"]
    for d in ("agents", "plugins", "skills", "projects", "commands", "rules"):  # no user memory/skills/plugins
        if (real / d).exists():
            a += ["--tmpfs", str(real / d)]
    if (real / "CLAUDE.md").exists():
        a += ["--ro-bind", "/dev/null", str(real / "CLAUDE.md")]
    return a + [str(exe)]


ALLQ = QUESTIONS + QUESTIONS_V1


def run_one(layout: str, qid: str, q: str, model: str, rep: int) -> dict:
    cmd = sandbox(DATA / "layouts" / layout) + [
        "-p", PROMPT.format(q=q), "--model", model, "--output-format", "json", "--setting-sources", "project",
        "--strict-mcp-config", "--no-session-persistence", "--max-turns", "40",
        "--allowedTools", "Read,Grep,Glob,Bash(ls:*),Bash(find:*),Bash(grep:*),Bash(rg:*),Bash(cat:*),Bash(head:*),Bash(sed:*)",
        "--disallowedTools", "WebFetch,WebSearch,Task,Write,Edit"]
    t = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    try:
        j = json.loads(p.stdout)
    except json.JSONDecodeError:
        j = {"result": p.stdout[-500:] + p.stderr[-500:], "is_error": True}
    ans = j.get("result") or ""
    keys = dict((x[0], x[2]) for x in ALLQ)[qid]
    final = (re.findall(r"ANSWER:.*", ans) or [ans])[-1]
    u = j.get("usage") or {}
    return {"layout": layout, "q": qid, "model": model, "rep": rep, "secs": round(time.time() - t, 1),
            "turns": j.get("num_turns"), "correct": all(re.search(k, ans, re.I) for k in keys),
            "correct_final": all(re.search(k, final, re.I) for k in keys),
            "in_tok": (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0),
            "out_tok": u.get("output_tokens"), "error": bool(j.get("is_error")), "final": final[:300]}


def run(model="haiku", reps=2, jobs=4, layouts=("L0", "L1", "L2", "L3"), qset=None):
    qs = QUESTIONS_V1 if qset == "v1" else QUESTIONS
    out = DATA / "runs.jsonl"
    done = set()
    if out.exists():
        for l in out.open():
            r = json.loads(l)
            done.add((r["layout"], r["q"], r["model"], r["rep"]))
    todo = [(L, qid, q, model, r) for r in range(reps) for qid, q, _ in qs for L in layouts
            if (L, qid, model, r) not in done]
    print(len(todo), "runs")
    with ThreadPoolExecutor(jobs) as ex, out.open("a") as f:
        for r in ex.map(lambda a: run_one(*a), todo):
            f.write(json.dumps(r) + "\n"); f.flush()
            print(r["layout"], r["q"], r["rep"], "OK " if r["correct"] else "BAD", r["turns"], r["secs"], "s", r["final"][:90])


def summary():
    rows = [json.loads(l) for l in (DATA / "runs.jsonl").open()]
    agg = {}
    for r in rows:
        k = f'{r["model"]}/{r["layout"]}'
        a = agg.setdefault(k, {"n": 0, "correct": 0, "turns": [], "secs": [], "in_tok": []})
        a["n"] += 1; a["correct"] += r["correct"]
        a["turns"].append(r["turns"] or 0); a["secs"].append(r["secs"]); a["in_tok"].append(r["in_tok"])
    med = lambda v: sorted(v)[len(v) // 2]
    res = {k: {"n": a["n"], "accuracy": round(a["correct"] / a["n"], 2), "median_turns": med(a["turns"]),
               "median_secs": med(a["secs"]), "median_in_tok": med(a["in_tok"])} for k, a in sorted(agg.items())}
    per_q = {}
    for r in rows:
        per_q.setdefault(r["q"], {}).setdefault(r["layout"], []).append(int(r["correct"]))
    res["per_question_correct"] = {q: {L: f"{sum(v)}/{len(v)}" for L, v in sorted(d.items())} for q, d in sorted(per_q.items())}
    (STUDY / "data").mkdir(exist_ok=True)
    (STUDY / "data/summary.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    a = sys.argv[1:]
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    if a[:1] == ["build"]:
        build()
    elif a[:1] == ["run"]:
        run(opt("--model", "haiku"), int(opt("--reps", 2)), int(opt("--jobs", 4)), tuple(opt("--layouts", "L0,L1,L2,L3").split(",")), opt("--set", None))
    elif a[:1] == ["summary"]:
        summary()
    else:
        print(__doc__)
