# android-u2-driver-models-v0: LLM vs SLM driving uiautomator2

**Status: draft.** The fixtures are in place and the run is pending (part 2).

This study asks how well a model can drive a real Android phone when every outcome is checked by an independent oracle rather than by the model's own "done". The phone is a Galaxy S22+ (Android 16, One UI 8.0), driven through uiautomator2. The model matrix compares:
- **ChatGPT-subscription LLMs:** `openai-codex/gpt-6-luna`, `gpt-6.1-terra` and `gpt-6.1-sol` (Sol is the ceiling);
- **local SLMs on groot:** the llama.cpp router `:11530` (Qwen3 0.6B, 1.7B, 4B, 8B and 14B, plus Nemotron-Orchestrator-8B) and ollama (Qwen2.5-VL-3B, Qwen3-4B-Instruct-2507).

## How it runs

The runner is in [`kvnloo/.files` `services/phone-queue/evals`](https://github.com/kvnloo/.files/pull/122). For every model × task × rep it sends one `kind:"goal"` job to the shared phone-queue service (`POST /v1/jobs`). That makes it the queue's first real user.

The queue service handles:
- the S22+ UI flock;
- the owner-activity gate;
- uiautomator2, with installs and the IME patched off;
- the driver harness (fx by default);
- the `reset:"home"` start;
- the `tree_text` oracle;
- restoring the foreground app afterwards.

Before and after each job, the runner takes a read-only `settings list` snapshot. If a non-volatile setting changed, it records a side effect and stops the run. It never reverts the setting.

## Tasks (`data/tasks.json`)

There are 18 read-only goals; 15 of them are multi-step. All have `consequential: false` and start from home.

| Area | Goals |
|---|---|
| Settings | open; model name; One UI version; baseband; battery capacity; legal info; app list; Samsung app settings; Accessibility and its Advanced page; language; date and time |
| Clock | open; Stopwatch tab; Timer tab |
| My Files | storage used; Internal storage root; DCIM |

How the oracles work:
- Each oracle lists `must_contain` / `must_not_contain` substrings over node text or content-desc, plus the foreground package.
- Every oracle was written from **redacted** (`phone-screen-safe`) hierarchy dumps, taken read-only on 2026-10-28.
- Each one passes on its evidence screen and fails on the home screen: 18/18 over 37 screens (`data/oracle-check-20261028.json`).

`tasks.json` also lists the excluded candidates and why: there is no calculator app, the redactor fails closed on World clock, some screens are a single tap from a settings change, and some screens show PII.

## Metrics (filled in part 2)

These follow research-focus item 5 and PR #103's per-model rows. Each row in `data/rows.jsonl` is one job; `data/summary.json` gives the per-model figures.
- **Success:** oracle success with a Wilson 95% CI, split into multi-step and single-step goals.
- **Steps:** steps and step efficiency, measured against the minimum steps from home.
- **Errors:** wrong-act (a false done or a settings side effect) and abstain.
- **Latency:** per-decision choose p50/p95 and warm whole-task time. Cold model load is reported separately.
- **Usage:** tokens and cost.
- **Not scored:** rows that came back unavailable, timeout or blocked are counted but never scored, so a model that can't be reached shows as **unavailable**, not 0.

## Prior and related work

- **`android-phone-use-v0`:** OMP's untracked draft in the `z0evals-cua` worktree. It holds source-reported hermes-phone-goal timings (`local/hermes-phone-goal@ccc6931`):
  - S22+ "Android version" lookup: 9.19 s median, 3/3;
  - battery lookup: 5.00 s median, 3/3;
  - persistent u2 hierarchy read: about 25 ms.

  That draft has one chooser and no independent oracle. This study keeps its task shape and adds independent oracles plus a model matrix. It cites the draft and does not change it.
- **PR #103, `gui-scripting-speed/z0live-control`:** per-model chooser rows on synthetic and held-out S22+ goals. For example, groot Qwen3-4B scored 12/14 held-out, with a 26 ms p50 on synthetic cases. This study measures whole tasks through the queue instead of single choices.

## Reproduce

```sh
# on groot, in a checkout of kvnloo/.files at the source commit
cd services/phone-queue/evals
./run_suite.py probe && ./run_suite.py run --out RUN --reps 3 && ./summarize.py RUN/rows.jsonl --out RUN/summary.json
# then import into z0evals with imports/android-u2-driver-models-v0.local.yaml (copy of the .example.yaml)
```
