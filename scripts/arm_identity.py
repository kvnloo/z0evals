#!/usr/bin/env python3
"""Canonical arm identity — the ONE place that maps a raw arm id to a label.

Why this exists
---------------
The Phase 1B arm `compiler+jev` runs our local **NanoJev 0.6B**, not the hosted
TypeSafe Jev teacher. The raw arm id says `jev`; the immutable corpus says
`model_id=nanojev_06b`. For a period, publication code re-derived the display
label locally — one place with a regex, another with a dict, a third with a
`.replace(/\bjev\b/g, ...)` — and the deployed chart rendered a lane labelled
bare `jev`. The evidence was correct the whole time; only the presentation
layer disagreed with itself.

So: components may no longer derive a label. They call this.

    raw arm id -> semantic components -> short label -> long label

    compiler+jev
      components  prefix=compiler  models=[jev]
      backend     nanojev_06b
      short       nanojev 0.6b
      long        nanojev 0.6b · compiler-first

Frozen arm ids are NEVER renamed. Only the presentation of them is centralised.
Southbridge/TypeSafe Jev is a real, different thing and the word `jev` stays
legitimate in reference links; what this module forbids is `jev` being used as a
*model identity* in a rendered label.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path

SCHEMA = "z0evals.arm_identity.v1"

REPO = Path(__file__).resolve().parents[1]
IDENTITY_PATH = REPO / "studies" / "slm-router-v0" / "data" / "arm-identity.json"

#: Component tokens whose display form differs from their raw form. A component
#: that is not listed here renders as itself.
#:
#: `jev` is the load-bearing entry: as a standalone arm it is the NanoJev 0.6B
#: checkpoint; inside a composite id the model is already established, so the
#: shorter form is used to keep the 132px figure column within its old length.
COMPONENT_DISPLAY: dict[str, dict[str, str]] = {
    "jev": {
        "backend": "nanojev_06b",
        "solo": "nanojev 0.6b",
        "composite": "nanojev",
        "long": "nanojev 0.6b",
    },
}

#: Deliberate long-form overrides. These exist so the exact published labels are
#: asserted by test rather than emerging from string surgery.
LONG_OVERRIDES: dict[str, str] = {
    "compiler+jev": "nanojev 0.6b · compiler-first",
    "compiler+jev+qwen3.5_4b": "nanojev 0.6b + qwen3.5 4b · compiler-first",
    "compiler+jev+nemotron_orchestrator_8b":
        "nanojev 0.6b + nemotron orchestrator 8b · compiler-first",
    "compiler+jev+nemotron+qwen3.5_9b":
        "nanojev 0.6b + nemotron + qwen3.5 9b · compiler-first",
    "compiler+hammer3b+jev+nemotron+qwen3.5_9b":
        "hammer3b + nanojev 0.6b + nemotron + qwen3.5 9b · compiler-first",
}

#: Short-form overrides, sized for the fixed 132px figure name column.
SHORT_OVERRIDES: dict[str, str] = {
    "compiler+jev": "nanojev 0.6b",
    "compiler+jev+qwen3.5_4b": "nanojev+qwen4b",
}

#: Arms that exist in the generator but are not in the frozen corpus. Kept here
#: so the resolver is total over everything we know how to name.
EXTRA_ARMS: tuple[str, ...] = (
    "compiler+jev+nemotron_orchestrator_8b",
    "compiler+jev+nemotron+qwen3.5_9b",
    "compiler+hammer3b+jev+nemotron+qwen3.5_9b",
)

PREFIX_DISPLAY = {
    "compiler": "compiler-first",
    "unfiltered": "unfiltered",
    "deterministic.compiler_only": "deterministic only",
    "coldprobe": "cold probe",
}

#: Tokens that must never appear as a bare model identity in a rendered label.
#: Token-aware on purpose: `nanojev` and `openjev` contain the substring `jev`
#: and are fine.
FORBIDDEN_IDENTITY_TOKENS = ("jev",)


@dataclass(frozen=True)
class ArmIdentity:
    raw_id: str
    prefix: str
    models: tuple[str, ...]
    backend: str
    short: str
    long: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["models"] = list(self.models)
        return d


def _model_display(tokens: list[str], *, solo: bool) -> str:
    out: list[str] = []
    for t in tokens:
        spec = COMPONENT_DISPLAY.get(t)
        if spec is None:
            out.append(t.replace("_", " "))
        elif solo and len(tokens) == 1:
            out.append(spec["solo"])
        else:
            out.append(spec["composite"])
    return "+".join(out)


def _backend(tokens: list[str]) -> str:
    """The semantic backend. Named by the model component, not the prefix."""
    for t in tokens:
        spec = COMPONENT_DISPLAY.get(t)
        if spec and spec.get("backend"):
            return spec["backend"]
    # A plain model arm's backend is the model token itself.
    return tokens[-1] if tokens else ""


def resolve(arm_id: str) -> ArmIdentity:
    """Total over any arm id. Never returns a bare forbidden token as identity."""
    if arm_id == "deterministic.compiler_only":
        return ArmIdentity(
            raw_id=arm_id, prefix="deterministic", models=(),
            backend="deterministic", short="deterministic compiler only",
            long="deterministic compiler only",
        )

    prefix, _, rest = arm_id.partition("+")
    tokens = [t for t in rest.split("+") if t] or []
    pretty_prefix = PREFIX_DISPLAY.get(prefix, prefix)

    solo = len(tokens) == 1
    model_short = _model_display(tokens, solo=solo) if tokens else ""
    model_long = " + ".join(
        COMPONENT_DISPLAY.get(t, {}).get("long", t.replace("_", " "))
        for t in tokens
    ) if tokens else ""

    short = SHORT_OVERRIDES.get(arm_id) or model_short or pretty_prefix
    long = LONG_OVERRIDES.get(arm_id) or (f"{model_long} · {pretty_prefix}" if model_long else pretty_prefix)

    return ArmIdentity(
        raw_id=arm_id, prefix=prefix, models=tuple(tokens),
        backend=_backend(tokens), short=short, long=long,
    )


def short(arm_id: str) -> str:
    return resolve(arm_id).short


def long(arm_id: str) -> str:
    return resolve(arm_id).long


def backend(arm_id: str) -> str:
    return resolve(arm_id).backend


def _tokens(text: str) -> list[str]:
    """Token-aware split. `nanojev`, `openjev`, `jev-like` are single tokens."""
    return [t for t in re.split(r"[^A-Za-z0-9]+", text.lower()) if t]


def identity_violations(text: str) -> list[str]:
    """Forbidden *model identity* tokens in a rendered string.

    Deliberately not a substring grep. `jev` inside `nanojev`/`openjev` is a
    different token and passes; a standalone token `jev` fails.
    """
    return [t for t in _tokens(text) if t in FORBIDDEN_IDENTITY_TOKENS]


def all_known_arms() -> list[str]:
    """Every arm id this repo can name: corpus arms plus generator-only arms."""
    arms: set[str] = set(EXTRA_ARMS)
    for p in (
        REPO / "web" / "data" / "study.json",
        REPO / "studies" / "slm-router-v0" / "data" / "phase1b-summary.json",
    ):
        if not p.is_file():
            continue
        blob = p.read_text(encoding="utf-8")

        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in ("arm", "armId") and isinstance(v, str):
                        arms.add(v)
                    walk(v)
            elif isinstance(o, list):
                for x in o:
                    walk(x)

        try:
            walk(json.loads(blob))
        except ValueError:
            pass
    # `phase1b-summary.json` uses a spaced display form as its join key.
    arms = {a for a in arms if " " not in a}
    return sorted(arms)


def write_identity_file(path: Path | None = None) -> Path:
    """Emit the single data source consumed by both Python and TypeScript."""
    target = path or IDENTITY_PATH
    arms = {a: resolve(a).to_dict() for a in all_known_arms()}
    payload = {
        "schema": SCHEMA,
        "note": (
            "Canonical arm identity. Components must not derive labels; they read "
            "this. Raw/frozen arm ids are never renamed — only their presentation "
            "is centralised. `compiler+jev` is the local NanoJev 0.6B, not the "
            "hosted TypeSafe Jev teacher."
        ),
        "componentDisplay": COMPONENT_DISPLAY,
        "forbiddenIdentityTokens": list(FORBIDDEN_IDENTITY_TOKENS),
        "arms": arms,
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(payload, indent=1, sort_keys=True) + "\n"
    target.write_text(blob, encoding="utf-8")
    # The app imports a copy from inside its own root; Next will not reach
    # outside the app directory. Byte-identical, written in the same pass so the
    # two can never drift.
    web_copy = REPO / "web" / "data" / "arm-identity.json"
    web_copy.parent.mkdir(parents=True, exist_ok=True)
    web_copy.write_text(blob, encoding="utf-8")
    return target


def load_identity(path: Path | None = None) -> dict:
    return json.loads((path or IDENTITY_PATH).read_text(encoding="utf-8"))


if __name__ == "__main__":
    import sys

    if "--write" in sys.argv:
        p = write_identity_file()
        n = len(load_identity(p)["arms"])
        print(f"wrote {p} ({n} arms)")
    else:
        for a in all_known_arms():
            i = resolve(a)
            print(f"{a:48s} backend={i.backend:14s} short={i.short:22s} long={i.long}")
