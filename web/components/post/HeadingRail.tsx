"use client";

import { useEffect, useRef, useState } from "react";
import { haptic } from "@/lib/ux/haptics";
import type { TocItem } from "@/components/Toc";

// Dash PromptRail: tick length grows with the log of the section's characters.
export function railWidth(characters: number): number {
  if (!Number.isFinite(characters) || characters <= 0) return 8;
  return 8 + 24 * Math.min(1, Math.log1p(characters) / Math.log1p(12000));
}

export function railTarget(y: number, height: number, count: number): number {
  if (count === 0 || height <= 0) return 0;
  return Math.min(count - 1, Math.max(0, Math.floor((y / height) * count)));
}

/**
 * Heading scrubber for touch screens under 1024px on posts with ≥ 6 headings. Drag
 * along the right edge: a floating preview names the heading under the finger, one
 * `select` haptic per heading crossed; release jumps once, pointercancel never jumps.
 */
export default function HeadingRail({ items, onJump }: { items: TocItem[]; onJump: (id: string) => void }) {
  const [enabled, setEnabled] = useState(false);
  const [chars, setChars] = useState<number[]>([]);
  const [index, setIndex] = useState<number | null>(null);
  const rail = useRef<HTMLDivElement>(null);
  const idx = useRef<number | null>(null);
  const pointer = useRef<number | null>(null);

  useEffect(() => {
    const touch = matchMedia("(pointer: coarse) and (max-width: 1023px)").matches;
    if (!touch || items.length < 6) return;
    const els = items.map((i) => document.getElementById(i.id));
    if (els.some((e) => !e)) return;
    const end = document.querySelector(".article-body")?.lastElementChild;
    const counts = els.map((el, i) => {
      const r = document.createRange();
      r.setStartBefore(el!);
      const next = els[i + 1];
      if (next) r.setEndBefore(next);
      else if (end) r.setEndAfter(end);
      else return 0;
      return r.toString().length;
    });
    setChars(counts);
    setEnabled(true);
  }, [items]);

  // fade in after one screen of scrolling (attribute write in rAF, passive listener)
  useEffect(() => {
    if (!enabled) return;
    let frame = 0;
    const tick = () => {
      frame = 0;
      const on = window.scrollY > window.innerHeight;
      const el = rail.current;
      if (el && (el.dataset.visible === "1") !== on) el.dataset.visible = on ? "1" : "0";
    };
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(tick);
    };
    tick();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      if (frame) cancelAnimationFrame(frame);
    };
  }, [enabled]);

  if (!enabled) return null;

  const at = (clientY: number) => {
    const r = rail.current!.getBoundingClientRect();
    return railTarget(clientY - r.top, r.height, items.length);
  };
  const choose = (i: number) => {
    if (i === idx.current) return;
    idx.current = i;
    setIndex(i);
    haptic.select();
  };
  const reset = () => {
    pointer.current = null;
    idx.current = null;
    setIndex(null);
  };

  return (
    <div
      ref={rail}
      className="heading-rail"
      data-visible="0"
      data-active={index !== null ? "1" : undefined}
      role="slider"
      tabIndex={-1}
      aria-label="scrub through headings"
      aria-valuemin={1}
      aria-valuemax={items.length}
      aria-valuenow={(index ?? 0) + 1}
      onPointerDown={(e) => {
        pointer.current = e.pointerId;
        e.currentTarget.setPointerCapture(e.pointerId);
        choose(at(e.clientY));
      }}
      onPointerMove={(e) => {
        if (pointer.current !== e.pointerId) return;
        choose(at(e.clientY));
      }}
      onPointerUp={(e) => {
        if (pointer.current !== e.pointerId) return;
        const i = idx.current;
        reset();
        if (i === null) return;
        haptic.tap();
        onJump(items[i].id);
      }}
      onPointerCancel={reset}
    >
      <div className="heading-rail-ticks" aria-hidden="true">
        {items.map((it, i) => (
          <span key={it.id} className="heading-rail-slot">
            <i style={{ transform: `scaleX(${railWidth(chars[i] ?? 0) / 32})` }} data-on={index === i ? "1" : undefined} />
          </span>
        ))}
      </div>
      {index !== null ? (
        <div className="heading-rail-preview" style={{ transform: `translateY(${((index + 0.5) / items.length) * 100}cqh)` }} aria-hidden="true">
          <span className="heading-rail-n">{index + 1}/{items.length}</span>
          {items[index].label}
        </div>
      ) : null}
    </div>
  );
}
