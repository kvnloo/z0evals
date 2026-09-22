"use client";
import { useState } from "react";
import type { Arm } from "@/data/types";
import { fmtMs, fmtPct, log10, logTicks, linear } from "./util";
import { useReveal } from "./useReveal";

const W = 820, H = 400, L = 54, R = 118, T = 18, B = 54;

/** Success vs warm latency with Wilson intervals. The Pareto frontier is the argument. */
export default function ArmScatter({ arms }: { arms: Arm[] }) {
  const { ref, shown } = useReveal<HTMLDivElement>();
  const [hover, setHover] = useState<{ x: number; y: number; arm: Arm } | null>(null);

  const lats = arms.map((a) => a.warmP50Ms).filter((v): v is number => v != null);
  const x = log10([Math.min(...lats) * 0.72, Math.max(...lats) * 1.3], [L, W - R]);
  const y = linear([0.45, 0.99], [H - B, T]);
  const innerW = W - L - R, innerH = H - T - B;
  const lat = (a: Arm) => a.warmP50Ms ?? Math.min(...lats);

  const sorted = arms.filter((a) => a.warmP50Ms != null)
    .sort((a, b) => (a.warmP50Ms! - b.warmP50Ms!));
  const front: Arm[] = [];
  let best = -1;
  for (const a of sorted) if (a.successRate > best) { front.push(a); best = a.successRate; }

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg" role="img"
           aria-label="Success rate against warm median latency, with Wilson 95% intervals">
        {logTicks(Math.min(...lats), Math.max(...lats)).map((t) => (
          <g key={t}>
            <line className="grid" x1={x(t)} x2={x(t)} y1={T} y2={H - B} />
            <text x={x(t)} y={H - B + 18} textAnchor="middle" fontSize="10.5" fill="#888">{fmtMs(t)}</text>
          </g>
        ))}
        {[0.5, 0.6, 0.7, 0.8, 0.9].map((t) => (
          <g key={t}>
            <line className="grid" x1={L} x2={W - R} y1={y(t)} y2={y(t)} />
            <text x={L - 9} y={y(t) + 3.5} textAnchor="end" fontSize="10.5" fill="#888">
              {Math.round(t * 100)}%
            </text>
          </g>
        ))}
        <line className="axis" x1={L} x2={W - R} y1={H - B} y2={H - B} />
        <line className="axis" x1={L} x2={L} y1={T} y2={H - B} />
        <text x={L + innerW / 2} y={H - 8} textAnchor="middle" fontSize="11.5" fill="#676767">
          warm p50 latency (log)
        </text>
        <text transform={`translate(13 ${T + innerH / 2}) rotate(-90)`} textAnchor="middle"
              fontSize="11.5" fill="#676767">bounded-choice success</text>

        <polyline fill="none" stroke="#1a3029" strokeWidth="1.25" strokeDasharray="3 3"
                  points={front.map((a) => `${x(a.warmP50Ms!)},${y(a.successRate)}`).join(" ")}
                  style={{ opacity: shown ? 0.5 : 0, transition: "opacity .5s ease .15s" }} />

        {arms.map((a, i) => {
          const cx = x(lat(a)), cy = y(a.successRate);
          const [lo, hi] = a.wilson95;
          const stroke = a.unfiltered ? "#b91c1c" : "#29916e";
          return (
            <g key={a.id} className="mark"
               onMouseEnter={() => setHover({ x: cx, y: cy, arm: a })}
               onMouseLeave={() => setHover(null)}
               style={{ opacity: shown ? 1 : 0, transition: `opacity .45s ease ${i * 55}ms` }}>
              <line x1={cx} x2={cx} y1={y(lo)} y2={y(hi)} stroke={stroke} strokeWidth="1" opacity="0.4" />
              <line x1={cx - 4} x2={cx + 4} y1={y(lo)} y2={y(lo)} stroke={stroke} strokeWidth="1" opacity="0.5" />
              <line x1={cx - 4} x2={cx + 4} y1={y(hi)} y2={y(hi)} stroke={stroke} strokeWidth="1" opacity="0.5" />
              <circle cx={cx} cy={cy} r={a.unfiltered ? 7 : 5.5} fill={stroke} stroke="#fff" strokeWidth="1.5" />
              <text x={cx + 11} y={cy + 3.5} fontSize="11" fill="#3c3836">{a.label}</text>
            </g>
          );
        })}
      </svg>
      {hover ? (
        <div className="tooltip" style={{ left: `${(hover.x / W) * 100}%`, top: `${(hover.y / H) * 100}%`,
                                          transform: "translate(10px,-120%)" }}>
          {hover.arm.label} · {fmtPct(hover.arm.successRate)} · {fmtMs(lat(hover.arm))} · n={hover.arm.n}
        </div>
      ) : null}
      <div className="legend">
        <span><i className="swatch" style={{ background: "#29916e" }} />compiler-first</span>
        <span><i className="swatch" style={{ background: "#b91c1c" }} />unfiltered control</span>
        <span><i className="swatch" style={{ background: "#1a3029" }} />Pareto frontier</span>
      </div>
    </div>
  );
}
