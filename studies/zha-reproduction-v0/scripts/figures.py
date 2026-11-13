"""Derive every number and chart in the post from data/*.json; splice SVGs into the post.

  python figures.py           # write data/derived.json and splice <!-- figure:NAME --> blocks in the post
  python figures.py --check   # fail if derived.json or any spliced figure would change
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POST = ROOT.parents[1] / "posts" / "zha-reproduction-v0.md"
MODEL_ORDER = ["qwen3-0.6b", "qwen3.5-0.8b", "qwen2.5-1.5b", "qwen3-1.7b"]
LABEL = {"qwen3-0.6b": "Qwen3-0.6B", "qwen3.5-0.8b": "Qwen3.5-0.8B", "qwen2.5-1.5b": "Qwen2.5-1.5B", "qwen3-1.7b": "Qwen3-1.7B"}
ARMS = [("dense", "dense", "#8a8a8a"), ("wide-c256l1@0.95", "wide p=.95", "#4c9be8"),
        ("deep-c4l6@0.95", "deep p=.95", "#e8a33c"), ("deep-c4l6@0.8", "deep p=.8", "#d4553b")]


def load(name):
    return json.loads((ROOT / "data" / name).read_text())


def derive():
    ruler, training, scaling = load("ruler.json"), load("training.json"), load("scaling.json")
    mc = load("mc.json") if (ROOT / "data/mc.json").exists() else []
    models = [m for m in MODEL_ORDER if any(r["model"] == m for r in ruler)]
    cells = {(r["model"], r["length"], r["arm"]): r for r in ruler}
    table = []
    for m in models:
        for length in (4096, 8192):
            row = {"model": m, "length": length}
            for arm, _, _ in ARMS:
                c = cells.get((m, length, arm))
                if c:
                    row[arm] = {"score": round(c["ruler_score"], 1), "key_share": round(100 * c["key_share"], 1),
                                "diff": round(c["paired_diff_vs_dense"], 1),
                                "ci": [round(x, 1) for x in c["paired_diff_ci95"]], "n": c["n_examples"],
                                "complete": c["complete"]}
            table.append(row)
    train = [{"model": t["model"], "geometry": t["geometry"], "tokens": t["tokens"], "minutes": round(t["minutes"], 1),
              "kl_first": round(t["kl_first"], 3), "kl_final": round(t["kl_final"], 3),
              "kl_levels": {k: round(v, 3) for k, v in t["kl_final_levels"].items()}} for t in training]
    expo = [{"model": s["model"], "p": s["p"], "exponent": round(s["exponent_1k_plus"], 2), "range": s["fit_range"]}
            for s in scaling]
    mcs = [{"model": x["model"], "arm": x["arm"], "n": x["n"], "accuracy": round(x["accuracy"], 1),
            "diff": round(x["paired_diff_vs_dense"], 1), "ci": [round(v, 1) for v in x["paired_diff_ci95"]],
            "key_share": round(100 * x["key_share"], 1), "unparsed": x["unparsed"]} for x in mc]
    return {"models": models, "ruler": table, "training": train, "scaling": expo, "mc": mcs}


def svg_ruler(d, length=8192):
    rows = [r for r in d["ruler"] if r["length"] == length]
    w, top, gh, bw = 420, 34, 64, 13
    h = top + gh * len(rows) + 30
    out = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="RULER-13 at {length // 1024}K by model and attention">']
    for i, (_, lab, col) in enumerate(ARMS):
        out.append(f'<rect x="{8 + i * 102}" y="6" width="10" height="10" fill="{col}"/>'
                   f'<text x="{22 + i * 102}" y="15" font-size="11" fill="#9a9a9a">{lab}</text>')
    x0, x1 = 104, 384
    for gi, r in enumerate(rows):
        y = top + gi * gh
        out.append(f'<text x="4" y="{y + 30}" font-size="12" fill="#cfcfcf">{LABEL[r["model"]]}</text>')
        for ai, (arm, _, col) in enumerate(ARMS):
            c = r.get(arm)
            if not c:
                continue
            yy = y + ai * bw
            ww = (x1 - x0) * c["score"] / 100
            out.append(f'<rect x="{x0}" y="{yy}" width="{ww:.1f}" height="{bw - 2}" fill="{col}"/>')
            ks = "" if arm == "dense" else f' · {c["key_share"]:.0f}% keys'
            out.append(f'<text x="{x0 + ww + 4:.1f}" y="{yy + 10}" font-size="11" fill="#bdbdbd">{c["score"]:.1f}{ks}</text>')
    for v in (0, 50, 100):
        x = x0 + (x1 - x0) * v / 100
        out.append(f'<line x1="{x:.1f}" y1="{top - 4}" x2="{x:.1f}" y2="{h - 22}" stroke="#3a3a3a" stroke-width="1"/>'
                   f'<text x="{x:.1f}" y="{h - 8}" font-size="11" fill="#8a8a8a" text-anchor="middle">{v}</text>')
    out.append("</svg>")
    return "\n".join(out)


def svg_scaling(d):
    pts = [s for s in d["scaling"] if s["p"] == 0.9]
    w, h = 420, 40 + 26 * len(pts)
    out = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="dense top-p=.9 set growth exponent by model">']
    x0, x1 = 120, 380
    for v in (0.0, 0.5, 1.0):
        x = x0 + (x1 - x0) * v
        out.append(f'<line x1="{x:.1f}" y1="8" x2="{x:.1f}" y2="{h - 22}" stroke="#3a3a3a"/>'
                   f'<text x="{x:.1f}" y="{h - 8}" font-size="11" fill="#8a8a8a" text-anchor="middle">{v:g}</text>')
    for i, s in enumerate(sorted(pts, key=lambda s: MODEL_ORDER.index(s["model"]))):
        y = 14 + i * 26
        ww = (x1 - x0) * s["exponent"]
        out.append(f'<text x="4" y="{y + 11}" font-size="12" fill="#cfcfcf">{LABEL[s["model"]]}</text>'
                   f'<rect x="{x0}" y="{y}" width="{ww:.1f}" height="14" fill="#4c9be8"/>'
                   f'<text x="{x0 + ww + 4:.1f}" y="{y + 11}" font-size="11" fill="#bdbdbd">{s["exponent"]:.2f}</text>')
    out.append("</svg>")
    return "\n".join(out)


def splice(text, name, svg, caption):
    block = f'<!-- figure:{name} -->\n<figure class="figure">\n{svg}\n<figcaption>{caption}</figcaption>\n</figure>\n<!-- /figure:{name} -->'
    pat = re.compile(rf"<!-- figure:{name} -->.*?<!-- /figure:{name} -->", re.S)
    assert pat.search(text), f"missing figure marker {name}"
    return pat.sub(lambda _: block, text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    d = derive()
    derived = json.dumps(d, indent=1) + "\n"
    post = POST.read_text()
    new = splice(post, "ruler", svg_ruler(d),
                 "RULER-13 mean task score at 8K tokens, 10 examples × 13 tasks per bar. Labels: score and mean share of "
                 "decode keys attended. Same prompts and dense prefill for every bar of a model.")
    new = splice(new, "scaling", svg_scaling(d),
                 "Log-log slope of the mean dense top-p=.9 set size against context (1K up to 16K–32K), three books, all "
                 "full-attention heads. 1.0 would be linear growth.")
    if a.check:
        assert (ROOT / "data/derived.json").read_text() == derived, "derived.json drift"
        assert POST.read_text() == new, "post figure drift"
        print("ok: derived.json and post figures match data/")
        return
    (ROOT / "data/derived.json").write_text(derived)
    POST.write_text(new)
    print("wrote derived.json and spliced figures")


if __name__ == "__main__":
    main()
