"""Tests that the capstone and assessment pages are complete and consistent.

The course advertises twelve projects. A page that is listed but missing a
section, a rubric whose weights do not sum to 100, or an assessment bank without
an answer key is a content bug, not a styling issue. This test runs the checker
that the documentation build does not cover.

Run from the repository root:

    python -m unittest tests.test_course_projects -v
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECTS = REPO_ROOT / "docs" / "course" / "projects"
ASSESSMENTS = REPO_ROOT / "docs" / "course" / "assessments"
SUBMISSION = REPO_ROOT / "templates" / "capstone-submission"


class CourseContentTests(unittest.TestCase):
    def test_checker_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "check_course_projects.py")],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("12 projects", result.stdout)

    def test_every_project_file_exists_and_is_linked(self) -> None:
        index = (PROJECTS / "index.md").read_text(encoding="utf-8")
        specs = sorted(PROJECTS.glob("p*.md"))
        self.assertEqual(len(specs), 12)
        for spec in specs:
            self.assertIn(spec.name, index, f"{spec.name} is not linked from the index")

    def test_assessment_banks_have_solutions(self) -> None:
        banks = [path for path in ASSESSMENTS.glob("*.md") if path.name != "index.md"]
        self.assertGreaterEqual(len(banks), 8)
        for bank in banks:
            solution = ASSESSMENTS / "solutions" / bank.name
            self.assertTrue(solution.exists(), f"{bank.name} has no solutions file")
            self.assertGreater(len(solution.read_text(encoding="utf-8").splitlines()), 30)

    def test_submission_package_is_complete(self) -> None:
        required = {
            "project-scope.md": ["## Problem and decision", "## Objectives", "## Risk register"],
            "dataset-card.md": ["## Origin and provenance", "## Size and labels", "## Splits and leakage"],
            "model-card.md": ["## Intended use", "## Architecture", "## Training", "## Evaluation", "## Limitations"],
            "evaluation-report.md": ["## Frozen test declaration", "## Headline results", "## Qualitative evaluation and failure cases", "## Interpretation"],
            "threat-and-responsible-use-review.md": ["## Threat table", "## Privacy", "## Security boundaries"],
            "reproducibility.md": ["## Environment", "## Seeds and determinism", "## Commands"],
            "README.md": ["## Quick start", "## Limitations"],
            "release-notes.md": ["## Release decision", "## Rollback"],
            "final-report.md": ["## 1. Summary", "## 8. Error analysis", "## 11. Reproducibility"],
        }
        for name, headings in required.items():
            path = SUBMISSION / name
            self.assertTrue(path.exists(), f"missing submission file: {name}")
            text = path.read_text(encoding="utf-8")
            self.assertIn("[replace", text, f"{name} has no fill-in prompts")
            for heading in headings:
                self.assertIn(heading, text, f"{name} is missing {heading!r}")

        header = (SUBMISSION / "experiments.csv").read_text(encoding="utf-8").splitlines()[0]
        for column in (
            "experiment_id",
            "seed",
            "dataset_split",
            "model",
            "metrics",
            "runtime_seconds",
            "decision",
            "notes",
        ):
            self.assertIn(column, header, f"experiments.csv is missing {column!r}")

    def test_submission_package_is_documented(self) -> None:
        guide = (PROJECTS / "submission-package.md").read_text(encoding="utf-8")
        for name in (
            "project-scope.md",
            "dataset-card.md",
            "experiments.csv",
            "model-card.md",
            "evaluation-report.md",
            "threat-and-responsible-use-review.md",
            "reproducibility.md",
            "README.md",
            "release-notes.md",
            "final-report.md",
        ):
            self.assertIn(name, guide, f"the package guide does not mention {name}")
        self.assertIn("templates/capstone-submission/", guide)

    def test_no_solution_claims_grading(self) -> None:
        for path in (ASSESSMENTS / "solutions").glob("*.md"):
            text = path.read_text(encoding="utf-8").lower()
            self.assertNotIn("you have been graded", text)
            self.assertNotIn("your grade is", text)


if __name__ == "__main__":
    unittest.main()
