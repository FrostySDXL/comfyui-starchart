#!/usr/bin/env python3
"""AST-based verifier: ensure script output never leaks absolute filesystem paths.

This verifier walks the AST of each default scan target and flags any
``print(...)`` or ``logging.<level>()`` call that emits a
filesystem-path-style value without first passing it through
``display_path()`` or ``display_command()``.

Placement: advisory (not part of the blocking wrapper yet). See
``CONTRIBUTING.md`` -> "Verifier Inventory" for current lifecycle and
the documented promotion/demotion/removal criteria.

Scope:
- Default scan targets are the 12 files updated by the c1
  display_path fix, plus the 3 follow-up files wrapped under
  H-1, plus the verifier itself (self-scan).
- The heuristic catches the most common leak shapes: raw ``Path`` or
  f-string in a ``print()`` call, ``str()`` wrapping, string
  concatenation, qualified ``pathlib.Path()`` calls, imported
  ``logging`` levels, and logger instances.

False-positive tolerance:
- A ``print()`` call whose argument is a call to ``display_path()``
  or ``display_command()`` is treated as compliant.
- String literals containing ``://`` (URL schemes) are ignored.
- String literals without path-like content (no backslash, no drive
  letter, no slash + extension) are ignored.
- Backslash characters followed by standard Python escape characters
  (n, t, r, etc.) are treated as escape sequences, not paths.
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
# Sourced from the c1 (display_path) commit, the H-1 follow-up, and self-scan.
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
    # H-1 follow-up: refresh_git_ops was also updated to use display_command
    "scripts/common/refresh_git_ops.py",
    # Self-scan: the verifier must also pass its own leak detection
    "scripts/verify/no_leaky_paths.py",
    # verify_artifact_integrity: 5 error-return f-strings interpolate Path objects
    "scripts/verify/verify_artifact_integrity.py",
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
        "out_dir",
        "target_dir",
        "cache_dir",
        "snapshot_dir",
        "result_path",
        "clone_dir",
        "backup_path",
        "provenance_path",
    }
)

# Display-redaction helpers. A ``print(...)`` call whose argument is a
# call to one of these is treated as compliant.
REDACTING_HELPERS: frozenset[str] = frozenset({"display_path", "display_command"})

# URL scheme marker. Any string literal or f-string containing
# ``://`` is treated as informational, not a path leak.
URL_SCHEME: str = "://"

# Logging method names on the ``logging`` module that are treated
# as output sinks. A ``logging.info(str(p))`` call is inspected
# with the same path-leak checks as ``print(...)``.
_LOGGING_LEVELS: frozenset[str] = frozenset(
    {"debug", "info", "warning", "error", "critical", "exception", "log"}
)


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


def _is_logging_call(node: ast.AST, logging_names: frozenset[str] = frozenset()) -> bool:
    """True if ``node`` is a call to ``logging.<level>(...)``, an
    imported logging level (``from logging import info``), or a logger
    instance method (``logger.info(...)`` where ``logger`` was assigned
    via ``logging.getLogger(...)``)."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    # logging.<level>() -- module-global
    if isinstance(func, ast.Attribute) and func.attr in _LOGGING_LEVELS:
        if isinstance(func.value, ast.Name):
            if func.value.id == "logging":
                return True
            # logger instance: logger = logging.getLogger(...)
            if func.value.id in logging_names:
                return True
    # from logging import <level>; <level>(...)
    if isinstance(func, ast.Name) and func.id in logging_names:
        return True
    return False


def _collect_logging_names(tree: ast.AST) -> frozenset[str]:
    """Collect names imported from ``logging`` and variables assigned
    ``logging.getLogger(...)`` results (logger instances)."""
    names: set[str] = set()
    for node in ast.walk(tree):
        # from logging import info, debug, ...
        if isinstance(node, ast.ImportFrom):
            if node.module == "logging":
                for alias in node.names:
                    names.add(alias.asname if alias.asname is not None else alias.name)
        # logger = logging.getLogger(__name__)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and isinstance(node.value, ast.Call):
                    if (
                        isinstance(node.value.func, ast.Attribute)
                        and node.value.func.attr == "getLogger"
                    ):
                        names.add(target.id)
    return frozenset(names)


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
        # A backslash followed by a standard Python escape character
        # (n, t, r, \\, etc.) is likely an escape sequence, not a path.
        # Require at least one backslash that is NOT followed by a
        # standard escape character to treat the value as path-like.
        _ESCAPE_CHARS = frozenset("ntr\\'\"abfv0")
        for i, ch in enumerate(value):
            if ch == "\\" and i + 1 < len(value):
                if value[i + 1] not in _ESCAPE_CHARS:
                    return True
        # All backslashes are part of escape sequences -- not a path.
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
    a JoinedStr that references such a Name, a Call to ``Path(...)`` (bare or
    qualified), or a ``str(...)`` wrapping of a path-like expression."""
    if isinstance(node, ast.Name):
        if node.id.lower() in PATH_VARIABLE_NAMES:
            return True
    if isinstance(node, ast.JoinedStr):
        for value in node.values:
            if isinstance(value, ast.FormattedValue):
                if _expr_references_path_variable(value.value):
                    return True
    if isinstance(node, ast.Call):
        # Bare Path(...) call: Path("/abs/path")
        if isinstance(node.func, ast.Name) and node.func.id == "Path":
            return True
        # Qualified Path call: pathlib.Path(...) or Path("...")
        if isinstance(node.func, ast.Attribute) and node.func.attr == "Path":
            return True
        # str() wrapping: print(str(path_var)) -- recurse into args
        if isinstance(node.func, ast.Name) and node.func.id == "str":
            return any(_expr_references_path_variable(arg) for arg in node.args)
    return False


def _expr_is_path_binop(node: ast.AST) -> bool:
    """True if *node* is a ``BinOp`` (``+``) whose left or right operand
    is path-like."""
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Add):
        return False
    return (
        _expr_references_path_variable(node.left)
        or _print_arg_is_path_like(node.left)
        or _expr_references_path_variable(node.right)
        or _print_arg_is_path_like(node.right)
    )


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
    if _expr_is_path_binop(node):
        return True
    return False


def scan_source_for_leaky_prints(source: str) -> list[tuple[int, str]]:
    """Return ``(line_number, snippet)`` for every leaky ``print()`` or
    ``logging.<level>()`` call.

    ``snippet`` is the stripped text of the offending line.
    """
    findings: list[tuple[int, str]] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return findings
    logging_names = _collect_logging_names(tree)
    lines = source.splitlines()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        is_print = isinstance(node.func, ast.Name) and node.func.id == "print"
        is_logging = _is_logging_call(node, logging_names)
        if not (is_print or is_logging):
            continue
        for arg in node.args:
            if _print_arg_is_path_like(arg):
                line_index = node.lineno - 1
                snippet = lines[line_index].strip() if 0 <= line_index < len(lines) else ""
                findings.append((node.lineno, snippet))
                break  # one report per call
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
            f"OK: no leaky print() or logging output detected across "
            f"{len(DEFAULT_SCAN_RELATIVE_PATHS)} scanned files."
        )
        return 0
    print(
        f"FAIL: {len(findings)} leaky print()/logging call(s) detected in "
        f"{len({rel for rel, _, _ in findings})} file(s):"
    )
    for rel, line_number, snippet in findings:
        print(f"  {rel}:{line_number}: {snippet}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
