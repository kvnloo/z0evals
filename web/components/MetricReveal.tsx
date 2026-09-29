"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Reveal a headline number, then optionally disclose what it does not mean.
 *
 * Two-stage on purpose: the first figure is the one a reader would stop at, and
 * the second is the qualification that makes it honest. Both come from the same
 * data entry, so a revision cannot update one without the other.
 *
 * Server render is the FINAL state (number shown, caveat shown), so the figure is
 * correct with no JavaScript. The animation only ever plays forward from hidden.
 */
export type MetricRevealStage = {
  k: string;
  v: string;
  s?: string;
  kind?: "good" | "bad" | "neutral";
};

export default function MetricReveal({
  stages,
  caption,
  delayMs = 120,
}: {
  stages: MetricRevealStage[];
  caption?: string;
  delayMs?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [step, setStep] = useState(stages.length);
  const [armed, setArmed] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node || typeof window === "undefined") return;
    if (node.getBoundingClientRect().top > window.innerHeight * 0.9) {
      setStep(0);
      setArmed(true);
    }
  }, []);

  useEffect(() => {
    if (!armed || step >= stages.length) return;
    const t = setTimeout(() => setStep((s) => s + 1), delayMs);
    return () => clearTimeout(t);
  }, [armed, step, stages.length, delayMs]);

  return (
    <figure className="metric-reveal" ref={ref}>
      <div className="metric-reveal-stages">
        {stages.map((st, i) => (
          <div
            className="metric-reveal-stage"
            data-kind={st.kind ?? "neutral"}
            data-shown={i < step}
            key={st.k}
          >
            <div className="k">{st.k}</div>
            <div className="v">{st.v}</div>
            {st.s ? <div className="s">{st.s}</div> : null}
          </div>
        ))}
      </div>
      {caption ? <figcaption className="fig-caption">{caption}</figcaption> : null}
    </figure>
  );
}
