import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.extract import server_blocks, server_helpers, server_parameters, server_returns
from tests.unit.helpers.extractor_test_utils import call_main, load_module

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "extract" / "parse_server.py"


def _load_validate_schema():
    return load_module("validate_schema", REPO_ROOT / "scripts" / "verify" / "validate_schema.py")


def _load_parse_server():
    return load_module("parse_server", SCRIPT)


def _run_parse_server_main(server_path: Path, out_path: Path, *extra_args: str):
    parse_server = _load_parse_server()
    return call_main(parse_server, str(server_path), *extra_args, "--output", str(out_path))


def _extract_single_sample(sample: str) -> list[dict]:
    parse_server = _load_parse_server()
    return parse_server.extract_endpoints(sample)


EXPECTED_PROMPT_ERROR_TYPES = {
    "no_prompt",
    "missing_node_type",
    "prompt_no_outputs",
    "prompt_outputs_failed_validation",
    "exception_during_validation",
    "dependency_cycle",
    "required_input_missing",
    "bad_linked_input",
    "return_type_mismatch",
    "exception_during_inner_validation",
    "invalid_input_type",
    "value_smaller_than_min",
    "value_bigger_than_max",
    "value_not_in_list",
    "custom_validation_failed",
}


def _assert_traceability_is_repo_style(test_case: unittest.TestCase, value):
    if isinstance(value, dict):
        if "traceability" in value:
            traceability = value["traceability"]
            test_case.assertIsInstance(traceability, dict)
            source_file = traceability.get("source_file")
            if source_file is not None:
                test_case.assertNotIn("\\", source_file)
            test_case.assertIn("source_function", traceability)
        for child in value.values():
            _assert_traceability_is_repo_style(test_case, child)
    elif isinstance(value, list):
        for child in value:
            _assert_traceability_is_repo_style(test_case, child)


class ParseServerTests(unittest.TestCase):
    def test_server_helpers_get_helper_body_returns_only_target_body(self):
        source = """
def first_helper():
    return web.Response(status=200)

def image_upload(post):
    image = post.get("image")
    return web.json_response({"ok": True})

def trailing_helper():
    return web.Response(status=404)
"""

        helper_body = server_helpers._get_helper_body(source, "image_upload")
        self.assertIn('image = post.get("image")', helper_body)
        self.assertIn('return web.json_response({"ok": True})', helper_body)
        self.assertNotIn("first_helper", helper_body)
        self.assertNotIn("trailing_helper", helper_body)

    def test_server_helpers_extract_main_body_skips_nested_definitions(self):
        block = """
@routes.post(\"/upload/mask\")
async def upload_mask(request):
    post = await request.post()

    def nested_helper():
        return web.Response(status=400)

    return image_upload(post)
"""

        main_body = server_helpers._extract_main_body(block)
        self.assertIn("post = await request.post()", main_body)
        self.assertIn("return image_upload(post)", main_body)
        self.assertNotIn("return web.Response(status=400)", main_body)

    def test_server_blocks_finds_route_decorators(self):
        lines = [
            '@routes.get("/history")',
            "def history():",
            "    return None",
            '@routes.post("/prompt")',
        ]

        matches = server_blocks._find_decorator_matches(lines)
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0][1].groups(), ("get", "/history"))

    def test_server_parameters_extract_mapping_parameter_defaults(self):
        body = 'limit = request.rel_url.query.get("limit", 50)'
        extracted, _variable_map = server_parameters._extract_mapping_parameters(
            body,
            ["request.rel_url.query"],
            "query",
            "query_access",
        )

        self.assertEqual(extracted[0]["name"], "limit")
        self.assertEqual(extracted[0]["default"], 50)

    def test_server_returns_extracts_augmented_dict_fields(self):
        block = """
resp = {"name": "file.png"}
resp["asset"] = {"id": "123"}
return web.json_response(resp)
"""

        fields = server_returns._extract_json_fields_from_arg(
            block, "resp", block.index("web.json_response")
        )
        self.assertEqual({field["name"] for field in fields}, {"name", "asset"})

    def test_requires_argument(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_extracts_routes_to_json(self):
        sample = '''
@routes.get("/history")
def history():
    """History listing."""
    return None

@routes.post("/prompt")
def prompt():
    return None

@routes.ws("/ws")
def socket():
    """Socket stream."""
    return None
'''
        parse_server = _load_parse_server()
        endpoints = parse_server.extract_endpoints(sample)
        runtime_contracts = parse_server.extract_server_runtime_contracts(sample, "")
        data = {
            "metadata": {
                "sources": ["tmp/server.py"],
                "extracted_date": "2026-05-03",
                "version": "v0.0.1",
                "commit": "abc123",
            },
            "coverage": parse_server.ENDPOINT_COVERAGE,
            "endpoints": endpoints,
            **runtime_contracts,
        }

        self.assertEqual(len(data["endpoints"]), 3)
        self.assertIn("sources", data["metadata"])
        self.assertIsInstance(data["metadata"]["sources"], list)
        self.assertNotIn("source", data["metadata"])
        self.assertIn("coverage", data)
        self.assertIn("description", data["coverage"])
        self.assertIn("guaranteed_fields", data["coverage"])
        self.assertIn("best_effort_fields", data["coverage"])
        self.assertIn("deferred", data["coverage"])
        self.assertEqual(data["endpoints"][0]["method"], "GET")
        self.assertEqual(data["endpoints"][0]["route"], "/history")
        self.assertEqual(data["endpoints"][0]["description"], "History listing.")

        validate_schema = _load_validate_schema()
        errors = validate_schema.validate_top_level(
            data, validate_schema.SCHEMAS["server_endpoints.json"], "server_endpoints.json"
        )
        errors.extend(validate_schema.validate_metadata(data, "server_endpoints.json"))
        errors.extend(validate_schema.validate_coverage(data, "server_endpoints.json"))
        errors.extend(validate_schema.validate_endpoints(data, "server_endpoints.json"))
        errors.extend(
            validate_schema.validate_server_runtime_contracts(data, "server_endpoints.json")
        )
        self.assertEqual(errors, [], msg=f"Schema errors: {errors}")

        for ep in data["endpoints"]:
            self.assertIn("route", ep)
            self.assertIn("method", ep)
            self.assertIn("description", ep)
            self.assertIn("parameters", ep)
            self.assertIn("returns", ep)

    def test_extracts_server_runtime_contract_sections_from_snapshots(self):
        parse_server = _load_parse_server()
        server_path = (
            REPO_ROOT
            / "references"
            / "snapshots"
            / "2026-06-03"
            / "comfyui-core-v0.23.0"
            / "server.py"
        )
        execution_path = server_path.with_name("execution.py")
        server_text = server_path.read_text(encoding="utf-8")
        execution_text = execution_path.read_text(encoding="utf-8")

        data = parse_server.extract_server_runtime_contracts(
            server_text,
            execution_text,
            server_source=server_path.relative_to(REPO_ROOT).as_posix(),
            execution_source=execution_path.relative_to(REPO_ROOT).as_posix(),
        )

        self.assertIn("prompt_submission_contract", data)
        submission = data["prompt_submission_contract"]
        request_fields = {field["name"]: field for field in submission["request_fields"]}
        for field_name in {
            "number",
            "front",
            "prompt",
            "prompt_id",
            "partial_execution_targets",
            "extra_data",
            "client_id",
        }:
            self.assertIn(field_name, request_fields)
        self.assertTrue(request_fields["prompt"]["required"])

        success_fields = {field["name"] for field in submission["success_response_fields"]}
        self.assertGreaterEqual(success_fields, {"prompt_id", "number", "node_errors"})
        error_fields = {field["name"] for field in submission["error_response_fields"]}
        self.assertGreaterEqual(error_fields, {"error", "node_errors"})

        validation = data["prompt_validation_errors"]
        error_types = {entry["type"]: entry for entry in validation["error_types"]}
        self.assertGreaterEqual(len(error_types), 15)
        for error_type in EXPECTED_PROMPT_ERROR_TYPES:
            self.assertIn(error_type, error_types)
            self.assertEqual(error_types[error_type]["extraction_method"], "ast-structural")

        queue_history = data["queue_history_contract"]
        section_names = {section["name"] for section in queue_history["sections"]}
        self.assertGreaterEqual(
            section_names,
            {"queue_running", "queue_pending", "history", "status", "task_done", "flags"},
        )

        _assert_traceability_is_repo_style(self, data)

    def test_runtime_contract_sections_defer_when_sources_are_empty(self):
        parse_server = _load_parse_server()

        data = parse_server.extract_server_runtime_contracts("", "")

        submission = data["prompt_submission_contract"]
        self.assertEqual(submission["request_fields"], [])
        self.assertEqual(submission["success_response_fields"], [])
        self.assertEqual(submission["error_response_fields"], [])
        self.assertEqual(submission["coverage"], "deferred")

        validation = data["prompt_validation_errors"]
        self.assertEqual(validation["error_types"], [])
        self.assertEqual(validation["coverage"], "deferred")

        queue_history = data["queue_history_contract"]
        self.assertEqual(queue_history["sections"], [])
        self.assertEqual(queue_history["coverage"], "deferred")

    def test_runtime_contract_sections_defer_when_patterns_are_absent(self):
        parse_server = _load_parse_server()

        data = parse_server.extract_server_runtime_contracts(
            "def unrelated_server_function():\n    return None\n",
            "def unrelated_execution_function():\n    return None\n",
        )

        self.assertEqual(data["prompt_submission_contract"]["request_fields"], [])
        self.assertEqual(data["prompt_validation_errors"]["error_types"], [])
        self.assertEqual(data["queue_history_contract"]["sections"], [])

    def test_metadata_sources_are_repo_relative_when_input_is_in_repo(self):
        sample = """
@routes.get("/history")
def history():
    return None
"""

        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
            tmp_path = Path(tmp)
            server_path = tmp_path / "server.py"
            out_path = tmp_path / "server_endpoints.json"
            server_path.write_text(sample, encoding="utf-8")

            exit_code, _stdout, stderr = _run_parse_server_main(server_path, out_path)

            self.assertEqual(exit_code, 0, msg=stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(
                data["metadata"]["sources"],
                [server_path.relative_to(REPO_ROOT).as_posix()],
            )

    def test_json_response_extraction(self):
        sample = """
@routes.get("/models")
def list_models(request):
    models = ["a", "b"]
    return web.json_response(models)

@routes.post("/prompt")
def queue_prompt(request):
    return web.json_response({"prompt_id": "abc", "number": 1})
"""

        endpoints = _extract_single_sample(sample)

        ep_map = {ep["route"]: ep for ep in endpoints}
        self.assertEqual(ep_map["/models"]["returns"]["kind"], "json")
        self.assertIn(200, ep_map["/models"]["returns"]["status_codes"])

        self.assertEqual(ep_map["/prompt"]["returns"]["kind"], "json")
        fields = {f["name"] for f in ep_map["/prompt"]["returns"]["fields"]}
        self.assertIn("prompt_id", fields)
        self.assertIn("number", fields)

    def test_websocket_route_detection(self):
        sample = """
@routes.get("/ws")
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    return ws
"""

        endpoint = _extract_single_sample(sample)[0]
        self.assertEqual(endpoint["returns"]["kind"], "websocket")
        self.assertIn(101, endpoint["returns"]["status_codes"])

    def test_empty_acknowledgement_route(self):
        sample = """
@routes.post("/interrupt")
async def post_interrupt(request):
    nodes.interrupt_processing()
    return web.Response(status=200)
"""

        endpoint = _extract_single_sample(sample)[0]
        self.assertEqual(endpoint["returns"]["kind"], "empty")
        self.assertIn(200, endpoint["returns"]["status_codes"])

    def test_file_response_detection(self):
        sample = """
@routes.get("/")
async def get_root(request):
    return web.FileResponse(os.path.join(root, "index.html"))
"""

        endpoint = _extract_single_sample(sample)[0]
        self.assertEqual(endpoint["returns"]["kind"], "file")

    def test_unknown_fallback(self):
        sample = """
@routes.get("/legacy")
def legacy(request):
    result = some_old_function()
    return result
"""

        endpoint = _extract_single_sample(sample)[0]
        self.assertEqual(endpoint["returns"]["kind"], "unknown")

    def test_helper_delegation(self):
        sample = """
def image_upload(post):
    if not post.get("image"):
        return web.Response(status=400)
    resp = {"name": "file.png"}
    return web.json_response(resp)

@routes.post("/upload/image")
async def upload_image(request):
    post = await request.post()
    return image_upload(post)
"""

        endpoint = _extract_single_sample(sample)[0]
        self.assertEqual(endpoint["returns"]["kind"], "json")
        self.assertIn(400, endpoint["returns"]["status_codes"])

    def test_nested_function_ignored(self):
        """Nested function definitions should not confuse response inference."""
        sample = """
@routes.post("/upload/mask")
async def upload_mask(request):
    post = await request.post()

    def image_save_function(image, post, filepath):
        if not post.get("image"):
            return web.Response(status=400)
        with open(filepath, "wb") as f:
            f.write(image.file.read())

    return image_upload(post, image_save_function)
"""

        endpoint = _extract_single_sample(sample)[0]
        # The nested Response should be ignored; since image_upload is not defined
        # in this sample, it falls back to unknown.
        self.assertEqual(endpoint["returns"]["kind"], "unknown")

    def test_json_response_with_error_response_elsewhere(self):
        """When a handler has both web.Response(status=404) and a json_response,
        the endpoint contract should preserve both success and explicit error codes."""
        sample = """
@routes.get("/models/{folder}")
async def get_models(request):
    folder = request.match_info.get("folder", None)
    if folder not in folder_paths.folder_names_and_paths:
        return web.Response(status=404)
    files = folder_paths.get_filename_list(folder)
    return web.json_response(files)
"""

        endpoint = _extract_single_sample(sample)[0]
        # The json_response has no explicit status, so it defaults to 200,
        # but the handler also documents an explicit 404 branch.
        self.assertEqual(endpoint["returns"]["kind"], "json")
        self.assertIn(200, endpoint["returns"]["status_codes"])
        self.assertIn(404, endpoint["returns"]["status_codes"])

    def test_json_response_with_explicit_error_status(self):
        """When a json_response has an explicit error status in its argument,
        that status should be reflected in the output."""
        sample = """
@routes.post("/resource")
def create_resource(request):
    data = await request.json()
    if not data.get("name"):
        return web.json_response({"error": "name required"}, status=400)
    return web.json_response({"id": "123"})
"""

        endpoint = _extract_single_sample(sample)[0]
        # Should prefer the success response (more fields)
        self.assertEqual(endpoint["returns"]["kind"], "json")
        # The success response has no explicit status, so it defaults to 200
        self.assertIn(200, endpoint["returns"]["status_codes"])

    def test_json_response_variable_payload_and_augmented_fields(self):
        """Variable-backed dict payloads should expose literal and augmented keys."""
        sample = """
@routes.post("/upload/image")
async def upload_image(request):
    resp = {"name": "file.png", "subfolder": "", "type": "input"}
    if request.query.get("asset"):
        resp["asset"] = {"id": "123"}
    return web.json_response(resp)
"""

        endpoint = _extract_single_sample(sample)[0]
        fields = {f["name"] for f in endpoint["returns"]["fields"]}
        self.assertEqual(fields, {"name", "subfolder", "type", "asset"})
        self.assertEqual(
            endpoint["returns"]["summary"],
            "JSON object with fields: name, subfolder, type, asset.",
        )

    def test_extracts_route_and_query_parameter_details(self):
        sample = """
@routes.get("/models/{folder}")
async def get_models(request):
    folder = request.match_info.get("folder", None)
    limit = request.rel_url.query.get("limit", 50)
    sort_order = request.rel_url.query.get("sort_order", "desc")
    if sort_order not in ["asc", "desc"]:
        return web.json_response({"error": "bad sort order"}, status=400)
    if folder not in folder_paths.folder_names_and_paths:
        return web.Response(status=404)
    return web.json_response({"items": []})
"""

        endpoint = _extract_single_sample(sample)[0]
        params = {(param["name"], param["location"]): param for param in endpoint["parameters"]}
        self.assertTrue(params[("folder", "path")]["required"])
        self.assertEqual(params[("limit", "query")]["default"], 50)
        self.assertEqual(params[("sort_order", "query")]["allowed_values"], ["asc", "desc"])
        self.assertEqual(
            params[("folder", "path")]["traceability"]["strategy"],
            "route_token",
        )

    def test_extracts_form_parameters_from_helper(self):
        sample = """
def image_upload(post):
    image = post.get("image")
    overwrite = post.get("overwrite", False)
    return web.json_response({"ok": True})

@routes.post("/upload/image")
async def upload_image(request):
    post = await request.post()
    return image_upload(post)
"""

        endpoint = _extract_single_sample(sample)[0]
        params = {(param["name"], param["location"]): param for param in endpoint["parameters"]}
        self.assertIn(("image", "form"), params)
        self.assertEqual(params[("overwrite", "form")]["default"], False)

    def test_return_traceability_added(self):
        sample = """
@routes.get("/ws")
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    return ws
"""
        endpoint = _extract_single_sample(sample)[0]
        returns = endpoint["returns"]
        self.assertEqual(returns["traceability"]["strategy"], "web.WebSocketResponse")

    def test_sibling_helper_definitions_do_not_contaminate_route(self):
        """Top-level helpers after a route should not leak fields into that route."""
        sample = """
@routes.get("/extensions")
def get_extensions(request):
    extensions = ["/a.js"]
    return web.json_response(extensions)

def image_upload(post):
    resp = {"name": "file.png", "subfolder": "", "type": "input"}
    resp["asset"] = {"id": "123"}
    return web.json_response(resp)
"""

        endpoint = _extract_single_sample(sample)[0]
        returns = endpoint["returns"]
        self.assertEqual(returns["kind"], "json")
        self.assertEqual(returns["fields"], [])
        self.assertEqual(returns["status_codes"], [200])


if __name__ == "__main__":
    unittest.main()
