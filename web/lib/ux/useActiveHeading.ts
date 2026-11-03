"use client";
import { useEffect, useState } from "react";

/**
 * The heading currently being read: the last heading whose top has crossed the top third
 * of the viewport. Recomputed in rAF on scroll and resize, so fast flings, jumps and
 * scrolling back up all land on the right heading. Passive: it never scrolls and never
 * fires haptics.
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
    let frame = 0;
    const update = () => {
      frame = 0;
      const line = window.innerHeight / 3;
      let current = targets[0].id;
      for (const t of targets) {
        if (t.getBoundingClientRect().top <= line) current = t.id;
        else break;
      }
      setActive(current);
    };
    const schedule = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    return () => {
      if (frame) cancelAnimationFrame(frame);
      window.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
    };
  }, [key]);
  return active;
}
