"""Tests for scripts/verify/validate_schema.py."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "validate_schema.py"


class ValidateSchemaUnitTests(unittest.TestCase):
    """Direct unit tests for validation functions."""

    def _import_module(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("validate_schema", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _server_coverage(self):
        return {
            "description": "Static extraction of ComfyUI HTTP and WebSocket endpoint structure.",
            "guaranteed_fields": [
                "endpoints[].route",
                "endpoints[].method",
                "endpoints[].returns.kind",
                "endpoints[].returns.status_codes",
            ],
            "best_effort_fields": [
                "endpoints[].description",
                "endpoints[].parameters",
                "endpoints[].returns.summary",
                "endpoints[].returns.fields",
            ],
            "deferred": [
                "parameter typing",
                "richer error contracts",
                "variable-return response-body fidelity",
            ],
        }

    def _valid_server_endpoints_data(self):
        return {
            "metadata": {
                "sources": ["references/snapshots/server.py"],
                "extracted_date": "2026-04-22",
                "version": "v0.19.3",
                "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
            },
            "coverage": self._server_coverage(),
            "endpoints": [
                {
                    "route": "/prompt",
                    "method": "POST",
                    "description": "Queue a prompt.",
                    "parameters": [
                        {
                            "name": "client_id",
                            "location": "query",
                            "required": False,
                            "default": "",
                            "traceability": {
                                "source_type": "source-backed",
                                "strategy": "request.rel_url.query.get",
                            },
                        }
                    ],
                    "returns": {
                        "kind": "json",
                        "summary": "Prompt queued with ID and any node errors.",
                        "status_codes": [200, 400],
                        "fields": [
                            {"name": "prompt_id", "type_hint": "str", "description": "UUID of the queued prompt"},
                            {"name": "number", "type_hint": "int"},
                            {"name": "node_errors", "type_hint": "dict"},
                        ],
                        "notes": ["Returns 400 for validation failures."],
                        "traceability": {
                            "source_type": "source-backed",
                            "strategy": "web.json_response",
                        },
                    },
                },
                {
                    "route": "/ws",
                    "method": "GET",
                    "description": "WebSocket stream.",
                    "parameters": [],
                    "returns": {
                        "kind": "websocket",
                        "summary": "Upgraded WebSocket connection.",
                        "status_codes": [101],
                        "fields": [],
                        "notes": [],
                    },
                },
            ],
        }

    def _valid_js_hooks_data(self):
        return {
            "metadata": {
                "sources": ["references/snapshots/comfy.ts"],
                "extracted_date": "2026-04-29",
                "version": "v1.42.11",
                "commit": "abc123",
            },
            "coverage": {
                "description": "Static extraction of hooks.",
                "guaranteed_fields": ["hooks[].name"],
                "best_effort_fields": ["hooks[].description"],
                "deferred": ["runtime-only hook behavior"],
            },
            "hooks": [
                {
                    "name": "setup",
                    "type": "app_lifecycle",
                    "description": "Setup hook.",
                    "defined_in": "references/snapshots/comfy.ts",
                    "invoked_in": ["references/snapshots/app.ts"],
                    "signature": "setup?(app: ComfyApp): Promise<void> | void",
                    "arguments": [{"name": "app", "type_hint": "ComfyApp"}],
                    "return_type": "Promise<void> | void",
                    "invocation_style": ["async"],
                    "traceability": {
                        "source_type": "source-backed",
                        "strategy": "typed_definition",
                    },
                }
            ],
        }

    def _valid_node_api_schema_data(self):
        return {
            "metadata": {
                "sources": ["references/snapshots/server.py"],
                "extracted_date": "2026-04-22",
                "version": "v0.19.3",
                "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
            },
            "object_info_fields": ["input", "output"],
            "io_types": [
                {
                    "io_type": "BOOLEAN",
                    "class_name": "Boolean",
                    "input_class": "WidgetInput",
                    "input_parameters": ["default"],
                    "input_parameter_details": [
                        {
                            "name": "default",
                            "location": "input_signature",
                            "default": None,
                            "traceability": {
                                "source_type": "source-backed",
                                "strategy": "python_signature",
                            },
                        }
                    ],
                }
            ],
            "basic_input_shapes": {"ImageInput": "An image tensor."},
            "typed_input_shapes": {
                "AudioInput": {
                    "description": "TypedDict representing audio input.",
                    "defined_in": "references/snapshots/basic_types.py",
                    "fields": {
                        "waveform": {
                            "type": "torch.Tensor",
                            "traceability": {
                                "source_type": "source-backed",
                                "strategy": "typed_dict_field",
                            },
                        }
                    },
                }
            },
            "coverage": {
                "description": "Static and optional runtime coverage for object_info and IO typing.",
                "sources_covered": ["object_info_fields", "io_types", "basic_input_shapes"],
                "runtime_enriched": False,
                "deferred": ["runtime-only object_info details"],
            },
        }

    def test_valid_server_endpoints_pass(self):
        module = self._import_module()
        data = self._valid_server_endpoints_data()
        errors = module.validate_top_level(data, module.SCHEMAS["server_endpoints.json"], "server_endpoints.json")
        errors.extend(module.validate_metadata(data, "server_endpoints.json"))
        errors.extend(module.validate_coverage(data, "server_endpoints.json"))
        errors.extend(module.validate_endpoints(data, "server_endpoints.json"))
        self.assertEqual(errors, [])

    def test_valid_server_endpoints_pass_published_schema(self):
        module = self._import_module()
        errors = module.validate_against_published_artifact_schema(
            self._valid_server_endpoints_data(),
            "server_endpoints.json",
        )
        self.assertEqual(errors, [])

    def test_published_server_schema_rejects_missing_guaranteed_field(self):
        module = self._import_module()
        data = self._valid_server_endpoints_data()
        del data["endpoints"][0]["route"]
        errors = module.validate_against_published_artifact_schema(data, "server_endpoints.json")
        self.assertTrue(any("missing required key 'route'" in e for e in errors))

    def test_server_endpoints_rejects_singular_metadata_source(self):
        module = self._import_module()
        data = self._valid_server_endpoints_data()
        data["metadata"] = {
            "source": "references/snapshots/server.py",
            "extracted_date": "2026-04-22",
            "version": "v0.19.3",
            "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
        }
        errors = module.validate_metadata(data, "server_endpoints.json")
        self.assertTrue(any("missing required field 'sources'" in e for e in errors))

    def test_server_endpoints_rejects_non_list_sources(self):
        module = self._import_module()
        data = self._valid_server_endpoints_data()
        data["metadata"]["sources"] = "references/snapshots/server.py"
        errors = module.validate_metadata(data, "server_endpoints.json")
        self.assertTrue(any("metadata.sources expected list" in e for e in errors))

    def test_server_endpoints_rejects_missing_coverage(self):
        module = self._import_module()
        data = self._valid_server_endpoints_data()
        del data["coverage"]
        errors = module.validate_top_level(data, module.SCHEMAS["server_endpoints.json"], "server_endpoints.json")
        self.assertTrue(any("missing required key 'coverage'" in e for e in errors))

    def test_server_endpoints_rejects_invalid_coverage_shape(self):
        module = self._import_module()
        data = self._valid_server_endpoints_data()
        data["coverage"] = {
            "description": "bad",
            "guaranteed_fields": "endpoints[].route",
            "best_effort_fields": [],
            "deferred": [],
        }
        errors = module.validate_coverage(data, "server_endpoints.json")
        self.assertTrue(any("coverage.guaranteed_fields expected list" in e for e in errors))

    def test_malformed_returns_missing_kind_fails(self):
        module = self._import_module()
        data = self._valid_server_endpoints_data()
        data["endpoints"] = [
            {
                "route": "/prompt",
                "method": "POST",
                "description": "Queue a prompt.",
                "parameters": [],
                "returns": {
                    "summary": "missing kind",
                    "status_codes": [],
                    "fields": [],
                    "notes": [],
                },
            }
        ]
        errors = module.validate_endpoints(data, "server_endpoints.json")
        self.assertTrue(any("missing required key 'kind'" in e for e in errors))

    def test_malformed_returns_status_codes_not_int_fails(self):
        module = self._import_module()
        data = self._valid_server_endpoints_data()
        data["endpoints"] = [
            {
                "route": "/prompt",
                "method": "POST",
                "description": "Queue a prompt.",
                "parameters": [],
                "returns": {
                    "kind": "json",
                    "summary": "ok",
                    "status_codes": [200, "400"],
                    "fields": [],
                    "notes": [],
                },
            }
        ]
        errors = module.validate_endpoints(data, "server_endpoints.json")
        self.assertTrue(any("status_codes[1] expected int" in e for e in errors))

    def test_malformed_returns_field_missing_name_fails(self):
        module = self._import_module()
        data = self._valid_server_endpoints_data()
        data["endpoints"] = [
            {
                "route": "/prompt",
                "method": "POST",
                "description": "Queue a prompt.",
                "parameters": [],
                "returns": {
                    "kind": "json",
                    "summary": "ok",
                    "status_codes": [200],
                    "fields": [{"type_hint": "str"}],
                    "notes": [],
                },
            }
        ]
        errors = module.validate_endpoints(data, "server_endpoints.json")
        self.assertTrue(any("fields[0] missing required key 'name'" in e for e in errors))

    def test_legacy_string_returns_are_rejected(self):
        """String returns are no longer accepted; structured dict is required."""
        module = self._import_module()
        data = self._valid_server_endpoints_data()
        data["endpoints"] = [
            {
                "route": "/prompt",
                "method": "POST",
                "description": "Queue a prompt.",
                "parameters": [],
                "returns": "TODO",
            }
        ]
        errors = module.validate_endpoints(data, "server_endpoints.json")
        self.assertTrue(any("expected dict" in e for e in errors))

    def test_valid_node_api_schema_passes(self):
        module = self._import_module()
        data = self._valid_node_api_schema_data()
        errors = module.validate_top_level(data, module.SCHEMAS["node_api_schema.json"], "node_api_schema.json")
        errors.extend(module.validate_metadata(data, "node_api_schema.json"))
        errors.extend(module.validate_coverage(data, "node_api_schema.json"))
        errors.extend(module.validate_io_types(data, "node_api_schema.json"))
        errors.extend(module.validate_typed_input_shapes(data, "node_api_schema.json"))
        self.assertEqual(errors, [])

    def test_endpoint_parameter_rejects_invalid_allowed_values(self):
        module = self._import_module()
        data = self._valid_server_endpoints_data()
        data["endpoints"][0]["parameters"][0]["allowed_values"] = [{"bad": True}]
        errors = module.validate_endpoints(data, "server_endpoints.json")
        self.assertTrue(any("allowed_values[0] expected primitive" in e for e in errors))

    def test_hook_enrichment_fields_validate(self):
        module = self._import_module()
        data = self._valid_js_hooks_data()
        errors = module.validate_top_level(data, module.SCHEMAS["js_hooks.json"], "js_hooks.json")
        errors.extend(module.validate_metadata(data, "js_hooks.json"))
        errors.extend(module.validate_coverage(data, "js_hooks.json"))
        errors.extend(module.validate_hooks(data, "js_hooks.json"))
        self.assertEqual(errors, [])

    def test_valid_js_hooks_pass_published_schema(self):
        module = self._import_module()
        errors = module.validate_against_published_artifact_schema(
            self._valid_js_hooks_data(),
            "js_hooks.json",
        )
        self.assertEqual(errors, [])

    def test_valid_node_api_schema_pass_published_schema(self):
        module = self._import_module()
        errors = module.validate_against_published_artifact_schema(
            self._valid_node_api_schema_data(),
            "node_api_schema.json",
        )
        self.assertEqual(errors, [])

    def test_typed_input_shapes_rejects_missing_field_type(self):
        module = self._import_module()
        data = {
            "metadata": {
                "sources": ["references/snapshots/server.py"],
                "extracted_date": "2026-04-22",
                "version": "v0.19.3",
                "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
            },
            "object_info_fields": [],
            "io_types": [],
            "basic_input_shapes": {},
            "typed_input_shapes": {
                "AudioInput": {
                    "description": "audio",
                    "fields": {
                        "waveform": {}
                    },
                }
            },
            "coverage": {
                "description": "Static and optional runtime coverage for object_info and IO typing.",
                "sources_covered": ["object_info_fields"],
                "runtime_enriched": False,
                "deferred": [],
            },
        }
        errors = module.validate_typed_input_shapes(data, "node_api_schema.json")
        self.assertTrue(any("missing required key 'type'" in e for e in errors))

    def test_node_api_schema_rejects_missing_coverage(self):
        module = self._import_module()
        data = {
            "metadata": {
                "sources": ["references/snapshots/server.py"],
                "extracted_date": "2026-04-22",
                "version": "v0.19.3",
                "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
            },
            "object_info_fields": ["input", "output"],
            "io_types": [],
            "basic_input_shapes": {},
        }
        errors = module.validate_top_level(data, module.SCHEMAS["node_api_schema.json"], "node_api_schema.json")
        self.assertTrue(any("missing required key 'coverage'" in e for e in errors))

    def test_malformed_io_type_missing_class_name_fails(self):
        module = self._import_module()
        data = {
            "metadata": {
                "sources": ["references/snapshots/_io.py"],
                "extracted_date": "2026-04-22",
                "version": "v0.19.3",
                "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
            },
            "object_info_fields": [],
            "io_types": [
                {
                    "io_type": "BOOLEAN",
                    "input_class": "WidgetInput",
                    "input_parameters": [],
                }
            ],
            "basic_input_shapes": {},
        }
        errors = module.validate_io_types(data, "node_api_schema.json")
        self.assertTrue(any("io_types[0] missing required key 'class_name'" in e for e in errors))

    def test_valid_object_info_runtime_passes(self):
        module = self._import_module()
        data = {
            "metadata": {
                "url": "http://127.0.0.1:8188",
                "extracted_date": "2026-04-22",
                "version": "v0.19.3",
                "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
                "response_sha256": "abc123",
            },
            "object_info": {
                "KSampler": {
                    "input": {},
                    "output": ["LATENT"],
                }
            },
        }
        errors = module.validate_top_level(data, module.SCHEMAS["object_info_runtime.json"], "object_info_runtime.json")
        errors.extend(module.validate_metadata(data, "object_info_runtime.json"))
        errors.extend(module.validate_object_info_runtime(data, "object_info_runtime.json"))
        self.assertEqual(errors, [])

    def test_malformed_object_info_runtime_missing_url_fails(self):
        module = self._import_module()
        data = {
            "metadata": {
                "extracted_date": "2026-04-22",
                "version": "v0.19.3",
                "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
                "response_sha256": "abc123",
            },
            "object_info": {},
        }
        errors = module.validate_metadata(data, "object_info_runtime.json")
        self.assertTrue(any("missing required field 'url'" in e for e in errors))

    def test_malformed_object_info_runtime_non_dict_value_fails(self):
        module = self._import_module()
        data = {
            "metadata": {
                "url": "http://127.0.0.1:8188",
                "extracted_date": "2026-04-22",
                "version": "v0.19.3",
                "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
                "response_sha256": "abc123",
            },
            "object_info": {
                "KSampler": "not-a-dict",
            },
        }
        errors = module.validate_object_info_runtime(data, "object_info_runtime.json")
        self.assertTrue(any("object_info['KSampler'] is not a dict" in e for e in errors))

    def test_valid_ecosystem_packages_pass(self):
        module = self._import_module()
        data = {
            "metadata": {
                "schema_version": "1.0.0",
                "last_updated": "2026-04-23",
                "description": "Test packages",
            },
            "packages": [
                {
                    "slug": "test-pack",
                    "name": "Test Pack",
                    "repo_url": "https://github.com/example/test",
                    "registry_url": None,
                    "category": "node_pack",
                    "status": "Actively Maintained",
                    "role_summary": "A test package",
                    "notable_patterns": ["pattern_a"],
                    "used_by": "Testers",
                    "source_type": "community_observation",
                    "evidence_urls": ["https://github.com/example/test"],
                    "pinned_external_version": None,
                    "pinned_commit": None,
                    "last_verified": "2026-04-22",
                    "needs_review_after": "2026-07-22",
                    "maintenance_tier": "tier_2",
                    "caveats": None,
                }
            ],
        }
        errors = module.validate_top_level(data, module.COMMUNITY_SCHEMAS["ecosystem_packages.json"], "ecosystem_packages.json")
        errors.extend(module.validate_community_metadata(data, "ecosystem_packages.json"))
        errors.extend(module.validate_packages(data, "ecosystem_packages.json"))
        self.assertEqual(errors, [])

    def test_malformed_package_missing_required_key_fails(self):
        module = self._import_module()
        data = {
            "metadata": {
                "schema_version": "1.0.0",
                "last_updated": "2026-04-23",
                "description": "Test packages",
            },
            "packages": [
                {
                    "slug": "test-pack",
                    "name": "Test Pack",
                }
            ],
        }
        errors = module.validate_packages(data, "ecosystem_packages.json")
        self.assertTrue(any("missing required key 'category'" in e for e in errors))

    def test_package_category_enum_is_enforced(self):
        module = self._import_module()
        data = {
            "packages": [
                {
                    "slug": "test-pack",
                    "name": "Test Pack",
                    "repo_url": None,
                    "registry_url": None,
                    "category": "wrong",
                    "status": "Actively Maintained",
                    "role_summary": "A test package",
                    "notable_patterns": [],
                    "used_by": None,
                    "source_type": "community_observation",
                    "evidence_urls": ["https://example.com/test-pack"],
                    "pinned_external_version": None,
                    "pinned_commit": None,
                    "last_verified": "2026-04-22",
                    "needs_review_after": "2026-07-22",
                    "maintenance_tier": "tier_2",
                    "caveats": None,
                }
            ]
        }
        errors = module.validate_packages(data, "ecosystem_packages.json")
        self.assertTrue(any("invalid category 'wrong'" in e for e in errors))

    def test_duplicate_package_slug_is_rejected(self):
        module = self._import_module()
        data = {
            "packages": [
                {
                    "slug": "duplicate-pack",
                    "name": "Test Pack A",
                    "repo_url": None,
                    "registry_url": None,
                    "category": "node_pack",
                    "status": "Actively Maintained",
                    "role_summary": "A test package",
                    "notable_patterns": [],
                    "used_by": None,
                    "source_type": "community_observation",
                    "evidence_urls": ["https://example.com/a"],
                    "pinned_external_version": None,
                    "pinned_commit": None,
                    "last_verified": "2026-04-22",
                    "needs_review_after": "2026-07-22",
                    "maintenance_tier": "tier_2",
                    "caveats": None,
                },
                {
                    "slug": "duplicate-pack",
                    "name": "Test Pack B",
                    "repo_url": None,
                    "registry_url": None,
                    "category": "tooling",
                    "status": "Community Supported",
                    "role_summary": "Another test package",
                    "notable_patterns": [],
                    "used_by": None,
                    "source_type": "community_observation",
                    "evidence_urls": ["https://example.com/b"],
                    "pinned_external_version": None,
                    "pinned_commit": None,
                    "last_verified": "2026-04-22",
                    "needs_review_after": "2026-07-22",
                    "maintenance_tier": "tier_2",
                    "caveats": None,
                },
            ]
        }
        errors = module.validate_packages(data, "ecosystem_packages.json")
        self.assertTrue(any("duplicate slug 'duplicate-pack'" in e for e in errors))

    def test_valid_community_pages_pass(self):
        module = self._import_module()
        data = {
            "metadata": {
                "schema_version": "1.0.0",
                "last_updated": "2026-04-23",
                "description": "Test pages",
            },
            "pages": [
                {
                    "page_path": "docs/ecosystem/map.md",
                    "page_kind": "generated_catalog",
                    "evidence_label": "Community pattern study",
                    "source_type": "community_metadata",
                    "last_verified": "2026-04-22",
                    "needs_review_after": "2026-07-22",
                    "maintenance_tier": "tier_2",
                    "generated_from": "references/community/ecosystem_packages.json",
                    "notes": "Generated page",
                }
            ],
        }
        errors = module.validate_top_level(data, module.COMMUNITY_SCHEMAS["community_pages.json"], "community_pages.json")
        errors.extend(module.validate_community_metadata(data, "community_pages.json"))
        errors.extend(module.validate_pages(data, "community_pages.json"))
        self.assertEqual(errors, [])

    def test_malformed_page_missing_required_key_fails(self):
        module = self._import_module()
        data = {
            "metadata": {
                "schema_version": "1.0.0",
                "last_updated": "2026-04-23",
                "description": "Test pages",
            },
            "pages": [
                {
                    "page_path": "docs/test.md",
                    "page_kind": "hand_authored",
                }
            ],
        }
        errors = module.validate_pages(data, "community_pages.json")
        self.assertTrue(any("missing required key 'evidence_label'" in e for e in errors))

    def test_page_kind_enum_is_enforced(self):
        module = self._import_module()
        data = {
            "pages": [
                {
                    "page_path": "docs/test.md",
                    "page_kind": "wrong",
                    "evidence_label": "Operational guidance",
                    "source_type": "repo_local",
                    "last_verified": "2026-04-23",
                    "needs_review_after": "2026-10-23",
                    "maintenance_tier": "tier_2",
                    "generated_from": None,
                    "notes": None,
                }
            ]
        }
        errors = module.validate_pages(data, "community_pages.json")
        self.assertTrue(any("invalid page_kind 'wrong'" in e for e in errors))

    def test_duplicate_page_path_is_rejected(self):
        module = self._import_module()
        data = {
            "pages": [
                {
                    "page_path": "docs/test.md",
                    "page_kind": "hand_authored_policy",
                    "evidence_label": "Operational guidance",
                    "source_type": "repo_local",
                    "last_verified": "2026-04-23",
                    "needs_review_after": "2026-10-23",
                    "maintenance_tier": "tier_2",
                    "generated_from": None,
                    "notes": None,
                },
                {
                    "page_path": "docs/test.md",
                    "page_kind": "hand_authored_guide",
                    "evidence_label": "Community pattern study",
                    "source_type": "hybrid",
                    "last_verified": "2026-04-23",
                    "needs_review_after": "2026-10-23",
                    "maintenance_tier": "tier_2",
                    "generated_from": None,
                    "notes": None,
                },
            ]
        }
        errors = module.validate_pages(data, "community_pages.json")
        self.assertTrue(any("duplicate page_path 'docs/test.md'" in e for e in errors))

    def test_page_path_with_backslashes_is_rejected(self):
        module = self._import_module()
        data = {
            "pages": [
                {
                    "page_path": "docs\\reference\\community-maintenance-policy.md",
                    "page_kind": "hand_authored_policy",
                    "evidence_label": "Operational guidance",
                    "source_type": "repo_local",
                    "last_verified": "2026-04-23",
                    "needs_review_after": "2026-10-23",
                    "maintenance_tier": "tier_2",
                    "generated_from": None,
                    "notes": None,
                }
            ]
        }
        errors = module.validate_pages(data, "community_pages.json")
        self.assertTrue(any("page_path uses backslashes" in e for e in errors))

    def test_generated_from_with_backslashes_is_rejected(self):
        module = self._import_module()
        data = {
            "pages": [
                {
                    "page_path": "docs/ecosystem/map.md",
                    "page_kind": "generated_catalog",
                    "evidence_label": "Community pattern study",
                    "source_type": "community_metadata",
                    "last_verified": "2026-04-22",
                    "needs_review_after": "2026-07-22",
                    "maintenance_tier": "tier_2",
                    "generated_from": "references\\community\\ecosystem_packages.json",
                    "notes": "Generated page",
                }
            ]
        }
        errors = module.validate_pages(data, "community_pages.json")
        self.assertTrue(any("generated_from uses backslashes" in e for e in errors))


class ValidateSchemaScriptTests(unittest.TestCase):
    """Tests that the validation script runs successfully on the repo."""

    def _import_module(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("validate_schema", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_single_valid_file_passes_internal_validation(self):
        module = self._import_module()
        payload = {
            "metadata": {
                "sources": ["references/snapshots/server.py"],
                "extracted_date": "2026-04-22",
                "version": "v0.19.3",
                "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
            },
            "coverage": {
                "description": "Static extraction of ComfyUI HTTP and WebSocket endpoint structure.",
                "guaranteed_fields": [
                    "endpoints[].route",
                    "endpoints[].method",
                    "endpoints[].returns.kind",
                    "endpoints[].returns.status_codes",
                ],
                "best_effort_fields": [
                    "endpoints[].description",
                    "endpoints[].parameters",
                    "endpoints[].returns.summary",
                    "endpoints[].returns.fields",
                ],
                "deferred": [
                    "parameter typing",
                    "richer error contracts",
                    "variable-return response-body fidelity",
                ],
            },
            "endpoints": [
                {
                    "route": "/prompt",
                    "method": "POST",
                    "description": "Queue a prompt.",
                    "parameters": [],
                    "returns": {
                        "kind": "json",
                        "summary": "Prompt queued.",
                        "status_codes": [200],
                        "fields": [],
                        "notes": [],
                    },
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = Path(tmpdir) / "server_endpoints.json"
            json_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            errors = []
            module._validate_json_file(json_file, errors)
        self.assertEqual(errors, [])

    def test_single_file_reports_published_schema_violation(self):
        module = self._import_module()
        payload = {
            "metadata": {
                "sources": ["references/snapshots/server.py"],
                "extracted_date": "2026-04-22",
                "version": "v0.19.3",
                "commit": "3086026401180c9216bcb6ace442a4e3587d2c66",
            },
            "coverage": {
                "description": "Static extraction of ComfyUI HTTP and WebSocket endpoint structure.",
                "guaranteed_fields": [
                    "endpoints[].route",
                    "endpoints[].method",
                    "endpoints[].returns.kind",
                    "endpoints[].returns.status_codes",
                ],
                "best_effort_fields": [
                    "endpoints[].description",
                    "endpoints[].parameters",
                    "endpoints[].returns.summary",
                    "endpoints[].returns.fields",
                ],
                "deferred": [],
            },
            "endpoints": [
                {
                    "method": "POST",
                    "returns": {
                        "kind": "json",
                        "status_codes": [200],
                    },
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = Path(tmpdir) / "server_endpoints.json"
            json_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            errors = []
            module._validate_json_file(json_file, errors)
        self.assertTrue(any("published schema violation" in e for e in errors))
        self.assertTrue(any("missing required key 'route'" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
