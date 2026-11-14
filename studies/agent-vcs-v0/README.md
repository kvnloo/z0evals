# agent-vcs-v0: five "better git for agents" tools on T3 Code and Hermes seams

Status: draft. Local, reproducible micro-benchmarks. No LLM calls, no servers,
no accounts. Every number here is a reproduced measurement on one host; none is
an agent-outcome claim.

## Question

T3 Code and Hermes both version agent work with plain git today:

- **T3 Code** (`apps/server/src/vcs/GitVcsDriver*.ts`, pinned below) captures a
  checkpoint after every turn: temp index from `HEAD`, `git add -A`,
  `write-tree`, `commit-tree`, `update-ref refs/t3/checkpoints/<n>`; restores
  with `git restore --source --worktree --staged` + `git clean -fd`. Parallel
  threads get `git worktree add`.
- **Hermes** (`tools/checkpoint_manager.py`, pinned below) snapshots the
  working directory into one shared shadow store (`GIT_DIR` outside the
  project, per-project index) before file-mutating tools, and rolls back with
  `read-tree -u --reset`.

Which of the new agent-oriented VCS tools could replace or sit beside those
seams, and what do they cost on our real repositories?

## How the five were chosen

The landscape scan (GitHub search, named-repo API lookups, Codeberg, GitLab,
HN Algolia, vendor docs; ~700 candidates) is summarised in the post. A tool made
the cut only if it (1) maps onto a seam T3 Code or Hermes already has, (2)
ships a Linux x86_64 binary that runs offline without an account, and (3) is
under active development (commits in the last 30 days).

| Seam | Tool under test | Version | Why it, and not the neighbours |
|---|---|---|---|
| per-turn checkpoint + parallel workspaces | **Jujutsu** (`jj`) | v0.46.0 | working copy is a commit, op log, `jj workspace`; the most-used agent VCS; git-colocated so T3/Hermes keep git |
| per-turn checkpoint + parallel branches | **GitButler** (`but`) | installer "latest" (0.23.x) | oplog snapshots/restore and parallel branches in one worktree; vendor of vcbench |
| checkpoint + agent-facing CLI | **Oak** | v0.109.1 | the only new VCS built for agents with a local mode: BLAKE3/CDC store, `--json` everywhere, `oak agent state` |
| parallel workspaces | **rift** | v0.0.13 | copy-on-write workspace forks; the closest open peer to LayerFS for "N agents, one tree" |
| merging parallel agents' edits | **weave** | v0.7.1 | entity-level (tree-sitter) merge driver built for agents |

Baselines: T3's and Hermes' own git paths, `git worktree` (with and without
carrying dirty state), `cp -a --reflink=auto`, `git merge-file` (diff3 and
zdiff3+histogram), and **mergiraf** v0.20.0 as the mature structured-merge
reference.

Not selected, with the reason: Epic Lore (game/binary-asset focus, no agent
seam we have), Entire (server closed; CLI is a provenance layer, not a VCS),
Scion clones gitai/openscion (server-centric alpha), Sapling/EdenFS (monorepo
virtual FS; heavy setup for repos our size), Pijul (no git interop for our
checkouts), Lix (embeddable SDK, not a CLI for code trees), Turso AgentFS and
container-use (stalled), Radicle/Tangled (forges — they change hosting, not the
local seam), hosted forges (Cursor Origin, code.storage, Relace, Freestyle:
closed services).

## Experiments

`scripts/bench.py` (one driver per tool; JSONL out):

- **e1 — checkpoint loop.** Replay the last N first-parent commits of a fixture
  repo as N agent turns (plus one untracked scratch file per turn). Capture a
  checkpoint after each turn; restore the middle one and the last one and check
  the restored tree hash; diff first..last. Metrics: capture/restore/diff ms,
  store bytes, restore correctness.
- **e2 — parallel workspaces.** From a dirty tree (20 edited tracked files, 5
  untracked, an ignored `build-cache/` standing in for `node_modules`), create K
  ready workspaces. Metrics: ms per fork, disk delta, and fidelity (does the fork
  carry tracked edits / untracked files / ignored files).
- **e3 — merge corpus.** Real two-parent merges plus replayed same-base pairs of
  consecutive commits touching the same file, scored against the human result.
  Metrics: clean-merge rate, exact-match rate, ms.
- **e4 — agent-facing output.** Bytes of status/diff/log output for one dirty
  state, per tool (what an agent reads into context).

## Sources (pinned)

| Repo | Commit | Role |
|---|---|---|
| pingdotgg/t3code | `cefb544af3c98224874419198c0359b652ca3c94` | fixture + checkpoint seam |
| NousResearch/hermes-agent | `c314285f077e91937c995d419b9fa40af9eb4981` | fixture + checkpoint seam |

Tool binaries and sha256 are recorded by `scripts/install_tools.sh` into
`data/tools.json`.

## Reproduce

```bash
bash scripts/install_tools.sh
FX=$PWD/fixtures bash scripts/fixtures.sh
python3 scripts/bench.py e1 --repo fixtures/t3code --tools git-t3,git-hermes,jj,oak,gitbutler --turns 30 --out data
python3 scripts/bench.py e2 --repo fixtures/t3code --tools git-worktree,git-worktree+dirty,jj-workspace,rift,cp-reflink,oak-clone --forks 4 --out data
python3 scripts/bench.py e3 --repo fixtures/t3code,fixtures/hermes-agent --tools git-diff3,git-zdiff3-histogram,mergiraf,weave --out data
python3 scripts/bench.py e4 --repo fixtures/t3code --tools x --out data
```

Runs in this study used the MBP fleet host (`scripts/mbp.sh`).
