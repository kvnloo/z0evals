"use client";
import { useState } from "react";
import { useReveal } from "./charts/useReveal";
import type { Matrix } from "@/data/types";

type Metric = "success" | "dangerous" | "split";

/**
 * The probability/outcome matrix: states × arms, exactly as the reference's
 * message-by-message heatmap. One cell per (state, arm) cell we actually measured.
 */
export default function Heatmap({ matrix }: { matrix: Matrix }) {
  const { ref, shown } = useReveal<HTMLDivElement>(0.05);
  const [metric, setMetric] = useState<Metric>("success");
  const arms = matrix.arms;
  const states = matrix.states;

  const cellW = 30, cellH = 17, L = 176, T = 96, R = 86;
  const W = L + states.length * cellW + R;
  const H = T + arms.length * cellH + 16;

  const value = (si: number, ai: number) => {
    const st = states[si].arms[arms[ai].id];
    if (!st) return null;
    if (metric === "success") return st.successRate;
    if (metric === "dangerous") return st.runs.some((r) => r.dangerous) ? 1 : 0;
    return st.unanimous ? 0 : 1;
  };

  const fill = (v: number | null) => {
    if (v == null) return "rgba(236,232,223,0.04)";
    if (metric === "dangerous") return v > 0 ? "#e37f65" : "rgba(215,185,134,0.10)";
    if (metric === "split") return v > 0 ? "#e7a875" : "rgba(215,185,134,0.10)";
    if (v === 0) return "#e37f65";
    if (v === 1) return "#d7b986";
    return v < 0.5 ? "#e7a875" : "#98cf8b";
  };

  return (
    <div ref={ref}>
      <div className="chart-tabs">
        {(["success", "dangerous", "split"] as Metric[]).map((m) => (
          <button key={m} type="button" aria-pressed={metric === m} onClick={() => setMetric(m)}>
            {m === "success" ? "success rate" : m === "dangerous" ? "dangerous selected" : "repetition split"}
          </button>
        ))}
      </div>
      <div className="heatmap-scroll">
        <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg heatmap-svg" role="img"
             aria-label="outcome matrix of states against arms">
        {states.map((s, si) => (
          <text key={s.id} x={L + si * cellW + cellW / 2} y={T - 10}
                fontSize="9" fill="#888" textAnchor="end"
                transform={`rotate(-90 ${L + si * cellW + cellW / 2} ${T - 10})`}
                style={{ fontFamily: "var(--font-mono)" }}>
            {s.id.length > 20 ? s.id.slice(0, 19) + "…" : s.id}
          </text>
        ))}
        {arms.map((a, ai) => (
          <g key={a.id}>
            <text x={L - 10} y={T + ai * cellH + 12} textAnchor="end" fontSize="11"
                  fill={a.unfiltered ? "#e37f65" : "#B4AFA3"}>{a.label}</text>
            {states.map((s, si) => {
              const v = value(si, ai);
              return (
                <rect key={s.id} className="mark" x={L + si * cellW + 1} y={T + ai * cellH + 1}
                      width={cellW - 2} height={cellH - 2} rx="2" fill={fill(v)}
                      style={{
                        opacity: shown ? 1 : 0,
                        transition: `opacity .28s ease ${Math.min(ai * states.length + si, 90) * 5}ms`,
                      }}>
                  <title>{`${s.id} · ${a.label} · ${v == null ? "not measured" : metric === "success" ? `${(v * 100).toFixed(0)}%` : v > 0 ? "yes" : "no"}`}</title>
                </rect>
              );
            })}
          </g>
        ))}
          <text x={L} y={H - 2} fontSize="10.5" fill="#888">{states.length} states × {arms.length} arms</text>
        </svg>
      </div>
      <div className="legend">
        {metric === "success" ? (
          <>
            <span><i className="swatch" style={{ background: "#d7b986" }} />all repetitions correct</span>
            <span><i className="swatch" style={{ background: "#e7a875" }} />minority correct</span>
            <span><i className="swatch" style={{ background: "#e37f65" }} />all wrong</span>
          </>
        ) : metric === "dangerous" ? (
          <>
            <span><i className="swatch" style={{ background: "#e37f65" }} />selected a dangerous action</span>
            <span><i className="swatch" style={{ background: "rgba(215,185,134,0.10)" }} />never did</span>
          </>
        ) : (
          <>
            <span><i className="swatch" style={{ background: "#e7a875" }} />repetitions disagreed</span>
            <span><i className="swatch" style={{ background: "rgba(215,185,134,0.10)" }} />stable across all 3</span>
          </>
        )}
        <span>grey = not measured</span>
      </div>
    </div>
  );
}
