import type { TocItem } from "@/components/Toc";

// The phase 1b contents. Also the list of old home-page anchors that HashForward
// sends from /#<id> to /slm-router-v0/#<id>.
export const TOC: TocItem[] = [
  { id: "how-much", label: "how much of the llm do we need?", depth: 0 },
  { id: "first-shortcut", label: "the first shortcut", depth: 0 },
  { id: "boring-3b", label: "the boring 3b ruined the ladder", depth: 0 },
  { id: "phase1", label: "phase 1 was kind of trash", depth: 0 },
  { id: "held-up", label: "hammer3b actually held up", depth: 0 },
  { id: "wrong-job", label: "we gave big models the wrong job", depth: 0 },
  { id: "residency", label: "residency wrecked the framing", depth: 0 },
  { id: "composition", label: "composition made it worse", depth: 0 },
  { id: "nanojev", label: "nanojev failed. nanojev isn't useless.", depth: 0 },
  { id: "compiler", label: "the compiler was the intelligence", depth: 0 },
  { id: "gate", label: "the gate failed its own eval", depth: 0 },
  { id: "errors", label: "the errors were not noise", depth: 0 },
  { id: "architecture", label: "what architecture survived", depth: 0 },
  { id: "weirder", label: "make the bottom weirder", depth: 0 },
  { id: "result", label: "the actual result", depth: 0 },
  { id: "author", label: "author's note", depth: 0 },
  { id: "appendix", label: "appendix", depth: 0 },
  { id: "explore", label: "explore the matrix", depth: 1 },
  { id: "gate-caveats", label: "gate defects recorded", depth: 1 },
  { id: "provenance", label: "check or reuse the evidence", depth: 1 },
  { id: "references", label: "references", depth: 1 },
];

export const OLD_HOME_IDS = TOC.map((t) => t.id);
