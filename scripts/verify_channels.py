#!/usr/bin/env python3
"""Verify the correction on the four live channel URLs.

Channel -> URL mapping is the one documented in `.github/workflows/pages.yml`:

    main    -> /z0evals/
    dev     -> /z0evals/dev/
    nightly -> /z0evals/nightly/
    preview -> /z0evals/next/     (never /preview/ — that is the AODL collision)

Checks per channel:
  * `nanojev 0.6b` lane label visible
  * `nanojev+qwen4b` lane label visible
  * no incorrect model-identity bare `jev` on any identity surface
  * the external Southbridge Jev reference link survives
  * `data-model="compiler-first"` present AND the matching CSS selector shipped
  * the frozen arm ids are still present verbatim

Polls while a deploy propagates.

    python3 scripts/verify_channels.py [--attempts 30] [--delay 20]
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import arm_identity as A  # noqa: E402

BASE = "https://kvnloo.github.io/z0evals"
CHANNELS = {
    "main": f"{BASE}/",
    "dev": f"{BASE}/dev/",
    "nightly": f"{BASE}/nightly/",
    "preview": f"{BASE}/next/",
}

UA = "z0evals-channel-verify/1.0"
BARE_JEVE = re.compile(r"(?<![A-Za-z0-9_])jev(?![A-Za-z0-9_-])", re.IGNORECASE)
TAG = re.compile(r"<[^>]+>")


def fetch(url: str, timeout: int = 30) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return f"__HTTP_{e.code}__"
    except Exception as e:  # noqa: BLE001
        return f"__ERR_{type(e).__name__}__"


def strip_tags(s: str) -> str:
    return html.unescape(TAG.sub(" ", s)).strip()


def identity_surfaces(raw: str) -> list[str]:
    """Visible labels on the surfaces that carry model identity."""
    labels: list[str] = []
    # elements carrying data-arm-id
    for m in re.finditer(r"<(\w+)([^>]*\bdata-arm-id=\"[^\"]*\"[^>]*)>", raw):
        tag = m.group(1)
        close = raw.find(f"</{tag}>", m.end())
        inner = raw[m.end(): close] if close != -1 else raw[m.end(): m.end() + 600]
        labels.append(strip_tags(re.sub(r"<title>.*?</title>", " ", inner, flags=re.DOTALL)))
    labels += re.findall(r'class="modelName"[^>]*>([^<]*)<', raw)
    for m in re.finditer(r'class="corpusLabel"[^>]*data-arm-id="[^"]*"[^>]*>(.*?)</text>', raw, re.DOTALL):
        labels.append(strip_tags(re.sub(r"<title>.*?</title>", " ", m.group(1), flags=re.DOTALL)))
    return [l for l in labels if l]


def check(url: str) -> tuple[bool, list[str], dict]:
    raw = fetch(url)
    problems: list[str] = []
    info: dict = {}

    if not raw or raw.startswith("__"):
        return False, [f"fetch failed: {raw}"], info

    info["bytes"] = len(raw)
    info["has_nanojev_0_6b"] = "nanojev 0.6b" in raw
    info["has_nanojev_qwen4b"] = "nanojev+qwen4b" in raw
    info["southbridge_link"] = "southbridgeai/jev" in raw
    info["data_model_compiler_first"] = 'data-model="compiler-first"' in raw
    info["frozen_arm_ids"] = "compiler+jev" in raw and "compiler+jev+qwen3.5_4b" in raw
    info["arm_identity_surfaces"] = len(re.findall(r'data-arm-id="', raw))
    info["model_id_nanojev"] = 'data-model-id="nanojev_06b"' in raw

    if not info["has_nanojev_0_6b"]:
        problems.append("lane label 'nanojev 0.6b' not visible")
    if not info["has_nanojev_qwen4b"]:
        problems.append("lane label 'nanojev+qwen4b' not visible")
    if not info["southbridge_link"]:
        problems.append("external Southbridge Jev link missing")
    if not info["data_model_compiler_first"]:
        problems.append('data-model="compiler-first" missing (CSS/DOM contract)')
    if not info["frozen_arm_ids"]:
        problems.append("frozen arm ids missing — ids may have been renamed")

    for label in identity_surfaces(raw):
        if BARE_JEVE.search(label):
            problems.append(f"bare model-identity 'jev' rendered: {label[:80]!r}")

    # the shipped CSS must carry the selector that matches the DOM attribute
    css_hrefs = re.findall(r'href="([^"]+\.css)"', raw)
    info["css_files"] = len(css_hrefs)
    css_ok = False
    for href in css_hrefs:
        # Deployed hrefs are origin-absolute (`/z0evals/dev/_next/...`), so they
        # must be resolved against the ORIGIN, not against the channel path —
        # prepending the base path again produced `/z0evals/dev/z0evals/dev/...`.
        css_url = urljoin(url, href)
        css = fetch(css_url)
        if css and not css.startswith("__") and re.search(r"modelRow\[data-model\^=compiler-first\]", css):
            css_ok = True
            break
    info["css_selector_present"] = css_ok
    if css_hrefs and not css_ok:
        problems.append("CSS selector modelRow[data-model^=compiler-first] missing from shipped CSS")

    return not problems, problems, info


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--attempts", type=int, default=24)
    ap.add_argument("--delay", type=int, default=20)
    args = ap.parse_args()

    pending = dict(CHANNELS)
    results: dict[str, tuple[bool, list[str], dict]] = {}

    for attempt in range(1, args.attempts + 1):
        still: dict[str, str] = {}
        for name, url in pending.items():
            ok, probs, info = check(url)
            results[name] = (ok, probs, info)
            if not ok:
                still[name] = url
        if not still:
            print(f"all channels verified on attempt {attempt}\n")
            break
        print(f"attempt {attempt}: waiting on {sorted(still)}")
        pending = still
        if attempt < args.attempts:
            time.sleep(args.delay)

    print(f"{'channel':10s} {'ok':3s} {'nanojev':8s} {'+qwen4b':8s} {'css':4s} "
          f"{'ref':4s} {'ids':4s} {'surfaces':8s} problems")
    print("-" * 104)
    bad = 0
    for name in CHANNELS:
        ok, probs, info = results.get(name, (False, ["not attempted"], {}))
        if not ok:
            bad += 1
        print(f"{name:10s} {'yes' if ok else 'NO':3s} "
              f"{'yes' if info.get('has_nanojev_0_6b') else 'NO':8s} "
              f"{'yes' if info.get('has_nanojev_qwen4b') else 'NO':8s} "
              f"{'yes' if info.get('css_selector_present') else 'NO':4s} "
              f"{'yes' if info.get('southbridge_link') else 'NO':4s} "
              f"{'yes' if info.get('frozen_arm_ids') else 'NO':4s} "
              f"{str(info.get('arm_identity_surfaces', '-')):8s} "
              f"{'; '.join(probs)[:60]}")
    print()
    print(f"ANCHOR CHECKS  compiler+jev -> {A.long('compiler+jev')!r}")
    print(f"               compiler+jev+qwen3.5_4b -> {A.long('compiler+jev+qwen3.5_4b')!r}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
