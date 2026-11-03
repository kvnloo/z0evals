"use client";

import { useEffect, useRef, useState } from "react";
import { useSwipe } from "@/lib/ux/gesture";
import { follow } from "@/lib/ux/motion";
import { haptic } from "@/lib/ux/haptics";

const EDGE = 20;
const MAX = 0.35;

/**
 * Left-edge swipe back for touch screens. A 20px pan-y strip on the left edge: the page
 * follows the finger (up to 35% of the width, rubber band beyond), a chevron fades in,
 * crossing the commit threshold ticks once, release commits by velocity or distance.
 * Skipped on iOS Safari, which already owns this gesture natively.
 */
export default function EdgeBack() {
  const [on, setOn] = useState(false);
  const zone = useRef<HTMLDivElement>(null);
  const chev = useRef<HTMLDivElement>(null);
  const crossed = useRef(false);
  const extent = () => window.innerWidth * MAX;

  useEffect(() => {
    const nav = navigator as Navigator & { standalone?: boolean };
    const iosSafari = /iP(hone|ad)/.test(nav.userAgent) && nav.standalone !== true;
    setOn(!iosSafari && matchMedia("(pointer: coarse)").matches);
    const reset = () => {
      const main = document.getElementById("main");
      if (main) {
        main.getAnimations().forEach((a) => a.cancel());
        main.style.transform = "";
        main.style.willChange = "";
      }
    };
    window.addEventListener("pageshow", reset);
    window.addEventListener("popstate", reset);
    return () => {
      window.removeEventListener("pageshow", reset);
      window.removeEventListener("popstate", reset);
      reset();
    };
  }, []);

  useSwipe(zone, {
    axis: "x",
    target: () => document.getElementById("main"),
    canStart: (e) => e.pointerType !== "mouse" && e.clientX <= EDGE + 4,
    canLock: (dx) => dx > 0,
    range: () => [0, extent()],
    extent,
    onLock: () => {
      crossed.current = false;
    },
    onMove: (x) => {
      const p = Math.min(1, x / extent());
      if (chev.current) chev.current.style.opacity = String(p);
      const past = x > 0.4 * extent();
      if (past !== crossed.current) {
        crossed.current = past;
        if (past) haptic.select();
      }
    },
    onRelease: ({ commit, dir }) => {
      if (commit && dir === 1) {
        haptic.tap();
        return extent();
      }
      return 0;
    },
    onSettleStart: (from, to, v) => {
      if (chev.current) follow(chev.current, "opacity", Math.min(1, from / extent()), to > 0 ? 1 : 0, to - from, v);
    },
    onSettled: (to) => {
      if (to <= 0) return;
      if (history.length > 1) history.back();
      else location.href = `${process.env.NEXT_PUBLIC_BASE_PATH ?? ""}/research/`;
    },
  });

  return (
    <>
      <div ref={zone} className="edge-back-zone" hidden={!on} aria-hidden="true" />
      <div ref={chev} className="edge-back-chev" hidden={!on} aria-hidden="true">‹</div>
    </>
  );
}
