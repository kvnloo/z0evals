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
:root{--bg:#fbfaf6;--ink:#1d1f23;--muted:#6b6f76;--line:#e6e1d7;--accent:#574ce3;--card:#fff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.62}
main{max-width:860px;margin:0 auto;padding:72px 24px 120px}
nav{max-width:1100px;margin:0 auto;padding:20px 24px;display:flex;justify-content:space-between;border-bottom:1px solid var(--line)}
nav a{color:var(--ink);text-decoration:none;font-weight:650}
.kicker{font-size:.78rem;text-transform:uppercase;letter-spacing:.12em;color:var(--accent);font-weight:700}
h1{font-size:clamp(2.5rem,6vw,5.8rem);line-height:.96;letter-spacing:-.055em;margin:.3em 0}
h2{font-size:2rem;letter-spacing:-.03em;margin-top:2.4em}
h3{font-size:1.35rem;margin-top:2em}
p,li{font-size:1.08rem}
a{color:var(--accent)}
.subtitle{font-size:1.35rem;color:var(--muted);max-width:700px}
.meta{margin:28px 0 48px;padding:14px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);color:var(--muted);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.86rem}
article img{max-width:100%}
pre{overflow:auto;background:#15161a;color:#f5f2ea;padding:18px;border-radius:12px}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
:not(pre)>code{background:#efede7;padding:.12em .35em;border-radius:5px}
blockquote{border-left:3px solid var(--accent);margin:2em 0;padding:.2em 0 .2em 1.3em;color:#4b4f56}
.card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:24px;margin:18px 0}
.card h2{margin-top:0;font-size:1.5rem}
.card a{text-decoration:none}
.badge{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:3px 9px;font-size:.76rem;color:var(--muted);margin-left:8px}
footer{max-width:860px;margin:0 auto;padding:0 24px 48px;color:var(--muted);font-size:.84rem}
"""


def split_frontmatter(text: str):
    if not text.startswith("---\n"):
        return {}, text
    _, fm, body = text.split("---", 2)
    return yaml.safe_load(fm) or {}, body.lstrip()


def page(title: str, body: str, subtitle: str = "", meta: str = "") -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · z0evals</title><style>{STYLE}</style></head>
<body><nav><a href="../index.html">z0evals</a><span>reproducible evaluation</span></nav>
<main><div class="kicker">Zer0 evaluation report</div><h1>{html.escape(title)}</h1>
{f'<div class="subtitle">{html.escape(subtitle)}</div>' if subtitle else ''}
{f'<div class="meta">{meta}</div>' if meta else ''}
<article>{body}</article></main>
<footer>Evidence should resolve to a frozen study artifact. Source-reported results and reproduced measurements are kept separate.</footer>
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
        dest.write_text(page(title, body, subtitle, study_meta), encoding="utf-8")
        cards.append(f"""<div class="card"><div class="kicker">{html.escape(str(status))}</div>
<h2><a href="posts/{src.stem}.html">{html.escape(title)}</a></h2>
<p>{html.escape(subtitle)}</p>
<span class="badge">{html.escape(study)}</span></div>""")

    index = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>z0evals</title><style>{STYLE}</style></head>
<body><nav><a href="index.html">z0evals</a><span>evidence before promotion</span></nav>
<main><div class="kicker">Zer0 research</div><h1>Measure what the agents actually do.</h1>
<p class="subtitle">Frozen evaluations, reproducible artifacts, and public research reports for the Zer0 stack.</p>
<div class="meta">experiment → measurement → frozen evidence → publication → promotion</div>
{''.join(cards) if cards else '<p>No reports yet.</p>'}
</main><footer>kvnloo/z0evals · public reproducible evaluation layer</footer></body></html>"""
    (OUT / "index.html").write_text(index, encoding="utf-8")
    print(f"built {len(cards)} post(s) into {OUT}")


if __name__ == "__main__":
    main()
