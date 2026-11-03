"use client";

import { Sprite } from "./LineageSwimlane";
import type { Row, Trial } from "./types";
import { OUTCOME_COLOR } from "./types";

/** Teaser visual: a slow scroll through every 8th preserved render. */
export function SpriteWall({ rows, pages }: { rows: Row[]; pages: string[] }) {
  const pick = rows.filter((_, i) => i % 8 === 0);
  return (
    <div className="qk-wall" aria-hidden>
      <div className="qk-wall-scroll">
        {[...pick, ...pick].map((r, i) => (
          <Sprite key={i} row={r} pages={pages} className="qk-wall-sprite" box={0} />
        ))}
      </div>
    </div>
  );
}

/** Teaser visual: one square per review decision, in log order. */
export function DecisionGrid({ trials }: { trials: Trial[] }) {
  const cells = trials.flatMap((t) => Array.from({ length: t.count ?? 1 }, () => t.outcome));
  return (
    <div className="qk-dgrid" role="img" aria-label={`${cells.length} decisions; green squares were promoted`}>
      {cells.map((o, i) => (
        <span key={i} style={{ background: OUTCOME_COLOR[o], opacity: o === "promoted" ? 1 : 0.45 }} />
      ))}
    </div>
  );
}
