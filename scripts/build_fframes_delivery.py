#!/usr/bin/env python3
"""Freeze the fframestudio delivery study and derive the page's data document.

Two steps:

  freeze --clone <path-to-fframestudio-clone>
      Reads an allowlist of files at the pinned commit with `git show`, never from
      the worktree, and writes them to studies/fframes-delivery-v0/data/. Files that
      carry scrubbed local-path fields (`<local>/...`) are written as *.clean.json with
      those fields removed. data/provenance.json records source path, source sha256,
      frozen path, frozen sha256, and what the cleaning removed.

  site (default)
      Reads only the frozen files and writes web/data/fframes-delivery-v0.json.
      Recomputes pooled mean and p5 from frames.csv with the source's own percentile
      rule and fails if they disagree with summary.json.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "fframes-delivery-v0"
DATA = STUDY / "data"
SITE_OUT = ROOT / "web" / "data" / "fframes-delivery-v0.json"

REPO = "kvnloo/fframestudio"
COMMIT = "1a68268b24634332ed9b0fdc348168de91053b4f"

RAW = [
    "delivery/REPORT.md",
    "delivery/RESEARCH.md",
    "delivery/platforms.json",
    "delivery/evidence/summary.json",
    "delivery/evidence/frames.csv",
    "delivery/evidence/gates.json",
]
CLEAN = [
    "delivery/evidence/results.json",
    "delivery/evidence/gradient10.json",
]

PLATFORMS = ["youtube", "shorts", "tiktok", "reels", "x"]
CONTENTS = ["ui", "gradient", "satellite", "motion"]
ARMS = ["naive", "fast"]  # "fast" is the source's name for the selected recipe ("ours")
FRAME_KEYS = ["vmaf", "vmaf_neg"]
FORBIDDEN = ["/home/", "/Users/", "/root/", "/mnt/", "/tmp/"]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_show(clone: Path, path: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(clone), "show", f"{COMMIT}:{path}"], check=True, capture_output=True
    ).stdout


def scrub(obj, where: str, removed: list[str]):
    """Drop every key whose string value is a scrubbed local path."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if isinstance(v, str) and "<local>" in v:
                removed.append(f"{where}.{k}")
                continue
            out[k] = scrub(v, f"{where}.{k}", removed)
        return out
    if isinstance(obj, list):
        return [scrub(v, f"{where}[]", removed) for v in obj]
    return obj


def check_public(name: str, b: bytes) -> None:
    text = b.decode("utf-8", "replace")
    for needle in FORBIDDEN:
        if needle in text:
            raise SystemExit(f"{name}: contains private-looking path fragment {needle!r}")


def freeze(clone: Path) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    prov = {"repo": REPO, "commit": COMMIT, "files": []}
    for src in RAW:
        b = git_show(clone, src)
        check_public(src, b)
        dst = DATA / Path(src).name
        dst.write_bytes(b)
        prov["files"].append(
            {"source": src, "source_sha256": sha(b), "path": f"data/{dst.name}", "sha256": sha(b), "transform": "verbatim"}
        )
    for src in CLEAN:
        b = git_show(clone, src)
        removed: list[str] = []
        cleaned = scrub(json.loads(b), "$", removed)
        out = (json.dumps(cleaned, indent=1, sort_keys=True) + "\n").encode()
        check_public(src, out)
        if b"<local>" in out:
            raise SystemExit(f"{src}: cleaning left a <local> path behind")
        dst = DATA / (Path(src).stem + ".clean.json")
        dst.write_bytes(out)
        prov["files"].append(
            {
                "source": src,
                "source_sha256": sha(b),
                "path": f"data/{dst.name}",
                "sha256": sha(out),
                "transform": "json re-serialized; keys whose value was a scrubbed <local>/ file path removed",
                "removed_keys": sorted(set(removed)),
            }
        )
    (DATA / "provenance.json").write_text(json.dumps(prov, indent=2) + "\n")
    for f in prov["files"]:
        print(f"{f['sha256']}  {f['path']}  <- {f['source']} ({f['source_sha256'][:12]})")


def stats(values: list[float]) -> dict:
    """Same rule as delivery/summarize.py: linear-interpolated 5th percentile."""
    ordered = sorted(values)
    pos = (len(ordered) - 1) * 0.05
    lo = int(pos)
    p5 = ordered[lo] + (ordered[min(lo + 1, len(ordered) - 1)] - ordered[lo]) * (pos - lo)
    return {"mean": statistics.mean(ordered), "p5": p5}


def site() -> None:
    summary = json.loads((DATA / "summary.json").read_text())
    results = json.loads((DATA / "results.clean.json").read_text())
    gradient = json.loads((DATA / "gradient10.clean.json").read_text())
    gates = json.loads((DATA / "gates.json").read_text())
    platforms_cfg = json.loads((DATA / "platforms.json").read_text())

    frames: dict[tuple[str, str, str], list[dict]] = {}
    with (DATA / "frames.csv").open() as f:
        for r in csv.DictReader(f):
            frames.setdefault((r["platform"], r["content"], r["variant"]), []).append(r)
    if sum(len(v) for v in frames.values()) != 3600 or len(frames) != 40:
        raise SystemExit("frames.csv: expected 40 groups and 3600 rows")

    series: dict = {}
    pooled: dict = {}
    for p in PLATFORMS:
        series[p] = {}
        pooled[p] = {}
        for arm in ARMS:
            pool = {k: [] for k in FRAME_KEYS}
            for c in CONTENTS:
                rows = sorted(frames[(p, c, arm)], key=lambda r: int(r["frame"]))
                if [int(r["frame"]) for r in rows] != list(range(90)):
                    raise SystemExit(f"frames.csv: {p}/{c}/{arm} is not frames 0..89")
                series[p].setdefault(c, {})[arm] = {
                    k: [round(float(r[k]), 3) for r in rows] for k in FRAME_KEYS
                }
                for k in FRAME_KEYS:
                    pool[k].extend(float(r[k]) for r in rows)
            pooled[p][arm] = {k: stats(v) for k, v in pool.items()}
            for k in FRAME_KEYS:
                for s in ("mean", "p5"):
                    a, b = pooled[p][arm][k][s], summary[p][arm][k][s]
                    if abs(a - b) > 1e-6:
                        raise SystemExit(f"{p}/{arm}/{k}/{s}: frames give {a}, summary says {b}")

    def main_row(p: str, c: str, arm: str) -> dict:
        m = [r for r in results if r["platform"] == p and r["content"] == c and r["variant"] == arm and r["multiplier"] == 1]
        if len(m) != 1:
            raise SystemExit(f"results: need exactly one {p}/{c}/{arm}, got {len(m)}")
        return m[0]

    platforms = []
    for p in PLATFORMS:
        clips = []
        for c in CONTENTS:
            n, o = main_row(p, c, "naive"), main_row(p, c, "fast")
            if n["metrics"]["frames"] != 90 or o["metrics"]["frames"] != 90:
                raise SystemExit(f"results: {p}/{c} frame count is not 90")
            clips.append(
                {
                    "content": c,
                    "naive_upload_bytes": n["upload_bytes"],
                    "ours_upload_bytes": o["upload_bytes"],
                    "naive_playback_bytes": n["playback_bytes"],
                    "ours_playback_bytes": o["playback_bytes"],
                    "duration_s": n["duration"],
                }
            )
        nrow, orow = main_row(p, "ui", "naive"), main_row(p, "ui", "fast")
        keep = ["width", "height", "fps", "encoder", "quality", "scale", "prefilter", "gop_seconds", "maxrate_kbps", "bufsize_kbits", "audio_kbps"]
        platforms.append(
            {
                "id": p,
                "summary": {arm: {k: summary[p][arm][k] for k in FRAME_KEYS} for arm in ARMS},
                "gain": {k: summary[p]["gain"][k] for k in FRAME_KEYS},
                "upload_ratio": sum(c["ours_upload_bytes"] for c in clips) / sum(c["naive_upload_bytes"] for c in clips),
                "clips": clips,
                "naive_profile": {k: nrow["profile"].get(k) for k in keep},
                "ours_profile": {k: orow["profile"].get(k) for k in keep},
                "simulator": {k: platforms_cfg["platforms"][p][k] for k in ("width", "height", "fps", "codec", "crf", "bitrate_kbps", "gop_seconds")},
            }
        )

    grad = [
        {
            "platform": r["platform"],
            "variant": r["variant"],
            "encoder": r["profile"]["encoder"],
            "quality": r["profile"]["quality"],
            "vmaf": r["metrics"]["vmaf"],
            "cambi": r["metrics"]["cambi"],
            "frames": r["metrics"]["frames"],
            "source": r["source"],
        }
        for r in gradient
    ]

    gate_rows = [
        {
            "command": " ".join("python" if a.endswith("/python") else a for a in g["command"]),
            "returncode": g["returncode"],
            "output": g["output"].strip(),
        }
        for g in gates["gates"]
    ]

    report = (DATA / "REPORT.md").read_text()
    m = re.search(r"VMAF (v[\d.]+), VMAF NEG (v[\d.]+neg)", report)
    if not m:
        raise SystemExit("REPORT.md: metric model versions not found")

    doc = {
        "source": {"repo": REPO, "commit": COMMIT, "study": "fframes-delivery-v0"},
        "metric_versions": {"vmaf": m.group(1), "vmaf_neg": m.group(2)},
        "platforms": platforms,
        "contents": CONTENTS,
        "frames_per_clip": 90,
        "series": series,
        "gradient10": grad,
        "gates": {"gates": gate_rows, "static_scan_findings": gates["static_scan_findings"], "review": gates["review"]},
    }
    text = json.dumps(doc, separators=(",", ":"))
    for needle in FORBIDDEN + ["<local>"]:
        if needle in text:
            raise SystemExit(f"site data contains {needle!r}")
    SITE_OUT.write_text(text + "\n")
    print(f"wrote {SITE_OUT.relative_to(ROOT)} ({len(text)} bytes)")
    for p in platforms:
        g = p["gain"]["vmaf"]
        print(f"  {p['id']:8s} vmaf gain mean {g['mean']:.3f} p5 {g['p5']:.3f}  upload x{p['upload_ratio']:.2f}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    fz = sub.add_parser("freeze")
    fz.add_argument("--clone", type=Path, required=True)
    sub.add_parser("site")
    args = ap.parse_args()
    if args.cmd == "freeze":
        freeze(args.clone)
    else:
        site()


if __name__ == "__main__":
    sys.exit(main())
