#!/usr/bin/env python3
"""Regression tests for canonical arm identity.

The failure these exist to prevent: the Phase 1B arm `compiler+jev` runs our
local NanoJev 0.6B, but publication code re-derived its label locally and the
deployed chart rendered a lane labelled bare `jev`. The evidence was right; the
presentation layer disagreed with itself.

Run either as pytest or directly:

    .venv/bin/python -m pytest tests/test_arm_identity.py -q
    python3 tests/test_arm_identity.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import arm_identity as A  # noqa: E402

#: The cases the correction was specified against.
REQUIRED = [
    "compiler+jev",
    "compiler+jev+qwen3.5_4b",
    "compiler+hammer3b+jev+nemotron+qwen3.5_9b",
    "compiler+hammer2.1_3b",
    "unfiltered+hammer2.1_3b",
]

#: Labels asserted verbatim, so a future "harmless" refactor cannot silently
#: reword the published identity.
EXPECTED_LONG = {
    "compiler+jev": "nanojev 0.6b · compiler-first",
    "compiler+jev+qwen3.5_4b": "nanojev 0.6b + qwen3.5 4b · compiler-first",
    "compiler+hammer3b+jev+nemotron+qwen3.5_9b":
        "hammer3b + nanojev 0.6b + nemotron + qwen3.5 9b · compiler-first",
    "compiler+hammer2.1_3b": "hammer2.1 3b · compiler-first",
    "unfiltered+hammer2.1_3b": "hammer2.1 3b · unfiltered",
}

EXPECTED_SHORT = {
    "compiler+jev": "nanojev 0.6b",
    "compiler+jev+qwen3.5_4b": "nanojev+qwen4b",
    "compiler+hammer2.1_3b": "hammer2.1 3b",
    "unfiltered+hammer2.1_3b": "hammer2.1 3b",
}

EXPECTED_BACKEND = {
    "compiler+jev": "nanojev_06b",
    "compiler+jev+qwen3.5_4b": "nanojev_06b",
    "compiler+hammer3b+jev+nemotron+qwen3.5_9b": "nanojev_06b",
    "compiler+hammer2.1_3b": "hammer2.1_3b",
}


def test_required_arms_render_the_expected_long_label():
    for arm in REQUIRED:
        assert A.long(arm) == EXPECTED_LONG[arm], f"{arm} long label drifted"


def test_required_arms_render_the_expected_short_label():
    for arm, want in EXPECTED_SHORT.items():
        assert A.short(arm) == want, f"{arm} short label drifted"


def test_jev_arm_names_nanojev_and_never_bare_jev():
    """The specific regression. `compiler+jev` must name the backend that ran."""
    for arm in ("compiler+jev", "compiler+jev+qwen3.5_4b",
                "compiler+hammer3b+jev+nemotron+qwen3.5_9b"):
        ident = A.resolve(arm)
        assert "nanojev" in ident.long.lower(), f"{arm} does not name nanojev"
        assert "nanojev" in ident.short.lower(), f"{arm} short does not name nanojev"
        assert ident.backend == "nanojev_06b", f"{arm} backend is {ident.backend}"
        # No rendered label may use `jev` as a model identity.
        assert not A.identity_violations(ident.long), f"{arm} long renders bare jev"
        assert not A.identity_violations(ident.short), f"{arm} short renders bare jev"


def test_every_known_arm_has_a_safe_label():
    """Enumerate the whole population, not just the named cases."""
    arms = A.all_known_arms()
    assert len(arms) >= 13, f"only found {len(arms)} arms; the enumeration broke"
    for arm in arms:
        ident = A.resolve(arm)
        assert ident.long.strip(), f"{arm} has an empty long label"
        assert ident.short.strip(), f"{arm} has an empty short label"
        assert not A.identity_violations(ident.long), f"{arm} long renders bare jev"
        assert not A.identity_violations(ident.short), f"{arm} short renders bare jev"
        assert ident.backend, f"{arm} has no backend identity"


def test_jev_is_not_banned_globally():
    """Southbridge / TypeSafe Jev is a real, different thing.

    `nanojev` and `openjev` are different tokens and must pass; only a bare
    standalone `jev` used as an identity is a violation. A global ban on the
    substring would be the wrong fix and would break the reference links.
    """
    assert A.identity_violations("nanojev 0.6b") == []
    assert A.identity_violations("openjev / z0intelligence") == []
    assert A.identity_violations("jev") == ["jev"]
    assert A.identity_violations("southbridge — jev: watching the agents") == ["jev"]

    # The external reference itself is still present in the source post.
    post = (REPO / "posts" / "slm-router-v0.md").read_text(encoding="utf-8")
    assert "github.com/southbridgeai/jev" in post


def test_frozen_arm_ids_were_not_renamed():
    """Presentation was corrected downstream; the join keys are untouched."""
    corpus = Path("/home/kvn/tmp/openjev/results/phase1b/p1b-20260921T1430Z/observations.jsonl")
    if corpus.is_file():
        arms = set()
        with corpus.open(encoding="utf-8") as fh:
            for line in fh:
                arms.add(json.loads(line).get("arm"))
        assert "compiler+jev" in arms
        assert "compiler+jev+qwen3.5_4b" in arms
    # And the generated identity file keys on the raw id.
    data = A.load_identity()
    assert "compiler+jev" in data["arms"]
    assert data["arms"]["compiler+jev"]["raw_id"] == "compiler+jev"


def test_generated_identity_file_is_in_sync_with_the_resolver():
    """The data file both languages read must match the resolver that wrote it."""
    data = A.load_identity()
    for arm, entry in data["arms"].items():
        ident = A.resolve(arm)
        assert entry["long"] == ident.long, f"{arm} in the file disagrees with the resolver"
        assert entry["short"] == ident.short


def test_web_copy_is_byte_identical_to_the_canonical_file():
    a = (REPO / "studies" / "slm-router-v0" / "data" / "arm-identity.json").read_bytes()
    b = (REPO / "web" / "data" / "arm-identity.json").read_bytes()
    assert a == b, "the app copy and the canonical file have drifted"


def test_rendered_site_labels_come_from_the_resolver():
    """The label actually emitted into the built data, not just the resolver."""
    study = json.loads((REPO / "web" / "data" / "study.json").read_text(encoding="utf-8"))
    seen = []

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "arm" and isinstance(v, str):
                    seen.append(v)
                if k == "label" and isinstance(v, str):
                    assert not A.identity_violations(v), f"built label renders bare jev: {v!r}"
                walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)

    walk(study)
    assert "compiler+jev" in seen, "the jev arm vanished from the built data"
    assert "compiler+jev+qwen3.5_4b" in seen


def _main() -> int:
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL  {name}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())
