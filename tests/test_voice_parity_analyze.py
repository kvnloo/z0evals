"""Unit tests for the voice-parity scorer's acoustic primitives and gate semantics."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "studies/voice-omp-parity-v0/harness"))
import analyze as A  # noqa: E402


def windows(spec):
    """spec: list of (start_ms, end_ms, rms) runs -> 50 ms window list stamped at window end."""
    out = []
    for s, e, r in spec:
        t = s + 50
        while t <= e:
            out.append((float(t), r))
            t += 50
    return out


def test_first_audible_and_quiet_onset():
    lv = windows([(0, 1000, 0.0), (1000, 2000, 0.05), (2000, 3000, 0.0)])
    assert A.first_audible_after(lv, 500) == 1050
    # sustained quiet starts at the first quiet window's start (2000)
    assert A.quiet_onset(lv, 1500) == 2000
    assert A.segments(lv) == [[1000.0, 2000.0]]


def test_short_pause_is_not_a_false_interruption_gap():
    lv = windows([(0, 1000, 0.05), (1000, 1400, 0.0), (1400, 3000, 0.05), (3000, 4000, 0.0)])
    # a 400 ms pause does not reach the 700 ms false-interruption gap; the 1 s tail does
    assert A.quiet_onset(lv, 500, A.FALSE_INTERRUPT_GAP_MS) == 3000


def test_missing_data_is_incomplete_not_pass():
    base = {
        "runs": 1, "valid_runs": 1, "direct_first_audible": {"p50": None, "p95": None},
        "delegation_ack_first_audible": {"p50": None}, "delegation_used_by_scenario": {"work_status": "0/0", "repo_question": "0/0"},
        "repo_correct": "0/0", "barge_to_silence": {"p50": None, "p95": None, "not_stopped": 0}, "barge_applicable": "0/0",
        "barge_answer_correct": "0/0", "stale_resume_runs": 0, "false_interruptions": 0, "unwanted_speech_runs": 0,
        "repeat_runs": 0, "filler_per_delegation_run": None,
    }
    v = A.gates({"omp-live": dict(base), "z0live-realtime": dict(base)})["z0live-realtime"]
    assert v["verdict"] == "INCOMPLETE" and not v["failing"]


def test_repeats_detects_near_duplicate_turns():
    texts = [(1, "Canberra is the capital of Australia."), (2, "Canberra is the capital of Australia!"), (3, "Something else entirely here.")]
    assert A.repeats(texts) == 1


def test_keyword_hit_tolerates_split_asr_words():
    assert A.keyword_hit("Can berra.", ["canberra"])
    assert A.keyword_hit("It's in core dot py", ["core.py", "core dot py"])
    assert not A.keyword_hit("Sydney.", ["canberra"])


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
