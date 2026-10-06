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
        self.aria_controls: list[str] = []
        self._toc_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {k: v or "" for k, v in attrs}
        ident = data.get("id")
        if ident:
            self.ids.append(ident)
        controls = data.get("aria-controls", "").strip()
        if controls:
            self.aria_controls.extend(controls.split())
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


def check_ids_and_aria(name: str, audit: PageAudit, errors: list[str]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for ident in audit.ids:
        if ident in seen:
            duplicates.add(ident)
        seen.add(ident)
    if duplicates:
        errors.append(f"{name}: duplicate ids: {', '.join(sorted(duplicates))}")

    missing_controls = sorted(set(audit.aria_controls) - seen)
    if missing_controls:
        errors.append(
            f"{name}: aria-controls without targets: {', '.join(missing_controls)}"
        )


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


def check_relative_links(
    name: str,
    path: Path,
    root: Path,
    audit: PageAudit,
    errors: list[str],
) -> None:
    for href in audit.hrefs:
        if (
            href.startswith("#")
            or href.startswith("http://")
            or href.startswith("https://")
            or href.startswith("mailto:")
            or href.startswith("tel:")
        ):
            continue
        clean = href.split("#", 1)[0].split("?", 1)[0]
        if not clean or clean.startswith("/"):
            continue

        target = path.parent / clean
        if clean.endswith("/") or target.suffix == "":
            target = target / "index.html"
        try:
            target.relative_to(root)
        except ValueError:
            errors.append(f"{name}: internal href escapes export root: {href}")
            continue
        if not target.is_file():
            errors.append(f"{name}: internal href has no exported target: {href}")


def check_story_page(name: str, audit: PageAudit, errors: list[str]) -> None:
    if not any({"article-body", "prose"}.issubset(classes) for classes in audit.classes):
        errors.append(f"{name}: StoryShell article is missing the prose styling class")

    # A Pages project site must not use origin-root anchors for its own pages.
    # Those escape /z0evals/ and also break /next/, /nightly/ and /dev/.
    bad_root = [href for href in audit.hrefs if href.startswith("/") and not href.startswith("//")]
    if bad_root:
        errors.append(
            f"{name}: root-absolute internal anchors escape the project Pages site: "
            + ", ".join(sorted(set(bad_root)))
        )


def check_memory_progress(audit: PageAudit, errors: list[str]) -> None:
    """Do not publish the old memory page without its credited, pinned update."""
    for ident in ("optmem-update", "optchat-update"):
        if ident not in audit.ids:
            errors.append(f"memory: missing published progress section {ident}")
    required_sources = (
        "https://github.com/VictorTaelin/OptMem",
        "https://github.com/kvnloo/z0intelligence/blob/b345aa2bef199779cac8672b08d535cb28526fd7/src/z0int/memory/optmem_tree.py",
        "https://github.com/kvnloo/z0intelligence/commit/0828b7738d35e712b57814aa09a8bddf82a48fcc",
        "https://github.com/kvnloo/z0intelligence/commit/fc31fb5ca3e1322af3951080dfb0cd95b76fc93d",
    )
    for href in required_sources:
        if href not in audit.hrefs:
            errors.append(f"memory: missing progress provenance {href}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="web/out", help="Next static export directory")
    args = ap.parse_args()
    root = Path(args.root)

    pages = {
        "phase1b": root / "index.html",
        "routing": root / "z0intelligence-function-routing" / "index.html",
        "research": root / "researching-the-frontier" / "index.html",
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
        check_ids_and_aria(name, audit, errors)
        check_fragments(name, audit, errors)
        check_toc_order(name, audit, errors)
        check_relative_links(name, path, root, audit, errors)

    for name in ("routing", "research", "memory"):
        if name in parsed:
            check_story_page(name, parsed[name], errors)
    if "memory" in parsed:
        check_memory_progress(parsed["memory"], errors)

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
