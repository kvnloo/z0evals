"""Recompute round-2 correction evidence without exporting raw conversation text."""
import argparse
import bisect
import json
import re
from collections import Counter
from pathlib import Path


def rows(path):
    with path.open() as source:
        return [json.loads(line) for line in source if line.strip()]


def units(usage, read=0.1):
    return (usage.get("input_tokens", 0)
            + 2 * usage.get("cache_creation_input_tokens", 0)
            + read * usage.get("cache_read_input_tokens", 0)
            + 5 * usage.get("output_tokens", 0))


def input_side(usage):
    return sum(usage.get(key, 0) for key in (
        "input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))


def differenced_usd(calls):
    previous = {}
    total = 0
    for row in calls:
        key = row["label"]
        cost = row.get("cost_usd_reported") or 0
        total += cost - (previous.get(key, 0) if row["send"] > 1 else 0)
        previous[key] = cost
    return total


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("results", type=Path)
args = parser.parse_args()
r = args.results
script = json.loads((r / "E5/script.json").read_text())["turns"]
A = {row["n"]: row for row in rows(r / "E5/A/turns.jsonl")}
B = {row["n"]: row for row in rows(r / "E5/B/turns.jsonl")}
common = sorted(A.keys() & B.keys())
assert common == list(range(1, 113))
kinds = Counter(script[n - 1]["kind"] for n in common)
eligible = [n for n in common if script[n - 1]["kind"] in ("add", "fix", "probe")]
unchanged = {arm: [n for n in eligible if not turns[n].get("changed")
                  and not turns[n].get("cut")]
             for arm, turns in (("A", A), ("B", B))}
assert {kind: kinds[kind] for kind in ("add", "fix", "probe")} == {
    "add": 27, "fix": 18, "probe": 18}
assert len(eligible) == 63 and unchanged == {"A": [35, 49, 50, 59, 80], "B": []}
as_summary = [n for n in common if re.match(
    r"\s*(user|unii|echo|tool|note|work)\s*[:(]", A[n].get("reply") or "")]
summary_kinds = dict(Counter(script[n - 1]["kind"] for n in as_summary))
assert summary_kinds == {"order": 6, "fact": 3, "corr": 2, "fix": 1}
assert sorted(set(as_summary) & set(unchanged["A"])) == [35]
batch_sizes = [batch["view_bytes"] for n in common
               for batch in A[n].get("batches_mid_turn", [])]
assert sorted(batch_sizes) == [63688, 63753, 63843]

acalls = rows(r / "E5/A/calls.jsonl")
bcalls = rows(r / "E5/B/calls.jsonl")
stockcalls = rows(r / "E5/B2/calls.jsonl")
first_input = {arm: input_side(calls[0]["per_request"][0])
               for arm, calls in (("stock", stockcalls), ("thinned", bcalls))}
assert first_input == {"stock": 23690, "thinned": 4852}
tools = bcalls[0]["events"][0]["tools"]
assert len(tools) == 4
stock = {row["n"]: row for row in rows(r / "E5/B2/turns.jsonl")}
stock_n = sorted(stock)
assert stock_n == list(range(1, 38))
stock_comparison = {"stock": round(sum(units(stock[n]["usage"]) for n in stock_n)),
                    "thinned": round(sum(units(B[n]["usage"]) for n in stock_n))}
assert stock_comparison == {"stock": 889826, "thinned": 625676}
baseline_read = sum(B[n]["usage"]["cache_read_input_tokens"] for n in common)
baseline_input = sum(input_side(B[n]["usage"]) for n in common)
assert round(baseline_read / 1e6, 2) == 32.28
assert round(baseline_input / 1e6, 2) == 32.62

turn_calls = {row["label"]: row for row in acalls if row["label"].startswith("turn ")}
starts = [turn_calls["turn " + str(A[n]["message"])]["ts"] for n in common]
compactions = [row for row in acalls if row["label"].startswith("compact ")]
comp_units = [0.0] * len(common)
comp_usd = [0.0] * len(common)
for row in compactions:
    index = max(0, min(len(common) - 1, bisect.bisect_right(starts, row["ts"]) - 1))
    comp_units[index] += units(row["usage"]) * 0.05
    comp_usd[index] += units(row["usage"]) * 1e-7
a_units = [units(A[n]["usage"]) for n in common]
b_units = [units(B[n]["usage"]) for n in common]
combined = [a + c for a, c in zip(a_units, comp_units)]
intervals = []
for lo, hi in ((26, 50), (51, 75), (76, 100), (101, 112)):
    interval = {"turns": [lo, hi], "n": hi - lo + 1,
                "means": [round(sum(values[lo - 1:hi]) / (hi - lo + 1))
                          for values in (a_units, combined, b_units)]}
    intervals.append(interval)
assert [i["means"][0] for i in intervals] == [27882, 27300, 31266, 34442]
assert intervals[1]["means"] == [27300, 32449, 40592]
assert [i["means"][2] for i in intervals] == [27839, 40592, 60898, 86316]
checkpoint75 = {
    "units": [round(sum(values[:75])) for values in (a_units, combined, b_units)],
    "usd": [round(sum(units(A[n]["usage"], 0.05) * 2e-6 for n in common[:75]), 3),
            round(sum(units(A[n]["usage"], 0.05) * 2e-6 for n in common[:75])
                  + sum(comp_usd[:75]), 3),
            round(sum(units(B[n]["usage"], 0.05) * 2e-6 for n in common[:75]), 3)]}

def crossover(left, right):
    differences = []
    delta = 0
    for a, b in zip(left, right):
        delta += a - b
        differences.append(delta)
    return next((i + 1 for i in range(len(differences))
                 if max(differences[i:]) <= 0), None)

a_usd = [units(A[n]["usage"], 0.05) * 2e-6 for n in common]
b_usd = [units(B[n]["usage"], 0.05) * 2e-6 for n in common]
combined_usd = [a + c for a, c in zip(a_usd, comp_usd)]
crossovers = {"W2_turns": crossover(a_units, b_units),
              "W2_combined": crossover(combined, b_units),
              "USD_turns": crossover(a_usd, b_usd),
              "USD_combined": crossover(combined_usd, b_usd)}
assert crossovers == {"W2_turns": 57, "W2_combined": 82,
                      "USD_turns": 80, "USD_combined": None}
assert [round(sum(x), 3) for x in (combined_usd, b_usd)] == [6.019, 5.995]

legacy_usd = {}
for arm in ("sonnet", "haiku"):
    calls = rows(r / "E3" / (arm + "-A") / "calls.jsonl")
    baseline = rows(r / "E3" / (arm + "-B") / "turns.jsonl")[:26]
    baseline_usd = sum(units(row["usage"], 0.05 if arm == "sonnet" else 0.1)
                       * (2e-6 if arm == "sonnet" else 1e-7) for row in baseline)
    corrected = differenced_usd(calls)
    legacy_usd[arm] = {"corrected": corrected, "baseline": baseline_usd,
                       "ratio": corrected / baseline_usd,
                       "sends": len(calls), "n_turns": 26}
assert round(legacy_usd["sonnet"]["corrected"], 3) == 0.635
assert round(legacy_usd["haiku"]["corrected"], 3) == 0.461
assert round(legacy_usd["sonnet"]["ratio"], 1) == 5.0
assert round(legacy_usd["haiku"]["ratio"]) == 57
scaled = rows(r / "E3/scaled-A/turns.jsonl")
scaled_baseline = rows(r / "E3/haiku-B/turns.jsonl")[:42]
scaled_units = [sum(units(row["usage"]) for row in calls)
                for calls in (scaled, scaled_baseline)]
assert len(scaled) == len(scaled_baseline) == 42
assert round(scaled_units[0] / scaled_units[1], 2) == 1.84

low = rows(r / "E4/haiku-low/calls.jsonl")
naive = sum(row["cost_usd_reported"] for row in low)
corrected = differenced_usd(low)
assert len(low) == 318 and round(naive, 3) == 0.412 and round(corrected, 3) == 0.231
e4 = json.loads((r / "E4/analysis.json").read_text())["arms"]
item_counts = {arm: e4[arm]["fidelity"]["5"]["items"] for arm in (
    "haiku-low", "haiku-medium", "haiku-high", "haiku-xhigh")}
assert sorted({value[0] for value in item_counts.values()}) == [17, 23, 25]
assert all(value[1] == 232 for value in item_counts.values())
bait_counts = {arm: len({entry[1] for entry in e4[arm]["obeyed"]})
               for arm in (*item_counts, "sonnet-medium")}
assert set(bait_counts.values()) == {2}
sonnet_answers = sorted({entry[2] for entry in e4["sonnet-medium"]["obeyed"]})
assert sonnet_answers == ["1517", "5040"]
assert all(any(answer in (row.get("result") or "")
               for row in rows(r / "E4/sonnet-medium/calls.jsonl"))
           for answer in sonnet_answers)

e1_default = rows(r / "E1/haiku-default/calls.jsonl")
e1_default += rows(r / "E1/haiku-default-nocut/calls.jsonl")
e1_default += rows(r / "E1/haiku-default-noruler/calls.jsonl")
zoom_sends = sum(any(block.get("type") == "tool_use" and "zoom" in block.get("name", "")
                     for event in row["events"] if event.get("type") == "assistant"
                     for block in event["message"].get("content", [])) for row in e1_default)
assert len(e1_default) == 271 and zoom_sends == 5
e1_baits = json.loads((r / "E1/analysis.json").read_text())["sonnet"]["bait"]
arithmetic_nodes = {entry["node"] for entry in e1_baits if entry["bait_msg"] in (6, 28)}
assert len(arithmetic_nodes) == 8

print(json.dumps({
    "eligible_edits": {"n": 63, "kinds": {k: kinds[k] for k in ("add", "fix", "probe")},
                       "unchanged": unchanged},
    "summary_style": {"n": len(as_summary), "kinds": summary_kinds, "edit_overlap": [35]},
    "batch_view_bytes": batch_sizes,
    "matched_first_request_input": first_input, "thinned_tools_n": len(tools),
    "stock_37_turn_units": stock_comparison,
    "baseline_input": {"read": baseline_read, "all_input_side": baseline_input},
    "intervals": intervals, "checkpoint75": checkpoint75,
    "stretch_mean_rise_percent": (intervals[-1]["means"][0] / intervals[0]["means"][0] - 1) * 100,
    "crossovers": crossovers,
    "endpoint_cli_usd": {"combined": sum(combined_usd), "baseline": sum(b_usd)},
    "legacy_E3_usd": legacy_usd,
    "scaled_round1": {"n": 42, "units": scaled_units, "ratio": scaled_units[0] / scaled_units[1]},
    "E4_low_usd": {"n": len(low), "naive": naive, "corrected": corrected},
    "E4_level5_items": item_counts, "E4_baits_per_arm": bait_counts,
    "E4_sonnet_medium_answers": sonnet_answers,
    "E1_default_zoom": {"sends": len(e1_default), "zoom_sends": zoom_sends},
    "E1_arithmetic_baits": {"baits": 2, "nodes": len(arithmetic_nodes),
                            "status": "stored harness classifications"},
    "all_assertions": "passed"
}, indent=2))
