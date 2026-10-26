// Dash motion tokens for the web (Dash app/src/motion.ts). Fast first: motion confirms
// an action, it never gates it. Every animation here moves transform or opacity only.
export const MS = { press: 70, fade: 120, nav: 140, snap: 150, settle: 180 } as const;
export const EASE_CRIT = "cubic-bezier(.22,1,.36,1)";
export const PRESS = { row: 0.985, control: 0.92, nav: 0.9 } as const;

export const reduced = () =>
  typeof matchMedia !== "undefined" && matchMedia("(prefers-reduced-motion: reduce)").matches;

/** Normalised critically damped response: hard deadline, no energy tail. */
export function criticalProgress(t: number) {
  const k = 9;
  return (1 - (1 + k * t) * Math.exp(-k * t)) / (1 - (1 + k) * Math.exp(-k));
}

/** Release settle duration. velocity is px/s, signed so that > 0 points at the target. */
export function navDuration(distance: number, velocity: number) {
  if (reduced()) return 0;
  if (velocity <= 0) return MS.nav;
  return Math.min(140, Math.max(80, Math.abs(distance / velocity) * 1000));
}

/** Monotone Hermite settle that keeps the release velocity unless it would overshoot. */
export function hermiteEasing(distance: number, velocity: number, durMs: number): string {
  const s = Math.min(3, Math.max(0, (velocity * durMs) / (1000 * Math.max(1, Math.abs(distance)))));
  const pts = Array.from({ length: 17 }, (_, i) => {
    const t = i / 16;
    return ((s - 2) * t ** 3 + (3 - 2 * s) * t ** 2 + s * t).toFixed(4);
  });
  return typeof CSS !== "undefined" && CSS.supports("animation-timing-function", "linear(0, 1)")
    ? `linear(${pts.join(",")})`
    : EASE_CRIT;
}

/**
 * Settle a dragged element from `from` to `to` (CSS transform strings). Returns the
 * running Animation so a new pointerdown can cancel it and regrab mid-flight, or null
 * when the move was applied instantly (reduced motion or zero distance).
 */
export function settle(el: HTMLElement, from: string, to: string, distance: number, velocity: number): Animation | null {
  const duration = navDuration(distance, velocity);
  if (!duration || !distance || typeof el.animate !== "function") {
    el.style.transform = to;
    return null;
  }
  const anim = el.animate([{ transform: from }, { transform: to }], {
    duration,
    easing: hermiteEasing(distance, Math.max(0, velocity), duration),
    fill: "forwards",
  });
  anim.addEventListener("finish", () => {
    el.style.transform = to;
    anim.cancel();
  });
  return anim;
}

/** Same timing as settle() for a companion property (e.g. a backdrop's opacity). */
export function follow(el: HTMLElement, prop: "opacity", from: number, to: number, distance: number, velocity: number) {
  const duration = navDuration(distance, velocity);
  if (!duration || typeof el.animate !== "function") {
    el.style[prop] = String(to);
    return null;
  }
  const anim = el.animate([{ [prop]: from }, { [prop]: to }], {
    duration,
    easing: hermiteEasing(distance, Math.max(0, velocity), duration),
    fill: "forwards",
  });
  anim.addEventListener("finish", () => {
    el.style[prop] = String(to);
    anim.cancel();
  });
  return anim;
}

/** Current translate of an element, read from its computed matrix (mid-animation safe). */
export function currentTranslate(el: HTMLElement): { x: number; y: number } {
  const t = getComputedStyle(el).transform;
  if (!t || t === "none") return { x: 0, y: 0 };
  const m = new DOMMatrixReadOnly(t);
  return { x: m.m41, y: m.m42 };
}
