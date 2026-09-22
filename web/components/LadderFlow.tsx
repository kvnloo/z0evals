"use client";
import { useEffect, useRef, useState } from "react";

const R_PAD = 24;

const RUNGS = [
  { id: "deterministic", label: "deterministic compiler", detail: "legal-action set, no model", ms: "~0.003" },
  { id: "tiny", label: "tiny specialist", detail: "FnGemma 270M / Hammer 3B", ms: "66–195" },
  { id: "jev", label: "nanojev bounded scorer", detail: "calibrated typed questions", ms: "31" },
  { id: "slm", label: "local slm router", detail: "Qwen 3.5 4B / 9B", ms: "1993–3603" },
  { id: "general", label: "general fallback", detail: "escalation only", ms: "—" },
];

/** The escalation ladder, with a packet that pulses through the rungs. */
export default function LadderFlow() {
  const ref = useRef<HTMLDivElement>(null);
  const [armed, setArmed] = useState(false);
  const [step, setStep] = useState(-1);

  useEffect(() => {
    const n = ref.current; if (!n) return;
    const io = new IntersectionObserver((e) => {
      if (e[0]?.isIntersecting) { setArmed(true); io.disconnect(); }
    }, { threshold: 0.3 });
    io.observe(n); return () => io.disconnect();
  }, []);

  useEffect(() => {
    if (!armed) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) { setStep(RUNGS.length - 1); return; }
    let i = -1;
    const t = setInterval(() => {
      i += 1;
      setStep(i);
      if (i >= RUNGS.length) clearInterval(t);
    }, 520);
    return () => clearInterval(t);
  }, [armed]);

  const W = 820, rowH = 58, L = 30, T = 18;
  const H = T + RUNGS.length * rowH + 12;

  return (
    <div ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg" role="img"
           aria-label="escalation ladder from deterministic compilation to the general fallback">
        <line x1={L + 11} x2={L + 11} y1={T + 12} y2={T + (RUNGS.length - 1) * rowH + 12}
              stroke="#d9d9d9" strokeWidth="1" />
        {RUNGS.map((r, i) => {
          const lit = step >= i;
          const active = step === i;
          const y = T + i * rowH;
          return (
            <g key={r.id} className="mark" style={{ opacity: lit ? 1 : 0.35, transition: "opacity .35s ease" }}>
              <line x1={L + 4} x2={L + 18} y1={y + 12} y2={y + 12} stroke={lit ? "#29916e" : "#d9d9d9"} strokeWidth="1.5" />
              <circle cx={L + 11} cy={y + 12} r={active ? 6 : 4} fill={lit ? "#29916e" : "#fff"}
                      stroke="#29916e" strokeWidth="1.5"
                      style={{ animation: active ? "packetPulse 1s ease-in-out infinite" : "none",
                               transition: "r .3s ease" }} />
              <text x={L + 32} y={y + 9} fontSize="12.5" fill="#1a3029" fontWeight={active ? 700 : 500}>{r.label}</text>
              <text x={L + 32} y={y + 25} fontSize="11" fill="#888">{r.detail}</text>
              <text x={W - R_PAD} y={y + 16} fontSize="11.5" textAnchor="end"
                    fill={lit ? "#29916e" : "#a8a8a8"} fontFamily="var(--font-mono)">{r.ms} ms</text>
            </g>
          );
        })}
      </svg>
      <div className="legend">
        <span>a case descends only until a rung accepts it</span>
        <span>latencies are warm p50 from this run</span>
      </div>
    </div>
  );
}

