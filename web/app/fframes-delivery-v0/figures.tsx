"use client";

// Hand-rolled SVG figures for the fframes delivery post. No chart library.
// Every value comes from ./data, which reads the frozen study output.
import { useCallback, useId, useMemo, useRef, useState, type KeyboardEvent, type PointerEvent } from "react";
import {
  byId,
  contents,
  doc,
  fmt,
  FRAMES,
  gradientPlatforms,
  gradientRow,
  METRIC_LABEL,
  platforms,
  PLATFORM_LABEL,
  ratioMax,
  signed,
  stats,
  type Metric,
} from "./data";

function Toggle<T extends string>({
  label,
  options,
  value,
  onChange,
  name = (v: T) => v,
}: {
  label: string;
  options: readonly T[];
  value: T;
  onChange: (v: T) => void;
  name?: (v: T) => string;
}) {
  return (
    <div className="es-controls" role="group" aria-label={label}>
      <span className="ff-ctl-label">{label}</span>
      {options.map((o) => (
        <button key={o} type="button" className="es-btn" aria-pressed={o === value} onClick={() => onChange(o)}>
          {name(o)}
        </button>
      ))}
    </div>
  );
}

const metrics = ["vmaf", "vmaf_neg"] as const;

/* ------------------------------------------------------------------ (a) */
/** Per-frame explorer: platform x content, naive vs ours over the 90 scored frames. */
export function FrameExplorer() {
  const [pid, setPid] = useState(platforms[platforms.length - 1].id);
  const [content, setContent] = useState(contents[0]);
  const [metric, setMetric] = useState<Metric>("vmaf");
  const [frame, setFrame] = useState(0);
  const svgRef = useRef<SVGSVGElement>(null);
  const titleId = useId();

  const s = doc.series[pid][content];
  const naive = s.naive[metric];
  const ours = s.fast[metric];
  const p = byId(pid);
  const clipN = useMemo(() => stats(naive), [naive]);
  const clipO = useMemo(() => stats(ours), [ours]);

  const W = 680, H = 280, L = 46, R = 14, T = 14, B = 32;
  const lo = Math.floor(Math.min(...naive, ...ours)) - 1;
  const hi = Math.min(100, Math.ceil(Math.max(...naive, ...ours)) + 1);
  const x = (i: number) => L + (i / (FRAMES - 1)) * (W - L - R);
  const y = (v: number) => T + (1 - (v - lo) / (hi - lo)) * (H - T - B);
  const line = (vs: number[]) => vs.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join("");
  const ticks = [lo, (lo + hi) / 2, hi];

  const fromPointer = useCallback((e: PointerEvent<SVGSVGElement>) => {
    const r = svgRef.current?.getBoundingClientRect();
    if (!r) return;
    const vx = ((e.clientX - r.left) / r.width) * W;
    setFrame(Math.max(0, Math.min(FRAMES - 1, Math.round(((vx - L) / (W - L - R)) * (FRAMES - 1)))));
  }, []);
  const onKey = (e: KeyboardEvent<SVGSVGElement>) => {
    const step = e.shiftKey ? 10 : 1;
    let n = frame;
    if (e.key === "ArrowRight" || e.key === "ArrowUp") n = frame + step;
    else if (e.key === "ArrowLeft" || e.key === "ArrowDown") n = frame - step;
    else if (e.key === "Home") n = 0;
    else if (e.key === "End") n = FRAMES - 1;
    else return;
    e.preventDefault();
    setFrame(Math.max(0, Math.min(FRAMES - 1, n)));
  };

  const d = ours[frame] - naive[frame];
  const readout = `frame ${frame}: naive ${fmt(naive[frame])}, ours ${fmt(ours[frame])}, difference ${signed(d)}`;

  return (
    <div className="ff-explorer">
      <Toggle label="simulator" options={platforms.map((q) => q.id)} value={pid} onChange={setPid} name={(v) => PLATFORM_LABEL[v]} />
      <Toggle label="clip" options={contents} value={content} onChange={setContent} />
      <Toggle label="metric" options={metrics} value={metric} onChange={setMetric} name={(v) => METRIC_LABEL[v]} />
      <svg
        ref={svgRef}
        className="ff-svg ff-scrub"
        viewBox={`0 0 ${W} ${H}`}
        role="slider"
        tabIndex={0}
        aria-labelledby={titleId}
        aria-valuemin={0}
        aria-valuemax={FRAMES - 1}
        aria-valuenow={frame}
        aria-valuetext={readout}
        onPointerMove={fromPointer}
        onPointerDown={fromPointer}
        onKeyDown={onKey}
      >
        <title id={titleId}>
          {`per-frame ${METRIC_LABEL[metric]} for the ${content} clip in the ${pid} simulator. arrow keys move the frame cursor.`}
        </title>
        {ticks.map((t) => (
          <g key={t}>
            <line x1={L} x2={W - R} y1={y(t)} y2={y(t)} className="ff-grid" />
            <text x={L - 6} y={y(t) + 4} textAnchor="end" className="ff-tick">{fmt(t, 0)}</text>
          </g>
        ))}
        {[0, 30, 60, FRAMES - 1].map((f) => (
          <text key={f} x={x(f)} y={H - 10} textAnchor="middle" className="ff-tick">{f}</text>
        ))}
        <path d={line(naive)} className="ff-line ff-naive" />
        <path d={line(ours)} className="ff-line ff-ours" />
        <line x1={x(frame)} x2={x(frame)} y1={T} y2={H - B} className="ff-cursor" />
        <circle cx={x(frame)} cy={y(naive[frame])} r={4} className="ff-dot ff-naive" />
        <circle cx={x(frame)} cy={y(ours[frame])} r={4} className="ff-dot ff-ours" />
      </svg>
      <input
        className="es-range"
        type="range"
        min={0}
        max={FRAMES - 1}
        value={frame}
        aria-label="frame"
        onChange={(e) => setFrame(Number(e.target.value))}
      />
      <div className="ff-legend" aria-hidden="true">
        <span><i className="ff-key ff-naive" /> naive x264 CRF{p.naive_profile.quality}</span>
        <span><i className="ff-key ff-ours" /> ours {p.ours_profile.encoder} CQ{p.ours_profile.quality}{p.ours_profile.prefilter !== "none" ? ` + ${p.ours_profile.prefilter}` : ""}</span>
      </div>
      <p className="es-readout" aria-live="polite">
        frame {frame} · naive {fmt(naive[frame])} · ours {fmt(ours[frame])} · {signed(d)}
      </p>
      <table className="x-table ff-stats">
        <caption>{METRIC_LABEL[metric]}, mean / p5. clip rows use 90 frames; pooled rows use all {FRAMES * contents.length} frames of the simulator.</caption>
        <thead>
          <tr><th scope="col" /><th scope="col">naive</th><th scope="col">ours</th><th scope="col">ours minus naive</th></tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">{content} clip</th>
            <td>{fmt(clipN.mean)} / {fmt(clipN.p5)}</td>
            <td>{fmt(clipO.mean)} / {fmt(clipO.p5)}</td>
            <td>{signed(clipO.mean - clipN.mean)} / {signed(clipO.p5 - clipN.p5)}</td>
          </tr>
          <tr>
            <th scope="row">{pid} pooled</th>
            <td>{fmt(p.summary.naive[metric].mean)} / {fmt(p.summary.naive[metric].p5)}</td>
            <td>{fmt(p.summary.fast[metric].mean)} / {fmt(p.summary.fast[metric].p5)}</td>
            <td>{signed(p.gain[metric].mean)} / {signed(p.gain[metric].p5)}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

/* ------------------------------------------------------------- (b) + (d) */
/** Gain per simulator (mean and p5) with the upload-size multiplier beside it. */
export function GainChart() {
  const [metric, setMetric] = useState<Metric>("vmaf");
  const titleId = useId();
  const all = platforms.flatMap((p) => metrics.flatMap((m) => [p.gain[m].mean, p.gain[m].p5]));
  const gMin = Math.min(0, ...all);
  const gMax = Math.max(...all);
  const W = 680, rowH = 44, T = 26, H = T + platforms.length * rowH + 10;
  const gx0 = 86, gx1 = 430, cx0 = 486, cx1 = 660;
  const gx = (v: number) => gx0 + ((v - gMin) / (gMax - gMin)) * (gx1 - gx0);
  const cMax = Math.ceil(ratioMax);
  const cx = (v: number) => cx0 + (v / cMax) * (cx1 - cx0);
  return (
    <div>
      <Toggle label="metric" options={metrics} value={metric} onChange={setMetric} name={(v) => METRIC_LABEL[v]} />
      <svg className="ff-svg" viewBox={`0 0 ${W} ${H}`} role="img" aria-labelledby={titleId}>
        <title id={titleId}>
          {`${METRIC_LABEL[metric]} gain of ours over naive per simulator, mean and p5, with upload size relative to naive. ` +
            platforms
              .map((p) => `${p.id}: mean ${signed(p.gain[metric].mean)}, p5 ${signed(p.gain[metric].p5)}, upload ${fmt(p.upload_ratio)} times`)
              .join("; ")}
        </title>
        <text x={gx0} y={14} className="ff-head">{METRIC_LABEL[metric]} gain, ours minus naive</text>
        <text x={cx0} y={14} className="ff-head">upload size, ours / naive</text>
        <line x1={gx(0)} x2={gx(0)} y1={T - 4} y2={H - 6} className="ff-axis" />
        <line x1={cx(1)} x2={cx(1)} y1={T - 4} y2={H - 6} className="ff-axis ff-dash" />
        <text x={cx(1)} y={H} textAnchor="middle" className="ff-tick">1×</text>
        {platforms.map((p, i) => {
          const y0 = T + i * rowH;
          const bar = (v: number, yy: number, cls: string) => (
            <rect x={Math.min(gx(0), gx(v))} y={yy} width={Math.abs(gx(v) - gx(0))} height={12} className={`ff-bar ${cls}`} />
          );
          const m = p.gain[metric];
          return (
            <g key={p.id}>
              <text x={gx0 - 10} y={y0 + 18} textAnchor="end" className="ff-row">{PLATFORM_LABEL[p.id]}</text>
              {bar(m.mean, y0 + 4, "ff-mean")}
              {bar(m.p5, y0 + 18, "ff-p5")}
              <text x={Math.max(gx(0), gx(m.mean)) + 6} y={y0 + 14} className="ff-val">mean {signed(m.mean)}</text>
              <text x={Math.max(gx(0), gx(m.p5)) + 6} y={y0 + 28} className="ff-val">p5 {signed(m.p5)}</text>
              <rect x={cx0} y={y0 + 8} width={cx(p.upload_ratio) - cx0} height={16} className="ff-bar ff-cost" />
              <text x={cx(p.upload_ratio) + 6} y={y0 + 21} className="ff-val">{fmt(p.upload_ratio)}×</text>
            </g>
          );
        })}
      </svg>
      <div className="ff-legend" aria-hidden="true">
        <span><i className="ff-key ff-mean" /> pooled mean</span>
        <span><i className="ff-key ff-p5" /> pooled p5</span>
        <span><i className="ff-key ff-cost" /> upload bytes, sum of four clips</span>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ (c) */
const GRAD_VARIANTS = ["naive", "fast", "hevc10"] as const;
const GRAD_LABEL: Record<string, string> = { naive: "naive x264", fast: "ours h.264", hevc10: "hevc main10" };

/** The synthetic 10-bit blue ramp, where the selected H.264 recipe loses VMAF. */
export function GradientPanel() {
  const [view, setView] = useState<"vmaf" | "cambi">("vmaf");
  const titleId = useId();
  const rows = gradientPlatforms.flatMap((gp) => GRAD_VARIANTS.map((v) => gradientRow(gp, v)));
  const vLo = Math.floor(Math.min(...rows.map((r) => r.vmaf.p5)) - 0.5);
  const cMax = Math.ceil(Math.max(...rows.map((r) => r.cambi.mean)));
  const lo = view === "vmaf" ? vLo : 0;
  const hi = view === "vmaf" ? 100 : cMax;
  const W = 680, x0 = 190, x1 = 600, rowH = 30, gapH = 22;
  const H = gradientPlatforms.length * (GRAD_VARIANTS.length * rowH + gapH) + 30;
  const x = (v: number) => x0 + ((v - lo) / (hi - lo)) * (x1 - x0);
  return (
    <div>
      <Toggle
        label="score"
        options={["vmaf", "cambi"] as const}
        value={view}
        onChange={setView}
        name={(v) => (v === "vmaf" ? "VMAF mean and p5" : "CAMBI mean (lower is less banding)")}
      />
      <svg className="ff-svg" viewBox={`0 0 ${W} ${H}`} role="img" aria-labelledby={titleId}>
        <title id={titleId}>
          {"synthetic 10-bit blue ramp. " +
            rows.map((r) => `${r.platform} ${GRAD_LABEL[r.variant]}: VMAF mean ${fmt(r.vmaf.mean)}, p5 ${fmt(r.vmaf.p5)}, CAMBI ${fmt(r.cambi.mean)}`).join("; ")}
        </title>
        {gradientPlatforms.map((gp, gi) => {
          const top = gi * (GRAD_VARIANTS.length * rowH + gapH);
          return (
            <g key={gp}>
              <text x={8} y={top + 14} className="ff-head">{gp} simulator</text>
              {GRAD_VARIANTS.map((v, vi) => {
                const r = gradientRow(gp, v);
                const yy = top + 22 + vi * rowH;
                const cls = v === "naive" ? "ff-naive-fill" : v === "fast" ? "ff-ours-fill" : "ff-alt-fill";
                return (
                  <g key={v}>
                    <text x={x0 - 10} y={yy + 12} textAnchor="end" className="ff-row">{GRAD_LABEL[v]}</text>
                    {view === "vmaf" ? (
                      <>
                        <line x1={x(r.vmaf.p5)} x2={x(r.vmaf.mean)} y1={yy + 8} y2={yy + 8} className="ff-range" />
                        <circle cx={x(r.vmaf.p5)} cy={yy + 8} r={4} className={`ff-hollow ${cls}`} />
                        <circle cx={x(r.vmaf.mean)} cy={yy + 8} r={5} className={cls} />
                        <text x={x1 + 8} y={yy + 12} className="ff-val">{fmt(r.vmaf.mean)} / {fmt(r.vmaf.p5)}</text>
                      </>
                    ) : (
                      <>
                        <rect x={x0} y={yy + 1} width={x(r.cambi.mean) - x0} height={14} className={`ff-bar ${cls}`} />
                        <text x={x(r.cambi.mean) + 6} y={yy + 12} className="ff-val">{fmt(r.cambi.mean)}</text>
                      </>
                    )}
                  </g>
                );
              })}
            </g>
          );
        })}
        <text x={x0} y={H - 6} className="ff-tick">{fmt(lo, 0)}</text>
        <text x={x1} y={H - 6} textAnchor="end" className="ff-tick">{fmt(hi, 0)}</text>
      </svg>
      <p className="es-readout">
        {view === "vmaf"
          ? `filled dot is the mean, hollow dot is p5. the axis starts at ${fmt(lo, 0)}, so small gaps look large.`
          : "CAMBI is a no-reference banding score. lower means less banding by that score, not a better picture."}
      </p>
    </div>
  );
}

/** Teaser mini: naive vs ours on the ramp, one simulator, zoomed axis. */
export function GradientMini({ platform }: { platform: string }) {
  const n = gradientRow(platform, "naive").vmaf;
  const o = gradientRow(platform, "fast").vmaf;
  const lo = Math.floor(Math.min(n.p5, o.p5) - 0.5);
  const W = 240, H = 170, x0 = 16, x1 = 224;
  const x = (v: number) => x0 + ((v - lo) / (100 - lo)) * (x1 - x0);
  const row = (s: typeof n, yy: number, label: string, cls: string) => (
    <g>
      <text x={x0} y={yy - 10} className="ff-tick">{label}</text>
      <line x1={x(s.p5)} x2={x(s.mean)} y1={yy} y2={yy} className="ff-range" />
      <circle cx={x(s.p5)} cy={yy} r={4} className={`ff-hollow ${cls}`} />
      <circle cx={x(s.mean)} cy={yy} r={5} className={cls} />
    </g>
  );
  return (
    <svg className="ff-svg ff-mini" viewBox={`0 0 ${W} ${H}`} role="img"
      aria-label={`${platform} simulator, blue ramp VMAF. naive mean ${fmt(n.mean)} p5 ${fmt(n.p5)}; ours mean ${fmt(o.mean)} p5 ${fmt(o.p5)}`}>
      <defs>
        <linearGradient id="ff-ramp" x1="0" x2="1">
          <stop offset="0" stopColor="#0b1b3a" />
          <stop offset="1" stopColor="#4d86d9" />
        </linearGradient>
      </defs>
      <rect x={0} y={0} width={W} height={36} fill="url(#ff-ramp)" opacity={0.8} />
      {row(n, 80, "naive x264", "ff-naive-fill")}
      {row(o, 124, "ours h.264", "ff-ours-fill")}
      <text x={x0} y={H - 4} className="ff-tick">{lo}</text>
      <text x={x1} y={H - 4} textAnchor="end" className="ff-tick">100</text>
    </svg>
  );
}
