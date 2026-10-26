"use client";
import { useEffect, type RefObject } from "react";

/** data-overflow on a horizontal scroller: "none" | "end" | "both" | "start". */
export function overflowState(el: HTMLElement): string {
  const max = el.scrollWidth - el.clientWidth;
  if (max <= 1) return "none";
  const atStart = el.scrollLeft <= 1;
  const atEnd = el.scrollLeft + el.clientWidth >= el.scrollWidth - 1;
  return atStart ? "end" : atEnd ? "start" : "both";
}

/**
 * Keeps data-overflow current on one scroller. Reads scroll geometry in a passive
 * listener, writes the attribute in rAF, and never writes layout-affecting styles.
 */
export function watchOverflow(el: HTMLElement, onFirstScroll?: () => void): () => void {
  let frame = 0;
  let scrolled = false;
  const write = () => {
    frame = 0;
    const next = overflowState(el);
    if (el.dataset.overflow !== next) el.dataset.overflow = next;
  };
  const queue = () => {
    if (!frame) frame = requestAnimationFrame(write);
  };
  const onScroll = () => {
    if (!scrolled && el.scrollLeft > 4) {
      scrolled = true;
      onFirstScroll?.();
    }
    queue();
  };
  write();
  el.addEventListener("scroll", onScroll, { passive: true });
  const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(queue) : null;
  ro?.observe(el);
  return () => {
    el.removeEventListener("scroll", onScroll);
    ro?.disconnect();
    if (frame) cancelAnimationFrame(frame);
  };
}

export function useOverflowHint(ref: RefObject<HTMLElement | null>) {
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    return watchOverflow(el);
  }, [ref]);
}
