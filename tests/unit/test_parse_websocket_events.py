import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.unit.helpers.extractor_test_utils import call_main, load_module

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "extract" / "parse_websocket_events.py"


def _load_parse_websocket_events():
    return load_module("parse_websocket_events", SCRIPT)


def _run_parse_websocket_events_main(*args: str):
    return call_main(_load_parse_websocket_events(), *args)


SERVER_SAMPLE = """
class PromptServer:
    async def websocket_handler(self, request):
        await self.send("status", {"status": self.get_queue_info()}, sid=sid)
        await self.send("executing", {"node": None, "prompt_id": prompt_id}, sid=sid)

    def queue_updated(self):
        self.send_sync("status", {"exec_info": self.get_queue_info()})

    def send_json(self, event, data, sid=None):
        message = {"type": event, "data": data}

    def send_preview(self, image, sid=None):
        self.send_bytes(BinaryEventTypes.PREVIEW_IMAGE_WITH_METADATA, image, sid=sid)

"""

EXECUTION_SAMPLE = """
class PromptExecutor:
    def execute(self, prompt_id):
        self.server.send_sync("executing", {"node": "3", "display_node": "3", "prompt_id": prompt_id})
        self.server.send_sync("executed", {"node": "3", "display_node": "3", "output": {}, "prompt_id": prompt_id})
        self.server.send_sync("execution_error", {"prompt_id": prompt_id})

    def add_message(self, event, data, broadcast=True):
        self.server.send_sync(event, data, broadcast=broadcast)

    def messages(self, prompt_id):
        self.add_message("execution_start", {"prompt_id": prompt_id})
        self.add_message("execution_interrupted", {"prompt_id": prompt_id})
        self.add_message("execution_cached", {"nodes": [], "prompt_id": prompt_id})
        self.add_message("execution_success", {"prompt_id": prompt_id})
"""

MAIN_SAMPLE = """
def hijack_progress(server_instance, prompt_id):
    progress = {"value": 1, "max": 10, "prompt_id": prompt_id, "node": "7"}
    server_instance.send_sync("progress", progress, server_instance.client_id)
"""

PROTOCOL_SAMPLE = """
class BinaryEventTypes:
    PREVIEW_IMAGE = 1
    UNENCODED_PREVIEW_IMAGE = 2
    TEXT = 3
    PREVIEW_IMAGE_WITH_METADATA = 4
"""

PROGRESS_SAMPLE = """
class WebUIProgressHandler:
    def _send_progress_state(self, prompt_id):
        self.server.send_sync("progress_state", {"prompt_id": prompt_id, "nodes": {}})

    def update_handler(self, preview_bytes):
        self.server.send_sync(BinaryEventTypes.PREVIEW_IMAGE_WITH_METADATA, preview_bytes)
"""

APP_SAMPLE = """
class ComfyApp {
  private addApiUpdateHandlers() {
    api.addEventListener('status', ({ detail }) => {})
    api.addEventListener('progress', ({ detail }) => {})
    api.addEventListener('executing', ({ detail }) => {})
    api.addEventListener('executed', ({ detail }) => {})
    api.addEventListener('execution_start', ({ detail }) => {})
    api.addEventListener('execution_error', ({ detail }) => {})
    api.addEventListener('feature_flags', async () => {})
    api.addEventListener('b_preview_with_metadata', (event) => {})
  }
}
"""


def _sample_sources(include_protocol=True, include_main=True, include_progress=True):
    sources = {
        "references/snapshots/sample/comfyui-core/server.py": SERVER_SAMPLE,
        "references/snapshots/sample/comfyui-core/execution.py": EXECUTION_SAMPLE,
        "references/snapshots/sample/comfyui-frontend/src/scripts/app.ts": APP_SAMPLE,
    }
    if include_main:
        sources["references/snapshots/sample/comfyui-core/main.py"] = MAIN_SAMPLE
    if include_protocol:
        sources["references/snapshots/sample/comfyui-core/protocol.py"] = PROTOCOL_SAMPLE
    if include_progress:
        sources["references/snapshots/sample/comfyui-core/comfy_execution/progress.py"] = (
            PROGRESS_SAMPLE
        )
    return sources


class ParseWebsocketEventsTests(unittest.TestCase):
    def test_requires_argument(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage", (result.stdout + result.stderr).lower())

    def test_extracts_event_and_binary_contract_shape(self):
        parser = _load_parse_websocket_events()
        data = parser.build_artifact(
            _sample_sources(),
            version="core-v0.23.0+frontend-v1.46.6",
            commit="abc123",
        )

        self.assertEqual(set(data), {"metadata", "coverage", "events", "binary_events"})
        self.assertIn("sources", data["metadata"])
        self.assertIsInstance(data["metadata"]["sources"], list)
        self.assertNotIn("source", data["metadata"])
        for key in ("description", "guaranteed_fields", "best_effort_fields", "deferred"):
            self.assertIn(key, data["coverage"])

        guaranteed = set(data["coverage"]["guaranteed_fields"])
        self.assertIn("events.name", guaranteed)
        self.assertIn("events.traceability", guaranteed)
        self.assertIn("binary_events.name", guaranteed)
        best_effort = set(data["coverage"]["best_effort_fields"])
        self.assertIn("events.payload_fields", best_effort)
        self.assertIn("binary_events.enum_value", best_effort)

        event_by_name = {event["name"]: event for event in data["events"]}
        for name in {
            "status",
            "progress",
            "progress_state",
            "executing",
            "executed",
            "execution_start",
            "execution_error",
            "execution_interrupted",
            "execution_cached",
            "execution_success",
            "feature_flags",
        }:
            self.assertIn(name, event_by_name)

        for event in data["events"]:
            self.assertIn("name", event)
            self.assertIn("direction", event)
            self.assertIn("server_sources", event)
            self.assertIn("frontend_listeners", event)
            self.assertIn("traceability", event)
            self.assertTrue("payload_fields" in event or "payload_notes" in event)

        self.assertEqual(event_by_name["feature_flags"]["direction"], "bidirectional")
        self.assertEqual(event_by_name["progress"]["direction"], "server_to_client")
        self.assertTrue(
            any(
                source["source_file"].endswith("main.py")
                for source in event_by_name["progress"]["server_sources"]
            )
        )
        self.assertTrue(event_by_name["progress"]["frontend_listeners"])
        self.assertEqual(
            set(event_by_name["progress"]["payload_fields"]),
            {"value", "max", "prompt_id", "node"},
        )
        self.assertTrue(
            any(
                source["source_file"].endswith("comfy_execution/progress.py")
                for source in event_by_name["progress_state"]["server_sources"]
            )
        )

        dynamic_trace = " ".join(event_by_name["execution_start"]["traceability"].get("notes", []))
        self.assertIn("add_message", dynamic_trace)

        binary_by_name = {event["name"]: event for event in data["binary_events"]}
        for name in {
            "PREVIEW_IMAGE",
            "UNENCODED_PREVIEW_IMAGE",
            "TEXT",
            "PREVIEW_IMAGE_WITH_METADATA",
        }:
            self.assertIn(name, binary_by_name)
            self.assertIn("traceability", binary_by_name[name])
        self.assertEqual(binary_by_name["PREVIEW_IMAGE_WITH_METADATA"]["enum_value"], 4)

    def test_missing_protocol_keeps_empty_binary_events_with_deferred_note(self):
        parser = _load_parse_websocket_events()
        data = parser.build_artifact(
            _sample_sources(include_protocol=False), version="v0", commit="abc"
        )

        self.assertEqual(data["binary_events"], [])
        self.assertTrue(
            any("protocol.py" in note for note in data["coverage"].get("deferred", [])),
            msg=data["coverage"].get("deferred", []),
        )

    def test_missing_main_keeps_progress_event_with_degraded_note(self):
        parser = _load_parse_websocket_events()
        data = parser.build_artifact(
            _sample_sources(include_main=False), version="v0", commit="abc"
        )
        progress = next(event for event in data["events"] if event["name"] == "progress")

        self.assertEqual(progress["server_sources"], [])
        self.assertTrue(progress["frontend_listeners"])
        self.assertTrue(any("main.py" in note for note in progress.get("payload_notes", [])))

    def test_no_recognizable_events_still_emits_valid_empty_sections(self):
        parser = _load_parse_websocket_events()
        data = parser.build_artifact(
            {"tmp/server.py": "print('nothing')"}, version="v0", commit="abc"
        )

        self.assertEqual(set(data), {"metadata", "coverage", "events", "binary_events"})
        self.assertEqual(data["events"], [])
        self.assertEqual(data["binary_events"], [])

    def test_cli_writes_repo_relative_metadata_sources(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
            tmp_path = Path(tmp)
            server_path = tmp_path / "server.py"
            main_path = tmp_path / "main.py"
            execution_path = tmp_path / "execution.py"
            protocol_path = tmp_path / "protocol.py"
            progress_dir = tmp_path / "comfy_execution"
            progress_dir.mkdir()
            progress_path = progress_dir / "progress.py"
            app_path = tmp_path / "app.ts"
            out_path = tmp_path / "websocket_events.json"
            server_path.write_text(SERVER_SAMPLE, encoding="utf-8")
            main_path.write_text(MAIN_SAMPLE, encoding="utf-8")
            execution_path.write_text(EXECUTION_SAMPLE, encoding="utf-8")
            protocol_path.write_text(PROTOCOL_SAMPLE, encoding="utf-8")
            progress_path.write_text(PROGRESS_SAMPLE, encoding="utf-8")
            app_path.write_text(APP_SAMPLE, encoding="utf-8")

            exit_code, _stdout, stderr = _run_parse_websocket_events_main(
                str(server_path),
                str(main_path),
                str(execution_path),
                str(protocol_path),
                str(progress_path),
                str(app_path),
                "--version",
                "core-v0.23.0+frontend-v1.46.6",
                "--commit",
                "abc123",
                "--output",
                str(out_path),
            )

            self.assertEqual(exit_code, 0, msg=stderr)
            data = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(
                data["metadata"]["sources"],
                [
                    server_path.relative_to(REPO_ROOT).as_posix(),
                    main_path.relative_to(REPO_ROOT).as_posix(),
                    execution_path.relative_to(REPO_ROOT).as_posix(),
                    protocol_path.relative_to(REPO_ROOT).as_posix(),
                    progress_path.relative_to(REPO_ROOT).as_posix(),
                    app_path.relative_to(REPO_ROOT).as_posix(),
                ],
            )


if __name__ == "__main__":
    unittest.main()
