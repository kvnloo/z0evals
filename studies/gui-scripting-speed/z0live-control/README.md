# z0live in-app control: on-phone accessibility tree and tiered choosers

Sub-study of `gui-scripting-speed`. Iteration 1, not preregistered. Questions:

1. Why did z0live's in-app control ("click on the menu button" in ChatGPT) not land?
2. How fast can z0live read and act on the screen from its own accessibility service,
   compared with phone-harness's uiautomator2 path?
3. Which decision tier should pick the target when the on-phone matcher is unsure:
   an on-phone SLM, a small model on groot, or Jev?

Code under test: kvnloo/lawnchair `feat/z0live-fast-a11y` (APK `z0live-standby-1209e683e0a6`)
and kvnloo/z0live `feat/fast-phone-control`. Phone: Galaxy S22+ (SM-S906U1, Android 16) test
phone over an SSH-tunnelled adb, shared with two other workers. Every UI burst ran under
`flock .../s22-ui.lock`, one burst per scenario.

## 1. Root cause (owner session 6a4a0308, 18:45)

- The z0live accessibility service was installed but **not enabled**, and in-app control
  needed a per-session consent nobody had given, so `phone_ui_tree` returned `permission_required`.
- The utterance fell through to the Opus Hermes run, which used fire-and-forget
  `z0live action`, never saw the phone's result, guessed `phone_tap` arguments
  (`Unknown argument`) and still told the owner it had tapped. That took 38 s, and nothing happened.
- No tool reported whether a tap had landed.

Fixed on both sides. The phone now has `phone_do` (on-phone choice and act) and `phone_act`
(by id). Each action reports `landed` with evidence. The owner switch persists, and Settings
explains Android's restricted-setting step. The broker sends in-app requests straight to
`phone_do`, escalates to groot and then Jev, waits for a spoken yes before consequential
taps, and speaks landed or not landed.

## 2. Latency on the phone (S22+, v2, 12 app screens)

| step | z0live (in-process accessibility) | phone-harness u2 (`dumpWindowHierarchy`, curl on phone) |
| --- | --- | --- |
| tree read, warm p50 / p95 | **9.3 / 104 ms** | 98 / 165 ms |
| tree read, first after launch p50 | 75.5 ms | 111.6 ms |
| tier-0 decision (lexical + synonyms) p50 / p95 | 16.5 / 24 ms | n/a |
| act (performAction / gesture) p50 / p95 | 19.5 / 99 ms | n/a |
| landed confirmation (own events + re-read) p50 / p95 | 166 / 439 ms | n/a |
| whole `phone_do` p50 / p95 (n=16) | **267 / 477 ms**, 16/16 landed | n/a |

- Both tree columns are measured on the phone and include no host transport. The u2 numbers
  include starting curl, about 10 ms. The adb broadcast wrapper the bench uses adds about
  170 ms (`am` start-up). z0live does not pay that cost, because it runs inside Lawnchair.
- p95 tree time comes from Chrome's tab switcher (121 tabs), where u2 is just as slow.
- The confirmation window is bounded at 250 ms for the first app event plus at most 110 ms
  of settle time. Most of the `phone_do` total is spent there. It is the price of saying
  "landed", not of choosing.
- The owner's case on a logged-out ChatGPT: `skip` landed in 81 ms. "Can you click on the menu
  button" picked `Menu` at confidence 1.0 and landed in 109 ms.
- Gates held: Settings and Contacts returned `blocked_app` (policy). In v2, Play Store
  "search for apps" returned `confirm_required`, which was too broad. Fixed in lawnchair
  `6a3ca24718`: Play Store Get, Install and price taps are still gated.
- Chrome Custom Tab web content was invisible to both z0live and u2, because Chrome had not
  built its renderer accessibility tree. This is a known limit.

## 3. Tiers (synthetic labelled set: 29 cases, 12 screens, all controls as candidates)

| tier | where | top-1 | acted right / wrong at floor | p50 / p95 ms |
| --- | --- | --- | --- | --- |
| 0 lexical + synonyms | phone, in-process | 25 acted, 4 escalated | 25 / **0** | ~0.7 (JVM) / 16.5 on phone |
| SmolLM2-360M Q8 | phone CPU, llama.cpp | 0.25 | 0 / 0 @0.95 | 124 / 398 (full prompt) |
| Qwen3-0.6B Q8 | phone CPU | 0.22 | 0 / 0 @0.95 | 182 / 551 |
| Qwen3-1.7B Q4_K_M | phone CPU | 0.79 | 16 / **6** @0.95 | 765 / 2453 |
| Laya 421M (ModernBERT) | groot CUDA | 0.75 | 2 / 0 @0.85 (under-confident) | 23 / 38 |
| Laya 421M | groot CPU, 4 threads (phone proxy) | 0.75 | 2 / 0 @0.85 | 914 / 1156 |
| Qwen3-0.6B Q8 | groot llama-server | 0.25 | 2 / 2 @0.95 | 31 / 86 |
| Qwen3-1.7B Q4_K_M | groot | 0.71 | 19 / 4 @0.95 | 17 / 48 |
| **Qwen3-4B Q4_K_M** | groot | **0.93** | 26 / 3 @0.95 | **26 / 45** |
| **Jev** (jevkit chooser) | cloud | **1.00** | 28 / 1 | **155 / 204** |

Real S22+ screens (held-out: 14 goals from v1 and v2, the phone's own candidates):
groot Qwen3-4B got 12/14 top-1 with 2 wrong acts, p50 96 ms. Jev got 12/14 top-1 with 1 wrong
act, p50 173 ms. Real screens carry more candidates, so groot is slower here than on the
fixture.

Verdict for iteration 1:

- **Tier 0 on the phone stays the default.** It settles most requests in about 17 ms with
  no wrong acts and needs no model.
- **An on-phone SLM tier is not worth shipping now.** Models that are fast enough guess at
  chance. Qwen3-1.7B is accurate enough, but at 0.8 to 2.5 s it is slower than a round trip
  to groot, and it acted wrongly 6 times at 0.95. Laya on CPU takes about 0.9 s. On GPU it
  is fast but under-confident on this zero-shot task. Revisit with an NPU runtime or a
  fine-tuned 100-300M chooser.
- **Escalation is groot Qwen3-4B, then Jev.** Use groot (about 25 to 100 ms, floor 0.95);
  below the floor go to Jev (about 150 to 200 ms); below Jev's floor, ask the owner. Both
  wrong-act rates are above zero on real screens, so consequential taps stay behind a spoken yes.

## Caveats

- Small n (29 synthetic cases, 14 real goals, 16 landed acts). There is one phone, and it is
  a test phone, not the owner's S25 Ultra. Each run used one APK build. The same phone
  served other workers between bursts.
- The lexical rules, prompts and floors were written after seeing the fixture. A fresh
  confirmation set is needed before any credit.
- "Landed" means the app's own accessibility events or the screen hash changed after the
  action. It does not mean the goal was reached, and nothing independent verified intent.
- On-phone SLM numbers come from llama.cpp CPU builds with 4 threads (`-t 4`), no NPU.
  "Full prompt" is the first, uncached pass, which is what a new screen costs.

## Files

- `data/summary.json`: every number above.
- `data/ondevice-runs.jsonl`: per scenario timings, statuses, decisions. Screen text is
  dropped; only fixed control labels are kept.
- `data/tiers-fixture-rows.json`: per-case tier picks on the public synthetic set.
- `data/heldout-s22.json`: per-goal groot and Jev results on real screens. No screen text.
- `scripts/export.py`: rebuilds all of the above from the private raws (kept off-repo).
- Drivers: lawnchair `tools/zer0/z0live-control-bench.py` (`--u2`) and
  `tools/zer0/test-z0live-control.sh`; z0live `desktop/tests/bench_phone_tiers.py` and
  `bench_laya_tier.py`.
