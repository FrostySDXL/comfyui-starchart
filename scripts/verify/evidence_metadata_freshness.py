#!/usr/bin/env python3
"""Advisory verifier for retained-page evidence metadata discipline."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = REPO_ROOT / "src" / "content" / "docs"

REQUIRED_LABELS = ("**Evidence:**", "**Last Updated:**")
ALLOWED_BASELINE_PREFIXES = (
    "**Baseline verification status:** Verified against the current pinned baseline:",
    "**Baseline verification status:** Verified against the prior pinned baseline:",
)
ALLOWED_BASELINE_EXACT = {
    "**Baseline verification status:** Citation paths were updated where mechanical drift was obvious, but prose claims in this page have not yet been fully re-reviewed against the current baseline.",
    "**Baseline verification status:** This page has not been re-reviewed against the current baseline.",
}

BASELINE_REQUIRED_PATHS = {
    "api/endpoints.md",
    "api/history-queue.md",
    "api/prompt-submission.md",
    "api/websocket.md",
    "architecture/execution-pipeline.md",
    "architecture/overview.md",
    "custom-nodes/datatypes.md",
    "custom-nodes/development-guide.md",
    "custom-nodes/node-structure.md",
    "custom-nodes/registration.md",
    "deep-dives/execution-model-inversion.md",
    "deep-dives/registry-packaging-and-compatibility.md",
    "deep-dives/workflow-json-schema.md",
    "hooks/extension-points.md",
    "hooks/javascript-hooks.md",
    "hooks/server-hooks.md",
    "reference/machine-readable-artifacts.md",
    "reference/object-info.md",
}


def _relative_docs_paths() -> list[str]:
    return sorted(path.as_posix() for path in DOCS_ROOT.rglob("*.md"))


def _read_page(relative_path: str) -> str:
    return (DOCS_ROOT / relative_path).read_text(encoding="utf-8")


def _opening_lines(text: str, limit: int = 20) -> list[str]:
    return text.splitlines()[:limit]


def _find_line(lines: list[str], prefix: str) -> str | None:
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped
    return None


def _baseline_status_allowed(line: str) -> bool:
    if line.startswith(ALLOWED_BASELINE_PREFIXES):
        return True
    return line in ALLOWED_BASELINE_EXACT


def verify_pages() -> list[str]:
    errors: list[str] = []
    for relative_path in sorted(BASELINE_REQUIRED_PATHS):
        page_path = DOCS_ROOT / relative_path
        if not page_path.exists():
            errors.append(f"{relative_path}: covered page is missing")
            continue

        opening_lines = _opening_lines(_read_page(relative_path))

        for label in REQUIRED_LABELS:
            if _find_line(opening_lines, label) is None:
                errors.append(f"{relative_path}: missing opening metadata label {label}")

        baseline_line = _find_line(opening_lines, "**Baseline verification status:**")
        if baseline_line is None:
            errors.append(
                f"{relative_path}: missing opening metadata label **Baseline verification status:**"
            )
            continue
        if not _baseline_status_allowed(baseline_line):
            errors.append(
                f"{relative_path}: baseline verification status wording is not an approved phrasing"
            )
    return errors


def main() -> int:
    errors = verify_pages()
    if errors:
        print(f"Found {len(errors)} evidence metadata issue(s):")
        for error in errors:
            print(f"  {error}")
        return 1

    print(
        "Evidence metadata freshness checks passed for retained API, hooks, custom-node, architecture, object-info, machine-readable-artifact, and deep-dive pages."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
