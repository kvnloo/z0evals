"use client";
import { useLayoutEffect, useRef, useState } from "react";

/**
 * Keep SSR/no-JS charts visible, but arm below-fold or hidden-tab charts before
 * paint and reveal them only when their real layout box approaches the viewport.
 * This also fixes charts mounted inside StoryShell's hidden Explore panel.
 */
export function useReveal<T extends HTMLElement>(
  threshold = 0.05,
  rootMargin = "160px 0px",
) {
  const ref = useRef<T>(null);
  const [shown, setShown] = useState(true);

  useLayoutEffect(() => {
    const node = ref.current;
    if (!node || typeof window === "undefined") return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setShown(true);
      return;
    }

    const rect = node.getBoundingClientRect();
    const hasLayoutBox = node.getClientRects().length > 0;
    const alreadyNearViewport =
      hasLayoutBox && rect.bottom >= -80 && rect.top <= window.innerHeight * 0.92;

    if (!alreadyNearViewport) setShown(false);

    const io = new IntersectionObserver(
      (entries) => {
        if (!entries[0]?.isIntersecting) return;
        setShown(true);
        io.disconnect();
      },
      { threshold, rootMargin },
    );
    io.observe(node);
    return () => io.disconnect();
  }, [threshold, rootMargin]);

  return { ref, shown };
}
