// Research areas. One list for the log, the research index, the home chips and
// scripts/build_posts.py (AREAS there must match the ids here).
// Product areas come first: they name the system under test. The last four are
// cross-cutting. docs/areas.md says how to pick one.
export type AreaId =
  | "hermes"
  | "small-models"
  | "generative-ui"
  | "device-use"
  | "memory"
  | "governance"
  | "fleet"
  | "research";
export type Area = { id: AreaId; label: string; blurb: string };

export const AREAS: readonly Area[] = [
  { id: "hermes", label: "hermes & harnesses", blurb: "hermes, claude code, omp and t3 code: speed, cost and the agent loop" },
  { id: "small-models", label: "small models & routing", blurb: "which decisions deserve a model, local slms, quota and offload" },
  { id: "generative-ui", label: "generative ui", blurb: "interfaces agents generate: formats, tokens and validity" },
  { id: "device-use", label: "phone & computer use", blurb: "agents driving phones, desktops and the web" },
  { id: "memory", label: "memory", blurb: "what agents remember, and whether it is still true" },
  { id: "governance", label: "laws & governance", blurb: "statecharts, authority checks and admission bars" },
  { id: "fleet", label: "fleet", blurb: "placement, capacity and the machines underneath" },
  { id: "research", label: "papers & ideas", blurb: "syntheses, architecture and ideas not yet measured" },
] as const;

export const AREA_IDS = AREAS.map((a) => a.id);

export function areaLabel(id: string): string {
  return AREAS.find((a) => a.id === id)?.label ?? id;
}
