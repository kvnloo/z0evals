/** Tiny SVG helpers. No chart library — the reference hand-rolls its marks too. */
export const NS = "http://www.w3.org/2000/svg";

export const el = (name: string, attrs: Record<string, string | number>) => {
  const a = Object.entries(attrs)
    .map(([k, v]) => `${k}="${String(v)}"`)
    .join(" ");
  return `<${name} ${a}/>`;
};

export type Scale = (v: number) => number;

export function linear(domain: [number, number], range: [number, number]): Scale {
  const [d0, d1] = domain;
  const [r0, r1] = range;
  const span = d1 - d0 || 1;
  return (v) => r0 + ((v - d0) / span) * (r1 - r0);
}

export function log10(domain: [number, number], range: [number, number]): Scale {
  const [d0, d1] = domain.map(Math.log10) as [number, number];
  const [r0, r1] = range;
  const span = d1 - d0 || 1;
  return (v) => r0 + ((Math.log10(Math.max(v, 1e-9)) - d0) / span) * (r1 - r0);
}

/** Nice tick values for a log axis between two positive bounds. */
export function logTicks(min: number, max: number): number[] {
  const out: number[] = [];
  for (let e = Math.floor(Math.log10(min)); e <= Math.ceil(Math.log10(max)); e++) {
    for (const m of [1, 3]) {
      const v = m * 10 ** e;
      if (v >= min * 0.75 && v <= max * 1.25) out.push(v);
    }
  }
  return out;
}

export const fmtMs = (v: number) =>
  v >= 1000 ? `${(v / 1000).toFixed(v >= 10000 ? 0 : 1)}s` : `${Math.round(v)}ms`;

export const fmtPct = (v: number, digits = 1) => `${(v * 100).toFixed(digits)}%`;
