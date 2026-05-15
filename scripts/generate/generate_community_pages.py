#!/usr/bin/env python3
"""Generate community-facing documentation pages from structured metadata.

Reads references/community/ecosystem_packages.json and renders
docs/ecosystem/map.md. Do not hand-edit the generated markdown file;
edit the JSON source and rerun this generator.

Usage:
    python scripts/generate/generate_community_pages.py
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = REPO_ROOT / "references" / "community" / "ecosystem_packages.json"
OUTPUT_PATH = REPO_ROOT / "docs" / "ecosystem" / "map.md"

CATEGORY_ORDER = [
    ("package_manager", "Package Managers and Distribution"),
    ("registry", "Registry"),
    ("node_pack", "Node Packs"),
    ("tooling", "Tooling and Utilities"),
]

GENERATED_BANNER = (
    "<!-- GENERATED FILE: do not edit directly. "
    "Edit references/community/ecosystem_packages.json and run "
    "python scripts/generate/generate_community_pages.py. "
    "Note: curated follow-up study highlights are maintained in the generator "
    "code, not in the JSON source. -->"
)


def _escape_md(text: str) -> str:
    """Escape minimal markdown in free text."""
    return text.replace("|", r"\|")


def _build_package_section(package: dict) -> list[str]:
    """Render a single package as markdown bullet lines."""
    lines = []
    name = package.get("name", "Unknown")
    lines.append(f"### {name}")
    lines.append("")

    repo_url = package.get("repo_url")
    registry_url = package.get("registry_url")
    if repo_url:
        lines.append(f"- **Repo:** [{repo_url}]({repo_url})")
    if registry_url:
        lines.append(f"- **Registry:** [{registry_url}]({registry_url})")

    status = package.get("status", "Unknown")
    lines.append(f"- **Status:** {status}")

    pinned_version = package.get("pinned_external_version")
    pinned_commit = package.get("pinned_commit")
    if pinned_version:
        lines.append(f"- **Last Release:** {pinned_version}")
    elif pinned_commit:
        lines.append(f"- **Pinned Commit:** `{pinned_commit}`")

    role = package.get("role_summary", "")
    if role:
        lines.append(f"- **Role:** {role}")

    patterns = package.get("notable_patterns", [])
    if patterns:
        lines.append(f"- **Notable Patterns:** {', '.join(patterns)}")

    used_by = package.get("used_by")
    if used_by:
        lines.append(f"- **Used By:** {used_by}")

    last_verified = package.get("last_verified", "unknown")
    lines.append(f"- **Last Verified:** {last_verified}")

    caveats = package.get("caveats")
    if caveats:
        lines.append(f"- **Caveats:** {caveats}")

    lines.append("")
    return lines


def build_markdown(data: dict) -> str:
    """Render the full ecosystem map markdown from package metadata."""
    metadata = data.get("metadata", {})
    packages = data.get("packages", [])

    lines = [
        GENERATED_BANNER,
        "",
        "# Ecosystem Map",
        "",
        "**Evidence:** Community pattern study",
        f"**Last Updated:** {metadata.get('last_updated', 'unknown')}",
        "",
        "Status labels were manually checked against public package pages and should be",
        "re-verified before use. This page is a starting point, not a permanent assessment.",
        "",
        "## Overview",
        "",
        "This page maps major ComfyUI ecosystem packages with their maintenance status.",
        "Maintenance status is the most important signal for anyone deciding whether to",
        "build on or depend on a community package.",
        "",
        "For how this catalog is generated, how maintenance tiers are interpreted, and",
        "what this page does and does not claim, see",
        "[Community Generated Surfaces](../reference/community-generated-surfaces.md).",
        "",
        "A package that was popular two years ago may be effectively abandoned today.",
        "Building new work on an abandoned dependency creates immediate maintenance debt.",
        "",
        "Status labels on this page are time-bound assessments, not permanent facts.",
        "Treat them as a starting point and confirm the current project state before",
        "depending on a package.",
        "",
        "## Maintenance Status Legend",
        "",
        "| Status | Meaning |",
        "|--------|---------|",
        "| Actively Maintained | Regular releases within the last 6 months; issues/PRs get responses |",
        "| Community Supported | Original author inactive; community may still merge PRs or release |",
        "| Likely Unmaintained | No releases in over 12 months; no recent commits or responses |",
        "| Unknown | Insufficient public signal to assess |",
        "",
        "## How to Assess Maintenance",
        "",
        "Before depending on a community package:",
        "",
        "1. check the GitHub release page for release dates",
        "2. scan recent commit history (last 30 commits) for activity",
        "3. look at open issues -- are they accumulating without responses?",
        "4. check whether a Discord or support channel exists with recent activity",
        "5. verify the package works with your ComfyUI version before building workflows",
        "   around it",
        "",
    ]

    # Group packages by category
    by_category: dict[str, list[dict]] = {}
    for pkg in packages:
        cat = pkg.get("category", "unknown")
        by_category.setdefault(cat, []).append(pkg)

    # Render sections in category order
    for cat_key, cat_title in CATEGORY_ORDER:
        if cat_key not in by_category:
            continue
        lines.append(f"## {cat_title}")
        lines.append("")
        for pkg in by_category[cat_key]:
            lines.extend(_build_package_section(pkg))

    # Keep this curated list aligned with the current intended follow-up study
    # set when Plan AC-style ecosystem expansion changes the strongest teaching
    # examples. The generated banner points maintainers here on purpose.
    lines.extend(
        [
            "## Deep-Dive Candidates",
            "",
            "For learning extension and node pack architecture, these three packages are",
            "the most instructive follow-up studies in the current catalog:",
            "",
            "1. **ComfyUI-Manager** -- hybrid extension architecture, custom routes, server",
            "   hooks, and frontend panel integration",
            "2. **comfyui_controlnet_aux** -- large-scale preprocessor wrapper design,",
            "   structured pose-data outputs, and extension-friendly annotator packaging",
            "3. **ComfyUI-AnimateDiff-Evolved** -- advanced animation scheduling,",
            "   sliding context windows, and motion-module workflow design",
            "",
            "## Scope Notes",
            "",
            "This map covers packages that appear in ComfyUI-Manager's distribution list or",
            "that are frequently referenced in official docs and community discussions. It",
            "does not attempt to catalog every custom node repo -- there are thousands.",
            "",
            'Package status reflects publicly observable signals only. A "Community',
            'Supported" label does not guarantee responsiveness. Verify directly before',
            "building production dependencies.",
            "",
            "This map is repo-local and not automatically refreshed. When adding a new",
            "package as a dependency, verify its current status rather than relying on this",
            "page.",
            "",
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> int:
    data = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    OUTPUT_PATH.write_text(build_markdown(data), encoding="utf-8")
    print("Generated docs/ecosystem/map.md from community metadata")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
