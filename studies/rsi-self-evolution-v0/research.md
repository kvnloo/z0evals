# Research protocol and source-reported comparisons

These are findings from the inspected RSI-Anything paper and released code. They are not measurements from this Hermes pilot.

## Shared loop

A policy proposes candidates. A world model predicts consequences. A verifier excludes invalid actions, then selection allocates the remaining external-feedback budget. The system stores predictions separately from observed outcomes. Feedback supports policy or workflow updates and conditional predictor adaptation. Component checks and a policy-model compatibility check determine the retained pair.

JEPA-Anything supplies the predictive foundation, including domain encoders, target representations, orthogonal predictive factors, and downstream readouts. The standalone core does not supply a trained universal skill predictor. The code-repair implementation uses a Qwen2.5-Coder-3B encoder with LoRA, a target encoder, OPF, and execution readouts.

## Domains

| Domain | Candidate and external feedback |
|---|---|
| Code repair | Revised programs, public-test feedback, hidden-suite final success |
| GUI interaction | Proposed interface actions, environment outcomes and action counts |
| Laboratory planning | Protocol sequences, protocol-alignment and parameter scores |
| Reaction optimization | Reaction conditions, measured yields at matched experiment counts |
| Immune science | Scientific workflows and interventions, withheld prediction contexts and prospective hypotheses |

Planning scores do not establish physical laboratory execution. The immune-science therapeutic hypothesis still needs experimental testing.

## Code-repair ablations

The reported CodeContests comparison fixes the ReasonFlux-Coder-7B policy, proposes four revisions per round, and allows at most three feedback rounds. It covers 200 tasks and three seeds, or 600 task-seed episodes. Public tests provide feedback. Hidden tests determine final all-pass success.

| Source method | Hidden all-pass | Online suite calls per task |
|---|---:|---:|
| Random-K | 26.0% | 3.72 |
| Capacity-matched static verifier | 26.3% | 3.72 |
| Fixed world model | 29.2% | 3.71 |
| Adapted world model | 31.2% | 3.72 |

The fixed-world versus static-verifier comparison reports candidate-ranking accuracy of 72.8% versus 66.5% and Brier scores of 0.358 versus 0.488. These ablations separate prediction-guided selection from further predictor adaptation. The released evaluation stage seals public decisions before hidden judging and performs no optimizer updates during evaluation.

## Why this pilot is different

The Hermes experiment uses a small outcome regressor and scalar keyword scores, not latent JEPA dynamics or execution-class predictions. It adapts after every measured round and omits the paper's reliability and compatibility gates. Its external task budget is exact, but its task is single-turn static review. It cannot reproduce or refute the paper's code-repair benchmark claims.

Sources:
- [Paper, arXiv:2610.13912](https://arxiv.org/abs/2610.13912), sections 2, 3.1, and 6.1.
- [RSI-Anything reproduction guide at the inspected revision](https://github.com/Gen-Verse/RSI-Anything/blob/8ba44cd73ec6f57b151ec06e2f71a0726adfb687/docs/reproduction.en.md).
- [JEPA-Anything scope at the inspected revision](https://github.com/Gen-Verse/JEPA-Anything/blob/c6e6c88f3ef75a4ce7acd660d6fa5779d995512c/README.md).
- [Released resource collection at the inspected revision](https://huggingface.co/datasets/Gen-Verse/RSI-Anything/tree/672ecc37a8c9488002258bb2a3a9ea1250dfd54b).
