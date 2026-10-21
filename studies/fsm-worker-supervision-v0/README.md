# fsm-worker-supervision-v0

Loop 2 of the "statechart, then verify" layer for the z0 agent factory:
supervising the workers themselves. `Dispatched -> Running (heartbeats) ->
{Completed | Interrupted | Stalled} -> Resumed | Abandoned | Integrated`, plus
Overdue (interrupted past the limit, the needs-Kevin queue), a lease per
worktree/branch, the phone install lock and the S25's foreground. Source:
kvnloo/z0intelligence PR #184 (`docs/fsm/worker-supervision.md` has the
diagram, the laws, the findings and the 13-worker action table).

| evidence | result |
| --- | --- |
| Bend laws W1-W6 (19 claims) | `hermes bend verify` **pass**, kernel recheck (Bend 2.0.34, Lean 4.34.0); `hermes bend replay` matches |
| laws load-bearing | 17/17 law-breaking mutants rejected |
| Python twin == Bend | 400 worker tapes (3,370 events, all 9 phases) + 100 lease + 100 device tapes, identical |
| replay on real data (2026-10-21 05:31Z) | 26 Overdue workers (loop 1's 13: 10 resume, 2 already integrated, 1 abandon); 419 writes inside another session's lease; 1 orphan background process; groot heavy.lock: 118/333 jobs waited ~21.5 h; 1,695 heavy commands on groot outside fleet-build (97 after the fleet came up); fleet 36 jobs, no queue wait; 7 S25 installs without the lock; 11 S25 inputs without a foreground check |

Scope: a Bend PASS is about `fsm.bend` only; the replay mapping is heuristic
and listed under `limitations` in `manifest.yaml`. Worker goals, logs,
commands and paths are personal traces and are not published; only counts are.
