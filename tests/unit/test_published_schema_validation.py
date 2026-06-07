from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.verify import published_schema_validation

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLISHED_SCHEMA_DIR = REPO_ROOT / "public" / "artifacts" / "schemas"


def valid_delta_summary_payload() -> dict:
    block = {"old_count": 1, "new_count": 1, "added": [], "removed": [], "changed": []}
    return {
        "comparison": {
            "old": "references/old",
            "new": "references/raw",
            "methodology": "artifact-directory-to-artifact-directory",
        },
        "notes": [],
        "artifacts": {
            "server_endpoints": dict(block),
            "js_hooks": dict(block),
            "node_api_schema": {
                "object_info_fields": dict(block),
                "io_types": dict(block),
                "typed_input_shapes": dict(block),
                "prompt_conditioning_surface": {
                    "text_input_io_types": dict(block),
                    "conditioning_io_types": dict(block),
                },
                "basic_input_shapes": dict(block),
            },
            "websocket_events": {
                "events": dict(block),
                "binary_events": dict(block),
            },
        },
    }


def valid_manifest_payload() -> dict:
    schema_names = [
        "server_endpoints.json",
        "js_hooks.json",
        "node_api_schema.json",
        "websocket_events.json",
    ]
    return {
        "artifact_schema_version": "1.0.0",
        "version_key": "core-v0.23.0_frontend-v1.46.6_2026-06-03",
        "schemas": {
            name: {"schema_url": f"artifacts/schemas/{name.removesuffix('.json')}.schema.json"}
            for name in schema_names
        },
        "artifacts": {
            name: {
                "current_url": f"artifacts/current/{name}",
                "versioned_url": f"artifacts/versions/test/{name}",
                "sha256": "a" * 64,
                "version": "v0.23.0",
                "commit": "a88e02b18576283b1ff25a4b564548c5dc42cbf6",
                "extracted_date": "2026-06-04",
                "sources": ["references/snapshots/source.py"],
            }
            for name in schema_names
        },
    }


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
        payload = valid_delta_summary_payload()
        payload["artifacts"]["node_api_schema"]["io_types"]["new_count"] = "wrong"

        errors = published_schema_validation.validate_against_published_artifact_schema(
            payload,
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

    def test_validate_json_schema_instance_resolves_local_defs_ref(self):
        schema = {
            "$defs": {"name": {"type": "string"}},
            "type": "object",
            "properties": {"name": {"$ref": "#/$defs/name"}},
        }

        errors = published_schema_validation._validate_json_schema_instance(
            {"name": 1},
            schema,
            "sample.json",
        )

        self.assertIn("sample.json.name: expected string, got int", errors)

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

    def test_manifest_json_is_included_in_published_artifact_schemas(self):
        self.assertEqual(
            published_schema_validation.PUBLISHED_ARTIFACT_SCHEMAS["manifest.json"],
            "manifest.schema.json",
        )

        schema = published_schema_validation.load_published_artifact_schema(
            "manifest.json",
            PUBLISHED_SCHEMA_DIR,
        )

        self.assertIsNotNone(schema)
        self.assertEqual(schema["title"], "ComfyUI StarChart manifest support artifact")

    def test_manifest_json_valid_payload_passes_published_schema(self):
        errors = published_schema_validation.validate_against_published_artifact_schema(
            valid_manifest_payload(),
            "manifest.json",
            PUBLISHED_SCHEMA_DIR,
        )

        self.assertEqual(errors, [])

    def test_manifest_json_malformed_entry_fails_published_schema(self):
        payload = valid_manifest_payload()
        payload["artifacts"]["server_endpoints.json"]["sha256"] = "not-hex"

        errors = published_schema_validation.validate_against_published_artifact_schema(
            payload,
            "manifest.json",
            PUBLISHED_SCHEMA_DIR,
        )

        self.assertTrue(any("does not match pattern" in e for e in errors))

    def test_manifest_json_artifacts_closure_rejects_future_artifact(self):
        payload = valid_manifest_payload()
        payload["artifacts"]["future_artifact"] = {}

        errors = published_schema_validation.validate_against_published_artifact_schema(
            payload,
            "manifest.json",
            PUBLISHED_SCHEMA_DIR,
        )

        self.assertTrue(any("artifacts: unexpected key 'future_artifact'" in e for e in errors))

    def test_delta_summary_missing_websocket_events_is_rejected(self):
        payload = valid_delta_summary_payload()
        del payload["artifacts"]["websocket_events"]

        errors = published_schema_validation.validate_against_published_artifact_schema(
            payload,
            "delta-summary.json",
            PUBLISHED_SCHEMA_DIR,
        )

        self.assertTrue(any("missing required key 'websocket_events'" in e for e in errors))

    def test_delta_summary_current_emitted_shape_is_accepted(self):
        payload = json.loads(
            (REPO_ROOT / "public" / "artifacts" / "delta-summary.json").read_text()
        )
        payload["comparison"]["methodology"] = "artifact-directory-to-artifact-directory"

        errors = published_schema_validation.validate_against_published_artifact_schema(
            payload,
            "delta-summary.json",
            PUBLISHED_SCHEMA_DIR,
        )

        self.assertEqual(errors, [])

    def test_delta_summary_artifacts_closure_rejects_extra_section(self):
        payload = valid_delta_summary_payload()
        payload["artifacts"]["extra_section"] = {}

        errors = published_schema_validation.validate_against_published_artifact_schema(
            payload,
            "delta-summary.json",
            PUBLISHED_SCHEMA_DIR,
        )

        self.assertTrue(any("artifacts: unexpected key 'extra_section'" in e for e in errors))

    def test_delta_summary_node_api_schema_closure_rejects_extra_field(self):
        payload = valid_delta_summary_payload()
        payload["artifacts"]["node_api_schema"]["totally_new_field"] = {}

        errors = published_schema_validation.validate_against_published_artifact_schema(
            payload,
            "delta-summary.json",
            PUBLISHED_SCHEMA_DIR,
        )

        self.assertTrue(
            any("node_api_schema: unexpected key 'totally_new_field'" in e for e in errors)
        )


class TestComparisonSchemaClosure(unittest.TestCase):
    def test_comparison_closure_rejects_undeclared_field(self):
        payload = valid_delta_summary_payload()
        payload["comparison"]["methodology_version"] = "1.1"

        errors = published_schema_validation.validate_against_published_artifact_schema(
            payload,
            "delta-summary.json",
            PUBLISHED_SCHEMA_DIR,
        )

        self.assertTrue(
            any("comparison: unexpected key 'methodology_version'" in e for e in errors)
        )

    def test_comparison_closure_rejects_missing_methodology(self):
        payload = valid_delta_summary_payload()
        del payload["comparison"]["methodology"]

        errors = published_schema_validation.validate_against_published_artifact_schema(
            payload,
            "delta-summary.json",
            PUBLISHED_SCHEMA_DIR,
        )

        self.assertTrue(any("comparison: missing required key 'methodology'" in e for e in errors))

    def test_comparison_closure_accepts_optional_fields_absent(self):
        payload = valid_delta_summary_payload()

        errors = published_schema_validation.validate_against_published_artifact_schema(
            payload,
            "delta-summary.json",
            PUBLISHED_SCHEMA_DIR,
        )

        self.assertEqual(errors, [])

    def test_comparison_closure_accepts_all_fields_present(self):
        payload = valid_delta_summary_payload()
        payload["comparison"].update(
            {
                "source_kind": "pre_refresh_backup_vs_current_raw",
                "old_label": "raw backup 2026-06-03T18:36:37Z",
                "new_label": "current raw (extracted 2026-06-04)",
            }
        )

        errors = published_schema_validation.validate_against_published_artifact_schema(
            payload,
            "delta-summary.json",
            PUBLISHED_SCHEMA_DIR,
        )

        self.assertEqual(errors, [])

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
