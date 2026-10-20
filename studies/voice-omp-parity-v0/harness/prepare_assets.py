#!/usr/bin/env python3
"""Normalize TTS/noise clips and emit per-rate float32 PCM for the arm drivers.

Speech: trim leading/trailing silence (< -50 dBFS, 10 ms frames), scale so the active-speech
RMS (10 ms frames above -40 dBFS) is TARGET_SPEECH_DBFS, peak-capped at -1 dBFS.
Noise: scaled so its peak is NOISE_PEAK_DBFS (clips stay impulsive).
Outputs <id>.<rate>.f32 (mono float32 LE) at 16 kHz (OMP native input) and 48 kHz
(Chromium WebAudio), plus assets.json with exact durations and speech end offsets.
Resampling uses sox (very-high-quality).
"""
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

TARGET_SPEECH_DBFS = -20.0
NOISE_PEAK_DBFS = -6.0
RATES = (16000, 24000, 48000)


def read_wav(path):
    with wave.open(str(path)) as w:
        assert w.getnchannels() == 1 and w.getsampwidth() == 2
        rate = w.getframerate()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
    return data, rate


def frames(x, rate, ms=10):
    n = int(rate * ms / 1000)
    k = len(x) // n
    return x[: k * n].reshape(k, n), n


def dbfs(v):
    return 20 * np.log10(max(float(v), 1e-9))


def main(src_dir, out_dir):
    src, out = Path(src_dir), Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((src / "tts-manifest.json").read_text())
    assets = {"target_speech_dbfs": TARGET_SPEECH_DBFS, "noise_peak_dbfs": NOISE_PEAK_DBFS, "tts": {k: v for k, v in manifest.items() if k != "utterances"}, "clips": {}}
    items = [(k, src / v["file"], "speech") for k, v in manifest["utterances"].items()]
    items.append(("footsteps_door_keyboard", src / "footsteps_door_keyboard.24k.wav", "noise"))
    for cid, path, kind in items:
        x, rate = read_wav(path)
        fr, n = frames(x, rate)
        rms = np.sqrt((fr**2).mean(axis=1))
        if kind == "speech":
            on = np.where(20 * np.log10(np.maximum(rms, 1e-9)) > -50)[0]
            x = x[on[0] * n : (on[-1] + 1) * n]
            fr, n = frames(x, rate)
            rms = np.sqrt((fr**2).mean(axis=1))
            active = rms[20 * np.log10(np.maximum(rms, 1e-9)) > -40]
            gain = 10 ** (TARGET_SPEECH_DBFS / 20) / float(np.sqrt((active**2).mean()))
            gain = min(gain, 10 ** (-1 / 20) / float(np.abs(x).max()))
        else:
            gain = 10 ** (NOISE_PEAK_DBFS / 20) / float(np.abs(x).max())
        y = (x * gain).astype(np.float32)
        base = out / f"{cid}.24k.norm.wav"
        with wave.open(str(base), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes((np.clip(y, -1, 1) * 32767).astype("<i2").tobytes())
        fr2, _ = frames(y, rate)
        rms2 = np.sqrt((fr2**2).mean(axis=1))
        act = rms2[20 * np.log10(np.maximum(rms2, 1e-9)) > -40]
        entry = {"kind": kind, "duration_ms": round(len(y) / rate * 1000, 1), "gain_db": round(dbfs(gain), 2), "peak_dbfs": round(dbfs(np.abs(y).max()), 2), "active_rms_dbfs": round(dbfs(np.sqrt((act**2).mean())) if len(act) else -120, 2), "files": {}}
        for r in RATES:
            f32 = out / f"{cid}.{r // 1000}k.f32"
            subprocess.run(["sox", str(base), "-t", "raw", "-e", "floating-point", "-b", "32", "-L", "-r", str(r), str(f32), "rate", "-v"], check=True)
            entry["files"][str(r)] = f32.name
        assets["clips"][cid] = entry
        print(cid, entry["duration_ms"], "ms", entry["active_rms_dbfs"], "dBFS active")
    (out / "assets.json").write_text(json.dumps(assets, indent=2))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
