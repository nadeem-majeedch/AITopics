"""Check internal links, anchors, and navigation in the MkDocs sources.

Two modes:

    python scripts/check_docs_links.py
        Checks every Markdown file under ``docs/`` for broken relative links and
        missing heading anchors, and checks that every file in ``mkdocs.yml`` nav
        exists.

    python scripts/check_docs_links.py --site site
        Scans the built HTML for reference that would break when the site is
        served from a sub-path such as ``/AITopics/``: root-absolute URLs
        (``/assets/...``) and localhost URLs left over from development. Relative
        asset and page URLs are resolved against the output directory.

The GitHub Pages site is a project site, so every published URL lives under
``/AITopics/``. MkDocs writes relative URLs, which survive that prefix; this
script fails the build if a page starts using root-absolute paths instead.

Exit status is 0 when clean and 1 when problems are found, so it can gate CI.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CONFIG = ROOT / "mkdocs.yml"

FENCE = re.compile(r"^(```|~~~)")
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
EXPLICIT_ID = re.compile(r"\s*\{#([A-Za-z0-9_-]+)\}\s*$")
INLINE_CODE = re.compile(r"`[^`\n]*`")
LINK = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)>\s]+)>?(?:\s+\"[^\"]*\")?\s*\)")
HTML_ATTR = re.compile(r'(?:href|src)="([^"]+)"')
SKIP_SCHEMES = ("http://", "https://", "mailto:", "tel:", "javascript:", "data:", "ftp://")

# MkDocs/pymdownx default slugify, plus the duplicate suffixes toc assigns.
def slugify(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[^\w\s-]", "", text.strip().lower())
    return re.sub(r"[-\s]+", "-", text)


def strip_code(text: str) -> str:
    """Remove fenced blocks and inline code so examples are not treated as links."""
    out: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if FENCE.match(line.lstrip()):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else INLINE_CODE.sub("", line))
    return "\n".join(out)


def anchors(markdown: str) -> set[str]:
    """Heading ids a page exposes, including toc's duplicate suffixes."""
    found: set[str] = set()
    seen: dict[str, int] = {}
    in_fence = False
    for line in markdown.splitlines():
        if FENCE.match(line.lstrip()):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING.match(line)
        if not match:
            continue
        title = match.group(2).strip()
        explicit = EXPLICIT_ID.search(title)
        if explicit:
            found.add(explicit.group(1))
            continue
        base = slugify(title)
        if not base:
            continue
        count = seen.get(base, 0)
        seen[base] = count + 1
        found.add(base if count == 0 else f"{base}_{count}")
    return found


class Page:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.text = strip_code(path.read_text(encoding="utf-8"))
        self.anchors = anchors(path.read_text(encoding="utf-8"))


def nav_files(config: dict) -> list[str]:
    files: list[str] = []

    def walk(node) -> None:
        if isinstance(node, str):
            files.append(node)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, dict):
            for value in node.values():
                walk(value)

    walk(config.get("nav", []))
    return files


class _Loader(yaml.SafeLoader):
    """SafeLoader that tolerates MkDocs' pymdownx ``!!python/name:`` tag."""


_Loader.add_multi_constructor(
    "tag:yaml.org,2002:python/name:", lambda loader, suffix, node: suffix
)


def load_config(path: Path) -> dict:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=_Loader)  # noqa: S506 - safe subclass


def check_sources() -> list[str]:
    problems: list[str] = []
    pages = {path: Page(path) for path in sorted(DOCS.rglob("*.md"))}

    for path, page in pages.items():
        for match in LINK.finditer(page.text):
            target = match.group(1).strip()
            if not target or target.startswith(SKIP_SCHEMES):
                continue
            if target.startswith("#"):
                fragment = unquote(target[1:])
                if fragment and fragment not in page.anchors:
                    problems.append(f"{path.relative_to(ROOT)}: missing anchor #{fragment}")
                continue
            if target.startswith("/"):
                problems.append(
                    f"{path.relative_to(ROOT)}: root-absolute link {target} breaks under /AITopics/"
                )
                continue
            parts = urlsplit(target)
            raw_path = unquote(parts.path)
            if not raw_path:
                continue
            resolved = (path.parent / raw_path).resolve()
            if not resolved.exists():
                problems.append(f"{path.relative_to(ROOT)}: missing target {target}")
                continue
            if parts.fragment and resolved.suffix == ".md" and resolved in pages:
                fragment = unquote(parts.fragment)
                if fragment and fragment not in pages[resolved].anchors:
                    problems.append(
                        f"{path.relative_to(ROOT)}: {target} has no anchor #{fragment}"
                    )

    config = load_config(CONFIG)
    for entry in nav_files(config):
        if entry.startswith(SKIP_SCHEMES) or entry.startswith("#"):
            continue
        candidate = DOCS / entry
        if not candidate.exists():
            problems.append(f"mkdocs.yml nav points at missing file: {entry}")

    return problems


def site_base_path() -> str:
    """Path component of ``site_url``, for example ``/AITopics``."""
    url = str(load_config(CONFIG).get("site_url", "") or "")
    return urlsplit(url).path.rstrip("/")


def check_site(site: Path) -> list[str]:
    problems: list[str] = []
    if not site.is_dir():
        return [f"built site directory not found: {site}"]

    html_files = sorted(site.rglob("*.html"))
    if not html_files:
        return [f"no HTML files under {site}; did the build run?"]

    base = site_base_path()

    for page in html_files:
        text = page.read_text(encoding="utf-8", errors="replace")
        # Code samples are documentation, not references: drop them before scanning.
        text = re.sub(r"<(pre|code)\b.*?</\1>", "", text, flags=re.IGNORECASE | re.DOTALL)
        for match in HTML_ATTR.finditer(text):
            target = match.group(1).strip()
            if target.startswith("//") or target.startswith("#"):
                continue
            if any(target.startswith(scheme) for scheme in SKIP_SCHEMES):
                if "127.0.0.1" in target or "localhost" in target:
                    problems.append(f"{page.relative_to(site)}: development URL {target}")
                continue
            if target.startswith("/"):
                # MkDocs writes prefixed absolute URLs in 404.html on purpose; those
                # are valid. A root-absolute URL without the project prefix is not.
                if base and (target == base or target.startswith(base + "/")):
                    relative = target[len(base):].lstrip("/") or "."
                    resolved = (site / unquote(relative)).resolve()
                    if not resolved.exists():
                        problems.append(f"{page.relative_to(site)}: broken prefixed URL {target}")
                    continue
                problems.append(
                    f"{page.relative_to(site)}: root-absolute URL {target} lacks the {base or '/'} prefix"
                )
                continue
            parts = urlsplit(target)
            if not parts.path:
                continue
            resolved = (page.parent / unquote(parts.path)).resolve()
            if not resolved.exists():
                problems.append(f"{page.relative_to(site)}: broken asset or page {target}")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, help="scan a built site directory instead of sources")
    args = parser.parse_args()

    problems = check_site(args.site) if args.site else check_sources()
    if problems:
        print(f"{len(problems)} problem(s):")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    if args.site:
        count = len(list(args.site.rglob("*.html")))
        base = site_base_path() or "/"
        print(f"ok: {count} built pages, relative URLs resolve and absolute URLs use {base}")
    else:
        count = len(list(DOCS.rglob("*.md")))
        print(f"ok: {count} Markdown files, links, anchors, and nav entries all resolve")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
