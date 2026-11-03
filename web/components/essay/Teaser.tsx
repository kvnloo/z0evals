"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

export type TeaserPanel = {
  step: string;
  task: ReactNode;
  visual: ReactNode;
  by: ReactNode;
  big: ReactNode;
  note: ReactNode;
};

/** Three (or so) panels above the fold: what was asked, what happened, the number. */
export default function Teaser({ panels, label }: { panels: TeaserPanel[]; label?: string }) {
  return (
    <figure className="es-teaser-fig es-wide" aria-label={label ?? "the result in brief"}>
      <div className="es-teaser" style={{ ["--es-cols" as string]: panels.length }}>
        {panels.map((p, i) => (
          <div className="es-tz-panel" key={i}>
            <div className="es-tz-step">{p.step}</div>
            <div className="es-tz-task">{p.task}</div>
            <div className="es-tz-vis">{p.visual}</div>
            <div className="es-tz-by">{p.by}</div>
            <div className="es-tz-out">
              <span className="es-tz-big">{p.big}</span> <span className="es-tz-note">{p.note}</span>
            </div>
          </div>
        ))}
      </div>
    </figure>
  );
}

/**
 * Before/after bars. The "after" bar starts at the "before" value and counts up
 * the first time the figure is on screen, so the reader sees the move rather
 * than two static heights. Reduced motion shows the final state.
 */
export function GrowBars({
  from,
  to,
  max,
  labels,
  digits = 1,
  suffix = "",
  scale = 1,
  offset = 0,
}: {
  from: number;
  to: number;
  max: number;
  labels: [string, string];
  /** decimals shown while counting; plain values so a server page can pass them */
  digits?: number;
  suffix?: string;
  /** label shows v * scale + offset, e.g. bytes as kb, or a bar that starts at a floor */
  scale?: number;
  offset?: number;
}) {
  const format = (v: number) =>
    `${(v * scale + offset).toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits })}${suffix}`;
  const ref = useRef<HTMLDivElement>(null);
  const [v, setV] = useState(to);
  useEffect(() => {
    const node = ref.current;
    if (!node || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    setV(from);
    let raf = 0;
    const io = new IntersectionObserver(
      (es) => {
        if (!es[0]?.isIntersecting) return;
        io.disconnect();
        const t0 = performance.now() + 400;
        const tick = (now: number) => {
          const k = Math.max(0, Math.min(1, (now - t0) / 1400));
          setV(from + (to - from) * (1 - (1 - k) ** 3));
          if (k < 1) raf = requestAnimationFrame(tick);
        };
        raf = requestAnimationFrame(tick);
      },
      { threshold: 0.4 },
    );
    io.observe(node);
    return () => {
      io.disconnect();
      cancelAnimationFrame(raf);
    };
  }, [from, to]);
  const h = (x: number) => `${Math.max(2, (x / max) * 100)}%`;
  return (
    <div className="es-bars" ref={ref}>
      <div className="es-bar-col">
        <div className="es-bar es-bar-before" style={{ height: h(from) }}>
          <span>{format(from)}</span>
        </div>
        <div className="es-bar-l">{labels[0]}</div>
      </div>
      <div className="es-bar-col">
        <div className="es-bar es-bar-after" style={{ height: h(v) }}>
          <span>{format(v)}</span>
        </div>
        <div className="es-bar-l">{labels[1]}</div>
      </div>
    </div>
  );
}
