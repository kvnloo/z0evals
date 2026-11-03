#!/usr/bin/env python3
"""Prerender posts/*.md and the research-log focus note for the Next site.

Writes web/data/posts/<slug>.json ({slug, title, subtitle, study, status, author, date,
toc, lede, tldr, html}) and web/data/research-focus.html. The site renders these files; it
does not parse markdown itself. Nothing is invented: every field comes from the post.

Two optional conventions from the interactive-essay kit (web/components/essay):

* ``tldr:`` in the front matter (markdown) becomes ``tldr`` (html) and renders in the
  boxed tl;dr above the body. Absent means ``""`` and no box.
* a fenced block with the info string ``setup`` folds its markdown behind a "setup"
  pill attached to the next block (a table, an image paragraph, a fenced code block
  or a ``<figure>...</figure>``)::

      ```setup
      eight synthetic documents, ten fixed queries.
      ```
      | arm | recall@5 |
      |---|---:|

  The pair becomes ``<figure class="es-fig es-wide has-setup">`` with a
  ``<details class="es-setup">`` inside, the same markup SetupFigure renders, so it
  still works as a plain disclosure without JS. Posts without either stay byte-identical.
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


EXTENSIONS = ["attr_list", "tables", "fenced_code", "md_in_html", "sane_lists"]
# ```setup ... ``` then (after optional blank lines) the block it describes
SETUP = re.compile(r"^```setup[ \t]*\n(.*?)\n```[ \t]*\n(?:[ \t]*\n)*", re.S | re.M)
SLOT = "<!-- es-setup-slot:{} -->"


def _markdown(md: str) -> str:
    html = markdown.markdown(md, extensions=EXTENSIONS)
    # wide tables scroll inside their own box on phones instead of crushing their columns
    return re.sub(r"<table>(.*?)</table>", r'<div class="table-wrap"><table>\1</table></div>', html, flags=re.S)


def _next_block(md: str, start: int) -> int:
    """End offset of the markdown block that begins at ``start``."""
    rest = md[start:]
    fence = re.match(r"(`{3,}|~{3,})[^\n]*\n", rest)
    if fence:
        close = re.search(rf"^{fence.group(1)}[ \t]*$", rest[fence.end():], re.M)
        if not close:
            raise ValueError("setup block: the code fence after it never closes")
        return start + fence.end() + close.end()
    if rest.startswith("<figure"):
        close = rest.find("</figure>")
        if close < 0:
            raise ValueError("setup block: the <figure> after it never closes")
        return start + close + len("</figure>")
    blank = re.search(r"\n[ \t]*\n", rest)
    return start + (blank.start() if blank else len(rest))


def _fold_setups(md: str) -> tuple[str, list[str]]:
    """Swap each ```setup block and its figure for a slot; return the slot html."""
    out: list[str] = []
    figures: list[str] = []
    pos = 0
    while (m := SETUP.search(md, pos)) is not None:
        end = _next_block(md, m.end())
        target = md[m.end():end]
        if not target.strip():
            raise ValueError("setup block must be followed by the figure or table it describes")
        figures.append(
            '<figure class="es-fig es-wide has-setup">'
            '<details class="es-setup"><summary>setup</summary>'
            f'<div class="es-setup-body">{_markdown(m.group(1))}</div></details>'
            f"{_markdown(target)}</figure>"
        )
        out.append(md[pos:m.start()] + "\n\n" + SLOT.format(len(figures) - 1) + "\n\n")
        pos = end
    out.append(md[pos:])
    return "".join(out), figures


def render(md: str) -> str:
    md = HEADING_ID.sub(lambda m: f"{m.group(1)} {m.group(2)} {{: #{m.group(3)} }}", md)
    md, figures = _fold_setups(md)
    html = _markdown(md)
    for i, fig in enumerate(figures):
        slot = SLOT.format(i)
        if slot not in html:
            raise ValueError(f"setup slot {i} was lost while rendering")
        html = html.replace(slot, fig, 1)
    return html


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
        "tldr": markdown.markdown(str(meta["tldr"]).strip(), extensions=EXTENSIONS) if meta.get("tldr") else "",
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
