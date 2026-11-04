"""Queue item 3, qualitative half: audit 200 sampled dev decisions under recency top-2 narrowing.

  python audit200.py    # -> data/audit200-dev.json (counts and rates only; rows stay under ~/.z0int)

Sampling: 200 dev decisions, at most 4 per session (so one automated loop cannot dominate), fixed seed.
Narrowed set = {last family, most frequent train family} (the recency arm's top-2; prior breaks ties).
For each miss we record the transition (last -> true family), whether it is the session's first step, the session
kind (cron vs interactive, from the session id prefix). Rows with private text are never
written to the repo; a private per-row file for Kevin's spot check goes to ~/.z0int/state/tiny-gym/nextaction/.
"""
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import nextaction as N  # noqa: E402


def main():
    train = [r for r in N.rows(N.OUT / "train.jsonl") if r["family"] in N.FAMILIES]
    prior = Counter(r["family"] for r in train).most_common()
    top = prior[0][0]
    dev = [r for r in N.rows(N.OUT / "dev.jsonl") if r["family"] in N.FAMILIES]
    by = defaultdict(list)
    for r in dev:
        by[r["session"]].append(r)
    rng = random.Random(20261104)
    pool = []
    for s, rs in sorted(by.items()):
        pool += rng.sample(rs, min(4, len(rs)))
    sample = rng.sample(pool, min(200, len(pool)))
    miss, trans, kinds, first, priv = 0, Counter(), Counter(), Counter(), []
    tot_kind = Counter()
    for r in sample:
        last = r["prev"][-1] if r["prev"] else None
        lastfam = last  # prev holds family names
        keep = {f for f in (lastfam, top, prior[1][0] if lastfam == top else None) if f}
        kind = "cron" if r["session"].startswith("cron_") else "interactive"
        tot_kind[kind] += 1
        hit = r["family"] in keep
        if not hit:
            miss += 1
            trans[f"{lastfam or 'START'}->{r['family']}"] += 1
            kinds[kind] += 1
            first[bool(not r["prev"])] += 1
        priv.append({"session": r["session"], "ts": r["ts"], "last": last, "family": r["family"], "tool": r["tool"],
                     "kept": sorted(keep), "hit": hit, "user_head": (r["user"] or "")[:160]})
    res = {"split": "dev", "n": len(sample), "sessions": len({r["session"] for r in sample}), "max_per_session": 4,
           "narrowed_to": "last family + most frequent train family (" + top + ")",
           "miss_rate": round(miss / len(sample), 3), "misses": miss,
           "miss_by_session_kind": {k: f"{kinds[k]}/{tot_kind[k]}" for k in tot_kind},
           "misses_on_first_step": first[True], "top_miss_transitions": trans.most_common(10)}
    (HERE.parent / "data" / "audit200-dev.json").write_text(json.dumps(res, indent=1) + "\n")
    p = N.OUT / "audit200-dev-rows.jsonl"
    p.write_text("".join(json.dumps(x) + "\n" for x in priv))
    p.chmod(0o600)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
