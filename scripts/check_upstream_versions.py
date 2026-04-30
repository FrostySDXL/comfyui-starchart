#!/usr/bin/env python3
"""Compare pinned upstream versions against latest upstream tags and produce a summary.

Usage:
    python scripts/check_upstream_versions.py
    python scripts/check_upstream_versions.py --output-json summary.json --output-md summary.md

Exits 0 after producing summaries. Exits 1 on network or data errors.
"""

import argparse
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCES_RAW_DIR = REPO_ROOT / "references" / "raw"

CORE_TAGS_URL = "https://api.github.com/repos/Comfy-Org/ComfyUI/tags?per_page=100"
FRONTEND_TAGS_URL = "https://api.github.com/repos/Comfy-Org/ComfyUI_Frontend/tags?per_page=100"


def _fetch_json(url: str, timeout: int = 30) -> list | dict:
    """Fetch and parse JSON from a URL."""
    req = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "comfyui-kb-upstream-watch"})
    try:
        with urlopen(req, timeout=timeout) as response:
            return json.loads(response.read())
    except HTTPError as exc:
        raise RuntimeError(f"HTTP error {exc.code} from {url}: {exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"URL error reaching {url}: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON from {url}: {exc}") from exc


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


def _build_summary(core_pinned: dict, core_latest: str | None, frontend_pinned: dict, frontend_latest: str | None) -> dict:
    """Build a machine-readable summary dict."""
    def component_summary(pinned: dict, latest: str | None, name: str) -> dict:
        update_available = latest is not None and latest != pinned["version"]
        return {
            "name": name,
            "current_version": pinned["version"],
            "current_commit": pinned.get("commit", ""),
            "latest_version": latest or "unknown",
            "update_available": update_available,
            "suggested_refresh_command": f"python scripts/refresh_snapshots.py --core-version {latest}" if name == "ComfyUI Core" and latest else (
                f"python scripts/refresh_snapshots.py --frontend-version {latest}" if name == "ComfyUI Frontend" and latest else ""
            ),
        }

    return {
        "components": [
            component_summary(core_pinned, core_latest, "ComfyUI Core"),
            component_summary(frontend_pinned, frontend_latest, "ComfyUI Frontend"),
        ],
        "any_update_available": (
            (core_latest is not None and core_latest != core_pinned["version"]) or
            (frontend_latest is not None and frontend_latest != frontend_pinned["version"])
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
        if comp['suggested_refresh_command']:
            lines.append(f"- **Suggested refresh command:** `{comp['suggested_refresh_command']}`")
        lines.append("")

    if summary["any_update_available"]:
        lines.append("## Next Actions")
        lines.append("")
        lines.append("One or more components have a newer upstream version available.")
        lines.append("Review the changelog, run the suggested refresh command, and verify the extracted output before updating pins.")
    else:
        lines.append("## Status")
        lines.append("")
        lines.append("All pinned versions match the latest discovered upstream tags.")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare pinned upstream versions against latest upstream tags."
    )
    parser.add_argument("--output-json", default=None, help="Path to write machine-readable JSON summary")
    parser.add_argument("--output-md", default=None, help="Path to write human-readable markdown summary")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds")
    args = parser.parse_args()

    core_pinned = _read_pinned_version(REFERENCES_RAW_DIR / "server_endpoints.json")
    frontend_pinned = _read_pinned_version(REFERENCES_RAW_DIR / "js_hooks.json")

    if not core_pinned:
        print("ERROR: Could not read pinned core version from server_endpoints.json", file=sys.stderr)
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
        print(f"Wrote JSON summary to {args.output_json}")

    if args.output_md:
        Path(args.output_md).write_text(markdown, encoding="utf-8")
        print(f"Wrote markdown summary to {args.output_md}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
