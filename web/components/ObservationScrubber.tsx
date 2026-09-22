"use client";
import { useState } from "react";
import type { Matrix } from "@/data/types";

/**
 * Observe-one-state control. Mirrors the reference's event scrubber, including
 * the aria-valuetext readout, and shows the underlying evidence for the frame.
 */
export default function ObservationScrubber({ matrix }: { matrix: Matrix }) {
  const [i, setI] = useState(0);
  const states = matrix.states;
  const s = states[i];
  const arms = matrix.armOrder.filter((a) => s.arms[a]);

  const correct = arms.filter((a) => s.arms[a].successRate === 1).length;
  const wrong = arms.filter((a) => s.arms[a].successRate === 0).length;
  const split = arms.length - correct - wrong;
  const summary = `${correct} correct · ${wrong} wrong · ${split} split`;

  return (
    <div>
      <div className="chart-tabs" style={{ alignItems: "center", gap: 10 }}>
        <span style={{ fontSize: 12.5, fontFamily: "var(--font-mono)", color: "var(--color-sb-text-muted)" }}>
          state {i + 1} of {states.length}
        </span>
        <span style={{ fontSize: 12.5, color: "var(--color-sb-text-muted)" }}>
          {s.id} · <strong style={{ color: "var(--color-sb-secondary)" }}>{s.family}</strong>
          {" · "}{s.legalCount} legal actions
          {s.deterministicSolution ? ` · compiler solved it (${s.deterministicSolution})` : ""}
        </span>
      </div>

      <div className="scrubRow">
        <span className="scrubLabel">Inspect</span>
        <input
          aria-label="Inspect one recorded event"
          aria-valuetext={`Event ${i + 1} of ${states.length}, ${s.family}, ${summary}`}
          type="range" min={0} max={states.length - 1} step={1} value={i}
          onChange={(e) => setI(Number(e.target.value))}
        />
        <span className="progressValue">{i + 1}/{states.length}</span>
      </div>

      <table className="data-table">
        <thead>
          <tr>
            <th>arm</th><th className="num">n</th><th className="num">success</th>
            <th className="num">p50</th><th className="num">confidence</th><th>selected</th>
          </tr>
        </thead>
        <tbody>
          {arms.map((a) => {
            const st = s.arms[a];
            const arm = matrix.arms.find((x) => x.id === a)!;
            const r0 = st.runs[0];
            const rate = st.successRate ?? 0;
            const colour = rate === 1 ? "#29916e" : rate === 0 ? "#b91c1c" : "#b45309";
            return (
              <tr key={a} data-active={rate === 1 && !arm.unfiltered}>
                <td>{arm.label}</td>
                <td className="num">{st.n}</td>
                <td className="num" style={{ color: colour, fontWeight: 700 }}>
                  {st.unanimous ? (rate === 1 ? "correct" : "wrong") : `split ${(rate * 3).toFixed(0)}/${st.n}`}
                </td>
                <td className="num">{st.p50Ms == null ? "—" : `${Math.round(st.p50Ms).toLocaleString()} ms`}</td>
                <td className="num">{r0.confidence == null ? "—" : r0.confidence.toFixed(3)}</td>
                <td style={{ fontFamily: "var(--font-mono)", fontSize: 12.5 }}>
                  {r0.selected ?? "—"}
                  {r0.goldAction && r0.selected !== r0.goldAction ? (
                    <span style={{ color: "#b91c1c" }}> → gold {r0.goldAction}</span>
                  ) : null}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <div className="legend">
        <span>every column is read from the recorded receipt for this state — no interpolation</span>
      </div>
    </div>
  );
}
