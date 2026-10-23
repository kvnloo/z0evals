#!/usr/bin/env python3
"""Prerender posts/*.md and the research-log focus note for the Next site.

Writes web/data/posts/<slug>.json ({slug, title, subtitle, study, status, author, date,
toc, lede, html}) and web/data/research-focus.html. The site renders these files; it
does not parse markdown itself. Nothing is invented: every field comes from the post.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "posts"
OUT = ROOT / "web" / "data" / "posts"
FOCUS_MD = ROOT / "web" / "data" / "research-focus.md"
FOCUS_HTML = ROOT / "web" / "data" / "research-focus.html"

HEADING_ID = re.compile(r"^(#{1,6})\s+(.*?)\s*\{#([A-Za-z0-9_-]+)\}\s*$", re.M)
LEDE = re.compile(r'<div class="lede">\s*(.*?)\s*</div>', re.S)


def render(md: str) -> str:
    md = HEADING_ID.sub(lambda m: f"{m.group(1)} {m.group(2)} {{: #{m.group(3)} }}", md)
    html = markdown.markdown(md, extensions=["attr_list", "tables", "fenced_code", "md_in_html", "sane_lists"])
    # wide tables scroll inside their own box on phones instead of crushing their columns
    return re.sub(r"<table>(.*?)</table>", r'<div class="table-wrap"><table>\1</table></div>', html, flags=re.S)


def split(src: str) -> tuple[dict, str]:
    m = re.match(r"^---\n(.*?)\n---\n?", src, re.S)
    if not m:
        return {}, src
    return yaml.safe_load(m.group(1)) or {}, src[m.end():]


def build_post(path: Path) -> dict:
    meta, body = split(path.read_text(encoding="utf-8"))
    html = render(body)
    lede = ""
    m = LEDE.search(html)
    if m:
        # the lede is raw HTML in the source, so render any markdown inside it before stripping tags
        lede = re.sub(r"<[^>]+>", "", markdown.markdown(m.group(1))).strip()
        html = html.replace(m.group(0), "", 1)
    slug = path.stem
    return {
        "slug": slug,
        "title": str(meta.get("title", slug)),
        "subtitle": str(meta.get("subtitle", "")),
        "study": str(meta.get("study", slug)),
        "status": str(meta.get("status", "draft")),
        "author": str(meta.get("author", "zer0 research")),
        "date": str(meta.get("date", "")),
        "toc": [{"id": str(t["id"]), "label": str(t.get("label", t["id"]))} for t in (meta.get("toc") or [])],
        "lede": lede,
        "html": html,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.json"):
        old.unlink()
    n = 0
    for path in sorted(POSTS.glob("*.md")):
        (OUT / f"{path.stem}.json").write_text(json.dumps(build_post(path), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        n += 1
    if FOCUS_MD.exists():
        FOCUS_HTML.write_text(render(FOCUS_MD.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"ok: prerendered {n} post(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
