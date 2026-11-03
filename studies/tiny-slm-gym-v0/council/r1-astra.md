[Inference] Recommendation: use Southpaw to operate an evidence-gated specialist factory, not to make weight editing the default optimizer. Start with tool-family prediction as a bounded scoring experiment; require evidence that it replaces frontier work before promoting it. Keep weight editing as a small, failure-specific challenger.

1. Amdahl diagnosis

[Measured] The only demonstrated aggregate reduction in frontier-bound work is observation-pack shortening: 26.3% of frontier-bound units changed, with zero offloads. The matched-candidate NanoJev result—approximately 61% fewer Hammer3B calls at 94.1% success-given-covered—is encouraging but concerns a local specialist cascade, not measured frontier savings.

[Inference] Therefore, no supplied result establishes the fraction of expensive frontier work removable by tool-family prediction. Its savings ceiling is the fraction of frontier decisions actually replaceable by that specialist, multiplied by safe coverage—not its classification accuracy. Record actual displaced calls, input/output tokens, fallback cost, and verified outcomes.

[Measured] Tool-family prediction has the strongest existing data substrate: 76,970 steps, seven families, chronological train/test partitions, majority accuracy 0.319, ridge 0.412, MB 0.397. Recovery has stronger outcome relevance but only 379 held-out lineages and effectively no ask/abort support. Verified-outcome learning has six usable rows.

[Inference] First tiny-model target: seven-family scoring, behind deterministic admissibility constraints, initially in shadow. First product target remains context reduction unless profiling shows family scoring can eliminate a real frontier decision. Do not conflate “predict the next historical action” with “choose a beneficial action.”

2. Which optimization lever?

[Source: supplied lm_understand-logs results] Exp 8 improved a heavily looping Qwen model; the non-looping Gemma follow-up did not materially improve. The reported Qwen gains coincide with substantially fewer truncated answers.

[Inference] This supports failure-mode repair, not a general mechanism for teaching controller competence. Classification readouts already eliminate generated JSON and long reasoning loops, removing much of that demonstrated opportunity.

[Inference] My ordering is:

    Ridge/MB and recency/transition rules: mandatory controls.
    Frozen SLM plus trained head: first neural challenger.
    LoRA/SFT: only if frozen representations demonstrably underfit.
    Darwin merges: only between compatible, task-useful parents.
    Direct weight edits: only against a named, reproducible defect.

[Inference] A base×instruct merge is not evidence of useful diversity for seven-family classification. First establish task-skilled parents and compare against the best parent and a fixed interpolation; otherwise CMA-ES may merely search decoding and calibration artifacts.

[Inference] Editing plausibly wins when a localized defect survives simpler fixes: corrupted feature sensitivity, a reproducible activation pathology, or a task-specific collapse. Invalid format should first face constrained output; overconfidence should first face temperature calibration; majority collapse should first face imbalance correction and a retrained head.

[Inference] Falsifier: at matched coverage and evaluation budget, an edit fails to beat these controls on sealed selective error, Brier/log loss, and cost, or its benefit disappears when output truncation and decoding are matched. That kills the edit hypothesis, not the specialist.

3. Southpaw’s four loops

[Inference] Preserve the trainer/evaluator separation but redefine the loops:

    A — bounded candidate search:
    Search thresholds, head parameters, compatible merges, and explicit
    weight-repair hypotheses. Fix trial and forward-pass budgets.
    Search development data only.

    B — supervised specialists:
    Train ridge/MB, frozen heads, then justified adapters on identical
    input availability and label definitions. Separate each size-ladder arm.

    C — evidence ingestion:
    Produce timestamped, provenance-linked examples from decision-time
    state. Group sessions/lineages, deduplicate, record label uncertainty,
    and prioritize verified failures rather than more easy successes.

    D — release accounting:
    Publish candidate hashes, data/split hashes, search expenditure,
    calibration, risk/coverage, per-family errors, residency cost,
    fallback behavior, and invalidators.

[Inference] The evaluator owns inaccessible sealed data, deterministic scoring, and promotion permissions. A different-family referee reviews ambiguous cases, but does not replace executable verification. Repeated release attempts require fresh evaluation cohorts or an explicit multiple-testing policy. Trainer-written judging rules are prohibited.

4. Best next step and ranked attack surfaces

[Inference] This week’s single deliverable should be a local, leakage-audited family-scoring benchmark with an explicit call-replacement ledger. Reproduce controls first; then compare a frozen 135M head against a frozen 0.6–0.8B head using the same examples and feature budget. Keep both size ends, not four simultaneous training programs.

[Inference] First command-level experiment: after creating a local decision-time-only CSV export with columns split and label, run the majority control below. Set ROUTING_CSV to that approved local export. This is a proposed experiment, not a claimed execution or an existing repository interface.

    python -c 'import csv,os,collections; r=list(csv.DictReader(open(os.environ["ROUTING_CSV"]))); c=collections.Counter(x["label"] for x in r if x["split"]=="train"); k=c.most_common(1)[0][0]; t=[x for x in r if x["split"]=="test"]; print({"majority":k,"train_n":sum(c.values()),"test_n":len(t),"accuracy":sum(x["label"]==k for x in t)/len(t)})'

[Inference] Reproduce 0.319 on the original partition before changing splits; then freeze a lineage-safe benchmark and rerun all controls. The command establishes label/count reproducibility, not leakage safety or readiness to deploy.

[Inference] Ranked attack surfaces:

    1. Candidate-set/context narrowing.
    Predicted effect: fewer irrelevant tokens; potentially fewer repeated
    routing calls. Falsifier: no net frontier savings or worse outcomes.
    First experiment: paired shadow replays with identical legal-action
    compilation, with and without family-based narrowing.

    2. Calibrated family readout.
    Predicted effect: cheap high-confidence coverage without generation.
    Falsifier: ridge dominates its risk/coverage/cost curve.
    First experiment: ridge versus frozen heads, including macro recall,
    Brier/log loss, and task-weighted selective error.

    3. Retry/recover/escalate.
    Predicted effect: fewer redundant expensive retries.
    Falsifier: no improvement over existing ridge/canary policy.
    First experiment: lineage-held-out cost replay; force fallback on
    unsupported ask/abort regions rather than extrapolating competence.

    4. Context relevance.
    Predicted effect: extend the already observed shortening channel.
    Falsifier: evidence omissions worsen verification or faithfulness.
    First experiment: selection-only compression versus existing packs;
    no generated summaries, given the prior hallucination result.

    5. Named weight-space failure repair.
    Predicted effect: rescue a defective specialist, not create new skill.
    Falsifier: calibration/head retraining matches it, or gains fail across
    seeds and fresh cohorts.
    First experiment: capped edit versus no edit, simple repair, and LoRA,
    with identical inputs and evaluation budgets.

5. Validity threats

[Inference] Time leakage includes sessions crossing boundaries, duplicated prompts, shared repository tasks, and features containing the eventual tool result. Split by lineage and time; fit preprocessing on training data only.

[Inference] Structural labels can reward reconstructing a tool name already present in the input. Audit decision timestamps and distinguish historical imitation from outcome-grounded labels.

[Measured] The earlier format-perfect summarizer still increased hallucination by 12.6 points. [Inference] Valid syntax and legal actions are necessary gates, not outcome evidence.

[Inference] Report uncertainty clustered by session/lineage, not 76,970 independent trials. Small failure-class counts cannot certify rare-event safety. One principal supports personalized deployment claims, not general agent-controller claims. Keep editor, referee, and sealed evaluator separate; treat judge disagreement as uncertainty rather than majority-vote truth.

6. Kill criteria and math lanes

[Inference] Preregister these stops: no reproducible baseline, no training; no measurable replaceable frontier work, retarget; ridge dominates neural candidates at all operational coverage points, stop that neural lane; any authority violation, block promotion; no benefit beyond simple repair after the fixed edit budget, stop editing. Insufficient outcome labels means shadow only.

[Inference] Stop expanding math search. Preserve completed artifacts and at most the minimum remaining run needed to verify merge→evaluate→receipt mechanics. Do not pay to finish both full grids merely because they started. Math scores neither promote nor disqualify a routing specialist.

7. Privacy

[Inference] Default to groot-only private data preparation and lightweight controls. Use public stand-ins for Modal harness validation. Request explicit, narrow approval before moving even derived examples or embeddings: schema, redaction examples, retention, access policy, and deletion procedure. A private volume is access control, not permission or anonymization. Until approval, private-data GPU experiments remain blocked rather than silently exported.
