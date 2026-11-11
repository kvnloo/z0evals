"use client";
import { reduced } from "./motion";

function paddingTop(): number {
  const v = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop);
  return Number.isFinite(v) ? v : 0;
}

/**
 * Programmatic anchor jump. The only smooth scrolling on the site: browser find and
 * history traversal stay instant. Lands the heading below the sticky bars, then makes
 * one silent correction if content-visibility sections resized on the way.
 */
export function scrollToId(id: string, opts: { push?: boolean; instant?: boolean } = {}) {
  const el = document.getElementById(id);
  if (!el) return;
  // content-visibility:auto sections only have placeholder heights until rendered. Once
  // the reader jumps, lay everything out (html.cv-all) and keep it that way, so the
  // target position is exact and nothing above it can change size afterwards.
  document.documentElement.classList.add("cv-all");
  const top = () => el.getBoundingClientRect().top + window.scrollY - paddingTop();
  const smooth = !opts.instant && !reduced();
  window.scrollTo({ top: top(), behavior: smooth ? "smooth" : "auto" });
  if (opts.push !== false && location.hash !== `#${id}`) history.pushState(null, "", `#${id}`);
  let fixed = false;
  const fix = () => {
    if (fixed) return;
    fixed = true;

    // late layout (charts mounting near the viewport, fonts) can move the target after
    // arrival: re-check for a few frames and correct silently until it holds still
    let tries = 0;
    const settleOn = () => {
      const t = top();
      if (Math.abs(t - window.scrollY) <= 2 || tries++ >= 6) return;
      window.scrollTo({ top: t, behavior: "auto" });
      requestAnimationFrame(() => requestAnimationFrame(settleOn));
    };
    settleOn();
  };
  if (smooth) {
    // correct only once the smooth scroll is idle: an instant scroll issued while the
    // smooth one is still animating gets added to it instead of replacing it
    let last = performance.now();
    const onScroll = () => {
      last = performance.now();
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    const done = () => {
      window.removeEventListener("scroll", onScroll);
      fix();
    };
    if ("onscrollend" in window) window.addEventListener("scrollend", done, { once: true });
    const started = performance.now();
    const idle = () => {
      if (fixed) return window.removeEventListener("scroll", onScroll);
      if (performance.now() - last > 250 || performance.now() - started > 5000) done();
      else window.setTimeout(idle, 150);
    };
    window.setTimeout(idle, 400);
  } else {
    requestAnimationFrame(() => requestAnimationFrame(fix));
  }
}
