# breath-phase-camera

Status: **draft — literature survey + synthetic reproduction. No real-video result yet.**

Question: can NOOP's live heart meditation watch breathing through the front camera, on-device, well
enough to say *in / out / hold*, and fuse it with ring/strap R-R for resonance-breathing biofeedback?

## Findings so far

* **Method choice (source-reported):** chest/shoulder vertical motion beats face rPPG and face deep
  models for respiration. On COHFACE, Profile-1D MAE 0.84–1.29 br/min (~0.1 ms/frame), Farnebäck 1.02,
  RAFT 0.64, vs MTTS-CAN 2.31 and BigSmall 3.92 (Boccignone et al. 2025, ACM CSUR). Google's
  front-camera upper-torso vertical-flow method reached MAE 0.78 br/min in 50 seated adults at
  1–4 ms/frame on Pixel phones (Bae et al. 2022). `data/literature.json`.
* **Gap:** no public RGB benchmark reports inhale/exhale/hold *phase* accuracy — phase is a claim NOOP
  must validate itself.
* **Chosen:** dependency-free Profile-1D on the CameraX Y plane, 4 torso regions with band-SNR
  selection, causal velocity-sign phase with hysteresis + stillness holds, fused with R-R (RSA per
  measured breath, breath→HR lag; resonance at ≈0°), optional adaptive pacer. Default-off Experimental.
* **Synthetic reproduction (not real-video evidence):** 26 JVM tests at `kvnloo/noop@e12cd056`
  (25 pass, 1 skipped = the real-clip evaluator awaiting clips); full app suite 6755 tests, 0 failures.
  `data/synthetic-tests.json`.
* **Biofeedback evidence shaping the UI:** pacer-led slow breathing is the supported intervention
  (Goessl 2017 g≈0.8; Lehrer 2020; Laborde 2022); individual RF vs 0.1 Hz and 1:2 vs 1:1 I:E show no
  reliable difference — so the camera's job is adherence, holds, and measured coupling, and the adaptive
  pacer is a second default-off toggle.

## Pending: recorded-clip gate

Protocol `noop-breathcam-v1` (`data/protocol.json`; guide WAV from `Tools/breathcam/protocol.py`):
10, 6 and 4 br/min blocks plus box-breathing holds; the guide's start beeps align each clip.
Gate: ≥ 6 clips over ≥ 2 days in varied clothing/light/posture; rate error ≤ 1.0 br/min per paced
block; phase accuracy ≥ 85% with ≥ 80% coverage; hold recall and precision ≥ 80%. Results (aggregates
only, never video) will replace `data/clip-gate.json`, pass or fail.
