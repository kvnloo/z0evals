"""Stall-robust OMP output clock from the sideband audio mirror (sensitivity analysis only).

The Codex sideband carries `session.output_audio.delta` chunks (200 ms, 24 kHz int16 LE) with
server-timeline `start_ms`/`end_ms`. Server timeline position p maps to local time p + c with
c = min over chunks of (local receipt - end_ms): the earliest-arrival line, which JS event-loop
stalls can only delay, never advance. RMS windows are 50 ms like the primary meter.
"""
import base64
import json
from pathlib import Path

import numpy as np

RATE = 24000
WIN = 1200  # 50 ms


def sideband_levels(run_dir: Path):
    path = run_dir / "sideband-audio.b64.jsonl"
    if not path.exists():
        return []
    chunks = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    chunks = [c for c in chunks if isinstance(c.get("delta"), str) and c.get("end_ms") is not None]
    if not chunks:
        return []
    c = min(ch["t"] - ch["end_ms"] for ch in chunks)
    out = []
    for ch in chunks:
        pcm = np.frombuffer(base64.b64decode(ch["delta"]), dtype="<i2").astype(np.float32) / 32768.0
        for k in range(len(pcm) // WIN):
            w = pcm[k * WIN : (k + 1) * WIN]
            end_pos = ch["start_ms"] + (k + 1) * 50
            out.append((round(end_pos + c, 1), float(np.sqrt((w**2).mean()))))
    out.sort()
    return out
