"""The published unified-memory cohort must participate in study validation."""

from contextlib import redirect_stdout
import importlib.util
from io import StringIO
import json
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
STUDY = Path("studies/unified-memory-v0")


class UnifiedMemoryArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        # Explicit public-file allowlist; never import local runtime state.
        paths = [Path("schemas/study-manifest.schema.json")]
        paths += [STUDY / name for name in (
            "manifest.yaml", "question-contract.json", "receipt.schema.json", "cohort.json"
        )]
        for path in paths:
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, self.root / path)
        spec = importlib.util.spec_from_file_location("study_validator", ROOT / "scripts/validate.py")
        self.validator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.validator)
        self.validator.ROOT = self.root

    def validate(self):
        output = StringIO()
        error = None
        with redirect_stdout(output):
            try:
                self.validator.main()
            except SystemExit as exc:
                error = str(exc)
        return error, output.getvalue()

    def test_unmodified_public_cohort_is_valid(self):
        error, output = self.validate()
        self.assertIsNone(error)
        self.assertIn("ok: 1 study manifest(s)", output)

    def test_missing_executable_cohort_is_rejected(self):
        (self.root / STUDY / "cohort.json").unlink()
        error, output = self.validate()
        self.assertIsNotNone(error, f"Missing executable cohort was accepted: {output}")
        self.assertIn("missing artifact cohort.json", output)

    def test_changed_executable_cohort_is_rejected(self):
        path = self.root / STUDY / "cohort.json"
        cohort = json.loads(path.read_text())
        cohort["questions"][0]["prompt"] += " Changed after the cohort was frozen."
        path.write_text(json.dumps(cohort, indent=2) + "\n")
        error, output = self.validate()
        self.assertIsNotNone(error, f"Changed frozen cohort was accepted: {output}")
        self.assertIn("hash mismatch cohort.json", output)


if __name__ == "__main__":
    unittest.main()
