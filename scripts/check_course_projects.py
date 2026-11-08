"""Verify that every advertised capstone project has a complete specification.

Run from the repository root:

    python scripts/check_course_projects.py

The course index advertises twelve projects. This script fails if a project is
listed without a file, if a file is missing one of the required sections, if a
rubric's weights do not sum to 100, if the index and the specification disagree
about difficulty, or if a placeholder is left in the text.

It also checks that every assessment bank has a solutions file, so a bank cannot
ship without an answer key.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "docs" / "course" / "projects"
ASSESSMENTS = ROOT / "docs" / "course" / "assessments"

REQUIRED_SECTIONS = [
    "Problem statement and motivation",
    "Intended learning outcomes",
    "Difficulty and prerequisites",
    "Scope and out-of-scope features",
    "Dataset options, licences, and preparation",
    "Recommended baseline",
    "Milestones",
    "Repository or folder structure",
    "Detailed development tasks",
    "Testing and evaluation plan",
    "Metrics",
    "Expected deliverables",
    "Suggested extensions",
    "Common failure modes and troubleshooting",
    "Marking rubric",
    "Self-review checklist",
    "Report template",
    "Demonstration and presentation checklist",
]

ALLOWED_DIFFICULTY = {"Foundation", "Intermediate", "Advanced"}
PLACEHOLDERS = ("TBD", "TODO", "lorem ipsum", "[Project title]", "FIXME")

BANKS = {
    "quiz-bank.md": "solutions/quiz-bank.md",
    "conceptual.md": "solutions/conceptual.md",
    "code-reading.md": "solutions/code-reading.md",
    "debugging.md": "solutions/debugging.md",
    "scenarios.md": "solutions/scenarios.md",
    "lab-assessments.md": "solutions/lab-assessments.md",
    "evaluation-exercises.md": "solutions/evaluation-exercises.md",
    "revision.md": "solutions/revision.md",
}


def index_rows(text: str) -> list[dict]:
    rows = []
    for line in text.splitlines():
        match = re.match(r"\|\s*\[(P\d{2})\]\(([^)]+)\)\s*\|([^|]+)\|([^|]+)\|", line)
        if match:
            rows.append(
                {
                    "id": match.group(1),
                    "file": match.group(2),
                    "title": match.group(3).strip(),
                    "difficulty": match.group(4).strip(),
                }
            )
    return rows


def check_project(spec: Path, expected_difficulty: str | None) -> list[str]:
    problems: list[str] = []
    text = spec.read_text(encoding="utf-8")

    headings = re.findall(r"^## (\d{1,2})\. (.+)$", text, flags=re.MULTILINE)
    numbers = [int(number) for number, _ in headings]
    if numbers != list(range(1, 19)):
        problems.append(f"{spec.name}: section numbers are {numbers}, expected 1..18")
    titles = {int(number): title.strip() for number, title in headings}
    for index, required in enumerate(REQUIRED_SECTIONS, start=1):
        if required not in titles.get(index, ""):
            problems.append(f"{spec.name}: section {index} should be '{required}', got '{titles.get(index)}'")

    for field in ("**Difficulty**", "**Effort**", "**Hardware**", "**Prerequisites**"):
        if field not in text:
            problems.append(f"{spec.name}: missing snapshot field {field}")

    difficulty = re.search(r"\|\s*\*\*Difficulty\*\*\s*\|\s*([^|]+)\|", text)
    if not difficulty:
        problems.append(f"{spec.name}: difficulty not found")
    else:
        value = difficulty.group(1).strip()
        if value not in ALLOWED_DIFFICULTY:
            problems.append(f"{spec.name}: difficulty '{value}' not in {sorted(ALLOWED_DIFFICULTY)}")
        elif expected_difficulty and value != expected_difficulty:
            problems.append(
                f"{spec.name}: index says '{expected_difficulty}', specification says '{value}'"
            )

    rubric = text.split("## 15. Marking rubric", 1)
    if len(rubric) != 2:
        problems.append(f"{spec.name}: no marking rubric section")
    else:
        body = rubric[1].split("## 16.", 1)[0]
        weights = [int(match) for match in re.findall(r"\|\s*(\d{1,2})%\s*\|", body)]
        if not weights:
            problems.append(f"{spec.name}: rubric has no percentage weights")
        elif sum(weights) != 100:
            problems.append(f"{spec.name}: rubric weights sum to {sum(weights)}, expected 100")
        for level in ("4 - Excellent", "3 - Meets", "2 - Approaching", "1 - Not yet"):
            if level not in body:
                problems.append(f"{spec.name}: rubric missing level '{level}'")

    for link in ("index.md", "report-template.md", "completion-checklist.md"):
        if link not in text:
            problems.append(f"{spec.name}: does not link to {link}")

    lowered = text.lower()
    for token in PLACEHOLDERS:
        if token.lower() in lowered:
            problems.append(f"{spec.name}: contains placeholder '{token}'")

    if len(text.splitlines()) < 120:
        problems.append(f"{spec.name}: only {len(text.splitlines())} lines; specification looks thin")
    return problems


def check_assessments() -> list[str]:
    problems: list[str] = []
    for bank, solution in BANKS.items():
        bank_path = ASSESSMENTS / bank
        solution_path = ASSESSMENTS / solution
        if not bank_path.exists():
            problems.append(f"assessment bank missing: {bank}")
            continue
        if not solution_path.exists():
            problems.append(f"{bank}: no solutions file at {solution}")
            continue
        if solution not in bank_path.read_text(encoding="utf-8"):
            problems.append(f"{bank}: does not link to its solutions file")
        if len(solution_path.read_text(encoding="utf-8").splitlines()) < 30:
            problems.append(f"{solution}: solutions file looks empty")
    return problems


def main() -> int:
    problems: list[str] = []
    index_path = PROJECTS / "index.md"
    if not index_path.exists():
        print("missing docs/course/projects/index.md")
        return 1

    rows = index_rows(index_path.read_text(encoding="utf-8"))
    if len(rows) != 12:
        problems.append(f"index advertises {len(rows)} projects, expected 12")

    seen: set[str] = set()
    for row in rows:
        if row["id"] in seen:
            problems.append(f"index lists {row['id']} twice")
        seen.add(row["id"])
        spec = PROJECTS / row["file"]
        if not spec.exists():
            problems.append(f"{row['id']}: advertised but missing {row['file']}")
            continue
        problems.extend(check_project(spec, row["difficulty"]))

    for spec in sorted(PROJECTS.glob("p*.md")):
        if spec.name not in {row["file"] for row in rows}:
            problems.append(f"{spec.name} exists but is not advertised in index.md")

    for support in ("report-template.md", "completion-checklist.md"):
        if not (PROJECTS / support).exists():
            problems.append(f"missing shared project page: {support}")

    problems.extend(check_assessments())

    if problems:
        print(f"{len(problems)} problem(s):")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    specs = sum(len(check_project(PROJECTS / row["file"], row["difficulty"])) == 0 for row in rows)
    print(f"ok: {len(rows)} projects, {specs} complete specifications, "
          f"{len(BANKS)} assessment banks with solutions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
