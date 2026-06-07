#!/usr/bin/env python3
"""Validate the examples-only validation evidence matrix."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MATRIX = REPO_ROOT / "references" / "example-validation-matrix.json"

ALLOWED_TIERS = {
    "static",
    "offline_unit",
    "pinned_source",
    "runtime_smoke",
    "pattern_only_caveated",
}


def load_matrix(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_matrix(repo_root: Path, matrix: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    examples = matrix.get("examples")
    if not isinstance(examples, list) or not examples:
        return ["Matrix must include a non-empty examples list"]

    seen_paths: set[str] = set()
    for index, entry in enumerate(examples):
        if not isinstance(entry, dict):
            errors.append(f"Entry {index} must be an object")
            continue
        path = entry.get("path")
        if not isinstance(path, str) or not path.startswith("examples/"):
            errors.append(f"Entry {index} path must start with examples/")
            continue
        if path in seen_paths:
            errors.append(f"Duplicate matrix path: {path}")
        seen_paths.add(path)
        if not (repo_root / path).exists():
            errors.append(f"Matrix path does not exist: {path}")

        tiers = entry.get("validation_tiers")
        if not isinstance(tiers, list) or not tiers:
            errors.append(f"{path} must include non-empty validation_tiers")
            continue
        unknown_tiers = sorted(set(tiers) - ALLOWED_TIERS)
        if unknown_tiers:
            errors.append(f"{path} has unknown validation tiers: {', '.join(unknown_tiers)}")

        if "runtime_smoke" in tiers and "runtime_command" not in entry:
            errors.append(f"{path} uses runtime_smoke but lacks runtime_command")
        if "pattern_only_caveated" in tiers and not entry.get("caveat"):
            errors.append(f"{path} uses pattern_only_caveated but lacks caveat")
        if not entry.get("evidence"):
            errors.append(f"{path} must include evidence")

    readme_dirs = {
        readme.parent.relative_to(repo_root).as_posix()
        for readme in (repo_root / "examples").rglob("README.md")
        if readme.parent != repo_root / "examples"
    }
    for missing_path in sorted(readme_dirs - {path.rstrip("/") for path in seen_paths}):
        errors.append(f"Missing matrix entry for example README directory: {missing_path}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate examples-only validation matrix.")
    parser.add_argument(
        "--matrix", default=str(DEFAULT_MATRIX), help="Path to example-validation-matrix.json"
    )
    args = parser.parse_args()

    errors = validate_matrix(REPO_ROOT, load_matrix(Path(args.matrix)))
    if errors:
        for error in errors:
            print(f"FAILED: {error}", file=sys.stderr)
        return 1
    print("Example validation matrix OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
