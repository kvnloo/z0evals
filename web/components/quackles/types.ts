import type raw from "@/data/quackles-lineage-v0.json";

/** [themeIdx, timeMs, statusIdx, phaseIdx, label, atlasPage, [x,y,w,h] in page fractions, datedByReceipt(0|1)] */
export type Row = [number, number, number, number, string, number, number[], number];
export type Plate = { src: string; w: number; h: number; caption: string; date?: string | null };
export type Trial = {
  t: string;
  scene: string;
  candidate: string;
  against: string;
  outcome: string;
  reviewers: string;
  why: string;
  lesson?: string;
  count?: number;
};
export type ZoomRegion = {
  theme: string;
  scale: string;
  feature: string;
  full: number[];
  bounds: number[];
  seconds: number;
  w: number;
  h: number;
  lap: number;
  grad: number;
  blur1: number;
  src: string;
};

export type QuacklesData = Omit<typeof raw, "entries" | "current" | "references" | "trials" | "zoomRegions"> & {
  entries: Row[];
  current: Record<string, Plate>;
  references: Record<string, Plate>;
  trials: Trial[];
  zoomRegions: ZoomRegion[];
  statusCounts: Record<string, number>;
  trialCounts: Record<string, number>;
  counts: Record<string, number>;
};

export const THEME_LABEL: Record<string, string> = {
  day: "Day",
  white: "White",
  blue: "Blue",
  dark: "Dark",
  night: "Night",
};

export const STATUS_COLOR: Record<string, string> = {
  candidate: "#837F74",
  unknown: "#4a4843",
  rejected: "#e37f65",
  kept: "#98cf8b",
  shipped: "#8fb8de",
  current: "#d7b986",
};

export const OUTCOME_COLOR: Record<string, string> = {
  promoted: "#98cf8b",
  held: "#d7b986",
  tie: "#837F74",
  split: "#b89adf",
  lost: "#e37f65",
  stopped: "#c56a54",
  rejected: "#e37f65",
};
