# Our prior work this study builds on (source-reported by our own earlier runs)

These numbers come from earlier internal runs, cited at their pins. They were not re-run in
this study unless stated in `README.md`.

## kvnloo/cua (Cua Driver) — OSWorld dogfooding, Sept 2026

Branch `feat/osworld-cuadriver-optimization` @ `1f63bdf5003014c6f0b528c8fb5ea109391211d0`,
docs `libs/cua-driver/docs/research/2026-09-osworld/{01-eval-stock-driver-vs-pyautogui,02-optimization-log,03-papercuts}.md`.

- 15 OSWorld `test_small` tasks, Claude Haiku 4.5, 25-action cap, n=1/task/condition:
  classic screenshot+pyautogui loop **12/15 (80%)**, stock cua-driver 0.25.0 MCP **2/15
  (13%)**, curated 18-tool catalog 0/15; branch foreground delivery **8/15 (53%)**,
  background-only MPX+uinput 6/15 (40%). Driver arms cost ~3x more per task and used 2.3x
  more actions.
- Causes isolated on fresh VMs: GTK menus ignore default clicks; no working text route into
  LibreOffice (foreground route froze X); AT-SPI walks with no budget (LibreOffice Calc
  reports 2^30 children) and a daemon-wide deadlock on an unbounded cursor-overlay await
  (~5.5 min stalls). Fixed on the branch: `get_window_state.timeout_ms` (default 1000 ms)
  with labelled partial trees, 5.5 s overlay cap, x11rb foreground delivery, coordinate
  frames, screenshot scaling (a 1920 px PNG was down-scaled by the model, making every
  click ~20% short).
- Lesson for speed: tree-first is only fast when the tree walk is **budgeted**; one
  unbounded stall costs more than every model turn in an episode.

## kvnloo/cua — work-deletion research lane

`/mnt/zer0models/github/cua-lanes/speed-frontier` branch
`research/work-deletion-frontier-20260929` @ `bcf077d2092789832d6fee5018898f5160b35750`.
Guarded completion deletes exactly one provider decision on the accepted path (default /
accepted / declined chooser invocations 2/1/2); it deletes zero observations and zero
actions. No qualified current-head speedup is claimed. **The headless-Sway isolation
harness failed its independent safety review (5 blockers), so local Linux GUI/input
experiments remain paused**; this study therefore ran no Linux desktop input and used
`chrome-headless-shell` (no display) for the browser lane.

## kvnloo/OSWorld

Fork of `xlang-ai/OSWorld`; `main` @ `1a572e627ea0593587f57831a4caf5f5c99d3daf` with no
kvnloo-authored commits (branches azure/docker/mac-a11y/macos/main are upstream's). Other
OSWorld work: `kvnloo/cua` branches `feat/osworld-on-fleet`, `codex/osworld2-*`,
`hackathon/offline-osworld`.

## phone-harness fast tree + phone_goal (Hermes plugins)

- fast tree (`plugin-data/phone-harness/agent-workspace/fast_android.py`): persistent u2
  server, ~25 ms local reads vs ~2 s `uiautomator dump`; ~0.16 s via `adb exec-out` over the
  S22+ SSH tunnel.
- phone_goal (`/mnt/zer0models/hermes-phone-goal` @ `ccc6931`, plus an uncommitted
  working tree with `goalkit/pairwise.py`; file hashes in `manifest.yaml`): one tool call
  runs observe -> vetted table -> Jev pick -> act -> verify. Earlier bench (`bench/summary.json`):
  Android-version goal median 9.2 s / 6 Jev calls, battery goal 5.0 s / 3 calls, vs a
  one-model-turn-per-step baseline of ~38 s median.
- Offline chooser eval on the same 46 cases (`tests/eval/RESULTS.md`, before this study):
  flat 81% correct, flat+knockout 86%, flat+bt 88% (3.1 Jev calls/decision).

## jev-use `--plan` and plan memo

`jev-computer-use` runner: one ~1 s planning call turns a spoken multi-hop command into a
closed-vocabulary plan; measured loop 8 s vs ~36 s of agent turns around it. `JEV_MEMO=on`
reuses verified plans (skips the planning call). This is the desktop analogue of the
compiled macro measured here on Android.
