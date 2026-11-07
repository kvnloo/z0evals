# repo-navigation-v0: does consolidating factory code into one repo with a generated map help agents find tools?

Status: draft, private (not pushed). Run 2026-11-07.

## Setup
The same code was laid out in four ways, each built from the live tree by `scripts/nav_study.py build`:

| Layout | What it is |
|---|---|
| L0 | Today's layout: loose `ops/` folders (~9.6k text files, every ops folder, bounded), `bin/`, oss-factory main, plus feature-branch worktrees. |
| L1 | Factory code consolidated into one `oss-factory` repo (drivers, gates, tools); the router lives in `z0intelligence/`. Prose AGENTS.md only. |
| L2 | L1 plus a generated `MAP.md`: one line per tool with its path, its docstring purpose and how to run it. |
| L3 | L0 plus the same generated map at the root, pointing at the scattered paths. |

Each run uses a fresh Claude Code agent inside bwrap. Only `/work` is visible to it. It has no user CLAUDE.md, skills, plugins or memory, and only read-only tools. Answers were graded by regex on known file paths and values.

## Results

**Name lookups (q1-q8):** the question names the thing (Haiku ×3, Sonnet ×1).
Every layout scored 96-100%, so these questions hit a ceiling. Consolidating (L1) still cut Haiku's input tokens by about 18% and its p90 time by about 33% against L0.

**Capability lookups (c1-c6):** "is there a tool for X?", with no file names in the question (Haiku ×3).

| Layout | Correct | Mean turns | Mean secs | Mean input tokens |
|---|---|---|---|---|
| L0 as-is | 14/18 | 9.3 | 23.1 | 237k |
| L1 moved | 17/18 | 7.8 | 19.1 | 195k |
| L2 moved + map | 18/18 | 6.8 | 15.8 | 160k |
| L3 as-is + map | 16/18 | 7.7 | 16.4 | 157k |

Every miss had one of two causes:
- **The agent found a stale duplicate in a loose ops folder.** Examples: a second free-model client (`t3code-factory/.../free_stack.py`) or an old DeepSeek pause file.
- **The agent concluded that "no such limit exists".** In fact it lives in the factory planner.

Moving the code and adding the map removed both failure modes in this sample.

## Caveats
- The sample is small: 18 runs per cell, and capability questions were run on one model only.
- The map is generated from docstrings, so files without a docstring get an empty purpose line.
- Name-lookup questions are too easy to tell the layouts apart.

## Reproduce
`NAV_DATA=<private dir> python3 scripts/nav_study.py build && ... run --set v1 && ... summary`
