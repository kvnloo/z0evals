// status → (Dash semantic dot, plain label). Live = blue, needs you = amber, failing = red, done = green.
export const STATUS: Record<string, [string, string]> = {
  published: ["ok", "published"],
  frozen: ["ok", "frozen, not yet posted"],
  "frozen-internal": ["ok", "measured, internal evidence"],
  "draft-pr": ["info", "draft study PR"],
  "in-progress": ["info", "in progress"],
  proposal: ["prov", "proposal"],
  idea: ["prov", "idea / paper"],
  abandoned: ["faint", "stopped"],
};
