"""Behavioral tests for bounded, privacy-safe memory query outcome replay.

All rows are synthetic. No private audit, live retrieval, or answer evaluation.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

STUDY = Path(__file__).resolve().parent
SCRIPT = STUDY / "memory_query_replay.py"
spec = importlib.util.spec_from_file_location("memory_query_replay", SCRIPT)
assert spec is not None and spec.loader is not None
replay_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay_module)


def audit(**updates: object) -> dict:
    row = {
        "schema": "z0int.memory_query_outcome.v1",
        "tool": "search",
        "outcome": "hit",
        "timestamp": "2026-10-23T03:04:05Z",
        "query_hmac": "a" * 64,
        "count": 1,
        "bytes": 125,
        "denied_count": 0,
        "unavailable_count": 0,
        "decision": "allowed",
    }
    row.update(updates)
    return row


def encoded(row: dict) -> bytes:
    return json.dumps(row, sort_keys=True, separators=(",", ":")).encode("utf-8")


class MemoryQueryReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "sanitized-audit.jsonl"

    def write_rows(self, *rows: dict) -> None:
        self.path.write_bytes(b"".join(encoded(row) + b"\n" for row in rows))

    def run_cli(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--input", str(self.path)],
            capture_output=True, text=True, check=False,
        )

    def assert_rejected(self, raw: bytes) -> None:
        self.path.write_bytes(raw)
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("replay rejected:", result.stderr)
        self.assertNotIn(str(self.path), result.stderr)
        self.assertNotIn("a" * 64, result.stderr)

    def test_cli_aggregates_hits_and_misses_without_identifiers(self) -> None:
        self.write_rows(
            audit(),
            audit(outcome="miss", count=0, query_hmac="b" * 64),
            audit(tool="fetch", query_hmac="c" * 64),
        )
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        summary = json.loads(result.stdout)
        self.assertEqual(summary["schema"], "z0eval.memory_query_replay.v1")
        self.assertEqual(summary["input_schema"], "z0int.memory_query_outcome.v1")
        self.assertEqual(summary["records"], 3)
        self.assertEqual(summary["by_tool"], {"search": 2, "fetch": 1, "invalid": 0})
        self.assertEqual(summary["by_outcome"]["hit"], 2)
        self.assertEqual(summary["by_outcome"]["miss"], 1)
        self.assertEqual(summary["by_tool_outcome"]["search"]["miss"], 1)
        self.assertEqual(summary["by_tool_outcome"]["fetch"]["hit"], 1)
        self.assertEqual(summary["by_tool_outcome"]["invalid"]["hit"], 0)
        self.assertIn("NOT answer utility or causal RSI gain", summary["interpretation"])
        self.assertTrue(any("across launches" in value for value in summary["limitations"]))
        for identifier in ("a" * 64, "b" * 64, "c" * 64, str(self.path)):
            self.assertNotIn(identifier, result.stdout)

    def test_cli_distinguishes_denied_unavailable_stale_limited_invalid_error(self) -> None:
        self.write_rows(
            audit(outcome="denied", count=0, denied_count=2),
            audit(outcome="unavailable", count=0, unavailable_count=1),
            audit(tool="fetch", outcome="stale", count=0, decision="stale"),
            audit(outcome="rate_limited", count=0, decision="rate_limited"),
            audit(tool="invalid", outcome="invalid", count=0, decision="invalid_arguments"),
            audit(tool="fetch", outcome="unavailable", count=0, decision="unavailable"),
            audit(tool="fetch", outcome="denied", count=0, decision="denied"),
            audit(outcome="error", count=0, decision="error"),
            audit(outcome="hit", count=2, unavailable_count=1, denied_count=1),
        )
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["records"], 9)
        for category, expected in {
            "hit": 1, "miss": 0, "denied": 2, "unavailable": 2,
            "stale": 1, "rate_limited": 1, "invalid": 1, "error": 1,
        }.items():
            self.assertEqual(summary["by_outcome"][category], expected, category)
        self.assertEqual(summary["by_tool_outcome"]["fetch"]["stale"], 1)
        self.assertEqual(summary["by_tool_outcome"]["invalid"]["invalid"], 1)

    def test_cli_accepts_fixed_producer_error_decisions(self) -> None:
        self.write_rows(*(
            audit(tool="fetch", outcome="error", count=0, decision=decision)
            for decision in ("byte_limit", "error")
        ))
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        summary = json.loads(result.stdout)
        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["by_outcome"]["error"], 2)
        self.assertEqual(summary["by_tool_outcome"]["fetch"]["error"], 2)
        self.assertEqual(summary["by_outcome"]["miss"], 0)
        self.assertEqual(summary["by_outcome"]["invalid"], 0)

    def test_per_process_hmac_is_not_used_for_deduplication(self) -> None:
        self.write_rows(audit(), audit())
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["by_outcome"]["hit"], 2)
        self.assertNotIn("unique_queries", summary)

    def test_fail_closed_malformed_duplicate_and_unterminated_jsonl(self) -> None:
        valid = encoded(audit()) + b"\n"
        duplicate = encoded(audit()).replace(
            b'"tool":"search"', b'"tool":"search","tool":"fetch"'
        )
        for malformed in (
            b'{"schema":\n',
            b'["not a record"]\n',
            duplicate + b"\n",
            b"\xff\n",
            encoded(audit()),  # producer writes complete newline-terminated rows
            valid + b"\n",
            valid + b'{"schema":\n',
        ):
            with self.subTest(raw=repr(malformed[:32])):
                self.assert_rejected(malformed)

    def test_rejects_unknown_schema_raw_fields_and_missing_required_fields(self) -> None:
        variants = [
            audit(schema="z0int.memory_query_outcome.v2"),
            audit(schema=None),
            audit(tool="unsafe"),
            audit(outcome="read"),
            audit(query_hmac="not-a-hmac"),
            audit(timestamp="2026-02-29T03:04:05Z"),
            audit(timestamp="2026-10-23T03:04:05+00:00"),
        ]
        for name in ("query", "raw_query", "content", "secret", "token",
                     "locator", "source_path", "prompt", "access_key"):
            variants.append({**audit(), name: "PRIVATE_SYNTHETIC"})
        for name in ("timestamp", "query_hmac", "decision", "schema", "outcome",
                     "tool", "count", "bytes", "denied_count", "unavailable_count"):
            row = audit()
            del row[name]
            variants.append(row)
        for variant in variants:
            with self.subTest(variant=sorted(variant)):
                self.assert_rejected(encoded(variant) + b"\n")

    def test_rejects_typed_and_impossible_outcome_combinations(self) -> None:
        invalid = [
            audit(count=True), audit(bytes=False), audit(denied_count="1"),
            audit(unavailable_count=None), audit(bytes=0), audit(count=-1),
            audit(count=11), audit(bytes=replay_module.MAX_REPORTED_BYTES + 1),
            audit(outcome="hit", count=0),
            audit(outcome="miss", count=1),
            audit(outcome="miss", count=0, unavailable_count=1),
            audit(outcome="miss", count=0, denied_count=1),
            audit(outcome="denied", count=1, decision="denied"),
            audit(outcome="stale", tool="search", count=0, decision="stale"),
            audit(outcome="rate_limited", count=1, decision="rate_limited"),
            audit(outcome="invalid", count=0, decision="allowed"),
            audit(outcome="error", count=0, decision="stale"),
            audit(outcome="error", count=0, decision="unrecognized_error"),
            audit(tool="fetch", count=2),
            audit(tool="fetch", denied_count=1),
            audit(tool="invalid", count=0, outcome="hit"),
            audit(tool="invalid", count=0, outcome="miss"),
            audit(tool="invalid", count=0, outcome="unavailable", decision="unavailable"),
            audit(tool="invalid", count=0, unavailable_count=1, outcome="invalid",
                  decision="invalid_arguments"),
            audit(outcome="unavailable", count=0, denied_count=1, decision="unavailable"),
        ]
        for row in invalid:
            with self.subTest(tool=row["tool"], outcome=row["outcome"], count=row["count"]):
                self.assert_rejected(encoded(row) + b"\n")

    def test_rejects_overlarge_line_and_file(self) -> None:
        self.assert_rejected(b"x" * (replay_module.MAX_LINE_BYTES + 1) + b"\n")
        with self.path.open("wb") as stream:
            stream.truncate(replay_module.MAX_INPUT_BYTES + 1)
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("byte limit", result.stderr)

    def test_rejects_symlink_and_nonregular_file(self) -> None:
        if not hasattr(os, "O_NOFOLLOW"):
            self.skipTest("secure local open unavailable")
        target = Path(self.temp.name) / "regular.jsonl"
        target.write_bytes(encoded(audit()) + b"\n")
        self.path.symlink_to(target)
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertNotIn(str(target), result.stderr)
        self.path.unlink()
        self.path.mkdir()
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")

    def test_no_partial_output_on_late_failure(self) -> None:
        self.assert_rejected(encoded(audit()) + b"\n" +
                             encoded(audit(outcome="miss", count=3)) + b"\n")

    def test_unreadable_or_missing_file_is_never_reported_as_zero(self) -> None:
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertNotIn(str(self.path), result.stderr)


if __name__ == "__main__":
    unittest.main()
