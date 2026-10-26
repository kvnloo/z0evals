#!/usr/bin/env python3
"""Aggregate private exports; no causal or independently verified-success claims."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
import hashlib
import json
import math
from pathlib import Path
import random


try:
    from .extract import MIN_CELL, OUTPUT, ZONE, private_directory, private_write
except ImportError:
    from extract import MIN_CELL, OUTPUT, ZONE, private_directory, private_write

PROVISIONAL = True
MANY_RUNS = 6  # Prespecified proxy: >=6 other starts in either lookback window.
MIN_REGRESSION = 100
BOOTSTRAPS = 400


def wilson(successes, n, z=1.959963984540054):
    if n < 0 or not 0 <= successes <= n:
        raise ValueError("invalid binomial counts")
    if not n:
        return None
    p = successes / n
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return [max(0.0, center - margin), min(1.0, center + margin)]


def observed_target(row):
    labels = row["labels"]
    if labels.get("needed_owner") is True or labels.get("stalled") is True:
        return 0
    value = labels.get("completed_unattended")
    return int(value) if value is not None else None


def cell(rows):
    rows = list(rows)
    values = [v for r in rows if (v := observed_target(r)) is not None]
    n, successes = len(values), sum(values)
    return {"total": len(rows), "n": n, "successes": successes,
            "unknown": len(rows) - n, "rate": successes / n if n else None,
            "wilson_95": wilson(successes, n),
            "status": "sufficient" if n >= MIN_CELL else "insufficient"}


def comparison(rows, feature):
    exposed, control = [], []
    missing = 0
    for r in rows:
        value = feature(r)
        if value is None:
            missing += 1
        else:
            (exposed if value else control).append(r)
    a, b = cell(exposed), cell(control)
    verdict = "insufficient"
    if min(a["n"], b["n"]) >= MIN_CELL:
        # Conservative, descriptive non-overlap rule, not a causal test.
        if a["wilson_95"][1] < b["wilson_95"][0]:
            verdict = "confirmed"
        elif a["wilson_95"][0] > b["wilson_95"][1]:
            verdict = "rejected"
    return {"verdict": verdict, "n": a["n"], "control_n": b["n"],
            "exposed_total": len(exposed), "control_total": len(control),
            "missing_feature": missing, "exposed": a, "control": b,
            "interpretation": "Descriptive association only; insufficient also covers overlapping intervals, missingness, and low power."}


def week_key(night):
    d = date.fromisoformat(night)
    return (d - timedelta(days=d.weekday())).isoformat()


def outcome_available_at(row):
    """Conservative label-availability bound; never infer it from dispatch.

    End/activity bounds also prevent inconsistent observation metadata from
    admitting a label for a still-running session. Legacy/unknown timing is
    excluded from training, but remains usable in descriptive tables.
    """
    observed = row.get("outcome_observed_at")
    if not isinstance(observed, (int, float)) or not math.isfinite(observed):
        return None
    bounds = [observed, row["start"]]
    for key in ("end", "activity_end"):
        value = row.get(key)
        if value is not None:
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                return None
            bounds.append(value)
    return max(bounds)


def week_boundary(week):
    # Night dates roll at noon: Monday 00:00-11:59 belongs to Sunday.
    return datetime.combine(date.fromisoformat(week), time(12), ZONE).timestamp()


def time_blocked_folds(rows):
    """Forward weeks; exclude entire cross-week lineages from CV.

    A lineage cannot be in multiple held-out folds. Keeping it in its last
    week would move earlier nights into later folds, so exclude it instead.
    Training labels must be observed strictly before the held-out week starts.
    """
    group_weeks = defaultdict(set)
    for r in rows:
        group_weeks[r["group"]].add(week_key(r["night"]))
    weeks = defaultdict(list)
    for i, r in enumerate(rows):
        if len(group_weeks[r["group"]]) == 1:
            weeks[week_key(r["night"])].append(i)
    earlier = []
    for week in sorted(weeks):
        test = weeks[week]
        groups = {rows[i]["group"] for i in test}
        boundary = week_boundary(week)
        train = [i for i in earlier if rows[i]["group"] not in groups
                 and (available := outcome_available_at(rows[i])) is not None
                 and available < boundary]
        if train:
            yield train, test
        earlier.extend(test)


def auc(y, scores):
    positives = sum(y)
    negatives = len(y) - positives
    if not positives or not negatives:
        return None
    pairs = sorted(zip(scores, y))
    rank_sum = 0.0
    i = 0
    while i < len(pairs):
        j = i + 1
        while j < len(pairs) and pairs[j][0] == pairs[i][0]:
            j += 1
        rank_sum += ((i + 1 + j) / 2) * sum(v for _, v in pairs[i:j])
        i = j
    return (rank_sum - positives * (positives + 1) / 2) / (positives * negatives)


def design(rows, harnesses):
    names = ["intercept", "hour_sin", "hour_cos", "weekday_sin", "weekday_cos",
             "log_prompt_length", "log_preceding_30", "log_preceding_60"]
    flags = ["acceptance", "open_ended", "mentions_branch", "mentions_pr", "mentions_checkpoint", "mentions_resume", "is_automated"]
    names += flags + [k + "_missing" for k in ["prompt_length", *flags]]
    names += ["harness_" + h for h in harnesses]
    matrix = []
    for r in rows:
        f = r["features"]
        vector = [1.0, math.sin(2 * math.pi * f["start_hour"] / 24), math.cos(2 * math.pi * f["start_hour"] / 24),
                  math.sin(2 * math.pi * f["weekday"] / 7), math.cos(2 * math.pi * f["weekday"] / 7),
                  math.log1p(f["prompt_length"] or 0) / 10,
                  math.log1p(f["preceding_30"]) / 5, math.log1p(f["preceding_60"]) / 5]
        vector += [float(f[k] or False) for k in flags]
        vector += [float(f[k] is None) for k in ["prompt_length", *flags]]
        vector += [float(f["harness"] == h) for h in harnesses]
        matrix.append(vector)
    return names, matrix


def sigmoid(value):
    value = max(-30.0, min(30.0, value))
    return 1 / (1 + math.exp(-value))


def fit_logistic(x, y):
    """Small fixed L2 model, batch gradient descent; no tuning on held-out data."""
    n, width = len(x), len(x[0])
    weights = [0.0] * width
    for _ in range(180):
        gradient = [0.0] * width
        for row, target in zip(x, y):
            error = sigmoid(sum(a * b for a, b in zip(row, weights))) - target
            for j, value in enumerate(row):
                gradient[j] += error * value
        new = [w - 0.5 * (g / n + (0.01 * w if j else 0)) for j, (w, g) in enumerate(zip(weights, gradient))]
        if max(abs(a - b) for a, b in zip(new, weights)) < 1e-6:
            weights = new
            break
        weights = new
    return weights


def regression(rows):
    if len(rows) < MIN_REGRESSION:
        return {"status": "not fitted (n < 100)", "n": len(rows), "weights": None}
    usable = [r for r in rows if observed_target(r) is not None]
    classes = Counter(observed_target(r) for r in usable)
    if len(usable) < MIN_REGRESSION or min(classes.get(0, 0), classes.get(1, 0)) < MIN_CELL:
        return {"status": "not fitted (insufficient reliably labeled runs or outcome classes)", "n": len(usable), "weights": None}
    predictions, folds = [], 0
    for train, test in time_blocked_folds(usable):
        y = [int(observed_target(usable[i]) or 0) for i in train]
        if len(train) < MIN_REGRESSION or min(sum(y), len(y) - sum(y)) < MIN_CELL:
            continue
        # Vocabulary from train only; unseen harnesses get all-zero indicators.
        harnesses = sorted({usable[i]["features"]["harness"] for i in train})
        _, x = design([usable[i] for i in train], harnesses)
        weights = fit_logistic(x, y)
        _, test_x = design([usable[i] for i in test], harnesses)
        for i, vector in zip(test, test_x):
            predictions.append((week_key(usable[i]["night"]), observed_target(usable[i]), sigmoid(sum(a * b for a, b in zip(vector, weights)))))
        folds += 1
    if len({w for w, _, _ in predictions}) < 4 or not predictions:
        return {"status": "not fitted (fewer than four eligible held-out weeks after lineage and outcome-availability purging)", "n": len(usable), "folds": folds, "weights": None}
    point = auc([y for _, y, _ in predictions], [p for _, _, p in predictions])
    if point is None:
        return {"status": "not fitted (held-out outcomes single-class)", "n": len(usable), "weights": None}
    # Cluster bootstrap held-out weeks, keeping each night's rows together.
    blocks = defaultdict(list)
    for w, y, p in predictions:
        blocks[w].append((y, p))
    weeks, rng, samples = sorted(blocks), random.Random(1729), []
    for _ in range(BOOTSTRAPS):
        draw = [pair for w in rng.choices(weeks, k=len(weeks)) for pair in blocks[w]]
        value = auc([y for y, _ in draw], [p for _, p in draw])
        if value is not None:
            samples.append(value)
    if len(samples) < 100:
        return {"status": "not fitted (unstable week-bootstrap interval)", "n": len(usable), "weights": None}
    samples.sort()
    harnesses = sorted({r["features"]["harness"] for r in usable})
    names, x = design(usable, harnesses)
    weights = fit_logistic(x, [observed_target(r) for r in usable])
    return {"status": "fitted", "n": len(usable), "oof_n": len(predictions), "folds": folds,
            "auc": point, "auc_95": [samples[int(.025 * (len(samples) - 1))], samples[int(.975 * (len(samples) - 1))]],
            "interval_method": "400 seeded held-out-week cluster bootstrap draws; percentile interval, no causal interpretation",
            "weights": dict(zip(names, weights)), "penalty": "L2=0.01, intercept unpenalized; fixed transforms, no tuning",
            "warning": "Exploratory surrogate completion classifier; coefficients are not validated readiness policy weights."}


def bucket(key, value):
    if value is None:
        return "unknown"
    if key.startswith("preceding_"):
        return "6+" if value >= MANY_RUNS else "1-5" if value else "0"
    if key == "prompt_length":
        return "0-499" if value < 500 else "500-1999" if value < 2000 else "2000+"
    return str(value)


def analyze(rows, extraction):
    cohort = [r for r in rows if r["overnight"]]
    tables = {}
    feature_names = ["start_hour", "weekday", "harness", "provider", "model", "prompt_length", "acceptance", "open_ended", "preceding_30", "preceding_60", "mentions_branch", "mentions_pr", "mentions_checkpoint", "mentions_resume", "is_automated"]
    for feature in feature_names:
        groups = defaultdict(list)
        for r in cohort:
            groups[bucket(feature, r["features"].get(feature))].append(r)
        tables[feature] = {key: cell(group) for key, group in sorted(groups.items())}
    patterns = {
        "open_ended_bedtime_prompts": comparison(cohort, lambda r: r["features"]["open_ended"]),
        "many_recent_starts": comparison(cohort, lambda r: r["features"]["preceding_30"] >= MANY_RUNS or r["features"]["preceding_60"] >= MANY_RUNS),
    }
    # These are post-dispatch labels, not predictors. Project-level proxies do
    # not establish identical tasks, intent to resume, or benefit from resuming.
    for name, key in [("restart_instead_of_resume", "restarted_not_resumed"), ("evening_cut_never_resumed", "evening_cut_never_resumed")]:
        population = cohort if key == "restarted_not_resumed" else rows
        values = [r["labels"].get(key) if key == "restarted_not_resumed" else r.get(key) for r in population]
        patterns[name] = {"verdict": "insufficient", "n": sum(v is True for v in values),
                          "observable_n": sum(v is not None for v in values),
                          "population_n": len(population),
                          "reason": "Project/time/prompt proxy only; no reliable task-equivalence or intent-to-resume source. Cannot confirm or reject the named anti-pattern."}
    model = regression(cohort)
    receipt = {"provisional": PROVISIONAL, "extraction": extraction,
               "counts": {"all_runs": len(rows), "overnight": len(cohort),
                          "labeled": sum(observed_target(r) is not None for r in cohort)},
               "overall": cell(cohort), "label_counts": {k: dict(Counter(str(r["labels"].get(k)) for r in cohort)) for k in ["completed_unattended", "stalled", "restarted_not_resumed", "needed_owner"]},
               "tables": tables, "anti_patterns": patterns, "regression": model,
               "label_availability": {
                   "completed_unattended": "Source-reported completion surrogate only; no proof of no owner intervention.",
                   "stalled": "Independent native exit timestamp or explicit failed termination required.",
                   "needed_owner": "Positive exact timestamped links only; unavailable negatives. If no positive links, dropped from observed targets.",
                   "restarted_not_resumed": "Project-level heuristic only; dropped from outcome target and regression."},
               "decision_rule": "Both groups need >=15 labeled runs; nonoverlapping Wilson 95% intervals in harmful direction confirms descriptive association, opposite rejects; otherwise insufficient. No multiplicity correction, no causal claim.",
               "limitations": ["Unknown outcomes excluded from rates, never counted as failures.",
                               "Training labels require observed timing strictly before held-out night-week boundary; unknown timing is excluded.",
                               "Mutable source summaries use extraction read time as a conservative availability bound, not historical exit time.",
                               "No-event tail requires independent end timestamp; AgentsView last activity is not an independent end.",
                               "Owner intervention negatives unavailable; completion label is a surrogate, not proof of unattended execution.",
                               "Post-dispatch restart/evening-cut proxies excluded from regression.",
                               "Overnight selection conditions on future activity and is not itself a dispatch-time predictor.",
                               "Wilson intervals assume independent Bernoulli trials; within-night/task dependence may make them optimistic.",
                               "Retrospective observational data cannot establish necessary hard readiness gates."]}
    rubric = {"provisional": True, "supported_hard_gates": [],
              "proposed_unvalidated_gates": ["acceptance criteria", "checkpoint/resume plan", "no open questions", "approved before 23:00"],
              "hard_gate_reason": "Observational associations do not prove necessary gates; approval timestamps and open-question resolution are not measured.",
              "weights": model["weights"], "weights_reason": model["status"],
              "usage": "Research artifact only. Do not enforce or promote these exploratory coefficients as runtime policy."}
    return receipt, rubric


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    out = private_directory(args.input_dir)
    data = out / "runs.jsonl"
    extraction = json.loads((out / "extraction.json").read_text())
    sha = hashlib.sha256()
    rows = []
    with data.open() as f:
        for line in f:
            sha.update(line.encode())
            rows.append(json.loads(line))
    if sha.hexdigest() != extraction["runs_sha256"]:
        raise ValueError("frozen extraction hash mismatch")
    receipt, rubric = analyze(rows, extraction)
    receipt["analyze_script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    private_write(out / "receipt.json", json.dumps(receipt, indent=2) + "\n")
    private_write(out / "readiness_rubric.json", json.dumps(rubric, indent=2) + "\n")
    lines = ["# PROVISIONAL overnight forensics", "", "Source-reported completion surrogate, not independently verified success or proof of no owner intervention.", "", f"Overnight runs: {receipt['counts']['overnight']}; labeled: {receipt['counts']['labeled']}.", "", "| Anti-pattern | Verdict | n (exposed/proxy) |", "|---|---|---:|"]
    for key, result in receipt["anti_patterns"].items():
        lines.append(f"| {key} | {result['verdict']} | {result['n']} |")
    lines += ["", "For comparisons, n is exposed labeled runs; for restart/evening-cut, n is positive project-level proxies, not proven incidents.", "", f"Regression: {receipt['regression']['status']}.", "", "Hard gates: none validated. See receipt.json for denominators, unknowns, Wilson intervals, and limitations."]
    private_write(out / "RECEIPT.md", "\n".join(lines) + "\n")
    print(json.dumps({"counts": receipt["counts"], "anti_patterns": {k: {"verdict": v["verdict"], "n": v["n"]} for k, v in receipt["anti_patterns"].items()}, "regression": receipt["regression"]["status"]}))


if __name__ == "__main__":
    main()
