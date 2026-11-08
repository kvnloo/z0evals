#!/usr/bin/env python3
"""Derive web/data/quackles-lineage-v0.json from the frozen Quackles study files.

The page reads only this file. Every count it prints is computed here from
studies/quackles-lineage-v0/data, and the script fails if the frozen files
disagree with each other (dataset hash, entry counts, sprite keys).
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "studies" / "quackles-lineage-v0" / "data"
OUT = ROOT / "web" / "data" / "quackles-lineage-v0.json"
MEDIA = "/media/quackles-lineage-v0"


def load(name: str):
    return json.loads((DATA / name).read_text())


def ms(iso: str) -> int:
    return int(datetime.fromisoformat(iso).timestamp() * 1000)


def main() -> None:
    history = load("history-v1.json")
    timeline = load("timeline.json")
    atlas = load("atlas.json")
    crops = load("crop-metrics.json")["rows"]
    picks = load("review-picks.json")
    trials = load("overnight-trials.json")
    zoom = load("fidelity-zoom.json")
    ui = load("timeline-ui.json")

    if atlas["datasetSha256"] != timeline["datasetSha256"]:
        raise SystemExit("atlas and timeline were built from different datasets")

    themes: list[str] = timeline["themes"]
    entries = history["entries"]
    counts = Counter(e["theme"] for e in entries)
    if dict(counts) != history["counts"]:
        raise SystemExit(f"history counts disagree: {dict(counts)} vs {history['counts']}")
    if len(entries) != len(timeline["times"]):
        raise SystemExit("timeline and history disagree on version count")

    sprites = {s["key"]: s for s in atlas["sprites"]}
    statuses = sorted({e["status"] for e in entries})
    phases = sorted({e["phase"] for e in entries})
    rows = []
    for e in entries:
        s = sprites[f"{e['theme']}/{e['version']}"]
        rows.append([
            themes.index(e["theme"]),
            ms(e["date"]),
            statuses.index(e["status"]),
            phases.index(e["phase"]),
            e["caption"].split(" · ", 1)[-1],
            s["page"],
            [round(x, 6) for x in s["uv"]],
            0 if e["dateSource"].startswith("file mtime") else 1,
        ])
    times = [r[1] for r in rows]
    if times != sorted(times):
        raise SystemExit("entries are not in time order")

    def plate(e: dict) -> dict:
        f, w, h, _ = e["thumbs"]["medium"]
        return {"src": f"{MEDIA}/plates/{f}", "w": w, "h": h, "caption": e["caption"], "date": e.get("date")}

    trial_counts: Counter[str] = Counter()
    for t in trials["trials"]:
        trial_counts[t["outcome"]] += t.get("count", 1)

    zoom_regions = []
    for r in crops:
        zoom_regions.append({
            "theme": r["theme"], "scale": r["family"], "feature": r["feature"],
            "full": r["full_resolution"], "bounds": r["bounds_top_left"],
            "seconds": round(r["seconds"], 2), "w": r["width"], "h": r["height"],
            "lap": r["laplacian_variance"], "grad": r["gradient_energy"], "blur1": r["blur1_gradient_energy"],
            "src": f"{MEDIA}/zoom/{r['theme']}-{r['family']}-{r['feature']}.webp",
        })
    for z in zoom_regions:
        if not (ROOT / "web" / "public" / z["src"].lstrip("/")).exists():
            raise SystemExit(f"missing zoom crop {z['src']}")

    out = {
        "snapshot": history["snapshot"],
        "datasetSha256": timeline["datasetSha256"],
        "themes": themes,
        "statuses": statuses,
        "phases": phases,
        "counts": history["counts"],
        "statusCounts": dict(Counter(e["status"] for e in entries)),
        "mtimeDated": sum(1 for e in entries if e["dateSource"].startswith("file mtime")),
        "atlasPages": [f"{MEDIA}/atlas/{p['file']}" for p in atlas["pages"]],
        "entries": rows,
        "milestones": timeline["milestones"],
        "current": {t: plate(e) for t, e in history["current"].items()},
        "references": {t: plate(e) for t, e in history["references"].items()},
        "picks": picks["picks"],
        "protocol": trials["protocol"],
        "trials": trials["trials"],
        "trialCounts": dict(trial_counts),
        "trialTotal": sum(trial_counts.values()),
        "zoom": {k: v for k, v in zoom.items() if k != "source"},
        "zoomRegions": zoom_regions,
        "ui": {k: v for k, v in ui.items() if k != "source"},
    }
    OUT.write_text(json.dumps(out, separators=(",", ":")))
    print(f"wrote {OUT.relative_to(ROOT)}: {len(rows)} versions, {out['trialTotal']} overnight decisions, "
          f"{len(zoom_regions)} zoom crops")


if __name__ == "__main__":
    main()
