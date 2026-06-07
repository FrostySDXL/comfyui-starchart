"""Read the published delta-summary support artifact."""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def load_json_from_location(location: str) -> dict[str, Any]:
    if location.endswith(".json"):
        return _load_json_file_or_url(location)

    url = urllib.parse.urljoin(location.rstrip("/") + "/", "artifacts/delta-summary.json")
    with urllib.request.urlopen(url) as response:
        return json.load(response)


def _load_json_file_or_url(location: str) -> dict[str, Any]:
    parsed = urllib.parse.urlparse(location)
    if parsed.scheme == "file":
        path = Path(urllib.request.url2pathname(parsed.path))
        return json.loads(path.read_text(encoding="utf-8"))
    if parsed.scheme in {"http", "https"}:
        with urllib.request.urlopen(location) as response:
            return json.load(response)
    return json.loads(Path(location).read_text(encoding="utf-8"))


def iter_artifact_sections(artifacts: dict[str, Any], prefix: str = ""):
    for name, value in artifacts.items():
        section_name = f"{prefix}.{name}" if prefix else name
        if not isinstance(value, dict):
            continue
        if has_count_summary(value):
            yield section_name, value
            continue
        yield from iter_artifact_sections(value, section_name)


def has_count_summary(value: dict[str, Any]) -> bool:
    return any(key in value for key in ("old_count", "new_count", "added", "removed", "changed"))


def section_count(value: dict[str, Any], key: str) -> int:
    section = value.get(key, [])
    return len(section) if isinstance(section, list) else 0


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(
            "Usage: py -3.11 examples/consumers/python-artifact-delta-reader/read_delta_summary.py <published-site-base-url-or-delta-summary.json>",
            file=sys.stderr,
        )
        return 1

    payload = load_json_from_location(argv[1])
    comparison = payload.get("comparison", {})
    artifacts = payload.get("artifacts", {})

    print(f"Old baseline: {comparison.get('old', 'unknown')}")
    print(f"New baseline: {comparison.get('new', 'unknown')}")
    print(f"Methodology: {comparison.get('methodology', 'unknown')}")
    print(f"Source kind: {comparison.get('source_kind', 'unknown')}")
    if comparison.get("old_label"):
        print(f"Old label: {comparison['old_label']}")
    if comparison.get("new_label"):
        print(f"New label: {comparison['new_label']}")

    for section_name, summary in iter_artifact_sections(artifacts):
        print(
            f"{section_name}: old={summary.get('old_count', 0)} "
            f"new={summary.get('new_count', 0)} "
            f"added={section_count(summary, 'added')} "
            f"removed={section_count(summary, 'removed')} "
            f"changed={section_count(summary, 'changed')}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
