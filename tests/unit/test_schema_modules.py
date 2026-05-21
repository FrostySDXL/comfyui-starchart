from __future__ import annotations

import unittest

from scripts.verify import (
    schema_common,
    schema_community,
    schema_hooks,
    schema_node_api,
    schema_server,
)


class SchemaModuleImportTests(unittest.TestCase):
    def test_schema_common_import_and_top_level_validation(self):
        errors = schema_common.validate_top_level(
            {"metadata": {}, "coverage": {}, "endpoints": []},
            schema_common.SCHEMAS["server_endpoints.json"],
            "server_endpoints.json",
        )
        self.assertEqual(errors, [])

    def test_schema_server_validate_endpoints_accepts_minimal_entry(self):
        data = {
            "endpoints": [
                {
                    "route": "/prompt",
                    "method": "POST",
                    "description": "Queue prompt",
                    "parameters": [],
                    "returns": {
                        "kind": "json",
                        "summary": "ok",
                        "status_codes": [200],
                        "fields": [],
                        "notes": [],
                    },
                }
            ]
        }
        self.assertEqual(schema_server.validate_endpoints(data, "server_endpoints.json"), [])

    def test_schema_hooks_validate_hooks_accepts_minimal_entry(self):
        data = {
            "hooks": [
                {
                    "name": "setup",
                    "type": "app_lifecycle",
                    "description": "Setup hook",
                    "defined_in": "references/snapshots/comfy.ts",
                    "invoked_in": ["references/snapshots/app.ts"],
                }
            ]
        }
        self.assertEqual(schema_hooks.validate_hooks(data, "js_hooks.json"), [])

    def test_schema_node_api_validate_object_info_runtime_accepts_dict(self):
        data = {"object_info": {"KSampler": {"input": {}}}}
        self.assertEqual(
            schema_node_api.validate_object_info_runtime(data, "object_info_runtime.json"), []
        )

    def test_schema_community_validate_pages_accepts_minimal_entry(self):
        data = {
            "pages": [
                {
                    "page_path": "src/content/docs/example.md",
                    "page_kind": "hand_authored_policy",
                    "evidence_label": "Operational guidance",
                    "source_type": "repo_local",
                    "last_verified": "2026-05-20",
                    "needs_review_after": "2026-06-20",
                    "maintenance_tier": "maintainer",
                }
            ]
        }
        self.assertEqual(schema_community.validate_pages(data, "community_pages.json"), [])
