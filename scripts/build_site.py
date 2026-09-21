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
:root{
  --bg:#ffffff;
  --ink:#111111;
  --muted:#6f6f6f;
  --faint:#a8a8a8;
  --line:#e7e7e7;
  --green:#2f6f5d;
  --green-soft:#eef5f1;
  --purple:#6b5aa6;
  --warning:#8e3f2d;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0;
  background:var(--bg);
  color:var(--ink);
  font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
  font-size:17px;
  line-height:1.62;
  -webkit-font-smoothing:antialiased;
  text-rendering:optimizeLegibility;
}
a{color:inherit;text-decoration-color:#b9b9b9;text-underline-offset:3px}
a:hover{text-decoration-color:var(--ink)}
.site-nav{
  max-width:1180px;
  margin:0 auto;
  padding:18px 28px 14px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:24px;
  font-size:14px;
}
.site-nav .brand{font-weight:700;text-decoration:none;letter-spacing:-.02em}
.site-nav .links{display:flex;gap:20px;align-items:center;white-space:nowrap}
.site-nav .links a{text-decoration:none;color:#333}
.site-nav .links a:hover{color:#000}
.page-shell{max-width:930px;margin:0 auto;padding:54px 28px 96px}
.post-header{margin-bottom:30px}
.post-header h1{
  margin:0 0 12px;
  max-width:900px;
  font-size:clamp(2.55rem,5vw,3.5rem);
  line-height:1.03;
  letter-spacing:-.045em;
  font-weight:760;
}
.subtitle{
  max-width:760px;
  margin:0 0 14px;
  font-size:1.14rem;
  line-height:1.45;
  color:#333;
}
.meta{
  margin:0;
  font-size:14px;
  line-height:1.45;
  color:var(--muted);
}
.toc{
  margin:26px 0 42px;
  padding:0 0 0 19px;
  columns:2;
  column-gap:42px;
  font-size:15px;
  line-height:1.55;
}
.toc li{break-inside:avoid;margin:0 0 5px}
.toc a{color:#333}
article{max-width:850px}
article p,article li{font-size:17px}
article p{margin:0 0 1.15em}
article ul,article ol{padding-left:1.35em}
h2{
  margin:2.5em 0 .65em;
  font-size:1.78rem;
  line-height:1.18;
  letter-spacing:-.025em;
  font-weight:720;
  scroll-margin-top:24px;
}
h3{
  margin:1.9em 0 .55em;
  font-size:1.2rem;
  line-height:1.3;
  font-weight:700;
}
hr,.hero-rule{border:0;border-top:1px solid var(--line);margin:34px 0}
.lede{font-size:1.04rem;line-height:1.62;margin:0 0 26px}
.evidence-banner,.mock-banner{
  margin:0 0 28px;
  padding:12px 14px;
  border:1px solid var(--line);
  background:#fafafa;
  font-size:13px;
  line-height:1.5;
}
.evidence-banner strong,.mock-banner strong{
  display:block;
  margin-bottom:3px;
  font-size:11px;
  letter-spacing:.08em;
  text-transform:uppercase;
}
.evidence-banner strong{color:var(--green)}
.mock-banner strong{color:var(--warning)}
.metric-grid{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:0;
  margin:24px 0 38px;
  border-top:1px solid var(--line);
  border-bottom:1px solid var(--line);
}
.metric{padding:14px 18px 15px 0}
.metric+.metric{padding-left:18px;border-left:1px solid var(--line)}
.metric strong{
  display:block;
  margin:1px 0 1px;
  font-size:1.7rem;
  line-height:1.1;
  letter-spacing:-.035em;
  font-weight:690;
}
.metric-label,.metric small{
  display:block;
  color:var(--muted);
  font-size:12px;
  line-height:1.4;
}
.eyebrow{
  display:block;
  color:var(--muted);
  font-size:12px;
  font-weight:650;
  letter-spacing:.01em;
}
.figure-card,.figure-card.wide{
  margin:32px 0 44px;
  padding:0;
  border:0;
  background:transparent;
}
.figure-head{
  display:flex;
  align-items:flex-start;
  justify-content:space-between;
  gap:20px;
  margin-bottom:7px;
}
.figure-head h3{
  margin:2px 0 0;
  font-size:1.08rem;
  font-weight:700;
  letter-spacing:-.01em;
}
.figure-copy,.figure-foot{
  color:var(--muted);
  font-size:13px;
  line-height:1.5;
}
.figure-copy{margin:0 0 15px}
.figure-foot{margin-top:12px}
.sb-chart{display:block;width:100%;height:auto;overflow:visible}
.sb-grid{stroke:#ececec;stroke-width:1}
.sb-line{fill:none;stroke:var(--green);stroke-width:1.8;vector-effect:non-scaling-stroke}
.sb-point{fill:#fff;stroke:var(--green);stroke-width:1.8;vector-effect:non-scaling-stroke}
.sb-point-dark{stroke:#222;fill:#222}
.sb-axis,.sb-axis-title,.sb-x,.sb-value{font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
.sb-axis{fill:#8a8a8a;font-size:10px}
.sb-axis-title{fill:#666;font-size:11px}
.sb-x{fill:#666;font-size:9px}
.sb-value{fill:#222;font-size:10px;font-weight:650}
.sb-chart-note{margin-top:-4px;color:var(--muted);font-size:12px;line-height:1.45}
.mock-chip,.result-chip{
  padding:2px 7px;
  border:1px solid var(--line);
  border-radius:999px;
  background:white;
  color:var(--muted);
  font-size:10px;
  line-height:1.5;
  text-transform:uppercase;
  letter-spacing:.06em;
  white-space:nowrap;
}
.result-chip{border-color:#b9d0c7;color:var(--green);background:var(--green-soft)}
.tabs{
  display:flex;
  gap:18px;
  margin:8px 0 16px;
  border-bottom:1px solid var(--line);
}
.tab{
  padding:6px 0 7px;
  border:0;
  border-bottom:2px solid transparent;
  background:none;
  color:var(--muted);
  font:inherit;
  font-size:13px;
  cursor:pointer;
}
.tab.active{color:var(--ink);border-bottom-color:var(--ink)}
.route-bars{display:grid;gap:8px;margin:12px 0}
.route-row{
  display:grid;
  grid-template-columns:165px minmax(80px,1fr) 74px;
  align-items:center;
  gap:12px;
  font-size:12px;
  color:#333;
}
.bar-track{height:8px;background:#eeeeec}
.bar-fill{height:100%;background:#8f8f8a;transition:width .2s ease}
.route-row.phase-primary .bar-fill{background:var(--green)}
.route-row.phase-warning .bar-fill{background:#111}
.route-row b{font-size:12px;font-weight:600;text-align:right}
.result-table{
  width:100%;
  margin:20px 0 38px;
  border-collapse:collapse;
  font-size:13px;
}
.result-table th{
  color:var(--muted);
  font-weight:600;
  border-bottom:1px solid #cfcfcf;
}
.result-table th,.result-table td{padding:7px 6px;text-align:right;vertical-align:top}
.result-table th:first-child,.result-table td:first-child{text-align:left;padding-left:0}
.result-table th:last-child,.result-table td:last-child{padding-right:0}
.result-table td{border-bottom:1px solid #eeeeee}
.result-table tr.primary{background:transparent}
.result-table tr.primary td:first-child{font-weight:700}
.result-table tr.warning{background:transparent}
.result-table tr.warning td:first-child{text-decoration:underline;text-decoration-style:dotted;text-underline-offset:3px}
.finding-grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:22px 32px;
  margin:26px 0 42px;
}
.finding{padding:0;border:0}
.finding strong{display:block;margin-bottom:4px;font-size:14px}
.finding span{display:block;color:var(--muted);font-size:13px;line-height:1.5}
.pullquote{
  margin:36px 0;
  padding:0;
  border:0;
  font-size:1.18rem;
  line-height:1.5;
  font-weight:600;
}
.compare-grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:28px;
  margin:26px 0 40px;
}
.compare{padding:0;border:0;background:transparent}
.compare .eyebrow{margin-bottom:4px}
.compare strong{
  display:block;
  font-size:2.1rem;
  line-height:1.1;
  letter-spacing:-.035em;
  font-weight:700;
}
.compare span:last-child{display:block;color:var(--muted);font-size:13px}
.compare.good strong{color:var(--green)}
.compare.bad strong{color:#222}
.pipeline{
  display:flex;
  gap:0;
  align-items:stretch;
  margin:28px 0 40px;
  border-top:1px solid var(--line);
  border-bottom:1px solid var(--line);
}
.pipeline div{flex:1;padding:12px 12px 13px 0}
.pipeline div+div{padding-left:12px;border-left:1px solid var(--line)}
.pipeline b{display:block;font-size:13px}
.pipeline span{display:block;color:var(--muted);font-size:11px;line-height:1.4}
.pipeline i{display:none}
.method-card{
  margin:42px 0 0;
  padding:18px 0 0;
  border-top:1px solid var(--line);
  background:transparent;
  color:var(--ink);
}
.method-card h3{margin:3px 0 6px;font-size:1.15rem}
.method-card p{color:#333;font-size:14px}
.method-card a{font-size:14px}
code{font-family:"SFMono-Regular",Consolas,"Liberation Mono",monospace;font-size:.9em}
:not(pre)>code{padding:.08em .28em;border-radius:3px;background:#f3f3f2}
pre{
  margin:20px 0 32px;
  padding:14px 16px;
  overflow:auto;
  border:1px solid var(--line);
  background:#fafafa;
  color:#222;
  font-size:13px;
  line-height:1.5;
}
footer{
  max-width:930px;
  margin:0 auto;
  padding:32px 28px 42px;
  border-top:1px solid var(--line);
  color:var(--muted);
  font-size:13px;
}
.home{max-width:930px;margin:0 auto;padding:72px 28px 100px}
.home h1{margin:0 0 18px;font-size:clamp(2.8rem,6vw,4.5rem);line-height:1.02;letter-spacing:-.05em}
.card{padding:19px 0;border-top:1px solid var(--line)}
.card h2{margin:2px 0 5px;font-size:1.25rem}
.card a{text-decoration:none}
.badge{font-size:12px;color:var(--muted)}
.kicker{font-size:12px;color:var(--muted);font-weight:650}
@media(max-width:760px){
  body{font-size:16px}
  .site-nav{padding:15px 18px 10px}
  .site-nav .links{gap:13px;font-size:13px}
  .page-shell{padding:38px 18px 74px}
  .post-header h1{font-size:2.65rem}
  .toc{columns:1;margin-bottom:34px}
  article p,article li{font-size:16px}
  h2{font-size:1.55rem}
  .metric-grid{grid-template-columns:1fr}
  .metric{padding:11px 0}
  .metric+.metric{padding-left:0;border-left:0;border-top:1px solid var(--line)}
  .finding-grid,.compare-grid{grid-template-columns:1fr}
  .route-row{grid-template-columns:112px 1fr 62px;gap:8px;font-size:11px}
  .result-table{display:block;overflow-x:auto;white-space:nowrap}
  .pipeline{display:grid;grid-template-columns:1fr}
  .pipeline div{padding:10px 0}
  .pipeline div+div{padding-left:0;border-left:0;border-top:1px solid var(--line)}
}
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
        f'<li><a href="#{html.escape(str(item.get("id", "")))}">{html.escape(str(item.get("label", "")))}</a></li>'
        for item in toc_items
    )
    author = html.escape(str(fm.get("author", "Zer0 Research")))
    date = html.escape(str(fm.get("date", "")))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · z0evals</title><style>{STYLE}</style></head>
<body>
<nav class="site-nav">
  <a class="brand" href="../index.html">z0evals</a>
  <div class="links"><a href="../index.html">Research</a><a href="eval-architecture.html">Architecture</a><a href="https://github.com/kvnloo/z0evals">GitHub</a></div>
</nav>
<main class="page-shell">
  <header class="post-header">
    <h1>{html.escape(title)}</h1>
    <p class="meta">{author}·{date}</p>
    {f'<ul class="toc">{toc}</ul>' if toc else ''}
  </header>
  <article>{body}</article>
</main>
<footer>z0evals · Writing · Architecture · GitHub</footer>
<script src="../research-ui.js"></script>
</body></html>"""


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "posts").mkdir(parents=True)
    (OUT / "data").mkdir(parents=True)

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

        body = markdown.markdown(body_md, extensions=["fenced_code", "tables", "sane_lists", "attr_list"])
        dest = OUT / "posts" / f"{src.stem}.html"
        dest.write_text(page(title, body, subtitle, study_meta, fm), encoding="utf-8")
        cards.append(f"""<div class="card"><div class="kicker">{html.escape(str(status))}</div>
<h2><a href="posts/{src.stem}.html">{html.escape(title)}</a></h2>
<p>{html.escape(subtitle)}</p>
<span class="badge">{html.escape(study)}</span></div>""")

    index = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>z0evals</title><style>{STYLE}</style></head>
<body><nav><a href="index.html">z0evals</a><span><a href="posts/eval-architecture.html">architecture</a> · evidence before promotion</span></nav>
<main class="home"><div class="kicker">Zer0 research</div><h1>Measure what the agents actually do.</h1>
<p class="subtitle">Frozen evaluations, reproducible artifacts, and public research reports for the Zer0 stack.</p>
<div class="meta">experiment → measurement → frozen evidence → publication → promotion</div>
{''.join(cards) if cards else '<p>No reports yet.</p>'}
</main><footer>kvnloo/z0evals · public reproducible evaluation layer</footer></body></html>"""
    (OUT / "index.html").write_text(index, encoding="utf-8")
    for study_dir in sorted((ROOT / "studies").iterdir()):
        data_dir = study_dir / "data"
        if data_dir.is_dir():
            shutil.copytree(data_dir, OUT / "data" / study_dir.name, dirs_exist_ok=True)
    shutil.copy2(ROOT / "research-ui.js", OUT / "research-ui.js")
    print(f"built {len(cards)} post(s) into {OUT}")


if __name__ == "__main__":
    main()
