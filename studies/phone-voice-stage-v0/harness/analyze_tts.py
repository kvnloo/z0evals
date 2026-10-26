#!/usr/bin/env python3 -I
"""Analyze ttsbench trials -> receipts.jsonl + summary. usage: analyze_tts.py <dir> <device_label> <serial> <fingerprint>"""
import json, sys, os, bisect, statistics as st
d, dev, serial, fp = sys.argv[1:5]
GATE = {"s25": dict(t1p50=150, t1p95=250, rtf=0.5), "s22": dict(t1p50=250, t1p95=400, rtf=0.8)}[dev]
MODEL_SHA = "2f3b88823cbbb9bf0b2477ec8ae7b3fec417b3a87b6bb5f256dba66f2ad967cb"  # tarball sha256 (sherpa-onnx-pocket-tts-int8-2026-01-26)

def load(fn):
    p = os.path.join(d, fn)
    return [json.loads(l) for l in open(p)] if os.path.exists(p) else []
def therm(fn):
    rows = []
    p = os.path.join(d, fn)
    if os.path.exists(p):
        for l in open(p).read().splitlines()[1:]:
            f = l.split(",")
            try: rows.append((int(f[0]), int(f[1]), float(f[2]), int(f[3]) / 10 if len(f) > 3 and f[3] else None, int(f[4]) if len(f) > 4 and f[4] else None))
            except Exception: pass
    return rows
def near(rows, t):
    if not rows: return None
    i = bisect.bisect_left([r[0] for r in rows], t)
    c = [rows[j] for j in (i - 1, i) if 0 <= j < len(rows)]
    return min(c, key=lambda r: abs(r[0] - t))
def pct(v, p):
    v = sorted(v); k = (len(v) - 1) * p; f = int(k); c = min(f + 1, len(v) - 1)
    return v[f] + (v[c] - v[f]) * (k - f)

trials = load("dev_out/trials.jsonl"); soak = load("dev_out/soak.jsonl")
th = therm("therm.csv"); ths = therm("therm_soak.csv")
rec = open(os.path.join(d, "receipts.jsonl"), "w")
for src, T, TH in (("scored", trials, th), ("soak", soak, ths)):
    for t in T:
        ts = t["wall_ns"] // 10**9; n = near(TH, ts)
        r = dict(device=dict(label=dev, serial=serial, fingerprint=fp), component="tts", backend="CPU(onnxruntime,sherpa-onnx v2.0.0 C API)",
                 model="sherpa-onnx-pocket-tts-int8-2026-01-26", model_sha256=MODEL_SHA, stratum="cli_generated_pcm_no_acoustic", phase=src,
                 cell=t["tag"], threads=t["threads"], text_id=t["id"], bucket=t["bucket"], ts_epoch=ts,
                 metrics=dict(ttfa_ms=t["ttfa_ms"], synth_ms=t["synth_ms"], audio_s=t["audio_s"], rtf=t["rtf"], chunks=t["chunks"], max_chunk_gap_ms=t["max_chunk_gap_ms"], vmhwm_mb=t["vmhwm_kb"] / 1024, ok=t["ok"]),
                 thermal=dict(status=n[1], skin_c=n[2], battery_temp_c=n[3], battery_level=n[4], sample_age_s=abs(n[0] - ts)) if n else None)
        rec.write(json.dumps(r) + "\n")
rec.close()
cells = {}
for t in trials: cells.setdefault(t["tag"], []).append(t)
print(f"== {dev} TTS (n trials={len(trials)}; soak={len(soak)}) gates: {GATE}")
print(f"{'cell':14}{'n':>4}{'ok':>4}{'ttfa p50':>10}{'p95':>8}{'rtf p50':>9}{'p95':>7}{'RSS max MB':>11}{'gap max ms':>11}")
for c in sorted(cells):
    v = cells[c]; ok = [x for x in v if x["ok"]]
    tt = [x["ttfa_ms"] for x in ok]; rr = [x["rtf"] for x in ok]
    print(f"{c:14}{len(v):4}{len(ok):4}{pct(tt,.5):10.0f}{pct(tt,.95):8.0f}{pct(rr,.5):9.3f}{pct(rr,.95):7.3f}{max(x['vmhwm_kb'] for x in v)/1024:11.0f}{max(x['max_chunk_gap_ms'] for x in v):11.0f}")
if soak:
    first = soak[:10]; last = soak[-10:]
    sk = [r for r in ths if r]
    print(f"soak: n={len(soak)} dur~{soak[-1]['wall_ns']//10**9 - soak[0]['wall_ns']//10**9}s rtf first10 p50={pct([x['rtf'] for x in first],.5):.3f} last10 p50={pct([x['rtf'] for x in last],.5):.3f}; ttfa first10 {pct([x['ttfa_ms'] for x in first],.5):.0f} last10 {pct([x['ttfa_ms'] for x in last],.5):.0f}")
    if sk:
        slope = (sk[-1][2] - sk[0][2]) / max(1, (sk[-1][0] - sk[0][0]) / 60)
        print(f"soak thermal: status max={max(r[1] for r in sk)} skin start={sk[0][2]} end={sk[-1][2]} max={max(r[2] for r in sk)} slope={slope:.3f} C/min; battery level {sk[0][4]}->{sk[-1][4]}")
