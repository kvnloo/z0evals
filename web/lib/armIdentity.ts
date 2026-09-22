/**
 * Canonical arm identity — the ONE place a raw arm id becomes a label.
 *
 * Mirrors `scripts/arm_identity.py`, and reads the same generated data file, so
 * Python and TypeScript cannot disagree about what `compiler+jev` is.
 *
 * Background: that arm runs our local **NanoJev 0.6B**, not the hosted TypeSafe
 * Jev teacher. The raw id says `jev`; the frozen corpus says `model_id=nanojev_06b`.
 * Publication code used to re-derive the label locally — a regex here, a dict
 * there — and the deployed chart ended up rendering a lane labelled bare `jev`.
 *
 * Components must not derive labels. They call `shortLabel` / `longLabel` /
 * `backendOf`, and they carry `dataArm()` on the element so the DOM keeps the
 * machine-readable identity even when the visible text is abbreviated.
 *
 * Raw arm ids are never renamed. Only their presentation is centralised.
 */
import raw from "@/data/arm-identity.json";

export type ArmIdentity = {
  raw_id: string;
  prefix: string;
  models: string[];
  backend: string;
  short: string;
  long: string;
};

const DATA = raw as unknown as {
  schema: string;
  componentDisplay: Record<string, { backend?: string; solo?: string; composite?: string; long?: string }>;
  forbiddenIdentityTokens: string[];
  arms: Record<string, ArmIdentity>;
};

const COMPONENT_DISPLAY = DATA.componentDisplay ?? {};
const FORBIDDEN = DATA.forbiddenIdentityTokens ?? ["jev"];
const PREFIX_DISPLAY: Record<string, string> = {
  compiler: "compiler-first",
  unfiltered: "unfiltered",
  "deterministic.compiler_only": "deterministic only",
  coldprobe: "cold probe",
};

/** Derive an identity for an arm the generated file does not know about.
 *  Mirrors the Python derivation, including the forbidden-token substitution, so
 *  an unseen arm can never render a bare `jev` as its model identity. */
function derive(armId: string): ArmIdentity {
  if (armId === "deterministic.compiler_only") {
    return {
      raw_id: armId, prefix: "deterministic", models: [], backend: "deterministic",
      short: "deterministic compiler only", long: "deterministic compiler only",
    };
  }
  const [prefix, ...rest] = armId.split("+");
  const models = rest.filter(Boolean);
  const pretty = PREFIX_DISPLAY[prefix] ?? prefix;
  const solo = models.length === 1;
  const disp = models.map((m) => {
    const spec = COMPONENT_DISPLAY[m];
    if (!spec) return m.replace(/_/g, " ");
    return solo ? (spec.solo ?? m) : (spec.composite ?? spec.solo ?? m);
  });
  const longDisp = models.map((m) => COMPONENT_DISPLAY[m]?.long ?? m.replace(/_/g, " "));
  const short = disp.join("+") || pretty;
  const long = longDisp.length ? `${longDisp.join(" + ")} · ${pretty}` : pretty;
  const backend = models.map((m) => COMPONENT_DISPLAY[m]?.backend ?? m).slice(-1)[0] ?? "";
  return { raw_id: armId, prefix, models, backend, short, long };
}

export function resolveArm(armId: string): ArmIdentity {
  return DATA.arms?.[armId] ?? derive(armId);
}

/** Concise, sized for the fixed 132px figure name column. */
export function shortLabel(armId: string): string {
  return resolveArm(armId).short;
}

/** The full semantic name. Use in `title`/`aria-label`, never in a tight column. */
export function longLabel(armId: string): string {
  return resolveArm(armId).long;
}

/** The semantic backend, e.g. `nanojev_06b`. This is evidence, not presentation. */
export function backendOf(armId: string): string {
  return resolveArm(armId).backend;
}

/** DOM provenance for any element that renders an arm label. */
export function dataArm(armId: string): { "data-arm-id": string; "data-model-id": string } {
  return { "data-arm-id": armId, "data-model-id": backendOf(armId) };
}

/** Token-aware. `nanojev` and `openjev` are different tokens from `jev` and pass. */
export function identityViolations(text: string): string[] {
  const tokens = text.toLowerCase().split(/[^a-z0-9]+/).filter(Boolean);
  return tokens.filter((t) => FORBIDDEN.includes(t));
}
