"""The `setup:` block in zer0.repo.yaml stays consistent with itself and with CI.

The z0 onboarder reads that block to set up a fresh clone, so its python tier
must follow the same steps, in the same order, as .github/workflows/ci.yml.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]

# Facts a `when:` may name: the z0 host profile (kvnloo/z0 schemas/host-profile.schema.json;
# network keys are registry/onboarding.yaml `network_probes`). z0 treats a missing fact
# as false, so a misspelt fact silently disables a tier. kvnloo/z0 runs the full check:
# `scripts/repo-setup-check zer0.repo.yaml`.
Z0_FACTS = {
    "network": {"github", "pypi", "npmjs", "fonts_google", "pytorch", "bun", "k2_fsa"},
    "toolchains": {"node", "npm", "python3", "git", "uv", "bun"},
}
# z0 plans the registry's step and this one as the same step only when the ids match.
Z0_REGISTRY_IDS = re.compile(r"^z0evals\.(t0\.[a-z_]+|venv|deps|t1\.[a-z_]+|web\.[a-z_]+)$")


def load_setup() -> dict:
    return yaml.safe_load((REPO / "zer0.repo.yaml").read_text(encoding="utf-8"))["setup"]


def ci_python_runs() -> list[str]:
    ci = yaml.safe_load((REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
    runs = [s["run"] for s in ci["jobs"]["validate"]["steps"] if "run" in s]
    python_tier = []
    for run in runs:
        if run.startswith("npm "):
            break  # the web tier starts here
        if run.startswith("python ") and "pip install" not in run:
            python_tier.append(run)
    return python_tier


class RepoSetupTest(unittest.TestCase):
    def setUp(self) -> None:
        self.setup_block = load_setup()
        self.steps = {s["id"]: s for s in self.setup_block["steps"]}
        self.tiers = {t["id"]: t for t in self.setup_block["tiers"]}

    def test_step_ids_are_unique(self) -> None:
        ids = [s["id"] for s in self.setup_block["steps"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_tiers_are_ordered_and_cover_every_step_once(self) -> None:
        self.assertEqual([t["id"] for t in self.setup_block["tiers"]], ["preflight", "python", "web"])
        listed = [sid for t in self.setup_block["tiers"] for sid in t["steps"]]
        self.assertEqual(listed, [s["id"] for s in self.setup_block["steps"]])

    def test_needs_point_only_at_earlier_steps(self) -> None:
        seen: set[str] = set()
        for step in self.setup_block["steps"]:
            for dep in step.get("needs", []):
                self.assertIn(dep, seen, f"{step['id']} needs {dep}, which is not an earlier step")
            seen.add(step["id"])

    def test_run_steps_are_idempotent_and_located(self) -> None:
        for step in self.setup_block["steps"]:
            self.assertIn("where", step, step["id"])
            if step["kind"] == "run":
                self.assertTrue("probe" in step or "creates" in step, step["id"])

    def test_steps_are_c0_and_argv_only(self) -> None:
        for step in self.setup_block["steps"]:
            self.assertEqual(step["consent"], {"class": "C0"}, step["id"])
            self.assertIsInstance(step["argv"], list, step["id"])
            self.assertTrue(all(isinstance(a, str) for a in step["argv"]), step["id"])

    def test_web_tier_is_gated_on_network_and_node(self) -> None:
        gate = self.tiers["web"]["when"]
        facts = {c["fact"] for c in gate}
        self.assertIn("network.fonts_google", facts)
        self.assertIn("toolchains.node.version", facts)
        for sid in self.tiers["web"]["steps"]:
            self.assertEqual(self.steps[sid].get("when"), gate, sid)
        for sid in self.tiers["python"]["steps"] + self.tiers["preflight"]["steps"]:
            self.assertNotIn("when", self.steps[sid], sid)

    def test_when_facts_are_z0_host_facts(self) -> None:
        conds = [c for t in self.setup_block["tiers"] for c in t.get("when", [])]
        conds += [c for s in self.setup_block["steps"] for c in s.get("when", [])]
        self.assertTrue(conds)
        for cond in conds:
            root, key = cond["fact"].split(".")[:2]
            self.assertIn(root, Z0_FACTS, cond["fact"])
            self.assertIn(key, Z0_FACTS[root], cond["fact"])

    def test_step_ids_are_the_z0_registry_ids(self) -> None:
        for sid in self.steps:
            self.assertRegex(sid, Z0_REGISTRY_IDS)

    def test_python_tier_follows_ci_order(self) -> None:
        tier = [self.steps[sid] for sid in self.tiers["python"]["steps"]]
        ours = [
            " ".join(["python", *s["argv"][1:]])
            for s in tier
            if s["argv"][0] == ".venv/bin/python" and s["kind"] in ("check", "run")
        ]
        self.assertEqual(ours, ci_python_runs())

    def test_pins_match_version_files(self) -> None:
        py = (REPO / ".python-version").read_text(encoding="utf-8").strip()
        node = (REPO / ".nvmrc").read_text(encoding="utf-8").strip()
        self.assertEqual(self.setup_block["python"]["prefer"], py)
        self.assertEqual(self.setup_block["node"]["prefer"], node)

    def test_open_owner_decisions_are_listed_not_resolved(self) -> None:
        self.assertEqual([i["id"] for i in self.setup_block["open_issues"]], ["B7", "B8"])


if __name__ == "__main__":
    unittest.main()
