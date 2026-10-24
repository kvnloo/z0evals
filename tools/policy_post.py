#!/usr/bin/env python3
"""Publish a policy changelog as Markdown. Posts never feed policy compilation."""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]
VERSION = re.compile(r"^[0-9a-f]{64}$")
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\((https://[^\s)]+)\)")
LOCAL_LINK = re.compile(r"\[([^\]]+)\]\((file://[^)]+)\)")
SYNTHETIC_MARKER = "**Synthetic policy. This is not a real experiment promotion.**"


def public_url(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("links must be HTTPS URL strings")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("links must be public HTTPS URLs without credentials")
    if any(char.isspace() for char in value) or any(char in value for char in "<>()\\"):
        raise ValueError("link contains unsafe Markdown characters")
    return value


def change_markdown(diff: dict) -> str:
    changes = diff.get("changes")
    if not isinstance(changes, list):
        raise ValueError("JSON diff requires a changes array")
    lines = ["## Stage changes", ""]
    if not changes:
        lines.append("No stage changes.")
    for change in changes:
        if not isinstance(change, dict) or not all(key in change for key in ("rule_id", "from", "to", "because")):
            raise ValueError("each change requires rule_id, from, to and because")
        if change["from"] not in ("none", "shadow", "canary", "live") or change["to"] not in ("none", "shadow", "canary", "live"):
            raise ValueError("change stages must be none, shadow, canary or live")
        if not isinstance(change["because"], list) or not all(isinstance(item, str) for item in change["because"]):
            raise ValueError("change.because must contain finding IDs")
        lines.append(f"- `{change['rule_id']}`: {change['from']} → {change['to']}.")
        lines.append(f"  Evidence: {', '.join(change['because']) or 'no evidence recorded'}.")
    missing = diff.get("serving_missing", [])
    if not isinstance(missing, list) or not all(isinstance(rule, str) for rule in missing):
        raise ValueError("serving_missing must contain rule IDs")
    missing = sorted(set(missing) | {
        change["rule_id"] for change in changes if change.get("serving_missing") is True
    })
    if missing:
        lines.extend(["", "## Missing serving endpoints", ""])
        lines.extend(f"- `{rule}` has no matching serving endpoint." for rule in missing)
    return "\n".join(lines) + "\n"


def policy_post(
    source: str,
    *,
    from_version: str | None = None,
    to_version: str | None = None,
    policy_url: str | None = None,
    evidence_urls: list[str] | None = None,
    post_date: str | None = None,
    root: Path = ROOT,
) -> Path:
    """Render a JSON diff or Markdown changelog with public provenance links."""
    evidence = []
    synthetic = False
    replacements = {}
    for item in evidence_urls or []:
        if item.startswith("https://"):
            evidence.append(public_url(item))
        else:
            key, separator, url = item.partition("=")
            if not separator or not key:
                raise ValueError("evidence override requires FINDING_ID=https://... or LOCAL_PATH=https://...")
            replacements[key] = public_url(url)
    if source.lstrip().startswith("{"):
        diff = json.loads(source)
        if not isinstance(diff, dict):
            raise ValueError("JSON diff must be an object")
        synthetic = diff.get("synthetic", False)
        if not isinstance(synthetic, bool):
            raise ValueError("synthetic must be a boolean")
        for supplied, key in ((from_version, "from_version"), (to_version, "to_version"), (policy_url, "policy_url")):
            if supplied is not None and key in diff and supplied != diff[key]:
                raise ValueError(f"CLI and JSON disagree on {key}")
        from_version = from_version or diff.get("from_version")
        to_version = to_version or diff.get("to_version")
        policy_url = policy_url or diff.get("policy_url")
        refs = diff.get("evidence", [])
        if not isinstance(refs, list):
            raise ValueError("JSON evidence must be an array of {id, url} references")
        evidence_ids = set()
        for ref in refs:
            if not isinstance(ref, dict) or not isinstance(ref.get("id"), str) or not ref.get("id"):
                raise ValueError("JSON evidence requires id and a public URL or an explicit URL override")
            url = replacements.get(ref["id"], ref.get("url"))
            evidence_ids.add(ref["id"])
            evidence.append(public_url(url))
        body = change_markdown(diff)
        for change in diff["changes"]:
            if any(item not in evidence_ids for item in change["because"]):
                raise ValueError("every change finding ID needs an evidence URL")
    else:
        if not source.strip():
            raise ValueError("Markdown changelog is empty")
        synthetic = SYNTHETIC_MARKER in {line.strip() for line in source.splitlines()}
        for label, supplied in (("From", from_version), ("To", to_version)):
            match = re.search(rf"^{label}: `([0-9a-f]{{64}})`\s*$", source, re.M)
            if match:
                if supplied is not None and supplied != match[1]:
                    raise ValueError(f"CLI and Markdown disagree on {label} version")
                if label == "From":
                    from_version = match[1]
                else:
                    to_version = match[1]

        def replace_local(match):
            path = unquote(urlsplit(match[2]).path)
            url = replacements.get(path) or replacements.get(match[2])
            if not url:
                raise ValueError("local evidence links require an explicit public URL override")
            evidence.append(url)
            return f"[Evidence]({url})"

        body = LOCAL_LINK.sub(replace_local, source)
        if "file://" in body:
            raise ValueError("unmapped local evidence URL in Markdown")
        evidence.extend(MARKDOWN_LINK.findall(body))
    if not isinstance(from_version, str) or not VERSION.fullmatch(from_version):
        raise ValueError("from_version must be the full policy SHA-256")
    if not isinstance(to_version, str) or not VERSION.fullmatch(to_version):
        raise ValueError("to_version must be the full policy SHA-256")
    if not policy_url:
        raise ValueError("policy_url must link to the exact policy version")
    policy_url = public_url(policy_url)
    evidence = sorted({public_url(url) for url in evidence if url != policy_url})
    if not evidence:
        raise ValueError("at least one evidence URL is required")
    day = date.fromisoformat(post_date) if post_date else date.today()
    meta = {
        "title": f"Policy changes: {to_version[:12]}",
        "subtitle": "Evidence-linked policy changes, not routing instructions",
        "status": "policy-changelog",
        "author": "zer0 research",
        "date": day.isoformat(),
        "policy_from": from_version,
        "policy_version": to_version,
        "policy_url": policy_url,
        "changelog_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "evidence": evidence,
        "synthetic": synthetic,
    }
    links = "\n".join(f"- [Evidence {index}]({url})" for index, url in enumerate(evidence, 1))
    warning = (
        "> Synthetic policy evidence. This post does not report a real experiment promotion.\n\n"
        if synthetic else ""
    )
    rendered = (
        "---\n" + yaml.safe_dump(meta, sort_keys=False, allow_unicode=True) + "---\n\n"
        + f"Policy version: [`{to_version}`]({policy_url}).\n\n"
        + "This post records policy output. It does not authorize or change routes.\n\n"
        + warning
        + body.rstrip() + "\n\n## Evidence links\n\n" + links + "\n"
    )
    output = root / "posts" / "policy" / f"{day.isoformat()}-{to_version[:12]}.md"
    # Do not silently overwrite a publication or a short-hash collision.
    if output.exists():
        if output.read_text() != rendered:
            raise ValueError(f"post already exists with different content: {output}")
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Markdown or JSON changelog path, or - for stdin")
    parser.add_argument("--from-version")
    parser.add_argument("--to-version")
    parser.add_argument("--policy-url", help="public link to the exact policy artifact")
    parser.add_argument("--evidence-url", action="append", default=[],
                        help="HTTPS URL, FINDING_ID=URL for JSON, or LOCAL_PATH=URL for Markdown")
    parser.add_argument("--date", dest="post_date", help="publication date, YYYY-MM-DD")
    args = parser.parse_args()
    try:
        source = sys.stdin.read() if args.input == "-" else Path(args.input).read_text()
        output = policy_post(source, from_version=args.from_version, to_version=args.to_version,
                             policy_url=args.policy_url, evidence_urls=args.evidence_url,
                             post_date=args.post_date)
    except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
        parser.exit(1, f"policy_post: {exc}\n")
    print(output)


if __name__ == "__main__":
    main()
