"""tiny-slm-gym-v0 loop C + controls for Hermes tool-family next_action. Private data never leaves ~/.z0int.

  python nextaction.py split      # session-grouped time split + purge gap -> ~/.z0int/state/tiny-gym/nextaction/
  python nextaction.py controls   # majority / recency / bigram / ridge on dev (trainer view) -> data/controls-dev.json
  python nextaction.py parity     # the original row-level 80/20 split, to reproduce majority 0.319 / ridge 0.412

Features are the ones behind the earlier ridge baseline (z0int/train.py): 96-dim character-trigram hashes of the
user message and of the previous five families. The `tool` field is the label's source and never a feature.
Only counts, rates and sha256 hashes are written to the repo (data/); rows stay under ~/.z0int.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

SRC = Path.home() / ".z0int" / "episodes" / "next_action.jsonl"
OUT = Path.home() / ".z0int" / "state" / "tiny-gym" / "nextaction"
REPO_DATA = Path(__file__).resolve().parent.parent / "data"
FAMILIES = ["READ_SEARCH", "EDIT", "EXECUTE", "WEB", "DELEGATE", "VERIFY", "RESPOND", "ABSTAIN"]
FRACS = (0.70, 0.10, 0.20)  # train / dev / sealed test sessions, ordered by session start time
PURGE_H = 6.0               # sessions starting within this many hours before a boundary are dropped
PN = 96


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rows(path: Path):
    with path.open() as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def split():
    by_s = defaultdict(list)
    for r in rows(SRC):
        by_s[r["session"]].append(r)
    sess = sorted(by_s, key=lambda s: by_s[s][0]["ts"])
    total = sum(len(v) for v in by_s.values())
    cut, acc, names, bounds = [], 0, ("train", "dev", "test"), []
    # fractions are of SESSIONS (the independent unit): a few early sessions hold thousands of rows each
    target = [FRACS[0] * len(sess), (FRACS[0] + FRACS[1]) * len(sess)]
    assign = {}
    k = 0
    for i, s in enumerate(sess):
        while k < 2 and i >= target[k]:
            bounds.append(by_s[s][0]["ts"])
            k += 1
        assign[s] = names[k]
        acc += len(by_s[s])
    purged = set()
    for b in bounds:
        for s in sess:
            t0 = by_s[s][0]["ts"]
            if b - PURGE_H * 3600 <= t0 < b:  # whole sessions go by start time; purge only near-boundary starts
                purged.add(s)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "sealed").mkdir(exist_ok=True)
    os.chmod(OUT, 0o700)
    os.chmod(OUT / "sealed", 0o700)
    paths = {"train": OUT / "train.jsonl", "dev": OUT / "dev.jsonl", "test": OUT / "sealed" / "test.jsonl"}
    fh = {k: open(p, "w") for k, p in paths.items()}
    stats = {k: {"rows": 0, "sessions": 0, "families": Counter()} for k in paths}
    for s in sess:
        if s in purged:
            continue
        a = assign[s]
        stats[a]["sessions"] += 1
        for r in by_s[s]:
            fh[a].write(json.dumps(r) + "\n")
            stats[a]["rows"] += 1
            stats[a]["families"][r["family"]] += 1
    for f in fh.values():
        f.close()
    for p in paths.values():
        os.chmod(p, 0o600)
    import datetime as dt
    out = {"source": str(SRC), "source_sha256": sha(SRC), "source_rows": total, "source_sessions": len(sess),
           "fractions": FRACS, "purge_hours": PURGE_H,
           "boundaries_utc": [dt.datetime.fromtimestamp(b, dt.timezone.utc).isoformat() for b in bounds],
           "purged_sessions": len(purged), "purged_rows": sum(len(by_s[s]) for s in purged),
           "splits": {k: {"rows": v["rows"], "sessions": v["sessions"], "families": dict(v["families"]),
                          "sha256": sha(paths[k])} for k, v in stats.items()},
           "sealed_reader": "tiny-evaluator only (convention + hash; same OS user, so not OS-enforced)"}
    REPO_DATA.mkdir(parents=True, exist_ok=True)
    (REPO_DATA / "splits.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "splits"} | {
        "splits": {k: {kk: vv for kk, vv in v.items() if kk != "families"} for k, v in out["splits"].items()}}, indent=1))


# ------------------------------------------------------------------ features and controls
def _hash(text: str, dim: int = PN) -> np.ndarray:  # verbatim logic of z0int/train.py:_hash
    x = np.zeros(dim)
    t = (text or "").lower()
    if len(t) < 3:
        t = t.ljust(3)
    for i in range(len(t) - 2):
        h = hashlib.blake2b(t[i:i + 3].encode(), digest_size=8).digest()
        x[int.from_bytes(h, "little") % dim] += 1.0
    n = np.linalg.norm(x)
    return x / n if n else x


def load(path: Path):
    idx = {n: i for i, n in enumerate(FAMILIES)}
    R = [r for r in rows(path) if r["family"] in idx]
    X = np.stack([np.concatenate([_hash(r.get("user") or ""), _hash(" ".join(r.get("prev") or []))]) for r in R])
    y = np.array([idx[r["family"]] for r in R])
    last = np.array([idx.get((r.get("prev") or [None])[-1], -1) if r.get("prev") else -1 for r in R])
    return X, y, last


def ridge_fit(X, y, l2=1e-2):
    Y = np.eye(len(FAMILIES))[y]
    return np.linalg.solve(X.T @ X + l2 * np.eye(X.shape[1]), X.T @ Y)


def softmax(z):
    z = z - z.max(1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(1, keepdims=True)


def metrics(P, y):
    """P: (n, C) probabilities. Top-1/top-3, multiclass Brier, log loss, ECE (15 bins), k for 98% coverage."""
    n = len(y)
    order = np.argsort(-P, 1)
    rank = np.argmax(order == y[:, None], 1)
    cov = {k: float((rank < k).mean()) for k in range(1, P.shape[1] + 1)}
    conf, pred = P.max(1), P.argmax(1)
    bins = np.minimum((conf * 15).astype(int), 14)
    ece = sum(abs((pred[bins == b] == y[bins == b]).mean() - conf[bins == b].mean()) * (bins == b).sum() / n
              for b in range(15) if (bins == b).any())
    Y = np.eye(P.shape[1])[y]
    return {"n": n, "top1": cov[1], "top3": cov[3], "brier": float(((P - Y) ** 2).sum(1).mean()),
            "logloss": float(-np.log(np.clip(P[np.arange(n), y], 1e-12, 1)).mean()), "ece": float(ece),
            "k_for_98pct": next(k for k, c in cov.items() if c >= 0.98)}


def wmetrics(P, y, w):
    """Session-macro versions: each row weighted 1/len(its session), so long automated loops cannot dominate."""
    w = w / w.sum()
    order = np.argsort(-P, 1)
    rank = np.argmax(order == y[:, None], 1)
    Y = np.eye(P.shape[1])[y]
    cov = {k: float((w * (rank < k)).sum()) for k in range(1, P.shape[1] + 1)}
    return {"top1": cov[1], "top3": cov[3], "brier": float((w * ((P - Y) ** 2).sum(1)).sum()),
            "logloss": float((w * -np.log(np.clip(P[np.arange(len(y)), y], 1e-12, 1))).sum()),
            "k_for_98pct": next(k for k, c in cov.items() if c >= 0.98)}


def macro_ci(v: np.ndarray, groups: np.ndarray, B: int = 4000, seed: int = 0):
    """95% CI of the session-macro mean of v: resample sessions, average each session's mean."""
    rng = np.random.default_rng(seed)
    ug, inv = np.unique(groups, return_inverse=True)
    per = np.bincount(inv, weights=v) / np.bincount(inv)
    s = [per[rng.integers(0, len(per), len(per))].mean() for _ in range(B)]
    return [float(np.percentile(s, 2.5)), float(per.mean()), float(np.percentile(s, 97.5))]


def boot_ci(correct: np.ndarray, groups: np.ndarray | None = None, B: int = 2000, seed: int = 0):
    rng = np.random.default_rng(seed)
    if groups is None:
        s = [correct[rng.integers(0, len(correct), len(correct))].mean() for _ in range(B)]
    else:
        ug = np.unique(groups)
        gi = {g: np.where(groups == g)[0] for g in ug}
        s = []
        for _ in range(B):
            pick = np.concatenate([gi[g] for g in rng.choice(ug, len(ug))])
            s.append(correct[pick].mean())
    return [float(np.percentile(s, 2.5)), float(np.percentile(s, 97.5))]


def arms(Xtr, ytr, ltr, Xev, yev, lev, Xcal=None, ycal=None):
    C = len(FAMILIES)
    prior = (np.bincount(ytr, minlength=C) + 1) / (len(ytr) + C)
    out = {"majority": np.tile(prior, (len(yev), 1))}
    big = np.ones((C + 1, C))  # add-one bigram on last family (row C = no previous step)
    for a, b in zip(ltr, ytr):
        big[a if a >= 0 else C, b] += 1
    big /= big.sum(1, keepdims=True)
    out["bigram"] = big[np.where(lev >= 0, lev, C)]
    rec = np.tile(prior, (len(yev), 1)) * 1e-3  # recency: the last family, prior as tie-breaker
    rec[np.arange(len(yev))[lev >= 0], lev[lev >= 0]] = 1.0
    out["recency"] = rec / rec.sum(1, keepdims=True)
    W = ridge_fit(Xtr, ytr)
    S = Xev @ W
    T = 1.0
    if Xcal is not None:  # temperature for ridge scores, fit on the calibration rows only
        Sc = Xcal @ W
        best = min((float(-np.log(np.clip(softmax(Sc * t)[np.arange(len(ycal)), ycal], 1e-12, 1)).mean()), t)
                   for t in np.geomspace(0.5, 64, 40))
        T = best[1]
    out["ridge"] = softmax(S * T)
    return out, {"ridge_params": int(W.size), "ridge_temperature": float(T)}


def controls():
    Xtr, ytr, ltr = load(OUT / "train.jsonl")
    Xdv, ydv, ldv = load(OUT / "dev.jsonl")
    sess = np.array([r["session"] for r in rows(OUT / "dev.jsonl") if r["family"] in FAMILIES])
    half = len(np.unique(sess)) // 2  # calibrate on the first half of dev sessions, score on the second half
    first = set(list(dict.fromkeys(sess))[:half])
    cal = np.array([s in first for s in sess])
    P, info = arms(Xtr, ytr, ltr, Xdv[~cal], ydv[~cal], ldv[~cal], Xdv[cal], ydv[cal])
    res = {"split": "dev (second half of dev sessions; first half calibrates ridge temperature)",
           "train_rows": int(len(ytr)), **info, "arms": {}}
    sc = sess[~cal]
    _, inv, cnt = np.unique(sc, return_inverse=True, return_counts=True)
    w = 1.0 / cnt[inv]  # session-macro: every session counts once, whatever its length
    res["scoring_sessions"] = int(len(cnt))
    res["largest_session_row_share"] = float(cnt.max() / cnt.sum())
    mbdir = os.environ.get("TINY_MB_PATH", "/workspace/evolution-lab")  # Evolution Lab's local_plasticity (read-only)
    try:
        sys.path.insert(0, mbdir)
        from evolution_lab.jev_distill import fit_fly, predict_fly  # noqa: PLC0415
        fly = fit_fly(Xtr, ytr, len(FAMILIES), n_kc=96, seed=1)
        mb_pred = predict_fly(Xdv[~cal], fly)
        res["mb"] = {"source": mbdir, "n_kc": 96, "n_params": int(fly.get("n_params", 0))}
    except Exception as e:  # noqa: BLE001 - report, never fake
        mb_pred, res["mb"] = None, {"unavailable": f"{type(e).__name__}: {e}"}
    yy = ydv[~cal]
    corr = {k: (p.argmax(1) == yy).astype(float) for k, p in P.items()}
    if mb_pred is not None:
        corr["mb"] = (mb_pred == yy).astype(float)
    for k, c in corr.items():
        m = {}
        if k in P:
            m = {"row_micro": metrics(P[k], yy), "session_macro": wmetrics(P[k], yy, w)}
            m["row_micro"]["top1_ci95_session_clustered"] = boot_ci(c, sc)
        else:
            m = {"row_micro": {"top1": float(c.mean())}, "session_macro": {"top1": float((w * c).sum() / w.sum())}}
        m["session_macro"]["top1_ci95"] = macro_ci(c, sc)
        if k != "recency":
            m["session_macro"]["top1_minus_recency_ci95"] = macro_ci(c - corr["recency"], sc)
        res["arms"][k] = m
    (REPO_DATA / "controls-dev.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))


def parity():
    X, y, last = load(SRC)
    n_c = max(100, int(len(y) * 0.2))
    n_tr = len(y) - n_c
    P, info = arms(X[:n_tr], y[:n_tr], last[:n_tr], X[n_tr:], y[n_tr:], last[n_tr:])
    res = {"split": "original row-level 80/20 (z0int/train.py); reproduces the published baselines",
           "expected": {"majority": 0.3186, "ridge": 0.4122}, **info,
           "arms": {k: metrics(p, y[n_tr:]) for k, p in P.items()}}
    (REPO_DATA / "controls-parity.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: round(v["top1"], 4) for k, v in res["arms"].items()}))


def sealed():
    """tiny-evaluator's ONE pass on the sealed test window: fit on train+dev, score test, session-macro + CIs."""
    tp = OUT / "sealed" / "test.jsonl"
    if json.loads((REPO_DATA / "splits.json").read_text())["splits"]["test"]["sha256"] != sha(tp):
        raise SystemExit("sealed test hash mismatch")
    if (REPO_DATA / "controls-sealed.json").exists():
        raise SystemExit("sealed pass already recorded; a second pass would spend the holdout")
    Xa, ya, la = load(OUT / "train.jsonl")
    Xb, yb, lb = load(OUT / "dev.jsonl")
    Xtr, ytr, ltr = np.vstack([Xa, Xb]), np.concatenate([ya, yb]), np.concatenate([la, lb])
    Xte, yte, lte = load(tp)
    sess = np.array([r["session"] for r in rows(tp) if r["family"] in FAMILIES])
    P, info = arms(Xtr, ytr, ltr, Xte, yte, lte)
    sys.path.insert(0, os.environ.get("TINY_MB_PATH", "/workspace/evolution-lab"))
    from evolution_lab.jev_distill import fit_fly, predict_fly  # noqa: PLC0415
    corr = {k: (p.argmax(1) == yte).astype(float) for k, p in P.items()}
    corr["mb"] = (predict_fly(Xte, fit_fly(Xtr, ytr, len(FAMILIES), n_kc=96, seed=1)) == yte).astype(float)
    _, inv, cnt = np.unique(sess, return_inverse=True, return_counts=True)
    res = {"split": "sealed test (fit on train+dev)", "test_rows": int(len(yte)), "test_sessions": int(len(cnt)),
           "largest_session_row_share": float(cnt.max() / cnt.sum()), **info, "arms": {}}
    for k, c in corr.items():
        a = {"row_micro_top1": float(c.mean()), "session_macro_top1_ci95": macro_ci(c, sess)}
        if k != "recency":
            a["minus_recency_ci95"] = macro_ci(c - corr["recency"], sess)
        if k in P:
            a["session_macro"] = wmetrics(P[k], yte, 1.0 / cnt[inv])
        res["arms"][k] = a
    (REPO_DATA / "controls-sealed.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    {"split": split, "controls": controls, "parity": parity, "sealed": sealed}[sys.argv[1]]()
