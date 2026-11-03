# Council brief, round 1: tiny SLMs for z0intelligence via Southpaw scaffolding + weight-space programming

You are one seat of a four-seat council (Claude Opus 5.5, Claude Fable 5.1, gpt-6-astra, gpt-6.1-sol). This is round 1:
give an independent opening; you will not see the other seats' text. You may read files and the web, but the brief
below is self-contained. Label every claim **Measured** (from the evidence below), **Source** (a published paper/repo)
or **Inference**. Be concrete; no generic ML advice.

## 1. The owner's goals (z0intelligence README + ROADMAP, paraphrased)

- z0intelligence is a provenance-backed cognition and control plane for agent systems (Hermes, Claude Code, OMP, ...).
  Success = **verified outcomes stay equal or improve while expensive generic (frontier) inference decreases**: fewer
  frontier calls, less irrelevant context, fewer repetitive decisions, lower latency.
- Mechanism-neutral promotion: rule, cache, ridge/linear, mushroom-body (MB) "fly" learner, logit-readout head
  (Jev/NanoJev), small SLM, or anything else wins only by beating simple baselines on a sealed holdout, with risk/coverage,
  calibration (Brier/log loss), fallback, invalidators and shadow mode before canary.
- First target decision families (ROADMAP P3/P5): intent/skill routing, tool-family selection, context relevance,
  retry/recover/escalate, verification-needed/done, model/effort routing. "Army of flies" = many independent bounded
  specialists, not one universal model. "Shadow network" idea = several SLMs running beside Jev as decision models,
  improved by meta methods (Bradley-Terry, autoresearch, SFT, RSI/GEPA curricula).
- Hard non-goals: replacing frontier models on open-ended reasoning; letting the training loop modify its own judge or
  sealed eval; uploading the raw private corpus anywhere public.

## 2. The owner's approach idea (what he asked for today)

1. Reuse **Southpaw's evolutionary-training repo** (kvnloo fork of SouthpawIN/evolutionary-training). Its point is that
   the training process is scaffolded into **Hermes profiles**: a `gym-trainer` profile runs four loops (A: CMA-ES
   "Darwin" weight-space merges of parent models -> benchmark -> keep best; B: SFT/GRPO on agentic/tool-calling data ->
   eval; C: data ingestion; D: reporting), and a `gym-evaluator` profile independently assesses releases. Source
   headline claim (not reproduced): Darwin-27B-Opus 86.9% GPQA Diamond with merges only.
2. Use those profiles to run **the process from the blog "Sparks of Weight-Space Programming"** (rikiyat.github.io):
   a frontier LLM reads raw weights in a sandbox and writes weight edits directly, no gradients.
3. "Go meta": train/edit tiny SLMs (<1B) **at work that helps z0intelligence's goals**, not at math.
4. Work the size ladder **from both ends in parallel**: smallest (SmolLM2-135M, Gemma-3-270M) and largest under 1B
   (Qwen3.5-0.8B, Qwen3-0.6B).

## 3. The blog's results (Source: RikiyaT/lm_understand-logs @ 4d09ba6)

- Exp 1/2 (read): a frontier model names a game / shape from a small network's raw weights. Exp 5 (write): it writes
  all 20,486 weights of a MinAtar policy in one reply; Astra (paper) scored Breakout 517.4 vs PPO-500M 25.3.
- **Exp 8**: Astra edits Qwen3.5-0.8B (thinking on) with a CPU weight kernel + a budget of forward passes.
  MATH-500 / GSM8K / IFEval / %answers cut at 32k tokens: unedited 7.9 / 13.8 / 21.0 / 93.0; 10 passes 12.3 / 25.7 /
  49.0 / 87.2; 25 passes 14.1 / 25.1 / 39.9 / 86.4; **50 passes 48.1 / 67.1 / 62.3 / 33.1**. The winning edits removed
  a "loop/repetition" direction (W' = W - 1.5 u u^T W) from attention/MLP output matrices, or zeroed one attention head.
- **Gemma-3-270M follow-up**: it rarely loops (8.5% cut vs 93% for Qwen). Astra could **not** improve it: no edit moved
  MATH-500 by more than about a point, at 5-50 passes.
- Inference the paper invites: weight editing found and removed a **failure mode** (degenerate looping); it did not
  add capability.

## 4. Our replication so far (Measured, this host, 2026-11-02/03)

- z0intelligence `benchmarks/weight_space`, grid `20261102-grid`, tool-free single replies with paper prompts:
  read tasks correct: Astra 7/7, Argon 7/7, Opus 7/7, Fable 7/7, DeepSeek 4/7. Write (MinAtar mean over 1,000
  episodes): Astra Breakout 586.4 / Seaquest 43.2 / Asterix 42.2; Opus Asterix 47.3, Seaquest 46.2; Argon 61.3 / 1.8 /
  31.6; DeepSeek near zero; Fable mostly no weights (spent 128k output tokens reasoning).
- The multi-turn Exp-8-style SLM pilot (3 targets x 5 editors) has **never produced a result**: every local cell was
  OOM-killed on the 24 GB RAM / 12 GB VRAM host. It is now ported to Modal (sandbox verified: no network, no CUDA,
  edit round-trip works; GPU path deployed, L4).
- New today: a Southpaw-method tiny gym on Modal (Darwin MRI-Trust merge of base x instruct, simplified CMA-ES,
  fitness on 64 GSM8K-train items, held-out GSM8K-test 250 + MATH-500 100). Smoke: SmolLM2-135M base 0/64, instruct
  4/64 on fitness; held-out instruct GSM8K 1.2%, MATH-500 0% with 99% no-answer. Qwen3.5-0.8B (thinking off, 512
  tokens) base 34/64 vs instruct 32/64 on fitness. Full 6x8 runs for both ends are in progress. This lane is **math**,
  i.e. not yet aligned with item 2.3.

## 5. Prior z0evals studies on small models for z0's own decisions (Measured unless noted)

- **slm-router-v0, Phase 1B** (local RTX 3080 Ti, 1,102 receipts, 370 cells): bounded legal-action choice behind a
  deterministic legal-action compiler: Hammer2.1-3B 75/84 at 195 ms warm p50; Qwen3.5-4B 75/84 at 1,993 ms; Qwen3.5-9B
  78/84 at 3,603 ms; FunctionGemma-270M 51/84 at 66 ms; NanoJev 0.6B (logit readout) 45/84 at 31 ms zero-shot; on the
  compiler's matched candidate set NanoJev removed ~61% of Hammer3B calls at 94.1% success-given-covered. Unfiltered
  Hammer3B made 6/84 dangerous selections; compiler-first arms 0. **Composition hurt**: Qwen4B alone 18/28 vs Qwen4B +
  NanoJev hint 13/28. Residency matters: cold load p50 13.9 s, swap 12.9 s. Measured next feature: `budget_units`
  (+0.071 ceiling). Phase 2 plan: 420-episode gold corpus, chronological 70/15/15, stop before training.
- **factory-intelligence-v0**: forming z0's own function calls (48 real route/delegate items + 125 BFCL + 11):
  **no candidate beat Qwen3-8B**; Hammers returned `[]` or invented tools. Recovery controller (6 actions, 2,340
  Hermes failure episodes, 379 held-out lineages): MB controller beats the constant on expected cost, but ties the MLP
  (diff -0.007 [-0.069, +0.056]); ridge is the best single model; ask/abort essentially untested (1 each in test).
  Auto-merge-on-green failed on history (11 of 21 bad events auto-merged).
- **local-offload-and-authority-v0**: Qwen3-8B 43/48 on evidence_sufficiency (bar 44; Jev 46/48). A "learned router"
  (Nemotron-orchestrator-8B) tied a generic Qwen3-8B (23/59 each); a trivial `cheapest` rule got 35/59. Authority must
  be checked on the tool call, not the prompt.
- **offload-and-loop-v0**: a local 8B passed a format check (60/60) on summarize_tool_output then **failed
  faithfulness** (+12.6 pt hallucination vs Haiku). The verified-outcome learning loop has **insufficient data** (6
  usable rows, 1 not-success); the binding constraint is verified not-success rows (base rate 0.043). Utilization
  north star: 26.3% of frontier-bound units changed by z0, all by observation-pack shortening, 0 offloads.
- **next-action-baseline (desktop)**: recency top-1 0.771 vs engine 0.454 on app-switch (n=5,442); 0 commits of 7,859
  shadow predictions.
- **Hermes tool-family next_action dataset** (local vault only; 76,970 steps from Hermes state.db, families
  READ_SEARCH/EXECUTE/EDIT/WEB/DELEGATE/VERIFY/ABSTAIN; time split 61,576 / 15,394): majority 0.319, ridge 0.412
  (1,536 params), MB 0.397 (768 params). A recovery_action specialist (linear/MB) is already in canary with OMP hooks.
- **math372-transfer-v0 council lesson** (same four seats, 2026-11-03): candidates chosen theorem-first all failed on
  fit; invert the funnel (profile a measured hot path first), always run a simple conventional control arm, referee
  from a different model family, stop rule.
- **slm-replication-plan-v0**: preregistration only (SmolLM3-3B IFEval 76.7 reproduction); nothing run.

## 6. Constraints

- Compute: groot (12 GB VRAM, 24 GB RAM, chronically memory-starved) launches and collects only; GPU work on Modal
  (paid card on file, ~$30/month free credit). Editors run on the owner's subscriptions (Astra/Sol via Codex, Opus/Fable
  via Anthropic, Argon via agy, DeepSeek API).
- Privacy: the Hermes next_action / recovery episodes are the owner's own prompts and tool history ("local vault
  only"). Moving even derived features to Modal needs his explicit OK (options: redacted derived features on a private
  volume; groot-only; public stand-in task).
- Sub-1B decoders are much worse than 3-8B at free-form tool calling (Section 5); their plausible niche is
  **bounded scoring/classification** with calibrated abstention, where 31-66 ms latency matters.

## 7. What to answer

1. **Amdahl diagnosis**: for "frontier inference does less work", where is the measured volume? Which decision family
   is the best first target for a tiny model, given the data that exists today (labels, n, baselines)?
2. **Is the blog's method (frontier-model weight editing) the right lever for tiny SLMs on z0 decision tasks**, versus
   (a) SFT/LoRA, (b) a trained classification/logit head on a frozen SLM (Jev-style), (c) Southpaw Darwin merges,
   (d) ridge/MB? When does weight editing plausibly win (e.g. removing a named failure mode such as invalid-format
   output, overconfidence, or majority-class collapse)? Give a falsifier.
3. **How to use the Southpaw profile scaffold** (trainer runs loops, evaluator gates) so that this becomes a durable,
   evidence-gated loop, not a demo. What should loop A/B/C/D become here?
4. **The best single next step** (executable this week, with first command-level experiment), plus the top 5 attack
   surfaces ranked, each with predicted effect, falsifier and first experiment.
5. **Measurement-validity threats** specific to this plan (leakage across time splits, label noise from structural
   rules, format-only gains, small n, one principal, judge reuse).
6. **Kill / retarget criteria**, and what to do with the running math lanes (keep as harness validation, or stop).
7. Your recommendation on the privacy option.

Keep it under ~1,500 words.
