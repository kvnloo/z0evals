#!/usr/bin/env python3
"""Prerender posts/*.md and the research-log focus note for the Next site.

Writes web/data/posts/<slug>.json ({slug, title, subtitle, study, status, author, date,
dek, area, tags, published, updated, kind, series, log, featured, toc, lede, html}),
web/data/posts/_index.json (the same records without html, for list pages) and
web/data/research-focus.html. The site renders these files; it does not parse markdown
itself. Nothing is invented: every field comes from the post.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "posts"
OUT = ROOT / "web" / "data" / "posts"
FOCUS_MD = ROOT / "web" / "data" / "research-focus.md"
FOCUS_HTML = ROOT / "web" / "data" / "research-focus.html"

# keep in step with web/lib/areas.ts
AREAS = ("governance", "speed-ux", "memory", "cost-routing", "research", "fleet")
KINDS = ("post", "study", "living", "architecture")
INDEX = "_index"


class PostError(ValueError):
    pass


def iso_date(value: object, field: str, slug: str) -> str:
    """Normalise a front-matter date to YYYY-MM-DD, or fail loudly."""
    if isinstance(value, dt.datetime):
        return value.date().isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    text = str(value).strip()
    try:
        return dt.date.fromisoformat(text).isoformat()
    except ValueError as exc:
        raise PostError(f"{slug}: {field} is not an ISO date: {text!r}") from exc


def published_from_date(label: str, slug: str) -> str:
    """Fallback when `published` is missing: parse the free-text `date:`."""
    text = re.sub(r"^\s*updated\s+", "", label.strip(), flags=re.I)
    try:
        return dt.datetime.strptime(text.lower(), "%B %d, %Y").date().isoformat()
    except ValueError as exc:
        raise PostError(f"{slug}: no `published` and `date` is not parseable: {label!r}") from exc


HEADING_ID = re.compile(r"^(#{1,6})\s+(.*?)\s*\{#([A-Za-z0-9_-]+)\}\s*$", re.M)
LEDE = re.compile(r'<div class="lede">\s*(.*?)\s*</div>', re.S)


def render(md: str) -> str:
    md = HEADING_ID.sub(lambda m: f"{m.group(1)} {m.group(2)} {{: #{m.group(3)} }}", md)
    html = markdown.markdown(md, extensions=["attr_list", "tables", "fenced_code", "md_in_html", "sane_lists"])
    # wide tables scroll inside their own box on phones instead of crushing their columns
    return re.sub(r"<table>(.*?)</table>", r'<div class="table-wrap"><table>\1</table></div>', html, flags=re.S)


BLOCK_TAG = re.compile(r"<(/?)(div|section|details|blockquote|figure|aside|table|ul|ol)\b[^>]*>", re.I)


def sectionize(html: str) -> str:
    """Wrap each top-level h2 run in <section class="post-sec"> so long posts can skip
    rendering off-screen sections (content-visibility). Nested h2s are left alone."""
    cuts, depth, pos = [], 0, 0
    for m in re.finditer(r"<h2\b|" + BLOCK_TAG.pattern, html, flags=re.I):
        if m.group(0).lower().startswith("<h2"):
            if depth == 0:
                cuts.append(m.start())
            continue
        depth += -1 if m.group(1) else 1
        depth = max(depth, 0)
    if not cuts:
        return html
    parts = [html[: cuts[0]]]
    for i, start in enumerate(cuts):
        end = cuts[i + 1] if i + 1 < len(cuts) else len(html)
        parts.append(f'<section class="post-sec">{html[start:end].rstrip()}</section>\n')
    return "".join(parts)


def split(src: str) -> tuple[dict, str]:
    m = re.match(r"^---\n(.*?)\n---\n?", src, re.S)
    if not m:
        return {}, src
    return yaml.safe_load(m.group(1)) or {}, src[m.end():]


GENERATED = ROOT / "web/data/generated"
BLOCK = re.compile(r"(<!-- generated:([a-z0-9-]+) -->\n)(.*?)(<!-- /generated:\2 -->)", re.S)


def splice_generated(body: str) -> str:
    """Replace a committed snapshot block with web/data/generated/<name>.md when it exists."""
    def swap(m: re.Match) -> str:
        fresh = GENERATED / f"{m.group(2)}.md"
        return m.group(1) + (fresh.read_text(encoding="utf-8") if fresh.is_file() else m.group(3)) + m.group(4)
    return BLOCK.sub(swap, body)


def build_post(path: Path) -> dict:
    meta, body = split(path.read_text(encoding="utf-8"))
    body = splice_generated(body)
    html = render(body)
    lede = ""
    m = LEDE.search(html)
    if m:
        # the lede is raw HTML in the source, so render any markdown inside it before stripping tags
        lede = re.sub(r"<[^>]+>", "", markdown.markdown(m.group(1))).strip()
        html = html.replace(m.group(0), "", 1)
    html = sectionize(html)
    slug = path.stem
    date_label = str(meta.get("date", ""))
    if meta.get("published"):
        published = iso_date(meta["published"], "published", slug)
    else:
        published = published_from_date(date_label, slug)
        print(f"warning: {slug}: no `published`; parsed {published} from date {date_label!r}", file=sys.stderr)
    area = str(meta.get("area", ""))
    if area not in AREAS:
        raise PostError(f"{slug}: area {area!r} is not one of {', '.join(AREAS)}")
    kind = str(meta.get("kind") or "post")
    if kind not in KINDS:
        raise PostError(f"{slug}: kind {kind!r} is not one of {', '.join(KINDS)}")
    tags = [str(t) for t in (meta.get("tags") or [])]
    if len(tags) > 4 or any(not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", t) for t in tags):
        raise PostError(f"{slug}: tags must be at most 4 lowercase kebab words")
    subtitle = str(meta.get("subtitle", ""))
    dek = str(meta.get("dek") or "").strip()
    if not dek:
        dek = subtitle if len(subtitle) <= 140 else subtitle[:139].rstrip() + "…"
    if len(dek) > 140:
        raise PostError(f"{slug}: dek is longer than 140 characters")
    return {
        "slug": slug,
        "title": str(meta.get("title", slug)),
        "subtitle": subtitle,
        "study": str(meta.get("study", slug)),
        "status": str(meta.get("status", "draft")),
        "author": str(meta.get("author", "zer0 research")),
        "date": date_label,
        "dek": dek,
        "area": area,
        "tags": tags,
        "published": published,
        "updated": iso_date(meta["updated"], "updated", slug) if meta.get("updated") else None,
        "kind": kind,
        "series": str(meta["series"]) if meta.get("series") else None,
        "log": [str(x) for x in (meta.get("log") or [])],
        "featured": bool(meta.get("featured", False)),
        "toc": [{"id": str(t["id"]), "label": str(t.get("label", t["id"]))} for t in (meta.get("toc") or [])],
        "lede": lede,
        "html": html,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.json"):
        old.unlink()
    index = []
    for path in sorted(POSTS.glob("*.md")):
        try:
            post = build_post(path)
        except PostError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        (OUT / f"{path.stem}.json").write_text(json.dumps(post, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        index.append({k: v for k, v in post.items() if k != "html"})
    if sum(1 for p in index if p["featured"]) > 1:
        print("error: at most one post may set featured: true", file=sys.stderr)
        return 1
    index.sort(key=lambda p: (p["published"], p["slug"]), reverse=True)
    (OUT / f"{INDEX}.json").write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    n = len(index)
    if FOCUS_MD.exists():
        FOCUS_HTML.write_text(render(FOCUS_MD.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"ok: prerendered {n} post(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
