"use client";

import { useReveal } from "./charts/useReveal";

/**
 * Provider routing and saturation.
 *
 * Two things this component refuses to blur:
 *   - a cap is a POLICY INPUT unless it was measured, so `capMeasured` drives a
 *     visible label rather than the bar pretending to be evidence;
 *   - headroom is UNKNOWN where the source was not reproduced, so an unknown
 *     provider renders an explicit dashed placeholder instead of a short bar that
 *     would read as "little headroom".
 */
export type ProviderRow = {
  provider: string;
  model: string;
  tasks?: number;
  cap: number | null;
  capMeasured?: boolean;
  headroom?: "UNKNOWN";
};

export type AdmissionTest = {
  admitted: number;
  capped: number;
  peak: number;
  fixture: string;
};

export default function RoutingTrace({
  providers,
  admission,
  caption,
}: {
  providers: ProviderRow[];
  admission?: AdmissionTest;
  caption?: string;
}) {
  const { ref, shown } = useReveal<HTMLElement>(0.2);
  const maxTasks = Math.max(1, ...providers.map((p) => p.tasks ?? 0));

  return (
    <figure className="routing-trace" ref={ref} data-shown={shown}>
      <ul className="rt-list">
        {providers.map((p) => (
          <li className="rt-row" key={p.provider}>
            <span className="rt-provider">{p.provider}</span>
            <span className="rt-model">{p.model}</span>
            <span className="rt-bar-track">
              {typeof p.tasks === "number" ? (
                <span
                  className="rt-bar"
                  style={{ width: `${(p.tasks / maxTasks) * 100}%` }}
                  aria-hidden="true"
                />
              ) : null}
            </span>
            <span className="rt-tasks">
              {typeof p.tasks === "number" ? `${p.tasks} task${p.tasks === 1 ? "" : "s"}` : "—"}
            </span>
            <span className="rt-cap" data-measured={Boolean(p.capMeasured)}>
              {p.cap === null ? "cap UNKNOWN" : `cap ${p.cap}`}
              {p.cap !== null && !p.capMeasured ? <em> policy</em> : null}
            </span>
          </li>
        ))}
      </ul>

      {admission ? (
        <div className="rt-admission">
          <div className="rt-admission-label">Admission control — measured</div>
          <div className="rt-admission-track" aria-hidden="true">
            <span className="rt-admitted" style={{ flexGrow: admission.admitted }} />
            <span className="rt-capped" style={{ flexGrow: admission.capped }} />
          </div>
          <div className="rt-admission-legend">
            <span>
              <b>{admission.admitted}</b> admitted
            </span>
            <span>
              <b>{admission.capped}</b> capped before provider HTTP
            </span>
            <span>
              peak inflight <b>{admission.peak}</b>
            </span>
          </div>
          <p className="rt-fixture">{admission.fixture}</p>
        </div>
      ) : null}

      {caption ? <figcaption className="fig-caption">{caption}</figcaption> : null}
    </figure>
  );
}
