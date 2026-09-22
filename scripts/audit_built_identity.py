#!/usr/bin/env python3
"""Semantic audit of the BUILT output for model identity.

Runs after the Next build and inspects the real HTML, because the failure this
guards against was never visible in source: every source file was individually
defensible while the rendered page showed a lane labelled `jev`.

This is a **surface** audit, not a text grep. It walks the DOM hooks that carry
identity and checks those, then separately asserts that the frozen raw arm ids
are still present verbatim — because the two things that must both hold are:

    the UI may abbreviate; the evidence identity may not

Case-insensitive and token-aware. `nanojev` and `openjev` are different tokens
from `jev` and pass.

Explicitly allowed contexts for a bare `jev` (documented rather than silently
ignored, so the exclusions are reviewable):

  * external reference links to the actual Jev project
  * **raw frozen arm ids** rendered as code, e.g. ``compiler+jev`` — these are
    join keys and were deliberately not renamed
  * **state/fixture ids** such as ``jev_uncertain``, which name a benchmark
    state and not a model
  * the J1 pilot sentence, where `jev` is the hosted teacher and is named
    *alongside* `nanojev`, which is the whole point of that comparison

    python3 scripts/audit_built_identity.py
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import arm_identity as A  # noqa: E402

OUT_DIRS = [REPO / "web" / "out", REPO / "site"]
TARGETS = ["index.html", "posts/slm-router-v0.html"]

BARE_JEVE = re.compile(r"(?<![A-Za-z0-9_])jev(?![A-Za-z0-9_-])", re.IGNORECASE)
TAG = re.compile(r"<[^>]+>")


def strip_tags(s: str) -> str:
    return html.unescape(TAG.sub(" ", s)).strip()


def attr_elements(text: str, attr: str):
    """(value, full attribute string, inner text) for each element with `attr`."""
    out = []
    for m in re.finditer(r"<(\w+)([^>]*\b%s=\"([^\"]*)\"[^>]*)>" % re.escape(attr), text):
        tag, attrs, val = m.group(1), m.group(2), m.group(3)
        close = text.find(f"</{tag}>", m.end())
        inner = text[m.end(): close] if close != -1 else text[m.end(): m.end() + 600]
        out.append((val, attrs, inner))
    return out


def surface_problems(path: Path, raw: str) -> tuple[list[str], dict]:
    """Check only the surfaces that carry model identity.

    Scoped per document: the Next build carries identity surfaces, the legacy
    static build does not. A missing long name is only a defect in a document
    that renders arm identities in the first place.
    """
    rel = path.relative_to(REPO)
    problems: list[str] = []
    stats: dict = {}

    # --- 1. every data-arm-id element: model id + visible label --------------
    by_arm = attr_elements(raw, "data-arm-id")
    stats["data-arm-id elements"] = len(by_arm)
    for arm, attrs, inner in by_arm:
        m = re.search(r'data-model-id="([^"]*)"', attrs)
        want = A.backend(arm)
        if not m:
            problems.append(f"{rel}: {arm} carries no data-model-id")
        elif m.group(1) != want:
            problems.append(f"{rel}: {arm} declares data-model-id={m.group(1)!r}, resolver says {want!r}")
        label = strip_tags(re.sub(r"<title>.*?</title>", " ", inner, flags=re.DOTALL))
        if BARE_JEVE.search(label):
            problems.append(f"{rel}: arm {arm} renders bare 'jev' as its label: {label[:90]!r}")

    # --- 2. the model-board name column -------------------------------------
    names = re.findall(r'class="modelName"[^>]*>([^<]*)<', raw)
    stats["model-board name cells"] = len(names)
    for n in names:
        if BARE_JEVE.search(n):
            problems.append(f"{rel}: model-board identity renders bare 'jev': {n!r}")

    # --- 3. chart lanes that carry an arm id ---------------------------------
    lanes = re.findall(r'class="corpusLabel"[^>]*data-arm-id="([^"]+)"[^>]*>(.*?)</text>', raw, re.DOTALL)
    stats["identity-bearing chart lanes"] = len(lanes)
    for arm, inner in lanes:
        label = strip_tags(re.sub(r"<title>.*?</title>", " ", inner, flags=re.DOTALL))
        if BARE_JEVE.search(label):
            problems.append(f"{rel}: lane {arm} renders bare 'jev': {label[:90]!r}")
        if not re.search(r"<title>", inner):
            problems.append(f"{rel}: lane {arm} has no <title> with the long name")

    # --- 4. the escalation ladder rungs -------------------------------------
    rungs: list[str] = []
    for m in re.finditer(r'aria-label="escalation ladder[^"]*"', raw):
        seg = raw[m.end(): m.end() + 4000]
        rungs += [strip_tags(t) for t in re.findall(r"<text[^>]*>([^<]+)</text>", seg)]
    stats["ladder rung labels"] = len(rungs)
    for r in rungs:
        if BARE_JEVE.search(r):
            problems.append(f"{rel}: ladder rung renders bare 'jev': {r!r}")
    if rungs and not any("nanojev" in r.lower() for r in rungs):
        problems.append(f"{rel}: no ladder rung names nanojev (rungs={rungs})")

    # --- 5. the long semantic name must be reachable somewhere --------------
    titles = [html.unescape(t) for t in re.findall(r"<title>([^<]*)</title>", raw)]
    stats["<title> elements"] = len(titles)
    stats["carries identity surfaces"] = bool(by_arm)
    if by_arm and not any("nanojev" in t.lower() for t in titles):
        problems.append(f"{rel}: renders arm identities but no <title> carries the long nanojev name")

    return problems, stats


def main() -> int:
    docs = [(d / r, (d / r).read_text(encoding="utf-8", errors="replace"))
            for d in OUT_DIRS for r in TARGETS if (d / r).is_file()]
    if not docs:
        print("no built output found; run the Next build first", file=sys.stderr)
        return 2

    problems: list[str] = []
    all_stats: dict[str, dict] = {}
    for path, raw in docs:
        p, s = surface_problems(path, raw)
        problems += p
        all_stats[str(path.relative_to(REPO))] = s

    # --- 6. frozen ids preserved verbatim (ids were NOT renamed) ------------
    joined = "\n".join(raw for _, raw in docs)
    for arm in ("compiler+jev", "compiler+jev+qwen3.5_4b"):
        if arm not in joined:
            problems.append(f"frozen arm id {arm!r} is missing from the built output — ids were renamed")

    # --- 7. allowed contexts must survive ----------------------------------
    ref_ok = "southbridgeai/jev" in joined
    if not ref_ok:
        problems.append("the external Southbridge Jev reference link disappeared")
    pilot_ok = bool(re.search(r"nanojev p50/p95", joined))
    if not pilot_ok:
        problems.append("the J1 pilot comparison (hosted jev vs nanojev) disappeared")

    # --- 8. the CSS/DOM contract recovered earlier must stay tested --------
    attr = set(re.findall(r'data-model="([^"]+)"', joined))
    css = "\n".join(f.read_text(encoding="utf-8", errors="replace")
                    for f in (REPO / "web" / "out").rglob("*.css"))
    selectors = set(re.findall(r"modelRow\[data-model\^=([^\]]+)\]", css))
    contract_ok = "compiler-first" in attr and "compiler-first" in selectors
    if not contract_ok:
        problems.append(f"css/dom contract broken: html attr={sorted(attr)} css selector={sorted(selectors)}")

    print("built-output identity audit (surface-based, not a text grep)")
    print(f"  documents                : {len(docs)}")
    for name, s in all_stats.items():
        print(f"  {name}")
        for k, v in s.items():
            print(f"      {k:32s}: {v}")
    print(f"  frozen arm ids present   : {'yes' if 'compiler+jev' in joined else 'NO'}")
    print(f"  southbridge jev link kept: {'yes' if ref_ok else 'NO'}")
    print(f"  J1 pilot comparison kept : {'yes' if pilot_ok else 'NO'}")
    print(f"  css/dom contract         : {'ok' if contract_ok else 'BROKEN'}")
    print()
    if problems:
        print(f"FAIL — {len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("PASS — no incorrect model-identity 'jev' in any arm label, ladder rung,")
    print("       model-board identity or chart lane; frozen ids and reference intact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
