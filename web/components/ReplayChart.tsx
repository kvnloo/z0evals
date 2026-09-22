"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import type { Arm, Matrix } from "@/data/types";
import { useReveal } from "./charts/useReveal";

const COLOUR = ["#29916e", "#1a3029", "#0f766e", "#7c5295", "#b45309", "#64748b", "#b91c1c"];
const W = 860, H = 320, L = 52, R = 150, T = 22, B = 62;

/**
 * Replayable progress curve with a playhead.
 *
 * Mirrors the reference's Replay control: the curves are drawn up to the
 * playhead, the playhead can be dragged, and Replay sweeps it. The series are
 * our real per-state results — position N is the Nth state in the bounded-choice
 * sweep, not an illustration.
 */
export default function ReplayChart({ matrix, selected }: { matrix: Matrix; selected: string[] }) {
  const { ref, shown } = useReveal<HTMLDivElement>();
  const [playhead, setPlayhead] = useState(1000);
  const [playing, setPlaying] = useState(false);
  const raf = useRef<number | null>(null);
  const last = useRef<number>(0);

  const arms = useMemo(
    () => matrix.arms.filter((a) => selected.includes(a.id)),
    [matrix, selected]
  );
  const n = matrix.states.length;

  // series: cumulative mean decision latency per state, per arm, normalised to
  // each arm's own p50 so different scales are comparable (the reference does
  // the same normalisation for its "remaining time" curves).
  const series = useMemo(() => {
    return arms.map((a, i) => {
      const vals: (number | null)[] = matrix.states.map((s) => s.arms[a.id]?.p50Ms ?? null);
      const scale = a.warmP50Ms && a.warmP50Ms > 0 ? a.warmP50Ms : 1;
      return {
        arm: a,
        colour: a.unfiltered ? "#b91c1c" : COLOUR[i % COLOUR.length],
        points: vals.map((v, k) => (v == null ? null : { k, y: v / scale })),
      };
    });
  }, [arms, matrix]);

  const maxY = useMemo(() => {
    let m = 1;
    for (const s of series) for (const p of s.points) if (p) m = Math.max(m, p.y);
    return m * 1.1;
  }, [series]);

  const x = (k: number) => L + (k / Math.max(1, n - 1)) * (W - L - R);
  const y = (v: number) => H - B - (v / maxY) * (H - T - B);

  const progress = playhead / 1000;
  const cut = progress * (n - 1);

  useEffect(() => {
    if (!playing) return;
    const step = (t: number) => {
      if (!last.current) last.current = t;
      const dt = t - last.current;
      last.current = t;
      setPlayhead((p) => {
        const next = p + dt * 0.28;
        if (next >= 1000) { setPlaying(false); return 1000; }
        return next;
      });
      raf.current = requestAnimationFrame(step);
    };
    raf.current = requestAnimationFrame(step);
    return () => { if (raf.current) cancelAnimationFrame(raf.current); last.current = 0; };
  }, [playing]);

  const cursor = matrix.states[Math.min(n - 1, Math.round(cut))];

  return (
    <div ref={ref}>
      <div className="chart-tabs" style={{ alignItems: "center", gap: 10 }}>
        <button type="button" onClick={() => { setPlayhead(0); setPlaying(true); }}
                aria-label="Replay the sweep">
          ▶ Replay
        </button>
        <button type="button" onClick={() => setPlayhead(1000)}>⤒ End</button>
        <span style={{ fontSize: 12.5, color: "var(--color-sb-text-muted)", fontFamily: "var(--font-mono)" }}>
          state {Math.min(n, Math.round(cut) + 1)} / {n}
          {cursor ? ` · ${cursor.family}` : ""}
        </span>
      </div>

      <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg" role="img"
           aria-label="Replayable per-state latency curves for the selected arms">
        {[0, 0.25, 0.5, 0.75, 1].map((f) => (
          <g key={f}>
            <line className="grid" x1={L} x2={W - R} y1={H - B - f * (H - T - B)} y2={H - B - f * (H - T - B)} />
            <text x={L - 8} y={H - B - f * (H - T - B) + 3.5} textAnchor="end" fontSize="10.5" fill="#888">
              {(f * maxY).toFixed(1)}×
            </text>
          </g>
        ))}
        <line className="axis" x1={L} x2={W - R} y1={H - B} y2={H - B} />
        <line className="axis" x1={L} x2={L} y1={T} y2={H - B} />
        <text x={L + (W - L - R) / 2} y={H - 26} textAnchor="middle" fontSize="11" fill="#676767">
          bounded-choice state, in sweep order
        </text>
        <text transform={`translate(13 ${T + (H - T - B) / 2}) rotate(-90)`} textAnchor="middle"
              fontSize="11" fill="#676767">decision latency ÷ that arm&rsquo;s own p50</text>

        {matrix.states.map((s, k) => (
          <line key={s.id} x1={x(k)} x2={x(k)} y1={T} y2={H - B} stroke="#f7f7f7" />
        ))}

        {series.map((s, si) => {
          const seg: string[] = [];
          for (const p of s.points) {
            if (!p) continue;
            if (p.k > cut) break;
            seg.push(`${x(p.k)},${y(p.y)}`);
          }
          return (
            <g key={s.arm.id}>
              <polyline fill="none" stroke={s.colour}
                        strokeWidth={s.arm.unfiltered ? 1.1 : 1.6}
                        strokeDasharray={s.arm.unfiltered ? "3 2" : undefined}
                        points={seg.join(" ")}
                        style={{ opacity: shown ? 1 : 0, transition: `opacity .4s ease ${si * 60}ms` }} />
              {n > 0 && s.points[Math.round(cut)] ? (
                <circle cx={x(Math.round(cut))} cy={y(s.points[Math.round(cut)]!.y)} r="3"
                        fill={s.colour} />
              ) : null}
              <text x={W - R + 8} y={T + 12 + si * 15} fontSize="11" fill={s.colour}>{s.arm.label}</text>
            </g>
          );
        })}

        <line x1={x(cut)} x2={x(cut)} y1={T} y2={H - B} stroke="#1a3029" strokeWidth="1" opacity="0.55" />
      </svg>

      <div className="scrubRow">
        <span className="scrubLabel">Replay</span>
        <input
          aria-label="Replay position"
          type="range" min={0} max={1000} step={1} value={Math.round(playhead)}
          onChange={(e) => { setPlaying(false); setPlayhead(Number(e.target.value)); }}
        />
        <span className="progressValue">{Math.round((playhead / 1000) * 100)}%</span>
      </div>
      <div className="legend">
        <span>solid = compiler-first · dashed red = unfiltered</span>
        <span>curves are drawn to the playhead; drag it, or press Replay</span>
      </div>
    </div>
  );
}
