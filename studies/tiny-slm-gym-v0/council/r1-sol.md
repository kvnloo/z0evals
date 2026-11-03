Sol — round 1

[Inference] Recommendation: make a local, bounded tool-family scorer the first research target, but make demonstrated frontier-work displacement—not prediction accuracy—the promotion target. Use Southpaw as an experiment governor; treat weight editing as one challenger, not the organizing principle.

1. Amdahl diagnosis

[Measured] The only demonstrated intervention volume is observation-pack shortening: 26.3% of frontier-bound units changed, with zero offloads. The 76,970 next_action steps establish abundant training examples, not 76,970 replaceable frontier decisions. Recovery has 2,340 episodes but sparse ask/abort coverage; verified-outcome learning has only six usable rows.

[Inference] Separate two questions: “What can we train today?” and “What removes expensive inference?” Tool-family prediction wins the first; its answer to the second remains unmeasured. Predicting that a frontier agent will search does not eliminate the frontier reasoning that selects the query.

[Inference] First specialist: seven-family next_action scoring, constrained by the legal-action compiler, with abstention. It has the largest existing corpus and explicit majority/ridge/MB controls. Recovery should be the second candidate because it has more directly actionable labels, but the existing ridge/canary must remain the incumbent.

[Inference] Before training, audit a chronological sample of 200 frontier-bound decisions: which could a family-only decision actually replace, which merely predict the next tool, and which require arguments or reasoning? Record attributable tokens, calls, latency, and verification cost. If family-only replacement volume is negligible, retarget before spending GPU credit.

2. Which lever?

[Source] The supplied weight-editing report shows a large improvement on a looping Qwen checkpoint and essentially no improvement on non-looping Gemma. It supports failure-mode repair, not a general recipe for learning z0 policy.

[Inference] My default ordering is:

    Ridge/MB and deterministic controls first.
    Frozen-SLM classification head second.
    LoRA/SFT third, if errors require representation changes.
    Weight editing fourth, for a diagnosed internal pathology.
    Darwin merges only when complementary, compatible parents exist.

[Inference] A frozen head avoids generating action strings and permits direct calibration. LoRA is justified only if the frozen representation misses task-relevant distinctions. Base×instruct merging has no demonstrated relationship to the desired seven-family boundary; math fitness makes that mismatch worse.

[Inference] Invalid formatting is usually better removed by constrained scoring than repaired inside weights. Overconfidence is first a calibration/abstention problem. Majority collapse is first a label-distribution, loss, and feature audit. Weight editing earns a trial only after these alternatives fail and a specific intervention predicts a specific improvement.

[Inference] Falsifier: identify the pathology on development data; preregister its metric and collateral-damage tests; grant editing and conventional challengers matched search budgets. Reject the editing hypothesis if reduced pathology does not improve calibrated selective risk or end-to-end outcomes, or if calibration/constrained decoding achieves the same result more cheaply.

3. Southpaw’s four loops

[Inference] Keep the profile separation, but replace the optimization contract:

    A — Challenger search.
    Compare rules, ridge, MB, frozen heads, LoRA, edits, and eligible merges
    on development data. Record editor calls, GPU cost, candidate count,
    parent checkpoints, seeds, and every rejected candidate.

    B — Supervised adaptation.
    Train heads first; permit LoRA only after an explicit head-only comparison.
    Use class-balanced diagnostics, calibrated abstention, and compiler legality.
    Do not use GRPO against a manipulable proxy at this stage.

    C — Evidence ingestion.
    Group whole work-item lineages, preserve timestamps and provenance,
    audit labels, identify unsupported classes, and quarantine future data.
    No automatic corpus export.

    D — Reporting and release proposal.
    Emit immutable artifacts, risk/coverage curves, calibration, runtime cost,
    invalidators, and a rollback manifest. Report failures and inconclusive runs.

[Inference] The evaluator owns sealed outcomes and release eligibility. The trainer receives development feedback, not iterative sealed-test scores. A different model family can adjudicate ambiguous examples, but deterministic receipts and human audits remain necessary.

[Source] Repository AGENTS.md assigns training/search machinery to Evolution Lab, runtime promotion to z0intelligence, and frozen evidence/publication to z0evals. Preserve those boundaries rather than building production control inside this study.

4. Best next step this week

[Inference] Run one local “replacement opportunity + baseline integrity” experiment before launching another tiny-model search. Its deliverable is a frozen lineage-aware split, audited labels, reproduced ridge results, and an estimate of genuinely replaceable frontier work.

[Inference] First command-level step, using the known checkout:

    rg -n 'next_action|recovery_action|61,576|76,970' /mnt/zer0models/worktrees/z0evals-tiny-slm/studies

[Measured] My bounded repository lookup found the corpus description in the council brief, not an executable private-data runner. Therefore I cannot honestly provide an existing training CLI or claim this experiment ran. Locate the local-vault producer next; do not invent a public runner or export the corpus to make the command convenient.

[Inference] After that prerequisite, reproduce majority/ridge/MB locally; reserve a new untouched terminal time block, with lineage grouping. Fit calibration and thresholds only on development data. Then compare frozen heads from the smallest and largest size brackets in parallel, subject to local memory limits and an explicit spending cap.

[Inference] Ranked attack surfaces:

    1. Replacement eligibility.
       Predicted effect: prevent spending on predictions that save no work.
       Falsifier: almost no audited decisions are safely substitutable.
       First experiment: the 200-decision displacement audit.

    2. Legal-candidate narrowing.
       Predicted effect: lower dangerous-choice risk and simplify classification.
       Falsifier: compiler errors or omissions erase useful coverage.
       First experiment: audit candidate recall and replay compiler-first scoring.

    3. Frozen representation + calibrated head.
       Predicted effect: improve ridge’s risk/coverage frontier without generation.
       Falsifier: no meaningful improvement after latency and residency costs.
       First experiment: two size brackets, identical splits and thresholds.

    4. Recovery residuals.
       Predicted effect: reduce repeated expensive retries beyond existing ridge.
       Falsifier: gains disappear on held-out lineages or unsupported actions.
       First experiment: compare against incumbent ridge on matched support.

    5. Named weight pathology.
       Predicted effect: repair a localized failure without broad retraining.
       Falsifier: calibration/head training matches gains, or regressions dominate.
       First experiment: matched-budget edit versus conventional repair,
       with untouched cross-task collateral tests.

5. Measurement validity

[Inference] Time ordering alone is insufficient: repeated sessions, retries, copied prompts, and branches can straddle the boundary. Group lineages; quarantine boundary-crossing groups and report exclusions.

[Inference] Structural labels may encode historical tool use, not optimal actions. If label rules are also input features, apparent learning can be rule reconstruction. Compare explicitly with that rule and human-audit disagreements.

[Inference] Format gains are not semantic gains. Evaluate legality, correct action, verified outcome, and actual displacement separately. Include fallback, loading, and verification costs.

[Measured] Earlier studies already show format/faithfulness divergence, composition regressions, substantial residency costs, and rare-action undercoverage.

[Inference] Report lineage-clustered uncertainty, class-specific support, and paired comparisons. Treat repeated candidate search as selection bias. One principal supports a personalized claim, not general-agent competence. Never let the editor amend the judge, labels, or sealed evaluation.

6. Kill and retarget

[Inference] Before search, set a minimum useful displacement target and acceptable outcome-risk margin. Kill promotion if conservative estimates fail either requirement, if savings vanish after fallback/residency, or if sensitive classes lack evidence. Zero observed dangerous choices is not proof of safety.

[Inference] Stop a method after its preregistered budget fails to beat the strongest simple incumbent on development evidence; do not repeatedly spend the sealed set. If classification improves but saves no work, retarget to context relevance or an actionable recovery residual.

[Inference] Keep only the minimum math work needed to validate merge identity, deterministic evaluation, artifact restoration, and evaluator separation. Preserve completed results; cap or cancel remaining sweeps at safe checkpoints. Math gains must not select z0 decision-policy candidates.

7. Privacy

[Inference] Choose groot-only for private traces now. Run small linear/head experiments in bounded batches; do not force decoder training onto the memory-starved host. Use a public stand-in on Modal to validate GPU machinery separately, without claiming private-task transfer.

[Inference] If the owner later explicitly approves Modal, specify the exact derived fields, retention, access controls, logging exclusions, and deletion procedure. Redaction is not anonymization; private volumes do not themselves authorize transfer.
