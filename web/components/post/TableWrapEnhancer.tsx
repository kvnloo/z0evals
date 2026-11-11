"use client";

import { useEffect, type RefObject } from "react";
import { watchOverflow } from "@/lib/ux/useOverflowHint";

const SCROLLERS = ".table-wrap, .x-table-wrap, .figure-pan, .heatmap-scroll";

/**
 * Overflow hints for horizontal scrollers inside rendered article HTML: keeps
 * data-overflow current (drives the right-edge fade) and shows a one-time "swipe →"
 * chip on the first overflowing table, removed after its first scroll.
 */
export default function TableWrapEnhancer({ root }: { root: RefObject<HTMLElement | null> }) {
  useEffect(() => {
    const host = root.current;
    if (!host) return;
    let hinted = false;
    const stops = Array.from(host.querySelectorAll<HTMLElement>(SCROLLERS)).map((el) => {
      const stop = watchOverflow(el, () => {
        if (el.dataset.hint) el.dataset.hint = "done";
      });
      requestAnimationFrame(() => {
        if (!hinted && el.dataset.overflow === "end" && el.matches(".table-wrap, .x-table-wrap")) {
          hinted = true;
          el.dataset.hint = "swipe";
        }
      });
      return stop;
    });
    return () => stops.forEach((s) => s());
  }, [root]);
  return null;
}
