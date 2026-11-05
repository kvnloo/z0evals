"""Runner checks and original/reference controls. These are NOT model measurements."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("coding_license", HERE / "run.py")
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)


class LicenseTests(unittest.TestCase):
    def setUp(self):
        self.policy = R.load_policy()
        self.temp = tempfile.TemporaryDirectory()
        self.out = Path(self.temp.name)
        self.model = self.policy["models"][0]

    def tearDown(self):
        self.temp.cleanup()

    def rows(self):
        return [{"model": self.model["id"], "tier": tier, "task": task, "rep": 0,
                 "status": "PASS"} for tier, rule in self.policy["tiers"].items()
                for task in rule["tasks"]]

    def cells(self, rows):
        return [c for c in R.summarize(self.policy, rows) if c["model"] == self.model["id"]]

    def test_all_tasks_required_and_lower_tiers_are_cumulative(self):
        rows = self.rows()
        self.assertEqual([c["status"] for c in self.cells(rows)], ["PASS"] * 3)
        self.assertEqual([c["required"] for c in self.cells(rows)], [6, 10, 14])
        rows[0]["status"] = "FAIL"
        self.assertEqual([c["status"] for c in self.cells(rows)], ["FAIL"] * 3)
        rows[0]["status"] = "BLOCKED"
        self.assertEqual([c["status"] for c in self.cells(rows)], ["BLOCKED"] * 3)

    def test_missing_evidence_never_passes(self):
        rows = self.rows()[:-1]
        self.assertEqual([c["status"] for c in self.cells(rows)], ["PASS", "PASS", "BLOCKED"])
        self.assertFalse(self.cells([])[0]["licensed"])

    def test_duplicate_and_wrong_fold_results_are_rejected(self):
        rows = self.rows()
        with self.assertRaises(ValueError):
            self.cells(rows + rows[:1])
        for field, value in (("task", "not-a-task"), ("rep", 1), ("tier", "L"),
                             ("model", "not-a-model"), ("status", "success")):
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.cells([rows[0] | {field: value}])

    def test_timeout_without_stdout_is_bounded(self):
        result = R.process([sys.executable, "-c", "import time; time.sleep(10)"], self.out, 0.1)
        self.assertTrue(result["timeout"])
        self.assertNotEqual(result["exit"], 0)
        self.assertLess(result["seconds"], 5)

    def test_missing_executable_blocks(self):
        with patch.object(R.shutil, "which", return_value=None):
            result = R.preflight(self.model, self.out)
        self.assertFalse(result["ready"])
        self.assertIn("missing executable", result["reason"])

    def test_unknown_price_never_calls_model_or_inventory(self):
        with patch.object(R.shutil, "which", return_value="/bin/opencode"), patch.object(R, "process") as proc:
            result = R.preflight(self.model, self.out)
        self.assertFalse(result["ready"])
        proc.assert_not_called()

    def test_subscription_status_is_required(self):
        model = next(m for m in self.policy["models"] if m["adapter"] == "fx")
        for auth, expected in (("Codex subscription", True), ("AI Gateway", False)):
            with patch.object(R.shutil, "which", return_value="/bin/fx"), patch.object(
                R, "process", return_value={"exit": 0, "stdout": json.dumps({"auth": auth})}
            ):
                self.assertEqual(R.preflight(model, self.out)["ready"], expected)
        argv = R.command(model, "task")
        self.assertEqual(argv[0], "fx")
        self.assertIn("codex", argv)
        self.assertIn("--no-fast", argv)
        self.assertIn("--no-ultrafast", argv)

    def test_anonymous_route_does_not_inherit_owner_home(self):
        model = next(m for m in self.policy["models"] if m["funding"] == "free-catalog-zero")
        with patch.object(R.shutil, "which", return_value="/bin/opencode"), patch.object(
            R, "process", return_value={"exit": 0, "stdout": model["id"] + "\n"}
        ) as proc:
            self.assertTrue(R.preflight(model, self.out)["ready"])
        env = proc.call_args.args[3]
        self.assertEqual(env["HOME"], str(self.out / "anonymous-home"))
        self.assertEqual(set(env), {"HOME", "PATH", "LANG", "TERM", "XDG_CONFIG_HOME",
                                   "XDG_DATA_HOME", "XDG_CACHE_HOME"})

    def test_blocked_run_writes_every_cell_and_refuses_overwrite(self):
        out = self.out / "run"
        with patch.object(R.shutil, "which", return_value=None), patch("builtins.print"):
            self.assertEqual(R.run(self.policy, out), 1)
        rows = [json.loads(line) for line in (out / "rows.jsonl").read_text().splitlines()]
        self.assertEqual(len(rows), 14 * len(self.policy["models"]))
        self.assertEqual({r["status"] for r in rows}, {"BLOCKED"})
        self.assertEqual(len(json.loads((out / "matrix.json").read_text())), 3 * len(self.policy["models"]))
        with self.assertRaises(FileExistsError):
            R.run(self.policy, out)

    def test_symlinks_cannot_escape_grading_copy(self):
        submitted = self.out / "submitted"
        submitted.mkdir()
        (submitted / "test_escape.py").symlink_to(HERE / "run.py")
        result = R.grade("t01-paginate", submitted, self.out)
        self.assertFalse(result["pass"])
        self.assertIn("symlink", result["summary"])

    def test_all_frozen_fixtures_fail_original_and_pass_reference(self):
        for tier, rule in self.policy["tiers"].items():
            for task in rule["tasks"]:
                for mode, expected in (("original", False), ("reference", True)):
                    with self.subTest(task=task, mode=mode):
                        out = self.out / task / mode
                        out.mkdir(parents=True)
                        submitted = out / "submitted"
                        source = R.SOURCE / "tasks" / task
                        shutil.copytree(source / "repo", submitted)
                        if expected:
                            shutil.copytree(source / "reference", submitted, dirs_exist_ok=True)
                        result = R.grade(task, submitted, out)
                        self.assertEqual(result["pass"], expected, result)
                        self.assertFalse(result["tests_modified"])
                        print(f"CONTROL {task} {mode} pass={result['pass']}", flush=True)

    def test_test_tampering_disqualifies_a_correct_submission(self):
        source = R.SOURCE / "tasks/t01-paginate"
        submitted = self.out / "submitted"
        shutil.copytree(source / "repo", submitted)
        shutil.copytree(source / "reference", submitted, dirs_exist_ok=True)
        original = next(submitted.glob("test_*.py"))
        original.unlink()
        result = R.grade("t01-paginate", submitted, self.out)
        self.assertTrue(result["pass"])
        self.assertTrue(result["tests_modified"])

    def test_cli_error_is_blocked_and_test_tampering_fails(self):
        task = "t01-paginate"
        cases = [("import sys; sys.exit(7)", "BLOCKED"),
                 ("from pathlib import Path; [p.unlink() for p in Path('.').glob('test_*.py')]", "FAIL")]
        for index, (code, expected) in enumerate(cases):
            with self.subTest(expected=expected), patch.object(
                R, "command", return_value=[sys.executable, "-c", code]
            ):
                row = R.probe_task(self.model, task, "S", 5, self.out / str(index) / "tasks" / task)
                self.assertEqual(row["status"], expected)

    def test_probe_preserves_submission_and_verifier_receipts(self):
        model = self.model
        task = "t01-paginate"
        reference = R.SOURCE / "tasks" / task / "reference"
        code = f"import shutil; shutil.copytree({str(reference)!r}, '.', dirs_exist_ok=True)"
        with patch.object(R, "command", return_value=[sys.executable, "-c", code]):
            row = R.probe_task(model, task, "S", 5, self.out / "model/tasks" / task)
        self.assertEqual(row["status"], "PASS")
        artifact = self.out / "model/tasks" / task
        self.assertTrue((artifact / "submission").is_dir())
        self.assertTrue((artifact / "agent-process.json").exists())
        self.assertTrue((artifact / "verifier-process.json").exists())
        self.assertTrue(row["submission_sha256"])


if __name__ == "__main__":
    unittest.main()
