#!/usr/bin/env python3
"""Verify that pinned commits in JSON metadata still exist in upstream repositories.

Checks that tags and commit hashes referenced in references/raw/*.json still
resolve in their respective GitHub repositories. Uses the GitHub API (no auth
required for public repos, but rate-limited to 60 requests/hour).

Results are cached locally in .cache/upstream_pins.json with a 24-hour TTL
to avoid repeated API calls.

Usage:
    python scripts/verify/upstream_pins.py

Exits 0 if all pins are valid, exits 1 if any are broken or unreachable.
"""

import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCES_RAW_DIR = REPO_ROOT / "references" / "raw"
CACHE_DIR = REPO_ROOT / ".cache"
CACHE_FILE = CACHE_DIR / "upstream_pins.json"
CACHE_TTL_SECONDS = 24 * 60 * 60  # 24 hours

# Map from JSON file to its upstream GitHub repo. Artifacts with multiple
# upstream components can override this default per extracted pin.
REPO_MAP = {
    "server_endpoints.json": {
        "owner": "Comfy-Org",
        "repo": "ComfyUI",
    },
    "node_api_schema.json": {
        "owner": "Comfy-Org",
        "repo": "ComfyUI",
    },
    "js_hooks.json": {
        "owner": "Comfy-Org",
        "repo": "ComfyUI_Frontend",
    },
    "websocket_events.json": {
        "owner": "Comfy-Org",
        "repo": "ComfyUI",
    },
}


def _load_cache() -> dict:
    """Load the pin verification cache, returning an empty dict if unavailable."""
    if not CACHE_FILE.exists():
        return {}
    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    return {}


def _save_cache(cache: dict) -> None:
    """Persist the pin verification cache to disk."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, indent=2) + "\n", encoding="utf-8")


def _check_commit_via_github_api(owner: str, repo: str, commit: str) -> tuple[bool, str]:
    """Check that a commit SHA still exists in a GitHub repository.

    Uses urllib.request from stdlib (no external deps).
    Returns (is_valid, detail_message).
    """
    import urllib.error
    import urllib.request

    url = f"https://api.github.com/repos/{owner}/{repo}/git/commits/{commit}"
    req = urllib.request.Request(url, headers={"User-Agent": "comfyui-kb-pin-checker/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                return True, f"commit {commit[:12]} resolves in {owner}/{repo}"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False, f"commit {commit[:12]} NOT FOUND in {owner}/{repo}"
        if e.code == 422:
            return False, f"commit {commit[:12]} invalid or not found in {owner}/{repo}"
        return False, f"HTTP {e.code} checking commit {commit[:12]} in {owner}/{repo}"
    except urllib.error.URLError as e:
        return False, f"network error checking {owner}/{repo}: {e.reason}"
    except Exception as e:
        return False, f"unexpected error checking {owner}/{repo}: {e}"

    return False, f"unexpected response checking commit {commit[:12]} in {owner}/{repo}"


def _check_tag_via_github_api(owner: str, repo: str, tag: str) -> tuple[bool, str]:
    """Check that a tag still exists in a GitHub repository.

    Returns (is_valid, detail_message).
    """
    import urllib.error
    import urllib.request

    url = f"https://api.github.com/repos/{owner}/{repo}/git/refs/tags/{tag}"
    req = urllib.request.Request(url, headers={"User-Agent": "comfyui-kb-pin-checker/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                return True, f"tag {tag} resolves in {owner}/{repo}"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False, f"tag {tag} NOT FOUND in {owner}/{repo}"
        return False, f"HTTP {e.code} checking tag {tag} in {owner}/{repo}"
    except urllib.error.URLError as e:
        return False, f"network error checking {owner}/{repo}: {e.reason}"
    except Exception as e:
        return False, f"unexpected error checking {owner}/{repo}: {e}"

    return False, f"unexpected response checking tag {tag} in {owner}/{repo}"


def extract_pins_from_json(json_path: Path) -> list[dict]:
    """Extract pinned version/commit info from a JSON reference file.

    Returns a list of dicts with keys: version, commit, source (json file name).
    """
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"  WARNING: cannot parse {json_path.name}: {e}")
        return []

    metadata = data.get("metadata", {})
    if json_path.name == "websocket_events.json" and isinstance(metadata, dict):
        commits = metadata.get("commits")
        version = metadata.get("version", "")
        versions = version.split("+", 1) if isinstance(version, str) else []
        if isinstance(commits, dict) and len(versions) == 2:
            core_commit = commits.get("core", "")
            frontend_commit = commits.get("frontend", "")
            pins = []
            if core_commit:
                pins.append(
                    {
                        "version": versions[0],
                        "commit": core_commit,
                        "source": json_path.name,
                        "owner": "Comfy-Org",
                        "repo": "ComfyUI",
                        "component": "core",
                    }
                )
            if frontend_commit:
                pins.append(
                    {
                        "version": versions[1],
                        "commit": frontend_commit,
                        "source": json_path.name,
                        "owner": "Comfy-Org",
                        "repo": "ComfyUI_Frontend",
                        "component": "frontend",
                    }
                )
            if pins:
                return pins

    version = metadata.get("version", "")
    commit = metadata.get("commit", "")

    if not version and not commit:
        return []

    return [{"version": version, "commit": commit, "source": json_path.name}]


def verify_pins(use_cache: bool = True) -> list[tuple[bool, str]]:
    """Verify all pinned commits and tags in JSON reference files.

    Returns a list of (is_valid, detail_message) tuples.
    """
    cache = _load_cache() if use_cache else {}
    now = time.time()
    results: list[tuple[bool, str]] = []

    json_files = sorted(REFERENCES_RAW_DIR.glob("*.json"))
    if not json_files:
        print("No JSON reference files found.")
        return [(True, "no pins to check")]

    for json_file in json_files:
        print(f"Checking {json_file.name}...")

        repo_info = REPO_MAP.get(json_file.name)
        if repo_info is None:
            print(f"  SKIP: no repo mapping for {json_file.name}")
            continue

        pins = extract_pins_from_json(json_file)
        for pin in pins:
            version = pin["version"]
            commit = pin["commit"]
            owner = pin.get("owner", repo_info["owner"])
            repo = pin.get("repo", repo_info["repo"])

            # Check commit
            if commit:
                cache_key = f"{owner}/{repo}/commit/{commit}"
                cached = cache.get(cache_key)
                if use_cache and cached and (now - cached.get("timestamp", 0)) < CACHE_TTL_SECONDS:
                    is_valid = cached["valid"]
                    detail = cached["detail"]
                    print(f"  CACHED: {detail}")
                else:
                    is_valid, detail = _check_commit_via_github_api(owner, repo, commit)
                    cache[cache_key] = {
                        "valid": is_valid,
                        "detail": detail,
                        "timestamp": now,
                    }
                    print(f"  {detail}")

                results.append((is_valid, detail))

            # Check tag (version)
            if version and version != "unversioned":
                cache_key = f"{owner}/{repo}/tag/{version}"
                cached = cache.get(cache_key)
                if use_cache and cached and (now - cached.get("timestamp", 0)) < CACHE_TTL_SECONDS:
                    is_valid = cached["valid"]
                    detail = cached["detail"]
                    print(f"  CACHED: {detail}")
                else:
                    is_valid, detail = _check_tag_via_github_api(owner, repo, version)
                    cache[cache_key] = {
                        "valid": is_valid,
                        "detail": detail,
                        "timestamp": now,
                    }
                    print(f"  {detail}")

                results.append((is_valid, detail))

    if use_cache:
        _save_cache(cache)

    return results


def main():
    """Run upstream pin verification and report results."""
    results = verify_pins()

    if not results:
        print("No pins found to verify.")
        return 0

    broken = [(valid, detail) for valid, detail in results if not valid]

    print()
    if not broken:
        print(f"All {len(results)} pin(s) are valid.")
        return 0
    else:
        print(f"BROKEN PINS ({len(broken)} of {len(results)}):")
        for _, detail in broken:
            print(f"  {detail}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
