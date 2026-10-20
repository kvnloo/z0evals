# voice-omp-parity-v0

Desktop voice-quality A/B: **OMP `/live` (control) vs z0live**, on identical spoken scenarios,
scored on what the owner hears. Tracks [kvnloo/z0live#32](https://github.com/kvnloo/z0live/issues/32) (P0/P2).

This study measures acoustic timing on the **output audio** of each system (RMS windows), not
transcript text. Provider transcripts are used only for content checks (keywords, repeats,
filler, stale speech).

## What is compared

| Arm | Model / voice | Client + transport | Delegation path |
|---|---|---|---|
| `omp-live` (control) | `gpt-live-1-codex` / `sol` | Installed OMP `LiveSessionController` + `CodexLiveTransport` (Codex quicksilver signaling, native webrtc-rs peer, api.openai.com sideband) | Client delegation into an in-memory OMP `AgentSession` (default role model) |
| `z0live-realtime` | `gpt-realtime` / `marin` | Headless Chromium WebRTC client porting the Lawnchair z0live client loop; ephemeral secret minted by an **isolated** z0live broker | Broker tools (`ask_z0` → liaison → Hermes meta agent → workers, legacy work tools, `tell_hermes`), results via broker inbox |
| `z0live-bidi` | `gpt-live-1-codex` / `sol` | Same headless Chromium driver (`--arm z0live-bidi`): mints `transports:["bidi","realtime"]`, posts the SDP offer to the isolated broker's `POST /v1/live/calls` (kvnloo/z0live `feat/frameless-bidi` @ 86a9e0c); captions only | Broker-owned sideband delegation into a persistent Hermes session |

The arms differ in model, voice, transport and delegation stack. The scoreboard compares
**the products as shipped**; it does not attribute differences to any single layer. See
"Not comparable" below.

## How each arm is driven (headless, no microphone, no speaker)

- **User speech**: offline TTS, Kokoro-82M (`onnx-community/Kokoro-82M-v1.0-ONNX`, q8, Apache-2.0)
  via `kokoro-js@1.2.1` from OMP's local TTS runtime cache, voice `am_michael`. Clips are trimmed
  and normalized to **−20 dBFS active-speech RMS** (peak ≤ −1 dBFS), then resampled with sox
  (`harness/prepare_assets.py`). Silence between clips is a −85 dBFS noise floor.
- **Noise**: one procedurally synthesized clip (`harness/noise.py`: 4 footsteps, a door slam,
  1.2 s of keyboard clicks; −6 dBFS peak). No third-party samples, so no license terms.
- **OMP**: `harness/omp_arm.ts` (Bun) imports the *installed* OMP package and runs its
  controller unchanged. A Bun runtime plugin swaps only `AudioCapture` for a scripted 16 kHz
  source (so OMP's own echo gate still applies) and wraps `LiveWebRtcPeer` to timestamp the
  native 50 ms output-RMS callback. The native speaker is pointed at an ALSA null PCM.
- **z0live**: `harness/z0live_arm.mjs` (Node + Playwright + system Chromium). An AudioWorklet
  injects the same clips at 48 kHz into a sendrecv WebRTC track; the remote track feeds a
  50 ms RMS meter (muted output). The page ports Lawnchair's `Z0LiveService` loop
  (`speech_started` → `response.cancel` + `output_audio_buffer.clear`; tool calls through
  `/v1/tools`; safe-turn continuations; inbox polling and "Hermes says" relay; server VAD
  `silence_duration_ms=450`, `interrupt_response=true`). No client-local phone tools are declared.
- **Isolation**: the z0live broker under test runs from a detached worktree on loopback port
  18791 with a private data dir; nothing reaches the phone inbox. Session summaries are not
  forced (`/end` is not called; idle/summary flush disabled for the isolated broker).
  OMP runs with extension discovery disabled and an in-memory session.
- Shared timeline runner (`harness/runner.mjs`) executes `scenarios.json` identically in both
  arms; all waits are acoustic (output RMS) plus the arm's own "work pending" signal.

## Scenarios (`scenarios.json`)

`greeting`, `quick_fact`, `work_status` (needs delegation/tools), `repo_question` (needs
delegation; expects `core.py`), `barge_in` (real speech 2.5 s into a long answer),
`noise_during_answer` (noise 1.5 s into a ~6-sentence answer), `closing_silence` (20 s watch after
"Thanks, that's all for now."), `rapid_followup` (second question 600 ms after the first reply
goes quiet). ≥ 5 runs per scenario per arm, arms interleaved, ≥ 4 s between runs.

## Metric definitions (frozen before the main run)

- **Audible**: a 50 ms output window with RMS ≥ 0.015 (≈ −36.5 dBFS; equals OMP's own
  `OUTPUT_ACTIVE_LEVEL`). Window timestamp = window end.
- **EOS → first audible**: first audible window after the last injected speech sample.
- **Direct-turn pool**: greeting q1, quick_fact q1, rapid_followup q1+q2, closing q1, noise q1, barge q1.
- **Barge-in → silence**: from barge speech onset to the start of the first ≥ 300 ms quiet run
  (must begin before barge end + 1 s, else "not stopped"). Only scored when the assistant was audible at barge onset.
- **False interruption (noise)**: assistant was audible at noise onset and a ≥ 700 ms quiet run
  begins before noise end + 500 ms (the requested answer is far longer than the noise window).
  Protocol evidence (VAD start / user turn during noise) is reported alongside.
- **Unwanted speech**: any audible window in the 20 s watch after the closing reply ends.
- **Repeated speech**: two assistant turns in one run with normalized similarity ≥ 0.9 (≥ 20 chars).
- **Stale resume**: an assistant turn after the barge utterance mentioning the interrupted story (print/gutenberg/press).
- **Delegation used**: OMP `delegation.created`; z0live any broker tool call other than `get_context`/`summarize`.
- **Result audible**: EOS → first audible after the work-complete signal (OMP terminal `agent_end`; z0live terminal inbox item or synchronous tool result).
- **Filler**: regex count of stalling phrases ("let me check", "one moment", "still working", "no update" …) per delegation run.
- **Session ready**: OMP `controller.start()`; z0live broker mint + SDP + data-channel open.

## Pre-registered thresholds (committed before any scored run)

z0live is **non-inferior** to the OMP control only if **all** hold (computed by `harness/analyze.py::gates`):

| Gate | Criterion |
|---|---|
| G1 | Direct-turn EOS→first-audible **p50 ≤ OMP p50 + 150 ms** |
| G2 | Direct-turn EOS→first-audible **p95 ≤ OMP p95 + 300 ms** |
| G3a | Delegation-turn EOS→first-audible p50 ≤ OMP p50 + 150 ms |
| G3b | Delegation used in ≥ 4/5 runs of each delegation scenario |
| G3c | Repo answer correct count ≥ OMP's |
| G4a | Barge-in→silence p50 ≤ OMP p50 + 100 ms |
| G4b | Every applicable barge stops; p95 ≤ 1,000 ms (absolute) |
| G4c | Barge follow-up answered correctly ≥ 4/5 |
| G4d | Zero stale resumes after barge (blocking) |
| G5 | **Zero false interruptions from non-speech noise** (blocking) |
| G6 | **Zero unwanted speech after a closing remark** (blocking) |
| G7 | **Zero repeated speech** (blocking) |
| G8 | Filler phrases per delegation run ≤ OMP mean + 1 |
| G9 | Run failures ≤ OMP's |

A missing value makes the verdict `INCOMPLETE`, never `PASS`. Severe regressions (G4d, G5, G6,
G7) block release regardless of aggregate latency. OMP's own absolute results on G4b–G7 are
reported too: the control is not assumed perfect.

A one-run-per-cell pilot was used only to debug the harness; its data are excluded and the
thresholds above were committed before it ran. The pilot exposed three harness faults, fixed
before the scored run without touching any threshold: (1) OMP delegation events arrive on both
the data channel and the sideband and were double counted, (2) `await_result` could end before
the spoken result, (3) OMP's JS event loop stalled for seconds while LSP/MCP started, delaying
level timestamps. The OMP arm now disables LSP/MCP/Python preflight, logs event-loop stalls
(> 50 ms), and the analysis **excludes** (does not score) any OMP latency whose interval overlaps
a stall, reporting the count. Keyword checks also match with spaces removed, because provider
ASR of the assistant audio can split words ("Can berra").

## Not comparable (always reported with results)

1. Different realtime models (`gpt-live-1-codex` full-duplex vs `gpt-realtime` + server VAD) and voices (`sol` vs `marin`).
2. Different WebRTC stacks and measurement points: OMP's level is computed at the native Opus
   decoder **before** speaker buffering and without a jitter buffer; Chromium's is after NetEq
   (jitter buffer mean is recorded per z0live run). This favors OMP by roughly the jitter-buffer delay.
3. z0live's client here is a headless port of the Lawnchair loop, not the Android APK; OMP is the real controller.
4. Delegation backends differ (OMP AgentSession vs z0live liaison/Hermes/workers) and reach different data.
5. Headphone condition: no acoustic echo or room noise is injected, so OMP's echo gate and
   Chromium/Android AEC are not exercised. Synthetic TTS user voice, single speaker.
6. Shared, loaded host (load average recorded per run); both arms run on the same host and network.
7. Not measured: physical mic/speaker, Bluetooth/route changes, Android background policy,
   human-perceived naturalness, cost.

## Results (baseline 2026-10-20)

`results/voice-parity-20261020.{json,md}` — 40 runs per arm (8 scenarios × 5). `omp-live` and
`z0live-realtime` were interleaved in one block (03:50–04:47 CDT); `z0live-bidi` ran as a
second block (04:54–05:20 CDT) once its branch existed, so it is **not interleaved** with the
control. Verdicts: `z0live-realtime` **FAIL** (G1, G2, G3c); `z0live-bidi` **FAIL** (G2, G4a, G4b, G5).

Reading notes, decided after seeing the data and therefore *not* applied to the verdicts:

- G1/G2 for `z0live-realtime` depend on stall handling. When the 19 stall-affected OMP turns are
  included (they can only make OMP look slower), OMP is 1,212 / 1,995 ms and the gap shrinks
  to +102 / −12 ms. G3c (repo answers 0/5 vs 5/5) does not depend on it.
- G4b is absolute and the control fails it too (OMP barge p95 1,220 ms): the full-duplex
  `gpt-live-1-codex` model keeps talking about a second after barge-in, in both OMP and z0live-bidi.
- The two flagged noise "false interruptions" (OMP 1/5, bidi 1/5) are 738/750 ms pauses
  next to the noise window, with transcripts showing an uninterrupted answer, and `sol` has
  ~700 ms pauses between sentences elsewhere. For v1, require transcript truncation or a VAD
  event as well as the acoustic gap.
- z0live-bidi's Chromium jitter buffer averaged ~145 ms vs ~33 ms on the gpt-realtime path;
  OMP's meter has no jitter buffer, so part of bidi's p95 gap is where it is measured.
- The z0live page's "silent inbox items are not pending work" fix (cf2bd00) landed partway
  through the first block. It changes only when a run stops waiting, not any metric.

## Reproduce

```bash
S=~/.hermes/profiles/clean/cache/scratch/voice-eval
R=/mnt/zer0models/workspace/zer0/data/operations/voice-eval   # private, never committed
node harness/tts.mjs scenarios.json $R/assets-v1 am_michael
python3 harness/noise.py $R/assets-v1/footsteps_door_keyboard.24k.wav
python3 harness/prepare_assets.py $R/assets-v1 $R/assets-v1/norm
# isolated broker (detached z0live worktree, loopback, private data dir with a copied .hermes-api-key)
Z0LIVE_DATA=$R/broker-data Z0LIVE_PORT=18791 Z0LIVE_BASE_URL=http://127.0.0.1:18791 \
  Z0LIVE_IDLE_SECONDS=1e9 Z0LIVE_SUMMARY_SECONDS=1e9 python3 $S/z0live-<sha>/bin/z0live serve &
python3 harness/run.py --run-id <run-id> --reps 5
python3 harness/analyze.py --runs $R/<run-id> --out results/<run-id>.json --md results/<run-id>.md
```

Raw audio, transcripts and event logs stay in the private run directory. Only aggregates
(`results/*.json`, `results/*.md`) are published.
