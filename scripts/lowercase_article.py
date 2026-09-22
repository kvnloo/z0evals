#!/usr/bin/env python3
"""Fold every rendered letter in the article to lowercase.

A CSS `text-transform: lowercase` would only change how the letters *look*: the
DOM, copy-paste, search engines and screen readers would all still see
mixed-case. So this rewrites the actual source text.

The hard part is that these files mix prose and code on the same line. A regex
pass corrupts identifiers; a naive `<` test also matches TypeScript generics
(`Record<string, never>`) and type arguments (`useReveal<HTMLDivElement>`), which
desyncs the scanner and folds the code instead of the prose. So the scanner:

  * tracks JSX text vs code, and emits every `{ ... }` expression verbatim
  * only treats `<` as a tag when it is not preceded by an identifier character
  * folds JSX text nodes, template literals inside `<pre>` diagrams, and the
    string-literal sites that hold visible copy (TOC labels, metric items,
    figure captions, aria-labels)

Three things keep their case because folding them would make them *wrong* rather
than lowercase:

  * the run id (`p1b-20260921T1430Z`) - it must match the artifact
  * URLs and import specifiers
  * identifiers and JSX/TS syntax

Usage:
  python3 scripts/lowercase_article.py            # report, change nothing
  python3 scripts/lowercase_article.py --apply
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"

PROTECT = [
    "p1b-20260921T1430Z",
    "hammer2.1-3b", "hammer2.1_3b", "hammer2.1_7b",
    "functiongemma-270m", "nemotron-orchestrator-8b",
    "qwen3.5-4b", "qwen3.5-9b", "qwen3.5_4b", "qwen3.5_9b",
    "state_id", "budget_units", "authority_breadth", "legal_family_count",
    "dangerous_rate", "exposed_dangerous", "tiny_specialist",
    "insufficient_features",
]

TEXT_ATTRS = ("title", "label", "unit", "alt", "placeholder", "aria-label")


def fold(text: str) -> str:
    low = text.lower()
    for tok in PROTECT:
        if tok.lower() in low:
            low = re.sub(re.escape(tok.lower()), tok, low)
    return low


def _scan_tag(src: str, i: int) -> int:
    n = len(src)
    j = i + 1
    if j < n and src[j] == "/":
        j += 1
    depth = 0
    while j < n:
        c = src[j]
        if c in "\"'":
            q = c
            j += 1
            while j < n and src[j] != q:
                j += 2 if src[j] == "\\" else 1
            j += 1
            continue
        if c == "`":
            j += 1
            while j < n and src[j] != "`":
                j += 2 if src[j] == "\\" else 1
            j += 1
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth = max(0, depth - 1)
        elif c == ">" and depth == 0:
            return j + 1
        j += 1
    return n


def _fold_tag_attrs(tag: str) -> str:
    return re.sub(
        r'(\s(?:' + "|".join(re.escape(a) for a in TEXT_ATTRS) + r')=)\"([^\"]*)\"',
        lambda m: m.group(1) + '"' + fold(m.group(2)) + '"',
        tag,
    )


def transform(src: str) -> str:
    out: list[str] = []
    i, n = 0, len(src)
    in_text = False
    pre_depth = 0

    while i < n:
        ch = src[i]

        # Block and line comments are handled before anything else. They are
        # prose, but they routinely *quote* markup (`` `<svg ...>` `` in a
        # docstring), and entering text mode on a quoted tag never returns:
        # the rest of the file gets folded as prose, which is how
        # `export function FrogGlyph` became `frogglyph`.
        if src.startswith("/*", i):
            end = src.find("*/", i + 2)
            end = n if end < 0 else end + 2
            out.append(src[i:end])
            i = end
            continue
        if src.startswith("//", i):
            end = src.find("\n", i)
            end = n if end < 0 else end
            out.append(src[i:end])
            i = end
            continue

        if in_text:
            if ch == "<":
                in_text = False
                continue
            if ch == "{":
                depth, j, buf = 0, i, []
                while j < n:
                    c = src[j]
                    if c in "\"'":
                        q = c
                        buf.append(c)
                        j += 1
                        while j < n and src[j] != q:
                            if src[j] == "\\":
                                buf.append(src[j:j + 2]); j += 2; continue
                            buf.append(src[j]); j += 1
                        if j < n:
                            buf.append(src[j]); j += 1
                        continue
                    if c == "`":
                        j += 1
                        t = []
                        while j < n and src[j] != "`":
                            if src[j] == "\\" and j + 1 < n:
                                t.append(src[j:j + 2]); j += 2; continue
                            t.append(src[j]); j += 1
                        inner = "".join(t)
                        buf.append("`" + (fold(inner) if pre_depth > 0 else inner) + "`")
                        j += 1
                        continue
                    if c == "{":
                        depth += 1
                    elif c == "}":
                        depth -= 1
                        if depth == 0:
                            buf.append(c); j += 1; break
                    buf.append(c); j += 1
                out.append("".join(buf))
                i = j
                continue
            if src.startswith("</pre>", i):
                pre_depth = max(0, pre_depth - 1); out.append("</pre>"); i += 6; continue
            if src.startswith("<pre>", i):
                pre_depth += 1; out.append("<pre>"); i += 5; continue
            out.append(fold(ch)); i += 1
            continue

        prev = src[i - 1] if i > 0 else ""
        is_generic = prev.isalnum() or prev in "_$."
        if ch == "<" and not is_generic and i + 1 < n and (src[i + 1].isalpha() or src[i + 1] in "/>"):
            end_i = _scan_tag(src, i)
            tag = src[i:end_i]
            out.append(_fold_tag_attrs(tag))
            i = end_i
            # Whether the following characters are prose depends on the tag:
            #
            #   <div>      opening   -> its children are text
            #   <Frog />   self-closing -> back to the parent, which is code
            #   </div>     closing  -> back to the parent, which is code
            #
            # Treating a closing tag as an entry into text is what folded
            # `export function Fn` after `</aside>`: the scanner never returned
            # to code, so the rest of the file was lowercased as prose.
            is_closing = tag.startswith("</")
            is_self_closing = tag.rstrip().endswith("/>")
            in_text = not (is_closing or is_self_closing)
            continue
        out.append(ch)
        i += 1

    return "".join(out)


LITERAL_SITES = (
    r'(\blabel:\s*")([^"]*)(")',
    r'(\bunit:\s*")([^"]*)(")',
    r'(\bbase:\s*")([^"]*)(")',
    r'(\bk:\s*")([^"]*)(")',
    r'(\bv:\s*")([^"]*)(")',
    r'(\bs:\s*")([^"]*)(")',
)


def fold_literal_sites(src: str) -> str:
    for pat in LITERAL_SITES:
        src = re.sub(pat, lambda m: m.group(1) + fold(m.group(2)) + m.group(3), src)
    return src


def targets() -> list[Path]:
    files = [WEB / "app" / "page.tsx", WEB / "app" / "layout.tsx"]
    files += sorted((WEB / "components").rglob("*.tsx"))
    return [f for f in files if f.is_file()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    changed = 0
    for f in targets():
        src = f.read_text(encoding="utf-8")
        dest = fold_literal_sites(transform(src))
        if dest != src:
            changed += 1
            n = sum(1 for x, y in zip(src.splitlines(), dest.splitlines()) if x != y)
            verb = "folded" if a.apply else "would fold"
            print(f"  {verb} {n:4} lines  {f.relative_to(ROOT)}")
            if a.apply:
                f.write_text(dest, encoding="utf-8")
    print(f"{'changed' if a.apply else 'to change'}: {changed} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
