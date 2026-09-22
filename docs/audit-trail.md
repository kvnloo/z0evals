# Audit trail

Chronological record of things that affected the repository's content lineage
where the history does **not** tell the whole story on its own. Nothing here is
rewritten after the fact; the commits are what they are and this file exists so
that a reader of `git log` is not misled.

---

## 2026-09-22 — one commit landed on `main` without passing through `preview`

**What happened.** Work on the Phase 1B article rewrite was committed directly to
`main` (`59b61a5`) instead of going through a feature branch. The working tree was
already on `main` from an earlier channel promotion and the commit was made
without checking the branch first.

**What was done about it.**

* The change was *not* reverted and history was *not* rewritten. `main` is a
  published channel and a force-push would have invalidated any clone.
* PR #48 was opened to route the same change back through `preview`. It was
  closed: opened as `head=main → base=preview`, it inverts the channel direction,
  and it could not merge anyway because the two branches had genuinely diverged.
* PR #49 re-opened the change from a proper feature branch
  (`feat/blog-story-rewrite`) onto `preview`. It was closed too: `preview` was
  behind `main`, so replaying the diff onto a stale base produced conflicts.
* The channels were then reconciled by merge rather than by replay:
  `main → preview` (convergence), then `preview → nightly → dev → main`.

**Consequence for the lineage.** One commit in `main`'s history
(`59b61a5`, "rewrite the body as the actual story…") did not pass through
`preview` first. Its content *is* in `preview`, `nightly` and `dev` — it arrived
there by merge — but anyone auditing "did every change to `main` pass through the
integration channel" will find this one that did not. That is the accurate answer,
and this note is the record of it.

**Related.** The channel set is now reconciled: all four branches carry the same
`web/app/page.tsx` and the same generated data. Two follow-on defects were found
during the reconciliation and fixed:

* A promote merge auto-merged `web/app/page.tsx` textually and produced a hybrid
  that referenced `DangerousBars` without importing it, so `dev` and `nightly`
  failed to build and were silently omitted from the deploy (404 on `/dev/` and
  `/nightly/`). A full-file rewrite should not be auto-merged; the affected
  channels were reset to the tree that actually builds.
* The deployed `<title>` still read "Small Models Calling the Shots" from the
  previous article, so every channel tab and search result contradicted the page.

---

## 2026-09-22 — recovered evidence reclassified

The 27-decision NanoJev/Jev J1 shadow pilot was narrated with a "provisional,
receipt not found" caveat. The pilot's temp artifacts
(`/tmp/nanojev-shadow-paired*`) were deleted, but a captured process log
survived and holds the complete run output. The caveat has been replaced with a
citation to `studies/slm-router-v0/data/nanojev-j1-shadow-pilot.json`.

Two corrections came out of the recovery and are recorded in the artifact: the
high-risk disagreement count is **10**, not the 11 that was recalled, and the
48.1% agreement rate was measured across **mismatched candidate sets** (the
matched rerun reports 100%). See the artifact's `discrepancy_note` and `caveat`.

---

## 2026-09-22 — Phase 1B `compiler+jev` was mislabelled as Jev

**What was wrong.** The Phase 1B bounded-choice arm `compiler+jev` was published as
"JEV" / "jev scorer", and its **45/84 at 31 ms** was narrated as the hosted TypeSafe
Jev router's score. It was never Jev. The arm has always been our local **NanoJev
0.6B** (the Qwen3-0.6B backbone).

**Where the label came from.** The arm's `model` field historically held the literal
display string `"JEV"` and every emission rewrote it to `nanojev_06b`, so no
measurement was wrong — only the name leaked. In z0evals the leaked strings were
`scripts/build_site_data.py:32` (`ARM_LABEL["compiler+jev"] = "jev scorer"`),
`scripts/build_site_data.py:344` (composition label `"qwen 4b + jev scorer"`), the
display text in `posts/slm-router-v0.md`, and the legacy chart mapping
`research-ui.js:16`. The generator now states the identity explicitly:
`/home/kvn/tmp/openjev/scripts/densify_measurements.py:264`
(`Arm("compiler+jev", "bounded", model="nanojev_06b", jev=True, scorer_type="nanojev")`),
`:459` (`"model_id": arm.model`) and `:466` (`"scorer_type": "nanojev"`).

**Evidence it was NanoJev.** Every `arm == "compiler+jev"` row in the immutable
`results/phase1b/p1b-20260921T1430Z/observations.jsonl` (84 rows) records
`model_id = "nanojev_06b"`,
`model_revision = "4a19595eada0857133c0d2be024f879a4077054b"` and `quant = "bfloat16"`.

**What was changed.** In `scripts/build_site_data.py`, `ARM_LABEL["compiler+jev"]` is
now `"nanojev 0.6b"` and the composition entry `qwen4b+jev` is labelled
`"qwen 4b + nanojev 0.6b"`. The arm id `compiler+jev`, the composition id
`qwen4b+jev`, the cascade id `compiler+jev+qwen3.5_4b` and every JSON key are
unchanged — ids are join keys. The article's display text now reads NanoJev 0.6B /
NanoJev, and the regenerated site data carries the corrected labels. No measurement,
count, interval or latency was altered; only the display name of the arm.

**History and raw data were not rewritten.** The immutable corpus under
`/home/kvn/tmp/openjev/results/` was not touched, and its `arm` ids were always
`compiler+jev`. No commit was amended, reverted or force-pushed.

**Separate experiment, unaffected.** The 27-decision J1 shadow pilot at
`studies/slm-router-v0/data/nanojev-j1-shadow-pilot.json` genuinely compares the
hosted remote TypeSafe Jev against local NanoJev (`jev_p50_ms` 304 vs
`nanojev_p50_ms` 236.4). That pilot is a different experiment with a different
`evidence_class` and a different run id; this correction does not rename or merge it,
and its `jevP50Ms` / `jevP95Ms` fields are untouched.

## 2026-09-22 — display identity centralised so this class of error cannot recur

**Summary for anyone reading old artifacts.**

```
historical frozen arm id `compiler+jev`
was initially interpreted in publication/UI code as hosted/generic Jev.

canonical Phase 1B rows identify the model as:
nanojev_06b @ revision 4a19595eada0857133c0d2be024f879a4077054b

frozen ids were not rewritten.
presentation semantics were corrected downstream.
```

This is recorded because a later reader will otherwise find `jev` in a 2026-09-21
run and reasonably ask why it means NanoJev there.

**Root cause.** The label was derived independently in three places — a
`partition("+")` machine in `build_component_data.py`, a hand-maintained
`ARM_LABEL` dict in `build_site_data.py`, and a regex inside `UtilityTie.tsx`.
Each was individually defensible; together they disagreed, and the deployed chart
rendered a beeswarm lane labelled bare `jev`. The evidence was correct the whole
time — only presentation drifted from it.

**What changed.**

* `scripts/arm_identity.py` is now the single resolver:
  `raw arm id → semantic components → short label → long label`. Total over every
  known arm, including generator-only cascade ids that are not in the corpus.
* `studies/slm-router-v0/data/arm-identity.json` is the single data source, and
  `web/data/arm-identity.json` is a byte-identical copy written in the same pass
  (`arm_identity.py --write`) so the two languages cannot drift.
* `web/lib/armIdentity.ts` reads that data. Components call it; none of them
  derive a label any more.
* Brevity in the visible figure is preserved (the 132px name column is unchanged
  in length). The canonical identity moved into the DOM instead:
  `data-arm-id="compiler+jev+qwen3.5_4b" data-model-id="nanojev_06b"`, with the
  long semantic name in a `<title>`. The UI may abbreviate; the evidence identity
  may not.

**What was deliberately NOT changed.** Frozen arm ids (`compiler+jev`,
`compiler+jev+qwen3.5_4b`, `qwen4b+jev`) are join keys and are untouched. The
word `jev` is not banned — the Southbridge / TypeSafe Jev project is a real and
different thing, and the external reference link and the J1 pilot comparison
(which genuinely contrasts hosted `jev` at 304 ms with local `nanojev` at
236 ms) both remain.

**New regression layer.**

* `tests/test_arm_identity.py` — enumerates every known arm and asserts its
  rendered label; asserts `compiler+jev` names nanojev and never renders a bare
  `jev` as a model identity; asserts the opposite for `nanojev`/`openjev` so the
  fix cannot over-reach; asserts the generated file stays in sync with the
  resolver and the web copy stays byte-identical.
* `scripts/audit_built_identity.py` — runs against the **built** output, not the
  source, because the original defect was invisible in every individual source
  file. It is a surface audit, not a text grep: it walks `data-arm-id`
  elements, the model-board name column, identity-bearing chart lanes and the
  ladder rungs, and separately asserts the frozen ids are still present verbatim
  and that the CSS/DOM contract (`data-model="compiler-first"` ↔
  `modelRow[data-model^=compiler-first]`) still holds. Bare `jev` in raw arm ids,
  in the `jev_uncertain` state id, in external links and in the J1 pilot sentence
  is explicitly allowed, with each exclusion documented in the script rather than
  silently ignored.
