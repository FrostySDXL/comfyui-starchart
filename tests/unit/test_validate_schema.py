"""Tests for scripts/verify/validate_schema.py."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
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

    def _server_runtime_contracts(self):
        traceability = {
            "source_type": "pinned_snapshot",
            "strategy": "ast-structural",
            "source_file": "references/snapshots/server.py",
            "source_function": "post_prompt",
        }
        return {
            "prompt_submission_contract": {
                "request_fields": [
                    {
                        "name": "prompt",
                        "location": "json_body",
                        "required": True,
                        "type_hint": "dict",
                        "traceability": traceability,
                    }
                ],
                "success_response_fields": [
                    {
                        "name": "prompt_id",
                        "location": "json_response",
                        "type_hint": "str",
                        "traceability": traceability,
                    }
                ],
                "error_response_fields": [
                    {
                        "name": "error",
                        "location": "json_response",
                        "type_hint": "dict",
                        "traceability": traceability,
                    }
                ],
            },
            "prompt_validation_errors": {
                "error_types": [
                    {
                        "type": "no_prompt",
                        "source_function": "post_prompt",
                        "traceability": traceability,
                        "extraction_method": "ast-structural",
                        "extra_info_fields": ["prompt_id"],
                    }
                ]
            },
            "queue_history_contract": {
                "sections": [
                    {
                        "name": "queue_pending",
                        "summary": "Pending queue entries returned by GET /queue.",
                        "traceability": {
                            **traceability,
                            "source_function": "get_queue",
                        },
                    }
                ]
            },
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
                            {
                                "name": "prompt_id",
                                "type_hint": "str",
                                "description": "UUID of the queued prompt",
                            },
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
            **self._server_runtime_contracts(),
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
            "extension_fields": [
                {
                    "name": "setup",
                    "type_hint": "(app: ComfyApp) => Promise<void> | void",
                    "required": False,
                    "description": "Setup extension callback.",
                    "defined_in": "references/snapshots/comfy.ts",
                    "traceability": {
                        "source_type": "source-backed",
                        "strategy": "typed_interface_field",
                    },
                    "is_hook": True,
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
                    "type_hint": "BOOLEAN",
                    "defined_in": "references/snapshots/_io.py",
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
            "v3_schema_contract": {
                "contract_version": "3.0",
                "schema_fields": [
                    {
                        "name": "is_api_node",
                        "type_hint": "bool",
                        "required": False,
                        "default": False,
                        "description": "Flag for API nodes.",
                        "defined_in": "references/snapshots/_io.py",
                        "traceability": {
                            "source_type": "source-backed",
                            "strategy": "dataclass_field",
                        },
                    }
                ],
                "node_info_fields": [
                    {
                        "name": "input",
                        "type_hint": "dict[str, Any]",
                        "required": True,
                        "defined_in": "references/snapshots/_io.py",
                        "traceability": {
                            "source_type": "source-backed",
                            "strategy": "dataclass_field",
                        },
                    }
                ],
                "hidden_values": {
                    "hidden_enum": [
                        {
                            "name": "prompt",
                            "value": "PROMPT",
                            "description": "Prompt hidden input.",
                            "defined_in": "references/snapshots/_io.py",
                            "traceability": {
                                "source_type": "source-backed",
                                "strategy": "enum_member",
                            },
                        }
                    ],
                    "hidden_auto_injection": [
                        {
                            "condition": "is_api_node",
                            "injected": ["auth_token_comfy_org"],
                        }
                    ],
                },
                "price_badge_contract": [
                    {
                        "class_name": "PriceBadge",
                        "fields": [
                            {
                                "name": "amount",
                                "type_hint": "float | None",
                                "required": False,
                                "default": None,
                                "defined_in": "references/snapshots/_io.py",
                                "traceability": {
                                    "source_type": "source-backed",
                                    "strategy": "dataclass_field",
                                },
                            }
                        ],
                        "traceability": {
                            "source_type": "source-backed",
                            "strategy": "dataclass",
                        },
                    }
                ],
                "node_flags": [
                    {
                        "name": "is_api_node",
                        "schema_fields_ref": "is_api_node",
                    }
                ],
            },
            "coverage": {
                "description": "Static and optional runtime coverage for object_info and IO typing.",
                "sources_covered": ["object_info_fields", "io_types", "basic_input_shapes"],
                "runtime_enriched": False,
                "guaranteed_fields": ["v3_schema_contract"],
                "best_effort_fields": [
                    "v3_schema_contract.schema_fields",
                    "v3_schema_contract.node_info_fields",
                    "v3_schema_contract.hidden_values",
                    "v3_schema_contract.price_badge_contract",
                    "v3_schema_contract.node_flags",
                ],
                "deferred": ["runtime-only object_info details"],
            },
        }

    def _valid_websocket_events_data(self):
        return {
            "metadata": {
                "sources": [
                    "references/snapshots/core/server.py",
                    "references/snapshots/frontend/src/scripts/app.ts",
                ],
                "extracted_date": "2026-06-04",
                "version": "v0.23.0+v1.46.6",
                "commit": "a88e02b18576283b1ff25a4b564548c5dc42cbf6",
                "commits": {
                    "core": "a88e02b18576283b1ff25a4b564548c5dc42cbf6",
                    "frontend": "0123456789abcdef0123456789abcdef01234567",
                },
            },
            "coverage": {
                "description": "Source-observed ComfyUI WebSocket and binary event contracts.",
                "guaranteed_fields": ["events.name", "binary_events.name"],
                "best_effort_fields": ["events.payload_fields"],
                "deferred": ["Runtime-computed payloads are summarized when visible."],
                "ast_scan_notes": [],
            },
            "events": [
                {
                    "name": "status",
                    "direction": "server_to_client",
                    "server_sources": [
                        {
                            "source_file": "references/snapshots/core/server.py",
                            "source_function": "send_sync",
                            "line": 10,
                            "method": "send_sync",
                        }
                    ],
                    "frontend_listeners": [],
                    "payload_fields": ["exec_info"],
                    "payload_notes": [],
                    "ast_scan_notes": [],
                    "traceability": {
                        "strategy": "ast_send_call_and_frontend_listener_merge",
                        "notes": [],
                    },
                }
            ],
            "binary_events": [],
        }

    def test_valid_server_endpoints_pass(self):
        module = self._import_module()
        data = self._valid_server_endpoints_data()
        errors = module.validate_top_level(
            data, module.SCHEMAS["server_endpoints.json"], "server_endpoints.json"
        )
        errors.extend(module.validate_metadata(data, "server_endpoints.json"))
        errors.extend(module.validate_coverage(data, "server_endpoints.json"))
        errors.extend(module.validate_endpoints(data, "server_endpoints.json"))
        errors.extend(module.validate_server_runtime_contracts(data, "server_endpoints.json"))
        self.assertEqual(errors, [])

    def test_server_coverage_dotted_runtime_paths_require_existing_parent(self):
        module = self._import_module()
        data = self._valid_server_endpoints_data()
        del data["prompt_submission_contract"]
        data["coverage"]["best_effort_fields"].append("prompt_submission_contract.request_fields")
        errors = module.validate_coverage(data, "server_endpoints.json")
        self.assertTrue(
            any("unresolved coverage.best_effort_fields path" in error for error in errors)
        )

    def test_server_coverage_dotted_runtime_paths_accept_existing_parent(self):
        module = self._import_module()
        data = self._valid_server_endpoints_data()
        data["coverage"]["best_effort_fields"].append("prompt_submission_contract.request_fields")
        errors = module.validate_coverage(data, "server_endpoints.json")
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
        errors = module.validate_top_level(
            data, module.SCHEMAS["server_endpoints.json"], "server_endpoints.json"
        )
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
        errors = module.validate_top_level(
            data, module.SCHEMAS["node_api_schema.json"], "node_api_schema.json"
        )
        errors.extend(module.validate_metadata(data, "node_api_schema.json"))
        errors.extend(module.validate_coverage(data, "node_api_schema.json"))
        errors.extend(module.validate_io_types(data, "node_api_schema.json"))
        errors.extend(module.validate_typed_input_shapes(data, "node_api_schema.json"))
        errors.extend(module.validate_v3_schema_contract(data, "node_api_schema.json"))
        self.assertEqual(errors, [])

    def test_v3_schema_contract_rejects_unknown_node_flag_ref(self):
        module = self._import_module()
        data = self._valid_node_api_schema_data()
        data["v3_schema_contract"]["node_flags"][0]["schema_fields_ref"] = "missing"
        errors = module.validate_v3_schema_contract(data, "node_api_schema.json")
        self.assertTrue(any("does not resolve" in e for e in errors))

    def test_v3_schema_contract_rejects_extra_node_flag_key(self):
        module = self._import_module()
        data = self._valid_node_api_schema_data()
        data["v3_schema_contract"]["node_flags"][0]["extra"] = "not allowed"
        errors = module.validate_v3_schema_contract(data, "node_api_schema.json")
        self.assertTrue(any("must contain exactly" in e for e in errors))

    def test_v3_schema_contract_rejects_missing_node_flag_schema_fields_ref(self):
        module = self._import_module()
        data = self._valid_node_api_schema_data()
        del data["v3_schema_contract"]["node_flags"][0]["schema_fields_ref"]

        errors = module.validate_v3_schema_contract(data, "node_api_schema.json")

        self.assertTrue(any("missing required key 'schema_fields_ref'" in e for e in errors))

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

    def test_extension_fields_reject_missing_required_field_metadata(self):
        module = self._import_module()
        data = self._valid_js_hooks_data()
        data["extension_fields"][0].pop("defined_in")

        errors = module.validate_extension_fields(data, "js_hooks.json")

        self.assertTrue(
            any("extension_fields[0] missing required key 'defined_in'" in e for e in errors)
        )

    def test_extension_fields_reject_invalid_traceability_shape(self):
        module = self._import_module()
        data = self._valid_js_hooks_data()
        data["extension_fields"][0]["traceability"] = {"source_type": "source-backed"}

        errors = module.validate_extension_fields(data, "js_hooks.json")

        self.assertTrue(
            any(
                "extension_fields[0].traceability missing required key 'strategy'" in e
                for e in errors
            )
        )

    def test_metadata_sources_accept_forward_slash_repo_paths(self):
        module = self._import_module()
        data = self._valid_server_endpoints_data()
        data["metadata"]["sources"] = ["references/snapshots/server.py"]

        errors = module.validate_metadata(data, "server_endpoints.json")

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

    def test_valid_websocket_events_pass_internal_and_published_schema(self):
        module = self._import_module()
        data = self._valid_websocket_events_data()
        errors = module.validate_top_level(
            data, module.SCHEMAS["websocket_events.json"], "websocket_events.json"
        )
        errors.extend(module.validate_metadata(data, "websocket_events.json"))
        errors.extend(module.validate_coverage(data, "websocket_events.json"))
        errors.extend(module.validate_websocket_events(data, "websocket_events.json"))
        errors.extend(
            module.validate_against_published_artifact_schema(data, "websocket_events.json")
        )

        self.assertEqual(errors, [])

    def test_websocket_events_rejects_non_string_deferred_item(self):
        module = self._import_module()
        data = self._valid_websocket_events_data()
        data["coverage"]["deferred"] = [123]

        errors = module.validate_coverage(data, "websocket_events.json")
        errors.extend(
            module.validate_against_published_artifact_schema(data, "websocket_events.json")
        )

        self.assertTrue(any("coverage.deferred[0] expected str" in e for e in errors))
        self.assertTrue(any("published schema violation" in e for e in errors))

    def test_docs_index_schema_accepts_nested_tooling_metadata(self):
        module = self._import_module()
        data = {
            "artifact": "docs-index.json",
            "artifact_schema_version": "1.1.0",
            "scope": {
                "surface": "test navigation with tooling metadata",
                "excludes": [],
            },
            "pages": [
                {
                    "title": "Prompt Submission",
                    "path": "api/prompt-submission.md",
                    "nav_section": "API Reference",
                    "audience": None,
                    "evidence": "Source-backed from pinned snapshots",
                    "summary": "Prompt summary.",
                    "tooling_metadata": {
                        "task_intents": ["submit-prompt"],
                        "related_artifacts": ["docs-index.json", "server_endpoints.json"],
                        "related_routes": ["POST /prompt"],
                        "related_events": ["executing", "execution_success"],
                        "runtime_required": True,
                        "stability_tier": "pinned-baseline",
                        "recommended_next_reads": ["api/history-queue.md"],
                    },
                }
            ],
        }
        errors = module.validate_against_published_artifact_schema(data, "docs-index.json")
        self.assertEqual(errors, [])

    def test_validate_schema_wrapper_uses_published_schema_helper_module(self):
        module = self._import_module()
        self.assertEqual(
            module._validate_against_published_artifact_schema.__module__,
            "scripts.verify.published_schema_validation",
        )

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
                    "fields": {"waveform": {}},
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
        errors = module.validate_top_level(
            data, module.SCHEMAS["node_api_schema.json"], "node_api_schema.json"
        )
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
        errors = module.validate_top_level(
            data, module.SCHEMAS["object_info_runtime.json"], "object_info_runtime.json"
        )
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

    def test_validate_prompt_conditioning_surface_valid_returns_empty(self):
        """Valid surface with both io_type lists passes validation."""
        module = self._import_module()
        data = {
            "prompt_conditioning_surface": {
                "text_input_io_types": [
                    {
                        "io_type": "STRING",
                        "class_name": "String",
                        "supports_multiline_parameter": True,
                        "traceability": {
                            "source_type": "source-backed",
                            "strategy": "python_signature",
                        },
                    }
                ],
                "conditioning_io_types": [],
            }
        }
        errors = module.validate_prompt_conditioning_surface(data, "test.json")
        self.assertEqual(errors, [])

    def test_validate_prompt_conditioning_surface_missing_io_type(self):
        """Entry without required 'io_type' returns an error."""
        module = self._import_module()
        data = {
            "prompt_conditioning_surface": {
                "text_input_io_types": [
                    {"class_name": "String", "supports_multiline_parameter": False}
                ],
                "conditioning_io_types": [],
            }
        }
        errors = module.validate_prompt_conditioning_surface(data, "test.json")
        self.assertTrue(any("missing required key 'io_type'" in e for e in errors))

    def test_validate_prompt_conditioning_surface_wrong_type(self):
        """Entry with int where str is expected returns a type error."""
        module = self._import_module()
        data = {
            "prompt_conditioning_surface": {
                "text_input_io_types": [{"io_type": 42, "class_name": "String"}],
                "conditioning_io_types": [],
            }
        }
        errors = module.validate_prompt_conditioning_surface(data, "test.json")
        self.assertTrue(any("expected str" in e for e in errors))


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
            "prompt_submission_contract": {
                "request_fields": [],
                "success_response_fields": [],
                "error_response_fields": [],
                "coverage": "deferred",
            },
            "prompt_validation_errors": {
                "error_types": [],
                "coverage": "deferred",
            },
            "queue_history_contract": {
                "sections": [],
                "coverage": "deferred",
            },
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
            "prompt_submission_contract": {
                "request_fields": [],
                "success_response_fields": [],
                "error_response_fields": [],
                "coverage": "deferred",
            },
            "prompt_validation_errors": {
                "error_types": [],
                "coverage": "deferred",
            },
            "queue_history_contract": {
                "sections": [],
                "coverage": "deferred",
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = Path(tmpdir) / "server_endpoints.json"
            json_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            errors = []
            module._validate_json_file(json_file, errors)
        self.assertTrue(any("published schema violation" in e for e in errors))
        self.assertTrue(any("missing required key 'route'" in e for e in errors))

    def test_single_support_artifact_file_reports_published_schema_violation(self):
        module = self._import_module()
        payload = {
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
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = Path(tmpdir) / "delta-summary.json"
            json_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            errors = []
            module._validate_json_file(json_file, errors)
        self.assertTrue(any("published schema violation" in e for e in errors))
        self.assertTrue(any("expected integer" in e for e in errors))

    def test_main_validates_support_artifacts_and_excludes_manifest(self):
        module = self._import_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            raw_dir = tmp_path / "references" / "raw"
            raw_dir.mkdir(parents=True)
            published_dir = tmp_path / "public" / "artifacts"
            published_dir.mkdir(parents=True)
            schema_dir = published_dir / "schemas"
            schema_dir.mkdir(parents=True)

            (schema_dir / "docs-index.schema.json").write_text(
                (
                    REPO_ROOT / "public" / "artifacts" / "schemas" / "docs-index.schema.json"
                ).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (schema_dir / "delta-summary.schema.json").write_text(
                (
                    REPO_ROOT / "public" / "artifacts" / "schemas" / "delta-summary.schema.json"
                ).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (schema_dir / "refresh-provenance.schema.json").write_text(
                (
                    REPO_ROOT
                    / "public"
                    / "artifacts"
                    / "schemas"
                    / "refresh-provenance.schema.json"
                ).read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            docs_index_payload = {
                "artifact": "docs-index.json",
                "artifact_schema_version": "1.1.0",
                "scope": {"surface": "test", "excludes": []},
                "pages": [],
            }
            delta_summary_payload = {
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
                            "new_count": 1,
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
            }
            refresh_provenance_payload = {
                "backup_location": None,
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
                "requested_versions": {"core": "v0.22.0", "frontend": "v1.45.12"},
                "resolved_commits": {"core": "abc", "frontend": "def"},
                "runtime_object_info": {"merged_into_node_api_schema": False, "requested": False},
            }

            docs_index_path = published_dir / "docs-index.json"
            docs_index_path.write_text(json.dumps(docs_index_payload, indent=2), encoding="utf-8")
            (published_dir / "delta-summary.json").write_text(
                json.dumps(delta_summary_payload, indent=2), encoding="utf-8"
            )
            (published_dir / "refresh-provenance.json").write_text(
                json.dumps(refresh_provenance_payload, indent=2), encoding="utf-8"
            )
            (published_dir / "manifest.json").write_text("{}", encoding="utf-8")

            original_raw_dir = module.REFERENCES_RAW_DIR
            original_published_schema_dir = module.PUBLISHED_SCHEMA_DIR
            original_docs_index_path = module.DOCS_INDEX_PATH

            module.REFERENCES_RAW_DIR = raw_dir
            module.PUBLISHED_SCHEMA_DIR = schema_dir
            module.DOCS_INDEX_PATH = docs_index_path
            try:
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    result = module.main()
            finally:
                module.REFERENCES_RAW_DIR = original_raw_dir
                module.PUBLISHED_SCHEMA_DIR = original_published_schema_dir
                module.DOCS_INDEX_PATH = original_docs_index_path

        output = stdout.getvalue()
        self.assertEqual(result, 0)
        self.assertIn("Validating delta-summary.json...", output)
        self.assertIn("Validating refresh-provenance.json...", output)
        self.assertNotIn("Validating manifest.json...", output)


if __name__ == "__main__":
    unittest.main()
