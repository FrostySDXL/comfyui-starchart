#!/usr/bin/env python3
"""Compare pinned upstream versions against latest upstream tags and produce a summary.

Usage:
    python scripts/check_upstream_versions.py
    python scripts/check_upstream_versions.py --output-json summary.json --output-md summary.md

Exits 0 after producing summaries. Exits 1 on network or data errors.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, cast

from packaging.version import InvalidVersion, Version

from scripts.common import http_utils
from scripts.common.display_path import display_path

REPO_ROOT = Path(__file__).resolve().parents[1]

REFERENCES_RAW_DIR = REPO_ROOT / "references" / "raw"

CORE_TAGS_URL = "https://api.github.com/repos/Comfy-Org/ComfyUI/tags?per_page=100"
FRONTEND_TAGS_URL = "https://api.github.com/repos/Comfy-Org/ComfyUI_Frontend/tags?per_page=100"


def _github_api_headers() -> dict[str, str]:
    """Return GitHub API headers, adding auth when GITHUB_TOKEN is available."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "comfyui-kb-upstream-watch",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _fetch_json(url: str, timeout: int = 30) -> list[Any] | dict[str, Any]:
    """Fetch and parse JSON from a URL."""
    return cast(
        list[Any] | dict[str, Any],
        http_utils.get_json(
            url,
            timeout=timeout,
            headers=_github_api_headers(),
        ),
    )


def _read_pinned_version(json_path: Path) -> dict | None:
    """Read pinned version and commit from a raw JSON metadata block."""
    if not json_path.exists():
        return None
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    metadata = data.get("metadata", {})
    return {
        "version": metadata.get("version", "unknown"),
        "commit": metadata.get("commit", ""),
    }


def _parse_version_tag(tag_name: str) -> tuple[int, ...] | None:
    """Parse tags like v1.44.13 into comparable integer tuples."""
    if not isinstance(tag_name, str) or not tag_name.startswith("v"):
        return None
    parts = tag_name[1:].split(".")
    if not parts or any(not part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def _latest_tag_from_github(tags_url: str) -> str | None:
    """Fetch the latest tag name from GitHub API tags endpoint."""
    data = _fetch_json(tags_url)
    if isinstance(data, list) and data:
        latest_name = None
        latest_version = None
        for entry in data:
            name = entry.get("name")
            version = _parse_version_tag(name)
            if version is None:
                continue
            if latest_version is None or version > latest_version:
                latest_name = name
                latest_version = version
        return latest_name
    return None


def _is_newer_version(current_version: str, latest_version: str | None) -> bool:
    """Return True only when latest_version is newer than current_version."""
    if latest_version is None:
        return False

    try:
        return Version(latest_version.lstrip("v")) > Version(current_version.lstrip("v"))
    except InvalidVersion:
        current_parsed = _parse_version_tag(current_version)
        latest_parsed = _parse_version_tag(latest_version)
        if current_parsed is None or latest_parsed is None:
            return False
        return latest_parsed > current_parsed


def _build_summary(
    core_pinned: dict, core_latest: str | None, frontend_pinned: dict, frontend_latest: str | None
) -> dict:
    """Build a machine-readable summary dict."""

    def component_summary(pinned: dict, latest: str | None, name: str) -> dict:
        update_available = _is_newer_version(pinned["version"], latest)
        suggested_refresh_command = ""
        if update_available:
            if name == "ComfyUI Core" and latest:
                suggested_refresh_command = (
                    f"python scripts/refresh_snapshots.py --core-version {latest}"
                )
            elif name == "ComfyUI Frontend" and latest:
                suggested_refresh_command = (
                    f"python scripts/refresh_snapshots.py --frontend-version {latest}"
                )
        return {
            "name": name,
            "current_version": pinned["version"],
            "current_commit": pinned.get("commit", ""),
            "latest_version": latest or "unknown",
            "update_available": update_available,
            "suggested_refresh_command": suggested_refresh_command,
        }

    return {
        "components": [
            component_summary(core_pinned, core_latest, "ComfyUI Core"),
            component_summary(frontend_pinned, frontend_latest, "ComfyUI Frontend"),
        ],
        "any_update_available": (
            _is_newer_version(core_pinned["version"], core_latest)
            or _is_newer_version(frontend_pinned["version"], frontend_latest)
        ),
    }


def _build_markdown(summary: dict) -> str:
    """Build a human-readable markdown summary."""
    lines = [
        "# Upstream Version Check Summary",
        "",
        f"**Generated:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
    ]

    for comp in summary["components"]:
        lines.append(f"## {comp['name']}")
        lines.append("")
        lines.append(f"- **Current pinned version:** {comp['current_version']}")
        lines.append(f"- **Current pinned commit:** `{comp['current_commit'] or 'n/a'}`")
        lines.append(f"- **Latest upstream version:** {comp['latest_version']}")
        lines.append(f"- **Update available:** {'Yes' if comp['update_available'] else 'No'}")
        if comp["suggested_refresh_command"]:
            lines.append(f"- **Suggested refresh command:** `{comp['suggested_refresh_command']}`")
        lines.append("")

    if summary["any_update_available"]:
        lines.append("## Next Actions")
        lines.append("")
        lines.append("One or more components have a newer upstream version available.")
        lines.append(
            "Review the changelog, run the suggested refresh command, and verify the extracted output before updating pins."
        )
    else:
        lines.append("## Status")
        lines.append("")
        lines.append("No newer upstream versions were detected.")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare pinned upstream versions against latest upstream tags."
    )
    parser.add_argument(
        "--output-json", default=None, help="Path to write machine-readable JSON summary"
    )
    parser.add_argument(
        "--output-md", default=None, help="Path to write human-readable markdown summary"
    )
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds")
    args = parser.parse_args()

    core_pinned = _read_pinned_version(REFERENCES_RAW_DIR / "server_endpoints.json")
    frontend_pinned = _read_pinned_version(REFERENCES_RAW_DIR / "js_hooks.json")

    if not core_pinned:
        print(
            "ERROR: Could not read pinned core version from server_endpoints.json", file=sys.stderr
        )
        return 1
    if not frontend_pinned:
        print("ERROR: Could not read pinned frontend version from js_hooks.json", file=sys.stderr)
        return 1

    try:
        core_latest = _latest_tag_from_github(CORE_TAGS_URL)
        frontend_latest = _latest_tag_from_github(FRONTEND_TAGS_URL)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    summary = _build_summary(core_pinned, core_latest, frontend_pinned, frontend_latest)
    markdown = _build_markdown(summary)

    print(json.dumps(summary, indent=2))
    print()
    print(markdown)

    if args.output_json:
        Path(args.output_json).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote JSON summary to {display_path(args.output_json)}")

    if args.output_md:
        Path(args.output_md).write_text(markdown, encoding="utf-8")
        print(f"Wrote markdown summary to {display_path(args.output_md)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
