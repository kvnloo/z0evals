# Number sources for the combined post

The historical index below uses pre-correction post line numbers, including repeated denominators, dates, identifiers and formula coefficients. Round-2 correction evidence and the current post digest are appended below. Counts written as words are covered by the prose-count supplement below. Identifiers and dates are not measurements. This index applies to post SHA-256 `d8a94388ccaffaf67391510b7de1585f8e9621ec804869519db9752de861e5cd`.

Source names below are relative to the supplied trial evidence, not paths embedded in the public post. No raw request bodies or private conversations are copied here.

- **J3 / J6 / J7 / J9:** `journal.jsonl`, workflow `wf_ceef584c-19b`, result lines 3 / 6 / 7 / 9. They are E4 / E6 / E5 / final skeptical report, respectively. J9 takes priority. Its keys `economics`, `compactor_tradeoff`, `correctness_and_compliance`, `harness_bloat_answer`, `numbers_that_did_not_recompute` and `calls_used` contain the audited conclusions.
- **S:** saved specification `optchat-spec/optchat.md`, sections 3.2 and 3.3 for view sizes and price assumptions, section 4 for line limits, section 5 for prompt quotations. The public revision is pinned in the manifest. These are source-reported design constants, not trial measurements.
- **L1 / L2:** `optchat-trial/results/ledger.jsonl` / `ledger-r2.jsonl`. Sum signed `n` by `family` and experiment prefix. `settle` rows already have negative `n`; do not negate them again. Round-1 programme scope includes probes. J9 `calls_used` confirms the totals.
- **C4:** `results/E4/{haiku-low,haiku-medium,haiku-high,haiku-xhigh,sonnet-low,sonnet-medium}/calls.jsonl`; per-send `usage`, `wall_s`, `label`, `send`, cumulative `cost_usd_reported`, and `events`.
- **A4:** `results/E4/analysis.json`, `arms`, `prefix32`, `qa`, `qa_haiku_reader`, `qa_haiku_reader_2`. Arm order in the full sweep table is low, medium, high, xhigh. Rule/correction fields are harness regex grades; scores are parsed-answer grades. Corpus denominator fields are in `corpus/{messages.jsonl,items.json,orders.json,corrections.json,questions.json}`.
- **T5 / C5:** `results/E5/{A,B,B2,opus-A,opus-B}/turns.jsonl` / `calls.jsonl`. Use the last row per `n` for resumed turn rows. A turn rows supply `usage`, `logged_to`, `view_bytes_sent`, `batch_merges`, `waited_s`; call rows supply `ts`, `label`, `usage`, `model_usage`, `events`, `cost_usd_reported` and `wall_s`.
- **A5:** `results/E5/analysis.json`, `totals`, `requests`, `batches`, `lookback`, `grades`, `opus`, `A_replied_as_a_compaction_line`, `edit_turns_with_no_file_change`. Cost checkpoints in the old file are superseded by J9's corrections. Outcome grades remain reported, not independently regraded. `script.json` contains the actual script and keyed outcomes.
- **A6 / I6:** `results/E6/analysis.json` / `{thin,turns5m,mid5m,gap5m}/index.jsonl` and `stock/usage.jsonl`. Overhead uses `input + cache_write + cache_read`; the two small block sizes are differences from the base probe. `capture/shapes.txt` is request-shape evidence only, never live pi usage.
- **Trees:** `chats/e5-A/tree/2026-10-12.jsonl` for final node count and sizes; `chats/e4-<arm>/tree` for built-line size checks. The trial Git objects resolve `098433d` and `fd454e7` to the full immutable manifest revisions.

## Cost recipes, checked from the raw rows

Let U(W,R) = `input_tokens + W*cache_creation_input_tokens + R*cache_read_input_tokens + 5*output_tokens`. Output already includes thinking. The post's unit uses R=0.1. Its observed runs use W=2; five-minute repricing uses W=1.25. These coefficients are declared accounting assumptions, not subscription charges.

Sort the last A turn row for each `n`. For each, look up its turn call by `label = "turn " + message`. Assign a compaction by its `ts` to the interval between successive turn-call `ts` values, not the turn row's earlier `t0`. Include the final background tail in the last interval. This yields 474 / 1,125 / 2,140 / 2,383 compaction sends at checkpoints 25 / 50 / 100 / 112, matching J9 `numbers_that_did_not_recompute`.

Turn units are summed from T5 A and B `usage`. Add Haiku compaction U(2,0.1) multiplied by 0.05 for the corrected combined unit table. Cumulative n is the checkpoint; per-turn means use the stated interval's n. Whole units are rounded only after summation. With the discarded blended weight 0.0627, the same corrected assignment reproduces J9 checkpoint totals 482,909 / 1,420,160 / 3,261,190 / 3,772,166. The public post uses the corrected 0.05 price ratio instead. Both reconciliation figures and public-table results are frozen in summary.json.

For CLI USD, Sonnet is `U(2,0.05)*2e-6`; Haiku is `U(2,0.1)*1e-7`. The fitted input/write/read/output prices reproduce the CLI cost rows after taking differences within retry processes and resumed sessions. Table USD is rounded to three decimals. The 5.995 baseline figure is the precise endpoint rounded to three decimals, rather than choosing between the reports' 5.99 and 6.00 prose rounding. Cumulative USD crosses on turn calls at 80 but never including compactions through 112.

A cumulative crossover is the first index from which every remaining cumulative difference is non-positive. Direct recomputation gives 57 / 82 with W=2, 32 / 71 with W=1.25, and 80 / none with CLI USD. These match J9's corrected economic interpretation. Five-minute long-run values are repriced observations, not a five-minute replay.

For E4 cost per line, take cumulative process USD differences per `(label, send)` retry sequence, resetting on send 1, or reconstruct from Haiku token weights. Sum cost and divide by `lines.model_built`. Sum `wall_s` and divide by the same denominator for call-seconds per line, which is not elapsed tree-build time. Thinking-per-send divides summed thinking by actual send rows. First-fit/final-fit comes from node size and per-label build history, as audited by J9.

For tool events, join each assistant `tool_use.id/name` to user `tool_result.tool_use_id/is_error` within a compactor send. There are 266 tool-call sends and 273 tool calls. Non-error shell results are 159; six shell results are errors. The final report called all six “denied”, but one is a runtime error. Its one unsuccessful edit is string-not-found, not a permission refusal. The post retains the final counts and uses accurate outcome labels. Memory-tool failures are explicit denials. A non-error file read occurred once. These are execution observations, not verified task success.

## Every numeric-bearing post line

| post line | numeric occurrences, in order | source file and field or recipe |
|---|---|---|
| 4 | `0` | Existing front-matter convention: study/author identifiers; publication date updated to 2026-10-12. Round labels are editorial identifiers. |
| 6 | `0` | Existing front-matter convention: study/author identifiers; publication date updated to 2026-10-12. Round labels are editorial identifiers. |
| 7 | `12,`, `2026` | Existing front-matter convention: study/author identifiers; publication date updated to 2026-10-12. Round labels are editorial identifiers. |
| 13 | `1` | Existing front-matter convention: study/author identifiers; publication date updated to 2026-10-12. Round labels are editorial identifiers. |
| 42 | `64`, `128`, `1.25`, `0.1` | S §3.2 `128,000` high / `64,000` low bytes, expressed as KB; §3.3 source write/read price weights 1.25/0.1. |
| 46 | `1`, `2` | J3/J6/J7 `experiment` and `completed`; round and experiment names are identifiers. |
| 48 | `250`, `260`, `112` | J7 `experiment`/`completed`; E5/script.json script length 260; A5 `turns_common=112`; 250 is the brief label, not a measured endpoint. |
| 52 | `1,`, `1,082`, `205`, `56` | L1 signed n by family including probes; existing summary `requests.programme_total`; J9 `calls_used` round-1 comparison. |
| 53 | `2,`, `4`, `1,099`, `235`, `0` | L2 signed n by experiment prefix E4/E5/E6 and family; J9 `calls_used` experiment table. |
| 54 | `2,`, `5`, `2,387`, `643`, `40` | L2 signed n by experiment prefix E4/E5/E6 and family; J9 `calls_used` experiment table. |
| 55 | `2,`, `6`, `43`, `9`, `0` | L2 signed n by experiment prefix E4/E5/E6 and family; J9 `calls_used` experiment table. |
| 57 | `2`, `098433`, `1`, `454`, `7` | Trial Git revisions / manifest source pins; J7 `core_changes`; J3 `core_changes`; J9 `claims` background-compaction entry. |
| 59 | `1` | J6 `findings` and `core_changes`, I6 cache write classes/environment setting; heading/round/E6 identifiers. |
| 61 | `6`, `5` | J6 `findings` and `core_changes`, I6 cache write classes/environment setting; heading/round/E6 identifiers. |
| 63 | `24`, `8`, `1`, `330` | A6 `e2_turns_haiku.n_warm_turns=24`, `e2_turns_sonnet.n_warm_turns=8`; I6 gap5m label `3-after-330s-pause`; J9 `claims` cache-lifetime entry. One expiry sample. |
| 65 | `1`, `1`, `0.412`, `0.231`, `318`, `1`, `1` | C4 haiku-low cumulative USD naive sum versus differenced sum rounded to 0.412/0.231, n=318 rows; J3 `findings` cost-sum correction, J9 `compactor_tradeoff`; round/E1 identifiers. |
| 71 | `1` | J6 `findings` and `core_changes`, I6 cache write classes/environment setting; heading/round/E6 identifiers. |
| 73 | `26`, `1.45` | E3/sonnet-A and sonnet-B calls usage U(2,0.1), 26-turn paired scope; A6 `e3.sonnet.uniichat_cc_1h_measured.cost / continued_cc_1h_measured.cost = 110260/76297`, rounded ratio. |
| 74 | `26`, `1.54` | E3/haiku-A and first 26 haiku-B calls U(2,0.1), 26-turn paired scope; A6 `e3.haiku` measured cost fields, ratio rounded to 1.54; J9 `economics` short chats. |
| 75 | `42`, `1.84` | E3/scaled-A and haiku-B calls U(2,0.1), all 42 turns; haiku-B is the continued-session comparison reused for this scaled run; A6 `e3.scaled-haiku` measured cost fields, ratio rounded to 1.84; J9 `economics` short chats. |
| 81 | `1,161`, `2,318`, `52,`, `77`, `103,`, `127,752` | T5 final A `logged_to+1=1161`; Trees row count 2318; A5 `batches[].turn` and max T5 A `view_bytes_sent=127752`; J9 `claims` bounded context. |
| 85 | `52`, `348`, `124,266`, `65,652` | A5 `batches[]`: `turn`, `pairs_merged`, `view_bytes_sent_this_turn`, `view_bytes_after_this_turn`; T5 A matching `n`; J9 `claims` bounded context. |
| 86 | `77`, `263`, `118,428`, `67,467` | A5 `batches[]`: `turn`, `pairs_merged`, `view_bytes_sent_this_turn`, `view_bytes_after_this_turn`; T5 A matching `n`; J9 `claims` bounded context. |
| 87 | `103`, `276`, `127,752`, `65,634` | A5 `batches[]`: `turn`, `pairs_merged`, `view_bytes_sent_this_turn`, `view_bytes_after_this_turn`; T5 A matching `n`; J9 `claims` bounded context. |
| 89 | `0.1`, `5`, `2`, `1.25` | Declared cost recipe U(W,R), J9 `economics`; S §3.3 prices; W=2 observed write class, W=1.25 hypothetical repricing; 5 is study output weight. |
| 91 | `0.05`, `5` | J9 `numbers_that_did_not_recompute[0:2]`: fitted Haiku/Sonnet input/write/output ratio 0.05; fitted C5 CLI costs. E5 is an identifier. |
| 93 | `5` | J9 `economics` and `numbers_that_did_not_recompute` corrected checkpoint discussion; E5 identifier. |
| 97 | `25`, `1`, `25,`, `25`, `13,475`, `18,133`, `13,699`, `336,881`, `453,331`, `342,472` | T5/C5 cost recipes above; summary `round_2.checkpoints[turn]`: interval bounds/n, mean_units_W2 and cumulative_units_W2 |
| 98 | `50`, `26`, `50,`, `25`, `27,882`, `35,544`, `27,839`, `1,033,920`, `1,341,926`, `1,038,436` | T5/C5 cost recipes above; summary `round_2.checkpoints[turn]`: interval bounds/n, mean_units_W2 and cumulative_units_W2 |
| 99 | `100`, `76`, `100,`, `25`, `31,266`, `38,139`, `60,898`, `2,498,064`, `3,106,617`, `3,575,688` | T5/C5 cost recipes above; summary `round_2.checkpoints[turn]`: interval bounds/n, mean_units_W2 and cumulative_units_W2 |
| 100 | `112`, `101`, `112,`, `12`, `34,442`, `40,933`, `86,316`, `2,911,371`, `3,597,811`, `4,611,482` | T5/C5 cost recipes above; summary `round_2.checkpoints[turn]`: interval bounds/n, mean_units_W2 and cumulative_units_W2 |
| 106 | `112` | T5 distinct last n per A/B, n=112; J9 `economics` scope. |
| 108 | `57`, `82` | J9 `economics` corrected cumulative crossover; direct cumulative recipe W=2, Haiku weight 0.05: 57/82. |
| 109 | `32`, `71` | J9 `economics` cumulative crossover; direct cumulative recipe W=1.25, Haiku weight 0.05: 32/71; repriced only. |
| 110 | `80` | J9 `economics`; direct CLI cumulative recipe: turn-only 80, combined not reached. |
| 118 | `25`, `0.588`, `0.821`, `0.525` | T5/C5 fitted CLI USD recipe above; summary `round_2.checkpoints[turn].cumulative_cli_usd`; cumulative n=checkpoint. |
| 119 | `50`, `1.693`, `2.309`, `1.490` | T5/C5 fitted CLI USD recipe above; summary `round_2.checkpoints[turn].cumulative_cli_usd`; cumulative n=checkpoint. |
| 120 | `100`, `3.992`, `5.209`, `4.708` | T5/C5 fitted CLI USD recipe above; summary `round_2.checkpoints[turn].cumulative_cli_usd`; cumulative n=checkpoint. |
| 121 | `112`, `4.646`, `6.019`, `5.995` | T5/C5 fitted CLI USD recipe above; summary `round_2.checkpoints[turn].cumulative_cli_usd`; cumulative n=checkpoint. |
| 123 | `0.1`, `0.05`, `0.1` | J9 `numbers_that_did_not_recompute[0:2]`; Sonnet read/input fitted ratio 0.05, Haiku 0.1, declared unit read weight 0.1. |
| 125 | `32.28`, `32.62`, `112` | A5 `totals.B.cr=32279785`; input-side total = in494 + cw344605 + cr32279785 = 32624884, rounded to millions; T5 n=112. |
| 131 | `95.6`, `112` | A5 `totals.A_turn.cache_read_share_of_input=0.9556`, n=112 distinct A turns. |
| 132 | `93.0`, `2,383` | A5 `totals.A_comp.cache_read_share_of_input=0.9297`; C5 compaction rows n=2383. |
| 133 | `98.9`, `112` | A5 `totals.B.cache_read_share_of_input=0.9894`, n=112 distinct B turns. |
| 139 | `4`, `128`, `5,`, `40` | A4 arms.*.messages=128; levels keys 0..5; qa.*.n=40; corpus message/question row counts; J3 `experiment`. |
| 145 | `171`, `177`, `178`, `179` | A4 `arms.<Haiku effort>.lines.model_built`; J9 `compactor_tradeoff` / `numbers_that_did_not_recompute` confirms matched scope. |
| 146 | `318`, `274`, `212`, `184` | A4 `arms.<Haiku effort>.sends`; J9 `compactor_tradeoff` / `numbers_that_did_not_recompute` confirms matched scope. |
| 147 | `94`, `171`, `112`, `177`, `144`, `178`, `174`, `179` | A4 `arms.<Haiku effort>.lines.first_try_fit / model_built`; J9 `compactor_tradeoff` / `numbers_that_did_not_recompute` confirms matched scope. |
| 148 | `170`, `171`, `177`, `177`, `178`, `178`, `179`, `179` | A4 `arms.<Haiku effort>.lines.final_fit / model_built`; J9 `compactor_tradeoff` / `numbers_that_did_not_recompute` confirms matched scope. |
| 149 | `0.00135`, `0.00159`, `0.00246`, `0.00657` | A4 `arms.<Haiku effort>.cost.usd_per_line; C4 corrected cost recipe`; J9 `compactor_tradeoff` / `numbers_that_did_not_recompute` confirms matched scope. |
| 150 | `6.5`, `8.5`, `15.5`, `47.7` | A4 `arms.<Haiku effort>.cost.wall_per_line_s; C4 sum wall_s / model_built`; J9 `compactor_tradeoff` / `numbers_that_did_not_recompute` confirms matched scope. |
| 151 | `1.86`, `1.55`, `1.19`, `1.03` | A4 `arms.<Haiku effort>.cost.sends_per_line; rows / model_built`; J9 `compactor_tradeoff` / `numbers_that_did_not_recompute` confirms matched scope. |
| 152 | `462`, `980`, `2,954`, `11,572` | A4 `arms.<Haiku effort>.usage.all.per_send.thinking, rounded; C4 summed output_tokens_details.thinking_tokens / n rows`; J9 `compactor_tradeoff` / `numbers_that_did_not_recompute` confirms matched scope. |
| 153 | `4`, `318`, `1`, `274`, `0`, `212`, `0`, `184` | A4 `arms.<Haiku effort>.flags.tool_call_sends / sends; C4 events`; J9 `compactor_tradeoff` / `numbers_that_did_not_recompute` confirms matched scope. |
| 154 | `5`, `13`, `9`, `8`, `12`, `12` | A4 `arms.<Haiku effort>.fidelity.5.standing = [present,13], reported regex`; J9 `compactor_tradeoff` / `numbers_that_did_not_recompute` confirms matched scope. |
| 155 | `5`, `10`, `7`, `7`, `10`, `8` | A4 `arms.<Haiku effort>.fidelity.5.corrections = [present,10], reported regex`; J9 `compactor_tradeoff` / `numbers_that_did_not_recompute` confirms matched scope. |
| 156 | `40`, `38`, `39`, `40`, `38` | A4 `qa.<Haiku effort>.right / n=40, parsed grades`; J9 `compactor_tradeoff` / `numbers_that_did_not_recompute` confirms matched scope. |
| 158 | `4.9`, `519` | A4 cost.usd_per_line xhigh/low, unrounded C4 ratio 4.87 rounds to 4.9; low lines.final_sizes_over=[519]; J9 `compactor_tradeoff`. |
| 162 | `40` | A4 qa_haiku_reader / qa_haiku_reader_2 correct scores, n=40; J9 `still_untested` repeated reader maximum difference two. |
| 168 | `32`, `45`, `0.01504`, `10`, `10` | A4 `arms.sonnet-low.messages=32, lines.model_built=45, cost.usd_per_line=0.01504; qa.sonnet-low.right/n=10/10`; J9 `compactor_tradeoff` / `numbers_that_did_not_recompute` confirms matched scope. |
| 169 | `32`, `45`, `0.01553`, `10`, `10` | A4 `arms.sonnet-medium.messages=32, lines.model_built=45, cost.usd_per_line=0.01553; qa.sonnet-medium.right/n=10/10`; J9 `compactor_tradeoff` / `numbers_that_did_not_recompute` confirms matched scope. |
| 173 | `23`, `2,383`, `5`, `58` | C5 Haiku reconstructed USD / total A USD ~=23%, n=2383; J9 `economics`. Historical 5/58: snapshot whole-arm table and summary cost_26_messages, scoped xhigh, not new outcomes. |
| 177 | `1,000,000`, `344,607`, `112` | C5 B model_usage.*.contextWindow=1000000; A5 B_session.prompt_tokens_last=344607 and auto_compaction_events=[]; T5 B n=112. |
| 181 | `50`, `54`, `54`, `54` | A5 `grades.{A,B}.recall.all pass and fail sum`; J9 `correctness_and_compliance`; outcomes are reported grades, not independently regraded. |
| 182 | `13`, `16`, `16`, `16` | A5 `grades.{A,B}.recall_by_category.correction pass/fail`; J9 `correctness_and_compliance`; outcomes are reported grades, not independently regraded. |
| 183 | `5`, `63`, `0`, `63` | A5 `edit_turns_with_no_file_change lengths; script reached add/fix/probe n=63 (27+18+18 among 112 completed turns)`; J9 `correctness_and_compliance`; outcomes are reported grades, not independently regraded. |
| 184 | `351`, `351`, `383`, `383` | A5 `grades.{A,B}.comply_all_edit_turns.all.pass`; J9 `correctness_and_compliance`; outcomes are reported grades, not independently regraded. |
| 185 | `31`, `2` | A5 `grades.{A,B}.not_gradable.all.na`; J9 `correctness_and_compliance`; outcomes are reported grades, not independently regraded. |
| 186 | `4`, `1` | A5 `grades.{A,B}.not_gradable.all.blocked`; J9 `correctness_and_compliance`; outcomes are reported grades, not independently regraded. |
| 187 | `27`, `27`, `27`, `27` | A5 `grades.{A,B}.probe_traps.all.pass`; J9 `correctness_and_compliance`; outcomes are reported grades, not independently regraded. |
| 188 | `12`, `112` | A5 `A_replied_as_a_compaction_line list length 12; turns_common=112`; J9 `correctness_and_compliance`; outcomes are reported grades, not independently regraded. |
| 200 | `10`, `11`, `12` | A5 `opus.turns_common=10; opus.A.recall.all pass=11, fail=1`; J9 `correctness_and_compliance`; outcomes are reported grades, not independently regraded. |
| 201 | `10`, `12`, `12` | A5 `opus.turns_common=10; opus.B.recall.all pass=12`; J9 `correctness_and_compliance`; outcomes are reported grades, not independently regraded. |
| 205 | `4`, `17`, `25`, `232`, `5,` | A4 arms.<Haiku effort>.fidelity.5.items: low [25,232], medium [25,232], high [23,232], xhigh [17,232]; exact-substring lower bound; level 5 is tree depth. |
| 209 | `12`, `112` | A5 A_replied_as_a_compaction_line length12, turns_common112; J9 `claims` shared prompt notes narrower regex9; use broad harness count. |
| 215 | `2,383` | C5 compaction row count=2383; J9 `claims` tool calls and `numbers_that_did_not_recompute`. |
| 217 | `266,`, `11.2` | C5 event-bearing sends=266 / 2383 =11.162%, rounded11.2; J9 `claims` tool calls and `numbers_that_did_not_recompute`. |
| 218 | `159` | C5 joined Bash tool_result.is_error false count159; J9 `claims` tool calls and `numbers_that_did_not_recompute`. |
| 219 | `1` | C5 joined Read tool_result.is_error false count1; J9 `claims` tool calls and `numbers_that_did_not_recompute`. |
| 220 | `102` | C5 joined mcp__chat__zoom tool_result errors/denials count102; J9 `claims` tool calls and `numbers_that_did_not_recompute`. |
| 221 | `4` | C5 joined mcp__chat__date tool_result errors/denials count4; J9 `claims` tool calls and `numbers_that_did_not_recompute`. |
| 222 | `6` | C5 joined Bash tool_result.is_error true count6; J9 `claims` tool calls and `numbers_that_did_not_recompute`. |
| 223 | `1` | C5 joined Edit tool_result.is_error true count1, string-not-found; J9 `claims` tool calls and `numbers_that_did_not_recompute`. |
| 231 | `112`, `3.8`, `95.0` | T5/A wait_view scheduling reconstruction; A5 per_turn A.wait_view_after_s; J9 `claims` wait entry median3.8/max95.0, n112; not isolated user latency. |
| 233 | `95`, `90` | A5 lookback[].lines_added=[95,90], n2; corresponding next-turn cache writes and batch overlap; T5/A appended message deltas. |
| 237 | `1`, `6` | J6 completed/findings; J9 harness_bloat_answer. Round/E6 identifiers; wrapper count two from I6 thin probes. |
| 241 | `23,690`, `2`, `1,` | C5/B2 first per_request input-side sum23690, n1; J9 harness_bloat_answer |
| 242 | `27,295`, `1,` | I6 stock/usage.jsonl input+cache_creation+cache_read=27295, n1; A6 overhead.cc_stock_owner_config |
| 243 | `2,253`, `2,` | I6 thin/index labels haiku/base and base-again, input+cache_write+cache_read=2253, n2, trivial-message Haiku probes with round-1 flags; separate from E5 matched comparison |
| 244 | `1,641`, `2` | I6 thin/index base cache_read=1641, n2 probes; A6 overhead.tools_plus_system_entry |
| 245 | `170`, `1,` | I6 thin plus-reminder-text minus base input-side sum=170, n1; A6 overhead.cc_reminder_block_tokens |
| 246 | `357`, `1,` | I6 thin plus-environment-text minus base input-side sum=357, n1; A6 overhead.cc_environment_tail_tokens |
| 247 | `1,726` | A6 overhead inferred pi subscription token estimate=1726; subtraction2253-170-357; J9 harness_bloat_answer; inferred, live n0 |
| 249 | `37`, `889,826`, `625,676` | C5/T5 B2 distinct turns37 and U(2,0.1)=889826; T5/B first37 U(2,0.1)=625676; J9 economics B2 table. |
| 251 | `6` | J6 completed/findings; J9 harness_bloat_answer. Round/E6 identifiers; wrapper count two from I6 thin probes. |
| 261 | `112`, `260` | E5/script.json length260; A5 turns_common112; J9 still_untested. Completion versus inference explicitly separated. |

## Prose counts written as words

- One run/tree per principal arm or effort: J3/J7 `limits`, J9 `still_untested`; supplementary Haiku-reader repeat is the stated exception. “Two rounds” and round/experiment labels identify programme structure, not sample sizes.
- Three real batches: A5 `batches` length, T5 A `batch_merges`, J9 `claims`; individual turns and merge counts are indexed above.
- One expiry sample: I6 `gap5m/index.jsonl`, one three-step sequence; J9 cache-lifetime claim. Five-minute and one-hour lifetime words specify cache policy; price weights and observed/repriced statuses are given above.
- Three of four recall misses on one turn, eight-request allowance: A5 `grades.A.failures`, three empty answers at turn105 and one unapplied correction at turn99; T5 A turn105 `requests=8` and cut status; J9 `correctness_and_compliance`. These remain source grades with cause inspection.
- Five skipped edits: A5 `edit_turns_with_no_file_change.A` has five entries, with reached add/fix/probe denominator63; ungradable checks are separately counted.
- Each candidate answering two or three of five planted requests: J9 `claims` compaction obedience entry and J3 `findings`; A4 arms.*.obeyed and C4 reply/result text were inspected, not counted by raw `obeyed_canaries` hits, which duplicate text variants and tree levels. Five is the planted-request denominator, not the number of independently repeated chats.
- One halt and resumed retry adjustment; unused high-effort fallback: J7 `completed`/`limits`, E5/halts.jsonl; A5 current turn sequence uses the last row per n. This is one fold, not a second independent run.
- Two wrapper blocks: I6 thin/index differences and A6 overhead; reminder and environment sizes indexed above. “At best parity” for the paper Sonnet estimate is A6 `e3.sonnet.uniichat_pi_5m_paper.cost / continued_cc_1h_measured.cost = 76109/76297`, not a live pi result. No live pi calls: L2 route/model counts and J6 completed, J9 calls_used.
- Up to two reader-answer differences out of forty: A4 supplementary Haiku reader paired aggregate correct fields, J9 still_untested. No variance estimate follows from this repeat.
- “One unit” and output weight five are study definitions, not measured sample counts. Halving the Sonnet read price is the fitted0.05 versus declared0.1 ratio.

## Checks performed for this revision

The signed ledger totals, unit and USD checkpoint recipes, corrected legacy-blend totals, cumulative crossovers, E4 per-line cost/call-seconds/thinking aggregates, raw E5 tool result counts, E5 node count, E6 stock/remaining-block sizes and source-grade fields were inspected or recomputed. Claims and prompt quotations were checked against the saved specification. No model calls, new daemons or provider-price lookups were needed. The post reports this frozen CLI accounting, not current provider prices.

A6's short-chat five-minute ratio wording and J9's compressed description can hide the paper wrapper subtraction. This post avoids those ambiguously labelled numeric ratios: it prints the observed round-1 ratios, identifies pi parity as paper and specifies the unchanged one-hour baseline in that paper comparison. E6's discrepant compaction-unit total and the unresolved E4 maximum-tries claim are also omitted, as instructed by the final audit.


## Round-2 correction evidence

Current post SHA-256: `71b54fb15bc4f5ace667a3ea03bd988590d19683852826b97c0f699c99d5cb8d`. Historical line numbers above are not current locators.

- Edit denominator: E5 script kinds add=27, fix=18, probe=18, n=63 among 112; raw A unchanged turns 35,49,50,59,80, B none.
- Batch completion: raw A mid-turn batch sizes 63,843, 63,688, 63,753; all below 64,000, n=3. Later messages explain table end-of-turn sizes.
- Matched overhead: first B2 and B per-request input-side sums 23,690 and 4,852, same message, n=1 each; B lists four tools. The 2,253 Haiku probes are a different sample.
- Reply format: raw reply regex plus script gives 6 orders, 3 facts, 2 corrections, 1 fix; only turn35 overlaps unchanged edits.
- E1 default-effort raw rows: 5 zoom sends among 271. Stored Sonnet arithmetic-bait entries identify two bait messages in 8 distinct nodes.
- E4 stored retained-line bait classifications identify two distinct requests per Haiku effort. Sonnet-medium raw replies contain both 1517 and 5040, so the requested single-answer claim is not applied. Partial 32-message corpus excludes later baits.
- E3 retry differencing gives 0.63515381 and 0.46074998; baseline 0.1277671 and 0.00810401; ratios 4.971 and 56.855, rounded in post to5.0 and about57. Historical source-reported totals0.640/0.468 and ratios5.0/58 are preserved as such. No E1 USD figure was published here.
- E5 intervals26-50/51-75/76-100/101-112 recompute to A means27,882/27,300/31,266/34,442; B27,839/40,592/60,898/86,316. First-to-last A stretch rises23.53%, about24%. Turn75 means27,300/32,449/40,592; cumulative1,716,425/2,153,148/2,053,234.
- E5 stock/thinned37-turn totals889,826/625,676. Baseline112-turn reads32,279,785 of32,624,884 input-side tokens, rounded32.28M/32.62M.
- E4 low318 sends: naive0.41234329, corrected0.23076418. Stored level5 exact-item grades low25, medium25, high23, xhigh17 out of232; not independently regraded.
- E3 scaled42-turn units219,094.2/119,060.4 =1.84019, compactions excluded.
- E5 cumulative crossovers recompute to units57/82 and CLI USD80/none; endpoint combined6.01897123 versus baseline5.9949865. Long5m values remain repriced.
- E6 reminder170 replaces approximate240; tail357 confirms approximate356. Saved specification describes subscription1h marks and cache-model prefix shares98.6%/96.2%; manifest pins gist revision3c190e06, dated2026-10-08, fetched2026-10-11.

Aggregate-only recomputation is reproducible with `verify-round2.py` and the existing raw results directory as its argument. Output is retained in `round2-verification.json`. No raw messages or request bodies are copied.
