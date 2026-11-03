// Typed view of web/data/fframes-delivery-v0.json, which scripts/build_fframes_delivery.py
// derives from the frozen files in studies/fframes-delivery-v0/data. Every number the page
// shows comes from here. The checks below run at build time (and again in the browser for
// the client figures) and throw if the per-frame series and the source summary disagree.
import raw from "@/data/fframes-delivery-v0.json";

export type Metric = "vmaf" | "vmaf_neg";
export type Arm = "naive" | "fast";
export type Stat = { mean: number; p5: number };
type Profile = {
  width: number;
  height: number;
  fps: number;
  encoder: string;
  quality: number;
  scale: string;
  prefilter: string;
  gop_seconds: number;
  maxrate_kbps: number | null;
  bufsize_kbits: number | null;
  audio_kbps: number;
};
export type Platform = {
  id: string;
  summary: Record<Arm, Record<Metric, Stat>>;
  gain: Record<Metric, Stat>;
  upload_ratio: number;
  clips: {
    content: string;
    naive_upload_bytes: number;
    ours_upload_bytes: number;
    naive_playback_bytes: number;
    ours_playback_bytes: number;
    duration_s: number;
  }[];
  naive_profile: Profile;
  ours_profile: Profile;
  simulator: { width: number; height: number; fps: number; codec: string; crf: number; bitrate_kbps: number; gop_seconds: number };
};
export type GradientRow = {
  platform: string;
  variant: string;
  encoder: string;
  quality: number;
  vmaf: Stat;
  cambi: Stat;
  frames: number;
  source: string;
};
type Doc = {
  source: { repo: string; commit: string; study: string };
  metric_versions: { vmaf: string; vmaf_neg: string };
  platforms: Platform[];
  contents: string[];
  frames_per_clip: number;
  series: Record<string, Record<string, Record<Arm, Record<Metric, number[]>>>>;
  gradient10: GradientRow[];
  gates: {
    gates: { command: string; returncode: number; output: string }[];
    static_scan_findings: unknown[];
    review: string;
  };
};

export const doc = raw as unknown as Doc;
export const platforms = doc.platforms;
export const contents = doc.contents;
export const FRAMES = doc.frames_per_clip;
export const METRIC_LABEL: Record<Metric, string> = { vmaf: "VMAF", vmaf_neg: "VMAF NEG" };
export const PLATFORM_LABEL: Record<string, string> = {
  youtube: "youtube",
  shorts: "shorts",
  tiktok: "tiktok",
  reels: "reels",
  x: "x",
};

/** The source's percentile rule (delivery/summarize.py): linear-interpolated 5th percentile. */
export function stats(values: number[]): Stat {
  const o = [...values].sort((a, b) => a - b);
  const pos = (o.length - 1) * 0.05;
  const lo = Math.floor(pos);
  const p5 = o[lo] + (o[Math.min(lo + 1, o.length - 1)] - o[lo]) * (pos - lo);
  return { mean: o.reduce((s, v) => s + v, 0) / o.length, p5 };
}

export function pooled(p: string, arm: Arm, m: Metric): Stat {
  return stats(contents.flatMap((c) => doc.series[p][c][arm][m]));
}

// ---- build-time agreement checks -------------------------------------------------
// The series are rounded to 3 decimals for size, so allow 0.005 against the summary.
const TOL = 0.005;
for (const p of platforms) {
  for (const arm of ["naive", "fast"] as Arm[]) {
    for (const m of ["vmaf", "vmaf_neg"] as Metric[]) {
      for (const c of contents) {
        if (doc.series[p.id][c][arm][m].length !== FRAMES) {
          throw new Error(`fframes: ${p.id}/${c}/${arm}/${m} does not have ${FRAMES} frames`);
        }
      }
      const got = pooled(p.id, arm, m);
      const want = p.summary[arm][m];
      if (Math.abs(got.mean - want.mean) > TOL || Math.abs(got.p5 - want.p5) > TOL) {
        throw new Error(`fframes: frames and summary disagree for ${p.id}/${arm}/${m}`);
      }
    }
    for (const m of ["vmaf", "vmaf_neg"] as Metric[]) {
      for (const s of ["mean", "p5"] as const) {
        const g = p.summary.fast[m][s] - p.summary.naive[m][s];
        if (Math.abs(g - p.gain[m][s]) > 1e-9) throw new Error(`fframes: gain mismatch ${p.id}/${m}/${s}`);
      }
    }
  }
  const ratio = p.clips.reduce((s, c) => s + c.ours_upload_bytes, 0) / p.clips.reduce((s, c) => s + c.naive_upload_bytes, 0);
  if (Math.abs(ratio - p.upload_ratio) > 1e-9) throw new Error(`fframes: upload ratio mismatch ${p.id}`);
}

export const allWin = platforms.every((p) => p.gain.vmaf.mean > 0 && p.gain.vmaf.p5 > 0);
export const totalFrames = platforms.length * contents.length * 2 * FRAMES;
export const ratios = platforms.map((p) => p.upload_ratio);
export const ratioMin = Math.min(...ratios);
export const ratioMax = Math.max(...ratios);
export const byId = (id: string) => {
  const p = platforms.find((q) => q.id === id);
  if (!p) throw new Error(`fframes: no platform ${id}`);
  return p;
};
export const bestPlatform = [...platforms].sort((a, b) => b.gain.vmaf.p5 - a.gain.vmaf.p5)[0];

/** Clip-level cases where the selected recipe loses on mean or p5 VMAF, from the frames. */
export const clipLosses = platforms.flatMap((p) =>
  contents.flatMap((c) => {
    const n = stats(doc.series[p.id][c].naive.vmaf);
    const o = stats(doc.series[p.id][c].fast.vmaf);
    const out: { platform: string; content: string; stat: "mean" | "p5"; naive: number; ours: number }[] = [];
    if (o.mean < n.mean) out.push({ platform: p.id, content: c, stat: "mean", naive: n.mean, ours: o.mean });
    if (o.p5 < n.p5) out.push({ platform: p.id, content: c, stat: "p5", naive: n.p5, ours: o.p5 });
    return out;
  }),
);

/** The synthetic 10-bit ramp. The page calls it a counterexample, so check that it is one. */
export const gradient = doc.gradient10;
export const gradientPlatforms = Array.from(new Set(gradient.map((g) => g.platform)));
export const gradientRow = (platform: string, variant: string) => {
  const r = gradient.find((g) => g.platform === platform && g.variant === variant);
  if (!r) throw new Error(`fframes: no gradient row ${platform}/${variant}`);
  return r;
};
for (const gp of gradientPlatforms) {
  const n = gradientRow(gp, "naive").vmaf;
  const o = gradientRow(gp, "fast").vmaf;
  if (!(o.mean < n.mean && o.p5 < n.p5)) throw new Error(`fframes: gradient ${gp} is no longer a counterexample`);
}

export const commit = doc.source.commit;
export const short = commit.slice(0, 7);
export const sourceUrl = (path: string) => `https://github.com/${doc.source.repo}/blob/${commit}/${path}`;
export const fmt = (v: number, d = 2) => v.toFixed(d);
export const signed = (v: number, d = 2) => `${v >= 0 ? "+" : "\u2212"}${Math.abs(v).toFixed(d)}`;
