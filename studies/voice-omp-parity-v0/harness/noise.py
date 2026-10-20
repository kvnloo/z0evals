#!/usr/bin/env python3
"""Procedurally synthesize the non-speech noise clip (no third-party samples, so no license terms).

footsteps_door_keyboard: four heel strikes (low thump + gravel noise burst), a door slam
(broadband impulse with a 120 Hz resonant tail and latch click), then ~1.2 s of keyboard
clicks (short band-passed ticks at irregular 70-160 ms intervals). Deterministic (seeded).
Writes 24 kHz mono 16-bit WAV.
"""
import math
import random
import struct
import sys
import wave

RATE = 24000


def thump(rng, dur=0.18, f=70.0, amp=0.6):
    n = int(dur * RATE)
    out = []
    for i in range(n):
        t = i / RATE
        env = math.exp(-t * 28)
        out.append(amp * env * (math.sin(2 * math.pi * f * t) + 0.35 * (rng.random() * 2 - 1) * math.exp(-t * 60)))
    return out


def slam(rng):
    n = int(0.9 * RATE)
    out = []
    lp = 0.0
    for i in range(n):
        t = i / RATE
        noise = rng.random() * 2 - 1
        lp += 0.25 * (noise - lp)
        body = 0.9 * math.exp(-t * 9) * math.sin(2 * math.pi * 120 * t)
        crack = 0.8 * math.exp(-t * 45) * lp
        out.append(body + crack)
    # latch click 60 ms later
    for i in range(int(0.06 * RATE), int(0.07 * RATE)):
        out[i] += 0.5 * (rng.random() * 2 - 1)
    return out


def click(rng):
    n = int(0.012 * RATE)
    out = []
    prev = 0.0
    for i in range(n):
        t = i / RATE
        x = rng.random() * 2 - 1
        hp = x - prev  # crude high-pass for a plastic tick
        prev = x
        out.append(0.35 * math.exp(-t * 500) * hp)
    return out


def place(buf, clip, at):
    start = int(at * RATE)
    need = start + len(clip)
    if len(buf) < need:
        buf.extend([0.0] * (need - len(buf)))
    for i, v in enumerate(clip):
        buf[start + i] += v


def main(path):
    rng = random.Random(20261020)
    buf = []
    t = 0.05
    for _ in range(4):
        place(buf, thump(rng=rng), t)
        t += 0.55
    place(buf, slam(rng), t + 0.1)
    t += 0.9
    end = t + 1.2
    while t < end:
        place(buf, click(rng), t)
        t += rng.uniform(0.07, 0.16)
    buf.extend([0.0] * int(0.05 * RATE))
    peak = max(abs(v) for v in buf)
    gain = 0.5 / peak  # -6 dBFS peak
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v * gain)) * 32767)) for v in buf))
    print(f"noise {len(buf) / RATE:.2f}s peak=-6dBFS -> {path}")


if __name__ == "__main__":
    main(sys.argv[1])
