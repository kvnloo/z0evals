"use client";
import { useEffect, useLayoutEffect, useRef, useState } from "react";

/**
 * Progressive enhancement for chart marks.
 *
 * Server render is VISIBLE, so the figure is readable with no JavaScript.
 * After hydration a mark that starts below the fold is hidden before first paint
 * and revealed on scroll. Entry animation without ever shipping a blank chart.
 */
export function useReveal<T extends HTMLElement>(threshold = 0.25) {
  const ref = useRef<T>(null);
  const [shown, setShown] = useState(true);
  const [armed, setArmed] = useState(false);

  useLayoutEffect(() => {
    const node = ref.current;
    if (!node || typeof window === "undefined") return;
    if (node.getBoundingClientRect().top > window.innerHeight * 0.92) {
      setShown(false);
      setArmed(true);
    }
  }, []);

  useEffect(() => {
    if (!armed) return;
    const node = ref.current;
    if (!node) return;
    const io = new IntersectionObserver(
      (e) => { if (e[0]?.isIntersecting) { setShown(true); io.disconnect(); } },
      { threshold }
    );
    io.observe(node);
    return () => io.disconnect();
  }, [armed, threshold]);

  return { ref, shown };
}
