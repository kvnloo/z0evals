#!/usr/bin/env python3
"""Bounded, read-only replay of sanitized memory-MCP query outcome audit rows.

This counts retrieval outcomes; it cannot establish model-input injection,
answer utility, independent verification, or causal RSI improvement.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
import re
import stat
import sys

INPUT_SCHEMA = "z0int.memory_query_outcome.v1"
OUTPUT_SCHEMA = "z0eval.memory_query_replay.v1"
TOOLS = ("search", "fetch", "invalid")
OUTCOMES = (
    "hit", "miss", "denied", "unavailable", "stale",
    "rate_limited", "invalid", "error",
)
FIELDS = frozenset({
    "schema", "tool", "outcome", "timestamp", "query_hmac",
    "count", "bytes", "denied_count", "unavailable_count", "decision",
})
MAX_INPUT_BYTES = 8 * 1024 * 1024
MAX_LINE_BYTES = 4096
MAX_REPORTED_BYTES = 64 * 1024 * 1024
MAX_REPORTED_COUNT = 1_000_000
UTC_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
SHA256_HEX = re.compile(r"[0-9a-f]{64}\Z")


class ReplayError(ValueError):
    """Audit is unsafe, incomplete, or not the recognized producer contract."""


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise ReplayError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(_value: str) -> None:
    raise ReplayError("non-finite JSON number")


def _validate_row(row: object, line_number: int) -> dict:
    prefix = f"line {line_number}"
    if type(row) is not dict or set(row) != FIELDS:
        # Reject every extra field (including raw text, locators and secrets).
        raise ReplayError(f"{prefix}: missing or unrecognized fields")
    if row["schema"] != INPUT_SCHEMA:
        raise ReplayError(f"{prefix}: unknown schema")
    tool = row["tool"]
    outcome = row["outcome"]
    decision = row["decision"]
    if type(tool) is not str or tool not in TOOLS:
        raise ReplayError(f"{prefix}: invalid tool")
    if type(outcome) is not str or outcome not in OUTCOMES:
        raise ReplayError(f"{prefix}: invalid outcome")
    if type(decision) is not str:
        raise ReplayError(f"{prefix}: invalid decision")
    timestamp = row["timestamp"]
    if type(timestamp) is not str or UTC_TIMESTAMP.fullmatch(timestamp) is None:
        raise ReplayError(f"{prefix}: invalid UTC timestamp")
    try:
        datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ReplayError(f"{prefix}: impossible UTC timestamp") from exc
    query_hmac = row["query_hmac"]
    if type(query_hmac) is not str or SHA256_HEX.fullmatch(query_hmac) is None:
        raise ReplayError(f"{prefix}: invalid per-process query HMAC")
    for field in ("count", "bytes", "denied_count", "unavailable_count"):
        value = row[field]
        cap = MAX_REPORTED_BYTES if field == "bytes" else MAX_REPORTED_COUNT
        if type(value) is not int or not 0 <= value <= cap:
            raise ReplayError(f"{prefix}: invalid numeric audit field")
    count = row["count"]
    denied = row["denied_count"]
    unavailable = row["unavailable_count"]
    if row["bytes"] == 0:
        raise ReplayError(f"{prefix}: empty encoded response is impossible")
    if ((tool == "fetch" and count > 1) or
            (tool == "search" and count > 10) or
            (tool == "invalid" and count != 0)):
        raise ReplayError(f"{prefix}: impossible result count")
    if tool != "search" and (denied != 0 or unavailable != 0):
        raise ReplayError(f"{prefix}: non-search backend counters")
    if outcome == "hit":
        valid = tool != "invalid" and count > 0 and decision == "allowed"
    elif outcome == "miss":
        valid = (tool != "invalid" and count == 0 and decision == "allowed"
                 and denied == 0 and unavailable == 0)
    elif outcome == "denied":
        valid = (count == 0 and unavailable == 0 and
                 (decision == "denied" or
                  (tool == "search" and decision == "allowed")))
    elif outcome == "unavailable":
        valid = (tool != "invalid" and count == 0 and denied == 0 and
                 (decision == "unavailable" or
                  (tool == "search" and decision == "allowed"
                   and unavailable > 0)))
    elif outcome == "stale":
        valid = (tool == "fetch" and count == 0 and decision == "stale")
    elif outcome == "rate_limited":
        valid = count == 0 and decision == "rate_limited"
    elif outcome == "invalid":
        valid = (count == 0 and (
            (tool == "invalid" and decision == "invalid_arguments") or
            (tool == "search" and decision in
             ("invalid_arguments", "byte_limit")) or
            (tool == "fetch" and decision in
             ("invalid_id", "invalid_arguments", "byte_limit"))))
    else:  # error
        valid = count == 0 and decision == "error"
    if outcome != "hit" and (denied != 0 or unavailable != 0):
        if outcome == "denied":
            valid = valid and denied >= 0 and unavailable == 0
        elif outcome == "unavailable":
            valid = valid and unavailable >= 0 and denied == 0
        else:
            valid = False
    if not valid:
        raise ReplayError(f"{prefix}: impossible outcome/decision/counter combination")
    return row


def _read_snapshot(path: str) -> bytes:
    """Read an unchanged, regular, local file at a strict byte bound."""
    if not hasattr(os, "O_NOFOLLOW"):
        raise ReplayError("secure no-follow input open is unsupported")
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NONBLOCK", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise ReplayError("cannot open a regular local input") from exc
    try:
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise ReplayError("input is not a regular file")
            if before.st_size > MAX_INPUT_BYTES:
                raise ReplayError("input exceeds byte limit")
            contents = stream.read(MAX_INPUT_BYTES + 1)
            after = os.fstat(stream.fileno())
    except OSError as exc:
        raise ReplayError("cannot read input") from exc
    if len(contents) > MAX_INPUT_BYTES:
        raise ReplayError("input exceeds byte limit")
    if (len(contents) != before.st_size or
            before.st_size != after.st_size or
            before.st_mtime_ns != after.st_mtime_ns or
            before.st_ctime_ns != after.st_ctime_ns):
        raise ReplayError("input changed during read")
    if not contents or not contents.endswith(b"\n"):
        raise ReplayError("empty or unterminated audit file")
    return contents


def replay(path: str) -> dict:
    """Validate the complete snapshot before emitting any aggregate."""
    contents = _read_snapshot(path)
    by_tool = {tool: 0 for tool in TOOLS}
    by_outcome = {outcome: 0 for outcome in OUTCOMES}
    by_tool_outcome = {
        tool: {outcome: 0 for outcome in OUTCOMES} for tool in TOOLS
    }
    rows = contents.split(b"\n")[:-1]
    for line_number, raw in enumerate(rows, 1):
        if not raw or len(raw) > MAX_LINE_BYTES:
            raise ReplayError(f"line {line_number}: blank or overlarge JSONL row")
        try:
            record = json.loads(
                raw.decode("utf-8"),
                object_pairs_hook=_unique_object,
                parse_constant=_reject_constant,
            )
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ReplayError(f"line {line_number}: malformed UTF-8 JSON") from exc
        row = _validate_row(record, line_number)
        tool, outcome = row["tool"], row["outcome"]
        by_tool[tool] += 1
        by_outcome[outcome] += 1
        by_tool_outcome[tool][outcome] += 1
    return {
        "schema": OUTPUT_SCHEMA,
        "input_schema": INPUT_SCHEMA,
        "records": len(rows),
        "by_tool": by_tool,
        "by_outcome": by_outcome,
        "by_tool_outcome": by_tool_outcome,
        "interpretation": "Retrieval outcomes only; NOT answer utility or causal RSI gain.",
        "limitations": [
            "No model-input, answer-use, source-verification or action-outcome proof.",
            "query_hmac uses a per-process random key; it cannot correlate across launches.",
            "Only locally supplied sanitized audit rows are read; no live source or upload.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Offline counts from bounded, sanitized memory query audit JSONL"
    )
    parser.add_argument("--input", required=True, metavar="LOCAL_AUDIT_JSONL")
    args = parser.parse_args(argv)
    try:
        report = replay(args.input)
    except (ReplayError, OSError) as exc:
        # Never echo private row contents, HMAC values, or the input path.
        message = str(exc) if isinstance(exc, ReplayError) else "I/O error"
        print(f"replay rejected: {message}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
