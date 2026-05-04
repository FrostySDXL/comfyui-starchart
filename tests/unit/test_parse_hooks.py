import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.unit.helpers.extractor_test_utils import call_main, load_module


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "extract" / "parse_hooks.py"


def _load_validate_schema():
    return load_module("validate_schema", REPO_ROOT / "scripts" / "verify" / "validate_schema.py")


def _load_parse_hooks():
    return load_module("parse_hooks", SCRIPT)


def _run_parse_hooks_main(*args: str):
    return call_main(_load_parse_hooks(), *args)


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
        parse_hooks = _load_parse_hooks()
        data = {
            "metadata": {
                "sources": ["tmp/app.js"],
                "extracted_date": "2026-05-03",
                "version": "v0.0.1",
                "commit": "abc123",
            },
            "coverage": parse_hooks.HOOK_COVERAGE,
            "hooks": parse_hooks.extract_hooks({"tmp/app.js": sample}),
        }

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

        hooks = _load_parse_hooks().extract_hooks(
            {
                "tmp/app.ts": app_sample,
                "tmp/service.ts": service_sample,
            }
        )
        entry = next(hook for hook in hooks if hook["name"] == "onNodeOutputsUpdated")
        self.assertEqual(entry["defined_in"], None)
        self.assertEqual(entry["description"], "")
        self.assertEqual(entry["invoked_in"], ["tmp/app.ts", "tmp/service.ts"])

    def test_typed_hook_comment_survives_blank_lines_and_comment_lines(self):
        sample = '''
/**
 * Allows additional setup.
 */

// implementation note
setup?(app: ComfyApp): Promise<void> | void
'''

        hooks = _load_parse_hooks().extract_hooks({"tmp/comfy.ts": sample})
        entry = next(hook for hook in hooks if hook["name"] == "setup")
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

        hooks = _load_parse_hooks().extract_hooks(
            {
                "tmp/comfy.ts": typed_sample,
                "tmp/app.ts": invocation_sample,
            }
        )
        setup = next(hook for hook in hooks if hook["name"] == "setup")
        before_register = next(hook for hook in hooks if hook["name"] == "beforeRegisterNodeDef")

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

    def test_metadata_sources_and_invoked_in_are_repo_relative_when_inputs_are_in_repo(self):
        sample = '''
invokeExtensions("beforeRegisterNodeDef", nodeDef, nodeData)
'''

        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
            tmp_path = Path(tmp)
            app_path = tmp_path / "app.ts"
            out_path = tmp_path / "js_hooks.json"
            app_path.write_text(sample, encoding="utf-8")

            exit_code, _stdout, stderr = _run_parse_hooks_main(str(app_path), "--output", str(out_path))

            self.assertEqual(exit_code, 0, msg=stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            expected_path = app_path.relative_to(REPO_ROOT).as_posix()
            self.assertEqual(data["metadata"]["sources"], [expected_path])
            entry = next(hook for hook in data["hooks"] if hook["name"] == "beforeRegisterNodeDef")
            self.assertEqual(entry["invoked_in"], [expected_path])


if __name__ == "__main__":
    unittest.main()
