#!/usr/bin/env python3
"""Agent version-control evals: one driver per tool, four experiments.

  e1  per-turn checkpoint loop (T3 Code / Hermes seam): replay real commits as
      agent turns, capture a checkpoint after each, then restore and diff.
  e2  parallel workspaces: time and bytes for N ready forks of a dirty tree
      that carries tracked edits, untracked files and an ignored build dir.
  e3  merging parallel edits to the same file: real merges plus replayed
      same-base commit pairs, scored against the human result.
  e4  agent-facing output size of status/diff/log for one dirty state.

Every run appends JSON lines under --out. Nothing here talks to a server or
an LLM. Tools come from $TOOLS/bin (see install_tools.sh).
"""
import argparse
import hashlib
import json
import os
import random
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

BIN = Path(os.environ.get("TOOLS", Path.home() / ".cache/agent-vcs-tools")) / "bin"
ENV = dict(os.environ)
ENV["PATH"] = f"{BIN}:{ENV['PATH']}"
ENV.update(
    GIT_AUTHOR_NAME="bench", GIT_AUTHOR_EMAIL="bench@example.invalid",
    GIT_COMMITTER_NAME="bench", GIT_COMMITTER_EMAIL="bench@example.invalid",
    JJ_USER="bench", JJ_EMAIL="bench@example.invalid",
    OAK_NO_UPDATE_CHECK="1", NO_COLOR="1", TERM="dumb",
)
# jj refuses to snapshot new files over 1 MiB by default (25 tracked files in
# t3code exceed it), which would silently drop them from checkpoints.
_JJ_CFG = Path(tempfile.gettempdir()) / "bench-jj-config.toml"
_JJ_CFG.write_text('[snapshot]\nmax-new-file-size = "256MiB"\n[ui]\npaginate = "never"\n')
ENV["JJ_CONFIG"] = str(_JJ_CFG)
CMD_TIMEOUT = int(os.environ.get("BENCH_CMD_TIMEOUT", "300"))
META_DIRS = {".git", ".jj", ".oak", ".rift"}


def run(cmd, cwd=None, env=None, check=True, inp=None):
    try:
        p = subprocess.run(cmd, cwd=cwd, env=env or ENV, input=inp, capture_output=True,
                           stdin=None if inp is not None else subprocess.DEVNULL, timeout=CMD_TIMEOUT)
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"{cmd!r} in {cwd}: timed out after {CMD_TIMEOUT}s; stderr={(e.stderr or b'')[-400:]!r}")
    if check and p.returncode != 0:
        raise RuntimeError(f"{cmd!r} in {cwd}: rc={p.returncode} {p.stderr.decode(errors='replace')[-800:]}")
    return p


def timed(fn):
    t = time.perf_counter()
    r = fn()
    return (time.perf_counter() - t) * 1000.0, r


def tree_digest(root: Path) -> str:
    """Hash of every (path, content) under root, ignoring VCS metadata."""
    h = hashlib.sha256()
    for dp, dns, fns in os.walk(root):
        dns[:] = sorted(d for d in dns if d not in META_DIRS)
        for fn in sorted(fns):
            p = Path(dp) / fn
            rel = p.relative_to(root).as_posix()
            if p.is_symlink():
                data = ("L" + os.readlink(p)).encode()
            else:
                data = p.read_bytes()
            h.update(rel.encode() + b"\0" + hashlib.sha1(data).digest())
    return h.hexdigest()


def du(path: Path) -> int:
    total = 0
    for dp, _, fns in os.walk(path):
        for fn in fns:
            try:
                total += os.lstat(os.path.join(dp, fn)).st_size
            except FileNotFoundError:
                pass
    return total


def git_src(repo, *args):
    return run(["git", "-C", str(repo), *args]).stdout


def export_tree(repo: Path, rev: str, dest: Path):
    dest.mkdir(parents=True, exist_ok=True)
    arch = run(["git", "-C", str(repo), "archive", "--format=tar", rev]).stdout
    run(["tar", "-x", "-C", str(dest)], inp=arch)


def apply_turn(repo: Path, prev: str, cur: str, wd: Path, turn: int):
    """Make wd's tracked content go from prev to cur, like an agent's edits,
    plus one untracked scratch file per turn."""
    out = git_src(repo, "diff", "--no-renames", "--name-status", "-z", prev, cur).split(b"\0")
    i = 0
    while i < len(out) - 1:
        st, path = out[i].decode(), out[i + 1].decode()
        i += 2
        dst = wd / path
        if st.startswith("D"):
            if dst.exists() or dst.is_symlink():
                dst.unlink()
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        mode = git_src(repo, "ls-tree", cur, "--", path).split()[0].decode()
        blob = git_src(repo, "show", f"{cur}:{path}")
        if dst.is_symlink() or dst.exists():
            dst.unlink()
        if mode == "120000":
            os.symlink(blob.decode(), dst)
        else:
            dst.write_bytes(blob)
            if mode == "100755":
                dst.chmod(0o755)
    scratch = wd / ".agent-scratch"
    scratch.mkdir(exist_ok=True)
    (scratch / f"turn-{turn:03d}.md").write_text(f"notes for turn {turn}\n")


# --------------------------------------------------------------------------
# Checkpoint drivers. init(wd) once; capture(wd, n) -> id; restore(wd, id);
# diff(wd, a, b) -> text; store_bytes(wd).


class GitT3:
    """T3 Code's GitVcsDriver: temp index from HEAD, add -A, write-tree,
    commit-tree, update-ref refs/t3/checkpoints/<n>; restore with
    `git restore --source --worktree --staged` + `git clean -fd`."""
    name = "git-t3"

    def init(self, wd):
        run(["git", "init", "-q"], cwd=wd)
        run(["git", "add", "-A"], cwd=wd)
        run(["git", "commit", "-qm", "base", "--no-verify"], cwd=wd)

    def capture(self, wd, n):
        idx = Path(tempfile.mkdtemp()) / "index"
        env = dict(ENV, GIT_INDEX_FILE=str(idx))
        run(["git", "read-tree", "--reset", "HEAD"], cwd=wd, env=env)
        run(["git", "add", "-A"], cwd=wd, env=env)
        tree = run(["git", "write-tree"], cwd=wd, env=env).stdout.decode().strip()
        c = run(["git", "commit-tree", tree, "-p", "HEAD", "-m", f"checkpoint {n}"], cwd=wd).stdout.decode().strip()
        run(["git", "update-ref", f"refs/t3/checkpoints/{n}", c], cwd=wd)
        shutil.rmtree(idx.parent)
        return c

    def restore(self, wd, cid):
        run(["git", "restore", f"--source={cid}", "--worktree", "--staged", "--", "."], cwd=wd)
        run(["git", "clean", "-fdq", "--", "."], cwd=wd)

    def diff(self, wd, a, b):
        return run(["git", "diff", "--numstat", a, b], cwd=wd).stdout

    def store_bytes(self, wd):
        return du(wd / ".git")


class GitHermes:
    """Hermes' checkpoint_manager: one shadow store (GIT_DIR) outside the
    project with a per-project index; commits on refs/hermes/<hash>."""
    name = "git-hermes"

    def _env(self, wd):
        return dict(ENV, GIT_DIR=str(self.store), GIT_WORK_TREE=str(wd), GIT_INDEX_FILE=str(self.store / "indexes" / "p"))

    def init(self, wd):
        self.store = wd.parent / (wd.name + ".hermes-store")
        run(["git", "init", "-q", "--bare", str(self.store)])
        (self.store / "indexes").mkdir()
        self.parent = None

    def capture(self, wd, n):
        env = self._env(wd)
        run(["git", "add", "-A", "--", "."], cwd=wd, env=env)
        tree = run(["git", "write-tree"], cwd=wd, env=env).stdout.decode().strip()
        args = ["git", "commit-tree", tree, "-m", f"checkpoint {n}"] + (["-p", self.parent] if self.parent else [])
        c = run(args, cwd=wd, env=env).stdout.decode().strip()
        run(["git", "update-ref", "refs/hermes/p", c], cwd=wd, env=env)
        self.parent = c
        return c

    def restore(self, wd, cid):
        env = self._env(wd)
        run(["git", "read-tree", "-u", "--reset", cid], cwd=wd, env=env)
        run(["git", "clean", "-fdq"], cwd=wd, env=env)

    def diff(self, wd, a, b):
        return run(["git", "diff", "--numstat", a, b], cwd=wd, env=self._env(wd)).stdout

    def store_bytes(self, wd):
        return du(self.store)


class Jj:
    """Jujutsu, colocated with git as T3 would run it. The working copy is a
    commit; `jj new` seals it as the checkpoint."""
    name = "jj"

    def init(self, wd):
        run(["jj", "git", "init", "--colocate", "--quiet"], cwd=wd)
        run(["jj", "new", "--quiet"], cwd=wd)

    def capture(self, wd, n):
        run(["jj", "new", "--quiet"], cwd=wd)
        return run(["jj", "log", "--no-graph", "-r", "@-", "-T", "commit_id"], cwd=wd).stdout.decode().strip()

    def restore(self, wd, cid):
        run(["jj", "restore", "--quiet", "--from", cid], cwd=wd)

    def diff(self, wd, a, b):
        return run(["jj", "diff", "--stat", "--from", a, "--to", b], cwd=wd).stdout

    def store_bytes(self, wd):
        return du(wd / ".jj") + du(wd / ".git")


class Oak:
    """Oak, local repository only (no server): `oak commit` is the checkpoint."""
    name = "oak"

    def init(self, wd):
        run(["oak", "init", "."], cwd=wd)
        run(["oak", "commit", "--quiet"], cwd=wd)

    def capture(self, wd, n):
        r = run(["oak", "commit", "--json"], cwd=wd).stdout.decode()
        j = json.loads(r)
        return j["head_after"]

    def restore(self, wd, cid):
        run(["oak", "restore", "-s", cid, "-f"], cwd=wd)

    def diff(self, wd, a, b):
        return run(["oak", "diff", a, b, "--stat"], cwd=wd).stdout

    def store_bytes(self, wd):
        return du(wd / ".oak")


class Butler:
    """GitButler `but`: checkpoints are oplog snapshots (`but oplog snapshot`),
    restored with `but oplog restore`."""
    name = "gitbutler"

    def init(self, wd):
        GitT3().init(wd)
        run(["but", "setup"], cwd=wd)

    def capture(self, wd, n):
        r = run(["but", "oplog", "snapshot", "-m", f"checkpoint {n}", "--json"], cwd=wd).stdout.decode()
        try:
            j = json.loads(r)
            return j.get("id") or j.get("snapshotId") or j.get("sha") or r.strip()
        except json.JSONDecodeError:
            return r.strip().split()[-1]

    def restore(self, wd, cid):
        run(["but", "oplog", "restore", cid, "--force"], cwd=wd)

    def diff(self, wd, a, b):
        return run(["git", "diff", "--numstat", a, b], cwd=wd).stdout

    def store_bytes(self, wd):
        return du(wd / ".git")


DRIVERS = {d.name: d for d in (GitT3, GitHermes, Jj, Oak, Butler)}


def e1(args):
    repo = Path(args.repo)
    revs = git_src(repo, "rev-list", "--first-parent", f"--max-count={args.turns + 1}", "HEAD").decode().split()[::-1]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name in args.tools.split(","):
        drv = DRIVERS[name]()
        base = Path(tempfile.mkdtemp(dir=args.work)) / "wd"
        export_tree(repo, revs[0], base)
        rec = {"exp": "e1", "tool": name, "repo": repo.name, "turns": args.turns, "base": revs[0], "head": revs[-1]}
        try:
            ms, _ = timed(lambda: drv.init(base))
            rec["init_ms"] = ms
            caps, ids, digests = [], [], []
            for t in range(1, len(revs)):
                apply_turn(repo, revs[t - 1], revs[t], base, t)
                ms, cid = timed(lambda: drv.capture(base, t))
                caps.append(ms)
                ids.append(cid)
                digests.append(tree_digest(base))
            rec["capture_ms"] = caps
            k = len(ids) // 2
            ms, _ = timed(lambda: drv.restore(base, ids[k - 1]))
            rec["restore_mid_ms"] = ms
            rec["restore_mid_ok"] = tree_digest(base) == digests[k - 1]
            ms, _ = timed(lambda: drv.restore(base, ids[-1]))
            rec["restore_head_ms"] = ms
            rec["restore_head_ok"] = tree_digest(base) == digests[-1]
            ms, d = timed(lambda: drv.diff(base, ids[0], ids[-1]))
            rec["diff_ms"] = ms
            rec["diff_bytes"] = len(d)
            rec["store_bytes"] = drv.store_bytes(base)
            rec["tree_bytes"] = du(base) - rec["store_bytes"] if name not in ("git-hermes",) else du(base)
            rec["ok"] = True
        except Exception as e:  # record the failure, keep going
            rec["ok"] = False
            rec["error"] = str(e)[-1500:]
        with open(out / "e1.jsonl", "a") as f:
            f.write(json.dumps(rec) + "\n")
        print(name, repo.name, "ok" if rec["ok"] else "FAIL", rec.get("error", "")[:300], flush=True)
        shutil.rmtree(base.parent, ignore_errors=True)
        if name == "git-hermes":
            shutil.rmtree(base.parent.parent / (base.name + ".hermes-store"), ignore_errors=True)


# --------------------------------------------------------------------------
# e2: N ready workspaces of a dirty tree.


def make_dirty_source(repo: Path, rev: str, dest: Path, ignored_files: int):
    export_tree(repo, rev, dest)
    run(["git", "init", "-q"], cwd=dest)
    gi = dest / ".gitignore"
    gi.write_text((gi.read_text() if gi.exists() else "") + "\n/build-cache/\n")
    run(["git", "add", "-A"], cwd=dest)
    run(["git", "commit", "-qm", "base", "--no-verify"], cwd=dest)
    # dirty state: edit 20 tracked files, add 5 untracked files, and an
    # ignored dependency/build dir standing in for node_modules.
    tracked = [p for p in run(["git", "ls-files"], cwd=dest).stdout.decode().split("\n") if p.endswith((".ts", ".py", ".md"))]
    random.Random(7).shuffle(tracked)
    for p in tracked[:20]:
        with open(dest / p, "a") as f:
            f.write("\n// agent edit\n")
    for i in range(5):
        (dest / f"agent-note-{i}.md").write_text(f"untracked {i}\n")
    bc = dest / "build-cache"
    for i in range(ignored_files):
        d = bc / f"pkg{i // 200:03d}"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"m{i}.js").write_text(f"module.exports={i};\n" * 8)


def fidelity(src: Path, ws: Path):
    def has(rel):
        return (ws / rel).exists()
    edited = run(["git", "diff", "--name-only"], cwd=src).stdout.decode().split()
    return {
        "tracked_edits": all((ws / p).exists() and (ws / p).read_bytes() == (src / p).read_bytes() for p in edited[:5]),
        "untracked": has("agent-note-0.md"),
        "ignored": has("build-cache/pkg000/m0.js"),
    }


def fork_git_worktree(src, dst, i):
    # T3 Code's path: a new worktree on a new branch from HEAD (no dirty state)
    run(["git", "worktree", "add", "-q", "-b", f"agent-{i}", str(dst), "HEAD"], cwd=src)


def fork_git_worktree_dirty(src, dst, i):
    # worktree plus copying the dirty tracked/untracked files (no ignored dir)
    fork_git_worktree(src, dst, i)
    stash = run(["git", "stash", "create"], cwd=src).stdout.decode().strip()
    if stash:
        run(["git", "stash", "apply", "-q", stash], cwd=dst)
    for p in run(["git", "ls-files", "--others", "--exclude-standard"], cwd=src).stdout.decode().split("\n"):
        if p:
            (dst / p).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src / p, dst / p)


def fork_jj(src, dst, i):
    if not (src / ".jj").exists():
        run(["jj", "git", "init", "--colocate", "--quiet"], cwd=src)
    run(["jj", "workspace", "add", "--quiet", "--name", f"agent-{i}", str(dst)], cwd=src)


_RIFT_INITED = set()


def fork_rift(src, dst, i):
    if src not in _RIFT_INITED:
        run(["rift", "init"], cwd=src)
        _RIFT_INITED.add(src)
    p = run(["rift", "create", "--name", f"agent-{i}", "--no-hooks"], cwd=src).stdout.decode().strip().splitlines()[-1]
    return Path(p)


def fork_cp_reflink(src, dst, i):
    run(["cp", "-a", "--reflink=auto", str(src), str(dst)])


def fork_oak_clone(src, dst, i):
    # local: clone reusing content from the source checkout
    if not (src / ".oak").exists():
        run(["oak", "init", "."], cwd=src)
        run(["oak", "commit", "--quiet"], cwd=src)
    run(["oak", "clone", "--from", str(src), "--json", str(dst)], cwd=src.parent)


FORKS = {
    "git-worktree": fork_git_worktree,
    "git-worktree+dirty": fork_git_worktree_dirty,
    "jj-workspace": fork_jj,
    "rift": fork_rift,
    "cp-reflink": fork_cp_reflink,
    "oak-clone": fork_oak_clone,
}


def e2(args):
    repo = Path(args.repo)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name in args.tools.split(","):
        root = Path(tempfile.mkdtemp(dir=args.work))
        src = root / "src"
        make_dirty_source(repo, "HEAD", src, args.ignored)
        rec = {"exp": "e2", "tool": name, "repo": repo.name, "forks": args.forks, "ignored_files": args.ignored}
        df0 = shutil.disk_usage(root).used
        try:
            times, paths = [], []
            for i in range(args.forks):
                dst = root / f"ws{i}"
                ms, p = timed(lambda: FORKS[name](src, dst, i))
                times.append(ms)
                paths.append(Path(p) if p else dst)
            rec["fork_ms"] = times
            rec["fidelity"] = fidelity(src, paths[0])
            os.sync()
            rec["disk_used_delta"] = shutil.disk_usage(root).used - df0
            rec["apparent_bytes_per_ws"] = du(paths[0])
            rec["ok"] = True
        except Exception as e:
            rec["ok"] = False
            rec["error"] = str(e)[-1500:]
        with open(out / "e2.jsonl", "a") as f:
            f.write(json.dumps(rec) + "\n")
        print(name, repo.name, "ok" if rec["ok"] else "FAIL", rec.get("error", "")[:300], flush=True)
        shutil.rmtree(root, ignore_errors=True)


# --------------------------------------------------------------------------
# e3: merge corpus. Cases are (base, ours, theirs, expected) file versions.

SRC_EXT = (".ts", ".tsx", ".js", ".py", ".json", ".rs", ".go", ".md", ".yaml", ".yml", ".css", ".toml")


def show(repo, rev, path):
    p = run(["git", "-C", str(repo), "show", f"{rev}:{path}"], check=False)
    return p.stdout if p.returncode == 0 else None


def corpus_real_merges(repo, limit):
    cases = []
    for line in git_src(repo, "rev-list", "--merges", "--parents", "HEAD").decode().splitlines():
        m, p1, p2 = (line.split() + [None, None])[:3]
        if not p2:
            continue
        mb = run(["git", "-C", str(repo), "merge-base", p1, p2], check=False).stdout.decode().strip()
        if not mb:
            continue
        a = set(git_src(repo, "diff", "--name-only", mb, p1).decode().split())
        b = set(git_src(repo, "diff", "--name-only", mb, p2).decode().split())
        for path in sorted(a & b):
            if not path.endswith(SRC_EXT):
                continue
            v = [show(repo, r, path) for r in (mb, p1, p2, m)]
            if None in v or v[1] == v[2]:
                continue
            cases.append({"kind": "real-merge", "repo": repo.name, "merge": m, "path": path, "v": v})
            if len(cases) >= limit:
                return cases
    return cases


def corpus_parallel_pairs(repo, limit, seed=11):
    """Two consecutive first-parent commits that touch the same file, replayed
    as if both started from the first one's parent: ours = C1's file,
    theirs = C2's change alone on the old base, expected = C2's file."""
    revs = git_src(repo, "rev-list", "--first-parent", "HEAD").decode().split()
    pairs = list(zip(revs[1:], revs[:-1]))  # (c1, c2) with c2 child of c1
    random.Random(seed).shuffle(pairs)
    cases = []
    for c1, c2 in pairs:
        par = git_src(repo, "rev-parse", f"{c1}^").decode().strip() if run(["git", "-C", str(repo), "rev-parse", "-q", "--verify", f"{c1}^"], check=False).returncode == 0 else None
        if not par:
            continue
        f1 = set(git_src(repo, "diff", "--name-only", par, c1).decode().split())
        f2 = set(git_src(repo, "diff", "--name-only", c1, c2).decode().split())
        for path in sorted(f1 & f2):
            if not path.endswith(SRC_EXT):
                continue
            base, ours, exp = show(repo, par, path), show(repo, c1, path), show(repo, c2, path)
            if base is None or ours is None or exp is None:
                continue
            # theirs = C2's delta (c1 -> c2) replayed onto base with a clean
            # 3-way merge; skip when git itself cannot build that version.
            with tempfile.TemporaryDirectory() as td:
                t = Path(td)
                (t / "cur").write_bytes(base)
                (t / "o").write_bytes(ours)
                (t / "x").write_bytes(exp)
                r = run(["git", "merge-file", "-p", str(t / "cur"), str(t / "o"), str(t / "x")], check=False)
            if r.returncode != 0:
                continue
            theirs = r.stdout
            if theirs in (base, ours) or theirs == exp:
                continue
            cases.append({"kind": "parallel-pair", "repo": repo.name, "c1": c1, "c2": c2, "path": path, "v": [base, ours, theirs, exp]})
            if len(cases) >= limit:
                return cases
    return cases


def norm(b):
    return b"\n".join(l.rstrip() for l in b.replace(b"\r\n", b"\n").strip().split(b"\n"))


MARKERS = (b"<<<<<<<", b">>>>>>>")


def merge_git(t, ext):
    r = run(["git", "merge-file", "-p", "--diff3", str(t / f"ours{ext}"), str(t / f"base{ext}"), str(t / f"theirs{ext}")], check=False)
    return r.returncode == 0, r.stdout


def merge_git_zdiff3_histogram(t, ext):
    r = run(["git", "merge-file", "-p", "--zdiff3", "--diff-algorithm=histogram", str(t / f"ours{ext}"), str(t / f"base{ext}"), str(t / f"theirs{ext}")], check=False)
    return r.returncode == 0, r.stdout


def merge_mergiraf(t, ext):
    r = run(["mergiraf", "merge", str(t / f"base{ext}"), str(t / f"ours{ext}"), str(t / f"theirs{ext}"), "-o", str(t / f"out{ext}")], check=False)
    data = (t / f"out{ext}").read_bytes() if (t / f"out{ext}").exists() else r.stdout
    return r.returncode == 0 and not any(m in data for m in MARKERS), data


def merge_weave(t, ext):
    # weave-driver follows git's merge driver contract: %O %A %B, result in %A
    a = t / f"out{ext}"
    r = run(["weave-driver", str(t / f"base{ext}"), str(t / f"ours{ext}"), str(t / f"theirs{ext}"), "-o", str(a), "-l", "7", "-p", f"file{ext}"], check=False)
    data = a.read_bytes() if a.exists() else b""
    return r.returncode == 0 and not any(m in data for m in MARKERS), data


MERGERS = {"git-diff3": merge_git, "git-zdiff3-histogram": merge_git_zdiff3_histogram, "mergiraf": merge_mergiraf, "weave": merge_weave}


def e3(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cases = []
    for repo in args.repo.split(","):
        repo = Path(repo)
        cases += corpus_real_merges(repo, args.limit)
        cases += corpus_parallel_pairs(repo, args.limit)
    print("cases", len(cases), flush=True)
    with open(out / "e3.jsonl", "a") as f:
        for c in cases:
            ext = Path(c["path"]).suffix
            with tempfile.TemporaryDirectory() as td:
                t = Path(td)
                for nm, data in zip(("base", "ours", "theirs"), c["v"][:3]):
                    (t / f"{nm}{ext}").write_bytes(data)
                expected = c["v"][3]
                row = {k: c[k] for k in c if k != "v"}
                row["bytes"] = len(expected)
                for mname in args.tools.split(","):
                    try:
                        ms, (clean, data) = timed(lambda: MERGERS[mname](t, ext))
                        row[mname] = {"clean": clean, "exact": clean and norm(data) == norm(expected), "ms": round(ms, 2)}
                    except Exception as e:
                        row[mname] = {"error": str(e)[-300:]}
                f.write(json.dumps(row) + "\n")


# --------------------------------------------------------------------------
# e4: output size of the read commands an agent runs most.


def e4(args):
    repo = Path(args.repo)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(dir=args.work))
    src = root / "src"
    make_dirty_source(repo, "HEAD", src, 50)
    cmds = {
        "git": [["git", "status"], ["git", "status", "--porcelain=v2"], ["git", "diff"], ["git", "diff", "--stat"], ["git", "log", "-n", "10"]],
        "jj": [["jj", "status"], ["jj", "diff"], ["jj", "diff", "--stat"], ["jj", "log", "-n", "10"]],
        "oak": [["oak", "status"], ["oak", "status", "--json", "--compact"], ["oak", "diff", "--print"], ["oak", "diff", "--stat"], ["oak", "agent", "state", "--json", "--compact"], ["oak", "log"]],
        "gitbutler": [["but", "status"], ["but", "status", "--json"], ["but", "diff"]],
    }
    rows = []
    for tool, cl in cmds.items():
        ws = root / tool
        shutil.copytree(src, ws, symlinks=True)
        try:
            if tool == "jj":
                run(["jj", "git", "init", "--colocate", "--quiet"], cwd=ws)
            elif tool == "oak":
                shutil.rmtree(ws / ".git")
                (ws / ".git").mkdir()  # placeholder removed below
                shutil.rmtree(ws / ".git")
                # Oak needs a base checkpoint: rebuild the clean tree first.
                dirty = {p: (ws / p).read_bytes() for p in run(["git", "diff", "--name-only"], cwd=src).stdout.decode().split()}
                run(["git", "-C", str(src), "stash", "-q"])
                clean = root / "oak-clean"
                shutil.copytree(src, clean, symlinks=True, ignore=shutil.ignore_patterns(".git"))
                run(["git", "-C", str(src), "stash", "pop", "-q"])
                shutil.rmtree(ws)
                clean.rename(ws)
                run(["oak", "init", "."], cwd=ws)
                run(["oak", "commit", "--quiet"], cwd=ws)
                for p, data in dirty.items():
                    (ws / p).write_bytes(data)
            elif tool == "gitbutler":
                run(["but", "setup"], cwd=ws)
        except Exception as e:
            rows.append({"exp": "e4", "tool": tool, "setup_error": str(e)[-400:]})
            continue
        for c in cl:
            p = run(c, cwd=ws, check=False)
            rows.append({"exp": "e4", "tool": tool, "cmd": " ".join(c), "rc": p.returncode, "stdout_bytes": len(p.stdout), "stderr_bytes": len(p.stderr)})
    with open(out / "e4.jsonl", "a") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    for r in rows:
        print(r)
    shutil.rmtree(root, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exp", choices=["e1", "e2", "e3", "e4"])
    ap.add_argument("--repo", required=True)
    ap.add_argument("--tools", required=True)
    ap.add_argument("--out", default="results")
    ap.add_argument("--work", default=None)
    ap.add_argument("--turns", type=int, default=30)
    ap.add_argument("--forks", type=int, default=4)
    ap.add_argument("--ignored", type=int, default=20000)
    ap.add_argument("--limit", type=int, default=150)
    args = ap.parse_args()
    if args.work:
        Path(args.work).mkdir(parents=True, exist_ok=True)
    {"e1": e1, "e2": e2, "e3": e3, "e4": e4}[args.exp](args)


if __name__ == "__main__":
    main()
