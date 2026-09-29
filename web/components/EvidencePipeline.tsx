"use client";

import { useEffect, useRef, useState } from "react";

/**
 * The evidence ladder: configured → selected → executed → consumed → receipted.
 *
 * Each stage advances only when the reader reaches it, and each stage carries the
 * point at which it was FALSIFIED at least once in this study. A pipeline that
 * only shows forward progress would make the same mistake the study is about, so
 * the failure note is part of the component rather than an aside in the prose.
 *
 * Generic: pass any stages with {id,label,gloss,ev,failed}.
 */
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
  const ref = useRef<HTMLDivElement>(null);
  const [reached, setReached] = useState(stages.length);
  const [active, setActive] = useState(stages.length - 1);

  useEffect(() => {
    const node = ref.current;
    if (!node || typeof window === "undefined") return;
    if (node.getBoundingClientRect().top > window.innerHeight * 0.85) {
      setReached(0);
      setActive(0);
      const io = new IntersectionObserver(
        (entries) => {
          if (!entries[0]?.isIntersecting) return;
          let i = 0;
          const tick = () => {
            i += 1;
            setReached(i);
            setActive(Math.min(i - 1, stages.length - 1));
            if (i < stages.length) setTimeout(tick, 420);
          };
          setTimeout(tick, 200);
          io.disconnect();
        },
        { threshold: 0.2 },
      );
      io.observe(node);
      return () => io.disconnect();
    }
  }, [stages.length]);

  const current = stages[Math.min(active, stages.length - 1)];

  return (
    <figure className="pipeline" ref={ref}>
      <ol className="pipeline-track">
        {stages.map((s, i) => (
          <li
            key={s.id}
            className="pipeline-stage"
            data-state={i < reached ? "reached" : "pending"}
            data-active={i === active}
            onMouseEnter={() => setActive(i)}
            onFocus={() => setActive(i)}
            tabIndex={0}
          >
            <span className="pipeline-dot" aria-hidden="true" />
            <span className="pipeline-label">{s.label}</span>
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
