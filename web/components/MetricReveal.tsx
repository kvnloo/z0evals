"use client";

import { useEffect, useState } from "react";
import { useReveal } from "./charts/useReveal";

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
  const { ref, shown } = useReveal<HTMLElement>(0.05, "120px 0px");
  const [step, setStep] = useState(stages.length);

  useEffect(() => {
    if (!shown) {
      setStep(0);
      return;
    }
    if (step >= stages.length) return;
    const timer = window.setTimeout(
      () => setStep((value) => Math.min(stages.length, value + 1)),
      delayMs,
    );
    return () => window.clearTimeout(timer);
  }, [shown, step, stages.length, delayMs]);

  return (
    <figure className="metric-reveal" ref={ref}>
      <div className="metric-reveal-stages">
        {stages.map((stage, index) => (
          <div
            className="metric-reveal-stage"
            data-kind={stage.kind ?? "neutral"}
            data-shown={index < step}
            key={stage.k}
          >
            <div className="k">{stage.k}</div>
            <div className="v">{stage.v}</div>
            {stage.s ? <div className="s">{stage.s}</div> : null}
          </div>
        ))}
      </div>
      {caption ? <figcaption className="fig-caption">{caption}</figcaption> : null}
    </figure>
  );
}
