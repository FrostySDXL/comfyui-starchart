"""Tests for scripts/verify/community_metadata.py."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "community_metadata.py"


class CommunityMetadataUnitTests(unittest.TestCase):
    """Direct unit tests for community metadata validation functions."""

    def _import_module(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("community_metadata", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_valid_package_passes(self):
        module = self._import_module()
        data = {
            "packages": [
                {
                    "maintenance_tier": "tier_2",
                    "last_verified": "2026-04-22",
                    "needs_review_after": "2026-07-22",
                }
            ]
        }
        errors = module.validate_packages(data, "ecosystem_packages.json")
        self.assertEqual(errors, [])

    def test_invalid_tier_fails(self):
        module = self._import_module()
        data = {
            "packages": [
                {
                    "maintenance_tier": "tier_99",
                    "last_verified": "2026-04-22",
                    "needs_review_after": "2026-07-22",
                }
            ]
        }
        errors = module.validate_packages(data, "ecosystem_packages.json")
        self.assertTrue(any("invalid maintenance_tier" in e for e in errors))

    def test_reviewed_package_requires_evidence_urls(self):
        module = self._import_module()
        data = {
            "packages": [
                {
                    "name": "Reviewed Pack",
                    "maintenance_tier": "tier_2",
                    "status": "Community Supported",
                    "source_type": "community_observation",
                    "evidence_urls": [],
                    "last_verified": "2026-04-22",
                    "needs_review_after": "2026-07-22",
                }
            ]
        }
        errors = module.validate_packages(data, "ecosystem_packages.json")
        self.assertTrue(any("must include at least one evidence_urls entry" in e for e in errors))

    def test_unknown_package_can_omit_evidence_urls(self):
        module = self._import_module()
        data = {
            "packages": [
                {
                    "name": "Unknown Pack",
                    "maintenance_tier": "tier_4",
                    "status": "Unknown",
                    "source_type": "community_observation",
                    "evidence_urls": [],
                    "last_verified": "2026-04-22",
                    "needs_review_after": "2026-07-22",
                }
            ]
        }
        errors = module.validate_packages(data, "ecosystem_packages.json")
        self.assertEqual(errors, [])

    def test_needs_review_before_last_verified_fails(self):
        module = self._import_module()
        data = {
            "packages": [
                {
                    "maintenance_tier": "tier_2",
                    "last_verified": "2026-07-22",
                    "needs_review_after": "2026-04-22",
                }
            ]
        }
        errors = module.validate_packages(data, "ecosystem_packages.json")
        self.assertTrue(any("needs_review_after" in e and "before" in e for e in errors))

    def test_valid_page_passes(self):
        module = self._import_module()
        data = {
            "pages": [
                {
                    "maintenance_tier": "tier_2",
                    "evidence_label": "Community pattern study",
                    "last_verified": "2026-04-22",
                    "needs_review_after": "2026-07-22",
                    "generated_from": "references/community/ecosystem_packages.json",
                }
            ]
        }
        errors = module.validate_pages(data, "community_pages.json")
        self.assertEqual(errors, [])

    def test_generated_from_missing_file_fails(self):
        module = self._import_module()
        data = {
            "pages": [
                {
                    "maintenance_tier": "tier_2",
                    "evidence_label": "Community pattern study",
                    "last_verified": "2026-04-22",
                    "needs_review_after": "2026-07-22",
                    "generated_from": "references/community/nonexistent.json",
                }
            ]
        }
        errors = module.validate_pages(data, "community_pages.json")
        self.assertTrue(any("generated_from points to missing file" in e for e in errors))

    def test_empty_evidence_label_fails(self):
        module = self._import_module()
        data = {
            "pages": [
                {
                    "maintenance_tier": "tier_2",
                    "evidence_label": "",
                    "last_verified": "2026-04-22",
                    "needs_review_after": "2026-07-22",
                    "generated_from": None,
                }
            ]
        }
        errors = module.validate_pages(data, "community_pages.json")
        self.assertTrue(any("evidence_label is empty" in e for e in errors))


class CommunityMetadataScriptTests(unittest.TestCase):
    """Tests that the community metadata script runs successfully."""

    def test_script_runs_and_passes(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Community metadata operational rules pass", result.stdout)


if __name__ == "__main__":
    unittest.main()
