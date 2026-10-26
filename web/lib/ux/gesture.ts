"use client";
import { useEffect, useRef, type RefObject } from "react";
import { currentTranslate, settle } from "./motion";

export type SwipeRelease = {
  offset: number; // where the finger left the element (after rubber band)
  velocity: number; // px/s along the axis, from the last 80ms of samples
  dir: 1 | -1; // which way the gesture went
  commit: boolean; // fast enough toward dir, or past 40% of the extent
};

export type SwipeOptions = {
  axis: "x" | "y";
  /** Should this pointerdown be tracked at all (edge zone, scrollTop = 0, ...). */
  canStart?: (e: PointerEvent) => boolean;
  /** Primary-axis delta at the 10px axis lock; false hands the gesture to native scroll. */
  canLock?: (delta: number) => boolean;
  /** Offsets reachable without rubber band, e.g. [0, sheetHeight]. */
  range: () => [number, number];
  /** Distance the 40% commit rule is measured against. */
  extent: () => number;
  /** Element that moves; defaults to the element the listeners are on. */
  target?: () => HTMLElement | null;
  /** Rest offset when the gesture starts with nothing in flight (default 0). */
  rest?: () => number;
  onLock?: () => void;
  /** Called in rAF after each transform write. Visual companions only. */
  onMove?: (offset: number) => void;
  /** Returns the offset to settle to. */
  onRelease: (r: SwipeRelease) => number;
  /** Same timing as the settle, for companions (backdrop opacity, chevrons). */
  onSettleStart?: (from: number, to: number, velocityToward: number) => void;
  onSettled?: (to: number) => void;
};

const SLOP = 10;
const CLICK_SLOP = 8;
const WINDOW_MS = 80;

export function rubberBand(x: number, w: number) {
  return Math.sign(x) * (1 - 1 / ((Math.abs(x) * 0.55) / Math.max(1, w) + 1)) * w;
}

const tf = (axis: "x" | "y", v: number) => (axis === "x" ? `translate3d(${v}px,0,0)` : `translate3d(0,${v}px,0)`);

/**
 * Dash-style direct manipulation on Pointer Events. The element follows the finger
 * 1:1 after a 10px axis lock, rubber-bands past its range, and settles with the
 * release velocity (settle() in motion.ts). Cross-axis movement wins → the gesture is
 * released to native scroll. Pair it with CSS touch-action (pan-y for horizontal
 * swipers, pan-x or none for vertical sheets) instead of preventDefault.
 */
export function useSwipe(ref: RefObject<HTMLElement | null>, opts: SwipeOptions) {
  const o = useRef(opts);
  o.current = opts;

  useEffect(() => {
    const host = ref.current;
    if (!host) return;
    let anim: Animation | null = null;
    let suppressClick = false;
    let frame = 0;
    let pending = 0;
    type Track = { id: number; x0: number; y0: number; base: number; locked: boolean; offset: number; samples: { t: number; p: number }[] };
    let tr: Track | null = null;

    const el = () => o.current.target?.() ?? host;
    const axisOf = (e: PointerEvent) => (o.current.axis === "x" ? e.clientX : e.clientY);

    const write = () => {
      frame = 0;
      const t = el();
      if (!t) return;
      t.style.transform = tf(o.current.axis, pending);
      o.current.onMove?.(pending);
    };

    const clamp = (raw: number) => {
      const [lo, hi] = o.current.range();
      const w = o.current.axis === "x" ? window.innerWidth : window.innerHeight;
      if (raw > hi) return hi + rubberBand(raw - hi, w);
      if (raw < lo) return lo + rubberBand(raw - lo, w);
      return raw;
    };

    const finish = (target: number, offset: number, velocity: number) => {
      const t = el();
      if (!t) return;
      const distance = target - offset;
      const toward = distance === 0 ? 0 : velocity * Math.sign(distance);
      o.current.onSettleStart?.(offset, target, toward);
      anim = settle(t, tf(o.current.axis, offset), tf(o.current.axis, target), distance, toward);
      const done = () => {
        anim = null;
        t.style.willChange = "";
        o.current.onSettled?.(target);
      };
      if (anim) anim.addEventListener("finish", done);
      else done();
    };

    const onDown = (e: PointerEvent) => {
      suppressClick = false;
      if (e.pointerType === "mouse" && e.button !== 0) return;
      if (o.current.canStart && !o.current.canStart(e)) return;
      const t = el();
      if (!t) return;
      let base = o.current.rest?.() ?? 0;
      if (anim) {
        // regrab mid-flight: freeze where it visually is, then follow from there
        const now = currentTranslate(t);
        base = o.current.axis === "x" ? now.x : now.y;
        anim.cancel();
        anim = null;
        t.style.transform = tf(o.current.axis, base);
      }
      tr = { id: e.pointerId, x0: e.clientX, y0: e.clientY, base, locked: false, offset: base, samples: [{ t: e.timeStamp, p: axisOf(e) }] };
    };

    const onMove = (e: PointerEvent) => {
      if (!tr || e.pointerId !== tr.id) return;
      const dx = e.clientX - tr.x0;
      const dy = e.clientY - tr.y0;
      const primary = o.current.axis === "x" ? dx : dy;
      const cross = o.current.axis === "x" ? dy : dx;
      if (!tr.locked) {
        if (Math.max(Math.abs(dx), Math.abs(dy)) < SLOP) return;
        if (Math.abs(cross) > Math.abs(primary) || (o.current.canLock && !o.current.canLock(primary))) {
          tr = null; // native scroll wins
          return;
        }
        tr.locked = true;
        try {
          host.setPointerCapture(e.pointerId);
        } catch {
          /* pointer already gone */
        }
        const t = el();
        if (t) t.style.willChange = "transform";
        o.current.onLock?.();
      }
      if (e.cancelable) e.preventDefault();
      if (Math.abs(primary) > CLICK_SLOP) suppressClick = true;
      const travel = primary - Math.sign(primary) * SLOP;
      tr.offset = clamp(tr.base + travel);
      const p = axisOf(e);
      tr.samples.push({ t: e.timeStamp, p });
      while (tr.samples.length > 2 && e.timeStamp - tr.samples[0].t > WINDOW_MS) tr.samples.shift();
      pending = tr.offset;
      if (!frame) frame = requestAnimationFrame(write);
    };

    const onUp = (e: PointerEvent) => {
      if (!tr || e.pointerId !== tr.id) return;
      const t0 = tr;
      tr = null;
      if (!t0.locked) return;
      if (frame) {
        cancelAnimationFrame(frame);
        write();
      }
      try {
        host.releasePointerCapture(e.pointerId);
      } catch {
        /* already released */
      }
      const s = t0.samples;
      const first = s[0];
      const lastS = s[s.length - 1];
      const dt = Math.max(1, lastS.t - first.t);
      const velocity = ((lastS.p - first.p) / dt) * 1000;
      const moved = t0.offset - (o.current.rest?.() ?? 0);
      const dir: 1 | -1 = (moved !== 0 ? Math.sign(moved) : Math.sign(velocity) || 1) as 1 | -1;
      const commit = (Math.abs(velocity) > 500 && Math.sign(velocity) === dir) || Math.abs(moved) > 0.4 * o.current.extent();
      const target = o.current.onRelease({ offset: t0.offset, velocity, dir, commit });
      finish(target, t0.offset, velocity);
    };

    const onCancel = (e: PointerEvent) => {
      if (!tr || e.pointerId !== tr.id) return;
      const t0 = tr;
      tr = null;
      if (!t0.locked) return;
      if (frame) cancelAnimationFrame(frame);
      frame = 0;
      finish(t0.base, t0.offset, 0); // snap back, never commit
    };

    const onClick = (e: MouseEvent) => {
      if (!suppressClick) return;
      suppressClick = false;
      e.preventDefault();
      e.stopPropagation();
    };

    host.addEventListener("pointerdown", onDown, { passive: true });
    host.addEventListener("pointermove", onMove, { passive: false });
    host.addEventListener("pointerup", onUp, { passive: true });
    host.addEventListener("pointercancel", onCancel, { passive: true });
    host.addEventListener("click", onClick, true);
    return () => {
      host.removeEventListener("pointerdown", onDown);
      host.removeEventListener("pointermove", onMove);
      host.removeEventListener("pointerup", onUp);
      host.removeEventListener("pointercancel", onCancel);
      host.removeEventListener("click", onClick, true);
      if (frame) cancelAnimationFrame(frame);
      anim?.cancel();
    };
  }, [ref]);
}
