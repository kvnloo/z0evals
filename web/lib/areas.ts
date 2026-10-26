// Research areas. One list for the log, the research index, the home chips and
// scripts/build_posts.py (AREAS there must match the ids here).
export type AreaId = "governance" | "speed-ux" | "memory" | "cost-routing" | "research" | "fleet";
export type Area = { id: AreaId; label: string; blurb: string };

export const AREAS: readonly Area[] = [
  { id: "memory", label: "memory", blurb: "what agents remember, and whether it is still true" },
  { id: "cost-routing", label: "cost & routing", blurb: "which decisions deserve a model, and what they cost" },
  { id: "governance", label: "laws & governance", blurb: "statecharts, authority checks and admission bars" },
  { id: "speed-ux", label: "speed & ux", blurb: "harness latency, phone control and the feel of the loop" },
  { id: "fleet", label: "fleet", blurb: "placement, capacity and the machines underneath" },
  { id: "research", label: "papers & ideas", blurb: "syntheses, architecture and ideas not yet measured" },
] as const;

export const AREA_IDS = AREAS.map((a) => a.id);

export function areaLabel(id: string): string {
  return AREAS.find((a) => a.id === id)?.label ?? id;
}
