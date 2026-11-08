"""Offline tests for the Pages channel identity verifier."""
from __future__ import annotations

import importlib.util
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "verify_channels", ROOT / "scripts" / "verify_channels.py"
)
assert SPEC and SPEC.loader
verify_channels = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_channels)  # type: ignore[union-attr]


GOOD_PAGE = (
    '<html><link href="/z0evals/dev/_next/a.css">'
    '<div class="modelRow" data-model="compiler-first" data-arm-id="compiler+jev" '
    'data-model-id="nanojev_06b">nanojev 0.6b</div> '
    "nanojev+qwen4b southbridgeai/jev compiler+jev+qwen3.5_4b</html>"
)


class VerifyChannelsTest(unittest.TestCase):
    def test_strip_tags(self):
        with mock.patch.object(verify_channels, "fetch"):
            self.assertEqual(verify_channels.strip_tags("<b>a &amp; b</b>"), "a & b")

    def test_identity_surfaces(self):
        raw = (
            '<span class="modelName">Jev</span>'
            '<text class="corpusLabel" data-arm-id="a">lane<title>Long</title></text>'
            '<b data-arm-id="x"> </b>'
        )
        with mock.patch.object(verify_channels, "fetch"):
            # Corpus lanes intentionally appear in both the data-arm-id and corpusLabel scans.
            self.assertEqual(verify_channels.identity_surfaces(raw), ["lane", "Jev", "lane"])

    def test_check_good_page(self):
        url = "https://kvnloo.github.io/z0evals/dev/"
        css_url = "https://kvnloo.github.io/z0evals/dev/_next/a.css"
        responses = {
            url: GOOD_PAGE,
            css_url: ".modelRow[data-model^=compiler-first]{}",
        }
        calls: list[str] = []

        def fake_fetch(requested: str, timeout: int = 30) -> str | None:
            calls.append(requested)
            return responses[requested]

        with mock.patch.object(verify_channels, "fetch", side_effect=fake_fetch):
            ok, problems, info = verify_channels.check(url)

        self.assertEqual((ok, problems), (True, []))
        self.assertEqual(info["css_files"], 1)
        self.assertIs(info["css_selector_present"], True)
        self.assertEqual(info["arm_identity_surfaces"], 1)
        self.assertEqual(calls, [url, css_url])

    def test_check_bare_jev_and_missing_css(self):
        page = GOOD_PAGE.replace("nanojev 0.6b</div>", "jev</div>")
        with mock.patch.object(verify_channels, "fetch", side_effect=[page, "nope"]):
            ok, problems, _ = verify_channels.check("https://kvnloo.github.io/z0evals/dev/")

        self.assertIs(ok, False)
        self.assertIn("lane label 'nanojev 0.6b' not visible", problems)
        self.assertIn("bare model-identity 'jev' rendered: 'jev'", problems)
        self.assertIn(
            "CSS selector modelRow[data-model^=compiler-first] missing from shipped CSS",
            problems,
        )

    def test_check_fetch_failures(self):
        for response, expected in (
            ("__HTTP_404__", ["fetch failed: __HTTP_404__"]),
            (None, ["fetch failed: None"]),
        ):
            with self.subTest(response=response), mock.patch.object(
                verify_channels, "fetch", return_value=response
            ):
                self.assertEqual(
                    verify_channels.check("https://example.invalid/"),
                    (False, expected, {}),
                )

    def test_check_missing_markers(self):
        page = (
            '<div class="modelRow" data-model="compiler-first" '
            'data-arm-id="compiler+jev" data-model-id="nanojev_06b">nanojev 0.6b</div> '
            "nanojev+qwen4b"
        )
        with mock.patch.object(verify_channels, "fetch", return_value=page):
            ok, problems, info = verify_channels.check("https://example.invalid/")

        self.assertIs(ok, False)
        self.assertIn("external Southbridge Jev link missing", problems)
        self.assertIn("frozen arm ids missing — ids may have been renamed", problems)
        self.assertEqual(info["css_files"], 0)
        self.assertNotIn(
            "CSS selector modelRow[data-model^=compiler-first] missing from shipped CSS",
            problems,
        )

    def test_fetch_maps_errors(self):
        url = "https://example.invalid/"
        http_error = urllib.error.HTTPError(url, 503, "x", {}, None)
        with mock.patch("urllib.request.urlopen", side_effect=http_error):
            self.assertEqual(verify_channels.fetch(url), "__HTTP_503__")
        with mock.patch("urllib.request.urlopen", side_effect=TimeoutError()):
            self.assertEqual(verify_channels.fetch(url), "__ERR_TimeoutError__")

    def test_main_exit_codes(self):
        argv = ["x", "--attempts", "1", "--delay", "0"]
        with mock.patch.object(sys, "argv", argv), mock.patch.object(
            verify_channels.time, "sleep"
        ) as sleep:
            with mock.patch.object(verify_channels, "check", return_value=(True, [], {})):
                self.assertEqual(verify_channels.main(), 0)
            with mock.patch.object(
                verify_channels, "check", return_value=(False, ["p"], {})
            ):
                self.assertEqual(verify_channels.main(), 1)
            self.assertEqual(sleep.call_count, 0)


if __name__ == "__main__":
    unittest.main()
