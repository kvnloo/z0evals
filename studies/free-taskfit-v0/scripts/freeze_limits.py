#!/usr/bin/env python3
"""Freeze the known per-model limits that run_taskfit.py plans against.

Reads two blobs from a z0intelligence checkout at a pinned commit and writes
frozen/limits.json, keyed by the runner's lane spec (provider/model):
  deploy/vllm-sr/limits.json            Groq/Cerebras per-model RPM/RPD/TPM/TPD (headers + docs)
  deploy/vllm-sr/profiles/catalog.json  per-route context window from each provider's /v1/models
plus published provider-wide free-tier limits (PROVIDER_DOCS) for lanes those files do not cover.

  freeze_limits.py --z0int /path/to/z0intelligence --ref origin/feat/vllm-sr-turbo-router

Refresh the upstream files (limits_inventory.py) first; never edit frozen/limits.json by hand.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "frozen" / "limits.json"
LIMITS_PATH = "deploy/vllm-sr/limits.json"
CATALOG_PATH = "deploy/vllm-sr/profiles/catalog.json"
# Lanes this study runs (runner spec -> (provider, model id at that provider)).
LANES = ["groq/openai/gpt-oss-20b", "groq/openai/gpt-oss-120b", "groq/qwen/qwen3.8-27b",
         "openrouter/nvidia/nemotron-3.5-super-vl:free", "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free",
         "nvidia/nvidia/nemotron-3-ultra-550b-a55b", "nvidia/nvidia/nemotron-3.5-super-vl-120b-a12b"]
REASONING = ("gpt-oss", "nemotron", "qwen3", "deepseek-r", "-r1", "thinking")
# Published free-tier limits for providers without per-model headers. null = unknown, never unlimited.
PROVIDER_DOCS = {
    "nvidia": {"rpm": 40, "rpd": 10000, "tpm": None, "tpd": None, "scope": "account-wide, shared across models",
               "source": "build.nvidia.com rateLimits.requestsPerMinute; offline-rate-limit-catalog free-tier-providers.md"},
    "openrouter": {"rpm": 20, "rpd": 50, "tpm": None, "tpd": None, "scope": "per key, all :free models; rpd 1000 after >=10 credits",
                   "source": "openrouter.ai/docs/api-reference/limits (key credit limit 0 -> 50/day)"},
}
# Groq answers a request whose tokens exceed the model's TPM with 413 at any concurrency.
GROQ_MAX_REQUEST = "tpm"


def blob(repo: Path, ref: str, path: str) -> tuple[bytes, str]:
    commit = subprocess.check_output(["git", "-C", str(repo), "rev-parse", ref], text=True).strip()
    data = subprocess.check_output(["git", "-C", str(repo), "show", f"{commit}:{path}"])
    return data, commit


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--z0int", required=True, type=Path)
    ap.add_argument("--ref", default="origin/feat/vllm-sr-turbo-router")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args(argv)
    lim_raw, commit = blob(a.z0int, a.ref, LIMITS_PATH)
    cat_raw, _ = blob(a.z0int, a.ref, CATALOG_PATH)
    lim, cat = json.loads(lim_raw), json.loads(cat_raw)
    per_model = {(m["provider"], m["model"]): m for m in lim["models"]}
    context = {(p, m["id"]): m.get("context") for p, v in cat["providers"].items()
               for m in (v if isinstance(v, list) else v.get("models", [])) if isinstance(m, dict)}
    lanes = {}
    for spec in LANES:
        provider, model = spec.split("/", 1)
        row = per_model.get((provider, model))
        if row:
            entry = {k: row.get(k) for k in ("rpm", "rpd", "tpm", "tpd")}
            entry["basis"] = row.get("basis") if isinstance(row.get("basis"), dict) else {"all": row.get("basis")}
            entry["scope"] = "per model"
        elif provider in PROVIDER_DOCS:
            doc = PROVIDER_DOCS[provider]
            entry = {k: doc[k] for k in ("rpm", "rpd", "tpm", "tpd")}
            entry["basis"] = {"all": "docs: " + doc["source"]}
            entry["scope"] = doc["scope"]
        else:
            continue
        entry["context"] = context.get((provider, model))
        entry["max_request_tokens"] = entry["tpm"] if provider == "groq" and GROQ_MAX_REQUEST == "tpm" else None
        entry["reasoning"] = any(t in model.lower() for t in REASONING)
        lanes[spec] = entry
    out = {
        "schema": "z0evals.free-taskfit.limits.v1",
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sources": [
            {"repo": "kvnloo/z0intelligence", "commit": commit, "path": LIMITS_PATH,
             "sha256": hashlib.sha256(lim_raw).hexdigest(), "observed_at": lim.get("observed_at")},
            {"repo": "kvnloo/z0intelligence", "commit": commit, "path": CATALOG_PATH,
             "sha256": hashlib.sha256(cat_raw).hexdigest(), "observed_at": cat.get("at")},
        ],
        "rule": ("run_taskfit.py plans every (task, lane) before sending: estimated request tokens = "
                 "ceil(len(prompt)/3.5) + max_tokens; a request above tpm, context or max_request_tokens is "
                 "written as not_eligible and never sent. null = unknown (unchecked), never unlimited."),
        "lanes": lanes,
    }
    a.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(f"wrote {a.out} ({len(lanes)} lanes) from {commit[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
