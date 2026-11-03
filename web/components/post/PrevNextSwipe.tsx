"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import SiteLink from "@/components/site/SiteLink";
import { useSwipe } from "@/lib/ux/gesture";
import { haptic } from "@/lib/ux/haptics";
import type { EntryLite } from "@/lib/catalog";

/**
 * prev / next cards. On touch screens the pair (and only the pair, never the article)
 * swipes horizontally: past the threshold it peeks the target title and ticks once;
 * release commits by velocity or distance.
 */
export default function PrevNextSwipe({ prev, next }: { prev?: EntryLite; next?: EntryLite }) {
  const router = useRouter();
  const pair = useRef<HTMLDivElement>(null);
  const [peek, setPeek] = useState<"prev" | "next" | null>(null);
  const peekRef = useRef<"prev" | "next" | null>(null);
  const extent = () => Math.min(260, (pair.current?.offsetWidth ?? 360) * 0.45);

  useSwipe(pair, {
    axis: "x",
    canStart: (e) => e.pointerType !== "mouse",
    range: () => [next ? -extent() : 0, prev ? extent() : 0],
    extent,
    onMove: (x) => {
      const past = Math.abs(x) > 0.4 * extent();
      const want = past ? (x > 0 && prev ? "prev" : x < 0 && next ? "next" : null) : null;
      if (want !== peekRef.current) {
        peekRef.current = want;
        setPeek(want);
        if (want) haptic.select();
      }
    },
    onRelease: ({ commit, dir }) => {
      const target = dir === 1 ? prev : next;
      if (commit && target) {
        haptic.tap();
        return dir * extent();
      }
      return 0;
    },
    onSettled: (to) => {
      peekRef.current = null;
      setPeek(null);
      if (to > 0 && prev) router.push(prev.href);
      else if (to < 0 && next) router.push(next.href);
      if (to !== 0 && pair.current) pair.current.style.transform = "";
    },
  });

  if (!prev && !next) return null;
  return (
    <div className="prevnext" data-peek={peek ?? undefined}>
      <div ref={pair} className="prevnext-pair">
        {prev ? (
          <SiteLink href={prev.href} className="prevnext-card" data-press="row" rel="prev">
            <span className="prevnext-dir">← previous</span>
            <span className="prevnext-title">{prev.title}</span>
          </SiteLink>
        ) : <span className="prevnext-card prevnext-empty" aria-hidden="true" />}
        {next ? (
          <SiteLink href={next.href} className="prevnext-card prevnext-next" data-press="row" rel="next">
            <span className="prevnext-dir">next →</span>
            <span className="prevnext-title">{next.title}</span>
          </SiteLink>
        ) : <span className="prevnext-card prevnext-empty" aria-hidden="true" />}
      </div>
      <p className="prevnext-peek" aria-live="polite">
        {peek === "prev" && prev ? `release for ${prev.title}` : peek === "next" && next ? `release for ${next.title}` : " "}
      </p>
    </div>
  );
}
