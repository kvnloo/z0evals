"use client";
import { useEffect, useState } from "react";

/** Scroll progress bar. requestAnimationFrame-throttled, like the reference. */
export default function RouteProgress() {
  const [pct, setPct] = useState(0);
  const [done, setDone] = useState(false);

  useEffect(() => {
    let frame = 0;
    const measure = () => {
      frame = 0;
      const doc = document.documentElement;
      const max = doc.scrollHeight - doc.clientHeight;
      const p = max > 0 ? Math.min(1, Math.max(0, doc.scrollTop / max)) : 0;
      setPct(p * 100);
      setDone(p > 0.995);
    };
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(measure);
    };
    measure();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      if (frame) cancelAnimationFrame(frame);
    };
  }, []);

  return (
    <div
      className={`route-progress${done ? " route-progress--done" : ""}`}
      style={{ width: `${pct}%` }}
      aria-hidden="true"
    />
  );
}
