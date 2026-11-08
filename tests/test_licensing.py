# SPDX-License-Identifier: MIT
"""Tests for scripts/check_licensing.py."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.check_licensing import REPO_ROOT, LicensingChecker


def _manifest(third_party: list[dict] | None = None) -> dict:
    return {
        "schema_version": 1,
        "approved_on": "2026-11-07",
        "copyright_holder": "Muhammad Nadeem Majeed",
        "copyright_year": "2026",
        "licenses": {
            "MIT": {"path": "LICENSE", "scope": "code"},
            "CC-BY-4.0": {"path": "LICENSES/CC-BY-4.0.txt", "scope": "content"},
            "CC0-1.0": {"path": "LICENSES/CC0-1.0.txt", "scope": "data"},
        },
        "scopes": [
            {
                "id": "original-source-code",
                "license": "MIT",
                "status": "approved",
                "include": ["scripts/**"],
                "exclude": [],
            },
            {
                "id": "original-educational-content",
                "license": "CC-BY-4.0",
                "status": "approved",
                "include": ["docs/**/*.md"],
                "exclude": [],
            },
            {
                "id": "original-synthetic-data",
                "license": "CC0-1.0",
                "status": "approved",
                "include": ["data/**"],
                "exclude": [],
            },
            {
                "id": "official-legal-texts",
                "license": "upstream-text",
                "status": "verified",
                "include": ["LICENSES/*.txt"],
                "exclude": [],
            },
        ],
        "non_content_files": [
            {"pattern": "**/.gitkeep", "reason": "empty placeholder"}
        ],
        "third_party_exclusions": third_party
        if third_party is not None
        else [
            {"id": "dependencies", "bundled": False, "terms": "upstream"},
            {"id": "external-datasets", "bundled": False, "terms": "upstream"},
            {"id": "pretrained-weights", "bundled": False, "terms": "upstream"},
            {"id": "ssdlite-weights", "bundled": False, "terms": "unresolved"},
            {"id": "external-media", "bundled": False, "terms": "upstream"},
        ],
        "unresolved": ["SSDLite weight terms"],
    }


def _write_manifest(root: Path, data: dict) -> None:
    (root / "licensing-scope.json").write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8"
    )


def _touch_required_licences(root: Path) -> None:
    (root / "LICENSES").mkdir(parents=True, exist_ok=True)
    for relative in ("LICENSE", "LICENSES/CC-BY-4.0.txt", "LICENSES/CC0-1.0.txt"):
        (root / relative).write_text("placeholder\n", encoding="utf-8")


class LicensingValidatorTests(unittest.TestCase):
    def test_missing_licence_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "LICENSES").mkdir()
            result = LicensingChecker(root).check_required_files()
            self.assertEqual(result.status, "FAIL")
            self.assertIn("LICENSE", result.detail)

    def test_missing_third_party_exception(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _touch_required_licences(root)
            data = _manifest(
                third_party=[
                    {"id": "dependencies", "bundled": False, "terms": "upstream"},
                    {"id": "external-datasets", "bundled": False, "terms": "upstream"},
                    {"id": "pretrained-weights", "bundled": False, "terms": "upstream"},
                    {"id": "ssdlite-weights", "bundled": False, "terms": "unresolved"},
                ]
            )
            _write_manifest(root, data)
            result = LicensingChecker(root).check_manifest()
            self.assertEqual(result.status, "FAIL")
            self.assertIn("external-media", result.detail)

    def test_conflicting_spdx_identifier(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _touch_required_licences(root)
            _write_manifest(root, _manifest())
            (root / "scripts").mkdir()
            (root / "scripts/example.py").write_text(
                "# SPDX-License-Identifier: " + "GPL-3.0\n", encoding="utf-8"
            )
            result = LicensingChecker(root).check_spdx()
            self.assertEqual(result.status, "FAIL")
            self.assertIn("GPL-3.0", result.detail)

    def test_unresolved_model_weight_licence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "projects/video-ai/video_core").mkdir(parents=True)
            (root / "projects/video-ai/video_core/detect.py").write_text(
                "SSDLite weights are MIT.\n", encoding="utf-8"
            )
            (root / "projects/video-ai/lab2_object_detection.py").write_text(
                "SSDLite weights unresolved.\n", encoding="utf-8"
            )
            (root / "docs/lessons/video-ai").mkdir(parents=True)
            (root / "docs/lessons/video-ai/model-card.md").write_text(
                "SSDLite weights unresolved.\n", encoding="utf-8"
            )
            (root / "docs/technical").mkdir(parents=True)
            (root / "docs/technical/licensing-and-attribution.md").write_text(
                "SSDLite weights unresolved.\n", encoding="utf-8"
            )
            (root / "LICENSES").mkdir()
            (root / "LICENSES/README.md").write_text(
                "SSDLite weights unresolved.\n", encoding="utf-8"
            )
            result = LicensingChecker(root).check_ssdlite()
            self.assertEqual(result.status, "FAIL")
            self.assertIn("forbidden weight claim", result.detail)

    def test_missing_synthetic_attribution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "LICENSES").mkdir()
            (root / "LICENSES/SYNTHETIC-DATA.md").write_text(
                "CC0 1.0 synthetic data.\n", encoding="utf-8"
            )
            result = LicensingChecker(root).check_synthetic()
            self.assertEqual(result.status, "FAIL")
            self.assertIn("objects_p06", result.detail)

    def test_correct_mixed_licence_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _touch_required_licences(root)
            _write_manifest(root, _manifest())
            (root / "scripts").mkdir()
            (root / "scripts/code.py").write_text(
                "# SPDX-License-Identifier: " + "MIT\n", encoding="utf-8"
            )
            (root / "docs").mkdir()
            (root / "docs/lesson.md").write_text(
                "<!-- SPDX-License-Identifier: " + "CC-BY-4.0 -->\n", encoding="utf-8"
            )
            result = LicensingChecker(root).check_spdx()
            self.assertEqual(result.status, "PASS")

    def test_tampered_cc_text_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _touch_required_licences(root)
            _write_manifest(root, _manifest())
            (root / "LICENSES").mkdir(exist_ok=True)
            shutil.copyfile(REPO_ROOT / "LICENSES/CC-BY-4.0.txt", root / "LICENSES/CC-BY-4.0.txt")
            with (root / "LICENSES/CC-BY-4.0.txt").open("a", encoding="utf-8") as handle:
                handle.write("\nmodified\n")
            result = LicensingChecker(root).check_legal_texts()
            self.assertEqual(result.status, "FAIL")
            self.assertIn("CC-BY-4.0.txt", result.detail)

    def test_unclassified_scope_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write_manifest(root, _manifest())
            result = LicensingChecker(root).check_scope_coverage(files=["notes.txt"])
            self.assertEqual(result.status, "FAIL")
            self.assertIn("notes.txt", result.detail)

    def test_non_content_placeholder_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write_manifest(root, _manifest())
            result = LicensingChecker(root).check_scope_coverage(files=["datasets/.gitkeep"])
            self.assertEqual(result.status, "PASS")

    def test_overlapping_scopes_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data = _manifest()
            data["scopes"].append(
                {
                    "id": "overlapping-content",
                    "license": "CC0-1.0",
                    "status": "approved",
                    "include": ["docs/**/*.md"],
                    "exclude": [],
                }
            )
            _write_manifest(root, data)
            result = LicensingChecker(root).check_scope_coverage(files=["docs/lesson.md"])
            self.assertEqual(result.status, "FAIL")
            self.assertIn("overlapping scopes", result.detail)

    def test_repository_configuration_passes(self) -> None:
        results = LicensingChecker(REPO_ROOT).run()
        failures = [result for result in results if result.status == "FAIL"]
        self.assertEqual([], failures, [result.detail for result in failures])


if __name__ == "__main__":
    unittest.main()
