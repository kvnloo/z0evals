"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { asset } from "@/lib/asset";
import type { QuacklesData, Row } from "./types";
import { STATUS_COLOR, THEME_LABEL } from "./types";

/**
 * The lineage swimlane, rebuilt for the essay. One lane per scene, one tick per
 * preserved render, coloured by its archive status. The playhead walks the 665
 * versions in time order; the cards above show each scene's latest render at
 * that moment, cut from the same sprite atlas the original /lineage page used.
 * Hold a card to see that scene's locked reference in its place.
 */
export default function LineageSwimlane({ data }: { data: QuacklesData }) {
  const rows = data.entries;
  const N = rows.length;
  const [k, setK] = useState(N - 1);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [axis, setAxis] = useState<"time" | "version">("version");
  const [only, setOnly] = useState<number | null>(null);
  const [peek, setPeek] = useState<number | null>(null);
  const kRef = useRef(k);
  kRef.current = k;

  const t0 = rows[0][1];
  const t1 = rows[N - 1][1];
  const xOf = (i: number) => (axis === "time" ? (rows[i][1] - t0) / (t1 - t0) : i / (N - 1));

  // latest version index per theme at the playhead
  const latest = useMemo(() => {
    const out = data.themes.map(() => -1);
    for (let i = 0; i <= k; i++) out[rows[i][0]] = i;
    return out;
  }, [k, rows, data.themes]);
  const seen = useMemo(() => {
    const out = data.themes.map(() => 0);
    for (let i = 0; i <= k; i++) out[rows[i][0]]++;
    return out;
  }, [k, rows, data.themes]);

  useEffect(() => {
    if (!playing) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setK(N - 1);
      setPlaying(false);
      return;
    }
    let raf = 0;
    let last = performance.now();
    let acc = 0;
    const tick = (now: number) => {
      acc += ((now - last) / 1000) * 14 * speed;
      last = now;
      const step = Math.floor(acc);
      if (step > 0) {
        acc -= step;
        const next = Math.min(N - 1, kRef.current + step);
        setK(next);
        if (next >= N - 1) {
          setPlaying(false);
          return;
        }
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [playing, speed, N]);

  const W = 1000;
  const laneH = 34;
  const top = 26;
  const H = top + laneH * data.themes.length + 26;
  const cur = rows[k];
  const date = new Date(cur[1]);
  const fmt = (d: Date) => d.toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });

  // day ticks for the axis
  const days: { x: number; label: string }[] = [];
  if (axis === "time") {
    const d = new Date(t0);
    d.setUTCHours(0, 0, 0, 0);
    for (let t = d.getTime() + 86400000; t < t1; t += 86400000 * 5) {
      days.push({ x: (t - t0) / (t1 - t0), label: fmt(new Date(t)) });
    }
  } else {
    for (let i = 0; i < N; i += 100) days.push({ x: i / (N - 1), label: `v${i}` });
  }

  return (
    <div className="qk-lane">
      <div className="qk-cards">
        {data.themes.map((theme, ti) => {
          const i = latest[ti];
          const ref = data.references[theme];
          const showRef = peek === ti;
          return (
            <button
              key={theme}
              type="button"
              className="qk-card"
              aria-label={`${THEME_LABEL[theme]}: hold to compare with the reference`}
              onPointerDown={() => setPeek(ti)}
              onPointerUp={() => setPeek(null)}
              onPointerLeave={() => setPeek(null)}
              onKeyDown={(e) => (e.key === " " || e.key === "Enter") && setPeek(ti)}
              onKeyUp={() => setPeek(null)}
            >
              <div className="qk-card-img">
                {showRef ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={asset(ref.src)} alt={`${THEME_LABEL[theme]} reference`} />
                ) : i >= 0 ? (
                  <Sprite row={rows[i]} pages={data.atlasPages} />
                ) : (
                  <div className="qk-card-empty">not started</div>
                )}
              </div>
              <div className="qk-card-meta">
                <span className="qk-card-theme">{THEME_LABEL[theme]}</span>
                <span className="qk-card-n">{showRef ? "reference" : i >= 0 ? rows[i][4] : "—"}</span>
              </div>
              <div className="qk-card-count">{seen[ti]} of {data.counts[theme]}</div>
            </button>
          );
        })}
      </div>

      <svg
        className="qk-lane-svg"
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={`${N} preserved versions across five scenes, ${fmt(new Date(t0))} to ${fmt(new Date(t1))}`}
        onPointerDown={(e) => {
          const svg = e.currentTarget;
          const pick = (clientX: number) => {
            const r = svg.getBoundingClientRect();
            const fx = Math.max(0, Math.min(1, (clientX - r.left) / r.width));
            let best = 0;
            let bd = Infinity;
            for (let i = 0; i < N; i++) {
              const dd = Math.abs(xOf(i) - fx);
              if (dd < bd) {
                bd = dd;
                best = i;
              }
            }
            setK(best);
          };
          pick(e.clientX);
          setPlaying(false);
          const move = (ev: PointerEvent) => pick(ev.clientX);
          const up = () => {
            window.removeEventListener("pointermove", move);
            window.removeEventListener("pointerup", up);
          };
          window.addEventListener("pointermove", move);
          window.addEventListener("pointerup", up);
        }}
      >
        {days.map((d, i) => (
          <g key={i}>
            <line x1={d.x * W} x2={d.x * W} y1={top - 4} y2={H - 22} className="qk-grid" />
            <text x={d.x * W + 3} y={H - 8} className="qk-axis">
              {d.label}
            </text>
          </g>
        ))}
        {data.themes.map((theme, ti) => (
          <g key={theme}>
            <text x={4} y={top + ti * laneH + 13} className="qk-lane-label">
              {THEME_LABEL[theme]}
            </text>
            <line x1={0} x2={W} y1={top + ti * laneH + laneH - 4} y2={top + ti * laneH + laneH - 4} className="qk-grid" />
          </g>
        ))}
        {rows.map((r, i) => {
          const dim = only !== null && r[2] !== only;
          const future = i > k;
          return (
            <rect
              key={i}
              x={xOf(i) * W - 1}
              y={top + r[0] * laneH + 16}
              width={2.2}
              height={12}
              fill={STATUS_COLOR[data.statuses[r[2]]] ?? "#888"}
              opacity={dim ? 0.08 : future ? 0.18 : 0.95}
            >
              <title>
                {`${THEME_LABEL[data.themes[r[0]]]} · ${r[4]} · ${data.statuses[r[2]]} · ${data.phases[r[3]]} · ${fmt(new Date(r[1]))}`}
              </title>
            </rect>
          );
        })}
        {data.milestones.map((m) => (
          <g key={m.index} className="qk-ms" onPointerDown={(e) => (e.stopPropagation(), setK(m.index), setPlaying(false))}>
            <path d={`M${xOf(m.index) * W},${top - 6} l5,-6 l-5,-6 l-5,6z`} data-kind={m.kind} />
            <title>{`${m.label} (${m.basis})`}</title>
          </g>
        ))}
        <line x1={xOf(k) * W} x2={xOf(k) * W} y1={6} y2={H - 22} className="qk-playhead" />
      </svg>

      <div className="es-controls">
        <button type="button" className="es-btn" aria-pressed={playing} onClick={() => {
          if (!playing && k >= N - 1) setK(0);
          setPlaying(!playing);
        }}>
          {playing ? "pause" : k >= N - 1 ? "replay" : "play"}
        </button>
        {[1, 4, 16].map((s) => (
          <button key={s} type="button" className="es-btn" aria-pressed={speed === s} onClick={() => setSpeed(s)}>
            {s}×
          </button>
        ))}
        <span className="qk-sep" />
        <button type="button" className="es-btn" aria-pressed={axis === "time"} onClick={() => setAxis("time")}>
          by date
        </button>
        <button type="button" className="es-btn" aria-pressed={axis === "version"} onClick={() => setAxis("version")}>
          by version
        </button>
      </div>
      <input
        className="es-range"
        type="range"
        min={0}
        max={N - 1}
        value={k}
        aria-label="playhead"
        aria-valuetext={`version ${k + 1} of ${N}, ${THEME_LABEL[data.themes[cur[0]]]} ${cur[4]}, ${fmt(date)}`}
        onChange={(e) => {
          setPlaying(false);
          setK(+e.target.value);
        }}
      />
      <div className="qk-readout es-readout">
        <span>
          {k + 1} / {N}
        </span>
        <span>
          {fmt(date)} {date.toISOString().slice(11, 16)}Z{cur[7] ? "" : " (file mtime)"}
        </span>
        <span>
          {THEME_LABEL[data.themes[cur[0]]]} · {cur[4]}
          {cur[4] === data.phases[cur[3]] ? "" : ` · ${data.phases[cur[3]]}`}
        </span>
      </div>
      <div className="es-controls qk-legend" role="group" aria-label="highlight one archive status">
        {data.statuses.map((s, si) => (
          <button
            key={s}
            type="button"
            className="es-btn"
            aria-pressed={only === si}
            onClick={() => setOnly(only === si ? null : si)}
          >
            <i style={{ background: STATUS_COLOR[s] }} /> {s} {data.statusCounts[s]}
          </button>
        ))}
      </div>
    </div>
  );
}

export function Sprite({
  row,
  pages,
  className,
  box = 2 / 3,
}: {
  row: Row;
  pages: string[];
  className?: string;
  /** width / height of the frame it sits in; the sprite is contained, never cropped */
  box?: number;
}) {
  // atlas uv is [x, y, width, height] as fractions of the 2048² page
  const [u0, v0, du, dv] = row[6];
  const wider = du / dv > box;
  return (
    <div
      className={className ?? "qk-sprite"}
      role="img"
      aria-label={row[4]}
      style={{
        aspectRatio: `${du * 2048} / ${dv * 2048}`,
        // percentage widths resolve reliably; percentage heights inside an
        // aspect-ratio box do not, so a tall sprite is narrowed instead
        width: wider ? "100%" : `${((du / dv) / box) * 100}%`,
        height: "auto",
        backgroundImage: `url(${asset(pages[row[5]])})`,
        backgroundSize: `${100 / du}% ${100 / dv}%`,
        backgroundPosition: `${(u0 / (1 - du)) * 100}% ${(v0 / (1 - dv)) * 100}%`,
      }}
    />
  );
}
