#!/usr/bin/env python3
"""Verify shared site/base configuration stays consistent across site tooling."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SITE_CONFIG_PATH = REPO_ROOT / "src" / "site" / "site-config.json"
ASTRO_CONFIG_PATH = REPO_ROOT / "astro.config.mjs"
MARKDOWN_PATH = REPO_ROOT / "src" / "site" / "markdown.js"
RENDERED_LINKS_PATH = REPO_ROOT / "scripts" / "verify" / "rendered_links.py"

EXPECTED_KEYS = {"site", "base", "siteBaseNoTrailingSlash"}


def normalize_site_base_no_trailing_slash(site: str, base: str) -> str:
    """Return site + base with leading/trailing slashes normalized."""
    normalized = (site or "").rstrip("/") + "/" + (base or "").lstrip("/").rstrip("/").lstrip("/")
    return normalized.rstrip("/") or ""


def normalize_base_path(base: str) -> str:
    """Return the route base as a leading-slash, no-trailing-slash path."""
    normalized = "/" + (base or "").lstrip("/").rstrip("/").lstrip("/")
    return normalized.rstrip("/") or ""


def load_site_config(path: Path = SITE_CONFIG_PATH) -> dict[str, str]:
    """Load and return the shared site config JSON."""
    data: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("site-config.json must contain a JSON object")
    return data


def validate_site_config(data: dict[str, Any]) -> list[str]:
    """Return validation errors for the shared site config object."""
    errors: list[str] = []
    if set(data) != EXPECTED_KEYS:
        errors.append(
            f"src/site/site-config.json must contain exactly keys: {sorted(EXPECTED_KEYS)}"
        )
    for key in EXPECTED_KEYS & set(data):
        if not isinstance(data[key], str):
            errors.append(f"src/site/site-config.json: {key} must be a string")
    if errors:
        return errors

    expected = normalize_site_base_no_trailing_slash(data["site"], data["base"])
    if data["siteBaseNoTrailingSlash"] != expected:
        errors.append(
            "src/site/site-config.json: siteBaseNoTrailingSlash must equal "
            "normalize_site_base_no_trailing_slash(site, base)"
        )
    if "/" in data["site"].removeprefix("https://").removeprefix("http://"):
        errors.append("src/site/site-config.json: site must not include a path component")
    return errors


def validate_tool_references() -> list[str]:
    """Return errors when site tooling stops using the shared JSON config."""
    checks = (
        (ASTRO_CONFIG_PATH, "siteConfig.site", "siteConfig.base"),
        (MARKDOWN_PATH, "site-config.json", "normalizeSiteBaseNoTrailingSlash"),
        (RENDERED_LINKS_PATH, "SITE_CONFIG_PATH", "normalize_base_path"),
    )
    errors: list[str] = []
    for path, *needles in checks:
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                errors.append(f"{path.relative_to(REPO_ROOT).as_posix()}: missing {needle}")
    return errors


def main() -> int:
    """Run site/base consistency checks."""
    errors = validate_site_config(load_site_config())
    errors.extend(validate_tool_references())
    if errors:
        print("SITE BASE CONSISTENCY ERRORS:")
        for error in errors:
            print(f"  {error}")
        return 1
    print("Site base configuration is consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
