// Server-only catalog: every post and bespoke study as one sorted list, plus the joins
// the site needs (log entries, prev/next, related). Reads build outputs with node:fs,
// so import it only from server components.
import fs from "node:fs";
import path from "node:path";
import { hasBespokePage, readIndex } from "./posts";
import { postStatus, type Tone } from "./status";
import type { StoryMeta } from "./story";

export type Entry = {
  slug: string;
  href: string;
  title: string;
  dek: string;
  area: string;
  tags: string[];
  status: string;
  statusRaw: string;
  tone: Tone;
  published: string;
  updated?: string;
  dateLabel: string;
  kind: string;
  series?: string;
  bespoke: boolean;
  logIds: string[];
  supersededBy?: string;
};

export type LogRef = { id: string; title: string; status: string; date: string; area: string; post?: string | null };

type StudyConf = {
  slug: string;
  fromJson?: string;
  title?: string;
  subtitle?: string;
  dek: string;
  lede?: string;
  author?: string;
  date?: string;
  area: string;
  published: string;
  status?: string;
  kind?: string;
  supersededBy?: string;
};

export type SiteConf = {
  positioning: string;
  repo: string;
  featured: string;
  highlights: string[];
  latestCount: number;
  studies: StudyConf[];
};

const DATA = path.join(process.cwd(), "data");
const readJson = <T,>(file: string): T => JSON.parse(fs.readFileSync(path.join(DATA, file), "utf8")) as T;

let cache: { site: SiteConf; entries: Entry[]; log: { updated: string; entries: LogRef[] }; studies: Map<string, StudyConf & StoryMeta> } | null = null;

function resolveStudy(s: StudyConf): StudyConf & StoryMeta {
  let base: Partial<StoryMeta> = {};
  if (s.fromJson) {
    const [file, key] = s.fromJson.split("#");
    const doc = readJson<Record<string, unknown>>(file);
    base = (key ? doc[key] : doc) as Partial<StoryMeta>;
  }
  return {
    ...s,
    title: s.title ?? base.title ?? s.slug,
    subtitle: s.subtitle ?? base.subtitle ?? "",
    author: s.author ?? base.author ?? "zer0 research",
    date: s.date ?? base.date ?? s.published,
    status: s.status ?? base.status ?? "draft",
    lede: s.lede ?? base.lede ?? "",
  };
}

function load() {
  if (cache) return cache;
  const site = readJson<SiteConf>("site.json");
  const log = readJson<{ updated: string; entries: LogRef[] }>("research-log.json");
  const studies = new Map(site.studies.map((s) => [s.slug, resolveStudy(s)]));

  const logIdsFor = (slug: string, declared: string[]) => {
    const ids = new Set(declared);
    for (const e of log.entries) if (e.post === slug || e.id === slug) ids.add(e.id);
    return [...ids].filter((id) => log.entries.some((e) => e.id === id));
  };

  const bySlug = new Map<string, Entry>();
  for (const p of readIndex()) {
    const [tone, label] = postStatus(p.status);
    bySlug.set(p.slug, {
      slug: p.slug,
      href: `/${p.slug}/`,
      title: p.title,
      dek: p.dek,
      area: p.area,
      tags: p.tags,
      status: label,
      statusRaw: p.status,
      tone,
      published: p.published,
      updated: p.updated ?? undefined,
      dateLabel: p.date,
      kind: p.kind,
      series: p.series ?? undefined,
      bespoke: hasBespokePage(p.slug),
      logIds: logIdsFor(p.slug, p.log),
    });
  }
  // bespoke studies win over their markdown twin: their page is what the URL serves
  for (const s of studies.values()) {
    const prev = bySlug.get(s.slug);
    const [tone, label] = postStatus(s.status);
    bySlug.set(s.slug, {
      slug: s.slug,
      href: `/${s.slug}/`,
      title: s.title,
      dek: s.dek,
      area: s.area,
      tags: prev?.tags ?? [],
      status: label,
      statusRaw: s.status,
      tone,
      published: s.published,
      updated: prev?.updated,
      dateLabel: s.date,
      kind: s.kind ?? "study",
      series: prev?.series,
      bespoke: true,
      logIds: logIdsFor(s.slug, []),
      supersededBy: s.supersededBy,
    });
  }
  const entries = [...bySlug.values()].sort(
    (a, b) => b.published.localeCompare(a.published) || a.slug.localeCompare(b.slug),
  );
  cache = { site, entries, log, studies };
  return cache;
}

export function site(): SiteConf {
  return load().site;
}

export function allEntries(): Entry[] {
  return load().entries;
}

export function entry(slug: string): Entry | undefined {
  return load().entries.find((e) => e.slug === slug);
}

export function featured(): Entry {
  const { site: conf, entries } = load();
  return entries.find((e) => e.slug === conf.featured) ?? entries[0];
}

export function highlights(): Entry[] {
  const { site: conf } = load();
  return conf.highlights.map((s) => entry(s)).filter((e): e is Entry => Boolean(e));
}

export function latest(n: number): Entry[] {
  const f = featured();
  return load().entries.filter((e) => e.slug !== f.slug).slice(0, n);
}

export function studies(): Entry[] {
  return load().site.studies.map((s) => entry(s.slug)).filter((e): e is Entry => Boolean(e));
}

export function studySlugs(): string[] {
  return load().site.studies.map((s) => s.slug);
}

// StoryMeta for a bespoke page, so its title/date/status live only in site.json
export function studyMeta(slug: string): StoryMeta {
  const s = load().studies.get(slug);
  if (!s) throw new Error(`site.json has no study ${slug}`);
  return { title: s.title, subtitle: s.subtitle, author: s.author, date: s.date, status: s.status, lede: s.lede };
}

export function logUpdated(): string {
  return load().log.updated;
}

export function logEntries(slug: string): LogRef[] {
  const e = entry(slug);
  if (!e) return [];
  const all = load().log.entries;
  return e.logIds.map((id) => all.find((x) => x.id === id)).filter((x): x is LogRef => Boolean(x));
}

export function neighbors(slug: string): { prev?: Entry; next?: Entry; related: Entry[] } {
  const entries = load().entries;
  const me = entries.find((e) => e.slug === slug);
  if (!me) return { related: [] };
  // oldest first, so "next" reads forward in time
  const pool = (me.series ? entries.filter((e) => e.series === me.series) : entries).slice().reverse();
  const usable = pool.length > 1 ? pool : entries.slice().reverse();
  const i = usable.findIndex((e) => e.slug === slug);
  const taken = new Set([slug, usable[i - 1]?.slug, usable[i + 1]?.slug]);
  const related = entries.filter((e) => e.area === me.area && !taken.has(e.slug)).slice(0, 3);
  return { prev: usable[i - 1], next: usable[i + 1], related };
}

export type EntryLite = Pick<Entry, "slug" | "href" | "title" | "dek" | "area" | "status" | "tone" | "published" | "kind" | "bespoke">;
export const lite = (e: Entry): EntryLite => ({
  slug: e.slug, href: e.href, title: e.title, dek: e.dek, area: e.area, status: e.status,
  tone: e.tone, published: e.published, kind: e.kind, bespoke: e.bespoke,
});

export { shortDate, monthLabel } from "./dates";
