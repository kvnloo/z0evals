"use client";

import { useEffect, useId, useRef, useState } from "react";
import { asset } from "@/lib/asset";

/**
 * A live ephemeral-ui card (vendored under public/embeds/ephemeral-ui) in a same-origin
 * frame. The frame reports its content height, so the figure grows with the card instead
 * of scrolling inside the essay. Loads lazily; the reserved height avoids layout jumps.
 * The site is dark only, so the default host theme is T3 Code dark.
 */
export default function KitEmbed({
  params,
  title,
  theme = "t3-dark",
  minHeight = 420,
}: {
  /** query for embed.html, e.g. "view=kind&kind=trace" or "view=ask&q=why was this session slow?" */
  params: string;
  title: string;
  theme?: string;
  minHeight?: number;
}) {
  const id = useId();
  const ref = useRef<HTMLIFrameElement>(null);
  const [height, setHeight] = useState(minHeight);

  useEffect(() => {
    const onMsg = (e: MessageEvent) => {
      if (e.source !== ref.current?.contentWindow) return;
      const d = e.data as { type?: string; height?: number };
      if (d?.type === "eui-embed-height" && typeof d.height === "number") setHeight(Math.max(120, d.height));
    };
    window.addEventListener("message", onMsg);
    return () => window.removeEventListener("message", onMsg);
  }, []);

  const src = `${asset("/embeds/ephemeral-ui/embed.html")}?${params}&theme=${theme}&id=${encodeURIComponent(id)}`;
  return (
    <div className="es-embed">
      <iframe ref={ref} src={src} title={title} loading="lazy" style={{ height }} />
    </div>
  );
}
