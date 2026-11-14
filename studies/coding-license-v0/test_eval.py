import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("coding_license", HERE / "eval.py")
license_eval = importlib.util.module_from_spec(spec)
spec.loader.exec_module(license_eval)


class LicenseTests(unittest.TestCase):
    def test_upstream_source_is_pinned(self):
        license_eval.check_sources()

    def test_diagnostic_settings_cannot_grant_license(self):
        rows = [{"task": task, "rep": rep, "status": "PASS"}
                for tasks in license_eval.TIERS.values() for task in tasks for rep in range(2)]
        with tempfile.TemporaryDirectory() as tmp:
            normal = license_eval.write_summary(Path(tmp), "control", "test", "free", rows, 2, "digest", 180)
            self.assertTrue(all(normal["license_granted"].values()))
            diagnostic = license_eval.write_summary(Path(tmp), "control", "test", "free", rows, 2, "digest", 181)
            self.assertFalse(any(diagnostic["license_granted"].values()))

    def test_tiers_partition_all_upstream_tasks(self):
        names = [name for tasks in license_eval.TIERS.values() for name in tasks]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(set(names), {p.name for p in license_eval.TASKS.iterdir() if p.is_dir()})

    def test_response_formats(self):
        answer = {"files": {"pager.py": "pass\n"}}
        self.assertEqual(license_eval.decode_response(json.dumps(answer)), answer)
        fenced = "```json\n" + json.dumps(answer) + "\n```"
        self.assertEqual(license_eval.decode_response(fenced), answer)
        self.assertEqual(license_eval.decode_response(json.dumps({"final_output": fenced})), answer)
        with self.assertRaises(ValueError):
            license_eval.decode_response('{"final_output":"","output":"stale text"}')

    def test_patch_rejects_escape_tests_and_symlinks_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            (root / "pager.py").write_text("original")
            (root / "alias.py").symlink_to(root / "pager.py")
            for name in ("../escape.py", "/tmp/escape.py", "test_pager.py", ".git/hook.py", "alias.py", "newdir/file.py", "sitecustomize.py"):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    license_eval.apply_files(root, {"pager.py": "changed", name: "pass"})
                self.assertEqual((root / "pager.py").read_text(), "original")
            license_eval.apply_files(root, {"pager.py": "changed"})
            self.assertEqual((root / "pager.py").read_text(), "changed")

    def test_pass_requires_complete_clean_lower_tiers(self):
        rows = [{"task": task, "rep": rep, "status": "PASS"}
                for tasks in license_eval.TIERS.values() for task in tasks for rep in range(2)]
        self.assertEqual(license_eval.tier_results(rows, 2), {"S": "PASS", "M": "PASS", "L": "PASS"})
        rows[0]["status"] = "FAIL"
        self.assertEqual(license_eval.tier_results(rows, 2), {"S": "FAIL", "M": "FAIL", "L": "FAIL"})
        self.assertEqual(license_eval.tier_results([], 2), {"S": "NOT_RUN", "M": "NOT_RUN", "L": "NOT_RUN"})
        rows[0]["status"] = "ERROR"
        self.assertEqual(license_eval.tier_results(rows, 2), {"S": "INCOMPLETE", "M": "INCOMPLETE", "L": "INCOMPLETE"})
        rows[0]["status"] = "PASS"
        rows.append(rows[0])
        with self.assertRaises(ValueError):
            license_eval.tier_results(rows, 2)

    def test_originals_fail_references_pass(self):
        for tasks in license_eval.TIERS.values():
            for task in tasks:
                for reference in (False, True):
                    with self.subTest(task=task, reference=reference), tempfile.TemporaryDirectory() as tmp:
                        repo = Path(tmp) / "repo"
                        shutil.copytree(license_eval.TASKS / task / "repo", repo)
                        if reference:
                            shutil.copytree(license_eval.TASKS / task / "reference", repo, dirs_exist_ok=True)
                        result = license_eval.verify_task(task, repo)
                        self.assertEqual(result["pass"], reference, result)
                        self.assertFalse(result["tests_modified"])

    def test_modified_visible_test_cannot_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            task = license_eval.TASKS / "t01-paginate"
            shutil.copytree(task / "repo", repo)
            shutil.copytree(task / "reference", repo, dirs_exist_ok=True)
            (repo / "test_pager.py").write_text("# erased\n")
            result = license_eval.verify_task(task.name, repo)
            self.assertFalse(result["pass"])
            self.assertTrue(result["tests_modified"])

    def test_end_to_end_all_tiers_and_reject_output_reuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = root / "reference_model.py"
            # A control, not a model result. Only this test adapter can read references.
            fake.write_text('import json, pathlib, sys\n'
                            f'base = pathlib.Path({str(license_eval.TASKS)!r})\n'
                            'task = json.loads(sys.argv[1])["task"]\n'
                            'print(json.dumps({"files": {str(p.relative_to(base/task/"reference")): p.read_text() '
                            'for p in (base/task/"reference").rglob("*.py")}}))\n')
            out = root / "results"
            argv = [sys.executable, str(HERE / "eval.py"), "run", "--model", "reference-control",
                    "--provider", "test", "--billing", "free", "--reps", "1", "--out", str(out),
                    "--", sys.executable, str(fake), "{prompt}"]
            proc = subprocess.run(argv, capture_output=True, text=True, timeout=180)
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            summary = json.loads((out / "summary.json").read_text())
            self.assertEqual(summary["tiers"], {"S": "PASS", "M": "PASS", "L": "PASS"})
            self.assertFalse(summary["qualifying_protocol"])
            self.assertEqual(summary["license_granted"], {"S": False, "M": False, "L": False})
            self.assertEqual(len((out / "results.jsonl").read_text().splitlines()), 14)
            self.assertEqual(len(list((out / "attempts").glob("*/response.txt"))), 14)
            reused = subprocess.run(argv, capture_output=True, text=True, timeout=10)
            self.assertNotEqual(reused.returncode, 0)

    def test_process_and_response_errors_stop_without_retry(self):
        for code, expected_exit in (("raise SystemExit(75)", 75), ("print('not json')", 0)):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "results"
                argv = [sys.executable, str(HERE / "eval.py"), "run", "--model", "error-control",
                        "--provider", "test", "--billing", "free", "--out", str(out),
                        "--", sys.executable, "-c", code, "{prompt}"]
                proc = subprocess.run(argv, capture_output=True, text=True, timeout=20)
                self.assertEqual(proc.returncode, 2, proc.stderr + proc.stdout)
                rows = [json.loads(line) for line in (out / "results.jsonl").read_text().splitlines()]
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["status"], "ERROR")
                self.assertEqual(rows[0]["process_exit"], expected_exit)
                summary = json.loads((out / "summary.json").read_text())
                self.assertFalse(any(summary["license_granted"].values()))

    def test_gpt_must_use_fx_and_prompt_placeholder_is_required(self):
        with self.assertRaises(ValueError):
            license_eval.validate_command("gpt-test", ["opencode", "{prompt}"])
        with self.assertRaises(ValueError):
            license_eval.validate_command("free-model", ["echo", "no placeholder"])
        license_eval.validate_command("gpt-test", ["fx", "ask", "{prompt}"])


if __name__ == "__main__":
    unittest.main()
