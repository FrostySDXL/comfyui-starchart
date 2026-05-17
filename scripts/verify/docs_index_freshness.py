#!/usr/bin/env python3
"""Verify that docs-index.json matches current docs navigation and page metadata.

Runs the docs-index generator in memory and compares the result to the checked-in
public/artifacts/docs-index.json file. Fails if they differ, which means someone
changed the published docs surface without regenerating the support artifact.

Usage:
    python scripts/verify/docs_index_freshness.py

Exits 0 if docs-index.json is fresh, exits 1 with a diff summary if stale.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "scripts" / "generate" / "generate_docs_index.py"


def _load_generator_module():
    spec = importlib.util.spec_from_file_location("generate_docs_index", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generate_docs_index = _load_generator_module()
COMMITTED_PATH = generate_docs_index.OUTPUT_PATH


def render_docs_index_text(docs_index: dict[str, object]) -> str:
    return json.dumps(docs_index, indent=2, ensure_ascii=False) + "\n"


def verify_freshness() -> int:
    if not GENERATOR.exists():
        print(f"ERROR: Generator not found at {GENERATOR}")
        return 1

    if not COMMITTED_PATH.exists():
        print(f"ERROR: Committed file not found at {COMMITTED_PATH}")
        return 1

    generated = render_docs_index_text(
        generate_docs_index.build_docs_index(generate_docs_index.REPO_ROOT)
    )
    committed = COMMITTED_PATH.read_text(encoding="utf-8")

    if generated == committed:
        print("docs-index.json is fresh.")
        return 0

    print(
        "ERROR: public/artifacts/docs-index.json is out of sync with the checked-in published docs navigation or page metadata."
    )
    print()
    print("Run the generator to fix:")
    print("  python scripts/generate/generate_docs_index.py")
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
