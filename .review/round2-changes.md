# Round-2 revision audit

The existing snapshot was confirmed before rewriting and was not edited. Its SHA-256 is `96db66f09fe4a85b73d07fd3f12389cc335e68265745374f562ecc4e24956ce2`.

The post now tells one combined account. It opens with an exact quote from the saved UniiChat specification and treats the continued-session cost comparison as this study's choice. It reports the longer replay's bounded-view batches and crossover, then separates that result from the memory advantage that remains untested. The continued session never auto-compacted and was perfect on the harness's recall grades.

The final skeptical result in `journal.jsonl`, line 9, is authoritative over experiment results at lines 3 (E4), 6 (E6) and 7 (E5), in workflow `wf_ceef584c-19b`. The raw source files are in the sibling `optchat-trial/results` tree. No raw conversations, prompts or request bodies were imported into the publication files.

The cost tables use the final audit's corrected checkpoint assignment and Haiku's 0.05 relative weight, with the unit's 0.1 cache-read weight kept explicit. The audit's earlier-blend checkpoint totals are independently reproduced in `summary.json` for reconciliation. USD is reconstructed separately with the CLI Sonnet read weight 0.05. Five-minute long-run values are repricing, not a live replay. Pi is paper only.

Round-1 values remain in the summary, with correction metadata and historical scope. The manifest adds the full round-2 commit, call counts, experiment scope, measured/reported/inferred distinctions and a refreshed summary digest. Unrepaired E1 retry-cost figures are identified rather than guessed. The number-source audit enumerates numeric-bearing post lines and their fields or derivations.

The following inventory includes factual retractions, corrected estimates, superseded limitations and scoped statements whose wording no longer fits a combined post. A historical statement is not called false merely because round 2 differs. Every blockquote below is verbatim from the snapshot.

## 1. Opening conclusion and cost framing

> <div class="lede">
> the specification says a chat can run forever at a constant context size, with nearly every token read from the prompt cache. we rebuilt it as closely as the claude code cli allows and ran it beside an ordinary continued session. the specification makes no cost claim against such a session; that comparison is ours. the parts we could exercise behaved as described. but our chat was short: 60 logged messages, 21.7 kb, against a view that starts merging at 128 kb. we did not reach the regime the design is for. in this short chat, uniichat's turn calls cost 1.45 to 1.54 times (1.33 for sonnet at the specification's write price) the continued session's. the result that should carry to a long chat is the compaction work: the design needs about one merge per message, and haiku at xhigh spent thousands of thinking tokens on each line. this post states where our harness departs from the design and asks what we should measure next.
> </div>

Replace the short-chat-only opening with the source claim, observed bounded-view cost crossover and still-untested memory advantage. The short-chat measurements remain historical; xhigh compaction cost is not an unavoidable property of the design. The blanket statement that exercised parts behaved as described is too broad given the already observed request obedience and the new shared-prompt/tool failures.

## 2. Title

> title: "uniichat through claude code: a short-chat result and the compaction bill"

Replace with a lower-case title covering both rounds.

## 3. Subtitle

> subtitle: "victor taelin's one-chat-that-never-ends, rebuilt as closely as the cli allows and run on haiku, sonnet and opus. one short chat, 1,343 requests, and four questions for the author."

The programme now includes a longer replay, effort sweep and overhead probes. Retain the old call count only as round-1 scope, not the combined programme size.

## 4. Broad recomputation assurance

> unless a paragraph says otherwise, figures below were recomputed from raw rows or the request ledger. the fidelity counts, order survival, correction survival, answer grades and prefix-only cache percentages are the harness's reported results and were not independently recomputed.

Retract the unqualified assurance for E1 retry-arm USD. The cumulative-per-process cost was summed repeatedly. Round-1 E1 retry-arm USD remains unrepaired; E3 usage units remain valid. E5 outcome grades and E4 rule/correction regex results remain reported, not independently regraded.

## 5. Cache lifetime as a route constraint

> the specification notes that claude code subscriptions use their own 1-hour cache lifetime, so the specification is aware of this route. it is still not the api request drawn in the specification, and that difference matters here.

The saved spec does describe the subscription default, but this cannot justify treating that default as forced. E6 measured five-minute writes with the setting; the trial itself hard-coded one hour on the view.

## 6. Claim that cache marks cannot be changed

> **the write price.** every token written across the three experiments was reported as a 1-hour write, 3,356,351 tokens, with none at 5 minutes. the specification prices that write at 2×. claude code's own marks are 1-hour and we could not change them. our view mark also requested 1 hour. we did not test whether a 5-minute mark there would be honoured. this was the smallest effect: at a 1.25× write price, the sonnet turn ratio falls from 1.45× to 1.33×.

Retract "we could not change them." E6 changed the marks and measured five-minute writes. The quoted round-1 token total and its one-hour class remain historical observations. Keep the original 1.33 ratio as repricing only UniiChat against the old baseline; the paper pi wrapper subtraction plus repricing both short Sonnet arms gives 1.14.

## 7. Historical cache-lifetime limitation

> - **cache lifetime.** claude code's own marks were 1-hour entries. the view mark was ours, and we also set it to 1 hour. we did not test whether claude code would honour a 5-minute mark on the view.

True for round 1, now superseded by E6. It must not appear as a current untested control or fixed limitation of Claude Code.

## 8. Wrapper estimates

> - **claude code wraps the request.** by our estimate from rewritten tokens, about 240 tokens sat before the view and 356 after it; we did not read the request off the wire. the tail fits the specification, which puts per-turn state after the view. the block before the view does not, and no flag removed it.

Replace rough 240/356-token estimates with E6 measured-by-difference 170/357, n=1 each. Distinguish the request-shape capture from live pi behaviour. The unchanged round-1 claim that no tested flag removed those blocks is not converted into a claim about all possible flags.

## 9. Round-1 compactor effort as the only cost setting

> - **effort.** compactions used `--effort xhigh`; turn calls and the baseline used the cli default. we did not verify that xhigh on haiku through the cli assigns the same thinking budget as the api setting in the specification.

Keep xhigh as the historical setting and retain unverified API/CLI effort equivalence. Add measured low/medium/high sweep. E4 low and xhigh both score 38/40 once; low costs 4.9 times less per built line. This does not establish equal reliability.

## 10. Earlier whole-arm penalties

> | whole arm including compactions, usd, cli estimate | uniichat | continued session | ratio |
> |---|---:|---:|---:|
> | sonnet | 0.640 | 0.128 | 5.0× |
> | haiku | 0.468 | 0.0081 | 58× |

Keep 5.0/58 as historical short-chat xhigh reports in summary.json, explicitly scoped. Withdraw their use as a general or long-run compaction penalty. They are not replaced by invented repaired round-1 totals. E5 low-effort compaction is about 23% of the arm USD; units and CLI USD give different total-cost answers.

## 11. Write-price comparison scope

> the turn-call unit below is one uncached input token of the turn model. the relative api list-price weights are input + 2 × cache write + 0.1 × cache read + 5 × output. this is a notional cost on a subscription. at the specification's 1.25× write price, the sonnet ratio is 1.33× rather than 1.45×.

The one-sided 1.33 Sonnet repricing is not the two-arm five-minute result. E6 paper pi wrapper subtraction plus repricing both short Sonnet arms gives 1.14. Also label units as accounting weights and CLI USD as estimates, not paid subscription charges; E5 CLI Sonnet cache reads weigh 0.05 instead of the unit 0.1.

## 12. Earlier general conclusion

> this is not evidence that the specification is wrong. it shows that a 21.7 kb chat is too short to test the regime uniichat is designed for. in that start-up phase, its turn calls cost 1.45 to 1.54 times (1.33 for sonnet at the specification's write price) a cached continued session. separately, the specified compactor was expensive per line, and that work continues with chat length. the departures listed above apply to every figure here.

Retain the short-script observations but withdraw the extension of xhigh cost to any long chat. The new script reaches real batches and cumulative crossover; it is not a rerun of the short workload, so it neither repairs nor retroactively falsifies that measurement.

## 13. No measured break-even and old predictions

> - **there is no measured break-even.** no measured point extends beyond 42 user messages. a model prediction for this script puts a cheaper uniichat turn near the first batch, around message 185 to 215. with compactions it predicts around message 400 or later for sonnet turns, earlier for opus, and never for haiku turns. cumulative break-even would be later still.

Supersede as guidance. The observed long-script one-hour unit turn-call crossover is 57, total with Haiku weight 0.05 is 82; five-minute repricing is 32/71. CLI USD turn calls cross at 80, total has not crossed by 112. Predictions for the old short script remain archived as predictions, not revised measurements.

## 14. Real-limit regime untested

> - **the steady state was not tested.** after 26 messages the view was 15.8 to 16.2 kb, and it reached 17.7 kb only after six extra opus questions. the 64 to 128 kb sawtooth was not tested with real lines. one batch fired at limits scaled to 16/8 kb.

Superseded for the combined account: E5 records three real-limit batches at 52/77/103. Do not call a short run indefinite steady-state proof; later turns, rare failures and baseline degradation remain untested.

## 15. Additional untested claims in the partial-results paragraph

> some parts were only partial. haiku began only 79 of 112 lines with a bare kind tag; the other 33 decorated it, for example "user (msg 28):". sonnet wrote answers to two arithmetic baits into 8 nodes. at the specification's limits, sonnet and opus never needed to zoom because the view was nearly verbatim. we did not test the 64 to 128 kb sawtooth, the steady 16 to 32 kb compaction view, about 11 lines per level, or the simulated 21-versus-80 batching figure.

The round-1 format observations remain valid within their scope. Real-limit view batches and the compaction view are now exercised in E5. The simulated batching comparison and indefinite behaviour remain untested. Tool-free compaction and obedient turn classification cannot be generalized from xhigh to low effort.

## 16. Only scaled batching

> - **scaled batch.** the only batch used 16,000/8,000-byte view limits and 8,000/4,000-byte compaction-view limits. this produced about 16 to 30 lines per view, not the hundreds expected at the real limits.

Historical round-1 limitation retained in metadata; no longer a limitation of the entire study because E5 reached the real limits.

## 17. Background scheduling

> - **background work.** our harness started leaf compactions only after a turn ended, ran all merges to idle, and then sent the next message at once. the specification runs compaction during the turn and while the user reads and types, so every wait reported below is a harness upper bound. three experiments also shared one account, which makes wall times loose.

Historical wait statistics remain upper bounds for the round-1 feeder. E5 uses background compaction at the new commit and estimates immediate-next-message waits separately from actual lockstep waits.

## 18. Known core deviations and confidence about their effect

> - **known core deviations.** the wait-for-writer gate used the compaction view's epoch rather than the exact prefix. the process did one linear refill at startup, compactions received tools with an empty allow list, and each turn had a six-request cap, though no turn reached it. the trial listed eight bugs; several had regression tests at the pinned commit, but the reported fix for one was not re-verified. two design-relevant issues remained: unbuilt leaves were sized at the placeholder length, so a batch could end above 64,000 bytes, and the gate used the wrong key. we believe none changes a number here, but no independent check established that.

Withdraw an untested belief that the deviations cannot affect figures. Round 2 adds background processing and Chat.settle; placeholder-size accounting remains imperfect. Request allowances and retry handling differ in E5. An empty allow list did not prevent read-only shell execution, so tool visibility and tool execution need separate reporting.

## 19. Old sole implementation pin

> - **unpublished branch.** the core under test is commit `fd454e7767bbd907984cd7546c7f62da18ff35bf` on branch `trial/optchat-uniichat`. the branch had not been pushed when this study was frozen, so the author cannot yet inspect that commit.

Keep the immutable round-1 SHA and add the full round-2 098433d SHA. Both local-only status and E4 use of the old revision remain recorded; E6 exact per-call checkout is unresolved rather than invented.

## 20. Tool-heavy cache failure as inference only

> - **the 20-block lookback has a long-turn consequence.** the specification gives the 20-block lookback but does not say what happens past it. more than 21 blocks, or 84 lines, added between calls rewrote the whole view. a turn with about 42 tool calls would do that, inferred from two logged lines per call rather than measured. the api could place another mark every 20 blocks; claude code used all four marks, so we could not add one.

Update from inference to an observed consequence in two tool-heavy turns, adding 95/90 lines. The second coincides with a batch, so causal isolation remains limited. Do not replace the spec lookback with an unsupported universal tool-count threshold.

## 21. Round-1 accuracy as a general result

> the arms were equally accurate by the harness's regex grading, which we did not re-grade by hand: 61 of 61 across all six uniichat chats and 42 of 42 in the continued sessions.

The 61/61 and 42/42 short-chat harness scores remain historical facts. The combined claim must also disclose E5 50/54 versus 54/54, five skipped edits and outcome-grading limits. Neither round observed baseline auto-compaction or context rot.

## 22. Standing-order loss versus behaviour

> standing orders fade. at the leaf, 17 of 20 order messages for haiku and 14 of 16 for sonnet kept every key term. by the third merge, 9 of 20 and 9 of 16 did. these are harness counts, not independent recomputations. "do not redeploy" was missing from the first line written in both models, and "revert" was gone by the third merge in both. the nearest statement in the specification is about corrections, not orders: "a correction given in chat survives up the tree, so most of an `AGENTS.md` becomes unneeded." we did not test whether an agent still obeys an order that has left the view.

Keep the old substring/key-term counts as historical reports. Correct any implication that losing a key term establishes behavioural noncompliance: E5 passes all gradable standing-order checks, but skipped tasks are ungradable. Whether rules absent from every view line govern later work remains open.

## 23. Only Sonnet answers embedded requests

> sonnet also wrote answers to two arithmetic bait questions into 8 nodes, and those answers reached the third level. haiku and opus did not.

True for the reported round-1 scope. Expanded E4 evidence shows every candidate answering some planted requests; E5 compactions attempt repository work. Do not generalize old Haiku observations to new settings.

## 24. Stock-overhead scope

> - **the baseline was thinned.** its first request was 3,851 to 4,627 tokens with three tools. the default tool set measured 28,793 tokens in a separate haiku call with the specification's prompt appended and user configuration off. a larger baseline would cost more per call, but its prefix would also be cached.

Keep the old 28,793-token probe as a different measurement. Add 23,690 for stock tools/skills without user settings and 27,295 for normal configuration, each n=1. Neither is a correction to the old differently shaped request. Round 1 already thinned the baseline.

## 25. Round two in progress and a promised pi arm

> round two is in progress and is not part of this frozen study: a 250-turn tool-heavy replay at the real limits against a continued session that is allowed to auto-compact, a cheaper-compactor sweep, and a pi arm where we control the request. we will update this post with those results.

Replace the future promise with completed/partial outcomes: 112 of 260 scripted turns, budget stop; no baseline auto-compaction; compactor sweep complete for Haiku and partial for Sonnet; pi analysed on paper with zero live calls. The 250-turn brief label differs from the actual script length.

## 26. Old questions

> 1. **what does a compaction cost you?** in e3, leaf sends had a 6,165-token median and merges a 13,037-token median; the 49 sends averaged 17,027 output tokens, and merges were 81% of them. is that what you see with haiku at xhigh? would lower effort with more retries work, given our 96% first-try fit at xhigh against 59% at default?
> 2. **how do you run it?** do you use api billing or a subscription, which haiku version, and which model for turns? the specification says the cache misses after a model switch, but also says a haiku compaction reads the turn's cache entry. are your turns on haiku too, and what share of your calls or spend is compaction?
> 3. **when is the design meant to pay against a plain cached session?** the specification opens with "a session fills up, gets compacted or dropped," but makes no cost claim against a continued session before that happens. what fraction of your messages exceed 512 bytes, about how many messages reach the first 128 kb batch, and are eager merges deliberate even though they are built long before a view reads them?
> 4. **how do you handle the two open memory cases?** a turn that adds more than 84 lines defeats the 20-block lookback in claude code; do you place extra marks on the api? the specification says "a correction given in chat survives up the tree." our corrections did survive: 21 of 21 in e3, and 2 of 3 in the dense e1 corpus. standing orders did worse there: "do not redeploy" was already absent from the first line written, and 11 of 20 order messages had lost a key term by the third merge. have you seen a standing order drop out, and does the agent still obey it?

Replace the four bundled round-1 questions with six short round-2 questions derived from the final report. Remove questions already answered by the sweep/settings measurement; do not presuppose savings versus a short continued session. Keep questions about baseline, effort, prices, cache denominator, tools, prompt confusion and deep instruction behaviour.

## Retained limits and distinctions

The snapshot's statements that the specification does not promise savings versus a short continued session, the baseline never hit its failure mode, the arms use different prompts/tools, the source branch is local, the corpus is synthetic, and principal arms lack repeats are retained. Rephrasing or removing an old table for space is not a retraction of its valid historical measurement. No new result establishes indefinite memory, normal-user reliability, a live pi saving, or paid subscription prices.

The source report's E5 0.0627 “price ratio”, original checkpoint totals and tool-call refusals were also corrected before publication. They are round-2 corrections, not quotes falsely attributed to the round-1 snapshot. The final audit's corrected send denominator is used for E4 tool calls. Its unresolved maximum-tries and E6 compaction-unit discrepancy are omitted from the post.

## Tool-result wording checked against raw events

The final report’s event counts are retained, but its “denied” labels are too broad. In E5 compaction events, 159 shell results have no error, while six are unsuccessful. One of those six is a runtime command error rather than an explicit permission refusal. The single edit returns string-not-found, so no edit was applied, but it is not a permission denial. The post uses “non-error results”, “without a usable result” and “without an applied change”. This preserves the authoritative counts while avoiding an unsupported claim about the permission system.
