#!/usr/bin/env python3
"""Turn a Hermes Index snapshot into z0intelligence `generate_catalog.py --benchmark` rows.

Output shape (consumed unchanged by kvnloo/z0intelligence
operations/model-routing/generate_catalog.py, Catalog.benchmarks):

  {"rows": [{provider, model, task_class, benchmark, score, unit, source, observed_at}, ...]}

The catalog stores these under models[].benchmarks with basis
`external_benchmark`. They never become p_accept: that generator only sets
p_accept from canonical acceptance findings (see free-taskfit-v0).

Every row carries the provenance a reader needs without the snapshot file:
the source URL, capture time, raw page sha256 and whether the page flagged the
number provisional. Provisional costs are emitted with "[provisional]" in the
benchmark name because the catalog keeps only the name, score and source.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

TASK_CLASS = {
    "hermes_index": "external.hermes_index.mean",
    "hermes_bench": "external.hermes_bench",
    "terminalbench_4": "external.terminalbench_4",
    "terminalbench_science": "external.terminalbench_science",
    "skillsbench": "external.skillsbench",
}
LABEL = {"hermes_index": "Hermes Index", "hermes_bench": "Hermes Bench", "terminalbench_4": "TerminalBench 4",
         "terminalbench_science": "TerminalBench Science", "skillsbench": "SkillsBench (clean)"}


def rows_for(snapshot: dict, identity_map: dict, *, include_free_variants: bool = True) -> tuple[list[dict], list[dict]]:
    source = f"{snapshot['source_url']}#captured={snapshot['captured_at']}&sha256={snapshot['raw_sha256']}"
    families = identity_map["families"]
    out, skipped = [], []
    for row in snapshot["rows"]:
        family = families.get(row["model"])
        if family is None:
            skipped.append({"model": row["model"], "reason": "not in identity map"})
            continue
        targets = [(p, m, "family_alias") for p, m in family.get("aliases", [])]
        if include_free_variants:
            targets += [(p, m, "free_variant") for p, m in family.get("free_variants", [])]
        if not targets:
            skipped.append({"model": row["model"], "reason": family.get("unmapped_reason", "no catalog alias")})
            continue
        metrics = [("hermes_index", row["hermes_index"], row["usd_per_task"], row["cost_provisional"])]
        metrics += [(k, v["score"], v["usd_per_task"], v["provisional"]) for k, v in row["suites"].items()]
        for provider, model, alias_kind in targets:
            suffix = "" if alias_kind == "family_alias" else " [free variant: same family, endpoint weights unverified]"
            for key, score, cost, provisional in metrics:
                common = {"provider": provider, "model": model, "source": source,
                          "observed_at": snapshot["captured_at"], "task_class": TASK_CLASS[key]}
                out.append({**common, "benchmark": f"{LABEL[key]} (Hermes Agent harness, pass@1, source-reported){suffix}",
                            "score": score, "unit": "percent"})
                if alias_kind == "free_variant":
                    continue  # Nous's measured $/task is not what a free route costs; don't attach it.
                out.append({**common, "benchmark": f"{LABEL[key]} cost per task{' [provisional]' if provisional else ''}",
                            "score": cost, "unit": "USD_per_task"})
    return out, skipped


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser()
    ap.add_argument("snapshot")
    ap.add_argument("--identity-map", default=str(here / "data" / "identity-map.json"))
    ap.add_argument("--no-free-variants", action="store_true")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    snap = json.loads(Path(args.snapshot).read_text())
    idmap = json.loads(Path(args.identity_map).read_text())
    rows, skipped = rows_for(snap, idmap, include_free_variants=not args.no_free_variants)
    payload = {"schema": "z0int.external-benchmark-rows.v1", "snapshot": {k: snap[k] for k in
               ("source_url", "captured_at", "raw_sha256", "evidence_status")}, "use_rule": snap["use_rule"],
               "skipped": skipped, "rows": rows}
    Path(args.out).write_text(json.dumps(payload, indent=1) + "\n")
    print(f"{len(rows)} rows, {len(skipped)} skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
