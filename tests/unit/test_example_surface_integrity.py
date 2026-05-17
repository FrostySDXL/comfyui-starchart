"""Tests for scripts/verify/example_surface_integrity.py."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "example_surface_integrity.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("example_surface_integrity", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExampleSurfaceIntegrityUnitTests(unittest.TestCase):
    """Unit tests for static example-surface validation."""

    def test_validate_example_surface_succeeds_for_valid_fixture_tree(self):
        module = _load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._build_valid_fixture(root)

            errors = module.validate_example_surface(root)

        self.assertEqual(errors, [])

    def test_validate_example_surface_reports_missing_readme(self):
        module = _load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._build_valid_fixture(root)
            (root / "examples" / "consumers" / "alpha" / "README.md").unlink()

            errors = module.validate_example_surface(root)

        self.assertIn("Missing README.md: examples/consumers/alpha/README.md", errors)

    def test_validate_example_surface_reports_missing_routed_path(self):
        module = _load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._build_valid_fixture(root)
            doc_path = root / "src" / "content" / "docs" / "how-to" / "consumer-starter-examples.md"
            doc_path.write_text(
                "Repo path: `examples/consumers/missing-example/`\n",
                encoding="utf-8",
            )

            errors = module.validate_example_surface(root)

        self.assertIn(
            "Missing routed example path: examples/consumers/missing-example/ "
            "referenced in src/content/docs/how-to/consumer-starter-examples.md",
            errors,
        )

    def test_validate_example_surface_reports_invalid_json(self):
        module = _load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._build_valid_fixture(root)
            (root / "examples" / "workflows" / "demo.json").write_text(
                '{\n  "broken": true,\n',
                encoding="utf-8",
            )

            errors = module.validate_example_surface(root)

        self.assertTrue(
            any(error.startswith("Invalid JSON: examples/workflows/demo.json") for error in errors)
        )

    def test_validate_example_surface_reports_broken_local_readme_link(self):
        module = _load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._build_valid_fixture(root)
            readme_path = root / "examples" / "consumers" / "alpha" / "README.md"
            readme_path.write_text(
                "See [Missing Doc](../../../src/content/docs/how-to/missing.md).\n",
                encoding="utf-8",
            )

            errors = module.validate_example_surface(root)

        self.assertIn(
            "Broken local reference: ../../../src/content/docs/how-to/missing.md in "
            "examples/consumers/alpha/README.md",
            errors,
        )

    def test_validate_example_surface_reports_missing_example_family(self):
        module = _load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._build_valid_fixture(root)
            shutil.rmtree(root / "examples" / "extensions")

            errors = module.validate_example_surface(root)

        self.assertIn("Missing example family directory: examples/extensions", errors)

    @staticmethod
    def _build_valid_fixture(root: Path) -> None:
        paths_to_create = [
            root / "src" / "content" / "docs" / "how-to",
            root / "src" / "content" / "docs" / "start-here",
            root / "examples" / "api-calls",
            root / "examples" / "consumers" / "alpha",
            root / "examples" / "custom-nodes" / "beta",
            root / "examples" / "extensions" / "gamma",
            root / "examples" / "workflows",
        ]
        for path in paths_to_create:
            path.mkdir(parents=True, exist_ok=True)

        files = {
            root / "src" / "content" / "docs" / "how-to" / "consumer-starter-examples.md": (
                "Repo path: `examples/consumers/alpha/`\n"
            ),
            root / "src" / "content" / "docs" / "start-here" / "tooling-builder.md": (
                "- `examples/consumers/alpha/`\n"
            ),
            root / "examples" / "api-calls" / "README.md": "# API calls\n",
            root / "examples" / "api-calls" / "payload.json": "{}\n",
            root / "examples" / "consumers" / "alpha" / "README.md": (
                "See [Consumer Starter Examples](../../../src/content/docs/how-to/consumer-starter-examples.md).\n"
            ),
            root / "examples" / "custom-nodes" / "beta" / "README.md": "# Custom node\n",
            root / "examples" / "extensions" / "gamma" / "README.md": "# Extension\n",
            root / "examples" / "workflows" / "README.md": "# Workflows\n",
        }
        for path, content in files.items():
            path.write_text(content, encoding="utf-8")


class ExampleSurfaceIntegrityScriptTests(unittest.TestCase):
    """CLI-level tests for example_surface_integrity.py."""

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("example surfaces", result.stdout)
        self.assertIn("README/path/JSON integrity", result.stdout)


if __name__ == "__main__":
    unittest.main()
