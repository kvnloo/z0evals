"use client";

// Scrubbable version of the trajectory figure. Every value it draws or prints
// comes from the frozen turns the page passes in; nothing is interpolated.
import { useRef, useState, type KeyboardEvent, type PointerEvent } from "react";
import { GrowBars } from "@/components/essay/Essay";

export type Turn = {
  turn: number;
  file: string;
  messages: number;
  raw_bytes: number;
  view_bytes: number;
  built: number;
  placeholders: number;
};

type Mode = "bytes" | "ratio";

const W = 640, H = 300, L = 72, R = 18, T = 18, B = 44;
const fmt = (v: number) => new Intl.NumberFormat("en-US").format(v);
const pct = (r: Turn) => (100 * r.view_bytes) / r.raw_bytes;

export default function TrajectoryChart({ turns }: { turns: Turn[] }) {
  const [i, setI] = useState(turns.length - 1);
  const [mode, setMode] = useState<Mode>("bytes");
  const svg = useRef<SVGSVGElement>(null);
  const n = turns.length;
  const clamp = (k: number) => Math.max(0, Math.min(n - 1, k));

  const x = (k: number) => L + (k / Math.max(1, n - 1)) * (W - L - R);
  const maxBytes = Math.max(...turns.map((r) => r.raw_bytes), ...turns.map((r) => r.view_bytes));
  const maxPct = Math.max(...turns.map(pct));
  const top = mode === "bytes" ? maxBytes : maxPct;
  const y = (v: number) => H - B - (v / top) * (H - T - B);
  const line = (f: (r: Turn) => number) => turns.map((r, k) => `${x(k)},${y(f(r))}`).join(" ");

  const fromPointer = (e: PointerEvent<SVGSVGElement>) => {
    const box = svg.current?.getBoundingClientRect();
    if (!box || box.width === 0) return;
    const vx = ((e.clientX - box.left) / box.width) * W;
    setI(clamp(Math.round(((vx - L) / (W - L - R)) * (n - 1))));
  };
  const onKey = (e: KeyboardEvent) => {
    const step: Record<string, number> = { ArrowRight: 1, ArrowUp: 1, ArrowLeft: -1, ArrowDown: -1 };
    if (e.key in step) setI((k) => clamp(k + step[e.key]));
    else if (e.key === "Home") setI(0);
    else if (e.key === "End") setI(n - 1);
    else return;
    e.preventDefault();
  };

  const row = turns[i];
  const ticks = [0, top / 2, top];
  return (
    <div className="oc-chart">
      <div className="es-controls" role="group" aria-label="chart scale">
        <button type="button" className="es-btn" aria-pressed={mode === "bytes"} onClick={() => setMode("bytes")}>
          bytes
        </button>
        <button type="button" className="es-btn" aria-pressed={mode === "ratio"} onClick={() => setMode("ratio")}>
          view / raw
        </button>
        <span className="es-readout">drag across the chart, or focus it and use the arrow keys</span>
      </div>
      <svg
        ref={svg}
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        tabIndex={0}
        aria-labelledby="trajectory-title trajectory-description"
        onPointerMove={fromPointer}
        onPointerDown={fromPointer}
        onKeyDown={onKey}
      >
        <title id="trajectory-title">accumulated transcript and optchat view, in bytes</title>
        <desc id="trajectory-description">
          {n} recorded turns. the solid line is the raw transcript; the dashed line is the view. all
          measurements are available in the table below.
        </desc>
        <path d={`M${L},${T}V${H - B}H${W - R}`} fill="none" stroke="currentColor" opacity="0.35" />
        {ticks.map((v) => (
          <g key={v}>
            <line x1={L} x2={W - R} y1={y(v)} y2={y(v)} stroke="currentColor" opacity="0.12" />
            <text x={L - 8} y={y(v) + 4} textAnchor="end" fill="currentColor" fontSize="12">
              {mode === "bytes" ? `${fmt(Math.round(v / 1000))} kb` : `${v.toFixed(1)}%`}
            </text>
          </g>
        ))}
        {mode === "bytes" ? (
          <>
            <polyline points={line((r) => r.raw_bytes)} className="oc-raw" />
            <polyline points={line((r) => r.view_bytes)} className="oc-view" />
          </>
        ) : (
          <polyline points={line(pct)} className="oc-view" />
        )}
        <line x1={x(i)} x2={x(i)} y1={T} y2={H - B} className="oc-guide" />
        {mode === "bytes" ? (
          <>
            <circle cx={x(i)} cy={y(row.raw_bytes)} r="4" className="oc-dot-raw" />
            <circle cx={x(i)} cy={y(row.view_bytes)} r="4" className="oc-dot-view" />
          </>
        ) : (
          <circle cx={x(i)} cy={y(pct(row))} r="4" className="oc-dot-view" />
        )}
        {[0, n - 1].map((k) => (
          <text key={k} x={x(k)} y={H - 20} textAnchor={k === 0 ? "start" : "end"} fill="currentColor" fontSize="12">
            turn {turns[k].turn}
          </text>
        ))}
      </svg>
      <input
        className="es-range"
        type="range"
        min={1}
        max={n}
        value={i + 1}
        aria-label="turn"
        onChange={(e) => setI(clamp(Number(e.target.value) - 1))}
      />
      <div className="oc-readout es-readout" aria-live="polite">
        <span><b>turn {row.turn}</b> of {n}</span>
        <span>raw {fmt(row.raw_bytes)} b</span>
        <span>view {fmt(row.view_bytes)} b</span>
        <span>view / raw {pct(row).toFixed(2)}%</span>
        <span>{fmt(row.messages)} messages</span>
        <span>{row.placeholders} placeholders</span>
        <span className="oc-file">{row.file}</span>
      </div>
    </div>
  );
}

/** GrowBars in kilobytes. */
export function KbBars({ from, to, labels }: { from: number; to: number; labels: [string, string] }) {
  return <GrowBars from={from} to={to} max={to} labels={labels} digits={0} scale={0.001} suffix=" kb" />;
}
