"""Focused comparison tests for delta-summary semantic normalization."""

import unittest
from pathlib import Path

from scripts.generate.generate_snapshot_delta_summary import build_delta_summary
from scripts.verify import published_schema_validation

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLISHED_SCHEMA_DIR = REPO_ROOT / "public" / "artifacts" / "schemas"


def _artifacts_with_hooks(*hooks: dict) -> dict[str, dict]:
    return {
        "server_endpoints.json": {"endpoints": []},
        "js_hooks.json": {"hooks": list(hooks)},
        "node_api_schema.json": {
            "object_info_fields": [],
            "io_types": [],
            "typed_input_shapes": {},
        },
        "websocket_events.json": {"events": [], "binary_events": []},
    }


def _artifacts_with_node_schema(*, io_types=None, typed_input_shapes=None) -> dict[str, dict]:
    return {
        "server_endpoints.json": {"endpoints": []},
        "js_hooks.json": {"hooks": []},
        "node_api_schema.json": {
            "object_info_fields": [],
            "io_types": list(io_types or []),
            "typed_input_shapes": dict(typed_input_shapes or {}),
        },
        "websocket_events.json": {"events": [], "binary_events": []},
    }


class DeltaSummaryComparisonTests(unittest.TestCase):
    def assert_default_comparison(self, summary: dict, old: str = "old", new: str = "new") -> None:
        comparison = summary["comparison"]
        self.assertEqual(comparison["old"], old)
        self.assertEqual(comparison["new"], new)
        self.assertIsInstance(comparison["methodology"], str)
        self.assertNotEqual(comparison["methodology"], "")

    def test_provenance_only_hook_path_drift_does_not_count_as_changed(self):
        old_artifacts = _artifacts_with_hooks(
            {
                "name": "setup",
                "type": "app_lifecycle",
                "description": "Run setup work.",
                "defined_in": "references/snapshots/2026-04-30/comfyui-frontend-v1.44.13/src/types/comfy.ts",
                "invoked_in": [
                    "references/snapshots/2026-04-30/comfyui-frontend-v1.44.13/src/scripts/app.ts"
                ],
                "signature": "setup?(app: ComfyApp): Promise<void> | void",
                "arguments": [{"name": "app", "type_hint": "ComfyApp"}],
                "return_type": "Promise<void> | void",
                "invocation_style": ["async"],
                "traceability": {"source_type": "source-backed", "strategy": "typed_definition"},
            }
        )
        new_artifacts = _artifacts_with_hooks(
            {
                "name": "setup",
                "type": "app_lifecycle",
                "description": "Run setup work.",
                "defined_in": "references/snapshots/2026-05-18/comfyui-frontend-v1.45.9/src/types/comfy.ts",
                "invoked_in": [
                    "references/snapshots/2026-05-18/comfyui-frontend-v1.45.9/src/scripts/app.ts"
                ],
                "signature": "setup?(app: ComfyApp): Promise<void> | void",
                "arguments": [{"name": "app", "type_hint": "ComfyApp"}],
                "return_type": "Promise<void> | void",
                "invocation_style": ["async"],
                "traceability": {"source_type": "source-backed", "strategy": "typed_definition"},
            }
        )

        summary = build_delta_summary(old_artifacts, new_artifacts, "old", "new")

        self.assert_default_comparison(summary)
        self.assertEqual(summary["artifacts"]["js_hooks"]["changed"], [])

    def test_semantic_hook_changes_still_count_as_changed(self):
        old_artifacts = _artifacts_with_hooks(
            {
                "name": "setup",
                "type": "app_lifecycle",
                "description": "Run setup work.",
                "defined_in": "references/snapshots/2026-04-30/comfyui-frontend-v1.44.13/src/types/comfy.ts",
                "invoked_in": [
                    "references/snapshots/2026-04-30/comfyui-frontend-v1.44.13/src/scripts/app.ts"
                ],
                "signature": "setup?(app: ComfyApp): Promise<void> | void",
                "arguments": [{"name": "app", "type_hint": "ComfyApp"}],
                "return_type": "Promise<void> | void",
                "invocation_style": ["async"],
                "traceability": {"source_type": "source-backed", "strategy": "typed_definition"},
            }
        )
        new_artifacts = _artifacts_with_hooks(
            {
                "name": "setup",
                "type": "app_lifecycle",
                "description": "Run setup work after node definitions load.",
                "defined_in": "references/snapshots/2026-05-18/comfyui-frontend-v1.45.9/src/types/comfy.ts",
                "invoked_in": [
                    "references/snapshots/2026-05-18/comfyui-frontend-v1.45.9/src/scripts/app.ts"
                ],
                "signature": "setup?(app: ComfyApp, mode: string): Promise<void> | void",
                "arguments": [
                    {"name": "app", "type_hint": "ComfyApp"},
                    {"name": "mode", "type_hint": "string"},
                ],
                "return_type": "Promise<void> | void",
                "invocation_style": ["async"],
                "traceability": {"source_type": "source-backed", "strategy": "typed_definition"},
            }
        )

        summary = build_delta_summary(old_artifacts, new_artifacts, "old", "new")

        self.assert_default_comparison(summary)
        self.assertEqual(summary["artifacts"]["js_hooks"]["changed"], ["setup"])

    def test_meaningful_hook_location_change_still_counts_as_changed(self):
        old_artifacts = _artifacts_with_hooks(
            {
                "name": "setup",
                "type": "app_lifecycle",
                "description": "Run setup work.",
                "defined_in": "references/snapshots/2026-04-30/comfyui-frontend-v1.44.13/src/types/comfy.ts",
                "invoked_in": [
                    "references/snapshots/2026-04-30/comfyui-frontend-v1.44.13/src/scripts/app.ts"
                ],
                "signature": "setup?(app: ComfyApp): Promise<void> | void",
                "arguments": [{"name": "app", "type_hint": "ComfyApp"}],
                "return_type": "Promise<void> | void",
                "invocation_style": ["async"],
                "traceability": {"source_type": "source-backed", "strategy": "typed_definition"},
            }
        )
        new_artifacts = _artifacts_with_hooks(
            {
                "name": "setup",
                "type": "app_lifecycle",
                "description": "Run setup work.",
                "defined_in": "references/snapshots/2026-05-18/comfyui-frontend-v1.45.9/src/types/comfy.ts",
                "invoked_in": [
                    "references/snapshots/2026-05-18/comfyui-frontend-v1.45.9/src/services/litegraphService.ts"
                ],
                "signature": "setup?(app: ComfyApp): Promise<void> | void",
                "arguments": [{"name": "app", "type_hint": "ComfyApp"}],
                "return_type": "Promise<void> | void",
                "invocation_style": ["async"],
                "traceability": {"source_type": "source-backed", "strategy": "typed_definition"},
            }
        )

        summary = build_delta_summary(old_artifacts, new_artifacts, "old", "new")

        self.assert_default_comparison(summary)
        self.assertEqual(summary["artifacts"]["js_hooks"]["changed"], ["setup"])

    def test_provenance_only_io_type_path_drift_does_not_count_as_changed(self):
        old_artifacts = _artifacts_with_node_schema(
            io_types=[
                {
                    "io_type": "BACKGROUND_REMOVAL",
                    "class_name": "BackgroundRemoval",
                    "input_class": None,
                    "input_parameters": [],
                    "output_parameters": [],
                    "input_parameter_details": [],
                    "output_parameter_details": [],
                    "type_hint": "BackgroundRemovalModel",
                    "defined_in": "references/snapshots/2026-05-18/comfyui-core-v0.21.1/comfy_api/latest/_io.py",
                    "is_widget": False,
                }
            ]
        )
        new_artifacts = _artifacts_with_node_schema(
            io_types=[
                {
                    "io_type": "BACKGROUND_REMOVAL",
                    "class_name": "BackgroundRemoval",
                    "input_class": None,
                    "input_parameters": [],
                    "output_parameters": [],
                    "input_parameter_details": [],
                    "output_parameter_details": [],
                    "type_hint": "BackgroundRemovalModel",
                    "defined_in": "references/snapshots/2026-05-21/comfyui-core-v0.22.0/comfy_api/latest/_io.py",
                    "is_widget": False,
                }
            ]
        )

        summary = build_delta_summary(old_artifacts, new_artifacts, "old", "new")

        self.assert_default_comparison(summary)
        self.assertEqual(summary["artifacts"]["node_api_schema"]["io_types"]["changed"], [])

    def test_semantic_io_type_change_still_counts_as_changed(self):
        old_artifacts = _artifacts_with_node_schema(
            io_types=[
                {
                    "io_type": "BACKGROUND_REMOVAL",
                    "class_name": "BackgroundRemoval",
                    "input_class": None,
                    "input_parameters": [],
                    "output_parameters": [],
                    "input_parameter_details": [],
                    "output_parameter_details": [],
                    "type_hint": "BackgroundRemovalModel",
                    "defined_in": "references/snapshots/2026-05-18/comfyui-core-v0.21.1/comfy_api/latest/_io.py",
                    "is_widget": False,
                }
            ]
        )
        new_artifacts = _artifacts_with_node_schema(
            io_types=[
                {
                    "io_type": "BACKGROUND_REMOVAL",
                    "class_name": "BackgroundRemoval",
                    "input_class": None,
                    "input_parameters": [],
                    "output_parameters": [],
                    "input_parameter_details": [],
                    "output_parameter_details": [],
                    "type_hint": "BackgroundRemovalModelV2",
                    "defined_in": "references/snapshots/2026-05-21/comfyui-core-v0.22.0/comfy_api/latest/_io.py",
                    "is_widget": False,
                }
            ]
        )

        summary = build_delta_summary(old_artifacts, new_artifacts, "old", "new")

        self.assert_default_comparison(summary)
        self.assertEqual(
            summary["artifacts"]["node_api_schema"]["io_types"]["changed"],
            ["BACKGROUND_REMOVAL:BackgroundRemoval"],
        )

    def test_provenance_only_typed_input_shape_path_drift_does_not_count_as_changed(self):
        old_artifacts = _artifacts_with_node_schema(
            typed_input_shapes={
                "AudioInput": {
                    "description": "TypedDict representing audio input.",
                    "defined_in": "references/snapshots/2026-05-18/comfyui-core-v0.21.1/comfy_api/latest/_input/basic_types.py",
                    "fields": {
                        "sample_rate": {
                            "type": "int",
                            "traceability": {
                                "source_type": "source-backed",
                                "strategy": "typed_dict_field",
                            },
                        }
                    },
                }
            }
        )
        new_artifacts = _artifacts_with_node_schema(
            typed_input_shapes={
                "AudioInput": {
                    "description": "TypedDict representing audio input.",
                    "defined_in": "references/snapshots/2026-05-21/comfyui-core-v0.22.0/comfy_api/latest/_input/basic_types.py",
                    "fields": {
                        "sample_rate": {
                            "type": "int",
                            "traceability": {
                                "source_type": "source-backed",
                                "strategy": "typed_dict_field",
                            },
                        }
                    },
                }
            }
        )

        summary = build_delta_summary(old_artifacts, new_artifacts, "old", "new")

        self.assert_default_comparison(summary)
        self.assertEqual(
            summary["artifacts"]["node_api_schema"]["typed_input_shapes"]["changed"],
            [],
        )


class TestComparisonSchemaClosure(unittest.TestCase):
    def _summary(self) -> dict:
        return build_delta_summary(
            _artifacts_with_hooks(),
            _artifacts_with_hooks(),
            "old",
            "new",
        )

    def _schema_errors(self, summary: dict) -> list[str]:
        return published_schema_validation.validate_against_published_artifact_schema(
            summary,
            "delta-summary.json",
            PUBLISHED_SCHEMA_DIR,
        )

    def test_comparison_closure_rejects_undeclared_field(self):
        summary = self._summary()
        summary["comparison"]["methodology_version"] = "1.1"

        errors = self._schema_errors(summary)

        self.assertTrue(
            any("comparison: unexpected key 'methodology_version'" in e for e in errors)
        )

    def test_comparison_closure_rejects_missing_methodology(self):
        summary = self._summary()
        del summary["comparison"]["methodology"]

        errors = self._schema_errors(summary)

        self.assertTrue(any("comparison: missing required key 'methodology'" in e for e in errors))

    def test_comparison_closure_accepts_optional_fields_absent(self):
        summary = self._summary()

        errors = self._schema_errors(summary)

        self.assertEqual(errors, [])

    def test_comparison_closure_accepts_all_fields_present(self):
        summary = build_delta_summary(
            _artifacts_with_hooks(),
            _artifacts_with_hooks(),
            "references/_refresh_backups/raw_20260603T183637Z",
            "references/raw",
            source_kind="pre_refresh_backup_vs_current_raw",
            comparison_old_label="raw backup 2026-06-03T18:36:37Z",
            comparison_new_label="current raw (extracted 2026-06-04)",
        )

        errors = self._schema_errors(summary)

        self.assertEqual(errors, [])
        self.assertEqual(summary["comparison"]["source_kind"], "pre_refresh_backup_vs_current_raw")
        self.assertEqual(summary["comparison"]["old_label"], "raw backup 2026-06-03T18:36:37Z")
        self.assertEqual(summary["comparison"]["new_label"], "current raw (extracted 2026-06-04)")


if __name__ == "__main__":
    unittest.main()
