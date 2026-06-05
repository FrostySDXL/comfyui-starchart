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
        sample = """
invokeExtensions("beforeRegisterNodeDef", nodeDef, nodeData)
invokeExtensionsAsync("setup")
app.registerExtension({
  async init() {},
  async setup() {},
  async nodeCreated(node) {}
})
"""
        parse_hooks = _load_parse_hooks()
        data = {
            "metadata": {
                "sources": ["tmp/app.js"],
                "extracted_date": "2026-05-03",
                "version": "v0.0.1",
                "commit": "abc123",
            },
            "coverage": parse_hooks.HOOK_COVERAGE,
            "extension_fields": [],
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
        errors = validate_schema.validate_top_level(
            data, validate_schema.SCHEMAS["js_hooks.json"], "js_hooks.json"
        )
        errors.extend(validate_schema.validate_metadata(data, "js_hooks.json"))
        errors.extend(validate_schema.validate_coverage(data, "js_hooks.json"))
        errors.extend(validate_schema.validate_hooks(data, "js_hooks.json"))
        self.assertEqual(errors, [], msg=f"Schema errors: {errors}")

    def test_extracts_extension_fields_from_comfy_extension(self):
        sample = """
export interface ComfyExtension {
  /**
   * The name of the extension
   */
  name: string
  /**
   * The commands defined by the extension
   */
  commands?: ComfyCommand[]
  /**
   * The keybindings defined by the extension
   */
  keybindings?: Keybinding[]
  /**
   * Menu commands to add to the menu bar
   */
  menuCommands?: MenuCommandGroup[]
  /**
   * Settings to add to the settings menu
   */
  settings?: SettingParams[]
  /**
   * Bottom panel tabs to add to the bottom panel
   */
  bottomPanelTabs?: BottomPanelExtension[]
  /**
   * Badges to add to the about page
   */
  aboutPageBadges?: AboutPageBadge[]
  /**
   * Badges to add to the top bar
   */
  topbarBadges?: TopbarBadge[]
  /**
   * Buttons to add to the action bar
   */
  actionBarButtons?: ActionBarButton[]
  /**
   * Allows the extension to add custom widgets
   */
  getCustomWidgets?(app: ComfyApp): Promise<Widgets> | Widgets
  /**
   * Allows the extension to add additional handling to the node before it is registered with LGraph
   */
  beforeRegisterNodeDef?(nodeType: typeof LGraphNode, nodeData: ComfyNodeDef, app: ComfyApp): Promise<void> | void
  /**
   * Allows the extension to modify a node that has been reloaded onto the graph.
   */
  loadedGraphNode?(node: LGraphNode, app: ComfyApp): void
  /**
   * Allows the extension to run code after the constructor of the node
   */
  nodeCreated?(node: LGraphNode, app: ComfyApp): void
  [key: string]: unknown
}
"""

        parse_hooks = _load_parse_hooks()
        hooks = parse_hooks.extract_hooks({"tmp/comfy.ts": sample})
        fields = parse_hooks.extract_extension_fields(
            {"tmp/comfy.ts": sample}, hook_names={entry["name"] for entry in hooks}
        )
        by_name = {entry["name"]: entry for entry in fields}

        for name in {
            "name",
            "commands",
            "keybindings",
            "menuCommands",
            "settings",
            "bottomPanelTabs",
            "aboutPageBadges",
            "topbarBadges",
            "actionBarButtons",
            "getCustomWidgets",
            "beforeRegisterNodeDef",
            "nodeCreated",
            "loadedGraphNode",
            "[key: string]",
        }:
            self.assertIn(name, by_name)

        self.assertEqual(by_name["name"]["type_hint"], "string")
        self.assertTrue(by_name["name"]["required"])
        self.assertEqual(by_name["commands"]["type_hint"], "ComfyCommand[]")
        self.assertFalse(by_name["commands"]["required"])
        self.assertEqual(
            by_name["beforeRegisterNodeDef"]["type_hint"],
            "(nodeType: typeof LGraphNode, nodeData: ComfyNodeDef, app: ComfyApp) => Promise<void> | void",
        )
        self.assertIn("additional handling", by_name["beforeRegisterNodeDef"]["description"])
        self.assertEqual(by_name["beforeRegisterNodeDef"]["defined_in"], "tmp/comfy.ts")
        self.assertTrue(by_name["beforeRegisterNodeDef"]["is_hook"])
        self.assertFalse(by_name["commands"]["is_hook"])
        self.assertTrue(by_name["[key: string]"]["is_index_signature"])
        for field in fields:
            self.assertIsInstance(field["is_hook"], bool)
            self.assertIn("traceability", field)

    def test_extension_field_description_is_omitted_when_comment_is_missing(self):
        parse_hooks = _load_parse_hooks()
        sample = """
export interface ComfyExtension {
  name: string
}
"""

        fields = parse_hooks.extract_extension_fields({"tmp/comfy.ts": sample}, hook_names=set())
        name_field = next(field for field in fields if field["name"] == "name")

        self.assertNotIn("description", name_field)

    def test_inline_jsdoc_extension_field_description_is_preserved(self):
        parse_hooks = _load_parse_hooks()
        sample = """
export interface ComfyExtension {
  /** The extension name. */ name: string
}
"""

        fields = parse_hooks.extract_extension_fields({"tmp/comfy.ts": sample}, hook_names=set())
        name_field = next(field for field in fields if field["name"] == "name")

        self.assertEqual(name_field["description"], "The extension name.")

    def test_consecutive_jsdoc_blocks_are_preserved_for_next_extension_field(self):
        parse_hooks = _load_parse_hooks()
        sample = """
export interface ComfyExtension {
  /** Primary description. */
  /** Additional note. */
  name: string
}
"""

        fields = parse_hooks.extract_extension_fields({"tmp/comfy.ts": sample}, hook_names=set())
        name_field = next(field for field in fields if field["name"] == "name")

        self.assertIn("Primary description.", name_field["description"])
        self.assertIn("Additional note.", name_field["description"])

    def test_main_output_includes_extension_fields_list(self):
        sample = """
export interface ComfyExtension {
  /** The name of the extension */
  name: string
  /** Allows any initialisation. */
  init?(app: ComfyApp): Promise<void> | void
}
"""

        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
            tmp_path = Path(tmp)
            comfy_path = tmp_path / "comfy.ts"
            out_path = tmp_path / "js_hooks.json"
            comfy_path.write_text(sample, encoding="utf-8")

            exit_code, _stdout, stderr = _run_parse_hooks_main(
                str(comfy_path), "--output", str(out_path)
            )

            self.assertEqual(exit_code, 0, msg=stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertIn("extension_fields", data)
            self.assertIsInstance(data["extension_fields"], list)
            init_field = next(
                field for field in data["extension_fields"] if field["name"] == "init"
            )
            self.assertTrue(init_field["is_hook"])

    def test_missing_comfy_extension_source_returns_empty_fields_with_deferred_note(self):
        parse_hooks = _load_parse_hooks()
        coverage = parse_hooks.build_hook_coverage([])

        self.assertEqual(parse_hooks.extract_extension_fields({}, hook_names=set()), [])
        self.assertTrue(
            any("no frontend source files" in note for note in coverage["deferred"]),
            msg=coverage["deferred"],
        )

    def test_source_without_comfy_extension_returns_empty_fields(self):
        parse_hooks = _load_parse_hooks()
        source_map = {"tmp/other.ts": "export interface Other { name: string }"}
        fields = parse_hooks.extract_extension_fields(source_map, hook_names=set())
        coverage = parse_hooks.build_hook_coverage(fields, source_map)

        self.assertEqual(fields, [])
        self.assertTrue(
            any("did not declare the interface" in note for note in coverage["deferred"]),
            msg=coverage["deferred"],
        )

    def test_unparseable_extension_member_is_skipped_without_dropping_following_field(self):
        parse_hooks = _load_parse_hooks()
        sample = """
export interface ComfyExtension {
  readonly foo: string
  name: string
}
"""

        fields = parse_hooks.extract_extension_fields({"tmp/comfy.ts": sample}, hook_names=set())
        field_names = {field["name"] for field in fields}

        self.assertNotIn("foo", field_names)
        self.assertIn("name", field_names)

    def test_unparseable_extension_member_adds_deferred_note(self):
        parse_hooks = _load_parse_hooks()
        sample = """
export interface ComfyExtension {
  readonly foo: string
  name: string
}
"""
        deferred = []

        fields = parse_hooks.extract_extension_fields(
            {"tmp/comfy.ts": sample}, hook_names=set(), deferred=deferred
        )
        coverage = parse_hooks.build_hook_coverage(fields, {"tmp/comfy.ts": sample}, deferred)

        self.assertTrue(
            any("unparseable ComfyExtension member" in note for note in coverage["deferred"]),
            msg=coverage["deferred"],
        )

    def test_extension_field_multiline_object_type_tracks_brace_depth(self):
        parse_hooks = _load_parse_hooks()
        sample = """
export interface ComfyExtension {
  /** Options preserved as a single property. */
  options?: {
    alpha: string;
    beta: Array<{ name: string }>;
  };
  setup?(): void;
}
"""

        fields = parse_hooks.extract_extension_fields({"tmp/comfy.ts": sample}, hook_names=set())

        options = next(field for field in fields if field["name"] == "options")
        self.assertEqual(
            options["type_hint"],
            "{ alpha: string; beta: Array<{ name: string }>; }",
        )
        self.assertIn("setup", {field["name"] for field in fields})

    def test_extension_field_multiline_method_without_semicolon_stops_at_signature_end(self):
        parse_hooks = _load_parse_hooks()
        sample = """
export interface ComfyExtension {
  /** Add definitions */
  addCustomNodeDefs?(
    defs: Record<string, ComfyNodeDef>,
    app: ComfyApp
  ): Promise<void> | void
  /** Add widgets */
  getCustomWidgets?(app: ComfyApp): Promise<Widgets> | Widgets
}
"""

        fields = parse_hooks.extract_extension_fields({"tmp/comfy.ts": sample}, hook_names=set())
        names = {field["name"]: field for field in fields}

        self.assertEqual(
            names["addCustomNodeDefs"]["type_hint"],
            "(defs: Record<string, ComfyNodeDef>, app: ComfyApp) => Promise<void> | void",
        )
        self.assertIn("getCustomWidgets", names)

    def test_malformed_comfy_extension_source_raises_clear_error(self):
        parse_hooks = _load_parse_hooks()
        sample = """
export interface ComfyExtension {
  name: string
"""

        with self.assertRaisesRegex(ValueError, "ComfyExtension interface block"):
            parse_hooks.extract_extension_fields({"tmp/comfy.ts": sample}, hook_names=set())

    def test_invocation_only_hooks_dedupe_invoked_in(self):
        app_sample = """
invokeExtensions("onNodeOutputsUpdated", value)
invokeExtensions("onNodeOutputsUpdated", otherValue)
"""
        service_sample = """
invokeExtensionsAsync("onNodeOutputsUpdated", payload)
"""

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
        sample = """
/**
 * Allows additional setup.
 */

// implementation note
setup?(app: ComfyApp): Promise<void> | void
"""

        hooks = _load_parse_hooks().extract_hooks({"tmp/comfy.ts": sample})
        entry = next(hook for hook in hooks if hook["name"] == "setup")
        self.assertEqual(entry["description"], "Allows additional setup.")

    def test_typed_hook_signature_and_invocation_style_are_enriched(self):
        typed_sample = """
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
"""
        invocation_sample = """
invokeExtensionsAsync("setup")
invokeExtensionsAsync("beforeRegisterNodeDef", nodeType, nodeData, app)
"""

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
        sample = """
invokeExtensions("beforeRegisterNodeDef", nodeDef, nodeData)
"""

        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
            tmp_path = Path(tmp)
            app_path = tmp_path / "app.ts"
            out_path = tmp_path / "js_hooks.json"
            app_path.write_text(sample, encoding="utf-8")

            exit_code, _stdout, stderr = _run_parse_hooks_main(
                str(app_path), "--output", str(out_path)
            )

            self.assertEqual(exit_code, 0, msg=stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            expected_path = app_path.relative_to(REPO_ROOT).as_posix()
            self.assertEqual(data["metadata"]["sources"], [expected_path])
            entry = next(hook for hook in data["hooks"] if hook["name"] == "beforeRegisterNodeDef")
            self.assertEqual(entry["invoked_in"], [expected_path])


if __name__ == "__main__":
    unittest.main()
