// Optimization techniques: the second facet of the research log. An entry has one
// area (the system or field under study) and any number of techniques (how it tries to
// make that system better). scripts/build_posts.py TECHNIQUES must match the ids here.
export type Technique = { id: string; label: string; blurb: string };

export const TECHNIQUES: readonly Technique[] = [
  { id: "output-format", label: "output format", blurb: "make the model write less: compact answer languages instead of full pages" },
  { id: "context-reduction", label: "context reduction", blurb: "send less: compaction, state packets, distilled corrections, prefix trimming" },
  { id: "model-routing", label: "model routing", blurb: "pick the cheapest model that is good enough, per decision or task" },
  { id: "local-inference", label: "local inference", blurb: "engines, quantization and placement for models on our own hardware" },
  { id: "caching-reuse", label: "caching & reuse", blurb: "keep and reuse work: warm processes, prefix caches, copy-on-write workspaces" },
  { id: "scheduling", label: "scheduling & placement", blurb: "where and when work runs: admission, fleets, fan-out, pacing" },
  { id: "algorithmic", label: "algorithms & math", blurb: "new algorithms or proved math results applied to a hot path" },
  { id: "search-optimization", label: "search & autoresearch", blurb: "prompt/program search and measured keep-or-revert hill-climbs" },
  { id: "formal-methods", label: "formal methods", blurb: "proved laws, statecharts and fail-closed gates" },
  { id: "measurement", label: "measurement method", blurb: "how we measure: ledgers, replays, referees, judges" },
] as const;

export function techniqueLabel(id: string): string {
  return TECHNIQUES.find((t) => t.id === id)?.label ?? id;
}
