"""A tiny report writer.

Every lab writes two artifacts: a Markdown report a human reads, and a JSON file a
script reads. Both come from the same numbers, which is the only way the report
and the dashboard can disagree without anyone noticing.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import metrics


class Report:
    def __init__(self, title: str, subtitle: str = ""):
        self.title = title
        self.subtitle = subtitle
        self.parts: list[str] = []

    def text(self, body: str) -> "Report":
        self.parts.append(body.strip())
        return self

    def heading(self, name: str, level: int = 2) -> "Report":
        self.parts.append(f"{'#' * level} {name}")
        return self

    def bullets(self, items: list[str]) -> "Report":
        self.parts.append("\n".join(f"- {item}" for item in items))
        return self

    def table(self, rows: list[dict], columns: list[str]) -> "Report":
        self.parts.append(metrics.table(rows, columns))
        return self

    def code(self, body: str, language: str = "text") -> "Report":
        self.parts.append(f"```{language}\n{body.strip()}\n```")
        return self

    def render(self, footer: str | None = None) -> str:
        lines = [f"# {self.title}", ""]
        if self.subtitle:
            lines += [self.subtitle.strip(), ""]
        lines += ["\n\n".join(self.parts), ""]
        if footer:
            lines += ["---", "", footer.strip(), ""]
        return "\n".join(lines)

    def write(self, directory: Path, name: str = "report.md", footer: str | None = None) -> Path:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / name
        path.write_text(self.render(footer), encoding="utf-8")
        return path


def write_json(directory: Path, name: str, payload) -> Path:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    return path


def measured_footer(environment: dict, note: str = "") -> str:
    """The provenance line every report carries."""
    parts = [
        f"Measured on {environment.get('platform', 'unknown platform')} with "
        f"Python {environment.get('python', '?')}, NumPy {environment.get('numpy', '?')}, "
        f"scikit-learn {environment.get('sklearn', '?')}."
    ]
    if note:
        parts.append(note)
    parts.append(
        "Numbers are from this run on this machine. Latency varies; accuracy and counts "
        "reproduce from the recorded seed and the data manifest."
    )
    return " ".join(parts)
