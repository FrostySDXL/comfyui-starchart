#!/usr/bin/env python3
"""AST-based verifier: ensure script output never leaks absolute filesystem paths.

This verifier walks the AST of each default scan target and flags any
``print(...)`` call that emits a filesystem-path-style value without
first passing it through ``display_path()`` or ``display_command()``.

Placement: advisory (not part of the blocking wrapper yet). See
``CONTRIBUTING.md`` -> "Verifier Inventory" for current lifecycle and
the documented promotion/demotion/removal criteria.

Scope:
- Default scan targets are the 12 files updated by the c1
  display_path fix plus the 3 follow-up files wrapped under H-1.
- The heuristic is intentionally narrow: it catches the most common
  leak shapes (raw ``Path``/f-string in a ``print()`` call) and
  ignores pure informational messages. False negatives are accepted
  in exchange for low false-positive noise during advisory rollout.

False-positive tolerance:
- A ``print()`` call whose argument is a call to ``display_path()``
  or ``display_command()`` is treated as compliant.
- String literals containing ``://`` (URL schemes) are ignored.
- String literals without path-like content (no backslash, no drive
  letter, no slash + extension) are ignored.
- The heuristic flags variables whose names match the
  ``PATH_VARIABLE_NAMES`` set. Custom variable names outside this set
  are not flagged (acceptable false-negative for the advisory pass).
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Files whose ``print(...)`` calls must redact filesystem paths.
# Sourced from the c1 (display_path) commit and the H-1 follow-up.
DEFAULT_SCAN_RELATIVE_PATHS: list[str] = [
    # c1: 12 files updated when display_path was introduced
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
    # H-1: 3 follow-up files wrapped after the c1 audit
    "scripts/verify/sidebar_navigation_coverage.py",
    "scripts/verify/shell_examples_syntax.py",
    "scripts/new_doc.py",
]

# Variable names that strongly suggest a filesystem path. Used to flag
# f-string expressions like ``f"{p}"`` that emit an unredacted path.
PATH_VARIABLE_NAMES: frozenset[str] = frozenset(
    {
        "path",
        "p",
        "file",
        "dir",
        "directory",
        "output_path",
        "template_path",
        "script",
        "scripts",
        "src_path",
        "dest_path",
        "src",
        "dest",
        "input_path",
        "output",
        "input_file",
        "output_file",
        "file_path",
        "dir_path",
        "cwd",
        "repo_root",
        "tmpdir",
        "script_path",
        "out_path",
        "in_path",
        "url",
        "target",
        "destination",
    }
)

# Display-redaction helpers. A ``print(...)`` call whose argument is a
# call to one of these is treated as compliant.
REDACTING_HELPERS: frozenset[str] = frozenset({"display_path", "display_command"})

# URL scheme marker. Any string literal or f-string containing
# ``://`` is treated as informational, not a path leak.
URL_SCHEME: str = "://"


def _is_redacting_call(node: ast.AST) -> bool:
    """True if ``node`` is a call to ``display_path`` or ``display_command``."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in REDACTING_HELPERS
    if isinstance(func, ast.Attribute):
        return func.attr in REDACTING_HELPERS
    return False


def _string_literal_looks_like_path(node: ast.AST) -> bool:
    """True if ``node`` is a string constant whose contents look like a
    filesystem path (contains a drive letter + colon, backslash, or a
    forward slash + file extension)."""
    if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
        return False
    value: str = node.value
    if URL_SCHEME in value:
        return False
    if "\\" in value:
        return True
    # Drive letter prefix like "C:" or "g:".
    if len(value) >= 2 and value[1] == ":" and value[0].isalpha():
        return True
    # Forward-slash path with a file extension.
    if "/" in value:
        last_segment = value.rsplit("/", 1)[-1]
        if "." in last_segment:
            return True
    return False


def _expr_contains_url(node: ast.AST) -> bool:
    """True if a JoinedStr or Constant contains a URL scheme substring."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return URL_SCHEME in node.value
    if isinstance(node, ast.JoinedStr):
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                if URL_SCHEME in value.value:
                    return True
    return False


def _expr_references_path_variable(node: ast.AST) -> bool:
    """True if ``node`` is a Name matching PATH_VARIABLE_NAMES (case-insensitive),
    a JoinedStr that references such a Name, or a Call to ``Path(...)``."""
    if isinstance(node, ast.Name):
        if node.id.lower() in PATH_VARIABLE_NAMES:
            return True
    if isinstance(node, ast.JoinedStr):
        for value in node.values:
            if isinstance(value, ast.FormattedValue):
                if _expr_references_path_variable(value.value):
                    return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id == "Path":
            return True
    return False


def _print_arg_is_path_like(node: ast.AST) -> bool:
    """True if a single ``print()`` argument is path-like and not redacted."""
    if _is_redacting_call(node):
        return False
    if _expr_contains_url(node):
        return False
    if _string_literal_looks_like_path(node):
        return True
    if _expr_references_path_variable(node):
        return True
    return False


def scan_source_for_leaky_prints(source: str) -> list[tuple[int, str]]:
    """Return ``(line_number, snippet)`` for every leaky ``print()`` call.

    ``snippet`` is the stripped text of the offending line.
    """
    findings: list[tuple[int, str]] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return findings
    lines = source.splitlines()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not (isinstance(node.func, ast.Name) and node.func.id == "print"):
            continue
        for arg in node.args:
            if _print_arg_is_path_like(arg):
                line_index = node.lineno - 1
                snippet = lines[line_index].strip() if 0 <= line_index < len(lines) else ""
                findings.append((node.lineno, snippet))
                break  # one report per print() call
    return findings


def default_scan_targets(repo_root: Path) -> list[Path]:
    """Return the default list of files to scan (resolved to absolute paths)."""
    return [repo_root / rel for rel in DEFAULT_SCAN_RELATIVE_PATHS]


def verify_repo(repo_root: Path) -> list[tuple[str, int, str]]:
    """Scan all default targets and return ``(rel_path, line, snippet)`` findings."""
    findings: list[tuple[str, int, str]] = []
    for path in default_scan_targets(repo_root):
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        for line_number, snippet in scan_source_for_leaky_prints(content):
            rel = str(path.relative_to(repo_root)).replace("\\", "/")
            findings.append((rel, line_number, snippet))
    return findings


def main() -> int:
    findings = verify_repo(REPO_ROOT)
    if not findings:
        print(
            f"OK: no leaky print() calls detected across "
            f"{len(DEFAULT_SCAN_RELATIVE_PATHS)} scanned files."
        )
        return 0
    print(
        f"FAIL: {len(findings)} leaky print() call(s) detected in "
        f"{len({rel for rel, _, _ in findings})} file(s):"
    )
    for rel, line_number, snippet in findings:
        print(f"  {rel}:{line_number}: {snippet}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
