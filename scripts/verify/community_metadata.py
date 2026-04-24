#!/usr/bin/env python3
"""Validate community metadata operational rules.

Checks rules that go beyond plain schema shape:
- maintenance tier values are allowed
- evidence labels are non-empty strings
- needs_review_after >= last_verified
- generated pages point to an existing metadata source

Usage:
    python scripts/verify/community_metadata.py

Exits 0 if all rules pass, exits 1 with a report of violations.
"""

import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMUNITY_DIR = REPO_ROOT / "references" / "community"

ALLOWED_TIERS = {"tier_1", "tier_2", "tier_3", "tier_4"}
STATUSES_REQUIRING_EVIDENCE = {
    "Actively Maintained",
    "Community Supported",
    "Likely Unmaintained",
}


def _parse_date(value: str) -> date:
    """Parse an ISO date string (YYYY-MM-DD)."""
    year, month, day = value.split("-")
    return date(int(year), int(month), int(day))


def validate_packages(data: dict, filename: str) -> list[str]:
    """Validate operational rules for ecosystem packages."""
    errors = []
    packages = data.get("packages", [])
    for i, package in enumerate(packages):
        prefix = f"{filename}: packages[{i}]"

        tier = package.get("maintenance_tier", "")
        if tier and tier not in ALLOWED_TIERS:
            errors.append(f"{prefix} has invalid maintenance_tier '{tier}'")

        last_verified = package.get("last_verified", "")
        needs_review = package.get("needs_review_after", "")
        if last_verified and needs_review:
            try:
                if _parse_date(needs_review) < _parse_date(last_verified):
                    errors.append(
                        f"{prefix} needs_review_after ({needs_review}) is before "
                        f"last_verified ({last_verified})"
                    )
            except ValueError as e:
                errors.append(f"{prefix} has invalid date format: {e}")

        status = package.get("status")
        evidence_urls = package.get("evidence_urls", [])
        if status in STATUSES_REQUIRING_EVIDENCE:
            non_empty_urls = [url for url in evidence_urls if isinstance(url, str) and url.strip()]
            if not non_empty_urls:
                errors.append(
                    f"{prefix} with status '{status}' must include at least one evidence_urls entry"
                )

    return errors


def validate_pages(data: dict, filename: str) -> list[str]:
    """Validate operational rules for community pages."""
    errors = []
    pages = data.get("pages", [])
    for i, page in enumerate(pages):
        prefix = f"{filename}: pages[{i}]"

        tier = page.get("maintenance_tier", "")
        if tier and tier not in ALLOWED_TIERS:
            errors.append(f"{prefix} has invalid maintenance_tier '{tier}'")

        evidence = page.get("evidence_label", "")
        if evidence and not isinstance(evidence, str):
            errors.append(f"{prefix} evidence_label must be a string")
        elif not evidence:
            errors.append(f"{prefix} evidence_label is empty")

        last_verified = page.get("last_verified", "")
        needs_review = page.get("needs_review_after", "")
        if last_verified and needs_review:
            try:
                if _parse_date(needs_review) < _parse_date(last_verified):
                    errors.append(
                        f"{prefix} needs_review_after ({needs_review}) is before "
                        f"last_verified ({last_verified})"
                    )
            except ValueError as e:
                errors.append(f"{prefix} has invalid date format: {e}")

        generated_from = page.get("generated_from")
        if generated_from is not None:
            source_path = REPO_ROOT / generated_from
            if not source_path.exists():
                errors.append(
                    f"{prefix} generated_from points to missing file '{generated_from}'"
                )

    return errors


def main() -> int:
    all_errors = []
    json_files = sorted(COMMUNITY_DIR.glob("*.json"))

    for json_file in json_files:
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            all_errors.append(f"{json_file.name}: invalid JSON: {e}")
            continue

        if json_file.name == "ecosystem_packages.json":
            all_errors.extend(validate_packages(data, json_file.name))
        elif json_file.name == "community_pages.json":
            all_errors.extend(validate_pages(data, json_file.name))

    if not all_errors:
        print("Community metadata operational rules pass.")
        return 0
    else:
        print(f"Found {len(all_errors)} community metadata violation(s):")
        for error in all_errors:
            print(f"  {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
