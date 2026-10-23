"use client";

import { useMemo, useState } from "react";
import { STATUS } from "@/lib/logStatus";

export type LogLink = { label: string; url: string };
export type LogEntry = {
  id: string;
  title: string;
  area: string;
  question: string;
  status: string;
  date: string;
  finding: string;
  caveat: string;
  links: LogLink[];
  interesting?: boolean;
  why?: string;
  post?: string | null;
};

const AREAS: [string, string][] = [
  ["all", "everything"],
  ["memory", "memory"],
  ["cost-routing", "cost & routing"],
  ["governance", "laws & governance"],
  ["speed-ux", "speed & ux"],
  ["fleet", "fleet"],
  ["research", "papers & ideas"],
];


export default function LogExplorer({ entries }: { entries: LogEntry[] }) {
  const [area, setArea] = useState("all");
  const [onlyHot, setOnlyHot] = useState(false);
  const [q, setQ] = useState("");
  const shown = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return entries
      .filter((e) => area === "all" || e.area === area)
      .filter((e) => !onlyHot || e.interesting)
      .filter((e) => !needle || `${e.title} ${e.question} ${e.finding} ${e.id}`.toLowerCase().includes(needle))
      .sort((a, b) => (b.date || "").localeCompare(a.date || ""));
  }, [entries, area, onlyHot, q]);
  const count = (a: string) => entries.filter((e) => a === "all" || e.area === a).length;

  return (
    <div className="log-explorer">
      <div className="log-controls">
        <div className="log-seg" role="group" aria-label="area">
          {AREAS.map(([k, label]) => (
            <button key={k} type="button" aria-pressed={area === k} onClick={() => setArea(k)}>
              {label} <span className="n">{count(k)}</span>
            </button>
          ))}
        </div>
        <div className="log-row2">
          <button type="button" className="log-toggle" aria-pressed={onlyHot} onClick={() => setOnlyHot(!onlyHot)}>
            <span className="dot gold" /> in focus now
          </button>
          <input className="log-search" type="search" placeholder="search findings" value={q} onChange={(e) => setQ(e.target.value)} aria-label="search findings" />
        </div>
      </div>
      <p className="log-meta">{shown.length} of {entries.length} entries, newest first</p>
      <ol className="log-list">
        {shown.map((e) => {
          const [tone, label] = STATUS[e.status] ?? ["faint", e.status];
          return (
            <li key={e.id} className="log-card" data-hot={e.interesting ? "true" : undefined} id={`e-${e.id}`}>
              <div className="log-card-top">
                <span className={`log-status ${tone}`}><span className={`dot ${tone}`} />{label}</span>
                <span className="log-area">{AREAS.find(([k]) => k === e.area)?.[1] ?? e.area}</span>
                <span className="log-date">{e.date}</span>
              </div>
              <h3>{e.post ? <a href={`../${e.post}/`}>{e.title}</a> : e.title}</h3>
              <p className="log-q">{e.question}</p>
              {e.finding ? <p className="log-finding">{e.finding}</p> : null}
              {e.why ? <p className={e.interesting ? "log-why hot" : "log-why"}>{e.interesting ? <span className="dot gold" /> : null}{e.interesting ? "in focus · " : "why it matters · "}{e.why}</p> : null}
              {e.caveat ? (
                <details className="log-caveat">
                  <summary>what this does not show</summary>
                  <p>{e.caveat}</p>
                </details>
              ) : null}
              <div className="log-links">
                {e.post ? <a className="log-post" href={`../${e.post}/`}>read the post</a> : null}
                {e.links.map((l) => (
                  <a key={l.url} href={l.url}>{l.label}</a>
                ))}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
