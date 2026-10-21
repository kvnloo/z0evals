# fsm-work-item-v0

Loop 1 of a "statechart, then verify" layer for the z0 agent factory: the
work-item lifecycle (Proposed -> Claimed -> Implementing -> Verifying ->
DraftPR -> Integrated -> Deployed -> OwnerAccepted -> Merged, plus Blocked,
Interrupted, Abandoned), with roles from ROLES-v0 and an owner-availability
input. Source: kvnloo/z0intelligence PR #183 (`docs/fsm/README.md` has the
diagram, the laws, the findings and the next loops).

| evidence | result |
| --- | --- |
| Bend laws L1-L7 (15 claims) | `hermes bend verify` **pass**, kernel recheck (Bend 2.0.34, Lean 4.34.0) |
| laws load-bearing | 10/10 law-breaking mutants rejected |
| Python twin == Bend | 400 seeded tapes, 5,077 events, all 12 phases, identical |
| replay on real data (2026-10-21 03:57Z) | 174 items; stale Company OS static service (31 behind, integrated line local-only); diverged + dirty z0intelligence service; 39 integrations without a head receipt (7 merged before tests finished); 6 default-branch merges without recorded owner acceptance; 13 dropped interrupted workers; 32 stranded integrations |

Scope: a Bend PASS is about `fsm.bend` only. The replay mapping is heuristic
and listed under `limitations` in `manifest.yaml`. Worker goals and logs are
personal traces and are not published here; only counts are.
