#!/usr/bin/env python3
"""Build a minimal static research site from z0eval posts and study manifests."""
from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

import markdown
import yaml


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site"


STYLE = """
:root{--paper:#fbfaf5;--ink:#171813;--muted:#6f7068;--line:#d9d5c9;--orange:#e4572e;--green:#446b48;--blue:#315f82}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font-family:Arial,Helvetica,sans-serif;line-height:1.58}
nav{height:68px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 34px;position:sticky;top:0;background:rgba(251,250,245,.94);backdrop-filter:blur(10px);z-index:20}nav a{color:var(--ink);text-decoration:none;font-weight:800}nav span,.meta{font:11px ui-monospace,Menlo,monospace;color:var(--muted)}
.layout{max-width:1240px;margin:auto;display:grid;grid-template-columns:190px minmax(0,820px) 170px;gap:34px;padding:64px 28px 120px}.toc,.side-note{position:sticky;top:104px;align-self:start;font:11px ui-monospace,Menlo,monospace;color:var(--muted)}.toc b,.side-note strong{display:block;color:var(--ink);margin-bottom:12px}.toc a{display:block;color:var(--muted);text-decoration:none;padding:6px 0 6px 12px;border-left:1px solid var(--line)}.toc a:hover{color:var(--orange);border-color:var(--orange)}.side-note{border-top:2px solid var(--ink);padding-top:10px;font-size:12px}
.kicker,.eyebrow{font:700 11px ui-monospace,Menlo,monospace;text-transform:uppercase;letter-spacing:.11em;color:var(--orange)}h1{font:500 clamp(3.7rem,7.6vw,7.3rem)/.87 Georgia,serif;letter-spacing:-.065em;margin:14px 0 24px}h2{font:500 2.65rem/1.04 Georgia,serif;letter-spacing:-.04em;margin:3.1em 0 .55em;scroll-margin-top:100px}h3{margin:0 0 8px}.subtitle{font:1.45rem/1.35 Georgia,serif;color:#4e504a;max-width:680px}.meta{margin:28px 0 44px}.lede{font:1.38rem/1.5 Georgia,serif;margin:42px 0}.hero-rule{height:1px;background:var(--ink);margin:42px 0}
.mock-banner{border:1px solid #d88969;background:#fff2e9;padding:16px 18px;margin-bottom:34px;display:flex;gap:18px;font-size:.9rem}.mock-banner strong{font:800 11px ui-monospace,Menlo,monospace;white-space:nowrap;color:#a83c19}.mock-banner span{color:#713f2e}
.metric-grid{display:grid;grid-template-columns:repeat(3,1fr);border-block:1px solid var(--ink);margin:34px 0 54px}.metric{padding:20px 16px;border-right:1px solid var(--line)}.metric:last-child{border:0}.metric strong{display:block;font:400 2.7rem Georgia,serif}.metric-label,.metric small{font:10px ui-monospace,Menlo,monospace;color:var(--muted);display:block}
.figure-card{background:#f1eee5;border:1px solid #d5d0c3;padding:24px;margin:38px -36px 54px}.figure-card.wide{margin-inline:-70px}.figure-head{display:flex;justify-content:space-between;gap:20px;border-bottom:1px solid #cfcabd;padding-bottom:14px}.figure-head h3{font:500 1.55rem Georgia,serif}.figure-copy{font-size:.9rem;color:var(--muted)}.mock-chip{font:10px ui-monospace,Menlo,monospace;text-transform:uppercase;border:1px solid #d88969;color:#a83c19;background:#fff2e9;padding:5px 8px;height:max-content}.figure-foot{font:10px ui-monospace,Menlo,monospace;color:var(--muted);border-top:1px solid #cfcabd;padding-top:10px;margin-top:16px}
.control-row{display:flex;gap:14px;align-items:center;margin:22px 0;font:11px ui-monospace,Menlo,monospace}.control-row label{display:flex;gap:12px;align-items:center;flex:1}.control-row input{width:100%}.route-bars{display:grid;gap:8px}.route-row{display:grid;grid-template-columns:145px 1fr 42px;gap:12px;align-items:center;font:11px ui-monospace,Menlo,monospace}.bar-track{height:23px;background:#e3dfd4}.bar-fill{height:100%;background:var(--blue);transition:width .25s}.route-row:nth-child(2) .bar-fill{background:var(--orange)}.route-row:nth-child(3) .bar-fill{background:var(--green)}
.tabs{display:flex;gap:6px;margin:18px 0}.tab{border:1px solid #bbb6aa;background:transparent;padding:7px 12px;font:11px ui-monospace,Menlo,monospace;cursor:pointer}.tab.active{background:var(--ink);color:var(--paper)}.scatter{height:320px;position:relative;border-left:1px solid #9f9b90;border-bottom:1px solid #9f9b90;margin:32px 28px}.point{position:absolute;width:15px;height:15px;border-radius:50%;background:var(--orange);transform:translate(-50%,50%)}.point:after{content:attr(data-label);position:absolute;left:12px;top:-14px;white-space:nowrap;font:10px ui-monospace,Menlo,monospace}.point.best{background:var(--green);box-shadow:0 0 0 5px #446b4820}
.pullquote{font:2rem/1.18 Georgia,serif;margin:54px 0;padding:24px 0;border-block:1px solid var(--ink)}.compare-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:36px 0}.compare{padding:24px;border:1px solid var(--line);background:#f4f1e8}.compare strong{font:400 4rem Georgia,serif;display:block}.compare span:last-child{font:11px ui-monospace,Menlo,monospace;color:var(--muted)}.compare.bad strong{color:#a83c19}.compare.good strong{color:var(--green)}
.trace{border:1px solid var(--ink);margin:34px 0 54px}.trace-head{display:flex;justify-content:space-between;padding:10px 14px;background:var(--ink);color:white;font:11px ui-monospace,Menlo,monospace}.trace-head button{font:inherit;background:white;border:0;padding:4px 9px}.trace-step{display:grid;grid-template-columns:38px 1fr 1fr;padding:13px 14px;border-top:1px solid var(--line);font:11px ui-monospace,Menlo,monospace;transition:.25s}.trace-step em{color:var(--muted);font-style:normal}.trace.replaying .trace-step{opacity:.18}.trace.replaying .trace-step.on{opacity:1;background:#fff8df}
.latency-plot{height:250px;position:relative;margin:28px 12px;background:repeating-linear-gradient(to top,transparent 0,transparent 49px,#d8d4c8 50px)}.latency-line{position:absolute;left:0;right:0;height:2px}.latency-line span{position:absolute;width:9px;height:9px;border-radius:50%;top:-4px}.legend-row{display:flex;gap:18px;font:10px ui-monospace,Menlo,monospace}.dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:5px}.d1{background:var(--green)}.d2{background:var(--orange)}.d3{background:var(--blue)}
.pipeline{display:flex;gap:8px;margin:38px -30px 48px}.pipeline div{flex:1;border-top:2px solid var(--ink);padding:10px 4px}.pipeline b{display:block;font-family:Georgia,serif}.pipeline span{font:9px ui-monospace,Menlo,monospace;color:var(--muted)}.pipeline i{align-self:center;font-style:normal;color:var(--muted)}.method-card{background:var(--ink);color:#f6f2e8;padding:28px;margin:50px 0}.method-card .eyebrow{color:#ef9a75}.method-card h3{font:400 2rem Georgia,serif}.method-card p{color:#cbc8c0}.method-card a{color:white}
article a{color:var(--orange)}pre{overflow:auto;background:#171813;color:#f5f2e9;padding:18px}code{font-family:ui-monospace,Menlo,monospace}:not(pre)>code{background:#ece8de;padding:.12em .32em}footer{border-top:1px solid var(--line);padding:28px;text-align:center;font:10px ui-monospace,Menlo,monospace;color:var(--muted)}
.home{max-width:1040px;margin:auto;padding:90px 28px}.home h1{max-width:900px}.card{border-top:1px solid var(--ink);padding:22px 0}.card h2{font:2rem Georgia,serif;margin:5px 0}.card a{text-decoration:none;color:var(--ink)}.badge{font:10px ui-monospace,Menlo,monospace;color:var(--muted)}
@media(max-width:1000px){.layout{grid-template-columns:1fr;max-width:850px}.toc,.side-note{display:none}.figure-card,.figure-card.wide{margin-inline:0}}@media(max-width:650px){nav{padding-inline:18px}.layout{padding:36px 18px 80px}h1{font-size:3.7rem}.metric-grid,.compare-grid{grid-template-columns:1fr}.pipeline{display:grid;grid-template-columns:1fr;margin-inline:0}.pipeline i{display:none}}
"""


def split_frontmatter(text: str):
    if not text.startswith("---\n"):
        return {}, text
    _, fm, body = text.split("---", 2)
    return yaml.safe_load(fm) or {}, body.lstrip()


def page(title: str, body: str, subtitle: str = "", meta: str = "", fm: dict | None = None) -> str:
    fm = fm or {}
    toc_items = fm.get("toc", []) or []
    toc = "".join(
        f'<a href="#{html.escape(str(item.get("id", "")))}">{html.escape(str(item.get("label", "")))}</a>'
        for item in toc_items
    )
    author = html.escape(str(fm.get("author", "Zer0 Research")))
    date = html.escape(str(fm.get("date", "")))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · z0evals</title><style>{STYLE}</style></head>
<body><nav><a href="../index.html">z0evals</a><span>research · systems · agents</span></nav>
<div class="layout">
<aside class="toc"><b>Contents</b>{toc}</aside>
<main><div class="kicker">Zer0 evaluation report</div><h1>{html.escape(title)}</h1>
{f'<div class="subtitle">{html.escape(subtitle)}</div>' if subtitle else ''}
<div class="meta">{author} · {date}<br>{meta}</div>
<article>{body}</article></main>
<aside class="side-note"><strong>BUILD STATUS</strong>UI reference implementation.<br><br>Interactive numbers are clearly marked mock until frozen eval artifacts land.</aside>
</div>
<footer>z0evals · evidence before promotion · public reproducible evaluation</footer>
<script src="../research-ui.js"></script>
</body></html>"""


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "posts").mkdir(parents=True)

    cards = []
    for src in sorted((ROOT / "posts").glob("*.md")):
        raw = src.read_text(encoding="utf-8")
        fm, body_md = split_frontmatter(raw)
        title = fm.get("title", src.stem)
        subtitle = fm.get("subtitle", "")
        study = fm.get("study", "")
        status = fm.get("status", "draft")
        study_meta = ""
        manifest = ROOT / "studies" / study / "manifest.yaml"
        if study and manifest.exists():
            m = yaml.safe_load(manifest.read_text()) or {}
            study_meta = f"study={html.escape(study)} · status={html.escape(str(m.get('status', status)))} · updated={html.escape(str(m.get('updated','')))}"
        else:
            study_meta = f"status={html.escape(str(status))}"

        body = markdown.markdown(body_md, extensions=["fenced_code", "tables", "sane_lists"])
        dest = OUT / "posts" / f"{src.stem}.html"
        dest.write_text(page(title, body, subtitle, study_meta, fm), encoding="utf-8")
        cards.append(f"""<div class="card"><div class="kicker">{html.escape(str(status))}</div>
<h2><a href="posts/{src.stem}.html">{html.escape(title)}</a></h2>
<p>{html.escape(subtitle)}</p>
<span class="badge">{html.escape(study)}</span></div>""")

    index = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>z0evals</title><style>{STYLE}</style></head>
<body><nav><a href="index.html">z0evals</a><span>evidence before promotion</span></nav>
<main class="home"><div class="kicker">Zer0 research</div><h1>Measure what the agents actually do.</h1>
<p class="subtitle">Frozen evaluations, reproducible artifacts, and public research reports for the Zer0 stack.</p>
<div class="meta">experiment → measurement → frozen evidence → publication → promotion</div>
{''.join(cards) if cards else '<p>No reports yet.</p>'}
</main><footer>kvnloo/z0evals · public reproducible evaluation layer</footer></body></html>"""
    (OUT / "index.html").write_text(index, encoding="utf-8")
    print(f"built {len(cards)} post(s) into {OUT}")


if __name__ == "__main__":
    main()
