from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.verify import published_schema_validation

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLISHED_SCHEMA_DIR = REPO_ROOT / "public" / "artifacts" / "schemas"


class PublishedSchemaValidationTests(unittest.TestCase):
    def test_load_published_artifact_schema_resolves_support_artifact_schemas(self):
        delta_schema = published_schema_validation.load_published_artifact_schema(
            "delta-summary.json",
            PUBLISHED_SCHEMA_DIR,
        )
        refresh_schema = published_schema_validation.load_published_artifact_schema(
            "refresh-provenance.json",
            PUBLISHED_SCHEMA_DIR,
        )

        self.assertIsNotNone(delta_schema)
        self.assertEqual(delta_schema["title"], "ComfyUI StarChart delta-summary support artifact")
        self.assertIsNotNone(refresh_schema)
        self.assertEqual(
            refresh_schema["title"],
            "ComfyUI StarChart refresh-provenance support artifact",
        )

    def test_validate_against_published_artifact_schema_reports_delta_summary_violation(self):
        errors = published_schema_validation.validate_against_published_artifact_schema(
            {
                "comparison": {"old": "references/old", "new": "references/raw"},
                "notes": [],
                "artifacts": {
                    "server_endpoints": {
                        "old_count": 1,
                        "new_count": 1,
                        "added": [],
                        "removed": [],
                        "changed": [],
                    },
                    "js_hooks": {
                        "old_count": 1,
                        "new_count": 1,
                        "added": [],
                        "removed": [],
                        "changed": [],
                    },
                    "node_api_schema": {
                        "object_info_fields": {
                            "old_count": 1,
                            "new_count": 1,
                            "added": [],
                            "removed": [],
                            "changed": [],
                        },
                        "io_types": {
                            "old_count": 1,
                            "new_count": "wrong",
                            "added": [],
                            "removed": [],
                            "changed": [],
                        },
                        "typed_input_shapes": {
                            "old_count": 1,
                            "new_count": 1,
                            "added": [],
                            "removed": [],
                            "changed": [],
                        },
                    },
                },
            },
            "delta-summary.json",
            PUBLISHED_SCHEMA_DIR,
        )

        self.assertTrue(
            any("node_api_schema.io_types.new_count: expected integer" in e for e in errors)
        )

    def test_validate_against_published_artifact_schema_reports_refresh_provenance_violation(self):
        errors = published_schema_validation.validate_against_published_artifact_schema(
            {
                "backup_location": "references/_refresh_backups/raw_test",
                "next_steps": {
                    "publish_reference_artifacts_command": "py -3.11 scripts/generate/publish_reference_artifacts.py",
                    "verify_artifact_integrity_command": "py -3.11 scripts/verify/verify_artifact_integrity.py",
                    "delta_summary_command": None,
                    "run_all_command": "py -3.11 scripts/verify/run_all.py",
                },
                "published": {
                    "manifest_included": False,
                    "provenance_path": "public/artifacts/refresh-provenance.json",
                    "canonical_artifacts_updated_by_refresh": False,
                    "delta_summary_updated_by_refresh": False,
                },
                "refresh_date": "2026-05-21",
                "requested_versions": {
                    "core": "v0.22.0",
                    "frontend": "v1.45.12",
                },
                "resolved_commits": {
                    "core": None,
                    "frontend": 123,
                },
                "runtime_object_info": {
                    "merged_into_node_api_schema": False,
                    "requested": False,
                },
            },
            "refresh-provenance.json",
            PUBLISHED_SCHEMA_DIR,
        )

        self.assertTrue(
            any("resolved_commits.frontend: expected string | null" in e for e in errors)
        )

    def test_integer_and_number_do_not_accept_bool(self):
        self.assertFalse(published_schema_validation._instance_matches_json_type(True, "integer"))
        self.assertFalse(published_schema_validation._instance_matches_json_type(True, "number"))
        self.assertTrue(published_schema_validation._instance_matches_json_type(True, "boolean"))

    def test_validate_json_schema_instance_rejects_unexpected_keys(self):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "additionalProperties": False,
        }

        errors = published_schema_validation._validate_json_schema_instance(
            {"name": "ok", "extra": "nope"},
            schema,
            "docs-index.json",
        )

        self.assertIn("docs-index.json: unexpected key 'extra'", errors)

    def test_validate_json_schema_instance_checks_pattern_properties(self):
        schema = {
            "type": "object",
            "patternProperties": {
                r"^x-.*": {"type": "integer"},
            },
        }

        errors = published_schema_validation._validate_json_schema_instance(
            {"x-count": "wrong"},
            schema,
            "docs-index.json",
        )

        self.assertIn(
            "docs-index.json.x-count: expected integer, got str",
            errors,
        )

    def test_validate_against_published_artifact_schema_reports_invalid_schema_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            schema_dir = Path(tmp)
            (schema_dir / "docs-index.schema.json").write_text("{not json}", encoding="utf-8")

            errors = published_schema_validation.validate_against_published_artifact_schema(
                {},
                "docs-index.json",
                schema_dir,
            )

        self.assertEqual(len(errors), 1)
        self.assertIn("published schema file is invalid JSON", errors[0])

    def test_load_published_artifact_schema_returns_none_for_unknown_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            schema = published_schema_validation.load_published_artifact_schema(
                "unknown.json",
                Path(tmp),
            )

        self.assertIsNone(schema)

    def test_manifest_json_is_intentionally_excluded_from_published_artifact_schemas(self):
        self.assertNotIn(
            "manifest.json",
            published_schema_validation.PUBLISHED_ARTIFACT_SCHEMAS,
        )

        with tempfile.TemporaryDirectory() as tmp:
            schema = published_schema_validation.load_published_artifact_schema(
                "manifest.json",
                Path(tmp),
            )

        self.assertIsNone(schema)

    def test_validate_against_published_artifact_schema_validates_additional_properties_dict(self):
        with tempfile.TemporaryDirectory() as tmp:
            schema_dir = Path(tmp)
            (schema_dir / "docs-index.schema.json").write_text(
                json.dumps(
                    {
                        "type": "object",
                        "additionalProperties": {"type": "integer"},
                    }
                ),
                encoding="utf-8",
            )

            errors = published_schema_validation.validate_against_published_artifact_schema(
                {"count": "wrong"},
                "docs-index.json",
                schema_dir,
            )

        self.assertEqual(
            errors,
            [
                "docs-index.json: published schema violation: docs-index.json.count: expected integer, got str"
            ],
        )

    def test_validate_json_schema_instance_checks_required_fields_across_nesting(self):
        """Nested required-fields enforcement should span multiple levels."""
        schema = {
            "type": "object",
            "required": ["info"],
            "properties": {
                "info": {
                    "type": "object",
                    "required": ["name", "count"],
                    "properties": {
                        "name": {"type": "string"},
                        "count": {"type": "integer"},
                    },
                    "additionalProperties": False,
                },
            },
        }

        errors = published_schema_validation._validate_json_schema_instance(
            {"info": {"count": 5}},
            schema,
            "tools.json",
        )

        self.assertIn("tools.json.info: missing required key 'name'", errors)


if __name__ == "__main__":
    unittest.main()
