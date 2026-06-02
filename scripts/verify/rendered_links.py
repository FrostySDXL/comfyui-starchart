#!/usr/bin/env python3
"""Verify internal navigation links in built HTML output resolve correctly.

Usage:
    python scripts/verify/rendered_links.py
    python scripts/verify/rendered_links.py --dist-dir path/to/dist

Parses all HTML files in the built site and checks that internal <a href> links
point to existing files in the dist directory. This catches link rewrite bugs
that produce valid-looking URLs that don't resolve to real pages.

Requires the site to be built first (npm run build).

Exits 0 if all internal links are valid, exits 1 with a report of broken links.
"""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from scripts.common.display_path import display_path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DIST_DIR = REPO_ROOT / "dist"
# Must match the `base` setting in astro.config.mjs and the SITE_BASE constant in
# src/site/markdown.js. If astro.config.mjs changes, update both files together.
SITE_BASE = "/comfyui-starchart"


def find_html_files(directory: Path) -> list[Path]:
    """Find all HTML files in a directory tree."""
    return sorted(directory.rglob("*.html"))


def extract_internal_links(html_content: str, site_base: str) -> list[str]:
    """Extract internal navigation link hrefs from HTML content.

    Returns hrefs that:
    - Start with the site base path and end with / (page navigation links)
    - Are relative paths that look like page navigation (not assets)

    Excludes:
    - External URLs (http://, https://, //)
    - Anchor-only links (#...)
    - mailto:, tel:, javascript:, data: links
    - Links to static assets (files with extensions like .css, .js, .svg, .xml, etc.)
    - Links to _astro/, pagefind/, and other build artifact directories
    """
    links = []
    # Match href="..." attributes
    for match in re.finditer(r'href="([^"]*)"', html_content):
        href = match.group(1)

        # Skip empty hrefs
        if not href:
            continue

        # Skip anchor-only links
        if href.startswith("#"):
            continue

        # Skip external protocols
        if re.match(r"^(?:https?:|mailto:|tel:|javascript:|data:|//)", href, re.I):
            continue

        # Strip anchor from href for path analysis
        path_part = href.split("#")[0].split("?")[0]

        # Skip links to files with extensions (static assets)
        # Page navigation links end with / or have no extension
        if "." in path_part.split("/")[-1]:
            continue

        # Skip build artifact directories
        if "/_astro/" in href or "/pagefind/" in href:
            continue
        if href.startswith("_astro/") or href.startswith("pagefind/"):
            continue

        # Include absolute internal links (starting with site base)
        if href.startswith(site_base):
            links.append(href)
        # Include relative links that look like page navigation
        elif not href.startswith("/") and not re.match(r"^[a-z]+:", href, re.I):
            links.append(href)

    return links


def resolve_link(href: str, page_url_path: str, site_base: str) -> str:
    """Resolve a link href to an absolute path within the site.

    Args:
        href: The href value from the link
        page_url_path: The URL path of the page containing the link (e.g., /comfyui-starchart/reference/glossary/)
        site_base: The site base path (e.g., /comfyui-starchart)

    Returns:
        Absolute path within the site (e.g., /comfyui-starchart/reference/source-evidence-policy/)
    """
    # Strip anchor and query string
    parsed = urlparse(href)
    path = unquote(parsed.path)

    if path.startswith(site_base):
        # Already absolute
        return path

    # Relative link - resolve against page URL
    if page_url_path.endswith("/"):
        base_dir = page_url_path
    else:
        base_dir = page_url_path.rsplit("/", 1)[0] + "/"

    # Combine and normalize
    combined = base_dir + path
    segments = []
    for seg in combined.split("/"):
        if seg == "..":
            if segments:
                segments.pop()
        elif seg and seg != ".":
            segments.append(seg)

    return "/" + "/".join(segments) + ("/" if path.endswith("/") or not path else "")


def link_to_dist_path(resolved_link: str, site_base: str) -> str:
    """Convert a resolved link to a dist directory path.

    Args:
        resolved_link: Absolute URL path (e.g., /comfyui-starchart/reference/glossary/)
        site_base: The site base path

    Returns:
        Relative path within dist (e.g., reference/glossary/index.html)
    """
    # Strip site base
    if resolved_link.startswith(site_base):
        path = resolved_link[len(site_base) :]
    else:
        path = resolved_link

    # Strip leading slash
    path = path.lstrip("/")

    # If path ends with /, it's a directory - look for index.html
    if path.endswith("/") or not path:
        path = path + "index.html"
    elif not path.endswith(".html"):
        # Assume directory
        path = path.rstrip("/") + "/index.html"

    return path


def get_page_url_path(html_file: Path, dist_dir: Path, site_base: str) -> str:
    """Get the URL path for an HTML file.

    Args:
        html_file: Path to the HTML file
        dist_dir: Path to the dist directory
        site_base: The site base path

    Returns:
        URL path (e.g., /comfyui-starchart/reference/glossary/)
    """
    rel_path = html_file.relative_to(dist_dir)
    # Convert to URL path
    url_path = "/" + str(rel_path).replace("\\", "/")
    # Remove index.html suffix
    if url_path.endswith("/index.html"):
        url_path = url_path[: -len("index.html")]
    return site_base + url_path


def verify_links_in_file(
    html_file: Path, dist_dir: Path, site_base: str
) -> list[tuple[str, str, str]]:
    """Verify all internal links in an HTML file.

    Returns list of (href, resolved_path, expected_dist_path) tuples for broken links.
    """
    broken = []
    content = html_file.read_text(encoding="utf-8")
    page_url = get_page_url_path(html_file, dist_dir, site_base)

    for href in extract_internal_links(content, site_base):
        resolved = resolve_link(href, page_url, site_base)
        dist_path = link_to_dist_path(resolved, site_base)
        full_path = dist_dir / dist_path

        if not full_path.exists():
            broken.append((href, resolved, dist_path))

    return broken


def verify_all_links(dist_dir: Path, site_base: str) -> dict[str, list[tuple[str, str, str]]]:
    """Verify all internal links in all HTML files.

    Returns dict mapping HTML file paths to lists of broken links.
    """
    broken_by_file = {}

    for html_file in find_html_files(dist_dir):
        broken = verify_links_in_file(html_file, dist_dir, site_base)
        if broken:
            rel_path = str(html_file.relative_to(dist_dir))
            broken_by_file[rel_path] = broken

    return broken_by_file


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify internal navigation links in built HTML output."
    )
    parser.add_argument(
        "--dist-dir",
        type=Path,
        default=DEFAULT_DIST_DIR,
        help=f"Path to the built site directory (default: {DEFAULT_DIST_DIR})",
    )
    parser.add_argument(
        "--site-base",
        type=str,
        default=SITE_BASE,
        help=f"Site base path (default: {SITE_BASE})",
    )
    args = parser.parse_args()

    if not args.dist_dir.exists():
        print(f"ERROR: dist directory not found: {display_path(args.dist_dir)}")
        print("Run 'npm run build' first to generate the site.")
        return 1

    broken_by_file = verify_all_links(args.dist_dir, args.site_base)

    if not broken_by_file:
        print("All internal navigation links are valid.")
        return 0

    print("BROKEN INTERNAL LINKS:")
    total_broken = 0
    for html_file, broken_links in sorted(broken_by_file.items()):
        print(f"\n  {display_path(html_file)}:")
        for href, resolved, dist_path in broken_links:
            print(f'    href="{href}"')
            print(f"      -> resolves to: {resolved}")
            print(f"      -> expected file: {display_path(dist_path)} (NOT FOUND)")
            total_broken += 1

    print(f"\nFound {total_broken} broken link(s) in {len(broken_by_file)} file(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
