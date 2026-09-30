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
    for token in ("border", "bg-muted", "secondary", "text", "text-light", "highlight-soft", "error"):
        require(
            f"--sb-{token}: var(--color-sb-{token})" in css,
            f"Reference SVG tokens must resolve: --sb-{token}",
            errors,
        )
    require(".story-grid {\n  display: block;" in css,
            "StoryShell must not reserve a grid track for its fixed rail", errors)
    require(".toc-scrollable-container {" in css and "max-height: calc(100vh - 10rem)" in css,
            "Long desktop TOCs must scroll inside the viewport", errors)
    require("grid-template-columns: 12px minmax(0, 1fr) auto;" in css,
            "Capability rows need a narrow-screen layout", errors)
    require(".story-shell * {" in css and "text-transform: lowercase !important" in css,
            "New research posts must keep the lowercase z0evals voice", errors)
    require(".heatmap-svg" in css and "min-width: 760px" in css,
            "The old post heatmap must stay readable on narrow screens", errors)
    require(".tooltip {" in css and "animation: none;" in css,
            "Chart tooltips must not self-dismiss while the target is still active", errors)
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
    require("@keyframes packetPulse" in css,
            "packetPulse keyframe must exist in the stylesheet", errors)
    require('"packetpulse' not in ladder, "Lowercase packetpulse keyframe is invalid", errors)

    animated = [
        "web/components/ActionTable.tsx",
        "web/components/EvidencePipeline.tsx",
        "web/components/FamilyStack.tsx",
        "web/components/Heatmap.tsx",
        "web/components/MetricReveal.tsx",
        "web/components/ReplayChart.tsx",
        "web/components/RoutingTrace.tsx",
        "web/components/charts/ArmScatter.tsx",
        "web/components/charts/Calibration.tsx",
        "web/components/charts/CompositionSplit.tsx",
        "web/components/charts/DangerousBars.tsx",
        "web/components/charts/DensityBars.tsx",
        "web/components/charts/OrchestrationBars.tsx",
        "web/components/charts/ResidencyBars.tsx",
        "web/components/figures/CorpusGrowth.tsx",
        "web/components/figures/FamilyBoard.tsx",
        "web/components/figures/ForecastPair.tsx",
        "web/components/figures/ModelBoard.tsx",
        "web/components/figures/ProgressRows.tsx",
        "web/components/figures/UtilityTie.tsx",
    ]
    for path in animated:
        body = read(path)
        require("useReveal" in body and "shown" in body,
                f"{path} must participate in the reveal lifecycle", errors)

    explorer = read("web/components/ResultsExplorer.tsx")
    require("<Heatmap matrix={scoped} />" in explorer,
            "Family filtering must apply to the heatmap", errors)
    require("if (cur.length === 1) return cur;" in explorer,
            "Replay controls must not allow every arm to disappear", errors)

    scrubber = read("web/components/ObservationScrubber.tsx")
    require("rate * st.n" in scrubber and "rate * 3" not in scrubber,
            "Split counts must use the actual measured repetition count", errors)
    require("safeIndex" in scrubber and "states.length - 1" in scrubber,
            "Filtered old-post scrubber must clamp its index", errors)

    heatmap = read("web/components/Heatmap.tsx")
    require('className="heatmap-scroll"' in heatmap and "heatmap-svg" in heatmap,
            "Old-post heatmap must use the narrow-screen scroll surface", errors)

    scatter = read("web/components/charts/ArmScatter.tsx")
    calibration = read("web/components/charts/Calibration.tsx")
    require("onFocus" in scatter and "tabIndex={0}" in scatter,
            "Old-post scatter points must be keyboard readable", errors)
    require("onFocus" in calibration and "tabIndex={0}" in calibration,
            "Old-post calibration points must be keyboard readable", errors)

    routing_page = read("web/app/z0intelligence-function-routing/page.tsx")
    memory_page = read("web/app/unified-memory-v0/page.tsx")
    require("everything was green. that was the problem." in routing_page,
            "Routing story should use the informal lowercase voice", errors)
    require("can four agents remember the same thing?" in memory_page,
            "Memory story should use the informal lowercase voice", errors)

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
