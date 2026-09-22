"use client";
import { useMemo, useState } from "react";
import type { Matrix } from "@/data/types";
import ReplayChart from "./ReplayChart";
import ObservationScrubber from "./ObservationScrubber";
import Heatmap from "./Heatmap";
import FamilyStack from "./FamilyStack";
import ArmTable from "./ArmTable";

const DEFAULT_ARMS = [
  "compiler+hammer2.1_3b",
  "compiler+qwen3.5_4b",
  "compiler+qwen3.5_9b",
  "compiler+jev",
  "unfiltered+hammer2.1_3b",
];

/**
 * Holds the control state the reference keeps across its whole results section:
 * which arms are plotted, and which task family is in focus. Every control here
 * has a counterpart in the reference (trace selector, tool chips, observer
 * table, heatmap).
 */
export default function ResultsExplorer({ matrix }: { matrix: Matrix }) {
  const [arms, setArms] = useState<string[]>(DEFAULT_ARMS);
  const [family, setFamily] = useState<string | null>(null);

  const toggle = (id: string) =>
    setArms((cur) => (cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id]));

  const shown = useMemo(
    () => (family ? matrix.states.filter((s) => s.family === family) : matrix.states),
    [matrix, family]
  );
  const scoped: Matrix = useMemo(
    () => ({ ...matrix, states: shown }),
    [matrix, shown]
  );

  return (
    <>
      <div className="chart-tabs" role="group" aria-label="arms shown">
        {matrix.arms.map((a) => (
          <button key={a.id} type="button" aria-pressed={arms.includes(a.id)}
                  onClick={() => toggle(a.id)}
                  style={a.unfiltered ? { borderColor: arms.includes(a.id) ? "#b91c1c" : undefined } : undefined}>
            {a.label}
          </button>
        ))}
      </div>

      <figure>
        <div className="fig-body"><ReplayChart matrix={scoped} selected={arms} /></div>
        <figcaption>
          <span className="fig-n">fig 2</span>
          replayable per-state curves. each point is one bounded-choice state in sweep
          order; the y value is that state&rsquo;s measured decision latency divided by the
          arm&rsquo;s own p50, so a flat line means the arm behaved like its median.
          press <strong>replay</strong> or drag the playhead.
          {family ? <> filtered to <strong>{family}</strong>.</> : null}
        </figcaption>
      </figure>

      <figure>
        <div className="fig-body"><ObservationScrubber matrix={scoped} /></div>
        <figcaption>
          <span className="fig-n">fig 3</span>
          scrub to any state and read the underlying evidence: what each arm chose, its
          measured median, its calibrated confidence, and the gold action where the
          fixture has one. repetition splits are shown rather than averaged away.
        </figcaption>
      </figure>

      <figure>
        <div className="fig-body"><FamilyStack families={matrix.families} selected={family} onSelect={setFamily} /></div>
        <figcaption>
          <span className="fig-n">fig 7</span>
          where the work and the failures actually sit, by state family. the only
          dangerous selections on the whole page are in <strong>security</strong>.
        </figcaption>
      </figure>

      <figure>
        <div className="fig-body"><Heatmap matrix={matrix} /></div>
        <figcaption>
          <span className="fig-n">fig 8</span>
          outcome matrix: {matrix.states.length} states × {matrix.arms.length} arms.
          switch between success rate, dangerous selections, and repetition splits.
          every cell is a measured cell, not an interpolation.
        </figcaption>
      </figure>

      <ArmTable arms={matrix.arms} highlight={arms} />
    </>
  );
}
