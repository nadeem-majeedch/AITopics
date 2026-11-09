#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Validate the AITopics licensing architecture and its documentation.

The checker is deliberately explicit. It does not guess a licence from a file
extension; it reads ``licensing-scope.json``, the official legal texts, and the
maintained notices. Exit status is 0 for PASS or PASS WITH WARNINGS and 1 for
FAIL.

Usage:
    python scripts/check_licensing.py
    python scripts/check_licensing.py --root .
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "LICENSE",
    "LICENSES/CC-BY-4.0.txt",
    "LICENSES/CC0-1.0.txt",
    "LICENSES/README.md",
    "LICENSES/SYNTHETIC-DATA.md",
    "licensing-scope.json",
)

# SHA-256 of the complete official text after normalising CRLF to LF.
CC_TEXT_SHA256 = {
    "LICENSES/CC-BY-4.0.txt": "9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411",
    "LICENSES/CC0-1.0.txt": "a2010f343487d3f7618affe54f789f5487602331c0a8d03f49e9a7c547cf0499",
}

# The MIT licence body is the 162-word text from opensource.org, excluding the
# copyright line. Normalisation makes ASCII and typographic quotes equivalent.
MIT_BODY_SHA256 = "fe2a9817987f862eaced948f0468c7f51d2fedfc48c5c505b246a49a3870e9a5"

ALLOWED_SPDX = {
    "MIT",
    "CC-BY-4.0",
    "CC0-1.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "Apache-2.0",
    "MIT-CMU",
}

REQUIRED_SCOPES = {
    "original-source-code",
    "original-educational-content",
    "original-synthetic-data",
    "official-legal-texts",
}

REQUIRED_THIRD_PARTY = {
    "dependencies",
    "external-datasets",
    "pretrained-weights",
    "ssdlite-weights",
    "external-media",
}

CONFLICT_PATTERNS = (
    "license has not yet been approved",
    "licence has not yet been approved",
    "licensing is pending",
    "licence is pending",
    "no repository licence",
    "no repository license",
    "no licence has been selected",
    "no license has been selected",
    "license files | pending",
    "licence files | pending",
    "copyright remains with the author",
    "reuse requires written permission",
)

DOCUMENTATION_FILES = (
    "README.md",
    "docs/index.md",
    "docs/technical/contributing.md",
    "docs/technical/licensing-and-attribution.md",
    "docs/technical/licensing-decision-package.md",
    "docs/planning/content-inventory.md",
    "docs/technical/release-readiness-audit.md",
)

SSDLITE_FILES = (
    "projects/video-ai/video_core/detect.py",
    "projects/video-ai/lab2_object_detection.py",
    "docs/lessons/video-ai/model-card.md",
    "docs/technical/licensing-and-attribution.md",
    "LICENSES/README.md",
)

FORBIDDEN_WEIGHT_CLAIMS = (
    "bsd-3-clause code and weights",
    "weights are mit",
    "weights are bsd",
    "weights are apache",
    "mit-licensed weights",
    "mit licensed weights",
    "coco weights are mit",
    "coco weights are bsd",
    "coco weights are apache",
)


@dataclass(frozen=True)
class Result:
    check: str
    status: str
    detail: str


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _normalise(text: str) -> str:
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    return " ".join(text.split())


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Translate a POSIX-style glob with ** into a path regex."""

    out: list[str] = []
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if pattern.startswith("**/", index):
            out.append("(?:.*/)?")
            index += 3
        elif pattern.startswith("**", index):
            out.append(".*")
            index += 2
        elif char == "*":
            out.append("[^/]*")
            index += 1
        elif char == "?":
            out.append("[^/]")
            index += 1
        else:
            out.append(re.escape(char))
            index += 1
    return re.compile("^" + "".join(out) + "$")


class LicensingChecker:
    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or REPO_ROOT).resolve()
        self.manifest_path = self.root / "licensing-scope.json"

    def _document(self, relative: str) -> str:
        return _read(self.root / relative)

    def _manifest(self) -> dict:
        return json.loads(_read(self.manifest_path))

    def check_required_files(self) -> Result:
        missing = [name for name in REQUIRED_FILES if not (self.root / name).is_file()]
        if missing:
            return Result("required files", "FAIL", "missing: " + ", ".join(missing))
        return Result("required files", "PASS", f"{len(REQUIRED_FILES)} files present")

    def check_legal_texts(self) -> Result:
        problems: list[str] = []

        mit_path = self.root / "LICENSE"
        if not mit_path.is_file():
            return Result("legal texts", "FAIL", "LICENSE is missing")
        mit = _read(mit_path)
        lines = mit.splitlines()
        if not lines or lines[0].strip() != "MIT License":
            problems.append("LICENSE does not start with 'MIT License'")
        copyright_line = next((line for line in lines[:6] if line.startswith("Copyright (c) ")), "")
        match = re.fullmatch(r"Copyright \(c\) (\d{4}) (.+)", copyright_line)
        if not match:
            problems.append("LICENSE has no 'Copyright (c) YEAR HOLDER' line")
        try:
            manifest = self._manifest()
        except (OSError, json.JSONDecodeError) as exc:
            problems.append(f"manifest cannot be read for copyright check: {exc}")
        else:
            if match and match.group(1) != str(manifest.get("copyright_year", "")):
                problems.append("MIT year does not match licensing-scope.json")
            if match and match.group(2).strip() != manifest.get("copyright_holder"):
                problems.append("MIT copyright holder does not match licensing-scope.json")

        body_start = next(
            (i for i, line in enumerate(lines) if line.startswith("Permission is hereby granted")),
            None,
        )
        if body_start is None:
            problems.append("LICENSE has no MIT permission paragraph")
        else:
            body = _normalise("\n".join(lines[body_start:]))
            if hashlib.sha256(body.encode("utf-8")).hexdigest() != MIT_BODY_SHA256:
                problems.append("MIT body does not match the official 162-word text")

        markers = {
            "LICENSES/CC-BY-4.0.txt": "Creative Commons Attribution 4.0 International Public License",
            "LICENSES/CC0-1.0.txt": "CC0 1.0 Universal",
        }
        for relative, digest in CC_TEXT_SHA256.items():
            path = self.root / relative
            if not path.is_file():
                problems.append(f"{relative} is missing")
                continue
            data = path.read_bytes().replace(b"\r\n", b"\n")
            if hashlib.sha256(data).hexdigest() != digest:
                problems.append(f"{relative} does not match the official text hash")
            if markers[relative] not in data.decode("utf-8", errors="replace"):
                problems.append(f"{relative} is missing its title marker")

        if problems:
            return Result("legal texts", "FAIL", "; ".join(problems))
        return Result("legal texts", "PASS", "MIT body and both CC texts verified")

    def check_manifest(self) -> Result:
        try:
            manifest = self._manifest()
        except (OSError, json.JSONDecodeError) as exc:
            return Result("scope manifest", "FAIL", f"cannot read licensing-scope.json: {exc}")

        problems: list[str] = []
        for key in ("schema_version", "approved_on", "copyright_holder", "copyright_year"):
            if not manifest.get(key):
                problems.append(f"missing top-level field: {key}")
        licenses = manifest.get("licenses", {})
        for identifier in ("MIT", "CC-BY-4.0", "CC0-1.0"):
            entry = licenses.get(identifier)
            if not isinstance(entry, dict):
                problems.append(f"missing licence entry: {identifier}")
                continue
            path = entry.get("path")
            if not path or not (self.root / path).is_file():
                problems.append(f"{identifier} path is missing or does not exist")
            if not entry.get("scope"):
                problems.append(f"{identifier} has no scope statement")

        scopes = manifest.get("scopes", [])
        scope_ids = {scope.get("id") for scope in scopes if isinstance(scope, dict)}
        missing_scopes = REQUIRED_SCOPES - scope_ids
        if missing_scopes:
            problems.append("missing scope(s): " + ", ".join(sorted(missing_scopes)))
        for scope in scopes:
            if not isinstance(scope, dict):
                problems.append("scope entry is not an object")
                continue
            license_id = scope.get("license")
            if license_id not in set(licenses) | {"upstream-text"}:
                problems.append(f"scope {scope.get('id')} uses unknown licence {license_id}")
            if scope.get("status") not in {"approved", "verified", "excluded"}:
                problems.append(f"scope {scope.get('id')} has invalid status")
            if not scope.get("include"):
                problems.append(f"scope {scope.get('id')} has no include paths")

        third_party = manifest.get("third_party_exclusions", [])
        third_party_ids = {item.get("id") for item in third_party if isinstance(item, dict)}
        missing_third_party = REQUIRED_THIRD_PARTY - third_party_ids
        if missing_third_party:
            problems.append("missing third-party exception(s): " + ", ".join(sorted(missing_third_party)))
        for item in third_party:
            if isinstance(item, dict):
                if item.get("bundled") is not False:
                    problems.append(f"third-party item {item.get('id')} must not be bundled")
                if not item.get("terms"):
                    problems.append(f"third-party item {item.get('id')} has no terms")
        non_content = manifest.get("non_content_files", [])
        if not non_content:
            problems.append("non-content placeholder rules are not recorded")
        for item in non_content:
            if not isinstance(item, dict) or not item.get("pattern") or not item.get("reason"):
                problems.append("non-content entry needs a pattern and reason")
        if not manifest.get("unresolved"):
            problems.append("unresolved licensing items are not recorded")

        if problems:
            return Result("scope manifest", "FAIL", "; ".join(problems))
        return Result("scope manifest", "PASS", f"{len(scopes)} scopes, {len(third_party)} exclusions")

    def check_documentation(self) -> Result:
        problems: list[str] = []
        readme = self._document("README.md")
        for phrase in (
            "MIT",
            "CC BY 4.0",
            "CC0 1.0",
            "third-party",
            "commercial",
            "model weights",
            "not covered",
        ):
            if phrase.lower() not in readme.lower():
                problems.append(f"README lacks '{phrase}'")
        for phrase in ("LICENSES/README.md", "licensing-scope.json"):
            if phrase not in readme:
                problems.append(f"README does not point to {phrase}")

        licences_readme = self._document("LICENSES/README.md")
        for phrase in ("licensing-scope.json", "SSDLite", "unresolved", "third-party"):
            if phrase.lower() not in licences_readme.lower():
                problems.append(f"LICENSES/README.md lacks '{phrase}'")

        register = self._document("docs/technical/licensing-and-attribution.md")
        for phrase in (
            "Original Python source code",
            "Jupyter notebooks",
            "Original synthetic datasets",
            "Third-party datasets",
            "Pretrained models",
            "Dependencies",
            "SSDLite",
            "Approved and implemented",
            "Pending verification",
            "Excluded third-party material",
        ):
            if phrase.lower() not in register.lower():
                problems.append(f"register lacks '{phrase}'")

        decision = self._document("docs/technical/licensing-decision-package.md")
        for phrase in (
            "Instructor approval",
            "Implementation date",
            "Files created",
            "Third-party exceptions",
            "Remaining unresolved",
        ):
            if phrase.lower() not in decision.lower():
                problems.append(f"decision package lacks '{phrase}'")

        if "License texts | `LICENSE`, `LICENSES/` | 1 | Blocked" in self._document(
            "docs/planning/content-inventory.md"
        ):
            problems.append("content inventory still marks licence texts as Blocked")

        for relative in DOCUMENTATION_FILES:
            path = self.root / relative
            if not path.is_file():
                problems.append(f"documentation file is missing: {relative}")
                continue
            lower = _read(path).lower()
            for pattern in CONFLICT_PATTERNS:
                if pattern in lower:
                    problems.append(f"{relative} contains conflicting phrase: '{pattern}'")

        if problems:
            return Result("documentation", "FAIL", "; ".join(problems))
        return Result("documentation", "PASS", "approved statements and register categories found")

    def check_ssdlite(self) -> Result:
        problems: list[str] = []
        for relative in SSDLITE_FILES:
            path = self.root / relative
            if not path.is_file():
                problems.append(f"missing SSDLite evidence file: {relative}")
                continue
            text = _read(path)
            lower = text.lower()
            if relative.startswith("projects/") or relative.startswith("docs/"):
                if "ssdlite" not in lower and "weight" not in lower:
                    problems.append(f"{relative} does not mention SSDLite or weights")
                if "unresolved" not in lower and "not separately stated" not in lower:
                    problems.append(f"{relative} does not record unresolved weight terms")
            for claim in FORBIDDEN_WEIGHT_CLAIMS:
                if claim in lower:
                    problems.append(f"{relative} makes a forbidden weight claim: '{claim}'")

        register = self._document("docs/technical/licensing-and-attribution.md").lower()
        if "ssdlite" not in register or "unresolved" not in register:
            problems.append("register does not record SSDLite weights as unresolved")

        if problems:
            return Result("SSDLite weights", "FAIL", "; ".join(problems))
        return Result("SSDLite weights", "PASS", "code and weight terms distinguished; weights unresolved")

    def check_synthetic(self) -> Result:
        path = self.root / "LICENSES/SYNTHETIC-DATA.md"
        if not path.is_file():
            return Result("synthetic data", "FAIL", "LICENSES/SYNTHETIC-DATA.md is missing")
        text = _read(path)
        lower = text.lower()
        problems: list[str] = []
        for phrase in ("objects_p06", "cc0 1.0", "960", "no third-party", "make_vision_data.py"):
            if phrase.lower() not in lower:
                problems.append(f"P06 record lacks '{phrase}'")

        card = self.root / "data/computer-vision/dataset_card.json"
        if card.is_file():
            try:
                data = json.loads(_read(card))
            except json.JSONDecodeError:
                problems.append("dataset_card.json is not valid JSON")
            else:
                if "CC0-1.0" not in str(data.get("licence", "")):
                    problems.append("dataset card does not declare CC0-1.0")
                if "third-party" not in str(data.get("attribution", "")).lower():
                    problems.append("dataset card does not state that no third-party images are included")

        if problems:
            return Result("synthetic data", "FAIL", "; ".join(problems))
        return Result("synthetic data", "PASS", "P06 CC0 provenance record is explicit")

    def _scope_hits(self, relative: str) -> list[str]:
        try:
            manifest = self._manifest()
        except (OSError, json.JSONDecodeError):
            return []
        matches: list[str] = []
        for scope in manifest.get("scopes", []):
            includes = [_glob_to_regex(pattern) for pattern in scope.get("include", [])]
            excludes = [_glob_to_regex(pattern) for pattern in scope.get("exclude", [])]
            if any(pattern.match(relative) for pattern in includes) and not any(
                pattern.match(relative) for pattern in excludes
            ):
                matches.append(scope.get("id", scope.get("license", "")))
        return sorted(set(matches))

    def _expected_licence(self, relative: str) -> str | None:
        hits = self._scope_hits(relative)
        if len(hits) != 1:
            return None
        try:
            manifest = self._manifest()
        except (OSError, json.JSONDecodeError):
            return None
        for scope in manifest.get("scopes", []):
            if scope.get("id") == hits[0]:
                return scope.get("license")
        return None

    def _release_files(self) -> list[str]:
        """Return tracked and untracked non-ignored files, or a filesystem fallback."""

        if (self.root / ".git").exists():
            try:
                raw = subprocess.check_output(
                    ["git", "-C", str(self.root), "ls-files", "--cached", "--others", "--exclude-standard"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                )
                return [
                    path
                    for path in raw.splitlines()
                    if path and not path.startswith(".freebuff/")
                ]
            except (OSError, subprocess.CalledProcessError):
                pass

        skip_dirs = {".git", ".venv", "site", "tmp", "node_modules", "__pycache__"}
        return sorted(
            path.relative_to(self.root).as_posix()
            for path in self.root.rglob("*")
            if path.is_file()
            and not any(part in skip_dirs for part in path.relative_to(self.root).parts)
        )

    def check_scope_coverage(self, files: Iterable[str] | None = None) -> Result:
        """Every release file must have one scope or an explicit non-content rule."""

        try:
            manifest = self._manifest()
        except (OSError, json.JSONDecodeError) as exc:
            return Result("scope coverage", "FAIL", f"cannot read manifest: {exc}")
        non_content = [
            _glob_to_regex(item["pattern"])
            for item in manifest.get("non_content_files", [])
            if isinstance(item, dict) and item.get("pattern")
        ]
        unclassified: list[str] = []
        overlaps: list[str] = []
        paths = list(files) if files is not None else self._release_files()
        for relative in paths:
            if any(pattern.match(relative) for pattern in non_content):
                continue
            hits = self._scope_hits(relative)
            if not hits:
                unclassified.append(relative)
            elif len(hits) > 1:
                overlaps.append(f"{relative} ({', '.join(hits)})")

        if unclassified or overlaps:
            detail: list[str] = []
            if unclassified:
                detail.append("unclassified: " + ", ".join(sorted(unclassified)))
            if overlaps:
                detail.append("overlapping scopes: " + ", ".join(sorted(overlaps)))
            return Result("scope coverage", "FAIL", "; ".join(detail))
        return Result("scope coverage", "PASS", f"{len(paths)} release files classified")

    def check_spdx(self) -> Result:
        allowed = set(ALLOWED_SPDX)
        try:
            manifest = self._manifest()
        except (OSError, json.JSONDecodeError) as exc:
            return Result("SPDX identifiers", "FAIL", f"cannot read manifest: {exc}")
        allowed.update(manifest.get("licenses", {}).keys())

        problems: list[str] = []
        pattern = re.compile(r"SPDX-License-Identifier:\s*([A-Za-z0-9.+-]+)")
        skip_dirs = {".git", ".venv", "site", "tmp", "node_modules", "data", "__pycache__"}
        suffixes = {".py", ".md", ".json", ".yml", ".yaml", ".ipynb", ".txt"}
        for path in self.root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in suffixes:
                continue
            relative_path = path.relative_to(self.root)
            if any(part in skip_dirs for part in relative_path.parts):
                continue
            relative = relative_path.as_posix()
            try:
                text = _read(path)
            except OSError:
                continue
            for identifier in pattern.findall(text):
                if identifier not in allowed:
                    problems.append(f"{relative} uses unknown SPDX identifier {identifier}")
                expected = self._expected_licence(relative)
                if expected and expected != "upstream-text" and identifier != expected:
                    problems.append(
                        f"{relative} declares {identifier}, expected {expected} from the scope manifest"
                    )

        if problems:
            return Result("SPDX identifiers", "FAIL", "; ".join(problems))
        return Result("SPDX identifiers", "PASS", "all declared identifiers are known and consistent")

    def run(self) -> list[Result]:
        return [
            self.check_required_files(),
            self.check_legal_texts(),
            self.check_manifest(),
            self.check_scope_coverage(),
            self.check_documentation(),
            self.check_ssdlite(),
            self.check_synthetic(),
            self.check_spdx(),
        ]


def print_results(results: Iterable[Result]) -> str:
    statuses: list[str] = []
    for result in results:
        print(f"{result.status:5} {result.check}: {result.detail}")
        statuses.append(result.status)
    if "FAIL" in statuses:
        verdict = "FAIL"
    elif "WARN" in statuses:
        verdict = "PASS WITH WARNINGS"
    else:
        verdict = "PASS"
    print(f"RESULT: {verdict}")
    return verdict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="repository root")
    args = parser.parse_args(argv)
    verdict = print_results(LicensingChecker(args.root).run())
    return 1 if verdict == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
