---
title: "uniichat through claude code: a short-chat result and the compaction bill"
subtitle: "victor taelin's one-chat-that-never-ends, rebuilt as closely as the cli allows and run on haiku, sonnet and opus. one short chat, 1,343 requests, and four questions for the author."
study: optchat-claude-code-v0
status: evidence-local
author: "zer0 research"
date: "october 11, 2026"
mock_data: false
toc:
  - id: what-we-built
    label: what we built
  - id: holds
    label: what we could exercise
  - id: departures
    label: where our harness departs from the design
  - id: cost
    label: what the short chat cost
  - id: why
    label: where the cost came from
  - id: cache
    label: cache behaviour we measured
  - id: fidelity
    label: what the lines keep
  - id: limits
    label: what this does not prove
  - id: questions
    label: questions for the author
---

<div class="lede">
the specification says a chat can run forever at a constant context size, with nearly every token read from the prompt cache. we rebuilt it as closely as the claude code cli allows and ran it beside an ordinary continued session. the specification makes no cost claim against such a session; that comparison is ours. the parts we could exercise behaved as described. but our chat was short: 60 logged messages, 21.7 kb, against a view that starts merging at 128 kb. we did not reach the regime the design is for. in this short chat, uniichat's turn calls cost 1.45 to 1.54 times (1.33 for sonnet at the specification's write price) the continued session's. the result that should carry to a long chat is the compaction work: the design needs about one merge per message, and haiku at xhigh spent thousands of thinking tokens on each line. this post states where our harness departs from the design and asks what we should measure next.
</div>

<div class="hero-rule"></div>

## what we built {#what-we-built}

the spec is victor taelin's uniichat specification (an unlisted gist; revision 3c190e06 of october 8, 2026), fetched october 11. an [earlier post](optchat-long-horizon-v0.html) used the former name optchat and code written against an older revision. that code measured a pair's age from its first message instead of its last, merged at every message, rebuilt the view on load and scanned the tree for work. those are four of the specification's thirteen listed mistakes. it also gave compactions their own system prompt, which is half of a fifth. we discarded that implementation and started again.

the new core is about 1,700 lines of python with no dependencies, including the claude code backend. it has the append-only log, the tree of 512-byte nodes, the saved view with the last-message due order and the 128 kb to 64 kb batch, and the 16 to 32 kb compaction view. it uses the task texts, ruler and retry text byte for byte. it uses the system prompt verbatim, less the paragraph on computers, which the specification says to drop without device tools. it supplies `zoom` and `date` as tools.

before the three experiments ran, a second ai agent that had not written the code checked the build against the specification under our direction:

- the merge order equals taelin's `push` at all 20,001 steps for t = 0 to 20,000. the wrong formula that measures from the first message matches `push` at only 481 of 20,001 steps, as the specification says.
- the t=10 counterexample behaves as described: our implementation merges 8-9, while the wrong formula merges 0-7.
- the prompt, task texts, retry text and ruler compare equal to the saved specification text, subject to the allowed omission above.
- `view.json` survived eight kills during an append and was not rebuilt. we did not re-run this check independently.

not built: handing a message to a running call, pages for long messages, images, subagents and `zoom("Name")`, or per-turn device state. the prompt still tells the model about these features.

the model calls went through claude code 2.1.296 on a subscription with user settings, user plugins, memory files and the user's mcp servers switched off. the only mcp server was ours, serving `zoom` and `date`. claude code's two built-in plugins still loaded. compactions ran at `--effort xhigh` on `claude-haiku-5-5`. turns and the baseline ran at claude code's default effort on `claude-haiku-5-5`, `claude-sonnet-5-5` and `claude-opus-5-5`. we did not confirm that the cli's xhigh setting matches the api setting.

the specification notes that claude code subscriptions use their own 1-hour cache lifetime, so the specification is aware of this route. it is still not the api request drawn in the specification, and that difference matters here.

e1 asked whether models can write the required lines on an 80-message synthetic corpus. e2 measured cache behaviour with synthetic views. e3 ran a 26-message chat in both arms on sonnet and on haiku, six late questions on opus, one 42-message uniichat chat at scaled-down limits and two short probes: six uniichat chats in all. the three experiments reserved 1,249 api requests: 988 haiku, 205 sonnet and 56 opus. another 94 haiku requests went on probes and smoke tests, 1,343 in all. five of those were killed in flight and left no row.

unless a paragraph says otherwise, figures below were recomputed from raw rows or the request ledger. the fidelity counts, order survival, correction survival, answer grades and prefix-only cache percentages are the harness's reported results and were not independently recomputed.

## what we could exercise {#holds}

| source | what the specification says | what we measured |
|---|---|---|
| e1, synthetic | a model can hit 512 bytes with the ruler, the cut and retries | every built line fit. first try at xhigh: haiku 108 of 112, opus 19 of 22, sonnet 68 of 87. no session needed a fifth try. |
| e1, matched leaves | the ruler shows the length | with the ruler, haiku xhigh fit 37 of 37 on the first try; without it, 34 of 37, p = 0.24. the measured difference was not significant. effort mattered more: 76 of 79 at xhigh against 47 of 79 at default, p < 0.01. |
| e2, synthetic | each turn reads the last view and writes only new lines | with a 64 kb view and 4 new lines, a turn wrote 1,006 haiku, 1,214 sonnet or 1,125 opus tokens and read about 28,000. over 24 haiku calls at 80 to 133 kb, 96.4% of the whole input was read. |
| e2, synthetic | entries exist only at marks, with a 20-block lookback | 20 and 21 added blocks found the prior mark. 22, 23 and 24 did not, and the whole view was rewritten, one haiku call at each block count. |
| e2, synthetic | calls on a prefix being written wait for the first response | without the gate, 8 of 8 concurrent haiku calls paid for the prefix in one wave and 2 of 8 in the other; sonnet was 2 of 4 and opus 2 of 2. with the gate, exactly 1 paid in all four waves. |
| e1 and e3 | compactions call no tools and output only the line | true at xhigh across 504 sends, 288 in e1 and 216 in e3: no heads, preambles or tool calls. at default effort haiku called `zoom` in 5 of 271 sends. no head or multiline reply appeared in all 775 compaction sends. |
| e3, one scaled batch | nothing is lost because `zoom` recovers it | 61 of 61 recall answers were correct across all six uniichat chats by the harness's regex grading, at most 64 messages deep. 13 detail questions came after the one batch, and the model zoomed on 10 of those turns. the batch used limits scaled to 16/8 kb, with an 8/4 kb compaction view. |
| e3 | the view's latest word is the truth | 26 of 26 questions about a later correction got the corrected value. the harness supplied these grades. |
| e3 | say in the reply what was learned | all 13 turns that zoomed restated the facts. |

some parts were only partial. haiku began only 79 of 112 lines with a bare kind tag; the other 33 decorated it, for example "user (msg 28):". sonnet wrote answers to two arithmetic baits into 8 nodes. at the specification's limits, sonnet and opus never needed to zoom because the view was nearly verbatim. we did not test the 64 to 128 kb sawtooth, the steady 16 to 32 kb compaction view, about 11 lines per level, or the simulated 21-versus-80 batching figure.

the view placement used 4-line blocks with a mark on the last whole block, as the specification gives them. we put the view at the start of the user message, which is our reading; the specification does not name the role. the same view as one user block was rewritten whole on the next message: 26,784 tokens written and only the 1,641 tools-and-system tokens read. in the system prompt, the view survived a new message but was rewritten whole as soon as it grew by 4 lines. these were one haiku sample each.

## where our harness departs from the design {#departures}

- **message shape.** the e3 script was short question-and-answer: 60 logged messages, 21.7 kb in all, with user messages averaging 270 bytes and 4 tool calls. 48 of 60 messages were 512 bytes or less and entered the view word for word, so there was little to compress.
- **eager merges.** the specification builds a merge as soon as both halves exist, and so did we. in the sonnet chat, 36 of 49 compaction sends were merges and they used 675,919 of 834,302 output tokens, 81% of the total; in the haiku chat, 43 of 53 were merges and used 768,474 of 859,289. no call in either chat read those merged lines.
- **cache lifetime.** claude code's own marks were 1-hour entries. the view mark was ours, and we also set it to 1 hour. we did not test whether claude code would honour a 5-minute mark on the view.
- **baseline shape.** the comparison used one continued `claude -p --resume` session with claude code's default system prompt and three file tools. uniichat replaced that prompt with the specification's prompt and also had `zoom` and `date`, so the arms did not carry the same system prompt or tool list.
- **background work.** our harness started leaf compactions only after a turn ended, ran all merges to idle, and then sent the next message at once. the specification runs compaction during the turn and while the user reads and types, so every wait reported below is a harness upper bound. three experiments also shared one account, which makes wall times loose.
- **whole-turn logging.** our feeder logged a whole turn before compacting it. in e1 this made 40 of 50 haiku leaf calls and 30 of 38 sonnet leaf calls miss the immediately preceding message; a live background compactor would see fewer such gaps.
- **effort.** compactions used `--effort xhigh`; turn calls and the baseline used the cli default. we did not verify that xhigh on haiku through the cli assigns the same thinking budget as the api setting in the specification.
- **scaled batch.** the only batch used 16,000/8,000-byte view limits and 8,000/4,000-byte compaction-view limits. this produced about 16 to 30 lines per view, not the hundreds expected at the real limits.
- **fidelity corpus.** e1 was synthetic and deliberately dense: 80 messages, 174 planted exact items and 20 order messages, graded by substring and by whether every key term remained. every line was forced to the third merge, though a real 80-message view would still show leaves.
- **usd table.** the cli estimate priced haiku input at about $0.10 per million tokens, about one twentieth of sonnet per token. at a 1:3 ratio, compaction would weigh several times more.
- **known core deviations.** the wait-for-writer gate used the compaction view's epoch rather than the exact prefix. the process did one linear refill at startup, compactions received tools with an empty allow list, and each turn had a six-request cap, though no turn reached it. the trial listed eight bugs; several had regression tests at the pinned commit, but the reported fix for one was not re-verified. two design-relevant issues remained: unbuilt leaves were sized at the placeholder length, so a batch could end above 64,000 bytes, and the gate used the wrong key. we believe none changes a number here, but no independent check established that.
- **unpublished branch.** the core under test is commit `fd454e7767bbd907984cd7546c7f62da18ff35bf` on branch `trial/optchat-uniichat`. the branch had not been pushed when this study was frozen, so the author cannot yet inspect that commit.

## what the short chat cost {#cost}

the comparison is ours, not one the specification makes. e3 used one scripted chat of 26 user messages, run as a pair on sonnet and again on haiku: once as uniichat, with a fresh call per message, and once as one continued claude code session with its default system prompt. both received the same messages and the same three file tools; uniichat also had `zoom` and `date`. opus answered only the last 6 recall questions on a chat seeded from the sonnet run, in both arms, and needed no compaction.

the turn-call unit below is one uncached input token of the turn model. the relative api list-price weights are input + 2 × cache write + 0.1 × cache read + 5 × output. this is a notional cost on a subscription. at the specification's 1.25× write price, the sonnet ratio is 1.33× rather than 1.45×.

| turn calls only, weighted tokens | uniichat | continued session | ratio |
|---|---:|---:|---:|
| sonnet, 26 messages | 110,260 | 76,297 | 1.45× |
| haiku, 26 messages | 124,750 | 81,040 | 1.54× |
| opus, last 6 questions | 35,618 | 33,807 | 1.05× |

| whole arm including compactions, usd, cli estimate | uniichat | continued session | ratio |
|---|---:|---:|---:|
| sonnet | 0.640 | 0.128 | 5.0× |
| haiku | 0.468 | 0.0081 | 58× |

in this chat no merged line ever entered a view. uniichat was in its start-up phase, where its view remained close to the raw transcript.

the arms were equally accurate by the harness's regex grading, which we did not re-grade by hand: 61 of 61 across all six uniichat chats and 42 of 42 in the continued sessions.

the turn call itself had a 3.2 s median in both sonnet arms. the haiku medians were 2.8 s for uniichat and 2.1 s for the continued session. in each 26-message chat, 19 turns needed no leaf call. on the other 7, the median leaf waits were 23 s for the sonnet chat and 63 s for the haiku chat; their maxima were 212 s and 109 s. the scaled 42-message chat had 15 waits, a 43 s median and a 296 s maximum. these are harness upper bounds because compaction did not run in the background.

## where the cost came from {#why}

the uniichat prompt sent 13% fewer prompt tokens than the continued sonnet session, 226,864 against 261,156. four effects outweighed that reduction.

**the compactor.** the specification says, "a cheap one. uniichat uses claude haiku at xhigh effort." haiku was cheap per token. it used many tokens per line.

compaction work per message does not fall as the chat grows. each long message needs about one leaf, and the binary tree needs about one merge per message over time.

in e1, a line-writing experiment, one haiku xhigh send averaged 11,326 output tokens, 11,107 of them thinking. wall time averaged 45.5 s, with an 18.5 s median and a 267 s maximum, n=116.

in the e3 sonnet cost chat, 13 leaf sends had a median of 6,165 output tokens and a maximum of 37,570. its 36 merge sends had a median of 13,037 and a maximum of 70,943. leaf wall-time medians were 23.2 s in the sonnet chat and 19.4 s in the haiku chat; merge medians were 49.8 s and 47.6 s. all 49 sonnet-chat sends averaged 17,027 output tokens and used 834,302 in total; the merges were 81% of those tokens. a long chat eventually needs the same merges, about one per message.

effort made the line fit. on the same 79 nodes in e1, haiku fit 76 lines on its first try at xhigh and 47 at default, p < 0.01. by contrast, the ruler result was 37 of 37 against 34 of 37, p = 0.24.

**the write price.** every token written across the three experiments was reported as a 1-hour write, 3,356,351 tokens, with none at 5 minutes. the specification prices that write at 2×. claude code's own marks are 1-hour and we could not change them. our view mark also requested 1 hour. we did not test whether a 5-minute mark there would be honoured. this was the smallest effect: at a 1.25× write price, the sonnet turn ratio falls from 1.45× to 1.33×.

**a continued session is already cheap here.** over the same 26 messages, the baseline read 95.1% of its sonnet prompt and 95.5% of its haiku prompt from cache. uniichat read 87.2% and 90.0%. after the first turn, uniichat wrote about 990 tokens per turn against 360 for the continued sonnet session.

**there was little to compress.** at message 26, the uniichat prompt was 10,602 tokens and the continued session's was 12,315. most messages were under 512 bytes and stayed word for word. about 12 of 60 needed a written line, and no merged line had entered the view. after 26 messages the view was 15.8 to 16.2 kb, or 17.7 kb after the six extra opus questions, an eighth of the 128 kb at which the first batch fires.

## cache behaviour we measured {#cache}

- **a batch costs the whole view, which agrees with the specification.** the specification says a batch rewrites the view once and that the cache misses after a batch. it also says a merge changes the view "from the merged line on", which reads as if earlier lines stay cached. with entries only at marks and the specification's mark at the view's end, they did not. a one-line change wrote 26,949 to 27,193 tokens and read 1,641: four positions on haiku, and the middle on sonnet and opus, one call each. after earlier calls had left a mark before the change, only 2,401 were written. on the real cache, merging at every message would therefore rewrite the whole view each time, which strengthens the case for batching.
- **the 20-block lookback has a long-turn consequence.** the specification gives the 20-block lookback but does not say what happens past it. more than 21 blocks, or 84 lines, added between calls rewrote the whole view. a turn with about 42 tool calls would do that, inferred from two logged lines per call rather than measured. the api could place another mark every 20 blocks; claude code used all four marks, so we could not add one.
- **model switches miss.** the specification says the cache misses after a model switch, and our result confirms it. a view warm on haiku cost sonnet 27,111 tokens and opus 27,084 to write. the narrower consequence is that a compaction can read the turn's cache entry only when both use the same model, while the specified compactor is haiku.
- **the lifetime was between 30 and 93 minutes in these samples.** untouched entries were read in full at 6, about 15 and 30 minutes, and the view was gone at 93 minutes in two samples. there was one sample per gap and none between 30 and 93 minutes.
- **claude code wraps the request.** by our estimate from rewritten tokens, about 240 tokens sat before the view and 356 after it; we did not read the request off the wire. the tail fits the specification, which puts per-turn state after the view. the block before the view does not, and no flag removed it.

in e2, haiku read 96.4% of the whole input at 80 to 133 kb, n=24, and about 97.5% of the prefix by the harness's estimate. the specification's 98.6% and 96.2% are simulated and are shares of the prefix.

## what the lines keep {#fidelity}

e1 used a synthetic, deliberately dense corpus with about two planted exact items per message. read these counts as a stress test, not as the loss rate of a normal chat. the harness looked for exact substrings, so paraphrases counted as losses. the counts were not independently recomputed.

| model and message set | at the leaf | after three forced merges, 8 messages per line |
|---|---:|---:|
| haiku xhigh, 80 messages | 119 of 174 | 40 of 174 |
| sonnet xhigh, 64 messages | 105 of 135 | 41 of 135 |
| opus xhigh, first 16 messages | 39 of 40 | 16 of 40 |

the rows cover different message sets. on the common first 16 messages, haiku went from 36 to 8 of 40, sonnet from 36 to 14, and opus from 39 to 16. the third merge was forced in e1; no merged line was shown in the cost chat.

standing orders fade. at the leaf, 17 of 20 order messages for haiku and 14 of 16 for sonnet kept every key term. by the third merge, 9 of 20 and 9 of 16 did. these are harness counts, not independent recomputations. "do not redeploy" was missing from the first line written in both models, and "revert" was gone by the third merge in both. the nearest statement in the specification is about corrections, not orders: "a correction given in chat survives up the tree, so most of an `AGENTS.md` becomes unneeded." we did not test whether an agent still obeys an order that has left the view.

corrections did better. in e3, 21 of 21 corrected values remained in the highest node across three chats, 7 facts in each chat, as reported by the harness. in e1, haiku lost one of three corrected values, "900 ms", at the third merge.

sonnet also wrote answers to two arithmetic bait questions into 8 nodes, and those answers reached the third level. haiku and opus did not.

the missing-predecessor figure belongs to our feeder, not to the design in general. because the feeder logged a whole turn before starting up to eight compactions, 40 of 50 haiku leaves and 30 of 38 sonnet leaves lacked the immediately preceding message. the mean gaps were 3.02 and 3.13 messages and the maximum was 11. a live background compactor would see fewer gaps.

## what this does not prove {#limits}

this is not evidence that the specification is wrong. it shows that a 21.7 kb chat is too short to test the regime uniichat is designed for. in that start-up phase, its turn calls cost 1.45 to 1.54 times (1.33 for sonnet at the specification's write price) a cached continued session. separately, the specified compactor was expensive per line, and that work continues with chat length. the departures listed above apply to every figure here.

- **the steady state was not tested.** after 26 messages the view was 15.8 to 16.2 kb, and it reached 17.7 kb only after six extra opus questions. the 64 to 128 kb sawtooth was not tested with real lines. one batch fired at limits scaled to 16/8 kb.
- **there is no measured break-even.** no measured point extends beyond 42 user messages. a model prediction for this script puts a cheaper uniichat turn near the first batch, around message 185 to 215. with compactions it predicts around message 400 or later for sonnet turns, earlier for opus, and never for haiku turns. cumulative break-even would be later still.
- **the baseline never got into trouble.** its prompt was 12,315 tokens at message 26 and peaked at 15,987 at message 42. it did not rot or auto-compact, so the failure uniichat addresses did not occur.
- **the baseline was thinned.** its first request was 3,851 to 4,627 tokens with three tools. the default tool set measured 28,793 tokens in a separate haiku call with the specification's prompt appended and user configuration off. a larger baseline would cost more per call, but its prefix would also be cached.
- **one run per arm.** there is no variance estimate.

round two is in progress and is not part of this frozen study: a 250-turn tool-heavy replay at the real limits against a continued session that is allowed to auto-compact, a cheaper-compactor sweep, and a pi arm where we control the request. we will update this post with those results.

## questions for the author {#questions}

1. **what does a compaction cost you?** in e3, leaf sends had a 6,165-token median and merges a 13,037-token median; the 49 sends averaged 17,027 output tokens, and merges were 81% of them. is that what you see with haiku at xhigh? would lower effort with more retries work, given our 96% first-try fit at xhigh against 59% at default?
2. **how do you run it?** do you use api billing or a subscription, which haiku version, and which model for turns? the specification says the cache misses after a model switch, but also says a haiku compaction reads the turn's cache entry. are your turns on haiku too, and what share of your calls or spend is compaction?
3. **when is the design meant to pay against a plain cached session?** the specification opens with "a session fills up, gets compacted or dropped," but makes no cost claim against a continued session before that happens. what fraction of your messages exceed 512 bytes, about how many messages reach the first 128 kb batch, and are eager merges deliberate even though they are built long before a view reads them?
4. **how do you handle the two open memory cases?** a turn that adds more than 84 lines defeats the 20-block lookback in claude code; do you place extra marks on the api? the specification says "a correction given in chat survives up the tree." our corrections did survive: 21 of 21 in e3, and 2 of 3 in the dense e1 corpus. standing orders did worse there: "do not redeploy" was already absent from the first line written, and 11 of 20 order messages had lost a key term by the third merge. have you seen a standing order drop out, and does the agent still obey it?

the frozen numbers, the call totals and the list of what was and was not recomputed are in `studies/optchat-claude-code-v0/`. raw call rows are not published.
