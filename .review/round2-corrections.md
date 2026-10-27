# Round-2 corrections

Scope: only the fifteen supplied corrections and the requested privacy edits. The second reviewer verdict was not received; its truncated opening supplied no additional actionable items. No new model runs, commits or pushes were made.

Verification: numerical recomputations use raw result rows; stored regex and exact-substring grades remain harness-reported results rather than independently verified outcomes. The saved specification and existing manifest confirm the gist revision and dates.

## Item 1

Applied.

Location: post

BEFORE
```text
| edit turns that changed nothing | 5/73 | 0/73 |
```

AFTER
```text
| edit turns that changed nothing | 5/63 | 0/63 |
```

Location: post

BEFORE
```text
Recall began late in the script and covered facts, details, corrections and orders.
```

AFTER
```text
The edit denominator is the 63 add, fix and probe turns among the 112 completed turns: 27 add, 18 fix and 18 probe. The unchanged UniiChat turns were 35, 49, 50, 59 and 80. Recall began late in the script and covered facts, details, corrections and orders.
```

Location: summary round_2.E5.edit_turns_with_no_file_change

BEFORE
```text
"(absent)"
```

AFTER
```text
{
  "A": 5,
  "B": 0,
  "n_eligible_turns_per_arm": 63,
  "eligible_kinds": {
    "add": 27,
    "fix": 18,
    "probe": 18
  },
  "n_completed_turns_per_arm": 112,
  "definition": "Add, fix and probe turns; numerator counts no changed files and no request-budget cut, matching the harness.",
  "A_turns": [
    35,
    49,
    50,
    59,
    80
  ],
  "B_turns": [],
  "runs_per_arm": 1,
  "status": "recomputed from raw turn rows and script; file changes are harness observations, not independently verified task outcomes"
}
```

Location: number-source audit

BEFORE
```text
`5`, `73`, `0`, `73`
```

AFTER
```text
`5`, `63`, `0`, `63`
```

Location: number-source audit

BEFORE
```text
script reached edit-turn n=73
```

AFTER
```text
script reached add/fix/probe n=63 (27+18+18 among 112 completed turns)
```

Location: number-source audit

BEFORE
```text
with reached edit denominator73
```

AFTER
```text
with reached add/fix/probe denominator63
```

## Item 2

Applied.

Location: post

BEFORE
```text
The batch result was followed by new messages, so end-of-turn sizes were above the low-water target; those sizes do not mean every batch stopped at that target.
```

AFTER
```text
Each batch took the view to 63,688-63,843 bytes, under the 64,000-byte target, n=3. The end-of-turn sizes in the table are higher because messages were added after the batch in the same turn.
```

Location: summary round_2.E5.batch_completion_view

BEFORE
```text
"(absent)"
```

AFTER
```text
{
  "min_bytes": 63688,
  "max_bytes": 63843,
  "target_bytes": 64000,
  "n_batches": 3,
  "view_bytes_by_turn": {
    "52": 63843,
    "77": 63688,
    "103": 63753
  },
  "status": "measured batch completion sizes from raw turn rows; end-of-turn sizes include later messages"
}
```

## Item 3

Applied.

Location: post

BEFORE
```text
| stock tools and skills, user settings disabled | 23,690 | first B2 request, n=1, measured |
```

AFTER
```text
| stock tools and skills, user settings disabled | 23,690 | E5 stock arm, first request, n=1, measured |
| thinned Claude Code, four tools | 4,852 | E5 thinned arm, first request, n=1, same message, measured |
```

Location: post

BEFORE
```text
| thinned Claude Code | 2,253 | baseline overhead probes, n=2, measured |
```

AFTER
```text
| thinned Claude Code, round-1 flags | 2,253 | E6 trivial-message Haiku probes, n=2, measured |
```

Location: post

BEFORE
```text
The stock comparison ended at 37 turns, one run per arm.
```

AFTER
```text
The matched first-request comparison is 23,690 versus 4,852 tokens on the same message. The 2,253-token figure is a separate round-1-flags probe with a trivial message on Haiku. The stock comparison ended at 37 turns, one run per arm.
```

Location: summary round_2.E5.matched_first_request_input

BEFORE
```text
"(absent)"
```

AFTER
```text
{
  "stock_tools_skills_user_settings_disabled": 23690,
  "thinned_four_tools": 4852,
  "n_requests_per_arm": 1,
  "same_scripted_message": true,
  "status": "measured first-request all-input-side tokens from raw per-request usage"
}
```

Location: summary round_2.E6.overhead.cc_thinned_round1_scope

BEFORE
```text
"(absent)"
```

AFTER
```text
{
  "n": 2,
  "model": "Haiku",
  "message": "trivial message",
  "status": "measured overhead probes with round-1 flags; separate from the matched E5 first requests"
}
```

Location: number-source audit

BEFORE
```text
| 243 | `2,253`, `2,` | I6 thin/index labels haiku/base and base-again, input+cache_write+cache_read=2253, n2; A6 overhead.cc_thinned_round1 |
```

AFTER
```text
| 243 | `2,253`, `2,` | I6 thin/index labels haiku/base and base-again, input+cache_write+cache_read=2253, n2, trivial-message Haiku probes with round-1 flags; separate from E5 matched comparison |
```

## Item 4

Applied.

Location: post

BEFORE
```text
In the replay, Sonnet sometimes summarized the new user message instead of doing the task. The harness identified 12 such turns out of 112.
```

AFTER
```text
In the replay, Sonnet returned a summary line in the compaction format on 12 of 112 turns. Eleven were orders, facts or corrections to note: 6 orders, 3 facts and 2 corrections. One was an edit task, turn 35, the only overlap with the five edit turns that changed nothing.
```

Location: summary round_2.E5.compaction_style_kind_counts

BEFORE
```text
"(absent)"
```

AFTER
```text
{
  "order": 6,
  "fact": 3,
  "correction": 2,
  "edit_fix": 1,
  "n_classified_turns": 12,
  "n_completed_turns": 112,
  "unchanged_edit_overlap_turns": [
    35
  ],
  "status": "broad harness reply-format classification recomputed from raw replies and script; not twelve failed edit tasks"
}
```

## Item 5

Applied.

Location: post

BEFORE
```text
    label: new failure modes
```

AFTER
```text
    label: failure modes at scale
```

Location: post

BEFORE
```text
## new failure modes {#failures}
```

AFTER
```text
## failure modes at scale {#failures}
```

Location: post

BEFORE
```text
The shared system prompt asks the same model to handle turns and compactions.
```

AFTER
```text
Round 1 saw zoom calls at default effort, 5 of 271 sends, and Sonnet answering two arithmetic baits in 8 nodes. Round 2 adds turn-as-compaction replies and executed shell commands; with shell tools listed, compactor tool-call sends reached 11.2%.

The shared system prompt asks the same model to handle turns and compactions.
```

## Item 6

Applied with a supported alternative. The requested Sonnet-medium single-answer claim is inaccurate: raw replies contain both 1517 and 5040, and stored retained-line classifications link them to distinct bait messages. Those classifications identify two distinct baits per Haiku effort, so the unverified two-or-three range is replaced by the supported count. The Sonnet corpus is partial and cannot be compared against all five baits.

Location: post

BEFORE
```text
In the sweep, each candidate answered two or three of five planted requests within a summary line, according to the report's inspected examples.
```

AFTER
```text
In the sweep, the stored retained-line classifications identify two of the five planted requests answered in a line by each Haiku effort. Sonnet medium wrote the answers 1517 and 5040 on its partial 32-message corpus, which does not contain all five baits.
```

Location: summary round_2.E4_bait_answers

BEFORE
```text
"(absent)"
```

AFTER
```text
{
  "haiku_distinct_requests_answered": {
    "low": 2,
    "medium": 2,
    "high": 2,
    "xhigh": 2
  },
  "n_planted_requests_full_corpus": 5,
  "runs_per_effort": 1,
  "status": "stored retained-line harness classifications, cross-checked against raw reply answer markers; not independently regraded",
  "sonnet_medium": {
    "answers": [
      "1517",
      "5040"
    ],
    "n_distinct_requests_answered": 2,
    "n_corpus_messages": 32,
    "all_five_baits_present": false,
    "status": "partial corpus; both answer markers verified in raw reply rows"
  }
}
```

## Item 7

Applied.

Location: post

BEFORE
```text
The round-1 retry-heavy E1 USD figures have not been repaired individually. We retain them as historical reported figures with that defect recorded, rather than treating them as audited costs.
```

AFTER
```text
The defect was in the E1 analysis script and affected no E1 USD figure published here. The retained E3 whole-arm estimates move immaterially when corrected: differenced USD 0.635 and 0.461 versus the source-reported 0.640 and 0.468. The Sonnet ratio stays 5.0 times; Haiku moves from 58 times to about 57 times.
```

Location: summary round_1_corrections.E1_usd_sum

BEFORE
```text
{
  "retracted": "Retry-heavy E1 USD totals independently recomputed as valid costs",
  "replacement": "E1 analysis sums cumulative process USD per send. Individual round-1 retry-arm USD totals remain unrepaired. E4 takes differences. E3 weighted-token results are unaffected.",
  "status": "known analysis defect, no invented replacement round-1 totals"
}
```

AFTER
```text
{
  "defect": "E1 analysis summed cumulative process USD per send, double-counting retries.",
  "replacement": "No E1 USD figure was published here. E4 costs use differences. E3 token ratios are unaffected; E3 whole-arm USD totals are corrected below.",
  "E1_published_usd_figure_affected": false,
  "E3_differenced_whole_arm_cli_usd": {
    "sonnet": 0.635,
    "haiku": 0.461
  },
  "E3_source_reported_whole_arm_cli_usd": {
    "sonnet": 0.64,
    "haiku": 0.468
  },
  "E3_corrected_whole_arm_ratios": {
    "sonnet": 5.0,
    "haiku_approximate": 57
  },
  "n_turns_per_arm": 26,
  "status": "E3 totals verified by differencing raw retry rows; subscription CLI estimates, not invoices"
}
```

Location: summary cost_26_messages sonnet

BEFORE
```text
{
  "turn_model": "sonnet",
  "uniichat_turn_calls_weighted_tokens": 110260,
  "continued_session_weighted_tokens": 76297,
  "ratio_at_write_weight_2": 1.45,
  "ratio_at_write_weight_1_25": 1.33,
  "uniichat_including_compactions_usd_cli_estimate": 0.64,
  "continued_usd_cli_estimate": 0.128,
  "whole_arm_ratio": 5.0,
  "whole_arm_interpretation": "Historical short-chat xhigh result, not a prediction for low effort or longer chats."
}
```

AFTER
```text
{
  "turn_model": "sonnet",
  "uniichat_turn_calls_weighted_tokens": 110260,
  "continued_session_weighted_tokens": 76297,
  "ratio_at_write_weight_2": 1.45,
  "ratio_at_write_weight_1_25": 1.33,
  "uniichat_including_compactions_usd_cli_estimate": 0.635,
  "continued_usd_cli_estimate": 0.128,
  "whole_arm_ratio": 5.0,
  "whole_arm_interpretation": "Historical short-chat xhigh result, not a prediction for low effort or longer chats.",
  "source_reported_before_usd_correction": {
    "uniichat_including_compactions_usd_cli_estimate": 0.64,
    "whole_arm_ratio": 5.0
  },
  "whole_arm_status": "corrected cumulative-USD differences from raw E3 rows; one run per arm, n=26 turns; rounded ratio"
}
```

Location: summary cost_26_messages haiku

BEFORE
```text
{
  "turn_model": "haiku",
  "uniichat_turn_calls_weighted_tokens": 124750,
  "continued_session_weighted_tokens": 81040,
  "ratio_at_write_weight_2": 1.54,
  "uniichat_including_compactions_usd_cli_estimate": 0.468,
  "continued_usd_cli_estimate": 0.0081,
  "whole_arm_ratio": 58,
  "whole_arm_interpretation": "Historical short-chat xhigh result, not a prediction for low effort or longer chats."
}
```

AFTER
```text
{
  "turn_model": "haiku",
  "uniichat_turn_calls_weighted_tokens": 124750,
  "continued_session_weighted_tokens": 81040,
  "ratio_at_write_weight_2": 1.54,
  "uniichat_including_compactions_usd_cli_estimate": 0.461,
  "continued_usd_cli_estimate": 0.0081,
  "whole_arm_ratio": 57,
  "whole_arm_interpretation": "Historical short-chat xhigh result, not a prediction for low effort or longer chats.",
  "source_reported_before_usd_correction": {
    "uniichat_including_compactions_usd_cli_estimate": 0.468,
    "whole_arm_ratio": 58
  },
  "whole_arm_status": "corrected cumulative-USD differences from raw E3 rows; one run per arm, n=26 turns; rounded ratio"
}
```

Location: manifest limitations

BEFORE
```text
- 'Correction: round-1 E1 script sums cumulative process USD on retry rows. Those retry-arm USD figures remain unrepaired;
  E4 costs use differences.'
```

AFTER
```text
- 'Correction: round-1 E1 script sums cumulative process USD on retry rows; no E1 USD figure was published here.
  E4 costs use differences. Corrected E3 whole-arm USD estimates are 0.635 and 0.461 rather than source-reported
  0.640 and 0.468; ratios remain 5.0 times and about 57 times, n=26 turns per arm.'
```

## Item 8

Applied.

Location: post

BEFORE
```text
They do not describe the longer replay at low effort.
```

AFTER
```text
They do not describe the longer replay at low effort. Round 1's break-even prediction, turn calls cheaper around user message 185-215 and with compactions around message 400 or later for Sonnet and never for Haiku, is superseded by the measured turn 57 and turn 82 under the stated unit weights, on a different script and compactor effort.
```

Location: summary predictions_not_measurements.status

BEFORE
```text
"superseded as guidance by the observed E5 replay; retained as historical round-1 predictions for a different short-chat script"
```

AFTER
```text
"superseded as guidance by measured E5 cumulative crossovers at turns 57 and 82 with W=2, read weight 0.1 and Haiku weight 0.05; historical predictions used a different script and xhigh compactor effort"
```

## Item 9

Applied.

Location: post

BEFORE
```text
| reminder block before the view | 170 | n=1, measured by difference |
```

AFTER
```text
| reminder block before the view | 170 | n=1, measured by difference; replaces round-1 estimate of about 240 |
```

Location: post

BEFORE
```text
| environment block after the message | 357 | n=1, measured by difference |
```

AFTER
```text
| environment block after the message | 357 | n=1, measured by difference; confirms round-1 tail estimate of 356 |
```

The existing summary wrapper-estimate fields already held 240, 356, 170 and 357, n=1 each, and were retained.

## Item 10

Applied.

Location: post

BEFORE
```text
Our longer replay reached the bounded-view regime and measured a cost crossover against a continued Claude Code session.
```

AFTER
```text
Our longer replay reached the bounded-view regime and measured a cost crossover against a continued Claude Code session on turn calls in both accountings. Including compactions, it crossed only at the gist's 0.1-times-input read price, on turn 82; the CLI's USD estimates were level but had not crossed at turn 112, 6.019 versus 5.995.
```

Title and subtitle already limit the measured crossover to cheaper turns. They remain accurate and were retained. Existing summary crossover and endpoint fields already record the price dependence.

## Item 11

Applied.

Location: post

BEFORE
```text
Do the reported cache shares count all input or only the cacheable prefix, and were the simulated shares checked against real usage?
```

AFTER
```text
Your 98.6% and 96.2% are prefix shares from a cache model; have you measured the share of all input on real usage? Ours was 95.6% for turns and 93.0% for compactions.
```

## Item 12

Applied.

Location: post

BEFORE
```text
We said Claude Code's one-hour cache marks could not be changed. That was wrong.
```

AFTER
```text
We said Claude Code's one-hour cache marks could not be changed. That was wrong. The specification notes that subscriptions mark with a one-hour lifetime; that is the default, and an environment setting changes it.
```

Location: summary round_1_corrections.cache_lifetime.replacement

BEFORE
```text
"E6 measured 5-minute writes with CLAUDE_CODE_PROMPT_CACHE_TTL=5m; the trial core also hard-coded 1h on its view mark"
```

AFTER
```text
"The specification notes subscription marks have a one-hour lifetime by default. E6 measured 5-minute writes with CLAUDE_CODE_PROMPT_CACHE_TTL=5m; the trial core also hard-coded 1h on its view mark"
```

## Item 13

Applied.

Location: post

BEFORE
```text
| 100 | turns 76-100, n=25 |
```

AFTER
```text
| 75 | turns 51-75, n=25 | 27,300 | 32,449 | 40,592 | 1,716,425 | 2,153,148 | 2,053,234 |
| 100 | turns 76-100, n=25 |
```

Location: post

BEFORE
```text
UniiChat's turn cost becomes roughly flat while the baseline grows with the accumulated session. The bounded view does not eliminate output, tools or occasional rewrites, so "flat" describes the observed trend rather than a constant charge on every turn.
```

AFTER
```text
From turn 26 on, UniiChat's stretch means range from 27,300 to 34,442 units per turn, against 27,839-86,316 for the baseline. The UniiChat means are 27,882 for turns 26-50, 27,300 for 51-75, 31,266 for 76-100 and 34,442 for 101-112, about a 24% rise from the first stretch to the last. The bounded view does not eliminate output, tools or occasional rewrites; these are stretch means, not a constant charge on every turn.
```

Location: summary round_2.checkpoints

BEFORE
```text
No turn-75 checkpoint.
```

AFTER
```text
{
  "turn": 75,
  "mean_range": [
    51,
    75
  ],
  "n_mean": 25,
  "cumulative_n_turns_per_arm": 75,
  "mean_units_W2": {
    "A_turn": 27300,
    "A_with_compactions": 32449,
    "B": 40592
  },
  "cumulative_units_W2": {
    "A_turn": 1716425,
    "A_with_compactions": 2153148,
    "B": 2053234
  },
  "cumulative_cli_usd": {
    "A_turn": 2.752,
    "A_with_compactions": 3.625,
    "B": 2.779
  },
  "status": "recomputed raw usage; compactions assigned by turn-call start timestamps"
}
```

Location: summary round_2.E5.turn_26_on_stretch_means

BEFORE
```text
"(absent)"
```

AFTER
```text
{
  "intervals": [
    {
      "turns": [
        26,
        50
      ],
      "n": 25,
      "means": [
        27882,
        35544,
        27839
      ]
    },
    {
      "turns": [
        51,
        75
      ],
      "n": 25,
      "means": [
        27300,
        32449,
        40592
      ]
    },
    {
      "turns": [
        76,
        100
      ],
      "n": 25,
      "means": [
        31266,
        38139,
        60898
      ]
    },
    {
      "turns": [
        101,
        112
      ],
      "n": 12,
      "means": [
        34442,
        40933,
        86316
      ]
    }
  ],
  "n_turns": 87,
  "runs_per_arm": 1,
  "A_turn_mean_range": [
    27300,
    34442
  ],
  "B_turn_mean_range": [
    27839,
    86316
  ],
  "first_to_last_stretch_rise_percent_rounded": 24,
  "status": "recomputed raw usage under W=2 and read weight 0.1; intervals are means, not individual-turn bounds"
}
```

## Item 14

Applied.

Location: summary round_2.E5.stock_tools_comparison

BEFORE
```text
"(absent)"
```

AFTER
```text
{
  "stock_units": 889826,
  "thinned_units": 625676,
  "n_turns_per_arm": 37,
  "runs_per_arm": 1,
  "status": "recomputed raw turn usage, W=2 and read weight 0.1; stock and thinned continued sessions"
}
```

Location: summary round_2.E5.baseline_cache_input_tokens

BEFORE
```text
"(absent)"
```

AFTER
```text
{
  "cache_read_tokens": 32279785,
  "all_input_side_tokens": 32624884,
  "cache_read_millions_rounded": 32.28,
  "all_input_side_millions_rounded": 32.62,
  "n_turns": 112,
  "runs": 1,
  "status": "recomputed raw usage; all input-side tokens includes input, cache write and cache read"
}
```

Location: summary round_2.E4_low_usd_accounting

BEFORE
```text
"(absent)"
```

AFTER
```text
{
  "naive_cumulative_sum": 0.412,
  "corrected_differenced_sum": 0.231,
  "n_sends": 318,
  "runs": 1,
  "status": "recomputed from raw low-effort rows; subscription CLI estimates, not invoices"
}
```

Location: summary round_2.E4_level5_exact_items

BEFORE
```text
"(absent)"
```

AFTER
```text
{
  "kept_range": [
    17,
    25
  ],
  "n_planted_items": 232,
  "kept_by_effort": {
    "low": 25,
    "medium": 25,
    "high": 23,
    "xhigh": 17
  },
  "runs_per_effort": 1,
  "status": "stored harness exact-substring grades, not independently regraded; paraphrases count as absent, not a recall error rate"
}
```

Location: summary round_1_scaled_42_messages

BEFORE
```text
"(absent)"
```

AFTER
```text
{
  "turn_model": "haiku",
  "n_turns_per_arm": 42,
  "runs_per_arm": 1,
  "uniichat_turn_calls_weighted_tokens": 219094,
  "continued_session_weighted_tokens": 119060,
  "ratio_at_write_weight_2": 1.84,
  "status": "recomputed raw usage; scaled view limits; compactions excluded; continued Haiku arm reused"
}
```

Location: manifest status

BEFORE
```text
status: draft
```

AFTER
```text
status: evidence-local
```

Location: manifest summary hash

BEFORE
```text
b812c727a97cb8bc70fa58a54870716fffc869b119065c3a05ec42cd09112654
```

AFTER
```text
e4d6b9afaeb7b65beec22c3eca0cb89fe0daedb4c828404c19e3f98ab49545f7
```

The requested 23,690, 4,852 and 5/63 figures and 63-turn definition were added with items 3 and 1. Batch sizes 63,688-63,843 and n=3 were added with item 2. No denominator claim of 73 remains; historical audit line number 73 is a locator, and digits inside unrelated measurements are unchanged.

## Item 15

Applied.

Location: post

BEFORE
```text
Round 1 used `fd454e7`.
```

AFTER
```text
Round 1 used `fd454e7`. It tested gist revision `3c190e06`, dated October 8, 2026 and fetched October 11, 2026.
```

## Privacy edits

Location: summary round_2.provenance.authoritative_report

BEFORE
```text
"workflow journal.jsonl result at line 9, final skeptical report"
```

AFTER
```text
"Final skeptical report; aggregate conclusions retained in this frozen summary"
```

Location: summary round_2.provenance.experiment_reports

BEFORE
```text
{
  "E4": "journal result line 3",
  "E6": "journal result line 6",
  "E5": "journal result line 7"
}
```

AFTER
```text
{
  "E4": "Compactor sweep report",
  "E6": "Overhead and cache-lifetime report",
  "E5": "Long replay report"
}
```

Location: summary round_2.provenance.priority

BEFORE
```text
"line 9 overrides experiment results where they differ"
```

AFTER
```text
"Final skeptical report takes precedence over experiment reports where they differ"
```

Location: summary round_2.provenance.number_audit

BEFORE
```text
".review/number-sources.md"
```

AFTER
```text
Removed unpublished-file reference.
```

Location: manifest rounds.round_2.evidence_priority

BEFORE
```text
    evidence_priority: Final skeptical journal result, line 9, overrides E4 line 3, E6 line 6 and E5 line 7
```

AFTER
```text
    evidence_priority: Final skeptical report takes precedence over the E4, E6 and E5 experiment reports where they differ
```

Location: post limits

BEFORE
```text
The number-source review records the accounting derivations and the distinction between recomputed usage, harness grades and paper estimates.
```

AFTER
```text
The frozen summary distinguishes recomputed usage, harness grades and paper estimates.
```
