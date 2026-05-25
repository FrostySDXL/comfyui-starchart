#!/usr/bin/env python3
"""
Bootstrap a new documentation page from a template.
"""

import argparse
import datetime
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_ROOT = (REPO_ROOT / "src" / "content" / "docs").resolve()
TEMPLATES_DIR = REPO_ROOT / "templates" / "docs"

MODE_TO_TEMPLATE = {
    "reference": "reference-template.md",
    "scaffold": "scaffold-template.md",
}

MODE_TO_ALLOWED_PREFIXES = {
    "reference": [
        "src/content/docs/reference/",
        "src/content/docs/api/",
        "src/content/docs/hooks/",
        "src/content/docs/custom-nodes/",
    ],
}


def normalize_output_argument(output_arg: str) -> Path:
    return Path(output_arg.replace("\\", "/"))


def parse_args():
    parser = argparse.ArgumentParser(description="Create a new doc page from a template")
    parser.add_argument(
        "--output", required=True, help="Output markdown path under src/content/docs/"
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=list(MODE_TO_TEMPLATE.keys()),
        help="Page mode",
    )
    parser.add_argument("--title", required=True, help="Page title")
    parser.add_argument("--evidence", default=None, help="Evidence label override")
    parser.add_argument(
        "--primary-source",
        default=None,
        help="Primary source line to insert when the template includes one",
    )
    parser.add_argument(
        "--allow-path-mismatch",
        action="store_true",
        help="Allow a mode/output path combination outside the usual docs folders",
    )
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing file")
    return parser.parse_args()


def resolve_output_path(output_arg: str):
    relative_output = normalize_output_argument(output_arg)
    if relative_output.is_absolute():
        raise ValueError(
            "Output path must be a repo-relative markdown path under src/content/docs/."
        )

    output_path = (REPO_ROOT / relative_output).resolve()
    try:
        output_path.relative_to(DOCS_ROOT)
    except ValueError as exc:
        raise ValueError(
            f"Output path must stay under src/content/docs/: {relative_output.as_posix()}"
        ) from exc

    if relative_output.suffix != ".md":
        raise ValueError(
            f"Output path must end with .md under src/content/docs/: {relative_output.as_posix()}"
        )

    legacy_prefix = Path("docs")
    if relative_output == legacy_prefix or relative_output.is_relative_to(legacy_prefix):
        raise ValueError(
            f"Legacy docs/ output paths are not allowed; use src/content/docs/: {relative_output.as_posix()}"
        )

    expected_prefix = Path("src") / "content" / "docs"
    if not relative_output.parts or relative_output.parts[:3] != expected_prefix.parts:
        raise ValueError(
            f"Output path must start with src/content/docs/: {relative_output.as_posix()}"
        )

    return relative_output, output_path


def validate_mode_path(mode: str, relative_output: Path, allow_path_mismatch: bool):
    allowed_prefixes = MODE_TO_ALLOWED_PREFIXES.get(mode)
    if not allowed_prefixes:
        return

    output_posix = relative_output.as_posix()
    if relative_output.parent.as_posix() == "src/content/docs":
        return

    if any(output_posix.startswith(prefix) for prefix in allowed_prefixes):
        return

    if allow_path_mismatch:
        return

    prefixes = ", ".join(allowed_prefixes)
    raise ValueError(
        f"{mode} pages usually belong under {prefixes}. "
        f"Got: {output_posix}. Use --allow-path-mismatch if this is intentional."
    )


def apply_metadata(
    content: str, title: str, evidence: str | None, primary_source: str | None
) -> tuple[str, bool]:
    frontmatter = f'---\ntitle: "{title}"\n---\n\n'
    if not content.startswith("---\n"):
        content = frontmatter + content
    content = content.replace("YYYY-MM-DD", datetime.date.today().isoformat())

    primary_source_applied = False
    lines = []
    for line in content.splitlines():
        if evidence and line.startswith("**Evidence:**"):
            lines.append(f"**Evidence:** {evidence}")
        elif primary_source and line.startswith("**Primary Source:**"):
            lines.append(f"**Primary Source:** {primary_source}")
            primary_source_applied = True
        else:
            lines.append(line)

    return "\n".join(lines), primary_source_applied


def main():
    args = parse_args()

    template_path = TEMPLATES_DIR / MODE_TO_TEMPLATE[args.mode]
    if not template_path.exists():
        print(f"Template not found: {template_path}", file=sys.stderr)
        sys.exit(1)

    try:
        relative_output, output_path = resolve_output_path(args.output)
        validate_mode_path(args.mode, relative_output, args.allow_path_mismatch)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    if output_path.exists() and not args.overwrite:
        print(f"File already exists: {output_path}", file=sys.stderr)
        sys.exit(1)

    content = template_path.read_text(encoding="utf-8")
    content, primary_source_applied = apply_metadata(
        content, args.title, args.evidence, args.primary_source
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    if args.primary_source and not primary_source_applied:
        print(
            "Primary source was provided but not used because the selected template does not include a **Primary Source:** line.",
            file=sys.stderr,
        )
    print(f"Created {relative_output.as_posix()}")


if __name__ == "__main__":
    main()
