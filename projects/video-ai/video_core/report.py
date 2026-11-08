"""Report plumbing: JSON files, aligned tables, and Markdown cards.

Labs print numbers and also write them to JSON, so a student can diff two runs and so the
docs can quote measured values instead of remembered ones. Nothing here computes anything.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np


def plain(value):
    """JSON-friendly version of numpy scalars, arrays, paths, and anything else odd."""
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, (set, tuple)):
        return [plain(v) for v in value]
    return value


def write_json(path: str | Path, payload: dict) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=plain) + "\n", encoding="utf-8")
    return path


def read_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rule(title: str) -> None:
    print(f"\n=== {title}")


def table(rows: Sequence[dict], columns: Sequence[str], *, indent: str = "  ") -> None:
    """Print rows as a left-aligned table. Column widths adapt to the content."""
    if not rows:
        print(f"{indent}(no rows)")
        return
    widths = {c: max(len(c), *(len(_cell(r.get(c))) for r in rows)) for c in columns}
    header = "  ".join(f"{c:<{widths[c]}}" for c in columns)
    print(indent + header)
    print(indent + "-" * len(header))
    for row in rows:
        print(indent + "  ".join(f"{_cell(row.get(c)):<{widths[c]}}" for c in columns))


def _cell(value) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def markdown_table(rows: Sequence[dict], columns: Sequence[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |",
             "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(_cell(row.get(c)) for c in columns) + " |")
    return "\n".join(lines)


def bullet_list(items: Iterable[str], *, marker: str = "-") -> str:
    return "\n".join(f"{marker} {item}" for item in items)


def check(name: str, passed: bool, detail: str = "") -> bool:
    """A visible pass/fail line. Labs return their exit status from the AND of these."""
    mark = "PASS" if passed else "FAIL"
    suffix = f"  ({detail})" if detail else ""
    print(f"  [{mark}] {name}{suffix}")
    return passed


def summary_line(title: str, values: dict) -> str:
    body = "  ".join(f"{k}={plain(v)}" for k, v in values.items())
    return f"{title}: {body}"
