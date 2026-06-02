"""Unit tests for scripts/verify/no_leaky_paths.py.

Contract:
- ``scan_source_for_leaky_prints(source)`` returns a list of (line, snippet)
  tuples for any ``print(...)`` call that emits a filesystem path-style
  string literal or ``Path`` / f-string expression containing a path, but
  does NOT pass that value through ``display_path()`` or
  ``display_command()``.
- A ``print(...)`` call whose argument is a call to ``display_path()`` or
  ``display_command()`` is treated as compliant and never reported.
- Pure informational ``print(...)`` calls (status, counts, no path
  content) are ignored.
- URL strings (``://`` scheme) are ignored.
- The ``main()`` entry point exits 0 when no leaks are detected and
  exits 1 when leaks are found.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VERIFIER_PATH = REPO_ROOT / "scripts" / "verify" / "no_leaky_paths.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("no_leaky_paths", VERIFIER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LeakyPrintDetectionTests(unittest.TestCase):
    def test_clean_print_with_status_message(self):
        module = _load_module()
        source = (
            "def go():\n"
            "    print('No shell example scripts found.')\n"
            "    print('Sidebar navigation coverage is complete.')\n"
        )
        self.assertEqual(module.scan_source_for_leaky_prints(source), [])

    def test_print_with_display_path_is_compliant(self):
        module = _load_module()
        source = (
            "from scripts.common.display_path import display_path\n"
            "def go(path):\n"
            "    print(f'File: {display_path(path)}')\n"
        )
        self.assertEqual(module.scan_source_for_leaky_prints(source), [])

    def test_print_with_display_command_is_compliant(self):
        module = _load_module()
        source = (
            "from scripts.common.display_path import display_command\n"
            "def go(cmd):\n"
            "    print(f'Running: {display_command(cmd)}')\n"
        )
        self.assertEqual(module.scan_source_for_leaky_prints(source), [])

    def test_print_with_raw_path_string_literal_is_flagged(self):
        module = _load_module()
        source = "from pathlib import Path\ndef go(p):\n    print(f'Wrote: {p}')\n"
        findings = module.scan_source_for_leaky_prints(source)
        self.assertEqual(len(findings), 1)
        line_number, snippet = findings[0]
        self.assertEqual(line_number, 3)
        self.assertIn("p}", snippet)

    def test_print_with_path_name_string_is_flagged(self):
        module = _load_module()
        source = (
            "from pathlib import Path\n"
            "REPO_ROOT = Path('/fake/repo')\n"
            "def go():\n"
            "    print(f'File not found: {REPO_ROOT}')\n"
        )
        findings = module.scan_source_for_leaky_prints(source)
        self.assertEqual(len(findings), 1)
        line_number, _ = findings[0]
        self.assertEqual(line_number, 4)

    def test_print_with_url_string_is_ignored(self):
        module = _load_module()
        source = "def go():\n    print('See https://example.com/repo for details.')\n"
        self.assertEqual(module.scan_source_for_leaky_prints(source), [])

    def test_print_with_safe_text_is_ignored(self):
        module = _load_module()
        source = (
            "def go():\n"
            "    print('Sidebar page paths: 29')\n"
            "    print('Hand-authored docs pages: 29')\n"
        )
        self.assertEqual(module.scan_source_for_leaky_prints(source), [])

    def test_multiple_leaky_prints_are_all_reported(self):
        module = _load_module()
        source = (
            "def go(src_path, dest_path):\n"
            "    print(f'Source: {src_path}')\n"
            "    print(f'Dest:   {dest_path}')\n"
        )
        findings = module.scan_source_for_leaky_prints(source)
        self.assertEqual(len(findings), 2)
        self.assertEqual([f[0] for f in findings], [2, 3])

    def test_print_call_inside_function_with_other_args_still_flagged(self):
        module = _load_module()
        source = "def go(path):\n    print('INFO', f'File: {path}')\n"
        findings = module.scan_source_for_leaky_prints(source)
        self.assertEqual(len(findings), 1)
        line_number, _ = findings[0]
        self.assertEqual(line_number, 2)

    def test_print_with_safe_string_path_variable_in_known_safe_name_is_flagged(self):
        module = _load_module()
        # The heuristic should flag any path-suggestive variable in a print
        # call. ``script_path`` is path-like and unredacted.
        source = "def go(script_path):\n    print(f'Reading: {script_path}')\n"
        findings = module.scan_source_for_leaky_prints(source)
        self.assertEqual(len(findings), 1)

    def test_stderr_print_is_also_flagged(self):
        module = _load_module()
        source = "import sys\ndef go(path):\n    print(f'Error: {path}', file=sys.stderr)\n"
        findings = module.scan_source_for_leaky_prints(source)
        self.assertEqual(len(findings), 1)

    def test_print_with_path_call_arg_is_flagged(self):
        module = _load_module()
        # A ``print()`` call that is itself a path object call (e.g.,
        # ``print(Path('...'))``) should also be flagged when no
        # ``display_path`` wraps it.
        source = "from pathlib import Path\ndef go():\n    print(Path('/abs/file.json'))\n"
        findings = module.scan_source_for_leaky_prints(source)
        # Plain print(Path(...)) is flagged because the path is emitted directly.
        self.assertEqual(len(findings), 1)

    def test_backslash_escape_sequence_not_flagged(self):
        module = _load_module()
        # A raw-string escape sequence like r"\n" contains a literal
        # backslash but is not a filesystem path.
        source = 'def go():\n    print(r"\\n")\n'
        findings = module.scan_source_for_leaky_prints(source)
        self.assertEqual(
            findings,
            [],
            f"Escape sequence r'\\n' should not be flagged as a path; got {findings}",
        )

    def test_known_path_variable_name_flagged_via_expr_references_path_variable(self):
        module = _load_module()
        # The variable name "p" is in PATH_VARIABLE_NAMES, so this
        # passes via _expr_references_path_variable without needing
        # backslash detection.
        source = 'from pathlib import Path\ndef go(p):\n    print(f"File: {p}")\n'
        findings = module.scan_source_for_leaky_prints(source)
        self.assertEqual(len(findings), 1)

    def test_backslash_containing_string_literal_is_flagged(self):
        module = _load_module()
        # A string literal containing a genuine Windows backslash path
        # must be detected by _string_literal_looks_like_path.
        source = 'def go():\n    print("C:\\\\Users\\\\file.json")\n'
        findings = module.scan_source_for_leaky_prints(source)
        self.assertEqual(len(findings), 1)

    # -- AST bypass pattern tests (Patterns 1-5) --

    def test_str_wrapping_path_variable_is_flagged(self):
        """Pattern 1: print(str(path_var)) should be detected."""
        module = _load_module()
        source = "from pathlib import Path\ndef go(p):\n    print(str(p))\n"
        findings = module.scan_source_for_leaky_prints(source)
        self.assertEqual(
            len(findings),
            1,
            f"str(path_var) wrapping should be flagged; got {findings}",
        )

    def test_string_concatenation_with_path_is_flagged(self):
        """Pattern 2: print('path: ' + str(path_var)) should be detected."""
        module = _load_module()
        source = "def go(p):\n    print('path: ' + str(p))\n"
        findings = module.scan_source_for_leaky_prints(source)
        self.assertEqual(
            len(findings),
            1,
            f"String concatenation with path var should be flagged; got {findings}",
        )

    def test_qualified_path_call_is_flagged(self):
        """Pattern 3: print(pathlib.Path(...)) should be detected."""
        module = _load_module()
        source = "import pathlib\ndef go():\n    print(pathlib.Path('/abs/file.json'))\n"
        findings = module.scan_source_for_leaky_prints(source)
        self.assertEqual(
            len(findings),
            1,
            f"Qualified pathlib.Path() should be flagged; got {findings}",
        )

    def test_imported_logging_level_is_flagged(self):
        """Pattern 4: from logging import info; info(str(p)) should be detected."""
        module = _load_module()
        source = "from logging import info\ndef go(p):\n    info(str(p))\n"
        findings = module.scan_source_for_leaky_prints(source)
        self.assertEqual(
            len(findings),
            1,
            f"Imported logging level should be flagged; got {findings}",
        )

    def test_logger_instance_call_is_flagged(self):
        """Pattern 5: logger = getLogger(...); logger.info(str(p)) should be detected."""
        module = _load_module()
        source = (
            "import logging\n"
            "logger = logging.getLogger(__name__)\n"
            "def go(p):\n"
            "    logger.info(str(p))\n"
        )
        findings = module.scan_source_for_leaky_prints(source)
        self.assertEqual(
            len(findings),
            1,
            f"Logger instance call should be flagged; got {findings}",
        )


class DefaultScanTargetsTests(unittest.TestCase):
    def test_default_scan_targets_include_all_c1_plus_h1_files(self):
        module = _load_module()
        targets = module.default_scan_targets(REPO_ROOT)
        # 12 files from c1
        c1_relative = [
            "scripts/extract/parse_from_api.py",
            "scripts/extract/parse_hooks.py",
            "scripts/extract/parse_node_api_schema.py",
            "scripts/extract/parse_server.py",
            "scripts/generate/generate_docs_index.py",
            "scripts/generate/generate_snapshot_delta_summary.py",
            "scripts/generate/publish_reference_artifacts.py",
            "scripts/verify/pipeline_smoke.py",
            "scripts/verify/rendered_links.py",
            "scripts/verify/runtime_smoke.py",
            "scripts/verify/schema_common.py",
            "scripts/check_upstream_versions.py",
        ]
        h1_relative = [
            "scripts/verify/sidebar_navigation_coverage.py",
            "scripts/verify/shell_examples_syntax.py",
            "scripts/new_doc.py",
            "scripts/common/refresh_git_ops.py",
            "scripts/verify/no_leaky_paths.py",
        ]
        for rel in c1_relative + h1_relative:
            self.assertIn(
                rel,
                [str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in targets],
                f"Missing default scan target: {rel}",
            )

    def test_repo_self_scan_returns_no_findings(self):
        # The repo's own scripts (after B-1 + H-1) should be fully compliant.
        module = _load_module()
        targets = module.default_scan_targets(REPO_ROOT)
        all_findings: list[tuple[str, int, str]] = []
        for path in targets:
            content = path.read_text(encoding="utf-8")
            for line_number, snippet in module.scan_source_for_leaky_prints(content):
                rel = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
                all_findings.append((rel, line_number, snippet))
        self.assertEqual(
            all_findings,
            [],
            f"Repo self-scan found {len(all_findings)} leak(s): {all_findings}",
        )


if __name__ == "__main__":
    unittest.main()
