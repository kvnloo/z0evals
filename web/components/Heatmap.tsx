"use client";
import { useState } from "react";
import type { Matrix } from "@/data/types";

type Metric = "success" | "dangerous" | "split";

/**
 * The probability/outcome matrix: states × arms, exactly as the reference's
 * message-by-message heatmap. One cell per (state, arm) cell we actually measured.
 */
export default function Heatmap({ matrix }: { matrix: Matrix }) {
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
    if (v == null) return "#f7f7f7";
    if (metric === "dangerous") return v > 0 ? "#b91c1c" : "#eef5f1";
    if (metric === "split") return v > 0 ? "#b45309" : "#eef5f1";
    if (v === 0) return "#b91c1c";
    if (v === 1) return "#29916e";
    return v < 0.5 ? "#d97706" : "#6aa88f";
  };

  return (
    <div>
      <div className="chart-tabs">
        {(["success", "dangerous", "split"] as Metric[]).map((m) => (
          <button key={m} type="button" aria-pressed={metric === m} onClick={() => setMetric(m)}>
            {m === "success" ? "success rate" : m === "dangerous" ? "dangerous selected" : "repetition split"}
          </button>
        ))}
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg" role="img"
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
                  fill={a.unfiltered ? "#b91c1c" : "#3c3836"}>{a.label}</text>
            {states.map((s, si) => {
              const v = value(si, ai);
              return (
                <rect key={s.id} className="mark" x={L + si * cellW + 1} y={T + ai * cellH + 1}
                      width={cellW - 2} height={cellH - 2} rx="2" fill={fill(v)}>
                  <title>{`${s.id} · ${a.label} · ${v == null ? "not measured" : metric === "success" ? `${(v * 100).toFixed(0)}%` : v > 0 ? "yes" : "no"}`}</title>
                </rect>
              );
            })}
          </g>
        ))}
        <text x={L} y={H - 2} fontSize="10.5" fill="#888">{states.length} states × {arms.length} arms</text>
      </svg>
      <div className="legend">
        {metric === "success" ? (
          <>
            <span><i className="swatch" style={{ background: "#29916e" }} />all repetitions correct</span>
            <span><i className="swatch" style={{ background: "#d97706" }} />minority correct</span>
            <span><i className="swatch" style={{ background: "#b91c1c" }} />all wrong</span>
          </>
        ) : metric === "dangerous" ? (
          <>
            <span><i className="swatch" style={{ background: "#b91c1c" }} />selected a dangerous action</span>
            <span><i className="swatch" style={{ background: "#eef5f1" }} />never did</span>
          </>
        ) : (
          <>
            <span><i className="swatch" style={{ background: "#b45309" }} />repetitions disagreed</span>
            <span><i className="swatch" style={{ background: "#eef5f1" }} />stable across all 3</span>
          </>
        )}
        <span>grey = not measured</span>
      </div>
    </div>
  );
}
