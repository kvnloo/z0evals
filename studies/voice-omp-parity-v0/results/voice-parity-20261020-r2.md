# Voice parity scoreboard — run `voice-parity-20261020-r1+voice-parity-20261020-r2`

Pre-registered gates: `studies/voice-omp-parity-v0/README.md`. Control arm: `omp-live`. Reps per scenario per arm: 5.

| Metric | omp-live | z0live-bidi | z0live-realtime |
|---|---:|---:|---:|
| Valid runs | 39/40 | 40/40 | 40/40 |
| Session ready (p50) | 1,207 ms | 887 ms | 1,051 ms |
| EOS → first audible, direct turns p50 | 1,112 ms | 1,265 ms | 1,815 ms |
| EOS → first audible, direct turns p95 | 1,539 ms | 1,960 ms | 2,978 ms |
| … incl. stall-affected OMP turns p50 / p95 | 1,212 ms / 1,995 ms | 1,265 ms / 1,960 ms | 1,815 ms / 2,978 ms |
| OMP turns excluded for harness stalls | 19 | 0 | 0 |
| Direct turns with no audible reply | 0/22 | 3/35 | 0/35 |
| EOS → first audible, delegation turns p50 | 1,702 ms | 1,798 ms | 1,830 ms |
| Delegation used (work / repo) | 5/5 / 5/5 | 5/5 / 5/5 | 4/5 / 5/5 |
| Result spoken (delegation runs) | 10/10 | 10/10 | 9/10 |
| EOS → result audible p50 | 36,499 ms | 13,172 ms | 2,925 ms |
| Repo answer correct (`core.py`) | 5/5 | 5/5 | 5/5 |
| Filler phrases / delegation run | 0.5 | 0.4 | 0.6 |
| Barge-in → silence p50 | 974 ms | 1,190 ms | 237 ms |
| Barge-in → silence p95 | 1,220 ms | 1,392 ms | 239 ms |
| Barge not stopped | 0 | 0 | 0 |
| Barge follow-up answered (`Central`) | 5/5 | 5/5 | 5/5 |
| Stale resume after barge (runs) | 0 | 0 | 0 |
| False interruptions from noise | 1/5 | 2/5 | 0/5 |
| Noise transcribed as a user turn | 0 | 1 | 0 |
| Unwanted speech in 20 s after closing | 0 | 0 | 0 |
| Runs with repeated speech | 0 | 0 | 0 |
| Delegated on a direct question (runs) | 0 | 0 | 0 |

**z0live-bidi vs omp-live: FAIL** — failing: G1_direct_first_audible_p50, G2_direct_first_audible_p95, G4a_barge_to_silence_p50, G4b_barge_stops_within_1000ms, G5_zero_false_interruptions; undetermined: none
**z0live-realtime vs omp-live: FAIL** — failing: G1_direct_first_audible_p50, G2_direct_first_audible_p95; undetermined: none

Per-scenario first-audible p50 (ms):

| Scenario | omp-live | z0live-bidi | z0live-realtime |
|---|---:|---:|---:|
| barge_in | 1,105 ms | 1,508 ms | 1,574 ms |
| closing_silence | 1,285 ms | 1,065 ms | 2,032 ms |
| greeting | 1,063 ms | 1,304 ms | 1,677 ms |
| noise_during_answer | 1,145 ms | 996 ms | 2,403 ms |
| quick_fact | 1,040 ms | 1,309 ms | 1,606 ms |
| rapid_followup | 1,327 ms | 1,487 ms | 1,854 ms |
| repo_question | 2,361 ms | 1,861 ms | 1,985 ms |
| work_status | 1,348 ms | 1,734 ms | 1,664 ms |

## Round 2 notes (post-hoc readings, not pre-registered verdicts)

- Block `voice-parity-20261020-r2`: z0live arms only, 40 runs each, interleaved, 06:00-07:10 CDT, broker
  kvnloo/z0live `b9c6b3f`-equivalent worktree (`58b1644`+`7a59645`), isolated port 18793. The OMP column is the
  unchanged 2026-10-20 r1 control block (not re-run). Host load average 25-51 during the block (r1: ~21-30).
- Client: `--client apk` (mirrors lawnchair `feat/z0live-realtime` after 3080a06: semantic_vad eagerness high,
  speech gate, 250 ms barge probe, early reply, interpret-not-read inbox). r1 used the 6db52cb port (server_vad 450 ms,
  interrupt on speech_started). Harness `158d8c0` for the first 17 runs, `bf9c9fd` after (await_result fix only).
- Plumbing narration (regex: work history, task status, Hermes, inbox, lookup, agent, tool) in the 10 delegation
  runs per arm: realtime 0/10 (r1: 10/10), bidi 0/10.
- Realtime direct-turn breakdown (median after end of speech): speech_stopped 806 ms, first transcript delta
  1,038 ms, response.created 1,108 ms, output_audio_buffer.started 1,506 ms, audible 1,774 ms. The speech gate
  (reply only after transcript words) costs ~450 ms vs r1's server_vad auto-reply.
- Realtime barge-in: the server cleared output on real speech_started (`output_audio_buffer.cleared` with
  `interrupt_response:false`) in barge runs but not on the noise clip; the word-gated probe interrupt followed at
  ~0.6-0.7 s.
- Realtime work_status r1: the response "On it." ran 33 s to `max_output_tokens` with no tool call (provider
  anomaly), the only missed delegation.
- Bidi rapid_followup: 3/5 q2 replies inaudible, caused by the client buffered-tail duck (the full-duplex answer
  streamed before its turn was created). Fixed in lawnchair a385752 / harness 8bc7639; see block r2c.
- No `session.context_window.*` wedge occurred in 55 bidi sessions, so the new broker guard did not fire.
- Block `voice-parity-20261020-r2c` (bidi only, rapid_followup + barge_in x5, harness 8bc7639 = lawnchair
  a385752 duck rules, 07:20-07:30 CDT during a local Gradle build): direct turns with no audible reply 0/15,
  first audible p50/p95 1,263/1,638 ms, barge-in to silence p50/p95 885/1,167 ms, follow-up answered 5/5.
  Small sample; see `voice-parity-20261020-r2c.md`.
