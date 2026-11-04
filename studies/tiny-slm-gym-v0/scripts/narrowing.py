"""Queue item 3: how many tool-schema tokens would top-k family narrowing remove from a frontier prompt?

  python narrowing.py schemas   # Hermes' real tool schemas -> family -> token sizes (data/tool-schemas-by-family.json)
  python narrowing.py replay    # dev split: tokens removed vs miss rate for recency / bigram / ridge top-k

Counterfactual only (no model calls): a step "misses" when the true family is outside the narrowed set; on a miss we
assume the full schema list is restored for one extra call (cost = full schema tokens). Token counts are chars/4, a
provider-neutral proxy; label them as such. Only counts and rates are written to the repo.
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
sys.path.insert(0, str(HERE))


def schemas():
    sys.path.insert(0, "/workspace/hermes-home/hermes-agent")
    from model_tools import get_tool_definitions  # noqa: PLC0415
    import importlib.util  # noqa: PLC0415
    spec = importlib.util.spec_from_file_location("fam", "/mnt/zer0models/z0-wt/z0int-weight-space/src/z0int/families.py")
    fam_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fam_mod)
    family_of = fam_mod.family_of
    defs = get_tool_definitions(quiet_mode=True, skip_tool_search_assembly=True)
    by = Counter()
    names = Counter()
    tools = []
    for d in defs:
        f = d.get("function", d)
        name = f.get("name")
        n = round(len(json.dumps(d, separators=(",", ":"))) / 4)  # chars/4 token proxy
        fam = family_of(name)
        by[fam] += n
        names[fam] += 1
        tools.append({"name": name, "family": fam, "tokens": n})
    out = {"source": "hermes-agent model_tools.get_tool_definitions(all toolsets, uncollapsed)",
           "tokenizer": "chars/4 (proxy)", "n_tools": len(tools), "total_tokens": sum(by.values()),
           "families": {k: {"tools": names[k], "tokens": by[k]} for k in sorted(by)}, "tools": sorted(
               tools, key=lambda t: -t["tokens"])}
    (DATA / "tool-schemas-by-family.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "tools"}, indent=1))


def replay():
    import numpy as np  # noqa: PLC0415
    import nextaction as N  # noqa: PLC0415
    sch = json.loads((DATA / "tool-schemas-by-family.json").read_text())
    fam_tok = np.array([sch["families"].get(f, {"tokens": 0})["tokens"] for f in N.FAMILIES], dtype=float)
    always = sch["families"].get("RESPOND", {"tokens": 0})["tokens"]
    full = float(fam_tok.sum())
    Xtr, ytr, ltr = N.load(N.OUT / "train.jsonl")
    Xdv, ydv, ldv = N.load(N.OUT / "dev.jsonl")
    sess = np.array([r["session"] for r in N.rows(N.OUT / "dev.jsonl") if r["family"] in N.FAMILIES])
    P, _ = N.arms(Xtr, ytr, ltr, Xdv, ydv, ldv)
    _, inv, cnt = np.unique(sess, return_inverse=True, return_counts=True)
    w = 1.0 / cnt[inv]
    w = w / w.sum()
    res = {"split": "dev (all dev sessions; counterfactual, no model calls)", "full_schema_tokens": full,
           "tokenizer": sch["tokenizer"], "miss_policy": "miss -> one extra call with the full list", "arms": {}}
    for arm in ("recency", "bigram", "ridge"):
        order = np.argsort(-P[arm], 1)
        for k in (1, 2, 3, 4):
            keep = order[:, :k]
            hit = (keep == ydv[:, None]).any(1)
            kept = fam_tok[keep].sum(1) + always
            cost = np.where(hit, kept, kept + full)
            saved = 1 - cost / full
            res["arms"][f"{arm}@top{k}"] = {
                "miss_rate_macro": float((w * ~hit).sum()), "tokens_saved_frac_macro": float((w * saved).sum()),
                "miss_rate_rows": float((~hit).mean()), "tokens_saved_frac_rows": float(saved.mean())}
    (DATA / "narrowing-dev.json").write_text(json.dumps(res, indent=1) + "\n")
    for k, v in res["arms"].items():
        print(f"{k:14s} miss {v['miss_rate_macro']:.3f} saved {v['tokens_saved_frac_macro']:+.3f} (rows: "
              f"{v['miss_rate_rows']:.3f} / {v['tokens_saved_frac_rows']:+.3f})")


if __name__ == "__main__":
    {"schemas": schemas, "replay": replay}[sys.argv[1]]()
