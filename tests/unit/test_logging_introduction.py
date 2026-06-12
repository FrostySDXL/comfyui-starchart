"""Tests for Plan 07 helper-module logging introduction boundaries."""

import ast
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


MODULE_PATHS = [
    REPO_ROOT / "scripts" / "common" / "subprocess_utils.py",
    REPO_ROOT / "scripts" / "common" / "path_normalization.py",
    REPO_ROOT / "scripts" / "common" / "snapshot_surface.py",
    REPO_ROOT / "scripts" / "common" / "published_docs_surface.py",
    REPO_ROOT / "scripts" / "generate" / "generate_snapshot_delta_summary.py",
]


class LoggingIntroductionTests(unittest.TestCase):
    def _tree(self, path: Path) -> ast.Module:
        return ast.parse(path.read_text(encoding="utf-8"))

    def test_task6_modules_declare_module_logger(self):
        for path in MODULE_PATHS:
            with self.subTest(path=path.relative_to(REPO_ROOT).as_posix()):
                tree = self._tree(path)
                self.assertTrue(
                    any(
                        isinstance(node, ast.Assign)
                        and any(
                            isinstance(target, ast.Name) and target.id == "logger"
                            for target in node.targets
                        )
                        and isinstance(node.value, ast.Call)
                        and isinstance(node.value.func, ast.Attribute)
                        and node.value.func.attr == "getLogger"
                        for node in tree.body
                    )
                )

    def test_subprocess_utils_has_bounded_operator_print_sites(self):
        tree = self._tree(REPO_ROOT / "scripts" / "common" / "subprocess_utils.py")
        print_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
        ]
        self.assertLessEqual(len(print_calls), 2)

    def test_delta_summary_cli_configures_logging(self):
        tree = self._tree(REPO_ROOT / "scripts" / "generate" / "generate_snapshot_delta_summary.py")
        self.assertTrue(
            any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "basicConfig"
                for node in ast.walk(tree)
            )
        )

    def test_delta_summary_uses_logger_for_helper_operator_messages(self):
        tree = self._tree(REPO_ROOT / "scripts" / "generate" / "generate_snapshot_delta_summary.py")
        logger_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "logger"
            and node.func.attr in {"info", "warning"}
        ]
        self.assertGreaterEqual(len(logger_calls), 2)

    def test_delta_summary_cli_logging_uses_message_only_format(self):
        tree = self._tree(REPO_ROOT / "scripts" / "generate" / "generate_snapshot_delta_summary.py")
        basic_config_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "basicConfig"
        ]
        self.assertTrue(basic_config_calls)
        self.assertTrue(
            any(
                keyword.arg == "format"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value == "%(message)s"
                for call in basic_config_calls
                for keyword in call.keywords
            )
        )


if __name__ == "__main__":
    unittest.main()
