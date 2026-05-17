"""Tests for scripts/generate/generate_community_pages.py."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "generate" / "generate_community_pages.py"
INPUT_PATH = REPO_ROOT / "references" / "community" / "ecosystem_packages.json"
OUTPUT_PATH = REPO_ROOT / "src" / "content" / "docs" / "ecosystem" / "map.md"


class GenerateCommunityPagesUnitTests(unittest.TestCase):
    """Direct unit tests for generator functions."""

    def _import_module(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("generate_community_pages", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_build_markdown_includes_generated_banner(self):
        module = self._import_module()
        data = {
            "metadata": {"last_updated": "2026-04-23"},
            "packages": [],
        }
        result = module.build_markdown(data)
        self.assertTrue(result.startswith('---\ntitle: "Ecosystem Map"\n---\n\n'))
        self.assertIn("GENERATED FILE: do not edit directly", result)

    def test_build_markdown_groups_by_category(self):
        module = self._import_module()
        data = {
            "metadata": {"last_updated": "2026-04-23"},
            "packages": [
                {
                    "slug": "pack-a",
                    "name": "Pack A",
                    "repo_url": "https://github.com/example/a",
                    "registry_url": None,
                    "category": "node_pack",
                    "status": "Actively Maintained",
                    "role_summary": "Test pack A",
                    "notable_patterns": [],
                    "used_by": None,
                    "source_type": "community_observation",
                    "evidence_urls": [],
                    "pinned_external_version": None,
                    "pinned_commit": None,
                    "last_verified": "2026-04-22",
                    "needs_review_after": "2026-07-22",
                    "maintenance_tier": "tier_2",
                    "caveats": None,
                },
                {
                    "slug": "tool-a",
                    "name": "Tool A",
                    "repo_url": "https://github.com/example/tool",
                    "registry_url": None,
                    "category": "tooling",
                    "status": "Community Supported",
                    "role_summary": "Test tool",
                    "notable_patterns": ["pattern_x"],
                    "used_by": "Developers",
                    "source_type": "community_observation",
                    "evidence_urls": [],
                    "pinned_external_version": None,
                    "pinned_commit": None,
                    "last_verified": "2026-04-22",
                    "needs_review_after": "2026-07-22",
                    "maintenance_tier": "tier_2",
                    "caveats": None,
                },
            ],
        }
        result = module.build_markdown(data)
        self.assertIn("## Node Packs", result)
        self.assertIn("## Tooling and Utilities", result)
        self.assertIn("### Pack A", result)
        self.assertIn("### Tool A", result)
        self.assertIn("pattern_x", result)
        self.assertIn("Developers", result)

    def test_build_markdown_includes_freshness_labels(self):
        module = self._import_module()
        data = {
            "metadata": {"last_updated": "2026-04-23"},
            "packages": [
                {
                    "slug": "pack-a",
                    "name": "Pack A",
                    "repo_url": None,
                    "registry_url": None,
                    "category": "node_pack",
                    "status": "Actively Maintained",
                    "role_summary": "Test",
                    "notable_patterns": [],
                    "used_by": None,
                    "source_type": "community_observation",
                    "evidence_urls": [],
                    "pinned_external_version": None,
                    "pinned_commit": None,
                    "last_verified": "2026-04-22",
                    "needs_review_after": "2026-07-22",
                    "maintenance_tier": "tier_2",
                    "caveats": None,
                }
            ],
        }
        result = module.build_markdown(data)
        self.assertIn("**Last Verified:** 2026-04-22", result)
        self.assertIn("**Last Updated:** 2026-04-23", result)

    def test_build_markdown_missing_required_field_still_renders(self):
        """Generator should not crash on missing optional metadata."""
        module = self._import_module()
        data = {
            "metadata": {},
            "packages": [],
        }
        result = module.build_markdown(data)
        self.assertIn('title: "Ecosystem Map"', result)

    def test_build_markdown_renders_caveats(self):
        module = self._import_module()
        data = {
            "metadata": {"last_updated": "2026-04-23"},
            "packages": [
                {
                    "slug": "warned-pack",
                    "name": "Warned Pack",
                    "repo_url": None,
                    "registry_url": None,
                    "category": "node_pack",
                    "status": "Unknown",
                    "role_summary": "Test",
                    "notable_patterns": [],
                    "used_by": None,
                    "source_type": "community_observation",
                    "evidence_urls": [],
                    "pinned_external_version": None,
                    "pinned_commit": None,
                    "last_verified": "2026-04-22",
                    "needs_review_after": "2026-07-22",
                    "maintenance_tier": "tier_4",
                    "caveats": "Verify before use",
                }
            ],
        }
        result = module.build_markdown(data)
        self.assertIn("**Caveats:** Verify before use", result)


class GenerateCommunityPagesScriptTests(unittest.TestCase):
    """Tests that the generator script runs successfully without overwriting tracked files during tests."""

    def test_script_runs_and_generates_output(self):
        # Run the script in a temporary directory with a copy of the repo structure
        # to avoid overwriting the tracked src/content/docs/ecosystem/map.md during tests.
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            # Create minimal directory structure
            (tmp_root / "references" / "community").mkdir(parents=True)
            (tmp_root / "src" / "content" / "docs" / "ecosystem").mkdir(parents=True)
            (tmp_root / "scripts" / "generate").mkdir(parents=True)

            # Copy generator script and input JSON
            import shutil

            shutil.copy(SCRIPT, tmp_root / "scripts" / "generate" / "generate_community_pages.py")
            shutil.copy(
                INPUT_PATH, tmp_root / "references" / "community" / "ecosystem_packages.json"
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(tmp_root / "scripts" / "generate" / "generate_community_pages.py"),
                ],
                capture_output=True,
                text=True,
                cwd=str(tmp_root),
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

            output_path = tmp_root / "src" / "content" / "docs" / "ecosystem" / "map.md"
            self.assertTrue(output_path.exists())
            content = output_path.read_text(encoding="utf-8")
            self.assertTrue(content.startswith('---\ntitle: "Ecosystem Map"\n---\n\n'))
            self.assertIn("GENERATED FILE: do not edit directly", content)


if __name__ == "__main__":
    unittest.main()
