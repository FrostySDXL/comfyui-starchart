#!/usr/bin/env python3
"""Verify that generated community pages match their JSON sources.

Runs the ecosystem map generator and compares its output to the committed
 src/content/docs/ecosystem/map.md. Fails if they differ, which means someone edited the
markdown directly or forgot to regenerate after changing the JSON source.

Usage:
    python scripts/verify/community_generated_freshness.py

Exits 0 if generated output matches committed file, exits 1 with a diff report.
"""

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "scripts" / "generate" / "generate_community_pages.py"
COMMITTED_PATH = REPO_ROOT / "src" / "content" / "docs" / "ecosystem" / "map.md"
COMMUNITY_PAGES_JSON = REPO_ROOT / "references" / "community" / "community_pages.json"


def load_tracked_generated_pages(json_path: Path | None = None) -> list[dict]:
    """Return community pages still tracked as generated pages."""
    resolved_json_path = json_path if json_path is not None else COMMUNITY_PAGES_JSON
    data = json.loads(resolved_json_path.read_text(encoding="utf-8"))
    pages = data.get("pages", [])
    return [
        page
        for page in pages
        if isinstance(page, dict)
        and (page.get("page_kind") == "generated_catalog" or page.get("generated_from") is not None)
    ]


def main() -> int:
    if not GENERATOR.exists():
        print(f"ERROR: Generator not found at {GENERATOR}")
        return 1

    tracked_generated_pages = load_tracked_generated_pages()
    if not tracked_generated_pages:
        print("Generated community pages are fresh.")
        print("  No tracked generated community pages on current published surface.")
        return 0

    if not COMMITTED_PATH.exists():
        print(f"ERROR: Committed file not found at {COMMITTED_PATH}")
        return 1

    # Run generator to a temporary output path
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_output = Path(tmpdir) / "map.md"

        # The generator hardcodes its output path, so we need to run it in a way
        # that captures output without overwriting the committed file.
        # We import and call build_markdown directly instead.
        import importlib.util

        spec = importlib.util.spec_from_file_location("generate_community_pages", GENERATOR)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        input_data = json.loads(module.INPUT_PATH.read_text(encoding="utf-8"))
        generated = module.build_markdown(input_data)
        tmp_output.write_text(generated, encoding="utf-8")

        committed = COMMITTED_PATH.read_text(encoding="utf-8")

        if generated == committed:
            print("Generated community pages are fresh.")
            return 0
        else:
            print("ERROR: src/content/docs/ecosystem/map.md is out of sync with its JSON source.")
            print()
            print("Run the generator to fix:")
            print("  python scripts/generate/generate_community_pages.py")
            print()
            # Show a simple line diff for debugging
            generated_lines = generated.splitlines()
            committed_lines = committed.splitlines()
            max_lines = max(len(generated_lines), len(committed_lines))
            for i in range(max_lines):
                g = generated_lines[i] if i < len(generated_lines) else "<missing>"
                c = committed_lines[i] if i < len(committed_lines) else "<missing>"
                if g != c:
                    print(f"  Line {i + 1} differs:")
                    print(f"    generated: {g[:120]}")
                    print(f"    committed: {c[:120]}")
                    # Only show first few diffs to avoid spam
                    if i > 5:
                        print("  ... (additional differences omitted)")
                        break
            return 1


if __name__ == "__main__":
    sys.exit(main())
