"use client";

import { useMemo, useState } from "react";
import { asset } from "@/lib/asset";
import type { Plate, ZoomRegion } from "./types";
import { THEME_LABEL } from "./types";

type Density = { theme: string; source: string; d201: number; d1gp: number };

// Crops and density rows were measured separately; only pair the ones whose
// receiver is the same surface.
const DENSITY_FOR: Record<string, string> = {
  "night/head-print": "head print, jaw receiver",
  "day/head-print": "head print, top shell",
  "day/banner": "poster, banner receiver",
};

/**
 * Pick a region on the plate. The ladder shows the same spot three ways: the
 * web plate scaled up, the native 201 MP render crop and the native 1 GP render
 * crop. Pixel counts go up 5.65× and then 2.23×; the detail mostly does not.
 */
export default function ZoomLadder({
  regions,
  plates,
  density,
}: {
  regions: ZoomRegion[];
  plates: Record<string, Plate>;
  density: Density[];
}) {
  const [theme, setTheme] = useState<"night" | "day">("night");
  const features = useMemo(
    () => Array.from(new Set(regions.filter((r) => r.theme === theme && r.scale === "1gp").map((r) => r.feature))),
    [regions, theme],
  );
  const [feature, setFeature] = useState("head-print");
  const [smooth, setSmooth] = useState(false);
  const f = features.includes(feature) ? feature : features[0];
  const r201 = regions.find((r) => r.theme === theme && r.scale === "201mp" && r.feature === f);
  const r1 = regions.find((r) => r.theme === theme && r.scale === "1gp" && r.feature === f)!;
  const plate = plates[theme];
  const dens = density.find((d) => d.theme === theme && d.source === DENSITY_FOR[`${theme}/${f}`]);

  const box = (r: ZoomRegion) => {
    const [W, H] = r.full;
    const [x, y, w, h] = r.bounds;
    return { left: `${(x / W) * 100}%`, top: `${(y / H) * 100}%`, width: `${(w / W) * 100}%`, height: `${(h / H) * 100}%` };
  };
  const plateCrop = (r: ZoomRegion) => {
    const [W, H] = r.full;
    const [x, y, w, h] = r.bounds;
    const du = w / W;
    const dv = h / H;
    return {
      backgroundImage: `url(${asset(plate.src)})`,
      backgroundSize: `${100 / du}% ${100 / dv}%`,
      backgroundPosition: `${(x / W / (1 - du)) * 100}% ${(y / H / (1 - dv)) * 100}%`,
      platePx: Math.round(du * plate.w),
    };
  };
  const pc = plateCrop(r1);
  const label = (s: string) => s.replace(/-/g, " ");

  return (
    <div className="qk-zoom">
      <div className="es-controls">
        {(["night", "day"] as const).map((t) => (
          <button key={t} type="button" className="es-btn" aria-pressed={t === theme} onClick={() => setTheme(t)}>
            {THEME_LABEL[t]} ({t === "night" ? "it12" : "r115"})
          </button>
        ))}
        <span className="qk-sep" />
        <button type="button" className="es-btn" aria-pressed={!smooth} onClick={() => setSmooth(!smooth)}>
          {smooth ? "smooth scaling" : "nearest pixel"}
        </button>
      </div>
      <div className="qk-zoom-grid">
        <div className="qk-zoom-plate" style={{ aspectRatio: `${plate.w} / ${plate.h}` }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={asset(plate.src)} alt={plate.caption} />
          {features.map((ft) => {
            const a = regions.find((r) => r.theme === theme && r.scale === "201mp" && r.feature === ft);
            const b = regions.find((r) => r.theme === theme && r.scale === "1gp" && r.feature === ft)!;
            const on = ft === f;
            return (
              <button
                key={ft}
                type="button"
                className="qk-zoom-hit"
                aria-pressed={on}
                aria-label={label(ft)}
                style={box(a ?? b)}
                onClick={() => setFeature(ft)}
              >
                {on ? <span className="qk-zoom-inner" style={a ? relBox(a, b) : undefined} /> : null}
              </button>
            );
          })}
        </div>
        <div className="qk-zoom-side">
          <div className="es-controls" role="tablist" aria-label="region">
            {features.map((ft) => (
              <button key={ft} type="button" role="tab" className="es-btn" aria-selected={ft === f} onClick={() => setFeature(ft)}>
                {label(ft)}
              </button>
            ))}
          </div>
          <div className={`qk-ladder${smooth ? "" : " pixelated"}`}>
            <figure>
              <div className="qk-ladder-img" style={{ backgroundImage: pc.backgroundImage, backgroundSize: pc.backgroundSize, backgroundPosition: pc.backgroundPosition }} role="img" aria-label="web plate, same region" />
              <figcaption>
                web plate · <b>{pc.platePx}px</b> across
              </figcaption>
            </figure>
            {r201 ? (
              <figure>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={asset(r201.src)} alt={`${label(f)} at 201 MP`} loading="lazy" />
                <figcaption>
                  201 MP · {r201.w}px · {r201.seconds}s
                </figcaption>
              </figure>
            ) : null}
            <figure>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={asset(r1.src)} alt={`${label(f)} at 1 GP`} loading="lazy" />
              <figcaption>
                1 GP · {r1.w}px · {r1.seconds}s
              </figcaption>
            </figure>
          </div>
          <p className="qk-zoom-note">
            {dens ? (
              <>
                measured source density for this surface: <b>{dens.d201.toFixed(3)}</b> texels per pixel at 201 MP,{" "}
                <b>{dens.d1gp.toFixed(3)}</b> at 1 GP. one texel would need about {Math.round(1 / dens.d1gp)} final pixels.
              </>
            ) : (
              <>no density row was measured for exactly this receiver; the crops are the evidence here.</>
            )}{" "}
            the 1 GP crop covers the inner box; the 201 MP crop the outer one.
          </p>
        </div>
      </div>
    </div>
  );
}

function relBox(outer: ZoomRegion, inner: ZoomRegion) {
  const [oW, oH] = outer.full;
  const [iW, iH] = inner.full;
  const ox = outer.bounds[0] / oW, oy = outer.bounds[1] / oH, ow = outer.bounds[2] / oW, oh = outer.bounds[3] / oH;
  const ix = inner.bounds[0] / iW, iy = inner.bounds[1] / iH, iw = inner.bounds[2] / iW, ih = inner.bounds[3] / iH;
  return {
    left: `${((ix - ox) / ow) * 100}%`,
    top: `${((iy - oy) / oh) * 100}%`,
    width: `${(iw / ow) * 100}%`,
    height: `${(ih / oh) * 100}%`,
  };
}
