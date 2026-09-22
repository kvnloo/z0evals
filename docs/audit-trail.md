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
