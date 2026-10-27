# The Shadow Network, applied to GUI steps

## What it is (from our code and issues, not from the GitHub repos `kvnloo/shadow` or `kvnloo/Shadowbroker`, which are unrelated forks)

The Shadow Network is z0intelligence's **observe-only lane**: for every decision the
deterministic compiler first builds the *legal action set*; the incumbent chooser acts; local
candidate models run **in shadow on the same compiled set** and only record what they would
have chosen, with latency and confidence. Their outputs carry `trafficEligible=false` and
are a distinct evidence class (*hypothetical action*) from executed outcomes. A candidate is
promoted to act only after it is **credited** against independently verified outcomes in
matched blocks (z0evals#93).

Evidence read for this definition (canonical checkout `/mnt/zer0models/z0-wt/z0intelligence`
@ `4de1aa962cf4c9a19b18a6120ea27309b908da65`, a local merge commit not present in the
remote refs at the time of writing):

- `src/z0int/cognition/shadow.py`: "Observe-only shadow lane ... compiles the deterministic
  legal action set first and hands every shadow backend that set and nothing else; never
  returns an executable decision"; receipts `z0int.cognition.shadow.receipt.v1` appended to
  `~/.z0int/shadow/cognition-shadow.jsonl`.
- `omp-extensions/local-cognition` ("Shadow-only OMP extension: compile the legal action set
  and record what local z0int models would choose", `OMP_Z0INT_COGNITION_SHADOW=1`).
- `src/z0int/refinement.py` `export_shadow_plan`, `src/z0int/routines.py` `decide_shadow`
  (uncredited -> shadow only), `src/z0int/aodl.py` (`"trafficEligible": not shadow`), merged PRs #151/#155 ("make shadow receipts scoreable"), z0intelligence
  #20/#26/#129/#144, z0evals#92/#93 ("Shadow Network routing" of CapabilityProfiles;
  "Passive shadow outputs have hypothetical actions, not independently observed
  counterfactual outcomes ... Agreement with an incumbent is not correctness").
- Prior pilot: `studies/slm-router-v0/data/nanojev-j1-shadow-pilot.json` (27 decisions,
  48.1% agreement with Jev; NanoJev p50 236 ms vs Jev 304 ms), agreement only.

## How this study uses it

1. **Compiled legal set = the phone_goal action table.** Each of the 46 frozen GUI decisions
   (`tasks/android-chooser-cases.v1.json`, 26 recorded on the S22+, 20 synthetic traps/edge
   cases) is the safety-filtered candidate table phone_goal would send to Jev, with its
   hand-labelled gold set. Consequential rows are marked; nothing outside the table is
   choosable.
2. **Incumbent:** Jev (`jev:flat`, 0.65 confidence floor) and `jev:flat+bt` (Bradley-Terry
   fallback). **Shadow candidates** on the identical table: z0int DecisionBackends
   (`openjev_06b`, `nanojev` 0.6B, `julia_1` 144M, `laya_421m`, `decider_2b`), llama.cpp
   (`qwen3-1.7b`, `qwen3-4b` Q4_K_M, JSON-schema-enum output), ollama `qwen2.5:3b`, and a
   zero-model lexical rule (deterministic control).
3. **Receipts:** `data/shadow/*.jsonl`, schema `z0evals.gui_scripting_speed.shadow_decision.v1`
   (fields mirror `z0int.cognition.shadow.receipt.v1`: `legal_ids`, `selected_action`,
   `confidence`, `latency_ms`, `trafficEligible=false`, `evidence_class`). Each row also
   carries the gold set so it is scoreable without a second store.
4. **Scoring:** against the gold labels only (`harness/analyze_shadow.py`). Agreement with
   Jev is printed as information, never as accuracy.
5. **Credit rule (offload simulation):** a candidate may answer first and "act" when its
   confidence >= tau, else the step defers to Jev. tau is fit on a lineage-safe DEV split
   (all cases of one recorded screen stay together) under the constraint *no accuracy loss vs
   Jev and zero false autonomy*, then reported on the disjoint HOLDOUT split. This is a
   passive replay; promotion still requires matched live ABAB blocks with the independent
   verifier (live harness `harness/live_s22.py`), per z0evals#93.
6. **Probing for the curriculum:** `harness/probe_ladder.py` asks every candidate easier
   derived questions (L1 done-detection, L2 two-way with both orders, L3 four-way) to find
   the level each model can already win.

## Not done yet (honest remainder)

- Candidates ran on the frozen fixture, not live beside Jev inside phone_goal. Wiring a
  shadow hook into `goalkit.loop` (record-only, after Jev's pick) is the next step; it needs
  the plugin owner's change and stays off by default.
- The cognition service on `127.0.0.1:11501` (`z0int.intelligence_service`) was not used as
  the shadow runner; candidates were called directly through the same `DecisionBackend`
  registry it uses.
