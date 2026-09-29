#!/usr/bin/env python3
"""Fast source-level guardrails for z0evals interaction contracts."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

def require(ok: bool, message: str, errors: list[str]) -> None:
    if not ok:
        errors.append(message)

def main() -> int:
    errors: list[str] = []

    shell = read("web/components/StoryShell.tsx")
    require('href="/"' not in shell, "StoryShell must not escape a project Pages site with href=/", errors)
    require('className="article-body prose"' in shell, "StoryShell must opt into shared prose typography", errors)
    require("hashchange" in shell and "closest('[data-mode=\"explore\"]')" in shell,
            "StoryShell must switch reading mode for hash/TOC navigation", errors)

    mobile = read("web/components/MobileToc.tsx")
    require("item.depth ?? 0" in mobile, "Mobile TOC must use TocItem.depth", errors)
    require('document.body.style.overflow = "hidden"' in mobile,
            "Mobile drawer must lock background scrolling", errors)

    css = read("web/app/globals.css")
    require("@media (max-width: 959px)" in css, "Mobile shell breakpoint must be explicit at 959px", errors)
    require(".story-grid {\n  display: block;" in css,
            "StoryShell must not reserve a grid track for its fixed rail", errors)
    require("@media (max-width: 1199px) {\n  .rail { display: none; }" not in css,
            "Desktop rail must not collapse to the mobile FAB at 1199px", errors)

    reveal = read("web/components/charts/useReveal.ts")
    require("rootMargin" in reveal and "getClientRects" in reveal,
            "Reveal lifecycle must handle below-fold and hidden-tab elements", errors)
    require("prefers-reduced-motion" in reveal,
            "Reveal lifecycle must honor reduced motion", errors)

    ladder = read("web/components/LadderFlow.tsx")
    require('"packetPulse 1s ease-in-out infinite"' in ladder,
            "Ladder must use the actual packetPulse keyframe name", errors)
    require('"packetpulse' not in ladder, "Lowercase packetpulse keyframe is invalid", errors)

    animated = [
        "web/components/figures/CorpusGrowth.tsx",
        "web/components/figures/ProgressRows.tsx",
        "web/components/figures/ForecastPair.tsx",
        "web/components/figures/ModelBoard.tsx",
        "web/components/figures/UtilityTie.tsx",
        "web/components/figures/FamilyBoard.tsx",
        "web/components/Heatmap.tsx",
    ]
    for path in animated:
        body = read(path)
        require("useReveal" in body and "shown" in body,
                f"{path} must participate in the reveal lifecycle", errors)

    explorer = read("web/components/ResultsExplorer.tsx")
    require("<Heatmap matrix={scoped} />" in explorer,
            "Family filtering must apply to the heatmap", errors)

    scrubber = read("web/components/ObservationScrubber.tsx")
    require("rate * st.n" in scrubber and "rate * 3" not in scrubber,
            "Split counts must use the actual measured repetition count", errors)

    notes = read("web/components/Notes.tsx")
    require("footnote = false" in notes and "fnref-" in notes,
            "Margin notes must only link when a collected footnote target exists", errors)

    if errors:
        print("web source audit failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"ok: web source interaction contracts ({len(animated)} animated figure surfaces)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
