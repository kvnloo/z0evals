#!/usr/bin/env python3 -I
"""Build ASR stimulus WAVs (Kokoro v0.19 int8, sid 6 = am_michael) via local sherpa-onnx CLI.
16 kHz mono PCM16, active-speech RMS -20 dBFS, peak <= -1 dBFS, -85 dBFS noise floor between clips.
Writes assets/<id>.wav + assets/manifest.jsonl (ground-truth text, eos_sample, speech_start_sample)."""
import json, os, subprocess, sys, wave
import numpy as np

R = os.path.expanduser("~/tmp/voice-evals")
CLI = [p for p in __import__("glob").glob(R + "/x64/*/bin/sherpa-onnx-offline-tts")][0]
KOK = __import__("glob").glob(R + "/kokoro/kokoro-int8-en-v0_19")[0]
OUT = sys.argv[1] if len(sys.argv) > 1 else R + "/assets"
os.makedirs(OUT, exist_ok=True)
SR = 16000
LEAD, TAIL = 1.5, 3.5  # seconds of floor noise before / after speech
rng = np.random.default_rng(20261027)

FIX = {
 "f01": "What time is my first meeting tomorrow morning?",
 "f02": "Set a timer for ten minutes please.",
 "f03": "Can you tell me the weather forecast for Saturday afternoon?",
 "f04": "Remind me to call my mother at six thirty tonight.",
 "f05": "How many calories are in a medium banana?",
 "f06": "Send a message to Sarah saying I will be fifteen minutes late.",
 "f07": "Turn the living room lights off and lock the front door.",
 "f08": "What is the capital of Australia, and how far is it from Sydney?",
}
PAUSE = ("So I was thinking about the trip next month,", "and I think we should probably book the hotel near the station.")
BACK = "Mm hm."

def tts(text, path):
    subprocess.run([CLI, f"--kokoro-model={KOK}/model.int8.onnx", f"--kokoro-voices={KOK}/voices.bin",
                    f"--kokoro-tokens={KOK}/tokens.txt", f"--kokoro-lexicon={R}/dl/lexicon-en-us.txt",
                    "--num-threads=2", "--sid=6", f"--output-filename={path}", text],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def readwav(path):
    with wave.open(path) as w:
        sr, n, ch = w.getframerate(), w.getnframes(), w.getnchannels()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float64) / 32768
    if ch > 1: x = x.reshape(-1, ch).mean(1)
    if sr != SR:
        t = np.arange(0, len(x) / sr, 1 / SR)
        x = np.interp(t, np.arange(len(x)) / sr, x)
    return x

def trim(x, thr=1e-3):
    idx = np.where(np.abs(x) > thr)[0]
    return x[idx[0]: idx[-1] + 1]

def norm(x, dbfs=-20.0):
    act = np.abs(x) > 10 ** (-45 / 20)  # active samples
    rms = np.sqrt(np.mean(x[act] ** 2)) if act.any() else 1e-6
    y = x * (10 ** (dbfs / 20) / rms)
    pk = np.max(np.abs(y))
    if pk > 10 ** (-1 / 20): y *= 10 ** (-1 / 20) / pk
    return y

def floor(n): return rng.normal(0, 10 ** (-85 / 20), n)

def noise_clip(n):
    """synthetic footsteps/door/keyboard transients, peak -6 dBFS"""
    y = np.zeros(n)
    def burst(pos, dur, f, amp):
        t = np.arange(int(dur * SR)); e = np.exp(-t / (dur * SR / 4))
        s = amp * e * (np.sin(2 * np.pi * f * t / SR) + 0.5 * rng.normal(0, 1, len(t)))
        end = min(n, pos + len(s)); y[pos:end] += s[: end - pos]
    for p in np.arange(0.4, n / SR - 0.4, 0.55): burst(int(p * SR), 0.12, 90, 0.5)         # footsteps
    burst(int(n * 0.45), 0.35, 150, 0.8)                                                   # door
    for p in np.arange(0.6, n / SR - 0.6, 0.11)[::2]: burst(int(p * SR), 0.02, 3500, 0.25)  # keyboard
    return y * (10 ** (-6 / 20) / np.max(np.abs(y)))

def write(name, speech, truth, noisy=False, pre=None):
    sp = norm(speech)
    x = np.concatenate([floor(int(LEAD * SR)), sp, floor(int(TAIL * SR))])
    start, eos = int(LEAD * SR), int(LEAD * SR) + len(sp)
    if noisy: x = x + noise_clip(len(x))
    pk = np.max(np.abs(x))
    if pk > 10 ** (-1 / 20): x *= 10 ** (-1 / 20) / pk
    with wave.open(f"{OUT}/{name}.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    return dict(id=name, truth=truth, speech_start_sample=start, eos_sample=eos, noisy=noisy, kind=pre or "fixture")

man = []
tmp = OUT + "/_tmp.wav"
for k, t in FIX.items():
    tts(t, tmp); s = trim(readwav(tmp))
    man.append(write(k, s, t))
    man.append(write(k + "g", s, t, noisy=True, pre="noisy"))
tts(PAUSE[0], tmp); a = trim(readwav(tmp)); tts(PAUSE[1], tmp); b = trim(readwav(tmp))
long_ = np.concatenate([a, np.zeros(int(1.2 * SR)), b])
d = write("p01", long_, " ".join(PAUSE), pre="long_thought_pause1.2s")
d["mid_pause_start_sample"] = d["speech_start_sample"] + len(a); d["mid_pause_end_sample"] = d["mid_pause_start_sample"] + int(1.2 * SR)
man.append(d)
tts(BACK, tmp); man.append(write("b01", trim(readwav(tmp)), BACK, pre="backchannel_only"))
os.remove(tmp)
with open(OUT + "/manifest.jsonl", "w") as f:
    for m in man: f.write(json.dumps(m) + "\n")
print(len(man), "clips")
