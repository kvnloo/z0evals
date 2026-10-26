// Dash haptics for the web. Only call these from user-activation handlers (pointerup,
// click, keydown) or on a discrete boundary crossed during an active drag; never from
// scroll, IntersectionObserver or effects. iOS Safari has no vibrate(): a silent no-op.
const P = { tap: 10, select: 5, success: [8, 40, 12], error: [20, 40, 20, 40, 30] } as const;
let last = 0;

function vib(p: number | readonly number[]) {
  try {
    const now = performance.now();
    if (now - last < 40) return;
    last = now;
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    (navigator as Navigator & { vibrate?: (p: number | number[]) => boolean }).vibrate?.(p as number | number[]);
  } catch {
    // vibration is a garnish; never let it break an interaction
  }
}

export type HapticKind = "tap" | "select" | "success" | "error";
export const haptic: Record<HapticKind, () => void> = {
  tap: () => vib(P.tap),
  select: () => vib(P.select),
  success: () => vib(P.success),
  error: () => vib(P.error),
};
