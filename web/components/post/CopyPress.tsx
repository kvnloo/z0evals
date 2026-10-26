"use client";

import { useEffect, useRef, useState, type RefObject } from "react";
import { haptic } from "@/lib/ux/haptics";

const SELECTOR = "pre, figure, .figure, .ref";
const HOLD_MS = 400;
const SLOP = 8;

type Bloom = { x: number; y: number; text: string; hash: string };

function nearestHeadingId(el: Element, root: HTMLElement): string {
  if (el.id) return el.id;
  const heads = Array.from(root.querySelectorAll<HTMLElement>("h2[id], h3[id], .heading-with-frog[id]"));
  let best = "";
  for (const h of heads) {
    if (h.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING) best = h.id;
    else break;
  }
  return best;
}

/**
 * Long-press (400ms, cancelled past 8px) on code, figures and references opens a small
 * bloom menu: copy, or copy a link to here. The context menu is suppressed only on
 * those elements, and only for touch.
 */
export default function CopyPress({ root }: { root: RefObject<HTMLElement | null> }) {
  const [bloom, setBloom] = useState<Bloom | null>(null);
  const menu = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const host = root.current;
    if (!host) return;
    let timer = 0;
    let start: { x: number; y: number; id: number } | null = null;
    let armedAt = 0;
    const clear = () => {
      window.clearTimeout(timer);
      timer = 0;
      start = null;
    };
    const onDown = (e: PointerEvent) => {
      if (e.pointerType === "mouse") return;
      const el = (e.target as Element).closest(SELECTOR);
      if (!el || !host.contains(el)) return;
      start = { x: e.clientX, y: e.clientY, id: e.pointerId };
      timer = window.setTimeout(() => {
        timer = 0;
        armedAt = performance.now();
        haptic.select();
        const text = (el.querySelector("figcaption")?.textContent || el.textContent || "").trim();
        setBloom({ x: start?.x ?? e.clientX, y: start?.y ?? e.clientY, text, hash: nearestHeadingId(el, host) });
      }, HOLD_MS);
    };
    const onMove = (e: PointerEvent) => {
      if (!start || e.pointerId !== start.id) return;
      if (Math.hypot(e.clientX - start.x, e.clientY - start.y) > SLOP) clear();
    };
    const onCtx = (e: Event) => {
      const el = (e.target as Element).closest(SELECTOR);
      if (el && host.contains(el) && (timer || performance.now() - armedAt < 1500)) e.preventDefault();
    };
    host.addEventListener("pointerdown", onDown, { passive: true });
    host.addEventListener("pointermove", onMove, { passive: true });
    host.addEventListener("pointerup", clear, { passive: true });
    host.addEventListener("pointercancel", clear, { passive: true });
    host.addEventListener("contextmenu", onCtx);
    return () => {
      clear();
      host.removeEventListener("pointerdown", onDown);
      host.removeEventListener("pointermove", onMove);
      host.removeEventListener("pointerup", clear);
      host.removeEventListener("pointercancel", clear);
      host.removeEventListener("contextmenu", onCtx);
    };
  }, [root]);

  useEffect(() => {
    if (!bloom) return;
    menu.current?.querySelector<HTMLButtonElement>("button")?.focus({ preventScroll: true });
    const away = (e: Event) => {
      if (menu.current && !menu.current.contains(e.target as Node)) setBloom(null);
    };
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") setBloom(null);
    };
    const t = window.setTimeout(() => document.addEventListener("pointerdown", away, { passive: true }), 0);
    window.addEventListener("scroll", away as EventListener, { passive: true });
    document.addEventListener("keydown", key);
    return () => {
      window.clearTimeout(t);
      document.removeEventListener("pointerdown", away);
      window.removeEventListener("scroll", away as EventListener);
      document.removeEventListener("keydown", key);
    };
  }, [bloom]);

  if (!bloom) return null;
  const copy = async (value: string) => {
    try {
      await navigator.clipboard.writeText(value);
      haptic.success();
    } catch {
      haptic.error();
    }
    setBloom(null);
  };
  const left = Math.min(Math.max(12, bloom.x - 90), window.innerWidth - 192);
  const top = Math.max(12, bloom.y - 64);
  return (
    <div ref={menu} className="copy-bloom" role="menu" aria-label="copy" style={{ left, top }}>
      <button type="button" role="menuitem" data-press="control" onClick={() => copy(bloom.text)}>copy</button>
      <button
        type="button"
        role="menuitem"
        data-press="control"
        onClick={() => copy(`${location.origin}${location.pathname}${bloom.hash ? `#${bloom.hash}` : ""}`)}
      >
        copy link to here
      </button>
    </div>
  );
}
