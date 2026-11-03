Standing-rule check: nothing new to save — the task-specific labeling rule and the math372 council lessons (invert the funnel, control arm, cross-family referee, stop rule) are already recorded.

SEAT: Claude Fable 5.1 — round 1 opening

1. Amdahl diagnosis

Measured: the only place where z0 has (a) volume, (b) labels, (c) a baseline, and (d) a live promotion path is the Hermes tool-family next_action stream: 76,970 steps, 7 families, time split 61,576/15,394, majority 0.319, ridge 0.412, MB 0.397. Everything else is either tiny (recovery: 379 held-out lineages, ask/abort n=1 each; verified-outcome loop: 6 rows), unlabeled (offload: 0 offloads), or already shows that a trivial rule wins (desktop recency 0.771 vs engine 0.454; `cheapest` 35/59 beats a learned router 23/59).

Inference: but next_action top-1 is the wrong objective for "frontier does less work". Predicting the family the frontier will pick does not remove the frontier call unless the prediction is good enough to skip the call — and 0.41 is not. The measured volume that actually changed frontier work is observation-pack shortening (26.3% of frontier-bound units, all from one mechanism). The decision family with the best ratio of (frontier tokens saved) x (labels available) is therefore context relevance / tool-output summarization gating, and secondarily verification-needed. The Hermes step log gives free labels for "was this tool output ever referenced later in the trajectory" (a derived, redactable boolean per observation), at n in the tens of thousands.

Inference, first-target recommendation: a sub-1B scorer for "will this observation be used downstream" (keep / shorten / drop) with calibrated abstention, trained on derived features from the vault. It is bounded scoring (the niche Section 6 identifies), it attaches to the one mechanism already proven to move the north star, and it has a dead-simple control arm (length + recency + tool-family rule). Tool-family next_action is the second target, as a rule-vs-ridge-vs-SLM bake-off, not an SLM-first project.

2. Is frontier weight editing the right lever?

Source: Exp 8's 48.1/67.1/62.3 came with %cut going 93.0 -> 33.1; the edits were a rank-1 projection removal or a zeroed head. Gemma-3-270M, which rarely loops, did not move more than ~1 point. Our Measured read/write replication (7/7 reads; Astra Breakout 586.4) confirms the frontier can read and write small weight sets, but the Exp-8 pilot has produced zero local results (OOM) and is only now deployed on Modal.

Inference: weight editing is a failure-mode surgery tool, not a training method. It plausibly wins only when (i) the target has one dominant, nameable, measurable failure mode, (ii) that mode is linear-ish and localized (a direction or a head), and (iii) removing it uncovers latent capability that already exists. For z0 decision tasks the candidate modes are: invalid-format output (SmolLM2 99% no-answer on MATH-500 is exactly this), majority-class collapse on a 7-way label, and overconfidence on abstain. Of these, invalid-format is the Gemma/Qwen analogue and the most likely to be editable.

Ranking for our tasks: (b) frozen SLM + trained logit/linear head (Jev-style) first — it is what NanoJev already does at 31 ms and it cannot collapse formats; (d) ridge/MB as the control that must be beaten; (a) LoRA-SFT when the head plateaus; (c) Darwin merges only as a cheap way to pick a better frozen trunk for (b); weight editing last, as a one-shot repair applied to a trunk that has a measured named failure.

Falsifier for weight editing on z0 tasks: take the frozen-trunk+head candidate with the worst format-validity or the strongest majority collapse on the sealed holdout. Give the editor 25 forward passes. If the edited model does not beat the unedited one on calibrated log loss and coverage-at-fixed-risk by more than the ridge-vs-MB gap already observed (0.015 accuracy, which is noise-scale here), and does not also beat a 5-minute LoRA on the same data, editing is not a lever for this program. Second falsifier: if the editor's "improvement" is entirely explained by %valid-output rising while accuracy-given-valid is flat, it is format-only and should be credited to a parser, not the method.

3. Using the Southpaw scaffold durably

Inference, keep the profile split (trainer cannot touch evaluator, evaluator holds the sealed holdout and the judge). Retarget the loops:

Loop A (was CMA-ES merges on GPQA): candidate generation over frozen trunks — SmolLM2-135M, Gemma-270M, Qwen3-0.6B, Qwen3.5-0.8B, plus Darwin merges of base x instruct — scored only by the probe-head metric from loop B. Merges are cheap on an L4 and this is the one place the Southpaw code is reused as-is.
Loop B (was SFT/GRPO on tool-calling): fit the head (ridge/logit readout on pooled hidden states), then LoRA if the head plateaus, then optionally one weight-edit repair round for a named failure. Every candidate ships with Brier, log loss, coverage at risk <= 5%, and latency.
Loop C (ingestion): the vault -> derived-features exporter with a redaction audit (no raw text leaves groot), chronological splits frozen by hash, and the invalidator list (schema change, new tool families).
Loop D (reporting): the z0 promotion receipt — candidate vs majority vs ridge vs MB on the same sealed split, shadow-mode disagreement rate, fallback path — written in the format the existing recovery_action canary already uses, so the evaluator profile can gate promotion mechanically.

The evaluator profile must use a different model family from any editor used in B (math372 lesson), and its holdout hash must be in the receipt.

4. Best single next step this week

Ship the frozen-trunk probe on the next_action dataset, groot-only, no Modal: extract last-layer pooled states from SmolLM2-135M and Qwen3-0.6B over the 76,970 steps (both fit in 12 GB at bf16 with batch 1-8), fit a ridge/logit head on the 61,576 train split, score on the 15,394 time-held-out split against majority 0.319 / ridge 0.412 / MB 0.397. First command is the feature extraction job with a redaction check that the exported matrix contains only hidden states and family labels. This tells us within a day whether any sub-1B trunk carries signal the 1,536-param ridge does not — the prerequisite for every other lane.

Top 5 attack surfaces:
1. Observation-relevance scorer (keep/shorten/drop). Predicted: coverage of 30-50% of observations at <=5% risk, directly raising the 26.3% north star. Falsifier: a length+recency rule matches it. First experiment: derive "referenced later" labels from state.db, fit ridge.
2. Frozen trunk + head on next_action (above). Predicted: +0.03-0.08 over ridge if trunk helps; falsifier: within 0.015 of ridge. First experiment: the extraction job.
3. Trunk selection via Darwin merges scored by head metric. Predicted: small (+0.01-0.02); falsifier: instruct trunk alone ties. First experiment: one 6x8 run with the fitness swapped from GSM8K to the head's held-out log loss.
4. Weight-edit repair for format validity on SmolLM2 (99% no-answer). Predicted: %valid rises sharply, accuracy-given-valid flat. Falsifier above. First experiment: one Modal L4 cell, 25 passes, SmolLM2-135M, metric = %valid and acc-given-valid reported separately.
5. Verification-needed scorer. Predicted: useful but blocked — the binding constraint is verified not-success rows (base rate 0.043, 1 row). Falsifier: cannot even be run. First experiment: count labels; if under 200 positives, park it.

5. Measurement-validity threats

Time-split leakage: Hermes sessions span the split boundary; a step at t and its sibling at t+1 share context. Split by session, then by time, and report both.
Label noise from structural rules: next_action labels include steps forced by the harness (e.g. VERIFY after EDIT by rule). Those inflate any model that learns the rule; strip rule-determined steps or report accuracy on the non-forced subset.
Format-only gains: already seen twice (8B format 60/60 then +12.6 pt hallucination; SmolLM2 99% no-answer). Always report accuracy-given-valid alongside validity.
Small n for the decisions that matter: ask/abort n=1, not-success n=1. No claim about those classes until n >= 50.
One principal: 100% of the data is Kevin's own workflow. Hold out by project/repo as a third split to estimate transfer; label the result "single-user" in every receipt.
Judge reuse: editors (Astra/Opus) must not be the evaluator; the Modal sandbox must never see the sealed split; the trainer profile gets fitness only on the train split.
Composition: slm-router showed Qwen4B + NanoJev hint 13/28 vs 18/28 alone. Any SLM output fed to a larger model must be A/B'd against the larger model alone.

6. Kill / retarget criteria

Kill the SLM-head lane if no sub-1B trunk beats ridge by >0.03 on session-split next_action after two trunks and one LoRA round. Kill the weight-edit lane if the format falsifier in (2) holds on its first two cells. Retarget to the observation-relevance scorer regardless of the above, since it attaches to the only proven north-star mechanism.

Running math lanes: keep them only until they produce one complete 6x8 run per end — that validates the Modal harness, CMA-ES loop, and receipt format. Then swap the fitness function; do not spend another dollar optimizing GSM8K. The Qwen3.5-0.8B base 34/64 vs instruct 32/64 result is already a useful harness sanity check, not a research result.

7. Privacy

Recommendation: groot-only for the probe work this week (it fits in 12 GB); for anything on Modal, redacted derived features only — pooled hidden states plus integer family labels, no token ids, no text — on a private volume, with a written audit that the exporter cannot emit strings. Public stand-in tasks (BFCL-style) are acceptable for harness validation but must never be the promotion evidence, given factory-intelligence-v0 showed sub-8B results on BFCL did not transfer to z0's own 48 route/delegate items.
