# phone-voice-stage-v0: pre-registration (z0live PR #48 on-device stage budget)

Owner request 2026-10-26: drive on-device evals on S25 Ultra and S22+ for the "Dessa-quality phone voice" roadmap.
Scope: per-stage CLI budget (TTS, streaming ASR endpointing, LLM first token), no end-to-end claim, no "Dessa parity" claim.

Timing disclosure: the S22+ and S25 TTS scored runs were started before this file was committed. The
thresholds below are the ones in the run protocol and were not changed after any scored data was seen.
The documented deviations are the thermal gate relaxations (see "Deviations").

## Gates (unchanged from protocol)
| ID | Metric | S25 | S22+ |
|---|---|---|---|
| T1 | TTS TTFA (call to first PCM chunk), short sentence | p50<=150 ms, p95<=250 ms | p50<=250, p95<=400 |
| T2 | TTS RTF, long sentence | <=0.5 | <=0.8 |
| T3 | Peak RSS (VmHWM) | <=350 MB | <=350 MB |
| T4 | No thermal status>=2 in 10 min soak; report skin slope | same | same |
| E1 | EOS to EOU commit | p50<=300, p95<=500 ms | p50<=450, p95<=700 |
| E2 | WER | <=12% | <=15% |
| E3 | False EOU on long-thought + 1.2 s pause fixture | 0 | 0 |
| L1 | LLM first token, warm, ~60-token prompt | <=200 ms | <=350 ms |
| B  | E1 p50 + L1 + T1 p50 + A1 p50 | <=500 ms | report |
A1/A2 (acoustic boundary) are NOT RUN in this pass (needs a mic-capturing APK; not built).

Blocking regressions: crash/OOM, stuck audio, non-zero false EOU, duplicated PCM.

## Method
Stratum: CLI generated-PCM (no speaker, no mic). Not comparable to the #44 synthetic-groot stratum or the OMP acoustic stratum.
Fixtures: tts_texts.tsv (24 sentences: 8 short, 8 medium, 8 long); ASR WAVs from Kokoro v0.19 int8 am_michael (prepare_assets.py).
Reps: 3 passes x 8 texts = 24 trials per cell, 4 s gap, order shuffled within pass; arms run as separate cells in randomized order per bucket (not per-trial interleaving).
Pilot (excluded): 1 rep, harness debug only.

## Deviations (disclosed)
- Thermal gate: S25 SKIN reads 37.7 C idle, so "<=37" is unreachable; gate = status 0 and skin<=38. S22+ sits at Thermal Status 1 (skin ~37.5) while on USB; gate = status<=1 and skin<=38, 4 min max wait then proceed (flagged in therm.csv).
- Pocket via sherpa-onnx needs a reference wav: the bundled Kyutai bria.wav test voice is used (no cloning of a real person).
- Pocket checkpoint is the sherpa export dated 2026-01-26 (not the Oct-2026 18.2M/6.9M releases).
- Parakeet-EOU is not supported by sherpa-onnx v2.0.0; E1/E3 use sherpa-onnx streaming zipformer endpoint rules instead (a silence-rule baseline, not a learned EOU). Gate meaning differs and is reported as such.
- Phonon 31M: BLOCKED (build of external gradium-ai/xn-ptts with cargo-ndk was denied by the permission system in this session).
