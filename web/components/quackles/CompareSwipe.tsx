"use client";

import { useState } from "react";
import { asset } from "@/lib/asset";
import type { Plate } from "./types";
import { THEME_LABEL } from "./types";

/** Reference on the left of the handle, the agent's pick on the right. */
export default function CompareSwipe({
  themes,
  references,
  current,
}: {
  themes: string[];
  references: Record<string, Plate>;
  current: Record<string, Plate>;
}) {
  const [theme, setTheme] = useState(themes[themes.length - 1]);
  const [x, setX] = useState(50);
  const ref = references[theme];
  const cur = current[theme];
  return (
    <div className="qk-swipe-wrap">
      <div className="es-controls" role="tablist" aria-label="scene">
        {themes.map((t) => (
          <button key={t} type="button" role="tab" className="es-btn" aria-selected={t === theme} onClick={() => setTheme(t)}>
            {THEME_LABEL[t]}
          </button>
        ))}
      </div>
      <div className="qk-swipe" style={{ aspectRatio: `${ref.w} / ${ref.h}` }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={asset(cur.src)} alt={`${cur.caption}, the agent pick in the 2026-10-15 snapshot`} />
        <div className="qk-swipe-top" style={{ clipPath: `inset(0 ${100 - x}% 0 0)` }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={asset(ref.src)} alt={ref.caption} />
        </div>
        <div className="qk-swipe-handle" style={{ left: `${x}%` }} aria-hidden />
        <span className="qk-swipe-l">reference</span>
        <span className="qk-swipe-r">{cur.caption.split(" · ")[1]}</span>
        <input
          className="qk-swipe-range"
          type="range"
          min={0}
          max={100}
          value={x}
          aria-label="reveal the reference"
          onChange={(e) => setX(+e.target.value)}
        />
      </div>
    </div>
  );
}
