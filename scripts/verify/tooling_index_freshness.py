#!/usr/bin/env python3
"""Verify that tooling-index.json matches current docs navigation and metadata."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "scripts" / "generate" / "generate_tooling_index.py"


def _load_generator_module():
    spec = importlib.util.spec_from_file_location("generate_tooling_index", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generate_tooling_index = _load_generator_module()
COMMITTED_PATH = generate_tooling_index.OUTPUT_PATH


def render_tooling_index_text(tooling_index: dict[str, object]) -> str:
    return json.dumps(tooling_index, indent=2, ensure_ascii=False) + "\n"


def verify_freshness() -> int:
    if not GENERATOR.exists():
        print(f"ERROR: Generator not found at {GENERATOR}")
        return 1

    if not COMMITTED_PATH.exists():
        print(f"ERROR: Committed file not found at {COMMITTED_PATH}")
        return 1

    generated = render_tooling_index_text(
        generate_tooling_index.build_tooling_index(generate_tooling_index.REPO_ROOT)
    )
    committed = COMMITTED_PATH.read_text(encoding="utf-8")

    if generated == committed:
        print("tooling-index.json is fresh.")
        return 0

    print(
        "ERROR: public/artifacts/tooling-index.json is out of sync with the checked-in published docs navigation, page metadata, or tooling-index metadata."
    )
    print()
    print("Run the generator to fix:")
    print("  python scripts/generate/generate_tooling_index.py")
    print()

    generated_lines = generated.splitlines()
    committed_lines = committed.splitlines()
    max_lines = max(len(generated_lines), len(committed_lines))
    shown = 0
    for i in range(max_lines):
        g = generated_lines[i] if i < len(generated_lines) else "<missing>"
        c = committed_lines[i] if i < len(committed_lines) else "<missing>"
        if g != c:
            print(f"  Line {i + 1} differs:")
            print(f"    generated: {g[:120]}")
            print(f"    committed: {c[:120]}")
            shown += 1
            if shown >= 6:
                print("  ... (additional differences omitted)")
                break
    return 1


def main() -> int:
    return verify_freshness()


if __name__ == "__main__":
    sys.exit(main())
