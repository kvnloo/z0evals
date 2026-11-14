"""Publish aggregate-only paper-v1 measurements from private matrix JSONL.

reuse-checked: offload-and-loop-v0/summarize.py, scripts/validate.py, and
hermes-rlm bench/paper_matrix.py, paper_proxy.Ledger, paper_tasks.score_task.
Scoring and inference remain upstream. No answers or task identifiers are emitted.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
import re
import statistics

ARMS = ("base-truncated", "rlm-no-subcalls", "released-rlm", "fork-rlm", "nano-rlm")
MODELS = ("nvidia/nemotron-3-ultra-550b-a55b", "nvidia/nemotron-3.5-lightning-30b-a3b", "qwen/qwen3.8-27b")
FAMILIES = ("CodeQA", "OOLONG", "OOLONG-Pairs", "S-NIAH", "local-aggregation")
METRICS = ("graded_score", "pair_f1", "choice_accuracy", "substring_hit", "local_exact_score")
METRIC = dict(zip(FAMILIES, ("choice_accuracy", "graded_score", "pair_f1", "substring_hit", "local_exact_score")))
ROOT = MODELS[0]
SEED = 20261114
DRAWS = 2000
REPEATS = 3
# Frozen materialized coverage. Counts are task items, never repeated executions.
PLAN = (("CodeQA", 483107, 1), ("CodeQA", 1043432, 1), ("CodeQA", 1061947, 1),
        ("OOLONG", 1024, 3), ("OOLONG-Pairs", 1024, 2), ("S-NIAH", 4096, 3),
        ("local-aggregation", 32000, 3), ("local-aggregation", 300000, 3),
        ("local-aggregation", 2000000, 3))
PARAMS = ("timeout", "cell_timeout", "max_turns", "max_tokens", "sub_max_tokens", "max_subcalls",
          "max_context_chars", "base_context_chars", "nano_total_tokens", "provider_cap")
HASHES = ("plugin_sha256", "harness_sha256", "proxy_sha256", "scorer_sha256", "hermes_client_sha256")
COUNTERS = ("wall_s", "root_request_latency_s", "sub_request_latency_s", "request_attempts",
            "root_api_attempts", "sub_api_attempts", "subcalls", "cells", "tool_calls")
TOKEN_METRICS = ("root_prompt_tokens", "root_completion_tokens", "sub_prompt_tokens", "sub_completion_tokens")


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def public_protocol(row):
    """Copy only typed budgets and immutable digests, never source paths."""
    source = row.get("protocol", {})
    if type(source) is not dict:
        raise ValueError("invalid protocol object")
    result = {"root_model": row["root_model"], "sub_model": row.get("sub_model", MODELS[1]),
              "disable_thinking": source.get("disable_thinking", False),
              "hermes_ingress": source.get("hermes_ingress", "cli")}
    if result["hermes_ingress"] not in ("cli", "library"):
        raise ValueError("invalid Hermes ingress")
    if result["sub_model"] not in MODELS or type(result["disable_thinking"]) is not bool:
        raise ValueError("invalid model or thinking policy")
    for key in PARAMS:
        value = source.get(key)
        if value is not None and (not finite(value) or value < 0):
            raise ValueError("invalid protocol budget")
        result[key] = value
    for key in HASHES:
        value = source.get(key)
        if value is not None and (type(value) is not str or not re.fullmatch(r"[a-f0-9]{64}", value)):
            raise ValueError("invalid source digest")
        result[key] = value
    shas = source.get("source_shas", {})
    result["source_shas"] = {}
    for name in ("released", "fork", "nano"):
        value = shas.get(name)
        if value is not None and (type(value) is not str or not re.fullmatch(r"[a-f0-9]{40}", value)):
            raise ValueError("invalid source commit")
        result["source_shas"][name] = value
    return result


def fingerprint(protocol):
    return hashlib.sha256(json.dumps(protocol, sort_keys=True, allow_nan=False).encode()).hexdigest()


def interval(values, seed):
    rng = random.Random(seed)
    samples = sorted(statistics.fmean(rng.choices(values, k=len(values))) for _ in range(DRAWS))
    # Fixed nearest-rank percentile convention, no dependency-specific interpolation.
    return [samples[math.ceil(DRAWS * .025) - 1], samples[math.ceil(DRAWS * .975) - 1]]


def wilson(successes, total):
    z = 1.959963984540054
    p = successes / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return [max(0., center - half), min(1., center + half)]


def numeric_summary(values, observed):
    known = [v for v in values if v is not None]
    if any(not finite(v) or v < 0 for v in known):
        raise ValueError("invalid numeric measurement")
    return {"known_rows": len(known), "missing_rows": observed - len(known),
            "sum_known": math.fsum(known) if known else None,
            "mean_known": statistics.fmean(known) if known else None}


def token_value(row, role, kind):
    """Sum reported request token or latency fields, not zero-filled ledger totals."""
    accounting = row.get("accounting", {})
    requests = accounting.get("requests")
    if requests is None:
        # No request-level evidence cannot establish whether a zero was measured.
        return None
    selected = [r for r in requests if r.get("role") == role]
    if not selected:
        return 0 if requests else None
    values = [r.get(kind) for r in selected]
    known = [v for v in values if v is not None]
    if any(not finite(v) or v < 0 for v in known):
        raise ValueError("invalid reported usage")
    return math.fsum(known) if known else None


def group_summary(rows, family, size, arm, root, pid, scheduled_tasks, repeats):
    observed = len(rows)
    valid = [r for r in rows if r["valid"]]
    clusters = defaultdict(list)
    observed_clusters = defaultdict(list)
    for row in rows:
        observed_clusters[row["task_id"]].append(row)
    for row in valid:
        clusters[row["task_id"]].append(row["score"])
    task_means = [statistics.fmean(clusters[t]) for t in sorted(clusters)]
    valid_repeats = [len(clusters[t]) for t in sorted(clusters)]
    if len(task_means) < 2:
        ci_status = "insufficient_task_clusters"
    elif repeats < REPEATS or any(n < REPEATS for n in valid_repeats):
        ci_status = "insufficient_repeats"
    else:
        ci_status = "descriptive"
    ci = None
    if ci_status == "descriptive":
        seed = SEED + int(hashlib.sha256(f"{family}:{size}:{arm}:{root}:{pid}".encode()).hexdigest()[:16], 16)
        ci = interval(task_means, seed)
    # Binary task event is all scheduled repeats correct. Never count repeats as IID.
    # Local/semantic questions share corpora, so no independent-task Wilson is offered.
    binary = {"definition": "all_scheduled_repeats_correct", "eligible_tasks": 0,
              "successful_tasks": None, "rate": None, "ci95": None, "status": "not_applicable"}
    if family in ("CodeQA", "S-NIAH"):
        complete = [rs for rs in observed_clusters.values()
                    if len(rs) == repeats and all(r["valid"] for r in rs)]
        if complete and all(r["score"] in (0, 1) for rs in complete for r in rs):
            successes = sum(all(r["score"] == 1 for r in rs) for rs in complete)
            n = len(complete)
            binary.update(eligible_tasks=n, successful_tasks=successes, rate=successes / n,
                          ci95=wilson(successes, n) if n >= 2 else None,
                          status="conditional_independent_tasks" if n >= 2 else "insufficient_task_clusters")
    measurements = {}
    for key in COUNTERS:
        if key.endswith("_request_latency_s"):
            role = key.split("_", 1)[0]
            values = [token_value(r, role, "latency") for r in rows]
        else:
            values = [r.get("accounting", {}).get(key) if key.endswith("attempts") else r.get(key) for r in rows]
        measurements[key] = numeric_summary(values, observed)
    for key in TOKEN_METRICS:
        role, kind = key.split("_", 1)
        measurements[key] = numeric_summary([token_value(r, role, kind) for r in rows], observed)
    usage_flags = [r.get("accounting", {}).get("usage_complete") for r in rows]
    return {"family": family, "size_tokens": size, "arm": arm, "root_model": root, "protocol_id": pid,
            "metric": METRIC[family], "scheduled": scheduled_tasks * repeats,
            "observed": observed, "missing": scheduled_tasks * repeats - observed,
            "valid": len(valid), "invalid": observed - len(valid), "scheduled_task_clusters": scheduled_tasks,
            "observed_task_clusters": len(observed_clusters), "valid_task_clusters": len(clusters),
            "task_clusters_ge3_observed": sum(len(rs) >= REPEATS for rs in observed_clusters.values()),
            "task_clusters_ge3_valid": sum(n >= REPEATS for n in valid_repeats),
            "scheduled_repeats": repeats,
            "valid_repeats_min": min(valid_repeats) if valid_repeats else None,
            "valid_repeats_max": max(valid_repeats) if valid_repeats else None,
            "mean_score": statistics.fmean(task_means) if task_means else None,
            "row_mean_score": statistics.fmean(r["score"] for r in valid) if valid else None,
            "score_ci95": ci, "score_ci_status": ci_status, "binary_task_outcome": binary,
            "usage_complete_rows": sum(x is True for x in usage_flags),
            "usage_partial_rows": sum(x is False for x in usage_flags),
            "usage_unknown_rows": sum(x is not True and x is not False for x in usage_flags),
            "measurements": measurements}


def aggregate(paths=(), smoke=(), pilot=(), tasks=None, closed=False):
    """Return a validated public document; reject duplicated or mixed-protocol primary rows."""
    plan = {(f, s): n for f, s, n in PLAN}
    identities = None
    if tasks is not None:
        identities = {}
        for task in read_rows(tasks):
            tid = task["id"]
            if tid in identities:
                raise ValueError("duplicate scheduled task")
            identities[tid] = (task["family"], task["size_tokens"])
        counts = defaultdict(int)
        for dim in identities.values():
            counts[dim] += 1
        if dict(counts) != plan:
            raise ValueError("task manifest differs from frozen 20-task coverage")
    collected = defaultdict(list)
    protocols = {}
    seen = set()
    for kind, files in (("primary", paths), ("smoke", smoke), ("pilot", pilot)):
        for path in files:
            name = Path(path).name
            allowed = {"primary": {f"matrix-v2-{x}.jsonl" for x in ("semantic", "codeqa", "local", "sniah")},
                       "smoke": {"smoke.jsonl", "matrix-v2-smoke.jsonl", "matrix-v2-smoke-library.jsonl"},
                       "pilot": {f"matrix-{x}.jsonl" for x in ("semantic", "codeqa", "local", "sniah")}}
            if name not in allowed[kind]:
                raise ValueError("input filename does not match its cohort")
            smoke_cohorts = {"smoke.jsonl": "normal-smoke", "matrix-v2-smoke.jsonl": "thinking-off-smoke",
                             "matrix-v2-smoke-library.jsonl": "library-thinking-off-smoke"}
            cohort = smoke_cohorts[name] if kind == "smoke" else kind
            for row in read_rows(path):
                f, s, arm, root = (row[k] for k in ("family", "size_tokens", "arm", "root_model"))
                if (f, s) not in plan or arm not in ARMS or root not in MODELS:
                    raise ValueError("unknown study dimension")
                if type(row.get("task_id")) is not str or not row["task_id"]:
                    raise ValueError("missing task identity")
                if identities is not None and identities.get(row["task_id"]) != (f, s):
                    raise ValueError("task does not match scheduled identity")
                rep = row.get("rep")
                if type(rep) is not int or not 0 <= rep < (1 if kind == "smoke" else REPEATS):
                    raise ValueError("repeat outside frozen schedule")
                if type(row.get("valid")) is not bool:
                    raise ValueError("missing validity")
                if row["valid"] and (not finite(row.get("score")) or not 0 <= row["score"] <= 1):
                    raise ValueError("valid row missing finite score")
                protocol = public_protocol(row)
                if (kind == "primary" or cohort in ("thinking-off-smoke", "library-thinking-off-smoke")) and not protocol["disable_thinking"]:
                    raise ValueError("thinking-off cohort missing explicit flag")
                if kind == "smoke" and protocol["hermes_ingress"] != ("library" if cohort == "library-thinking-off-smoke" else "cli"):
                    raise ValueError("smoke ingress does not match its cohort")
                pid = fingerprint(protocol)
                protocols[pid] = protocol
                key = (cohort, pid, f, s, arm, root, row["task_id"], rep)
                if key in seen:
                    raise ValueError("duplicate task-arm-repeat within protocol")
                seen.add(key)
                collected[(cohort, f, s, arm, root, pid)].append(row)
    primary_protocols = defaultdict(set)
    for cohort, _, _, _, root, pid in collected:
        if cohort == "primary":
            primary_protocols[root].add(pid)
    if any(len(pids) > 1 for pids in primary_protocols.values()):
        raise ValueError("primary protocols differ; summarize separate snapshots")
    primary = []
    for root in sorted(set(primary_protocols) | {ROOT}):
        pid = next(iter(primary_protocols[root])) if primary_protocols[root] else "pending"
        for (family, size), n in sorted(plan.items()):
            for arm in ARMS:
                rows = collected.get(("primary", family, size, arm, root, pid), [])
                if len({r["task_id"] for r in rows}) > n:
                    raise ValueError("more observed tasks than scheduled")
                primary.append(group_summary(rows, family, size, arm, root, pid, n, REPEATS))
    complete = all(g["observed"] == g["scheduled"] for g in primary)
    status = ("bounded_complete" if complete else "partial") if closed else "ongoing"
    result = {"schema_version": "rlm-paper-aggregate.v1", "status": status,
              "seed": SEED, "bootstrap_draws": DRAWS, "expected_primary_rows_per_root": 300,
              "primary": primary, "smoke": [], "pilot": [],
              "protocols": [dict(protocol_id=pid, **p) for pid, p in sorted(protocols.items())]}
    for (cohort, family, size, arm, root, pid), rows in sorted(collected.items()):
        if cohort == "primary":
            continue
        repeats = 1 if cohort.endswith("smoke") else REPEATS
        n = 1 if cohort.endswith("smoke") else plan[family, size]
        if len({r["task_id"] for r in rows}) > n:
            raise ValueError("too many cohort tasks")
        group = group_summary(rows, family, size, arm, root, pid, n, repeats)
        group["cohort"] = cohort
        result["smoke" if cohort.endswith("smoke") else "pilot"].append(group)
    validate_public(result)
    return result


def read_rows(path):
    with Path(path).open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                try:
                    row = json.loads(line)
                except ValueError:
                    raise ValueError("malformed JSONL; preserve and repair input") from None
                if type(row) is not dict:
                    raise ValueError("JSONL row must be an object")
                yield row


# Closed output schema. There is no generic string, object, or raw-row escape hatch.
NUMBER = "number"
NULL_NUMBER = "nullable-number"
COUNT = "count"
CI = "ci"
PID = "protocol-id"
SHA256 = "sha256"
SHA1 = "sha1"
STATS = {"known_rows": COUNT, "missing_rows": COUNT, "sum_known": NULL_NUMBER, "mean_known": NULL_NUMBER}
BINARY = {"definition": ("all_scheduled_repeats_correct",), "eligible_tasks": COUNT,
          "successful_tasks": NULL_NUMBER, "rate": NULL_NUMBER, "ci95": CI,
          "status": ("not_applicable", "conditional_independent_tasks", "insufficient_task_clusters")}
GROUP = {"family": FAMILIES, "size_tokens": COUNT, "arm": ARMS, "root_model": MODELS,
         "protocol_id": PID, "metric": METRICS,
         **{k: COUNT for k in ("scheduled", "observed", "missing", "valid", "invalid", "scheduled_task_clusters",
                               "observed_task_clusters", "valid_task_clusters", "task_clusters_ge3_observed",
                               "task_clusters_ge3_valid", "scheduled_repeats", "usage_complete_rows",
                               "usage_partial_rows", "usage_unknown_rows")},
         **{k: NULL_NUMBER for k in ("valid_repeats_min", "valid_repeats_max", "mean_score", "row_mean_score")},
         "score_ci95": CI, "score_ci_status": ("insufficient_task_clusters", "insufficient_repeats", "descriptive"),
         "binary_task_outcome": BINARY, "measurements": {k: STATS for k in COUNTERS + TOKEN_METRICS}}
PROTOCOL = {"protocol_id": SHA256, "root_model": MODELS, "sub_model": MODELS, "disable_thinking": "bool",
            "hermes_ingress": ("cli", "library"),
            **{k: NULL_NUMBER for k in PARAMS}, **{k: SHA256 for k in HASHES},
            "source_shas": {k: SHA1 for k in ("released", "fork", "nano")}}
SCHEMA = {"schema_version": ("rlm-paper-aggregate.v1",), "status": ("ongoing", "bounded_complete", "partial"), "seed": COUNT,
          "bootstrap_draws": COUNT, "expected_primary_rows_per_root": COUNT, "primary": [GROUP],
          "smoke": [dict(GROUP, cohort=("normal-smoke", "thinking-off-smoke", "library-thinking-off-smoke"))],
          "pilot": [dict(GROUP, cohort=("pilot",))], "protocols": [PROTOCOL]}


def check_shape(value, schema):
    if type(schema) is dict:
        if type(value) is not dict or value.keys() != schema.keys():
            raise ValueError("aggregate has missing or non-allowlisted keys")
        for key, child in schema.items():
            check_shape(value[key], child)
    elif type(schema) is list:
        if type(value) is not list:
            raise ValueError("aggregate requires list")
        for item in value:
            check_shape(item, schema[0])
    elif type(schema) is tuple:
        if type(value) is not str or value not in schema:
            raise ValueError("aggregate has non-allowlisted text")
    elif schema in (NUMBER, NULL_NUMBER, COUNT):
        if schema == NULL_NUMBER and value is None:
            return
        if not finite(value) or value < 0 or (schema == COUNT and type(value) is not int):
            raise ValueError("aggregate has invalid number")
    elif schema == CI:
        if value is not None and (type(value) is not list or len(value) != 2 or
                                  any(not finite(x) or not 0 <= x <= 1 for x in value) or value[0] > value[1]):
            raise ValueError("aggregate has invalid interval")
    elif schema in (SHA1, SHA256, PID):
        if value is None and schema != PID:
            return
        if schema == PID and value == "pending":
            return
        length = 40 if schema == SHA1 else 64
        if type(value) is not str or not re.fullmatch(r"[a-f0-9]{%d}" % length, value):
            raise ValueError("aggregate has invalid digest")
    elif schema == "bool" and type(value) is not bool:
        raise ValueError("aggregate requires boolean")


def validate_public(document):
    check_shape(document, SCHEMA)
    complete = bool(document["primary"]) and all(g["observed"] == g["scheduled"] for g in document["primary"])
    if document["status"] == "bounded_complete" and not complete:
        raise ValueError("bounded completion requires the full scheduled coverage")
    if document["status"] == "partial" and complete:
        raise ValueError("partial status conflicts with complete coverage")
    for group in document["primary"] + document["smoke"] + document["pilot"]:
        if group["observed"] != group["valid"] + group["invalid"] or group["scheduled"] != group["observed"] + group["missing"]:
            raise ValueError("aggregate counts disagree")
        if group["usage_complete_rows"] + group["usage_partial_rows"] + group["usage_unknown_rows"] != group["observed"]:
            raise ValueError("usage counts disagree")
        for stats in group["measurements"].values():
            if stats["known_rows"] + stats["missing_rows"] != group["observed"]:
                raise ValueError("measurement counts disagree")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", nargs="*", type=Path, default=[])
    parser.add_argument("--smoke", nargs="*", type=Path, default=[])
    parser.add_argument("--pilot", nargs="*", type=Path, default=[])
    parser.add_argument("--tasks", type=Path, help="Private frozen full.jsonl; validates task identities without reading contexts")
    parser.add_argument("--closed", action="store_true", help="Parent-only finalization: bounded_complete or partial, never full replication")
    parser.add_argument("--out", type=Path, default=Path("data/summary.json"))
    parser.add_argument("--check", type=Path, help="Validate an existing public aggregate without reading raw inputs")
    args = parser.parse_args(argv)
    if args.check:
        validate_public(json.loads(args.check.read_text()))
        print("ok: closed aggregate schema and count invariants")
        return
    document = aggregate(args.raw, args.smoke, args.pilot, args.tasks, args.closed)
    text = json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.out.with_suffix(args.out.suffix + ".tmp")
    temporary.write_text(text)
    temporary.replace(args.out)
    print(f"ok: aggregate written; status {document['status']}")


if __name__ == "__main__":
    main()
