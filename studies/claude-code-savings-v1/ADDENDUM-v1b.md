# Addendum v1b — does gating the State Packet by the prompt fix its coding-task overhead?

**Result: no, not by the pre-registered standard. Both hypotheses failed.**

v1 found that the SessionStart State Packet cuts tokens 35.5% over lean on current-work questions but adds 10.8% on fresh coding tasks. v1b tested a fix on kvnloo/z0intelligence `feat/packet-gating-v0` (`ebae4e3`), called `packet: "gated"`:

- Nothing is injected at SessionStart.
- At UserPromptSubmit, the plugin injects only the facts of the families named by DecisionOpportunity question scoping (`required_families`, vocabulary unchanged), at most once per session.

The pre-registration is `02eff0c`, pushed before any run. The results are `04b9186`, imported unchanged into `data/v1b/`.

Design:
- 372 `claude -p` trials with Sonnet on Claude Code 2.1.286.
- Arms: lean, lean+packet (SessionStart, v1) and lean+packet-gated.
- The frozen v1 suites: 11 qa questions × 4 reps and 20 repo tasks × 4 reps.
- At most 4 concurrent processes; 0 infrastructure failures.
- The gate fired exactly as predicted from the prompts alone: 44/44 qa trials and 20/80 repo trials (5 tasks where coding prompts happened to contain words like "priority" or "session").

| | session → gated | 95% CI | median | cheaper | p | cost | success | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H1 qa (non-inferiority, CI < +5%) | +16.6% | −4.8 … +45.6 | −4.7% | 28/44 | 0.72 | +10.6% | 44 → 44 | FAIL |
| H2 repo (superiority, CI < 0) | −7.3% | −13.8 … +0.8 | −5.6% | 67/80 | 1.4e-5 | −7.0% | 80 → 80 | FAIL (narrowly) |

Same-night comparisons against plain lean:

- **qa:** the session packet came in at −29.5% (replicating v1's −35.5%). Gated came in at −17.8%, with a median of −21.8% and p = 0.002.
- **repo:** the session packet came in at +4.7% pooled (median +6.9%; short tasks +9.7%, CI +4.9 … +14.9), confirming that its overhead is real. Gated was flat (median +0.1%), but equivalence within ±5% was not shown (CI −13.6 … +6.7).

What this means:

1. **On coding tasks, gating removes most of the packet's overhead.** The pre-registered test still fails on the CI.
2. **On current-work questions, gating gives back roughly half of the packet's saving.** The loss concentrates in two questions:
   - session-file recall
   - CI abstention

   Exploratory reading: the scoped text was truncated at its 800-token cap when conversation facts were in scope, and it drops the full packet's abstention rule.
3. **The live default should not change on this evidence.** A revised gate would need its own pre-registration.

Also fixed on the same branch (exploratory, no savings claim): `z0int claude-code launch --profile lean` now passes an `--mcp-config` containing only the z0 server. `route_worker` was listed and callable in 3/3 lean probe sessions. It returned PARENT_ONLY each time, with a receipt.
