# Skill-selection pilot protocol

## Comparison

One static-review skill, four training cases, four validation cases, and eight holdout cases. Problem lineages and task strings do not overlap across splits. Seeds are 0, 1, and 2. Arm order changes deterministically by seed.

- Native GEPA uses the existing optimizer engine with an explicit candidate-text adapter. Reflection minibatches contain at most two training cases. Every external task execution counts.
- Guided selection proposes four instruction bodies per round and evaluates the two highest predicted validation scores. The predictor updates from observed outcomes after the round.
- Random selection uses the same pool size and selected-candidate allowance, without prediction-based selection.

Every arm has 28 development task calls, including its initial baseline. Every arm has four eight-case holdout audits, for 32 holdout calls. Checkpoints are selection-call counts 4, 12, 20, and 28. A GEPA checkpoint retains the best fully validated candidate available by that count. Partial batches cannot become successful candidates.

Candidate generation has separate token, request, and latency accounting. The comparison does not equalize generation compute or candidate distributions. It cannot isolate every algorithmic difference between GEPA and the two pool-selection arms.

## Search and audit boundary

The optimizer sees training examples and development outcomes only. Every search for every arm and seed finishes before the runner seals search-file hashes. Only then does holdout execution begin. Holdout outcomes never enter the proposer, regressor, or incumbent-selection rule. Public holdout fixtures support reproduction, not secrecy from an operator.

Provider attempts count against hard request caps, even when they fail. At most three retries use bounded exponential backoff. Persistent quota or authentication failures close the client lane. Incomplete arms remain invalid. GEPA's internal proposal fallback must not hide a provider or schema failure: the adapter latches that failure, prevents another provider call, stops search, and invalidates the arm.

## Metrics

- Keyword-overlap validation and heldout fitness, using the repository metric unchanged.
- Known-answer accuracy of the structured `passed` verdict, with basic response-schema consistency checks.
- Validation best-so-far and heldout score at each fixed call checkpoint.
- Pre-update Spearman correlation on selected development candidates only. Ties use average ranks. Undefined correlations remain null.
- Requests by purpose, generation rejections, prompt and completion tokens, and elapsed provider and search time.

The verdict label does not prove every finding. The keyword metric can reward irrelevant vocabulary. Selected-only Spearman has selection bias. Repeated seeds share eight holdout tasks, so they do not create 24 independent task instances. This pilot makes no significance or generalization claim from three seeds.

## Research mapping and deviations

[RSI-Anything](https://arxiv.org/abs/2610.13912) combines candidate generation, world-model prediction, constrained selection, external feedback, component updates, and retention. Its domains are code repair, GUI interaction, laboratory planning, reaction optimization, and immune science.

The paper's code comparisons hold the coder fixed and use public tests for feedback and hidden tests for final success. It separates fixed-world-model selection from predictor adaptation. Those source-reported results are not reproduced here.

This pilot replaces JEPA's encoder, EMA target, OPF factors, and latent prediction with normalized sparse word embeddings and cosine-kernel regression. It updates after each round rather than using reliability-triggered adaptation. It omits predictor-quality and policy-model compatibility gates. It evaluates an adapted reviewer prompt in a single-turn fixture, not the complete Hermes tool workflow.

The released 3B bfloat16 predictor and online-adaptation requirements exceeded safe initial shared-GPU headroom. No other GPU workload was stopped. The experiment uses approved free Qwen or Nemotron APIs. Only aggregate result fields enter this publication repository.

## Publication

Every source revision is immutable. Import only the exact aggregate files listed in the local import spec. Preserve invalid and interrupted attempts. Keep raw outputs, candidate bodies, conversation history, credentials, and local paths outside the public study. Hashes identify the private raw artifacts without publishing their contents.
