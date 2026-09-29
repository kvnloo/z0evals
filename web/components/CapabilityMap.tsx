"use client";

import { useState } from "react";

/**
 * Function → capability evidence → candidate implementation.
 *
 * The map is deliberately keyed on the FUNCTION, not the model: selecting a
 * function answers "which implementation has evidence for this exact job", which
 * is the architectural claim of the article. Status is a contract, not decoration:
 * MEASURED / BOUNDED / UNKNOWN, and UNKNOWN is a first-class value rather than an
 * empty cell, because a route with no imported evidence must not look finished.
 */
export type CapabilityEntry = {
  id: string;
  label: string;
  route: string;
  implementation: string;
  status: "MEASURED" | "BOUNDED" | "UNKNOWN";
  basis: string;
  consumers?: string[];
  caveat?: string;
};

export default function CapabilityMap({
  functions,
  caption,
}: {
  functions: CapabilityEntry[];
  caption?: string;
}) {
  const [sel, setSel] = useState(functions[0]?.id ?? "");
  const active = functions.find((f) => f.id === sel) ?? functions[0];

  return (
    <figure className="capmap">
      <div className="capmap-list" role="listbox" aria-label="functions">
        {functions.map((f) => (
          <button
            type="button"
            role="option"
            aria-selected={f.id === sel}
            key={f.id}
            className="capmap-row"
            data-status={f.status}
            data-selected={f.id === sel}
            onClick={() => setSel(f.id)}
          >
            <span className="capmap-status" aria-hidden="true" />
            <span className="capmap-fn">{f.label}</span>
            <span className="capmap-arrow" aria-hidden="true">
              →
            </span>
            <span className="capmap-impl">{f.implementation}</span>
            <span className="capmap-badge">{f.status}</span>
          </button>
        ))}
      </div>

      {active ? (
        <div className="capmap-detail" data-status={active.status}>
          <div className="capmap-detail-head">
            <span className="capmap-route">{active.route}</span>
            <strong>{active.implementation}</strong>
            <span className="capmap-badge">{active.status}</span>
          </div>
          <dl>
            <dt>evidence</dt>
            <dd>{active.basis}</dd>
            {active.consumers?.length ? (
              <>
                <dt>consumers</dt>
                <dd>{active.consumers.join(", ")}</dd>
              </>
            ) : null}
            {active.caveat ? (
              <>
                <dt>caveat</dt>
                <dd className="capmap-caveat">{active.caveat}</dd>
              </>
            ) : null}
          </dl>
        </div>
      ) : null}
      {caption ? <figcaption className="fig-caption">{caption}</figcaption> : null}
    </figure>
  );
}
