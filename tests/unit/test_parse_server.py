import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import importlib.util

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "extract" / "parse_server.py"


def _load_validate_schema():
    spec = importlib.util.spec_from_file_location(
        "validate_schema",
        REPO_ROOT / "scripts" / "verify" / "validate_schema.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ParseServerTests(unittest.TestCase):
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

        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            out_path = Path(tmp) / "server_endpoints.json"
            server_path.write_text(sample, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(server_path), "--version", "v0.0.1", "--commit", "abc123", "--output", str(out_path)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("Extracted 3 endpoints", result.stdout)

            data = json.loads(out_path.read_text(encoding="utf-8"))
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

            # Verify output passes schema validation
            validate_schema = _load_validate_schema()
            errors = validate_schema.validate_top_level(data, validate_schema.SCHEMAS["server_endpoints.json"], "server_endpoints.json")
            errors.extend(validate_schema.validate_metadata(data, "server_endpoints.json"))
            errors.extend(validate_schema.validate_coverage(data, "server_endpoints.json"))
            errors.extend(validate_schema.validate_endpoints(data, "server_endpoints.json"))
            self.assertEqual(errors, [], msg=f"Schema errors: {errors}")

            # Assert richer contract: each endpoint has expected keys
            for ep in data["endpoints"]:
                self.assertIn("route", ep)
                self.assertIn("method", ep)
                self.assertIn("description", ep)
                self.assertIn("parameters", ep)
                self.assertIn("returns", ep)

    def test_json_response_extraction(self):
        sample = '''
@routes.get("/models")
def list_models(request):
    models = ["a", "b"]
    return web.json_response(models)

@routes.post("/prompt")
def queue_prompt(request):
    return web.json_response({"prompt_id": "abc", "number": 1})
'''

        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            out_path = Path(tmp) / "server_endpoints.json"
            server_path.write_text(sample, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(server_path), "--output", str(out_path)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))

            ep_map = {ep["route"]: ep for ep in data["endpoints"]}
            self.assertEqual(ep_map["/models"]["returns"]["kind"], "json")
            self.assertIn(200, ep_map["/models"]["returns"]["status_codes"])

            self.assertEqual(ep_map["/prompt"]["returns"]["kind"], "json")
            fields = {f["name"] for f in ep_map["/prompt"]["returns"]["fields"]}
            self.assertIn("prompt_id", fields)
            self.assertIn("number", fields)

    def test_websocket_route_detection(self):
        sample = '''
@routes.get("/ws")
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    return ws
'''

        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            out_path = Path(tmp) / "server_endpoints.json"
            server_path.write_text(sample, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(server_path), "--output", str(out_path)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(data["endpoints"][0]["returns"]["kind"], "websocket")
            self.assertIn(101, data["endpoints"][0]["returns"]["status_codes"])

    def test_empty_acknowledgement_route(self):
        sample = '''
@routes.post("/interrupt")
async def post_interrupt(request):
    nodes.interrupt_processing()
    return web.Response(status=200)
'''

        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            out_path = Path(tmp) / "server_endpoints.json"
            server_path.write_text(sample, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(server_path), "--output", str(out_path)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(data["endpoints"][0]["returns"]["kind"], "empty")
            self.assertIn(200, data["endpoints"][0]["returns"]["status_codes"])

    def test_file_response_detection(self):
        sample = '''
@routes.get("/")
async def get_root(request):
    return web.FileResponse(os.path.join(root, "index.html"))
'''

        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            out_path = Path(tmp) / "server_endpoints.json"
            server_path.write_text(sample, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(server_path), "--output", str(out_path)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(data["endpoints"][0]["returns"]["kind"], "file")

    def test_unknown_fallback(self):
        sample = '''
@routes.get("/legacy")
def legacy(request):
    result = some_old_function()
    return result
'''

        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            out_path = Path(tmp) / "server_endpoints.json"
            server_path.write_text(sample, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(server_path), "--output", str(out_path)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(data["endpoints"][0]["returns"]["kind"], "unknown")

    def test_helper_delegation(self):
        sample = '''
def image_upload(post):
    if not post.get("image"):
        return web.Response(status=400)
    resp = {"name": "file.png"}
    return web.json_response(resp)

@routes.post("/upload/image")
async def upload_image(request):
    post = await request.post()
    return image_upload(post)
'''

        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            out_path = Path(tmp) / "server_endpoints.json"
            server_path.write_text(sample, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(server_path), "--output", str(out_path)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(data["endpoints"][0]["returns"]["kind"], "json")
            self.assertIn(400, data["endpoints"][0]["returns"]["status_codes"])

    def test_nested_function_ignored(self):
        """Nested function definitions should not confuse response inference."""
        sample = '''
@routes.post("/upload/mask")
async def upload_mask(request):
    post = await request.post()

    def image_save_function(image, post, filepath):
        if not post.get("image"):
            return web.Response(status=400)
        with open(filepath, "wb") as f:
            f.write(image.file.read())

    return image_upload(post, image_save_function)
'''

        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            out_path = Path(tmp) / "server_endpoints.json"
            server_path.write_text(sample, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(server_path), "--output", str(out_path)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            # The nested Response should be ignored; since image_upload is not defined
            # in this sample, it falls back to unknown.
            self.assertEqual(data["endpoints"][0]["returns"]["kind"], "unknown")

    def test_json_response_with_error_response_elsewhere(self):
        """When a handler has both web.Response(status=404) and a json_response,
        the endpoint contract should preserve both success and explicit error codes."""
        sample = '''
@routes.get("/models/{folder}")
async def get_models(request):
    folder = request.match_info.get("folder", None)
    if folder not in folder_paths.folder_names_and_paths:
        return web.Response(status=404)
    files = folder_paths.get_filename_list(folder)
    return web.json_response(files)
'''

        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            out_path = Path(tmp) / "server_endpoints.json"
            server_path.write_text(sample, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(server_path), "--output", str(out_path)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            # The json_response has no explicit status, so it defaults to 200,
            # but the handler also documents an explicit 404 branch.
            self.assertEqual(data["endpoints"][0]["returns"]["kind"], "json")
            self.assertIn(200, data["endpoints"][0]["returns"]["status_codes"])
            self.assertIn(404, data["endpoints"][0]["returns"]["status_codes"])

    def test_json_response_with_explicit_error_status(self):
        """When a json_response has an explicit error status in its argument,
        that status should be reflected in the output."""
        sample = '''
@routes.post("/resource")
def create_resource(request):
    data = await request.json()
    if not data.get("name"):
        return web.json_response({"error": "name required"}, status=400)
    return web.json_response({"id": "123"})
'''

        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            out_path = Path(tmp) / "server_endpoints.json"
            server_path.write_text(sample, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(server_path), "--output", str(out_path)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            # Should prefer the success response (more fields)
            self.assertEqual(data["endpoints"][0]["returns"]["kind"], "json")
            # The success response has no explicit status, so it defaults to 200
            self.assertIn(200, data["endpoints"][0]["returns"]["status_codes"])

    def test_json_response_variable_payload_and_augmented_fields(self):
        """Variable-backed dict payloads should expose literal and augmented keys."""
        sample = '''
@routes.post("/upload/image")
async def upload_image(request):
    resp = {"name": "file.png", "subfolder": "", "type": "input"}
    if request.query.get("asset"):
        resp["asset"] = {"id": "123"}
    return web.json_response(resp)
'''

        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            out_path = Path(tmp) / "server_endpoints.json"
            server_path.write_text(sample, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(server_path), "--output", str(out_path)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            fields = {f["name"] for f in data["endpoints"][0]["returns"]["fields"]}
            self.assertEqual(fields, {"name", "subfolder", "type", "asset"})
            self.assertEqual(
                data["endpoints"][0]["returns"]["summary"],
                "JSON object with fields: name, subfolder, type, asset.",
            )

    def test_extracts_route_and_query_parameter_details(self):
        sample = '''
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
'''

        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            out_path = Path(tmp) / "server_endpoints.json"
            server_path.write_text(sample, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(server_path), "--output", str(out_path)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            params = {(param["name"], param["location"]): param for param in data["endpoints"][0]["parameters"]}
            self.assertTrue(params[("folder", "path")]["required"])
            self.assertEqual(params[("limit", "query")]["default"], 50)
            self.assertEqual(params[("sort_order", "query")]["allowed_values"], ["asc", "desc"])
            self.assertEqual(
                params[("folder", "path")]["traceability"]["strategy"],
                "route_token",
            )

    def test_extracts_form_parameters_from_helper(self):
        sample = '''
def image_upload(post):
    image = post.get("image")
    overwrite = post.get("overwrite", False)
    return web.json_response({"ok": True})

@routes.post("/upload/image")
async def upload_image(request):
    post = await request.post()
    return image_upload(post)
'''

        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            out_path = Path(tmp) / "server_endpoints.json"
            server_path.write_text(sample, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(server_path), "--output", str(out_path)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            params = {(param["name"], param["location"]): param for param in data["endpoints"][0]["parameters"]}
            self.assertIn(("image", "form"), params)
            self.assertEqual(params[("overwrite", "form")]["default"], False)

    def test_return_traceability_added(self):
        sample = '''
@routes.get("/ws")
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    return ws
'''
        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            out_path = Path(tmp) / "server_endpoints.json"
            server_path.write_text(sample, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(server_path), "--output", str(out_path)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            returns = data["endpoints"][0]["returns"]
            self.assertEqual(returns["traceability"]["strategy"], "web.WebSocketResponse")

    def test_sibling_helper_definitions_do_not_contaminate_route(self):
        """Top-level helpers after a route should not leak fields into that route."""
        sample = '''
@routes.get("/extensions")
def get_extensions(request):
    extensions = ["/a.js"]
    return web.json_response(extensions)

def image_upload(post):
    resp = {"name": "file.png", "subfolder": "", "type": "input"}
    resp["asset"] = {"id": "123"}
    return web.json_response(resp)
'''

        with tempfile.TemporaryDirectory() as tmp:
            server_path = Path(tmp) / "server.py"
            out_path = Path(tmp) / "server_endpoints.json"
            server_path.write_text(sample, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(server_path), "--output", str(out_path)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            returns = data["endpoints"][0]["returns"]
            self.assertEqual(returns["kind"], "json")
            self.assertEqual(returns["fields"], [])
            self.assertEqual(returns["status_codes"], [200])


if __name__ == "__main__":
    unittest.main()
