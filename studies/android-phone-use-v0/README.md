# Android phone-use evidence

Draft evidence study. z0evals imports and validates artifacts; it does not run the phone benchmark. The imported `data/phone-goal-summary.json` is the exact `bench/summary.json` blob from the local-only `hermes-phone-goal` commit recorded in `manifest.yaml`, not a new measurement. The commit preserves the summary; it is not proof of the exact versions that were executing during the experiment.

## Existing results

The source reports an S22+ over an ADB/SSH tunnel, using the phone-harness fast UIAutomator2 hierarchy path and Jev for decision selection. For each of two Settings goals, three runs were reported as completed: Android-version lookup had a 9.194 s median; battery lookup had a 4.995 s median. The separately measured phone_exec act-and-read median was 1.759 s (5 samples). The one-model-turn-per-step baseline is an estimate constructed from separate measurements, not an end-to-end matched comparison. The completion status is not evidence of an independent oracle.

A separate private Hermes report described S25 stable-screen hierarchy reads of approximately 2.05 s with stock dumping and 0.025 s with a persistent UIAutomator2 service. The underlying raw timings and tested revision have not been located; this remains a reported observation, not an imported result or Cua benchmark. The report also warned that a running persistent service interfered with plain `uiautomator dump`, and fast reads may precede UI settling.

## Import and validate

The local import spec is gitignored because it contains a machine-specific path. On a machine with access to the local source repository, create `imports/android-phone-use-v0.local.yaml` using `imports/slm-router-v0.example.yaml` as the template. Point `root` at the source repository, pin the commit from `manifest.yaml`, and allowlist only `bench/summary.json` to `data/phone-goal-summary.json`. Then:

```sh
python scripts/import_local.py imports/android-phone-use-v0.local.yaml
python scripts/validate.py
```

Do not import raw phone traces, screenshots, identifiers, or private logs without explicit privacy review. The source repository has no public remote, so the commit is not remotely reproducible. Do not publish this study as frozen or claim a Cua comparison until the source and sanitized evidence are available and the measurement is independently checked.

## Remaining comparison

Use a resettable, authorized fixture and a shared independent outcome oracle. Check that each available path can operate the same app, device and display before comparing; retain unavailable and non-equivalent paths as such. Measure setup, observation, action, fresh verification and whole-task latency separately, including failures. Run only with device ownership and the existing phone lock; the persistent UIAutomator service can conflict with other tooling.
