"""Focused comparison tests for delta-summary semantic normalization."""

import unittest

from scripts.generate.generate_snapshot_delta_summary import build_delta_summary


def _artifacts_with_hooks(*hooks: dict) -> dict[str, dict]:
    return {
        "server_endpoints.json": {"endpoints": []},
        "js_hooks.json": {"hooks": list(hooks)},
        "node_api_schema.json": {
            "object_info_fields": [],
            "io_types": [],
            "typed_input_shapes": {},
        },
    }


class DeltaSummaryComparisonTests(unittest.TestCase):
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

        self.assertEqual(summary["artifacts"]["js_hooks"]["changed"], ["setup"])


if __name__ == "__main__":
    unittest.main()
