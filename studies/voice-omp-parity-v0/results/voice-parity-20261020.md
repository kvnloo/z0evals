# Voice parity scoreboard — run `voice-parity-20261020-r1+voice-parity-20261020-bidi`

Pre-registered gates: `studies/voice-omp-parity-v0/README.md`. Control arm: `omp-live`. Reps per scenario per arm: 5.

| Metric | omp-live | z0live-bidi | z0live-realtime |
|---|---:|---:|---:|
| Valid runs | 39/40 | 40/40 | 39/40 |
| Session ready (p50) | 1,207 ms | 876 ms | 1,121 ms |
| EOS → first audible, direct turns p50 | 1,112 ms | 1,184 ms | 1,314 ms |
| EOS → first audible, direct turns p95 | 1,539 ms | 1,909 ms | 1,983 ms |
| … incl. stall-affected OMP turns p50 / p95 | 1,212 ms / 1,995 ms | 1,184 ms / 1,909 ms | 1,314 ms / 1,983 ms |
| OMP turns excluded for harness stalls | 19 | 0 | 0 |
| Direct turns with no audible reply | 0/22 | 0/35 | 0/34 |
| EOS → first audible, delegation turns p50 | 1,702 ms | 1,685 ms | 1,309 ms |
| Delegation used (work / repo) | 5/5 / 5/5 | 4/5 / 5/5 | 5/5 / 5/5 |
| Result spoken (delegation runs) | 10/10 | 9/10 | 10/10 |
| EOS → result audible p50 | 36,499 ms | 10,473 ms | 6,238 ms |
| Repo answer correct (`core.py`) | 5/5 | 5/5 | 0/5 |
| Filler phrases / delegation run | 0.5 | 0.4 | 0.2 |
| Barge-in → silence p50 | 974 ms | 1,107 ms | 138 ms |
| Barge-in → silence p95 | 1,220 ms | 1,367 ms | 191 ms |
| Barge not stopped | 0 | 0 | 0 |
| Barge follow-up answered (`Central`) | 5/5 | 5/5 | 5/5 |
| Stale resume after barge (runs) | 0 | 0 | 0 |
| False interruptions from noise | 1/5 | 1/5 | 0/4 |
| Noise transcribed as a user turn | 0 | 0 | 0 |
| Unwanted speech in 20 s after closing | 0 | 0 | 0 |
| Runs with repeated speech | 0 | 0 | 0 |
| Delegated on a direct question (runs) | 0 | 0 | 0 |

**z0live-bidi vs omp-live: FAIL** — failing: G2_direct_first_audible_p95, G4a_barge_to_silence_p50, G4b_barge_stops_within_1000ms, G5_zero_false_interruptions; undetermined: none
**z0live-realtime vs omp-live: FAIL** — failing: G1_direct_first_audible_p50, G2_direct_first_audible_p95, G3c_repo_correct_ge_control; undetermined: none

Per-scenario first-audible p50 (ms):

| Scenario | omp-live | z0live-bidi | z0live-realtime |
|---|---:|---:|---:|
| barge_in | 1,105 ms | 1,740 ms | 1,300 ms |
| closing_silence | 1,285 ms | 1,023 ms | 1,642 ms |
| greeting | 1,063 ms | 1,227 ms | 1,191 ms |
| noise_during_answer | 1,145 ms | 1,095 ms | 1,503 ms |
| quick_fact | 1,040 ms | 1,384 ms | 1,220 ms |
| rapid_followup | 1,327 ms | 1,179 ms | 1,328 ms |
| repo_question | 2,361 ms | 1,717 ms | 1,495 ms |
| work_status | 1,348 ms | 1,671 ms | 1,065 ms |
