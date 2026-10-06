#!/usr/bin/env python3
"""Validate frozen OptChat artifact integrity, NOT recall quality or promotion."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path

EXPECTED_TURNS_SHA256 = "f2f1b5da19e275b45c3120c9a08401d855359f653f5cce4dcdcec673ccd0d22f"
STUDY = "studies/optchat-long-horizon-v0"


def validate_values(summary: dict, turns: list[dict]) -> None:
    def integer(value: object, label: str, minimum: int = 0) -> int:
        if type(value) is not int or value < minimum:
            raise ValueError(f"{label}: expected integer >= {minimum}")
        return value

    total = integer(summary.get("turns"), "turns", 1)
    if len(turns) != total:
        raise ValueError("trajectory length differs from summary")
    previous_messages = 0
    for index, row in enumerate(turns, 1):
        if integer(row.get("turn"), "turn", 1) != index:
            raise ValueError("turns must be contiguous and ordered")
        raw = integer(row.get("raw_bytes"), "raw_bytes", 1)
        view = integer(row.get("view_bytes"), "view_bytes")
        messages = integer(row.get("messages"), "messages", 1)
        if messages <= previous_messages:
            raise ValueError("message count must advance")
        previous_messages = messages
        integer(row.get("placeholders"), "placeholders")
        recorded_ratio = row.get("ratio")
        if type(recorded_ratio) not in (int, float) or not math.isfinite(recorded_ratio):
            raise ValueError("ratio must be finite")
        if not math.isclose(recorded_ratio, view / raw, abs_tol=0.000051, rel_tol=0):
            raise ValueError("rounded row ratio disagrees with byte counts")
    last = turns[-1]
    for summary_key, row_key in (("final_raw_bytes", "raw_bytes"), ("final_view_bytes", "view_bytes"),
                                 ("placeholders_at_end", "placeholders")):
        if integer(summary.get(summary_key), summary_key) != last[row_key]:
            raise ValueError(f"{summary_key} disagrees with final row")
    final_ratio = summary.get("final_ratio")
    if type(final_ratio) not in (int, float) or not math.isfinite(final_ratio):
        raise ValueError("final_ratio must be finite")
    if not math.isclose(final_ratio, last["view_bytes"] / last["raw_bytes"], abs_tol=0.000051, rel_tol=0):
        raise ValueError("final_ratio disagrees with final row")


def validate_repository(root: Path) -> None:
    study = root / STUDY
    raw = (study / "turns.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_TURNS_SHA256:
        raise ValueError("frozen turns.json checksum mismatch; do not silently re-freeze evidence")
    manifest = (study / "manifest.yaml").read_text()
    if "scoring: unscored" not in manifest or "claims: []" not in manifest:
        raise ValueError("this publication must remain unscored with no certified claims")
    if "OptChat itself is uncommitted on that tree" not in manifest:
        raise ValueError("missing implementation provenance must remain disclosed")
    validate_values(json.loads((study / "summary.json").read_text()), json.loads(raw))


if __name__ == "__main__":
    validate_repository(Path(__file__).resolve().parents[1])
    print("ok: frozen OptChat bytes and summary agree; recall quality remains unscored")
