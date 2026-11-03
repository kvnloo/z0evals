"use client";
import { useEffect, useState } from "react";

/**
 * The heading currently being read, from one IntersectionObserver (the reference's
 * rootMargin: a heading becomes active as it crosses the top third of the viewport).
 * Passive: it never scrolls and never fires haptics.
 */
export function useActiveHeading(ids: string[]): string {
  const [active, setActive] = useState<string>(ids[0] ?? "");
  const key = ids.join("|");
  useEffect(() => {
    const targets = key
      .split("|")
      .map((id) => document.getElementById(id))
      .filter((el): el is HTMLElement => Boolean(el));
    if (!targets.length) return;
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) if (e.isIntersecting) setActive(e.target.id);
      },
      { rootMargin: "-100px 0px -66% 0px" },
    );
    targets.forEach((t) => io.observe(t));
    return () => io.disconnect();
  }, [key]);
  return active;
}
