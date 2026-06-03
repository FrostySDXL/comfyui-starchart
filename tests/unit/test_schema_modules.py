from __future__ import annotations

import unittest
from pathlib import Path

from scripts.verify import (
    published_schema_validation,
    schema_common,
    schema_hooks,
    schema_node_api,
    schema_server,
)


class SchemaModuleImportTests(unittest.TestCase):
    def test_schema_common_import_and_top_level_validation(self):
        errors = schema_common.validate_top_level(
            {
                "metadata": {},
                "coverage": {},
                "endpoints": [],
                "prompt_submission_contract": {
                    "request_fields": [],
                    "success_response_fields": [],
                    "error_response_fields": [],
                },
                "prompt_validation_errors": {"error_types": []},
                "queue_history_contract": {"sections": []},
            },
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

    def test_published_schema_validation_accepts_minimal_docs_index_page(self):
        data = {
            "artifact": "docs-index.json",
            "artifact_schema_version": "1.1.0",
            "scope": {"surface": "test", "excludes": []},
            "pages": [
                {
                    "title": "Prompt Submission",
                    "path": "api/prompt-submission.md",
                    "nav_section": "API Reference",
                    "audience": None,
                    "evidence": "Source-backed from pinned snapshots",
                    "summary": "Prompt summary.",
                }
            ],
        }
        errors = published_schema_validation.validate_against_published_artifact_schema(
            data,
            "docs-index.json",
            Path("public/artifacts/schemas"),
        )
        self.assertEqual(errors, [])
