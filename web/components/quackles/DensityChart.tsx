"use client";

import { useState } from "react";

type Density = { theme: string; source: string; d201: number; d1gp: number };

/**
 * Texels per final pixel, log scale. Toggle the output size and watch every
 * bar slide left by the same 2.23×: the pixels went up, the source did not.
 */
export default function DensityChart({
  rows,
  minimum,
  preferred,
}: {
  rows: Density[];
  minimum: number;
  preferred: number;
}) {
  const [scale, setScale] = useState<"d201" | "d1gp">("d1gp");
  const lo = Math.log10(0.02);
  const hi = Math.log10(4);
  const x = (v: number) => ((Math.log10(v) - lo) / (hi - lo)) * 100;
  const sorted = [...rows].sort((a, b) => a.d1gp - b.d1gp);
  const below = rows.filter((r) => r[scale] < minimum).length;
  return (
    <div className="qk-density">
      <div className="es-controls">
        <button type="button" className="es-btn" aria-pressed={scale === "d201"} onClick={() => setScale("d201")}>
          201 MP output
        </button>
        <button type="button" className="es-btn" aria-pressed={scale === "d1gp"} onClick={() => setScale("d1gp")}>
          1 GP output
        </button>
        <span className="es-readout">
          {below} of {rows.length} sources under {minimum} texel per pixel
        </span>
      </div>
      <div className="qk-dens-plot" role="table" aria-label="texels per pixel by source">
        <div className="qk-dens-overlay" aria-hidden>
          <div className="qk-dens-rule" style={{ left: `${x(minimum)}%` }}>
            <span>minimum {minimum}</span>
          </div>
          <div className="qk-dens-rule pref" style={{ left: `${x(preferred)}%` }}>
            <span>preferred {preferred}</span>
          </div>
          <div className="qk-dens-axis">
            {[0.03, 0.1, 0.3, 1, 3].map((t) => (
              <span key={t} style={{ left: `${x(t)}%` }}>
                {t}
              </span>
            ))}
          </div>
        </div>
        {sorted.map((r) => {
          const v = r[scale];
          return (
            <div key={r.theme + r.source} className="qk-dens-row" role="row">
              <span className="qk-dens-name" role="cell">
                <i data-theme={r.theme}>{r.theme}</i> {r.source}
              </span>
              <span className="qk-dens-track" role="cell">
                <span className="qk-dens-bar" data-ok={v >= minimum} style={{ width: `${x(v)}%` }} />
                <span className="qk-dens-v" style={{ left: `${x(v)}%` }}>
                  {v.toFixed(3)}
                </span>
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
