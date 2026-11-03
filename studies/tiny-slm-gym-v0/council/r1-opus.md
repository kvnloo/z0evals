Seat: Claude Opus 5.5, round 1 opening. Labels: (M) Measured, from the brief's evidence. (S) Source, a published paper or repo. (I) Inference.

1. AMDAHL DIAGNOSIS

Where the measured volume is:
- The only measured frontier-side change so far: 26.3% of frontier-bound units were changed by z0, all of it by shortening observation packs. Offloads: 0. (M)
- The savings that exist today come from context relevance, not from replacing frontier calls. (I)
- The biggest labeled dataset is Hermes tool-family next_action: 76,970 steps, with a time split of 61,576 train / 15,394 test. Baselines: majority 0.319, ridge 0.412, MB 0.397. (M)
- Everything else is small:
  - Recovery: 2,340 episodes, 379 held-out lineages. Ask and abort have 1 test example each. (M)
  - Verification-needed: base rate 0.043, 6 usable rows. (M)
  - Router: 84 items. (M)

Best first target: tool-family next_action, but only paired with a consumer that saves frontier tokens. Predicting the next family saves nothing by itself. (I)

The consumer: use the top-k predicted families to narrow which tool schemas and observation context go into the frontier prompt. This matches the existing finding that small models must choose from a narrowed set, not about 120 tools (owner correction). It also turns a 7-way classifier into a context-relevance saving, which is the one lever with measured volume. (I)

Figure of merit: tokens removed per step at a fixed family coverage (for example, true family in the top-k ≥ 98%) on the 15,394-step chronological test, with fallback to the full tool list on abstention. (I)

Missing baseline: recency / last-family and a first-order transition matrix (bigram) were never run on next_action. On desktop app-switch, recency scored 0.771 vs the engine's 0.454 (M). Until those exist, ridge 0.412 is not the bar. (I)

2. IS FRONTIER WEIGHT EDITING THE RIGHT LEVER?

Not as the primary lever for z0 decisions. (I)

The evidence says weight editing removes a named generative failure mode; it does not add capability:
- Qwen3.5-0.8B looped 93% of the time. Removing a rank-1 repetition direction or zeroing one head moved MATH-500 from 7.9 to 48.1. (S)
- Gemma-3-270M loops only 8.5% of the time, and no edit moved it more than about 1 point. (S)

z0 decision tasks are bounded classification. With a logit-readout head on a frozen model (option b), there is no output format to fail: invalid-label and no-answer rates are zero by construction. The failure surface weight editing is good at disappears. (I)

Ranking for z0 decision families: (b) frozen SLM + linear/logit head, (d) ridge/MB, (a) LoRA/SFT, then weight editing, then (c) Darwin merges, last.
- Merges need parents that differ in skill on the task. For z0 decisions no parent has the skill. (I)
- Qwen3.5-0.8B base 34/64 vs instruct 32/64 on fitness is indistinguishable at n=64 (M). There is no merge signal to find. (I)

When weight editing plausibly wins: an SLM that emits labels generatively and shows one of these named failure modes:
- invalid-format / no-answer output (SmolLM2-135M instruct: 99% no-answer on MATH-500, (M));
- majority-class collapse;
- systematic overconfidence;
- looping.

In that case a rank-1 ablation is the minimal fix, and an editor that can see activations may find it cheaply. (I)

Falsifier: under the same forward-pass budget and the same tuning data, the editor's best edit fails to beat, by a bootstrap CI on held-out items, the best of three controls:
- (i) a random rank-1 projection with the same norm and layers;
- (ii) a logit bias plus temperature fit on the tuning set (about 10 parameters);
- (iii) LoRA rank 4 on the same items.

If it doesn't beat them, weight editing is a curiosity, not a lever. (I)

3. MAKING THE SOUTHPAW SCAFFOLD A DURABLE LOOP

Loop C (ingestion) becomes the receipt extractor (I):
- Runs on groot.
- Hermes state.db → derived (family, features, outcome) rows.
- Frozen chronological windows, with a purge gap at each boundary and splits by session or lineage, never by step.
- The sealed test window is hashed, and its manifest is written to an evaluator-only directory.

Loop B (training) becomes per-family candidate training: frozen-SLM head, LoRA, ridge, MB, recency, bigram. Control arms are mandatory in every run. (I)

Loop A (weight-space search) becomes one budgeted mechanism, not the core. It holds CMA-ES merges and the frontier editor, applied only to named failure modes, always against the three section-2 controls. (I)

Loop D (reporting) writes into the z0intelligence promotion ledger (I):
- accuracy, top-k coverage, Brier/log loss, ECE;
- risk/coverage curve and p50/p95 latency at residency;
- estimated frontier tokens removed;
- a $ cost row.

Evaluator gating (I):
- The gym-evaluator is the only thing that reads the sealed window.
- The trainer profile gets no filesystem read access to it. Enforce this with OS permissions or a separate mount, not prompt text.
- The evaluator runs on a different model family from the editor and the trainer driver (council lesson, (M)).
- Promotion path: shadow → canary.

Stop rule: 3 consecutive loop iterations with no CI-separated gain over the best control → the loop halts and files a report. No auto-merge (11 of 21 bad events auto-merged on history, (M)). (I)

4. BEST SINGLE NEXT STEP, AND TOP 5 ATTACK SURFACES

Next step (this week, groot-only): run the next_action family benchmark on frozen tiny encoders, with the missing baselines added. (I)
- Arms:
  - majority, recency, bigram, ridge(1,536), MB(768);
  - mean-pooled last-layer embeddings from SmolLM2-135M, Gemma-3-270M and Qwen3-0.6B, each with a logistic head;
  - the same models with top-1 logit readout over 7 family tokens.
- A 135M–0.6B fp16 forward at 512 tokens fits in 12 GB VRAM. Stream embeddings to disk in shards so the 24 GB RAM never holds the corpus. (I)
- First command-level experiment: a script `studies/tiny-slm-gym-v0/nextaction_embed.py --model HuggingFaceTB/SmolLM2-135M --max-tokens 512 --batch 32 --out /vault/derived/emb/smol135/` over the existing split. It doesn't exist yet and has to be written; the vault path is a placeholder. Then `fit_heads.py` for logistic/ridge/MB on train, evaluated once on test.
- Report: top-1, top-3 coverage, Brier, ECE, and the k needed for 98% coverage.

Top 5 attack surfaces, ranked:

1. Frozen-SLM head on next_action. (I)
   - Prediction: +3 to +8 pt top-1 over max(ridge, bigram).
   - Falsifier: CI overlaps that max.
   - First experiment: the next step above.

2. Tool-schema narrowing via top-k family. (I)
   - Prediction: 30–50% of tool-schema tokens removed at ≥ 98% coverage, with abstention falling back to the full list.
   - Falsifier: k needed for 98% coverage is ≥ 5 of 7 families.
   - First experiment: an offline counterfactual token count on the test window using the arm-1 outputs.

3. Weight editing on a public failure mode. (I)
   - Testbed: SmolLM2-135M instruct's 99% no-answer. This reuses the running math lane.
   - Prediction: the editor cuts no-answer substantially, but does not beat the logit-bias / LoRA controls on accuracy.
   - Falsifier: editor > all three controls by CI.
   - First experiment: a 25-pass Modal run with the controls at an equal budget.

4. Recovery-action head. (I)
   - Prediction: ties ridge, as MB tied the MLP (M).
   - Falsifier: the SLM head beats ridge by CI on 379 lineages.
   - First experiment: reuse the arm-1 code. Run it only if arm 1 wins.

5. NanoJev-style coverage gate on the slm-router Phase 2 gold corpus (420 episodes). (I)
   - Prediction: about 60% of 3B calls removed at ≥ 94% success-given-covered, close to Phase 1B's ~61% at 94.1% (M).
   - Falsifier: it falls below 50% at that success rate.
   - First experiment: build the corpus first; it is already planned.

5. MEASUREMENT-VALIDITY THREATS

- Time leakage: sessions and lineages that cross the 61,576/15,394 boundary; near-duplicate repeated prompts; tool-set drift (new tools appear only in test). Fixes: split by session start, add a purge gap, and report the OOV-tool rate. (I)
- Labels are imitation of the frontier, not correctness. Predicting what the frontier did doesn't show the action was right. And if the family mapping is a structural rule (for example terminal-running-tests → VERIFY), heads may just relearn that rule. Report per-family confusion and accuracy on rule-ambiguous steps. (I)
- Format-only gains: a generative arm going from 0% to x% may be pure parse-rate. Report accuracy conditional on a valid parse, and keep the logit-readout arms. (I)
- Small n and selection:
  - 64-item fitness has a standard error of about 6 pt. Picking the best of 48 CMA-ES candidates inflates the winner by about 2 SE. (I)
  - Any winner must be re-scored on untouched held-out data. (I)
  - Ask/abort with n=1 can't be evaluated (M).
- Exp-8 tuning-set overlap: check whether the editor's forward passes touched eval items. If they did, the 48.1 is optimistic. (I)
- One principal: generalizes only to the owner's own drift. That's acceptable, but it requires a rolling forward-chained re-test, not one split. (I)
- Judge reuse: Astra as editor and Astra as referee, or a trainer and evaluator profile on the same model family. Enforce a cross-family referee. (I)
- Contamination: Qwen3.5 on GSM8K/MATH. Another reason not to read much into the math lanes. (I)
- Self-reference: this gym's own Hermes sessions enter the next_action corpus. Tag them and exclude them. (I)

6. KILL / RETARGET CRITERIA

- Tiny-SLM lane for a family: kill if no SLM head beats max(ridge, MB, recency, bigram) by CI on the sealed window. In that case ship ridge or MB for that family (cheaper, already in canary for recovery) and retarget the SLM lane to the next family. (I)
- Latency: kill an SLM arm whose warm p50 on groot exceeds about 70 ms, or which needs residency that competes with the 8B (cold load 13.9 s, (M)). (I)
- Weight editing: kill after 2 named failure modes where the editor is ≤ the logit-bias or random-direction control. (I)
- Darwin merges for z0 decisions: don't start until some parent shows non-trivial skill on the task. (I)
- Running math lanes:
  - Let the in-flight 6x8 runs finish, since most of the cost is already spent. Then freeze the lane as harness validation only: checking that the CMA-ES/merge/eval plumbing and Modal path work end to end. (I)
  - Don't extend it with more math budget. (I)
  - Repurpose the SmolLM2 no-answer finding as testbed for attack surface 3. (I)
  - Set a hard $ cap, for example the monthly free credit. (I)

7. PRIVACY OPTION

Recommendation: groot-only for anything derived from Hermes next_action or recovery data. (I)
- Frozen-encoder forward passes for ≤ 0.6B models and linear heads fit on groot, so no GPU-scale need justifies moving data. (I)
- Modal is for public stand-in tasks only: the math lanes and failure-mode editing. (I)
- Revisit "redacted derived features on a private Modal volume" only if a groot-only result clears the gate and LoRA at scale is then needed. Ask the owner explicitly at that point. (I)
- Exposure note: any weight-editing loop whose probe inputs are Hermes prompts sends those prompts to the editor vendor. They already see such traffic in normal use, but the owner should approve it explicitly. (I)

Standing-rule check: nothing saved; this message is a one-off council brief, not a standing rule.
