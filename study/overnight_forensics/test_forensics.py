"""Only synthetic records; no private corpus is required by tests."""

from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from study.overnight_forensics import analyze as a
from study.overnight_forensics import extract as e


def ts(value):
    return datetime.fromisoformat(value).timestamp()


def row(i=0, success: bool | None = True, **features):
    start = ts("2026-01-02T22:00:00-06:00") + i * 86400
    return {"id": str(i), "parent": None, "project": "synthetic", "group": str(i),
            "start": start, "end": start + 7200, "activity_end": start + 7200,
            "night": e.night_key(start), "overnight": True, "restart_observable": True,
            "termination_failed": False, "evening_cut_never_resumed": None,
            "features": {"start_hour": 22, "weekday": i % 7, "harness": "hermes", "provider": None, "model": None,
                         "preceding_30": 0, "preceding_60": 0, "is_automated": True,
                         **e.prompt_features("Acceptance: tests pass; checkpoint on branch; resume PR"), **features},
            "labels": {"completed_unattended": success, "stalled": not success if success is not None else None, "needed_owner": None, "restarted_not_resumed": None}}


def test_wilson_known_values_and_empty():
    assert a.wilson(5, 10) == pytest.approx([.2365930905, .7634069095])
    assert a.wilson(0, 0) is None
    lower, upper = a.wilson(0, 10), a.wilson(10, 10)
    assert lower is not None and upper is not None
    assert lower[0] == pytest.approx(0)
    assert upper[1] == pytest.approx(1)
    with pytest.raises(ValueError):
        a.wilson(2, 1)


@pytest.mark.parametrize("count,status", [(0, "insufficient"), (14, "insufficient"), (15, "sufficient")])
def test_minimum_cell(count, status):
    assert a.cell([row(i) for i in range(count)])["status"] == status


def test_unknown_outcomes_are_not_failures():
    result = a.cell([row(0), row(1, None)])
    assert (result["n"], result["unknown"], result["rate"]) == (1, 1, 1)


@pytest.mark.parametrize("start,end,expected", [
    ("2026-01-01T22:00:00-06:00", "2026-01-01T23:00:00-06:00", True),
    ("2026-01-01T22:00:00-06:00", "2026-01-01T22:59:59-06:00", False),
    ("2026-01-02T05:00:00-06:00", "2026-01-02T06:00:00-06:00", False),
    ("2026-01-01T21:00:00-06:00", "2026-01-02T03:00:00-06:00", True),
    ("2026-01-02T02:59:00-06:00", "2026-01-02T03:01:00-06:00", True),
    ("2026-03-08T01:59:00-06:00", "2026-03-08T03:01:00-05:00", True),
    ("2026-11-01T01:00:00-05:00", "2026-11-01T03:00:00-06:00", True),
])
def test_clock_only_overnight_and_dst(start, end, expected):
    assert e.overnight(ts(start), ts(end)) is expected


def test_naive_time_rejected_and_night_week_boundary():
    assert e.timestamp("2026-01-01T01:00:00") is None
    late = ts("2026-01-04T23:00:00-06:00")
    early = ts("2026-01-05T03:00:00-06:00")
    assert e.night_key(late) == e.night_key(early)
    assert a.week_key(e.night_key(late)) == a.week_key(e.night_key(early))


def test_predeclared_labels_and_no_inferred_completion():
    assert e.labels("completed", "clean", 100, 100)["completed_unattended"] is True
    assert e.labels("completed", None, 100, 100)["completed_unattended"] is None
    assert e.labels(None, "normal", 100, 100)["completed_unattended"] is None
    assert e.labels("completed", "killed", 100, 100)["stalled"] is True
    assert e.labels(None, None, 8000, 800)["stalled"] is True
    assert e.labels("completed", "normal", 100, 100, True)["completed_unattended"] is False
    assert e.labels(None, None, None, 100)["stalled"] is None


def test_dispatch_regexes_and_unknown_prompt():
    features = e.prompt_features("make everything super good all night; DoD [ ] test; branch PR checkpoint continue")
    assert all(features[k] for k in ["acceptance", "open_ended", "mentions_branch", "mentions_pr", "mentions_checkpoint", "mentions_resume"])
    assert e.prompt_features(None)["acceptance"] is None
    assert e.prompt_features("")["acceptance"] is False


def test_restart_heuristic_censoring_and_concurrent_starts():
    r0, r1, r2 = row(0), row(1), row(2)
    r1["start"] = r0["end"] + 3600
    r1["features"]["mentions_resume"] = False
    r2["start"] = r1["start"] + 60
    r2["features"]["mentions_resume"] = True
    r1["end"] = r1["start"] + 7200
    r2["end"] = r2["start"] + 7200
    rows = [r0, r1, r2]
    e.relationships(rows, r2["end"] + 12 * 3600)
    assert r0["labels"]["restarted_not_resumed"] is True
    assert r2["features"]["preceding_30"] == 1
    assert r1["group"] == r0["group"]
    e.relationships(rows, r0["end"] + 1)
    assert r0["labels"]["restarted_not_resumed"] is None


def test_simultaneous_starts_not_known_at_dispatch():
    rows = [row(0), row(1)]
    rows[1]["start"] = rows[0]["start"]
    e.relationships(rows, rows[1]["end"] + 99999)
    assert all(r["features"]["preceding_60"] == 0 for r in rows)


def test_time_folds_forward_nights_and_lineage_purge():
    rows = [row(i) for i in range(35)]
    rows[10]["group"] = rows[0]["group"]
    held_out_groups = set()
    for train, test in a.time_blocked_folds(rows):
        assert max(a.week_key(rows[i]["night"]) for i in train) < min(a.week_key(rows[i]["night"]) for i in test)
        assert not ({rows[i]["group"] for i in train} & {rows[i]["group"] for i in test})
        assert not ({rows[i]["night"] for i in train} & {rows[i]["night"] for i in test})
        current = {rows[i]["group"] for i in test}
        assert not (held_out_groups & current)
        held_out_groups |= current
        assert rows[0]["group"] not in current


def test_antipattern_verdict_direction_and_threshold():
    bad = [row(i, False, open_ended=True) for i in range(30)]
    good = [row(i + 30, True, open_ended=False) for i in range(30)]
    feature = lambda r: r["features"]["open_ended"]
    assert a.comparison(bad + good, feature)["verdict"] == "confirmed"
    assert a.comparison(bad[:14] + good, feature)["verdict"] == "insufficient"
    for r in bad + good:
        r["labels"]["completed_unattended"] = not r["labels"]["completed_unattended"]
        r["labels"]["stalled"] = not r["labels"]["stalled"]
    assert a.comparison(bad + good, feature)["verdict"] == "rejected"


def test_no_fabricated_regression_or_hard_gates():
    receipt, rubric = a.analyze([row()], {})
    assert receipt["regression"]["status"] == "not fitted (n < 100)"
    assert rubric["weights"] is None
    assert rubric["supported_hard_gates"] == []
    assert receipt["anti_patterns"]["restart_instead_of_resume"]["verdict"] == "insufficient"
    assert a.regression([row(i) for i in range(100)])["weights"] is None


def test_auc_ties_and_real_fit():
    assert a.auc([0, 1], [0, 1]) == 1
    assert a.auc([0, 1], [.5, .5]) == .5
    assert a.auc([1], [.5]) is None
    x = [[1.0, float(i % 2)] for i in range(100)]
    weights = a.fit_logistic(x, [i % 2 for i in range(100)])
    assert weights[1] > 0
    rows = [row(i, i % 2 == 1, acceptance=i % 2 == 1) for i in range(180)]
    result = a.regression(rows)
    assert result["status"] == "fitted"
    assert 0 <= result["auc_95"][0] <= result["auc"] <= result["auc_95"][1] <= 1
    assert result["weights"]["acceptance"] > 0


def make_db(path, native=False):
    c = sqlite3.connect(path)
    c.execute("CREATE TABLE sessions(id TEXT,source_session_id TEXT,started_at TEXT,ended_at TEXT,agent TEXT,project TEXT,outcome TEXT,termination_status TEXT,parent_session_id TEXT,end_reason TEXT)")
    c.execute("CREATE TABLE messages(id INTEGER,session_id TEXT,role TEXT,content TEXT,timestamp TEXT)")
    start = "2026-01-02T22:00:00-06:00"
    end = "2026-01-03T03:01:00-06:00"
    sid = "session" if native else "profile:session"
    c.execute("INSERT INTO sessions VALUES(?,?,?,?,?,?,?,?,?,?)", (sid, "session", start, end, "hermes", "synthetic", "completed", "clean", None, "cli_close"))
    c.executemany("INSERT INTO messages VALUES(?,?,?,?,?)", [(1, sid, "user", "SYNTHETIC PRIVATE SENTINEL acceptance test", start), (2, sid, "assistant", "done", end)])
    c.commit()
    c.close()


def test_readonly_extraction_dedup_enrichment_and_privacy(tmp_path):
    av, native = tmp_path / "av.db", tmp_path / "native.db"
    make_db(av)
    make_db(native, True)
    before = (av.stat().st_mtime_ns, hashlib.sha256(av.read_bytes()).hexdigest())
    seen, rows, manifest = {}, [], []
    e.extract_sessions(av, "agentsview", seen, rows, manifest)
    e.extract_sessions(native, "hermes", seen, rows, manifest)
    assert len(rows) == 1 and rows[0]["native_exit_enriched"]
    assert rows[0]["labels"]["completed_unattended"] is True
    assert rows[0]["features"]["acceptance"] is True
    safe = {k: v for k, v in rows[0].items() if not k.startswith("_")}
    assert "SYNTHETIC PRIVATE SENTINEL" not in json.dumps(safe)
    assert "synthetic" not in json.dumps(safe)
    assert before == (av.stat().st_mtime_ns, hashlib.sha256(av.read_bytes()).hexdigest())
    conn = e.connect(av)
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("DELETE FROM sessions")
    conn.close()


def test_late_prompt_excluded(tmp_path):
    db = tmp_path / "av.db"
    make_db(db)
    c = sqlite3.connect(db)
    c.execute("UPDATE messages SET timestamp='2026-01-02T22:02:00-06:00' WHERE role='user'")
    c.commit(); c.close()
    rows = []
    e.extract_sessions(db, "agentsview", {}, rows, [])
    assert rows[0]["features"]["acceptance"] is None


def test_owner_event_exact_join_and_time_window(tmp_path):
    db = tmp_path / "board.db"
    c = sqlite3.connect(db)
    c.executescript("CREATE TABLE tasks(id TEXT,session_id TEXT); CREATE TABLE task_events(task_id TEXT,kind TEXT,created_at INTEGER);")
    r = row()
    r.update(_harness="hermes", _aliases={"session"})
    c.execute("INSERT INTO tasks VALUES('task','session')")
    c.execute("INSERT INTO task_events VALUES('task','blocked',?)", (r["start"] - 1,))
    c.commit()
    e.enrich_blocked(db, [r], [])
    assert r["labels"]["needed_owner"] is None
    c.execute("INSERT INTO task_events VALUES('task','blocked',?)", (r["start"] + 1,))
    c.commit(); c.close()
    e.enrich_blocked(db, [r], [])
    assert r["labels"]["needed_owner"] is True
    assert a.observed_target(r) == 0


def test_private_permissions_and_repository_refusal(tmp_path):
    out = e.private_directory(tmp_path / "private")
    e.private_write(out / "receipt.json", "{}")
    assert out.stat().st_mode & 0o777 == 0o700
    assert (out / "receipt.json").stat().st_mode & 0o777 == 0o600
    repo = tmp_path / "repo"
    repo.mkdir(); (repo / ".git").mkdir()
    with pytest.raises(ValueError):
        e.private_directory(repo / "data")
    alias = tmp_path / "repository-alias"
    alias.symlink_to(repo, target_is_directory=True)
    with pytest.raises(ValueError):
        e.private_directory(alias / "data")
    (out / "link").symlink_to(out / "receipt.json")
    with pytest.raises(ValueError):
        e.private_write(out / "link", "oops")


def test_real_cli_synthetic_export_and_analyze(tmp_path):
    db = tmp_path / "av.db"
    make_db(db)
    out = tmp_path / "export"
    root = Path(__file__).resolve().parents[2]
    extract = subprocess.run([sys.executable, str(root / "study/overnight_forensics/extract.py"),
                              "--agentsview", str(db), "--hermes-root", str(tmp_path / "empty"),
                              "--output", str(out)], capture_output=True, text=True, check=True)
    assert json.loads(extract.stdout)["overnight"] == 1
    analysis = subprocess.run([sys.executable, str(root / "study/overnight_forensics/analyze.py"),
                               "--input-dir", str(out)], capture_output=True, text=True, check=True)
    assert json.loads(analysis.stdout)["counts"]["labeled"] == 1
    for file in out.iterdir():
        assert "SYNTHETIC PRIVATE SENTINEL" not in file.read_text()
        assert file.stat().st_mode & 0o777 == 0o600
    # A changed private dataset must not silently reuse a frozen receipt.
    with (out / "runs.jsonl").open("a") as f:
        f.write("{}\n")
    failure = subprocess.run([sys.executable, str(root / "study/overnight_forensics/analyze.py"),
                              "--input-dir", str(out)], capture_output=True, text=True)
    assert failure.returncode != 0
    assert "hash mismatch" in failure.stderr


def test_owner_journal_uses_exact_run_not_current_task_pointer(tmp_path):
    db = tmp_path / "board.db"
    c = sqlite3.connect(db)
    c.executescript("CREATE TABLE tasks(id TEXT,session_id TEXT); CREATE TABLE task_events(task_id TEXT,kind TEXT,created_at INTEGER,run_id INTEGER,payload TEXT);")
    r = row()
    r.update(_harness="hermes", _aliases={"earlier-session"})
    c.execute("INSERT INTO tasks VALUES('task','newer-session')")
    c.execute("INSERT INTO task_events VALUES('task','owner_admitted',?,1,?)", (r["start"], json.dumps({"session_id": "earlier-session"})))
    c.execute("INSERT INTO task_events VALUES('task','blocked',?,1,NULL)", (r["start"] + 1,))
    c.commit(); c.close()
    e.enrich_blocked(db, [r], [])
    assert r["labels"]["needed_owner"] is True


def test_parent_chain_and_evening_cut_followup(tmp_path):
    first, later = row(0, False), row(1, True)
    first["end"] = first["start"] + 60  # Still in the evening clock window.
    first["termination_failed"] = True
    later["project"] = "separate-project"
    later["parent"] = first["id"]
    e.relationships([first, later], later["end"] + 13 * 3600)
    assert first["group"] == later["group"]
    assert first["evening_cut_never_resumed"] is True
