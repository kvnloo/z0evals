# Frozen MBP thermal correction: cross-client handoff protocol

Tracking: https://github.com/kvnloo/z0evals/issues/56
Canonical continuity contract: https://github.com/kvnloo/z0intelligence/issues/22
Verified OPT1 roadmap: https://github.com/kvnloo/z0intelligence/issues/195#issuecomment-6356363333

**FROZEN VARIANT, NOT A COMPLETED EVALUATION.** D1 is agent-codified policy and D2 is a real user correction. The pure-user-to-user variant remains **BLOCKED**; a bounded search did not identify an earlier USER D1 authorizing 95 C or 400%. This is not proof of absence. The parent unified-memory-v0 study remains draft and unscored.

## Private source boundary

The public `fleet-mbp-thermal.case.json` freezes only sanitized meaning, source identities/digests, scope and safe gold.

- D1: `kvnloo/.files` commit `79b6c8494fb2709e8231ff87246e9debb9e4e558`, `config/fleet/nodes.yaml`, Git blob `dc9359dd87d0879d7b08a34c914135880ad8747e`. `mbp` inherited `defaults.health.max_temp_c: 95`; both D1 default and node CPU quotas were **600%**, not 400%.
- D2: native OMP session `01a16527-824c-7714-8205-9a2d0d5eff38`, message `95d71187`, `2026-10-23T02:59:41.618Z`, attributed to user (steering=true). Preserved private original native JSON: **539 bytes**, SHA-256 `56a0afb51f98f929fcc0d4643f775efaa167771d12d0ad2e9f3423af6e0e8c32`. **Do not publish the original row, transcript/body or local source file paths.** This metadata is not an executed source verification.
- Sanitized D2 meaning: old MBP cooling/paste; temporarily disregard the software temperature cutoff and defer to processor downclocking; possible later thermal paste replacement. Draft PR [kvnloo/.files#41](https://github.com/kvnloo/.files/pull/41), commit `4ca98802004b18f93693db722bb1892da1ae7817`, blob `7e1f2bd539c084518993dba03113ec822a23f2e0`, codifies `nodes.mbp.health.max_temp_c: 110`. **110 was chosen by the implementation, not said verbatim by the user.**
- The thermal correction does **not** supersede D1's 600% CPU quota. The D2 implementation snapshot separately contains a 400% quota change; do not attribute that independent change to the user's thermal steering. Preserve independent CPU, memory, disk and battery admission rules.

Scope is only `kvnloo/.files:fleet/host-intent:mbp`. Nothing authorizes global propagation, phone/sibling changes, job dispatch, bypass of other gates, a hardware-safety assertion or a live-host activation claim. Memory is evidence, never permission.

## Fresh client and control

Start a *new supported client* in the authorized workstream. Its **only** initial inputs are:

1. Workstream identity: `kvnloo/.files:fleet/host-intent:mbp`
2. Neutral question: “What thermal admission policy currently applies to this workstream's node, what superseded it and why, and what is the next permitted read-only step?”

Do not provide the source IDs, gold, 95/110 values, D1/D2 labels, recap or answer to the new client. A separate authorized executor retains the frozen source bindings and oracle. Compare memory-enabled versus memory-disabled arms under the same *actual* model revision, neutral question, prompt template, budget, decoding parameters, tool policy and source-coverage snapshot. Both arms are read-only. Record differences and do not compare unmatched arms.

## Required six separate receipts in each arm

Each receipt needs a real identity, timestamp, provenance, observed data and read-only/private evidence path recorded *outside the public case*. `fleet-mbp-thermal.receipts.json` contains **NOT_RUN slots**, not executions:

1. **capture** — admit a user-attributed steering event with exact native ID, content digest and workstream scope; confirm repeat identity/payload is idempotent, and changed-payload same-ID conflicts.
2. **retrieve** — report exact authorized workstream, filtered scope, evidence IDs/revisions, source reads, cached/stale status and latency. Filter before any metadata or payload is exposed.
3. **exact_source_verify** — locally recover native D2, verify its 539 bytes and SHA-256, inspect both pinned `.files` revisions; check bytes rather than mtime+size. Missing/outage/digest mismatch of any required source means **OBSERVE**.
4. **actual_model_input** — capture a private, exact model-input snapshot and digest at the real inference boundary. Enabled arm must include exact-source-verified D2 with provenance; disabled-memory control must not receive memory-derived D2. Retrieval hits and hook completions are insufficient.
5. **use** — capture the actual model answer and citations. Judge the scoped 110 C draft codification, superseded 95 C agent policy, genuine user reason, nonverbatim number, unchanged *thermal-supersession scope* for other gates, and next **read-only exact-source verification**. No job actions.
6. **independent_check** — separately re-read authorized native source and pinned Git revisions; assess support, source recoverability, supersession, false authority, scope leaks, and false safety/host-activation claims.

Only after **real** receipts exist should a harness emit a measured result against the existing `receipt.schema.json` (`z0eval.unified_memory_receipt.v0`). Do not create another evaluator, memory store, capability registry or identity transport. A schema-valid row is not by itself independently verified use.

## Negative controls (all NOT_RUN)

The case file specifies eight controls: sibling and unknown scope must disclose **zero metadata bytes and zero payload bytes**; same-metadata new bytes, missing original D2, and required source outage lead to **OBSERVE**; older quoted approvals grant **no** execution authority; duplicate/restart retains D2 without duplicate admission/injection; and other nodes receive no mbp exception. Inspect stale cache/source revisions before ranking, not after answer generation.

## Commands for OMP on MBP (not run by this worker)

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s studies/unified-memory-v0 -p 'test_fleet_mbp_thermal.py' -v
python3 scripts/validate.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/validate_optchat_publication.py
```

Inspect pinned `.files` revisions *read-only* using `git -C "$FILES_REPO" show 79b6c8494fb2709e8231ff87246e9debb9e4e558:config/fleet/nodes.yaml` and `git -C "$FILES_REPO" show 4ca98802004b18f93693db722bb1892da1ae7817:config/fleet/nodes.yaml`. From a separately authorized private source, extract only the original OMP native JSON row to a **private local** destination and verify `wc -c "$PRIVATE_D2_ROW"` returns 539 and `sha256sum "$PRIVATE_D2_ROW"` matches the pinned SHA-256. Never print/upload the original or its local path. Obtain actual model-input and independent-check receipts before qualifying either arm.

## Present status

All six stages of both arms: **NOT_RUN**. Admission and actual model input: **NOT_QUALIFIED**. All eight negatives: **NOT_RUN**. No live handoff, activation, hardware-safety guarantee, executed model use, or superiority claim.
