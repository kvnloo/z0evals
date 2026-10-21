# next-action-v0: a next-action predictor Kevin actually uses (desktop + Android)

Status: **proposal, pre-registered, no data from the new design yet**. The one frozen artifact is an aggregate audit of the existing desktop predictor (`data/baseline-desktop-shadow.json`).

## 1. What exists today, and why it has never been used

The `.files` "predict next action" concept is real and running:

- **Code:** `scripts/workspace-copilot`, `scripts/workspace_flow.py` (Flow engine, `os.next_context.v0`), `scripts/workspace_rerank.py` (`rerank-v1`, local-only commit `c2e2d63`), `scripts/workspace_routines.py` (routine miner). Skill: `config/agent-skills/workspace-copilot/SKILL.md`.
- **Runtime:** `workspace-copilot.service` (user unit), plus a daily re-rank timer. It reads Hyprland IPC events, tmux and a privacy-filtered ActivityWatch view into a local SQLite.
- **Trigger and UI:** a Noctalia bar chip (`next-action`). It shows a "ghost" guess at p ≥ 0.35 and a "ready" one at p ≥ 0.82. `Super+Return` commits and `Super+BackSpace` dismisses.

Audit of its own 30-day log (2026-09-21 → 2026-10-21, read-only, aggregates only):

| | value |
|---|---|
| shadow predictions | 7,859 |
| ready-tier surfaces | 19 |
| explicit commits (`commit-next`) | **0** |
| accept/reject decisions recorded | **0** (225 suggestions, all still pending) |
| what it predicts | 69% `switch_app`, 26% `noop`, 5% `switch_workspace` |
| engine top-1 / top-3 at 60 s | 0.389 / 0.611 |
| engine top-1 when its confidence ≥ 0.82 (n=76) | **0.227** (miscalibrated: high confidence is *less* accurate) |
| plain most-recently-used list, `switch_app` subset (n=5,442) | top-1 **0.771**, top-3 **0.972** |
| engine on the same subset | top-1 0.454, top-3 0.690 |
| predict latency p50 / p90 / p99 | 41 / 385 / 9,843 ms |

Why it is unused:

1. **Wrong action space.** It mostly predicts "focus app X". A recency list (what `Super+Tab` already shows) beats it: 77% vs 45% top-1. Switching apps by hand takes well under a second, so a correct guess saves nothing. Cursor's lesson is the opposite: predict actions that are *low-entropy for the model but expensive for the human*.
2. **Push UI with nothing to push.** The chip is passive and usually collapsed. Kevin would have to look at the bar, judge the guess and press a chord, which costs more than doing the switch himself.
3. **Uncalibrated confidence.** The 0.82 "ready" gate fires on the guesses that are right 23% of the time.
4. **No flywheel.** The re-ranker learns "what happened next", not "what Kevin accepted", because no accept or reject has ever been logged.
5. **No Android side at all**, and no trigger from the ring.

## 2. What made Cursor (and peers) good: five lessons

1. **Abstain; show fewer suggestions.** Cursor's online-RL Tab policy gets reward only when a shown suggestion clears an accept threshold (worked example: +0.75 if accepted, −0.25 if rejected, 0 if nothing is shown, which means "show when p > 25%"). The result was **21% fewer suggestions and a 28% higher accept rate** ([cursor.com/blog/tab-rl](https://cursor.com/blog/tab-rl)). GitHub's NES saw the same thing: shown −24.5%, accept +26.5%, hide −25.6% ([github.blog](https://github.blog/ai-and-ml/github-copilot/evolving-github-copilots-next-edit-suggestions-through-custom-model-training/)). Copilot's 2022 client gated suggestions with an 11-feature logistic "contextual filter" and skipped any below 15% ([Thakkar](https://thakkarparth007.github.io/copilot-explorer/posts/copilot-internals)).
2. **An on-policy accept/reject flywheel.** Tab handles 400M requests a day, and a new checkpoint goes from rollout to next-step training data in 1.5–2 h ([tab-rl](https://cursor.com/blog/tab-rl)). Zed's Zeta2 went from about 500 hand-made examples to about 100k opt-in real ones and got **+30% accept** ([zed.dev/blog/zeta2](https://zed.dev/blog/zeta2)). Copilot found that PR diffs failed because they contain no "don't edit" negatives; it needed real editing sessions ([github.blog](https://github.blog/ai-and-ml/github-copilot/evolving-github-copilots-next-edit-suggestions-through-custom-model-training/)).
3. **Latency inside the flow.** Fusion cut p50 server latency from 475 to 260 ms while adding cursor jumps ([cursor.com/blog/tab-update](https://cursor.com/blog/tab-update)). Speculative edits reach about 1000 tok/s on the apply model ([cursor.com/blog/instant-apply](https://cursor.com/blog/instant-apply)).
4. **A small model co-designed with the UX.** Copilot calls NES "a low-latency, task-specific model", and says it only works because training, prompt and UX were co-designed. Cursor uses a custom sparse model, and frames the goal as predicting the next *location, file and terminal command*, not just text: "tab 11 times and all other keys 3 times" ([cursor.com/blog/problems-2024](https://cursor.com/blog/problems-2024)).
5. **Measure the right thing online.** The online metrics are shown rate, accept rate, hide rate and "accepted and **retained** characters" (accepts not reverted shortly after) ([VS Code blog pt 1](https://code.visualstudio.com/blogs/2026/09/16/building-the-github-copilot-inline-suggestions-model-part-one), [pt 2](https://code.visualstudio.com/blogs/2026/09/23/building-the-github-copilot-inline-suggestions-model-part-two/)). Zed shipped a shadow release first, then a gradual rollout with acceptance rate as the primary signal ([zed.dev/blog/how-we-developed-zeta2](https://zed.dev/blog/how-we-developed-zeta2)).

What makes predictors annoying and unused is the mirror image: low precision, interrupting without being asked, and a trigger cost close to the cost of just doing the thing.

OS-level comparables:
- **Android:** `AppPredictionService` is system-only (`MANAGE_APP_PREDICTIONS`, [AOSP](https://android.googlesource.com/platform/frameworks/base/+/master/core/java/android/service/appprediction/AppPredictionService.java)). A third-party Lawnchair build gets no predicted-apps row ([lawnchair#2371](https://github.com/LawnchairLauncher/lawnchair/issues/2371)).
- **Windows:** Click to Do is *user-invoked* (key or `ms-clicktodo://`) and analyses the screen locally with Phi Silica ([learn.microsoft.com](https://learn.microsoft.com/en-us/windows/ai/click-to-do)).
- **Apple:** Siri Suggestions runs on-device ([support.apple.com](https://support.apple.com/guide/mac-help/what-are-siri-suggestions-mchl679bf72c/15.0/mac/15.0)).
- **Academic:** app-usage prediction ([Shin, Hong, Dey, UbiComp 2012](https://dl.acm.org/doi/10.1145/2370216.2370243); [Parate et al. APPM, UbiComp 2013](https://dl.acm.org/doi/10.1145/2493432.2493490), which needs no training and predicts *which* app and *when*); goal inference from UI trajectories ([arXiv:2406.14314](https://www.arxiv.org/abs/2406.14314)); the GUI-agent survey ([arXiv:2411.04890](https://arxiv.org/html/2411.04890)).
- **Shell:** McFly and Atuin rank the next shell command by cwd and the previous command, using local history.

## 3. Design

### 3.1 Action space: only actions worth predicting
A candidate qualifies only if it takes **≥ 3 s or ≥ 3 inputs by hand** and has no existing single chord. The existing routine miner already suppresses keyboard-optimal single actions; that rule is extended here. App focus is dropped as a target. Recency stays as a cheap filler and as the baseline arm.

Desktop families:
- `inspect_result`: open the Hermes or omp session that just finished, blocked or failed, with its recap.
- `rerun_last_failing`: the last non-zero-exit command in the focused terminal's project.
- `next_command`: the Atuin top-1 for (cwd, previous command).
- `open_pr_or_ci`: the PR or CI run for the branch just pushed.
- `resume_task`: return to the workspace and session of the active `task_context`.
- `run_routine`: a mined multi-step routine.

Android families:
- `open_app_deep`: an app plus a deep link, e.g. NOOP sleep after wake.
- `start_z0live_with`: start a z0live call with a pre-filled context.
- `reply_needs_kevin`: open the top "needs Kevin" item.
- `routine`: a mined launch sequence (A → B within 60 s, repeated).

### 3.2 Signals (local only)
- **Desktop:**
  - Hyprland IPC (already ingested);
  - tmux topology;
  - ActivityWatch window/AFK buckets (`aw-watcher-window_groot`, `aw-watcher-afk_groot`), behind the existing privacy filter;
  - Atuin `history.db` (cwd hash, exit code, command basename, never arguments);
  - Hermes/omp harness events (`harness-event completed|waiting|blocked|failed`);
  - `task_context`;
  - git push events (branch name hash).
- **Android, no adb at runtime:**
  - The Lawnchair fork (kvnloo/lawnchair) as the host. It is the launcher, so it sees every launch it starts.
  - With the user-granted *Usage access* special permission it can read `UsageStatsManager` foreground-app events.
  - z0live broker events (call start/end, gestures).
  - NOOP state (sleep/wake) through its existing paired agent API, aggregates only.
- **Privacy:**
  - Store package names and semantic families. Hash paths, cwd and branch names; never store window titles, URLs, text, notification bodies or command arguments.
  - Phone data stays on the phone, plus a nightly encrypted sync of semantic events to groot over the tailnet through the broker's existing pairing.
  - z0evals publishes only aggregates (as in this study's baseline).
  - Jev and any remote model never see raw events (ROLES-v0: Jev "must not see secrets or private data").

### 3.3 Generator → ranker → abstainer (per ROLES-v0 tiers)
1. **T0, plain code (ships first):**
   - per-family generators (above);
   - a first-order Markov / n-gram over semantic actions keyed by (context, hour bucket);
   - Atuin next-command;
   - harness-event rules;
   - recency as filler.
   Under 5 ms, no model.
2. **T1, learned scorer:** extend `rerank-v1` into an **accept-probability** model (logistic, Copilot-filter style). Its features are generator, family, recency, hour, what the previous invocation's outcome was, est_manual_s and the device. It trains on *accept/reject* logs, not on "what happened next". Calibrate it with isotonic regression on the last 14 days.
3. **T2, shadow only:**
   - groot Qwen3-4B (about 26 ms, acts only at ≥ 0.95 per ROLES-v0) re-scores the top 5 when the T1 margin is under 0.1;
   - Jev (about 155 ms) is the tie-breaker between prevalidated options in pull mode.
   Both stay shadow-only until a matched ABAB promotion (z0evals#93 policy). No frontier model in the loop; Opus only reviews rejected cases offline each week.
4. **Abstain:**
   - Show item *i* only if `p_cal(accept) ≥ τ` and `est_manual_s − invoke_cost_s > 0`.
   - Pull mode starts at τ = 0.25: Cursor's reward with r+ = 1 − τ, r− = −τ, and "show nothing" scores 0.
   - Push stays limited to `inspect_result`, at τ = 0.7.
   - If nothing clears τ, the panel says "nothing confident" and logs an abstention.

### 3.4 UX
Pull, not push. One trigger shows up to 3 items, each as a single line with its key (`1`/`2`/`3`, or a tap). `Esc` or a swipe-away counts as a reject. The panel never steals focus from a text field, and it disappears after 6 s.
- **Desktop:** `Super+period` (unbound today) opens a small Noctalia/fuzzel panel. The bar chip is retired, or kept for `inspect_result` push only.
- **Android:** a Lawnchair dock slot or Quick Settings tile ("Next"), with three large targets.

### 3.5 Accept/reject log: the flywheel (`next_action.v1`, local SQLite)
One row per invocation:
- trigger source (`desktop_chord|phone_tile|ring_*`) and device;
- context feature hash;
- the candidates, each with generator, family, `p_raw`, `p_cal`, est_manual_s and rank;
- the arm (`model|recency_withhold`);
- shown or abstained;
- the outcome: `accepted@k`, `rejected` (Esc), `ignored` (timeout) or `manual_equivalent` (the same action done by hand within 60 s, a missed true positive);
- execution ok;
- `reversed_8s` (Kevin undid or left within 8 s, the analogue of "retained characters");
- latency from trigger to panel.

The same rows feed T1 training (on-policy), the routine miner, and this study.

### 3.6 Metrics (stored as this z0evals study)
- **Invocation rate** per active day: the usage signal. The current system's equivalent is 0.
- **Accept rate**: invocations with an accept, out of non-abstained invocations. Also accept@1.
- **Abstain rate**, and **coverage**: accepted divided by (accepted + manual_equivalent).
- **Time saved:** Σ over accepts of (median observed manual duration for that action − trigger-to-done time). The manual duration is measured from `manual_equivalent` rows, never guessed.
- **Retained accepts:** accepts without `reversed_8s`.
- **False-interrupt rate:** pushes not accepted, per active hour. For ring gestures, unintended fires per hour: a gesture followed by immediate dismiss, or one fired during typing.
- **Latency** from trigger to panel, p50 and p95. The budget is ≤ 150 ms (the existing `open_budget_ms`).

## 4. Ring gesture allocation (Oura Ring 4, jerk-burst detector, kvnloo/noop#65)

Facts from #65 at head `2ecc6e1`:
- the accelerometer streams at about 50 Hz;
- a burst closes after 240 ms of quiet, and 2/3/4 impacts make a double, triple or quadruple tap;
- doubles were recognised 15/20 times, with 0 false gestures in 32 s of typing;
- triples and quads have not been recorded yet.

The ring has no touch sensor and the detector keys on jerk, so **a long hold produces no burst and is not detectable** (inferred from the detector design). Cases where the gesture comes out one impact short are the main risk: a quad that is missed by one impact becomes a triple (end call), and missed by two becomes a double (start call).

| Pattern | Action | Context gate |
|---|---|---|
| double | z0live call start / mute toggle (locked) | — |
| triple | end call (locked) | only during a call; outside one it does nothing |
| **quad** | **keyboard STT**: dictate into the focused field | only when an editable field has input focus **and** no z0live call is active. A second quad, or the end of dictation, switches back. |
| quint / rapid (≥ 5) | reserved: *next-action peek* (display only, so a false fire costs one glance) | adopted only if the guided recordings meet the gate below |
| long hold | not available | — |

**How to trigger STT on the S25 without touching the screen:**
- The phone (SDK 37) lists the Google voice-typing IME `com.google.android.tts/com.google.android.apps.speech.tts.googletts.settings.asr.voiceime.VoiceInputMethodService`. The default IME is Samsung Keyboard `com.samsung.android.honeyboard/.service.HoneyBoardService` (read with `ime list -s -a`, nothing changed).
- An enabled AccessibilityService can call `getSoftKeyboardController().switchToInputMethod(<voice IME>)` (API 30+, [docs](https://developer.android.com/reference/android/accessibilityservice/AccessibilityService.SoftKeyboardController)). The voice IME starts listening as soon as it is shown. Switch back to Honeyboard when dictation finishes. The same service checks for input focus, which is the context gate.
- Samsung voice input has no separate IME id on this phone; it lives behind Honeyboard's mic key. So without screen taps, the ring can only reach Google voice typing.
- Prototype route with no new app code: Tasker, which is installed, can set `default_input_method` once it has `WRITE_SECURE_SETTINGS`.

**Next-action does not start on the ring.** It needs eyes on a screen to choose, so the ring would save only the reach to a tile or chord, and it would be the third meaning packed into a 4–5-impact space. It starts on `Super+period` and the phone tile.

**Adoption gate for quad and quint** (from sa-1-a8cd8bfd's guided recordings, decided before looking):
- recall ≥ 90%;
- confusion into a *lower* count ≤ 2% (quad → double is the costly case);
- ≤ 0.5 false fires per hour across typing, walking and idle negatives (at least 10 min of each).

If quad fails, STT goes to a phone-side affordance and quad stays unused. If quint fails, next-action stays tile/chord only.

## 5. Smallest first experiment (one week of normal use)

**E1 (desktop pull panel, T0 only, plus Android shadow logging):**
- Ship `Super+period`, showing up to 3 from the T0 generators with τ = 0.25 on the T0 scorer's frequency estimates, and the `next_action.v1` log.
- In 1 of 5 invocations, show the **recency-only** list instead (withhold arm). This measures whether the new families beat what `Super+Tab` already gives.
- Android: Lawnchair logs launches and usage events as semantic rows only (no UI yet), so week 2 has a phone prior.

Pre-registered success criteria after 7 days:
- ≥ 3 invocations on ≥ 5 days;
- accept rate ≥ 40% on non-abstained invocations, with the model arm beating the recency arm;
- median time saved per accept ≥ 5 s, measured from manual equivalents;
- `reversed_8s` ≤ 10%;
- p95 trigger-to-panel ≤ 150 ms.

If invocations stay under 1 a day, the trigger or the action set is wrong. That is a publishable negative, and it means the action set gets redesigned before any model work. T1, T2 and phone UI only start after E1 passes.

## 6. Non-goals
No change to NOOP code in this study. No auto-execution: commit is always explicit. No raw events leave the device. The locked double and triple gestures do not change.
