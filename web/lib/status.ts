// Status vocabulary. Every status renders as a dot plus a text label, never a pill and
// never colour alone (the Dash rule). Tone names map to the .dot classes in globals.css.
export type Tone = "ok" | "info" | "warn" | "danger" | "prov" | "faint";

// post / study evidence statuses
export const POST_STATUS: Record<string, [Tone, string]> = {
  living: ["ok", "living"],
  "evidence-local": ["ok", "measured locally"],
  "evidence-mixed": ["warn", "mixed evidence"],
  "evidence-pending": ["info", "evidence pending"],
  // kept from the optchat publication: context bytes only, no answer-quality score
  unscored: ["info", "unscored"],
  "research-synthesis": ["prov", "synthesis"],
  architecture: ["faint", "architecture"],
  draft: ["faint", "draft"],
};

// research-log statuses. Live = blue, needs you = amber, failing = red, done = green.
export const STATUS: Record<string, [Tone, string]> = {
  published: ["ok", "published"],
  frozen: ["ok", "frozen, not yet posted"],
  "frozen-internal": ["ok", "measured, internal evidence"],
  "draft-pr": ["info", "draft study PR"],
  "in-progress": ["info", "in progress"],
  proposal: ["prov", "proposal"],
  idea: ["prov", "idea / paper"],
  abandoned: ["faint", "stopped"],
};

export function postStatus(raw: string): [Tone, string] {
  return POST_STATUS[raw] ?? STATUS[raw] ?? ["faint", raw.replace(/-/g, " ")];
}

export function logStatus(raw: string): [Tone, string] {
  return STATUS[raw] ?? ["faint", raw];
}

// "measured only" filter: statuses whose tone is ok
export function isMeasured(raw: string): boolean {
  return postStatus(raw)[0] === "ok";
}
