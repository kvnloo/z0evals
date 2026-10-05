import importlib.util
from pathlib import Path


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "certify_z0live",
    ROOT / "scripts" / "certify_z0live.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


IDENTITY = {
    "actor_id": "fake",
    "provider": "local",
    "model": "fake",
    "model_revision": "abc1234",
    "runtime_backend": "cpu",
    "quantization": "none",
    "host_fingerprint": "host",
    "hardware_class": "test",
    "harness": "omp",
    "harness_revision": "abc1234",
    "adapter_revision": "def5678",
}


def replay(passed=True):
    return {
        "schema": "z0live.replay_result.v1",
        "revision": "core-v1",
        "fixture_sha256": "a" * 64,
        "passed": passed,
        "cases": [
            {"fixture_id": "a", "passed": passed},
            {"fixture_id": "b", "passed": passed},
        ],
    }


def test_replay_only_is_partial_not_keep():
    out = MODULE.certify(replay(), IDENTITY)
    assert out["decision"] == "PARTIAL"
    assert out["contract_replay"]["cases_passed"] == 2


def test_failed_replay_discards():
    out = MODULE.certify(replay(False), IDENTITY)
    assert out["decision"] == "DISCARD"


def test_speculative_mutation_discards_even_with_replay_pass():
    out = MODULE.certify(
        replay(),
        IDENTITY,
        speculation={
            "speculative_mutations": 1,
            "p50_useful_gain_ms": 90,
        },
    )
    assert out["decision"] == "DISCARD"
