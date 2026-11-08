"""End-to-end tests for scripts/check_vision_manifests.py.

The complete P06 corpus is generated and git-ignored, so these tests use a tiny
synthetic manifest-managed fixture. They verify that the script distinguishes
PASS, FAIL, and SKIPPED, and that skipped data is never reported as a successful
integrity check.

Run from the repository root:

    python -m unittest tests.test_vision_manifests -v
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "check_vision_manifests.py"
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fixtures.vision_manifest import build_manifest_fixture  # noqa: E402


class ManifestCheckerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.data = Path(self._tmp.name)
        self.dataset = build_manifest_fixture(self.data)
        self.manifest_path = self.dataset / "manifest.json"

    def _run(self, *args: str, data_dir: Path | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--data-dir",
                str(data_dir or self.data),
                *args,
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )

    def _payload(self) -> dict:
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def _write_payload(self, payload: dict) -> None:
        self.manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def test_valid_fixture_passes(self) -> None:
        result = self._run("--require-datasets")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS: objects_p06_fixture", result.stdout)
        self.assertIn("RESULT: PASS", result.stdout)
        self.assertIn("0 failed", result.stdout)

    def test_no_data_is_skipped_not_passed(self) -> None:
        empty = Path(self._tmp.name) / "empty"
        empty.mkdir()
        result = self._run(data_dir=empty)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("RESULT: SKIPPED", result.stdout)
        self.assertNotIn("RESULT: PASS", result.stdout)

    def test_required_missing_data_is_status_2(self) -> None:
        empty = Path(self._tmp.name) / "empty"
        empty.mkdir()
        result = self._run("--require-datasets", data_dir=empty)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("RESULT: SKIPPED (datasets required", result.stdout)

    def test_missing_manifest_fails(self) -> None:
        self.manifest_path.unlink()
        result = self._run()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("manifest_missing", result.stdout)
        self.assertIn("RESULT: FAIL", result.stdout)

    def test_missing_image_fails(self) -> None:
        (self.dataset / "train" / "00000.png").unlink()
        result = self._run()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("missing_file", result.stdout)

    def test_corrupted_file_fails(self) -> None:
        (self.dataset / "train" / "00000.png").write_bytes(b"not a png")
        result = self._run()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("modified_file", result.stdout)

    def test_invalid_label_fails(self) -> None:
        payload = self._payload()
        payload["files"]["train/00000.png"]["label"] = 99
        self._write_payload(payload)
        result = self._run()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("bad_label", result.stdout)

    def test_duplicate_within_split_is_a_warning_but_passes(self) -> None:
        source = self.dataset / "train" / "00000.png"
        target = self.dataset / "train" / "00001.png"
        shutil.copyfile(source, target)
        payload = self._payload()
        payload["files"]["train/00001.png"]["sha256"] = payload["files"]["train/00000.png"]["sha256"]
        payload["files"]["train/00001.png"]["bytes"] = payload["files"]["train/00000.png"]["bytes"]
        self._write_payload(payload)

        result = self._run()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("RESULT: PASS", result.stdout)
        self.assertIn("duplicate_content", result.stdout)
        self.assertIn("warning(s) accepted", result.stdout)

    def test_source_leakage_fails(self) -> None:
        source = self.dataset / "train" / "00000.png"
        leaked = self.dataset / "test" / "00002.png"
        shutil.copyfile(source, leaked)
        payload = self._payload()
        entry = dict(payload["files"]["train/00000.png"])
        entry["split"] = "test"
        payload["files"]["test/00002.png"] = entry
        payload["splits"]["test"] += 1
        self._write_payload(payload)

        result = self._run()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("split_overlap", result.stdout)
        self.assertIn("RESULT: FAIL", result.stdout)


if __name__ == "__main__":
    unittest.main()
