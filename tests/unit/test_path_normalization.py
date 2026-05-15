import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "common" / "path_normalization.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("path_normalization", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PathNormalizationTests(unittest.TestCase):
    def test_normalize_windows_style_path(self):
        module = _load_module()
        self.assertEqual(
            module.normalize_repo_path(r"references\snapshots\server.py"),
            "references/snapshots/server.py",
        )

    def test_normalize_posix_path_is_stable(self):
        module = _load_module()
        self.assertEqual(
            module.normalize_repo_path("references/raw/server_endpoints.json"),
            "references/raw/server_endpoints.json",
        )

    def test_has_backslashes_detects_validator_case(self):
        module = _load_module()
        self.assertTrue(module.has_backslashes(r"path\with\backslashes"))
        self.assertFalse(module.has_backslashes("path/with/forward/slashes"))

    def test_normalize_repo_relative_path_strips_repo_prefix(self):
        module = _load_module()
        repo_root = Path(r"C:\repo")
        self.assertEqual(
            module.normalize_repo_relative_path(
                Path(r"C:\repo\references\raw\file.json"), repo_root
            ),
            "references/raw/file.json",
        )


if __name__ == "__main__":
    unittest.main()
