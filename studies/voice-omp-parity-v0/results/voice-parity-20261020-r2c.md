# Voice parity scoreboard — run `voice-parity-20261020-r1+voice-parity-20261020-r2c`

Pre-registered gates: `studies/voice-omp-parity-v0/README.md`. Control arm: `omp-live`. Reps per scenario per arm: 5.

| Metric | omp-live | z0live-bidi |
|---|---:|---:|
| Valid runs | 39/40 | 10/10 |
| Session ready (p50) | 1,207 ms | 854 ms |
| EOS → first audible, direct turns p50 | 1,112 ms | 1,263 ms |
| EOS → first audible, direct turns p95 | 1,539 ms | 1,638 ms |
| … incl. stall-affected OMP turns p50 / p95 | 1,212 ms / 1,995 ms | 1,263 ms / 1,638 ms |
| OMP turns excluded for harness stalls | 19 | 0 |
| Direct turns with no audible reply | 0/22 | 0/15 |
| EOS → first audible, delegation turns p50 | 1,702 ms | – |
| Delegation used (work / repo) | 5/5 / 5/5 | 0/0 / 0/0 |
| Result spoken (delegation runs) | 10/10 | 0/0 |
| EOS → result audible p50 | 36,499 ms | – |
| Repo answer correct (`core.py`) | 5/5 | 0/0 |
| Filler phrases / delegation run | 0.5 | – |
| Barge-in → silence p50 | 974 ms | 885 ms |
| Barge-in → silence p95 | 1,220 ms | 1,167 ms |
| Barge not stopped | 0 | 0 |
| Barge follow-up answered (`Central`) | 5/5 | 5/5 |
| Stale resume after barge (runs) | 0 | 1 |
| False interruptions from noise | 1/5 | 0/0 |
| Noise transcribed as a user turn | 0 | 0 |
| Unwanted speech in 20 s after closing | 0 | 0 |
| Runs with repeated speech | 0 | 0 |
| Delegated on a direct question (runs) | 0 | 0 |

**z0live-bidi vs omp-live: FAIL** — failing: G1_direct_first_audible_p50, G3c_repo_correct_ge_control, G4b_barge_stops_within_1000ms, G4d_no_stale_resume; undetermined: G3a_delegation_ack_p50, G3b_delegation_used_ge_4of5_each, G8_filler_le_control_plus_1

Per-scenario first-audible p50 (ms):

| Scenario | omp-live | z0live-bidi |
|---|---:|---:|
| barge_in | 1,105 ms | 1,449 ms |
| closing_silence | 1,285 ms | – |
| greeting | 1,063 ms | – |
| noise_during_answer | 1,145 ms | – |
| quick_fact | 1,040 ms | – |
| rapid_followup | 1,327 ms | 1,206 ms |
| repo_question | 2,361 ms | – |
| work_status | 1,348 ms | – |
