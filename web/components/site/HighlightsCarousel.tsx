"use client";

import { Children, useEffect, useRef, type ReactNode } from "react";
import { haptic } from "@/lib/ux/haptics";

/**
 * Phones: native horizontal scroll-snap carousel (momentum kept), a gold gel dot that
 * tracks scrollLeft 1:1 (transform in rAF), and one `select` tick when a touch-started
 * scroll settles on a new card. Tablet/desktop: a plain 2-column grid.
 */
export default function HighlightsCarousel({ children, label }: { children: ReactNode; label: string }) {
  const track = useRef<HTMLUListElement>(null);
  const dot = useRef<HTMLSpanElement>(null);
  const items = Children.toArray(children);
  const n = items.length;

  useEffect(() => {
    const el = track.current;
    if (!el) return;
    let raf = 0;
    let touched = false;
    let index = 0;
    let idle = 0;
    const hasScrollEnd = "onscrollend" in window;
    const step = 16; // dot pitch in px, matches .carousel-dots i + gap
    const write = () => {
      raf = 0;
      const max = el.scrollWidth - el.clientWidth;
      const p = max > 0 ? el.scrollLeft / max : 0;
      if (dot.current) dot.current.style.transform = `translateX(${p * (n - 1) * step}px)`;
    };
    const settled = () => {
      const card = el.firstElementChild as HTMLElement | null;
      const pitch = card ? card.offsetWidth + 12 : el.clientWidth;
      const next = Math.round(el.scrollLeft / Math.max(1, pitch));
      if (next !== index) {
        index = next;
        if (touched) haptic.select();
      }
      touched = false;
    };
    const onScroll = () => {
      if (!raf) raf = requestAnimationFrame(write);
      if (!hasScrollEnd) {
        clearTimeout(idle);
        idle = setTimeout(settled, 120) as unknown as number;
      }
    };
    const onDown = () => {
      touched = true;
    };
    el.addEventListener("scroll", onScroll, { passive: true });
    el.addEventListener("scrollend", settled, { passive: true });
    el.addEventListener("pointerdown", onDown, { passive: true });
    write();
    return () => {
      el.removeEventListener("scroll", onScroll);
      el.removeEventListener("scrollend", settled);
      el.removeEventListener("pointerdown", onDown);
      if (raf) cancelAnimationFrame(raf);
      clearTimeout(idle);
    };
  }, [n]);

  return (
    <div className="carousel">
      <ul ref={track} className="carousel-track" aria-label={label}>
        {items.map((c, i) => (
          <li key={i} className="carousel-item">{c}</li>
        ))}
      </ul>
      <div className="carousel-dots" aria-hidden="true">
        {items.map((_, i) => <i key={i} />)}
        <span ref={dot} className="carousel-dot" />
      </div>
    </div>
  );
}
