"""Offline UNIT: real source Agent/adapter plus native loopback HTTP, never a provider."""
import hashlib
import importlib.util
import json
import os
import resource
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SOURCE = Path("/home/kvn/tmp/dsh")


class NativeSourceCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("dsh_native_source_runner", HERE / "runner.py")
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.source_runtime(SOURCE)  # Clean source HEAD and Bun binary/version pins, read-only.

    def run_fixture(self, mode, delay):
        with tempfile.TemporaryDirectory(prefix="dsh-native-source-unit-", dir=os.environ["TMPDIR"]) as tmp:
            env = {**os.environ, "NODE_PATH": "/usr/lib/node_modules/@deepseek-ai/dsh/node_modules",
                   "BUN_RUNTIME_TRANSPILER_CACHE_PATH": "0", "DSH_UNIT_OUT": tmp,
                   "DSH_UNIT_CAPTURE_MODE": mode, "DSH_UNIT_EOF_DELAY": str(delay)}
            env.pop("DSH_STUDY_INPUT", None)
            program = (HERE / "runtime.mjs").read_text() + "\n" + (HERE / "tests/native-source-case.mjs").read_text()
            def limits():
                os.umask(0o077)
                resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            proc = subprocess.run(["/home/kvn/.bun/bin/bun", "-e", program], cwd=SOURCE,
                                  env=env, capture_output=True, text=True, timeout=30, preexec_fn=limits)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            result = json.loads(proc.stdout)
            self.assertEqual(result["provider_network_calls"], 0)
            self.assertEqual(result["fixture_calls"], 1)
            self.assertEqual(Path(tmp).stat().st_mode & 0o777, 0o700)
            for file in Path(tmp).rglob("*"):
                if file.is_file():
                    self.assertEqual(file.stat().st_mode & 0o777, 0o600)
                    self.assertNotIn(b"UNIT-not-a-credential", file.read_bytes())
                    self.assertNotIn(b"UNIT-private-response-header", file.read_bytes())
            captured = (Path(tmp) / "wire-0001-response.body").read_bytes()
            self.assertEqual(result["captured_sha256"], hashlib.sha256(captured).hexdigest())
            return result

    def test_terminal_frame_with_delayed_http_eof(self):
        for delay in (10, 1200):
            with self.subTest(delay_ms=delay):
                self.run_fixture("complete", delay)

    def test_immediate_eof_is_a_complete_http_body(self):
        self.run_fixture("complete", 0)

    def test_fragmented_terminal_frame_and_unobserved_http_tail(self):
        for mode in ("fragmented", "late-tail"):
            with self.subTest(mode=mode):
                self.run_fixture(mode, 1200)

    def test_malformed_fake_and_incomplete_terminals_block(self):
        for mode in ("truncated-frame", "incomplete", "fake-terminal", "malformed-terminal",
                     "invalid-json", "unsettled-block", "orphan-terminal", "sse-error"):
            with self.subTest(mode=mode):
                self.run_fixture(mode, 0)

    def test_agent_cancel_error_max_tokens_and_empty_answer_still_block(self):
        for mode in ("cancel", "cancel-terminal", "agent-error-terminal", "max-tokens", "empty-answer"):
            with self.subTest(mode=mode):
                self.run_fixture(mode, 1200)

    def test_http_failure_still_blocks(self):
        self.run_fixture("http-error", 0)

    def test_successful_agent_cannot_mask_incomplete_or_failed_capture(self):
        for mode in ("clone-truncated", "clone-read-error"):
            with self.subTest(mode=mode):
                self.run_fixture(mode, 1200)


if __name__ == "__main__":
    unittest.main()
