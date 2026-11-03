"use client";

import { useEffect, useLayoutEffect, useRef } from "react";
import { EASE_CRIT, MS, reduced } from "@/lib/ux/motion";
import { haptic } from "@/lib/ux/haptics";

export type SegOption = { id: string; label: string; count?: number };

const useIso = typeof window === "undefined" ? useEffect : useLayoutEffect;

/**
 * Segmented control with one gold gel pill that slides between segments (FLIP on
 * transform, --t-snap, critical easing). Without JS the pressed segment is styled
 * directly. On phones the segments scroll horizontally with snap and an edge fade.
 */
export default function GelSeg({
  options,
  value,
  onChange,
  label,
}: {
  options: SegOption[];
  value: string;
  onChange: (id: string) => void;
  label: string;
}) {
  const wrap = useRef<HTMLDivElement>(null);
  const pill = useRef<HTMLSpanElement>(null);
  const last = useRef<{ x: number; w: number } | null>(null);

  useIso(() => {
    const root = wrap.current;
    const p = pill.current;
    if (!root || !p) return;
    const btn = root.querySelector<HTMLElement>('button[aria-pressed="true"]');
    if (!btn) return;
    const x = btn.offsetLeft;
    const w = btn.offsetWidth;
    p.style.left = `${x}px`;
    p.style.top = `${btn.offsetTop}px`;
    p.style.width = `${w}px`;
    p.style.height = `${btn.offsetHeight}px`;
    root.dataset.gel = "1";
    const prev = last.current;
    last.current = { x, w };
    if (prev && (prev.x !== x || prev.w !== w) && !reduced()) {
      p.animate(
        [
          { transform: `translateX(${prev.x - x + (prev.w - w) / 2}px) scaleX(${prev.w / w})` },
          { transform: "translateX(0) scaleX(1)" },
        ],
        { duration: MS.snap, easing: EASE_CRIT },
      );
    }
    // keep the chosen segment visible inside the phone scroller
    const sc = root.closest<HTMLElement>(".seg-scroll");
    if (sc && sc.scrollWidth > sc.clientWidth) {
      const l = btn.offsetLeft - sc.scrollLeft;
      if (l < 0 || l + w > sc.clientWidth) sc.scrollTo({ left: btn.offsetLeft - 16, behavior: reduced() ? "auto" : "smooth" });
    }
  }, [value]);

  // re-measure on resize (fonts loading, rotation) without animating
  useEffect(() => {
    const root = wrap.current;
    if (!root) return;
    const ro = new ResizeObserver(() => {
      const p = pill.current;
      const btn = root.querySelector<HTMLElement>('button[aria-pressed="true"]');
      if (!p || !btn) return;
      p.style.left = `${btn.offsetLeft}px`;
      p.style.width = `${btn.offsetWidth}px`;
      p.style.top = `${btn.offsetTop}px`;
      p.style.height = `${btn.offsetHeight}px`;
      last.current = { x: btn.offsetLeft, w: btn.offsetWidth };
    });
    ro.observe(root);
    return () => ro.disconnect();
  }, []);

  return (
    <div className="seg-scroll">
      <div ref={wrap} className="log-seg gel-seg" role="group" aria-label={label}>
        <span ref={pill} className="gel-pill" aria-hidden="true" />
        {options.map((o) => (
          <button
            key={o.id}
            type="button"
            data-press="control"
            aria-pressed={value === o.id}
            onClick={() => {
              if (o.id === value) return;
              haptic.select();
              onChange(o.id);
            }}
          >
            {o.label} {o.count !== undefined ? <span className="n">{o.count}</span> : null}
          </button>
        ))}
      </div>
    </div>
  );
}
