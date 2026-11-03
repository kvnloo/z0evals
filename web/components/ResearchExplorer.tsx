"use client";

import { useEffect, useMemo, useState } from "react";
import GelSeg from "@/components/site/GelSeg";
import EntryRow from "@/components/site/EntryRow";
import { AREAS } from "@/lib/areas";
import { monthLabel } from "@/lib/dates";
import { haptic } from "@/lib/ux/haptics";
import type { EntryLite } from "@/lib/catalog";

export type ResearchItem = EntryLite & { measured: boolean; logCount: number; search: string };

/**
 * The full research index. Server-rendered with every entry (works without JS); area,
 * "measured only" and search filter as progressive enhancement, synced to the query
 * string with history.replaceState.
 */
export default function ResearchExplorer({ items }: { items: ResearchItem[] }) {
  const [area, setArea] = useState("all");
  const [measured, setMeasured] = useState(false);
  const [q, setQ] = useState("");

  // read the initial filter from the URL (?area=memory&measured=1&q=router)
  useEffect(() => {
    const p = new URLSearchParams(location.search);
    const a = p.get("area");
    if (a && AREAS.some((x) => x.id === a)) setArea(a);
    if (p.get("measured") === "1") setMeasured(true);
    if (p.get("q")) setQ(p.get("q") ?? "");
  }, []);

  useEffect(() => {
    const p = new URLSearchParams(location.search);
    const set = (k: string, v: string | null) => (v ? p.set(k, v) : p.delete(k));
    set("area", area === "all" ? null : area);
    set("measured", measured ? "1" : null);
    set("q", q.trim() || null);
    const qs = p.toString();
    const url = `${location.pathname}${qs ? `?${qs}` : ""}${location.hash}`;
    if (url !== `${location.pathname}${location.search}${location.hash}`) history.replaceState(history.state, "", url);
  }, [area, measured, q]);

  const shown = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return items.filter(
      (e) => (area === "all" || e.area === area) && (!measured || e.measured) && (!needle || e.search.includes(needle)),
    );
  }, [items, area, measured, q]);

  const groups = useMemo(() => {
    const m = new Map<string, ResearchItem[]>();
    for (const e of shown) {
      const k = monthLabel(e.published);
      m.set(k, [...(m.get(k) ?? []), e]);
    }
    return [...m.entries()];
  }, [shown]);

  const count = (a: string) => items.filter((e) => a === "all" || e.area === a).length;
  const clear = () => {
    setArea("all");
    setMeasured(false);
    setQ("");
  };

  return (
    <div className="research">
      <div className="filter-bar">
        <GelSeg label="area" value={area} onChange={setArea}
          options={[{ id: "all", label: "all", count: count("all") }, ...AREAS.map((a) => ({ id: a.id, label: a.label, count: count(a.id) }))]} />
        <div className="filter-row2">
          <button type="button" className="log-toggle" data-press="control" aria-pressed={measured}
            onClick={() => { haptic.select(); setMeasured(!measured); }}>
            <span className="dot ok" aria-hidden="true" /> measured only
          </button>
          <input className="log-search" type="search" placeholder="search" value={q}
            onChange={(e) => setQ(e.target.value)} aria-label="search research" />
        </div>
      </div>
      <p className="log-meta" aria-live="polite">{shown.length} of {items.length} write-ups, newest first</p>
      {groups.length ? (
        groups.map(([month, list]) => (
          <section key={month} className="month-group" aria-label={month}>
            <h2 className="month-head">{month}</h2>
            <ol className="entry-list">
              {list.map((e) => (
                <EntryRow key={e.slug} e={e} logCount={e.logCount} />
              ))}
            </ol>
          </section>
        ))
      ) : (
        <p className="empty-filter">
          nothing matches those filters.{" "}
          <button type="button" className="log-toggle" data-press="control" onClick={clear}>clear filters</button>
        </p>
      )}
    </div>
  );
}
