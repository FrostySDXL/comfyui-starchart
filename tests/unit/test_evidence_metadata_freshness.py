"""Tests for scripts/verify/evidence_metadata_freshness.py."""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "evidence_metadata_freshness.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("evidence_metadata_freshness", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EvidenceMetadataFreshnessUnitTests(unittest.TestCase):
    def _write_page(self, docs_root: Path, relative_path: str, lines: list[str]) -> None:
        page_path = docs_root / relative_path
        page_path.parent.mkdir(parents=True, exist_ok=True)
        page_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_passes_when_required_labels_and_baseline_status_exist(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            self._write_page(
                docs_root,
                "api/endpoints.md",
                [
                    "---",
                    'title: "API Endpoints"',
                    "---",
                    "",
                    "**Evidence:** Source-backed from pinned snapshots",
                    "**Last Updated:** 2026-05-24",
                    "**Baseline verification status:** Verified against the current pinned baseline: core `v0.22.0`, frontend `v1.45.12`, snapshots `2026-05-21`.",
                ],
            )

            old_docs_root = module.DOCS_ROOT
            old_paths = module.BASELINE_REQUIRED_PATHS
            try:
                module.DOCS_ROOT = docs_root
                module.BASELINE_REQUIRED_PATHS = {"api/endpoints.md"}
                self.assertEqual(module.verify_pages(), [])
            finally:
                module.DOCS_ROOT = old_docs_root
                module.BASELINE_REQUIRED_PATHS = old_paths

    def test_fails_when_required_label_is_missing(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            self._write_page(
                docs_root,
                "api/endpoints.md",
                [
                    "**Last Updated:** 2026-05-24",
                    "**Baseline verification status:** Verified against the current pinned baseline: core `v0.22.0`, frontend `v1.45.12`, snapshots `2026-05-21`.",
                ],
            )

            old_docs_root = module.DOCS_ROOT
            old_paths = module.BASELINE_REQUIRED_PATHS
            try:
                module.DOCS_ROOT = docs_root
                module.BASELINE_REQUIRED_PATHS = {"api/endpoints.md"}
                errors = module.verify_pages()
            finally:
                module.DOCS_ROOT = old_docs_root
                module.BASELINE_REQUIRED_PATHS = old_paths

            self.assertTrue(any("**Evidence:**" in error for error in errors))

    def test_fails_when_baseline_status_is_missing(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            self._write_page(
                docs_root,
                "api/endpoints.md",
                [
                    "**Evidence:** Source-backed from pinned snapshots",
                    "**Last Updated:** 2026-05-24",
                ],
            )

            old_docs_root = module.DOCS_ROOT
            old_paths = module.BASELINE_REQUIRED_PATHS
            try:
                module.DOCS_ROOT = docs_root
                module.BASELINE_REQUIRED_PATHS = {"api/endpoints.md"}
                errors = module.verify_pages()
            finally:
                module.DOCS_ROOT = old_docs_root
                module.BASELINE_REQUIRED_PATHS = old_paths

            self.assertTrue(any("Baseline verification status" in error for error in errors))

    def test_fails_when_exception_wording_is_not_approved(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_root = Path(tmpdir)
            self._write_page(
                docs_root,
                "deep-dives/workflow-json-schema.md",
                [
                    "**Evidence:** Official docs-backed from docs.comfy.org",
                    "**Last Updated:** 2026-05-24",
                    "**Baseline verification status:** Needs review soon.",
                ],
            )

            old_docs_root = module.DOCS_ROOT
            old_paths = module.BASELINE_REQUIRED_PATHS
            try:
                module.DOCS_ROOT = docs_root
                module.BASELINE_REQUIRED_PATHS = {"deep-dives/workflow-json-schema.md"}
                errors = module.verify_pages()
            finally:
                module.DOCS_ROOT = old_docs_root
                module.BASELINE_REQUIRED_PATHS = old_paths

            self.assertTrue(any("approved phrasing" in error for error in errors))


class EvidenceMetadataFreshnessScriptTests(unittest.TestCase):
    def test_script_runs_and_passes(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Evidence metadata freshness checks passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
