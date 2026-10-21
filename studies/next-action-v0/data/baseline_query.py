import sqlite3, json, os, subprocess
db = sqlite3.connect(f"file:{os.path.expanduser('~/.local/state/workspace-copilot/workspace.db')}?mode=ro", uri=True)
q = lambda s: db.execute(s).fetchall()
lo, hi, n = q("select min(ts),max(ts),count(*) from shadow_predictions")[0]
matched = q("select count(*) from shadow_predictions where matched_at is not null")[0][0]
top1 = q("select avg(ranked=1) from shadow_predictions where matched_at is not null")[0][0]
top3 = q("select avg(ranked between 1 and 3) from shadow_predictions where matched_at is not null")[0][0]
noop = q("select avg(actual_family='noop') from shadow_predictions where matched_at is not null")[0][0]
buckets = []
for lo_b, hi_b in [(0,0.35),(0.35,0.6),(0.6,0.82),(0.82,1.01)]:
    r = q(f"select count(*), avg(ranked=1) from shadow_predictions where matched_at is not null and confidence>={lo_b} and confidence<{hi_b}")[0]
    buckets.append({"confidence_lo": lo_b, "confidence_hi": min(hi_b,1.0), "n": r[0], "top1_hit_rate": round(r[1] or 0,3)})
fam = dict(q("select actual_family,count(*) from shadow_predictions group by 1"))
commits = q("select count(*) from shadow_predictions where receipt_json like '%\"committed\": true%' or receipt_json like '%\"committed\":true%'")[0][0]
shown = q("select count(*) from shadow_predictions where receipt_json like '%\"shown\"%'")[0][0]
lat = q("select avg(latency_ms) from shadow_predictions")[0][0]
lats = sorted(r[0] for r in q("select latency_ms from shadow_predictions"))
pct = lambda p: round(lats[int(p*(len(lats)-1))],1)
out = {
  "schema": "next-action-v0.baseline.v1",
  "source": "workspace-copilot sqlite (read-only), os.next_context.v0 shadow_predictions",
  "window_utc": [subprocess.check_output(["date","-u","-d",f"@{int(lo)}","+%FT%TZ"]).decode().strip(), subprocess.check_output(["date","-u","-d",f"@{int(hi)}","+%FT%TZ"]).decode().strip()],
  "predictions": n, "matched": matched,
  "top1_hit_rate_60s": round(top1,3), "top3_hit_rate_60s": round(top3,3), "noop_rate_60s": round(noop,3),
  "actual_family_counts": fam,
  "calibration_by_confidence": buckets,
  "surfaced_ready_tier": shown, "explicit_commits": commits,
  "decisions_rows": q("select count(*) from decisions")[0][0],
  "suggestions_pending": q("select count(*) from suggestions where status='pending'")[0][0],
  "suggestions_total": q("select count(*) from suggestions")[0][0],
  "predict_latency_ms": {"mean": round(lat,1), "p50": pct(.5), "p90": pct(.9), "p99": pct(.99)},
}
rr = json.load(open(os.path.expanduser("~/.local/state/workspace-copilot/rerank-v1.json")))
h = rr.get("holdout") or rr.get("metrics", {}).get("holdout")
out["rerank_v1_holdout"] = h
out["privacy"] = "aggregates only; no app names, titles, targets, paths or timestamps finer than the window"
print(json.dumps(out, indent=2))
