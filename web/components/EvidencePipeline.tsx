"use client";

import { useEffect, useState } from "react";
import { useReveal } from "./charts/useReveal";

export type PipelineStage = {
  id: string;
  label: string;
  gloss: string;
  ev: string;
  failed?: string;
};

export default function EvidencePipeline({
  stages,
  caption,
}: {
  stages: PipelineStage[];
  caption?: string;
}) {
  const { ref, shown } = useReveal<HTMLElement>(0.05, "120px 0px");
  const [reached, setReached] = useState(stages.length);
  const [active, setActive] = useState(Math.max(0, stages.length - 1));

  useEffect(() => {
    if (!shown) {
      setReached(0);
      setActive(0);
      return;
    }
    if (reached >= stages.length) return;

    const timer = window.setTimeout(() => {
      setReached((value) => {
        const next = Math.min(stages.length, value + 1);
        setActive(Math.max(0, next - 1));
        return next;
      });
    }, reached === 0 ? 180 : 360);

    return () => window.clearTimeout(timer);
  }, [shown, reached, stages.length]);

  const current = stages[Math.min(active, Math.max(0, stages.length - 1))];

  return (
    <figure className="pipeline" ref={ref}>
      <ol className="pipeline-track">
        {stages.map((stage, index) => (
          <li
            key={stage.id}
            className="pipeline-stage"
            data-state={index < reached ? "reached" : "pending"}
            data-active={index === active}
            onMouseEnter={() => setActive(index)}
            onFocus={() => setActive(index)}
            tabIndex={0}
          >
            <span className="pipeline-dot" aria-hidden="true" />
            <span className="pipeline-label">{stage.label}</span>
          </li>
        ))}
      </ol>
      <div className="pipeline-detail" data-stage={current?.id}>
        <div className="pipeline-detail-head">
          <span className="pipeline-ev">{current?.ev}</span>
          <strong>{current?.label}</strong>
          <span className="pipeline-gloss">{current?.gloss}</span>
        </div>
        {current?.failed ? (
          <p className="pipeline-failed">
            <span className="pipeline-failed-tag">falsified here</span> {current.failed}
          </p>
        ) : null}
      </div>
      {caption ? <figcaption className="fig-caption">{caption}</figcaption> : null}
    </figure>
  );
}
