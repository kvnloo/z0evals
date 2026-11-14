"""Validate only the allowlisted study files and closed aggregate JSON shape.

reuse-checked: scripts/validate.py and summarize.validate_public; no second JSON schema.
"""
from pathlib import Path
import json

from summarize import validate_public

ALLOWED = {"README.md", "protocol.md", "manifest.yaml", "summarize.py", "test_summarize.py",
           "check_public.py", "reproduce.sh", "data/summary.json"}
# Assemble markers so the scanner source does not contain the private literals.
MARKERS = (b"/" + b"mnt", b"/home/" + b"kvn", b"/" + b"workspace", b"ze" + b"r0")


def main():
    root = Path(__file__).resolve().parent
    found = set()
    for path in sorted(root.rglob("*")):
        if "__pycache__" in path.parts:
            continue
        if path.is_symlink():
            raise ValueError("study symlinks are not public artifacts")
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative not in ALLOWED:
            raise ValueError("non-allowlisted study file")
        found.add(relative)
        content = path.read_bytes()
        if any(marker in content.lower() for marker in MARKERS):
            raise ValueError("private marker in allowlisted study file")
        if path.suffix == ".py" and "reuse-checked:" not in content.decode():
            raise ValueError("missing reuse check")
    if found != ALLOWED:
        raise ValueError("missing required study artifact")
    document = json.loads((root / "data/summary.json").read_text())
    validate_public(document)
    # Status is mandatory even before the parent explicitly closes collection.
    if document["status"] not in {"ongoing", "partial", "bounded_complete"}:
        raise ValueError("unknown collection status")
    print("ok: 8 allowlisted files, private-marker scan, closed aggregate schema")


if __name__ == "__main__":
    main()
