"""Offline regression coverage for the Pages channel identity verifier.

The verifier is loaded from its script path, not imported as a package.
Every test installs a fake module-level fetch; the fetch-specific test also
patches urlopen before invoking the saved original function. No network calls.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
SPEC = importlib.util.spec_from_file_location(
    "verify_channels", ROOT / "scripts" / "verify_channels.py"
)
assert SPEC and SPEC.loader

# verify_channels imports arm_identity from scripts and also inserts that path.
# Restore the process import search path after loading the module.
_original_path = sys.path[:]
try:
    sys.path.insert(0, SCRIPTS)
    verify_channels = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(verify_channels)
finally:
    sys.path[:] = _original_path

_REAL_FETCH = verify_channels.fetch
CHANNEL_URL = "https://kvnloo.github.io/z0evals/dev/"
CSS_URL = "https://kvnloo.github.io/z0evals/dev/_next/a.css"
GOOD_PAGE = (
    '<html><link href="/z0evals/dev/_next/a.css">'
    '<div class="modelRow" data-model="compiler-first" '
    'data-arm-id="compiler+jev" data-model-id="nanojev_06b">'
    'nanojev 0.6b</div> nanojev+qwen4b southbridgeai/jev '
    'compiler+jev+qwen3.5_4b</html>'
)
GOOD_CSS = ".modelRow[data-model^=compiler-first]{}"


class VerifyChannelsTest(unittest.TestCase):
    def setUp(self):
        # Fail closed on any unexpected fetch: no test may reach the network.
        patcher = mock.patch.object(
            verify_channels, "fetch", side_effect=AssertionError("unexpected fetch")
        )
        self.fetch_mock = patcher.start()
        self.addCleanup(patcher.stop)

    def fake_responses(self, responses):
        # Unknown URLs are errors, rather than accidental live requests.
        self.fetch_mock.side_effect = lambda url: responses[url]

    def test_strip_tags(self):
        self.assertEqual(verify_channels.strip_tags("<b>a &amp; b</b>"), "a & b")

    def test_identity_surfaces(self):
        raw = (
            '<span class="modelName">Jev</span>'
            '<text class="corpusLabel" data-arm-id="a">'
            'lane<title>Long</title></text>'
            '<b data-arm-id="x"> </b>'
        )
        # The corpus lane is counted twice: by the generic data-arm-id scan
        # and by the specialized corpusLabel scan. Empty labels are dropped.
        self.assertEqual(verify_channels.identity_surfaces(raw), ["lane", "Jev", "lane"])

    def test_check_good_page(self):
        self.fake_responses({CHANNEL_URL: GOOD_PAGE, CSS_URL: GOOD_CSS})

        ok, problems, info = verify_channels.check(CHANNEL_URL)

        self.assertEqual((ok, problems), (True, []))
        self.assertEqual(info["css_files"], 1)
        self.assertIs(info["css_selector_present"], True)
        self.assertEqual(info["arm_identity_surfaces"], 1)
        self.assertIs(info["model_id_nanojev"], True)
        # Origin-absolute CSS href must never get a doubled /z0evals/dev/.
        self.assertEqual(
            [call.args[0] for call in self.fetch_mock.call_args_list],
            [CHANNEL_URL, CSS_URL],
        )

    def test_check_bare_jev_and_missing_css(self):
        bad_page = GOOD_PAGE.replace(">nanojev 0.6b</div>", ">jev</div>")
        self.fake_responses({CHANNEL_URL: bad_page, CSS_URL: "nope"})

        ok, problems, info = verify_channels.check(CHANNEL_URL)

        self.assertIs(ok, False)
        self.assertEqual(
            problems,
            [
                "lane label 'nanojev 0.6b' not visible",
                "bare model-identity 'jev' rendered: 'jev'",
                "CSS selector modelRow[data-model^=compiler-first] missing from shipped CSS",
            ],
        )
        self.assertEqual(info["css_files"], 1)
        self.assertIs(info["css_selector_present"], False)

    def test_check_fetch_failures(self):
        for fetched in ("__HTTP_404__", None):
            with self.subTest(fetched=fetched):
                self.fetch_mock.side_effect = None
                self.fetch_mock.return_value = fetched

                self.assertEqual(
                    verify_channels.check(CHANNEL_URL),
                    (False, [f"fetch failed: {fetched}"], {}),
                )

    def test_check_missing_markers(self):
        no_markers = (
            GOOD_PAGE.replace('<link href="/z0evals/dev/_next/a.css">', "")
            .replace("southbridgeai/jev", "reference-removed")
            .replace("compiler+jev+qwen3.5_4b", "id-removed")
        )
        self.fake_responses({CHANNEL_URL: no_markers})

        ok, problems, info = verify_channels.check(CHANNEL_URL)

        self.assertIs(ok, False)
        self.assertEqual(
            problems,
            [
                "external Southbridge Jev link missing",
                "frozen arm ids missing — ids may have been renamed",
            ],
        )
        self.assertEqual(info["css_files"], 0)
        self.assertIs(info["css_selector_present"], False)
        self.assertEqual(self.fetch_mock.call_count, 1)

    def test_fetch_maps_errors(self):
        url = "https://example.invalid/channel"
        cases = (
            (urllib.error.HTTPError(url, 503, "x", {}, None), "__HTTP_503__"),
            (TimeoutError(), "__ERR_TimeoutError__"),
        )
        for error, expected in cases:
            with self.subTest(error=type(error).__name__):
                # setUp replaced module.fetch; only the saved original is
                # invoked, with urlopen mocked to raise before any I/O.
                with mock.patch.object(
                    verify_channels.urllib.request, "urlopen", side_effect=error
                ) as urlopen:
                    self.assertEqual(_REAL_FETCH(url), expected)
                    self.assertEqual(urlopen.call_count, 1)

    def test_main_exit_codes(self):
        argv = ["x", "--attempts", "1", "--delay", "0"]
        cases = (
            ((True, [], {}), 0),
            ((False, ["p"], {}), 1),
        )
        for result, expected in cases:
            with self.subTest(expected=expected):
                with (
                    mock.patch.object(verify_channels, "check", return_value=result) as check,
                    mock.patch.object(verify_channels.time, "sleep") as sleep,
                    mock.patch.object(sys, "argv", argv),
                    contextlib.redirect_stdout(io.StringIO()),
                ):
                    self.assertEqual(verify_channels.main(), expected)

                self.assertEqual(
                    [call.args[0] for call in check.call_args_list],
                    list(verify_channels.CHANNELS.values()),
                )
                sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
