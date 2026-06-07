"""Tests for examples-only validation matrix policy."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "example_validation_matrix.py"
MATRIX = REPO_ROOT / "references" / "example-validation-matrix.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("example_validation_matrix", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExampleValidationMatrixTests(unittest.TestCase):
    """Matrix entries must make validation evidence explicit."""

    def test_matrix_file_exists_and_validates(self):
        module = _load_module()

        matrix = module.load_matrix(MATRIX)
        errors = module.validate_matrix(REPO_ROOT, matrix)

        self.assertEqual(errors, [])

    def test_runtime_smoke_entries_have_commands(self):
        module = _load_module()
        matrix = module.load_matrix(MATRIX)
        runtime_entries = [
            entry for entry in matrix["examples"] if "runtime_smoke" in entry["validation_tiers"]
        ]

        self.assertGreaterEqual(len(runtime_entries), 1)
        for entry in runtime_entries:
            self.assertIn("runtime_command", entry)
            self.assertIn("scripts/verify/example_runtime_smoke.py", entry["runtime_command"])

    def test_matrix_covers_each_example_readme_directory(self):
        module = _load_module()
        matrix = module.load_matrix(MATRIX)

        covered_paths = {entry["path"].rstrip("/") for entry in matrix["examples"]}
        readme_paths = {
            readme.parent.relative_to(REPO_ROOT).as_posix()
            for readme in (REPO_ROOT / "examples").rglob("README.md")
            if readme.parent != REPO_ROOT / "examples"
        }

        self.assertEqual(readme_paths - covered_paths, set())

    def test_validate_matrix_reports_uncovered_example_readme_directory(self):
        module = _load_module()
        matrix = {
            "examples": [
                {
                    "path": "examples/covered/",
                    "validation_tiers": ["static"],
                    "evidence": ["python scripts/verify/example_surface_integrity.py"],
                }
            ]
        }
        with self.subTest("fixture"):
            import tempfile

            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                (root / "examples" / "covered").mkdir(parents=True)
                (root / "examples" / "covered" / "README.md").write_text(
                    "# Covered\n", encoding="utf-8"
                )
                (root / "examples" / "uncovered").mkdir(parents=True)
                (root / "examples" / "uncovered" / "README.md").write_text(
                    "# Uncovered\n", encoding="utf-8"
                )

                errors = module.validate_matrix(root, matrix)

        self.assertIn(
            "Missing matrix entry for example README directory: examples/uncovered", errors
        )


if __name__ == "__main__":
    unittest.main()
