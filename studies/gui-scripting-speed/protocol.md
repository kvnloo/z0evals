# Protocol (iteration 1)

Not preregistered: the scoring script and credit rule were written after the Jev arms and
the first four z0int arms had run (but the gold labels predate this study). Iteration 2
must freeze `harness/analyze_shadow.py` and a fresh confirmation set before any run.

## Objective

Minimize wall time and model turns per GUI goal on Android phones and Linux desktop/browser
while keeping independently verified success at or above the incumbent.

## Experiments in iteration 1

| id | question | arms | verifier | evidence class |
| --- | --- | --- | --- | --- |
| E1 shadow chooser | Can a local model choose the next GUI step on the compiled legal set as well as Jev, faster? | Jev flat (incumbent), Jev flat+BT, 5 z0int backends, llama.cpp qwen3 1.7B/4B, ollama qwen2.5 3B, lexical rule | frozen hand-labelled gold sets (46 cases) | passive shadow prediction on frozen fixture |
| E2 difficulty ladder | Which question level can each SLM already win (curriculum start)? | same candidates on L1/L2/L3 derived questions | gold derived from the same labels | passive shadow prediction |
| E3 live S22+ | How much wall time does each removal of model work buy on a real phone? | A phone_goal flat, B phone_goal flat+BT, C compiled GUI macro (0 model calls), D deterministic adb read | value read independently via `getprop` / `dumpsys battery` must appear in the final screen | executed live read-only (D: deterministic control, same source) |
| E4 browser mechanics | Observation format and settle policy costs | pixel+fixed, axtree+fixed, axtree+event, compact+event, compiled | fixture oracle `window.__state` + returned value | executed owned fixture |

## Fixed rules

- **Scoring (E1/E2):** correct = id in gold; uncertain = `reobserve` when not gold;
  wrong = anything else; false autonomy = wrong pick of a row marked Consequential. Raw
  argmax (before any confidence floor) is scored separately.
- **Offload credit (E1):** candidate acts when confidence >= tau; else defer to Jev flat.
  tau fit on DEV, reported on HOLDOUT; DEV/HOLDOUT split by SHA-256 of the case lineage
  group (one recorded screen = one group). Constraint: DEV accuracy >= Jev DEV accuracy and
  zero false autonomy. Passive replay only; never a promotion by itself.
- **Order control:** E1 reps shuffle case order with a fixed seed and reverse it every
  other rep; E3 runs ABCD / DCBA blocks per rep; E4 alternates arm order per rep.
  Warm-up decision excluded for local models; cold load reported separately.
- **Repetition:** E1 3 reps x 46 cases per arm; E3 3 reps x 3 goals x 4 arms; E4 10 reps x
  3 tasks x 5 arms.
- **Safety:** Android only on the S22+ test phone, read-only Settings navigation, every run
  inside `flock .../s22-ui.lock` (shared with two other workers), foreground app restored
  after each run; Linux GUI input not run (isolation harness not certified); browser lane in
  `chrome-headless-shell` with a private temp profile and display variables scrubbed.
  Heavy local model work under `flock .../heavy.lock nice -n 10`, one model at a time.
- **Privacy:** fixture screen text is redacted (`[name]`, `[serial]`, `[number]`,
  `[redacted]`, and firmware/build strings -> `[fw]`, `[build]`, `[se-build]`,
  `[kernel-build]`). Public copy SHA-256 `964021d8...a32c`; the pre-redaction source
  (`hermes-phone-goal/tests/eval/cases.json`, SHA-256 `46ebb0b5...b7ed`) is referenced by
  hash only. Live rows store no screen text, only verified/not.

## Known confounds

- Gold labels were written by the agent that built phone_goal (not by Jev and not by any
  candidate), so they are independent of every arm, but a single labeller.
- The lexical rule and the SLM instruction text were written after seeing the fixture:
  both are post-hoc and need a fresh confirmation set before credit.
- Jev latency depends on the network and Jev service load; the GPU is shared with other
  resident llama.cpp servers (z0-farm router, garden_room), so local p95 includes contention.
- The live S22+ link is an SSH tunnel; the same phone served two other workers between runs.
