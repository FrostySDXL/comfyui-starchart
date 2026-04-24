#!/usr/bin/env python3
"""
Bootstrap a new documentation page from a template.
"""
import argparse
import datetime
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates" / "docs"

MODE_TO_TEMPLATE = {
    "reference": "reference-template.md",
    "tutorial": "tutorial-template.md",
    "decision-guide": "decision-guide-template.md",
    "community-pattern": "community-pattern-template.md",
    "scaffold": "scaffold-template.md",
}


def main():
    parser = argparse.ArgumentParser(description="Create a new doc page from a template")
    parser.add_argument("--output", required=True, help="Output path under docs/")
    parser.add_argument(
        "--mode",
        required=True,
        choices=list(MODE_TO_TEMPLATE.keys()),
        help="Page mode",
    )
    parser.add_argument("--title", required=True, help="Page title")
    parser.add_argument("--evidence", default=None, help="Evidence label override")
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing file"
    )
    args = parser.parse_args()

    template_path = TEMPLATES_DIR / MODE_TO_TEMPLATE[args.mode]
    if not template_path.exists():
        print(f"Template not found: {template_path}", file=sys.stderr)
        sys.exit(1)

    output_path = REPO_ROOT / args.output
    # Enforce that output must be under docs/
    try:
        output_path.relative_to(REPO_ROOT / "docs")
    except ValueError:
        print(
            f"Output path must be under docs/: {args.output}",
            file=sys.stderr,
        )
        sys.exit(1)

    if output_path.exists() and not args.overwrite:
        print(f"File already exists: {output_path}", file=sys.stderr)
        sys.exit(1)

    content = template_path.read_text(encoding="utf-8")

    # Replace title
    content = content.replace("# Page Title", f"# {args.title}")

    # Replace date
    today = datetime.date.today().isoformat()
    content = content.replace("YYYY-MM-DD", today)

    # Replace evidence if provided
    if args.evidence:
        lines = content.splitlines()
        new_lines = []
        for line in lines:
            if line.startswith("**Evidence:**"):
                new_lines.append(f"**Evidence:** {args.evidence}")
            else:
                new_lines.append(line)
        content = "\n".join(new_lines)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"Created {output_path}")


if __name__ == "__main__":
    main()
