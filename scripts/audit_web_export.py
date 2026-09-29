#!/usr/bin/env python3
"""Audit the exact Next static export for navigation/layout contracts.

Stdlib only so CI can run it after `next build` without another dependency.
This intentionally checks the shipped HTML rather than only source components.
"""
from __future__ import annotations

import argparse
import re
from html.parser import HTMLParser
from pathlib import Path


class PageAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.fragment_hrefs: list[str] = []
        self.hrefs: list[str] = []
        self.classes: list[set[str]] = []
        self.desktop_toc_hrefs: list[str] = []
        self._toc_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {k: v or "" for k, v in attrs}
        ident = data.get("id")
        if ident:
            self.ids.append(ident)
        classes = set(data.get("class", "").split())
        if classes:
            self.classes.append(classes)
        if tag == "nav" and {"toc", "toc-sidebar"}.issubset(classes):
            self._toc_depth = 1
        elif self._toc_depth:
            self._toc_depth += 1

        if tag == "a":
            href = data.get("href", "")
            if href:
                self.hrefs.append(href)
                if href.startswith("#") and len(href) > 1:
                    self.fragment_hrefs.append(href[1:])
                    if self._toc_depth:
                        self.desktop_toc_hrefs.append(href[1:])

    def handle_endtag(self, tag: str) -> None:
        if self._toc_depth:
            self._toc_depth -= 1


def parse(path: Path) -> tuple[str, PageAudit]:
    html = path.read_text(encoding="utf-8")
    parser = PageAudit()
    parser.feed(html)
    return html, parser


def check_fragments(name: str, audit: PageAudit, errors: list[str]) -> None:
    ids = set(audit.ids)
    missing = sorted(set(audit.fragment_hrefs) - ids)
    if missing:
        errors.append(f"{name}: fragment links without targets: {', '.join(missing)}")


def check_toc_order(name: str, audit: PageAudit, errors: list[str]) -> None:
    if not audit.desktop_toc_hrefs:
        return
    pos = {ident: i for i, ident in enumerate(audit.ids)}
    present = [ident for ident in audit.desktop_toc_hrefs if ident in pos]
    positions = [pos[ident] for ident in present]
    if positions != sorted(positions):
        errors.append(
            f"{name}: desktop TOC order does not match document order: "
            + " -> ".join(present)
        )


def check_story_page(name: str, audit: PageAudit, errors: list[str]) -> None:
    if not any({"article-body", "prose"}.issubset(classes) for classes in audit.classes):
        errors.append(f"{name}: StoryShell article is missing the prose styling class")

    # A Pages project site must never use '/' for its own home navigation.
    bad_root = [href for href in audit.hrefs if href == "/"]
    if bad_root:
        errors.append(f"{name}: root-absolute internal href='/' escapes the project Pages site")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="web/out", help="Next static export directory")
    args = ap.parse_args()
    root = Path(args.root)

    pages = {
        "phase1b": root / "index.html",
        "routing": root / "z0intelligence-function-routing" / "index.html",
        "memory": root / "unified-memory-v0" / "index.html",
    }

    errors: list[str] = []
    parsed: dict[str, PageAudit] = {}
    for name, path in pages.items():
        if not path.is_file():
            errors.append(f"{name}: missing exported page {path}")
            continue
        _, audit = parse(path)
        parsed[name] = audit
        check_fragments(name, audit, errors)
        check_toc_order(name, audit, errors)

    for name in ("routing", "memory"):
        if name in parsed:
            check_story_page(name, parsed[name], errors)

    if errors:
        print("web export audit failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    for name, audit in parsed.items():
        print(
            f"ok {name}: ids={len(audit.ids)} fragments={len(audit.fragment_hrefs)} "
            f"toc={len(audit.desktop_toc_hrefs)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
