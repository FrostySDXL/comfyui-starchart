import json
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "extract" / "parse_hooks.py"


def _load_validate_schema():
    spec = importlib.util.spec_from_file_location(
        "validate_schema",
        REPO_ROOT / "scripts" / "verify" / "validate_schema.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ParseHooksTests(unittest.TestCase):
    def test_requires_argument(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_extracts_hooks_to_json(self):
        sample = '''
invokeExtensions("beforeRegisterNodeDef", nodeDef, nodeData)
invokeExtensionsAsync("setup")
app.registerExtension({
  async init() {},
  async setup() {},
  async nodeCreated(node) {}
})
'''

        with tempfile.TemporaryDirectory() as tmp:
            app_path = Path(tmp) / "app.js"
            out_path = Path(tmp) / "js_hooks.json"
            app_path.write_text(sample, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(app_path), "--version", "v0.0.1", "--commit", "abc123", "--output", str(out_path)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("Extracted", result.stdout)

            data = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertIn("sources", data["metadata"])
            self.assertIsInstance(data["metadata"]["sources"], list)
            self.assertNotIn("source", data["metadata"])
            self.assertIn("coverage", data)
            self.assertIn("description", data["coverage"])
            self.assertIn("guaranteed_fields", data["coverage"])
            self.assertIn("best_effort_fields", data["coverage"])
            self.assertIn("deferred", data["coverage"])
            names = {entry["name"] for entry in data["hooks"]}
            self.assertIn("beforeRegisterNodeDef", names)
            self.assertIn("setup", names)
            self.assertIn("init", names)
            self.assertIn("nodeCreated", names)

            validate_schema = _load_validate_schema()
            errors = validate_schema.validate_top_level(data, validate_schema.SCHEMAS["js_hooks.json"], "js_hooks.json")
            errors.extend(validate_schema.validate_metadata(data, "js_hooks.json"))
            errors.extend(validate_schema.validate_coverage(data, "js_hooks.json"))
            errors.extend(validate_schema.validate_hooks(data, "js_hooks.json"))
            self.assertEqual(errors, [], msg=f"Schema errors: {errors}")

    def test_invocation_only_hooks_dedupe_invoked_in(self):
        app_sample = '''
invokeExtensions("onNodeOutputsUpdated", value)
invokeExtensions("onNodeOutputsUpdated", otherValue)
'''
        service_sample = '''
invokeExtensionsAsync("onNodeOutputsUpdated", payload)
'''

        with tempfile.TemporaryDirectory() as tmp:
            app_path = Path(tmp) / "app.ts"
            service_path = Path(tmp) / "service.ts"
            out_path = Path(tmp) / "js_hooks.json"
            app_path.write_text(app_sample, encoding="utf-8")
            service_path.write_text(service_sample, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(app_path), str(service_path), "--output", str(out_path)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            entry = next(hook for hook in data["hooks"] if hook["name"] == "onNodeOutputsUpdated")
            self.assertEqual(entry["defined_in"], None)
            self.assertEqual(entry["description"], "")
            self.assertEqual(entry["invoked_in"], [str(app_path).replace("\\", "/"), str(service_path).replace("\\", "/")])

    def test_typed_hook_comment_survives_blank_lines_and_comment_lines(self):
        sample = '''
/**
 * Allows additional setup.
 */

// implementation note
setup?(app: ComfyApp): Promise<void> | void
'''

        with tempfile.TemporaryDirectory() as tmp:
            app_path = Path(tmp) / "comfy.ts"
            out_path = Path(tmp) / "js_hooks.json"
            app_path.write_text(sample, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(app_path), "--output", str(out_path)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            entry = next(hook for hook in data["hooks"] if hook["name"] == "setup")
            self.assertEqual(entry["description"], "Allows additional setup.")

    def test_typed_hook_signature_and_invocation_style_are_enriched(self):
        typed_sample = '''
/**
 * Allows additional setup.
 */
setup?(app: ComfyApp): Promise<void> | void

/**
 * Called before nodes are registered.
 */
beforeRegisterNodeDef?(
  nodeType: typeof LGraphNode,
  nodeData: ComfyNodeDef,
  app: ComfyApp
): Promise<void> | void
'''
        invocation_sample = '''
invokeExtensionsAsync("setup")
invokeExtensionsAsync("beforeRegisterNodeDef", nodeType, nodeData, app)
'''

        with tempfile.TemporaryDirectory() as tmp:
            typed_path = Path(tmp) / "comfy.ts"
            app_path = Path(tmp) / "app.ts"
            out_path = Path(tmp) / "js_hooks.json"
            typed_path.write_text(typed_sample, encoding="utf-8")
            app_path.write_text(invocation_sample, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(typed_path), str(app_path), "--output", str(out_path)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            setup = next(hook for hook in data["hooks"] if hook["name"] == "setup")
            before_register = next(hook for hook in data["hooks"] if hook["name"] == "beforeRegisterNodeDef")

            self.assertEqual(setup["signature"], "setup?(app: ComfyApp): Promise<void> | void")
            self.assertEqual(setup["arguments"], [{"name": "app", "type_hint": "ComfyApp"}])
            self.assertEqual(setup["return_type"], "Promise<void> | void")
            self.assertEqual(setup["invocation_style"], ["async"])
            self.assertEqual(setup["traceability"]["strategy"], "typed_definition")

            self.assertEqual(
                before_register["arguments"],
                [
                    {"name": "nodeType", "type_hint": "typeof LGraphNode"},
                    {"name": "nodeData", "type_hint": "ComfyNodeDef"},
                    {"name": "app", "type_hint": "ComfyApp"},
                ],
            )


if __name__ == "__main__":
    unittest.main()
