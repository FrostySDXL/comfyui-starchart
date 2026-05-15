"""Tests for scripts/generate/generate_snapshot_delta_summary.py."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "generate" / "generate_snapshot_delta_summary.py"


class GenerateSnapshotDeltaSummaryTests(unittest.TestCase):
    def _write_baseline(
        self,
        root: Path,
        server_endpoints: list,
        hooks: list,
        io_types: list,
        object_info_fields: list,
        typed_input_shapes: dict,
    ) -> None:
        (root / "server_endpoints.json").write_text(
            json.dumps({"metadata": {}, "coverage": {}, "endpoints": server_endpoints}),
            encoding="utf-8",
        )
        (root / "js_hooks.json").write_text(
            json.dumps({"metadata": {}, "coverage": {}, "hooks": hooks}),
            encoding="utf-8",
        )
        (root / "node_api_schema.json").write_text(
            json.dumps(
                {
                    "metadata": {},
                    "coverage": {},
                    "object_info_fields": object_info_fields,
                    "io_types": io_types,
                    "basic_input_shapes": {},
                    "typed_input_shapes": typed_input_shapes,
                }
            ),
            encoding="utf-8",
        )

    def test_builds_deterministic_delta_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            old_dir = tmp_path / "old"
            new_dir = tmp_path / "new"
            old_dir.mkdir()
            new_dir.mkdir()
            output_path = tmp_path / "delta.json"

            self._write_baseline(
                old_dir,
                server_endpoints=[{"method": "GET", "route": "/a", "returns": {"kind": "json"}}],
                hooks=[{"name": "setup"}],
                io_types=[{"io_type": "BOOLEAN", "class_name": "Boolean"}],
                object_info_fields=["input"],
                typed_input_shapes={"AudioInput": {"description": "audio", "fields": {}}},
            )
            self._write_baseline(
                new_dir,
                server_endpoints=[
                    {
                        "method": "GET",
                        "route": "/a",
                        "returns": {"kind": "json", "summary": "changed"},
                    },
                    {"method": "POST", "route": "/b", "returns": {"kind": "json"}},
                ],
                hooks=[{"name": "setup"}, {"name": "nodeCreated"}],
                io_types=[
                    {"io_type": "BOOLEAN", "class_name": "Boolean"},
                    {"io_type": "FLOAT", "class_name": "Float"},
                ],
                object_info_fields=["input", "output"],
                typed_input_shapes={"AudioInput": {"description": "audio changed", "fields": {}}},
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--old",
                    str(old_dir),
                    "--new",
                    str(new_dir),
                    "--output",
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            data = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(data["artifacts"]["server_endpoints"]["added"], ["POST /b"])
            self.assertEqual(data["artifacts"]["server_endpoints"]["changed"], ["GET /a"])
            self.assertEqual(data["artifacts"]["js_hooks"]["added"], ["nodeCreated"])
            self.assertEqual(
                data["artifacts"]["node_api_schema"]["object_info_fields"]["added"], ["output"]
            )
            self.assertEqual(
                data["artifacts"]["node_api_schema"]["io_types"]["added"], ["FLOAT:Float"]
            )
            self.assertEqual(
                data["artifacts"]["node_api_schema"]["typed_input_shapes"]["changed"],
                ["AudioInput"],
            )


if __name__ == "__main__":
    unittest.main()
