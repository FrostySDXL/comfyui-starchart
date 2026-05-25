from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.verify import published_schema_validation


class PublishedSchemaValidationTests(unittest.TestCase):
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
