#!/usr/bin/env python3
"""Score voice-eval runs. Pure functions over each run dir (meta.json, events.jsonl, levels.jsonl).

Every timing metric is computed from output-audio RMS windows (50 ms, threshold 0.015 RMS),
never from transcript text. Transcripts (provider ASR of the assistant's own audio) are used
only for content checks (keywords, repeats, filler, stale speech).

python harness/analyze.py --runs <run-root> --out <results.json> --md <scoreboard.md>
"""
import argparse
import json
import math
import re
import statistics
from difflib import SequenceMatcher
from pathlib import Path

THR = 0.015
WIN = 50.0
QUIET_SUSTAIN_MS = 300
FALSE_INTERRUPT_GAP_MS = 700
SEGMENT_GAP_MS = 400
FILLER = re.compile(
    r"\b(let me (check|see|look|find)|one (moment|sec(ond)?)|hold on|hang on|give me a (sec(ond)?|moment)|"
    r"still (working|checking|looking)|no update|working on (it|that)|bear with me|stand by|i'll get back|"
    r"just a (moment|sec(ond)?)|checking (on )?(that|now))\b",
    re.I,
)
DIRECT_POOL = [("greeting", "q1"), ("quick_fact", "q1"), ("rapid_followup", "q1"), ("rapid_followup", "q2"), ("closing_silence", "q1"), ("noise_during_answer", "q1"), ("barge_in", "q1")]
DELEGATION = ["work_status", "repo_question"]
WORK_TOOL_EXCLUDE = {"get_context", "summarize"}


def pct(values, p):
    v = sorted(x for x in values if x is not None and not math.isnan(x))
    if not v:
        return None
    k = (len(v) - 1) * p / 100
    f, c = math.floor(k), math.ceil(k)
    return round(v[f] + (v[c] - v[f]) * (k - f), 1)


def load_run(d: Path):
    meta = json.loads((d / "meta.json").read_text())
    events = [json.loads(line) for line in (d / "events.jsonl").read_text().splitlines() if line.strip()] if (d / "events.jsonl").exists() else []
    levels = []
    if (d / "levels.jsonl").exists():
        for line in (d / "levels.jsonl").read_text().splitlines():
            if line.strip():
                t, r = line.split()
                levels.append((float(t), float(r)))
    return meta, events, levels


def marks_of(meta, events):
    marks = {}
    res = (meta.get("result") or {}).get("marks") or {}
    for k, v in res.items():
        if isinstance(v, dict) and "start" in v:
            marks[k] = {"start": v["start"], "end": v.get("end", v["start"])}
    for e in events:  # async clips (noise) only appear as mark events
        if e.get("kind") == "mark":
            t = e.get("t_audio", e.get("t_end") if e.get("phase") == "end" else e["t"])
            m = marks.setdefault(e["mark"], {})
            if e["phase"] == "start":
                m.setdefault("start", t)
            else:
                m.setdefault("end", e.get("t_end", t))
    return marks


def audible(levels):
    return [t for t, r in levels if r >= THR]


def first_audible_after(levels, t0):
    for t, r in levels:
        if t > t0 and r >= THR:
            return t
    return None


def segments(levels):
    segs = []
    for t, r in levels:
        if r < THR:
            continue
        if segs and t - segs[-1][1] <= SEGMENT_GAP_MS:
            segs[-1][1] = t
        else:
            segs.append([t - WIN, t])
    return segs


def quiet_onset(levels, t0, sustain=QUIET_SUSTAIN_MS):
    """Start time of the first window after t0 that begins >= sustain ms of continuous quiet."""
    run_start = None
    for t, r in levels:
        if t <= t0:
            continue
        if r < THR:
            if run_start is None:
                run_start = t - WIN
            if t - run_start >= sustain:
                return run_start
        else:
            run_start = None
    return None


def assistant_texts(arm, events):
    """(t, text) per completed assistant turn, from the provider's own transcript of its audio."""
    out = []
    for e in events:
        if arm.startswith("omp"):
            if e.get("kind") == "wire" and e.get("channel") == "sideband" and e.get("type") == "turn.done" and e.get("turn", {}).get("role") == "assistant":
                out.append((e["t"], e["turn"]["transcript"].strip()))
        elif e.get("kind") == "wire" and e.get("type") == "response.output_audio_transcript.done":
            out.append((e["t"], (e.get("text") or "").strip()))
    return out


def user_texts(arm, events):
    out = []
    for e in events:
        if arm.startswith("omp"):
            if e.get("kind") == "wire" and e.get("channel") == "sideband" and e.get("type") == "turn.done" and e.get("turn", {}).get("role") == "user":
                out.append((e["t"], e["turn"]["transcript"].strip()))
        elif e.get("kind") == "wire" and e.get("type") == "conversation.item.input_audio_transcription.completed":
            out.append((e["t"], (e.get("text") or "").strip()))
    return out


def delegation_info(arm, events):
    if arm.startswith("omp"):
        created = [e for e in events if e.get("kind") == "wire" and e.get("channel") == "sideband" and e.get("type") == "delegation.created"]
        done = [e["t"] for e in events if e.get("kind") == "agent" and e.get("type") == "agent_end" and e.get("terminal")]
        return {"used": bool(created), "count": len(created), "tools": [], "work_done_t": done[-1] if done else None}
    calls = [e for e in events if e.get("kind") == "tool_call" and e.get("name") not in WORK_TOOL_EXCLUDE]
    done = [e["t"] for e in events if e.get("kind") == "inbox" and e.get("event") in ("result", "clarification", "error", "failed", "cancelled", "blocked") and e.get("same_session")]
    sync_done = [e["t"] for e in events if e.get("kind") == "tool_result" and e.get("name") not in WORK_TOOL_EXCLUDE and '"turn_id"' not in e.get("result", "")]
    t = done[-1] if done else (sync_done[-1] if sync_done else None)
    return {"used": bool(calls), "count": len(calls), "tools": sorted({e["name"] for e in calls}), "work_done_t": t}


def norm(s):
    return re.sub(r"[^a-z0-9 ]+", "", s.lower()).strip()


def repeats(texts):
    n = 0
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            a, b = norm(texts[i][1]), norm(texts[j][1])
            if len(a) >= 20 and len(b) >= 20 and SequenceMatcher(None, a, b).ratio() >= 0.9:
                n += 1
    return n


def score_run(d: Path, spec):
    meta, events, levels = load_run(d)
    arm, sid = meta["arm"], meta["scenario"]
    sc = next(s for s in spec["scenarios"] if s["id"] == sid)
    checks = sc.get("checks", {})
    m = marks_of(meta, events)
    row = {"arm": arm, "scenario": sid, "run": d.name, "error": meta.get("error") or meta.get("terminal_error"), "connect_ms": meta.get("connect_ms")}
    if arm.startswith("z0live"):
        mint = next((e.get("ms") for e in events if e.get("msg") == "minted"), None)
        row["ready_ms"] = round((mint or 0) + (meta.get("connect_ms") or 0), 1) if meta.get("connect_ms") else None
        row["jitter_buffer_ms"] = (meta.get("webrtc_stats") or {}).get("jitter_buffer_mean_ms")
    else:
        row["ready_ms"] = meta.get("connect_ms")
    if row["error"] or not levels:
        row["valid"] = False
        return row
    row["valid"] = True
    texts = assistant_texts(arm, events)
    row["assistant_turns"] = len(texts)
    row["repeats"] = repeats(texts)
    lat = {}
    stalls = meta.get("stalls") or []
    row["stall_invalidated"] = []
    for mk in checks.get("direct_turns", []) + checks.get("ack_turns", []):
        if mk in m and "end" in m[mk]:
            fa = first_audible_after(levels, m[mk]["end"])
            lo, hi = m[mk]["start"], (fa if fa else m[mk]["end"])
            # Harness validity rule: OMP levels are stamped on the JS thread, so a measured
            # interval overlapping an event-loop stall (> 50 ms) is excluded, not scored.
            if any(s0 < hi and s0 + lag > lo for s0, lag in stalls):
                row["stall_invalidated"].append(mk)
                continue
            lat[mk] = round(fa - m[mk]["end"], 1) if fa else None
            # talk-over: assistant audible while this user utterance was still being spoken
            row.setdefault("talk_over_ms", 0)
            row["talk_over_ms"] += sum(WIN for t, r in levels if m[mk]["start"] + 300 < t <= m[mk]["end"] and r >= THR)
    row["first_audible_ms"] = lat
    kw = checks.get("answer_keywords", {})
    for mk, words in kw.items():
        if mk in m and "end" in m[mk]:
            nxt = sorted(v["start"] for k, v in m.items() if "start" in v and v["start"] > m[mk]["end"])
            upto = nxt[0] if nxt else math.inf
            said = " ".join(t for ts, t in texts if m[mk]["end"] < ts <= upto + 15000).lower()
            squashed = said.replace(" ", "")  # provider ASR may split words ("Can berra")
            row.setdefault("correct", {})[mk] = any(w in said or w.replace(" ", "") in squashed for w in words)
    if checks.get("expect_delegation") or checks.get("expect_no_delegation"):
        info = delegation_info(arm, events)
        row["delegation"] = info
        q = m.get("q1", {})
        if info["work_done_t"] and q.get("end"):
            fa = first_audible_after(levels, info["work_done_t"])
            row["result_audible_ms"] = round(fa - q["end"], 1) if fa else None
        row["filler"] = sum(len(FILLER.findall(t)) for _, t in texts)
        if q.get("end"):
            segs = [s for s in segments(levels) if s[0] >= q["end"]]
            gaps = [b[0] - a[1] for a, b in zip(segs, segs[1:])]
            row["longest_dead_air_ms"] = round(max(gaps), 1) if gaps else None
    if checks.get("barge_mark") and checks["barge_mark"] in m:
        b = m[checks["barge_mark"]]
        speaking = any(b["start"] - 200 <= t <= b["start"] + 50 and r >= THR for t, r in levels)
        row["barge_applicable"] = speaking
        if speaking:
            q = quiet_onset(levels, b["start"])
            row["barge_to_silence_ms"] = round(max(0.0, q - b["start"]), 1) if q is not None and q <= b["end"] + 1000 else None
            row["barge_stopped"] = row["barge_to_silence_ms"] is not None
        stale = [t for ts, t in texts if ts > b["end"] and any(w in t.lower() for w in checks.get("stale_keywords", []))]
        row["stale_resume"] = len(stale)
    if checks.get("noise_mark") and checks["noise_mark"] in m:
        n = m[checks["noise_mark"]]
        speaking = any(n["start"] - 150 <= t <= n["start"] + 50 and r >= THR for t, r in levels)
        row["noise_applicable"] = speaking
        if speaking:
            q = quiet_onset(levels, n["start"], FALSE_INTERRUPT_GAP_MS)
            row["false_interruption"] = q is not None and q <= n["end"] + 500
            if arm.startswith("z0live"):
                row["vad_triggered_by_noise"] = any(e.get("type") == "input_audio_buffer.speech_started" and n["start"] - 100 <= e["t"] <= n["end"] + 1000 for e in events)
            else:
                row["vad_triggered_by_noise"] = any(e.get("channel") == "sideband" and e.get("type") in ("turn.created", "input_transcript.added") and (e.get("turn", {}).get("role", "user") == "user") and n["start"] - 100 <= e["t"] <= n["end"] + 1000 for e in events)
            row["noise_user_turns"] = sum(1 for ts, t in user_texts(arm, events) if n["start"] <= ts <= n["end"] + 4000 and t)
    if checks.get("silence_watch_mark") and checks["silence_watch_mark"] in m:
        w = m[checks["silence_watch_mark"]]
        row["unwanted_speech_ms"] = sum(WIN for t, r in levels if w["start"] < t <= w.get("end", w["start"] + 20000) and r >= THR)
        q = m.get("q1", {})
        row["reply_segments_after_close"] = len([s for s in segments(levels) if q.get("end") and s[0] >= q["end"]])
    return row


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.mean(xs), 2) if xs else None


def aggregate(rows):
    arms = sorted({r["arm"] for r in rows})
    agg = {}
    for arm in arms:
        rs = [r for r in rows if r["arm"] == arm]
        ok = [r for r in rs if r.get("valid")]
        direct = [r["first_audible_ms"].get(mk) for r in ok for (s, mk) in DIRECT_POOL if r["scenario"] == s and mk in r.get("first_audible_ms", {})]
        direct_missing = sum(1 for x in direct if x is None)
        acks = [r["first_audible_ms"].get("q1") for r in ok if r["scenario"] in DELEGATION]
        dele = [r for r in ok if r["scenario"] in DELEGATION]
        barge = [r for r in ok if r["scenario"] == "barge_in"]
        noise = [r for r in ok if r["scenario"] == "noise_during_answer"]
        close = [r for r in ok if r["scenario"] == "closing_silence"]
        per_scen = {}
        for s in sorted({r["scenario"] for r in rs}):
            sr = [r for r in ok if r["scenario"] == s]
            fa = [v for r in sr for v in r.get("first_audible_ms", {}).values()]
            corr = [v for r in sr for v in r.get("correct", {}).values()]
            per_scen[s] = {"runs": len([r for r in rs if r["scenario"] == s]), "valid": len(sr), "first_audible_p50": pct(fa, 50), "first_audible_p95": pct(fa, 95), "correct": f"{sum(corr)}/{len(corr)}" if corr else None}
        agg[arm] = {
            "runs": len(rs),
            "valid_runs": len(ok),
            "errors": [r["error"] for r in rs if r.get("error")],
            "ready_ms_p50": pct([r.get("ready_ms") for r in ok], 50),
            "direct_first_audible": {"n": len(direct), "missing": direct_missing, "p50": pct(direct, 50), "p95": pct(direct, 95), "max": pct(direct, 100)},
            "delegation_ack_first_audible": {"n": len(acks), "p50": pct(acks, 50), "p95": pct(acks, 95)},
            "delegation_used": f"{sum(1 for r in dele if r.get('delegation', {}).get('used'))}/{len(dele)}",
            "delegation_used_by_scenario": {s: f"{sum(1 for r in dele if r['scenario'] == s and r.get('delegation', {}).get('used'))}/{sum(1 for r in dele if r['scenario'] == s)}" for s in DELEGATION},
            "delegation_tools": sorted({t for r in dele for t in r.get("delegation", {}).get("tools", [])}),
            "result_audible_ms_p50": pct([r.get("result_audible_ms") for r in dele], 50),
            "result_delivered": f"{sum(1 for r in dele if r.get('result_audible_ms') is not None)}/{len(dele)}",
            "repo_correct": f"{sum(1 for r in dele if r['scenario'] == 'repo_question' and r.get('correct', {}).get('q1'))}/{sum(1 for r in dele if r['scenario'] == 'repo_question')}",
            "filler_per_delegation_run": mean([r.get("filler") for r in dele]),
            "longest_dead_air_ms_p50": pct([r.get("longest_dead_air_ms") for r in dele], 50),
            "barge_applicable": f"{sum(1 for r in barge if r.get('barge_applicable'))}/{len(barge)}",
            "barge_to_silence": {"p50": pct([r.get("barge_to_silence_ms") for r in barge if r.get("barge_applicable")], 50), "p95": pct([r.get("barge_to_silence_ms") for r in barge if r.get("barge_applicable")], 95), "not_stopped": sum(1 for r in barge if r.get("barge_applicable") and not r.get("barge_stopped"))},
            "barge_answer_correct": f"{sum(1 for r in barge if r.get('correct', {}).get('barge'))}/{len(barge)}",
            "stale_resume_runs": sum(1 for r in barge if r.get("stale_resume")),
            "noise_applicable": f"{sum(1 for r in noise if r.get('noise_applicable'))}/{len(noise)}",
            "false_interruptions": sum(1 for r in noise if r.get("false_interruption")),
            "noise_vad_triggers": sum(1 for r in noise if r.get("vad_triggered_by_noise")),
            "noise_transcribed_as_user": sum(1 for r in noise if r.get("noise_user_turns")),
            "delegated_on_direct_scenarios": sum(1 for r in ok if r["scenario"] not in DELEGATION and r.get("delegation", {}).get("used")),
            "unwanted_speech_runs": sum(1 for r in close if (r.get("unwanted_speech_ms") or 0) > 0),
            "repeat_runs": sum(1 for r in ok if r.get("repeats")),
            "stall_invalidated_measurements": sum(len(r.get("stall_invalidated", [])) for r in ok),
            "talk_over_runs": sum(1 for r in ok if (r.get("talk_over_ms") or 0) > 0),
            "per_scenario": per_scen,
        }
    return agg


def gates(agg, control="omp-live"):
    """Pre-registered gates (README 'Pre-registered thresholds'); evaluated for every non-control arm."""
    out = {}
    c = agg.get(control)
    if not c:
        return out
    frac = lambda s: tuple(int(x) for x in s.split("/")) if s else (0, 0)
    for arm, a in agg.items():
        if arm == control:
            continue
        g = {}

        def cmp(name, x, y, tol):
            g[name] = {"value": x, "control": y, "tolerance": tol, "pass": None if x is None or y is None else x <= y + tol}

        cmp("G1_direct_first_audible_p50", a["direct_first_audible"]["p50"], c["direct_first_audible"]["p50"], 150)
        cmp("G2_direct_first_audible_p95", a["direct_first_audible"]["p95"], c["direct_first_audible"]["p95"], 300)
        cmp("G3a_delegation_ack_p50", a["delegation_ack_first_audible"]["p50"], c["delegation_ack_first_audible"]["p50"], 150)
        per = a["delegation_used_by_scenario"]
        g["G3b_delegation_used_ge_4of5_each"] = {"value": per, "pass": None if any(frac(v)[1] == 0 for v in per.values()) else all(frac(v)[0] >= 4 for v in per.values())}
        g["G3c_repo_correct_ge_control"] = {"value": a["repo_correct"], "control": c["repo_correct"], "pass": frac(a["repo_correct"])[0] >= frac(c["repo_correct"])[0]}
        cmp("G4a_barge_to_silence_p50", a["barge_to_silence"]["p50"], c["barge_to_silence"]["p50"], 100)
        bmax = a["barge_to_silence"]["p95"]
        g["G4b_barge_stops_within_1000ms"] = {"value": {"not_stopped": a["barge_to_silence"]["not_stopped"], "p95": bmax}, "pass": None if frac(a["barge_applicable"])[0] == 0 else (a["barge_to_silence"]["not_stopped"] == 0 and bmax is not None and bmax <= 1000)}
        g["G4c_barge_answer_ge_4of5"] = {"value": a["barge_answer_correct"], "pass": None if frac(a["barge_answer_correct"])[1] == 0 else frac(a["barge_answer_correct"])[0] >= 4}
        g["G4d_no_stale_resume"] = {"value": a["stale_resume_runs"], "pass": a["stale_resume_runs"] == 0}
        g["G5_zero_false_interruptions"] = {"value": a["false_interruptions"], "control": c["false_interruptions"], "pass": a["false_interruptions"] == 0}
        g["G6_zero_unwanted_speech_after_close"] = {"value": a["unwanted_speech_runs"], "control": c["unwanted_speech_runs"], "pass": a["unwanted_speech_runs"] == 0}
        g["G7_zero_repeated_speech"] = {"value": a["repeat_runs"], "control": c["repeat_runs"], "pass": a["repeat_runs"] == 0}
        f, fc = a["filler_per_delegation_run"], c["filler_per_delegation_run"]
        g["G8_filler_le_control_plus_1"] = {"value": f, "control": fc, "pass": None if f is None or fc is None else f <= fc + 1}
        g["G9_no_extra_run_failures"] = {"value": a["runs"] - a["valid_runs"], "control": c["runs"] - c["valid_runs"], "pass": (a["runs"] - a["valid_runs"]) <= (c["runs"] - c["valid_runs"])}
        failing = [k for k, v in g.items() if v["pass"] is False]
        unknown = [k for k, v in g.items() if v["pass"] is None]
        out[arm] = {"gates": g, "verdict": "PASS" if not failing and not unknown else ("FAIL" if failing else "INCOMPLETE"), "failing": failing, "unknown": unknown}
    return out


def fmt(x, unit=" ms"):
    return "–" if x is None else f"{x:,.0f}{unit}"


def scoreboard(agg, verdicts, meta):
    arms = list(agg)
    lines = [f"# Voice parity scoreboard — run `{meta['run_id']}`", "", f"Pre-registered gates: `studies/voice-omp-parity-v0/README.md`. Control arm: `omp-live`. Reps per scenario per arm: {meta.get('reps')}.", ""]
    head = "| Metric | " + " | ".join(arms) + " |"
    lines += [head, "|---|" + "---:|" * len(arms)]
    rows = [
        ("Valid runs", lambda a: f"{a['valid_runs']}/{a['runs']}"),
        ("Session ready (p50)", lambda a: fmt(a["ready_ms_p50"])),
        ("EOS → first audible, direct turns p50", lambda a: fmt(a["direct_first_audible"]["p50"])),
        ("EOS → first audible, direct turns p95", lambda a: fmt(a["direct_first_audible"]["p95"])),
        ("Direct turns with no audible reply", lambda a: f"{a['direct_first_audible']['missing']}/{a['direct_first_audible']['n']}"),
        ("EOS → first audible, delegation turns p50", lambda a: fmt(a["delegation_ack_first_audible"]["p50"])),
        ("Delegation used (work / repo)", lambda a: " / ".join(a["delegation_used_by_scenario"].values())),
        ("Result spoken (delegation runs)", lambda a: a["result_delivered"]),
        ("EOS → result audible p50", lambda a: fmt(a["result_audible_ms_p50"])),
        ("Repo answer correct (`core.py`)", lambda a: a["repo_correct"]),
        ("Filler phrases / delegation run", lambda a: "–" if a["filler_per_delegation_run"] is None else f"{a['filler_per_delegation_run']}"),
        ("Barge-in → silence p50", lambda a: fmt(a["barge_to_silence"]["p50"])),
        ("Barge-in → silence p95", lambda a: fmt(a["barge_to_silence"]["p95"])),
        ("Barge not stopped", lambda a: str(a["barge_to_silence"]["not_stopped"])),
        ("Barge follow-up answered (`Central`)", lambda a: a["barge_answer_correct"]),
        ("Stale resume after barge (runs)", lambda a: str(a["stale_resume_runs"])),
        ("False interruptions from noise", lambda a: f"{a['false_interruptions']}/{a['noise_applicable'].split('/')[0]}"),
        ("Noise transcribed as a user turn", lambda a: str(a["noise_transcribed_as_user"])),
        ("Unwanted speech in 20 s after closing", lambda a: str(a["unwanted_speech_runs"])),
        ("Runs with repeated speech", lambda a: str(a["repeat_runs"])),
        ("Delegated on a direct question (runs)", lambda a: str(a["delegated_on_direct_scenarios"])),
    ]
    for name, f in rows:
        lines.append(f"| {name} | " + " | ".join(f(agg[a]) for a in arms) + " |")
    lines.append("")
    for arm, v in verdicts.items():
        lines.append(f"**{arm} vs omp-live: {v['verdict']}** — failing: {', '.join(v['failing']) or 'none'}; undetermined: {', '.join(v['unknown']) or 'none'}")
    lines.append("")
    lines.append("Per-scenario first-audible p50 (ms):")
    lines.append("")
    scen = sorted({s for a in agg.values() for s in a["per_scenario"]})
    lines += ["| Scenario | " + " | ".join(arms) + " |", "|---|" + "---:|" * len(arms)]
    for s in scen:
        lines.append(f"| {s} | " + " | ".join(fmt(agg[a]["per_scenario"].get(s, {}).get("first_audible_p50")) for a in arms) + " |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--scenarios", default=str(Path(__file__).resolve().parents[1] / "scenarios.json"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--md", required=True)
    ap.add_argument("--private-rows")
    a = ap.parse_args()
    spec = json.loads(Path(a.scenarios).read_text())
    root = Path(a.runs)
    run_meta = json.loads((root / "run.json").read_text()) if (root / "run.json").exists() else {"run_id": root.name}
    rows = [score_run(d, spec) for d in sorted(p for p in root.iterdir() if (p / "meta.json").exists())]
    agg = aggregate(rows)
    verdicts = gates(agg)
    public_rows = [{k: v for k, v in r.items() if k not in ("error",)} | {"error": bool(r.get("error"))} for r in rows]
    Path(a.out).write_text(json.dumps({"schema": "z0eval.voice_parity_result.v1", "run": run_meta, "aggregate": agg, "verdicts": verdicts, "runs": public_rows}, indent=2) + "\n")
    Path(a.md).write_text(scoreboard(agg, verdicts, run_meta | {"reps": run_meta.get("reps")}))
    if a.private_rows:
        Path(a.private_rows).write_text(json.dumps(rows, indent=2))
    print(Path(a.md).read_text())


if __name__ == "__main__":
    main()
