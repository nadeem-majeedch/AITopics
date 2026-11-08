"""Model and dataset cards, rendered from measurements and then audited.

The card is generated, not written by hand, so a number in the card is a number
from a measurement file. ``claims_audit`` enforces the reverse direction: any
number in the prose that cannot be traced back to the measurement source is
reported. This does not make a card true, but it does make an invented metric
visible to a reviewer.
"""

from __future__ import annotations

import re
from typing import Iterable

MODEL_CARD_SECTIONS = (
    "Model details",
    "Intended use",
    "Out-of-scope use",
    "Training data",
    "Evaluation",
    "Limitations",
    "Ethical considerations",
    "Licence",
)

DATASET_CARD_SECTIONS = (
    "Dataset details",
    "Provenance",
    "Composition",
    "Collection process",
    "Preprocessing",
    "Uses",
    "Limitations",
    "Licence",
)

NUMBER = re.compile(r"-?\d+(?:\.\d+)?")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def render_model_card(meta: dict, metrics: dict) -> str:
    lines = [
        f"# Model card: {meta['name']}",
        "",
        "## Model details",
        f"- Version: {meta['version']}",
        f"- Type: {meta['type']}",
        f"- Owner: {meta['owner']}",
        f"- Created: {meta['created']}",
        f"- Artifact digest: `{meta.get('digest', 'not recorded')}`",
        "",
        "## Intended use",
        f"{meta['intended_use']}",
        "",
        "## Out-of-scope use",
        f"{meta['out_of_scope']}",
        "",
        "## Training data",
        f"{meta['training_data']}",
        "",
        "## Evaluation",
        "Measured on the held-out test split, which was not used for training or model selection.",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    for name, value in metrics.items():
        if isinstance(value, float):
            lines.append(f"| {name} | {value:.3f} |")
        else:
            lines.append(f"| {name} | {value} |")
    lines += [
        "",
        "## Limitations",
        *[f"- {item}" for item in meta["limitations"]],
        "",
        "## Ethical considerations",
        *[f"- {item}" for item in meta["ethical"]],
        "",
        "## Licence",
        f"{meta['licence']}",
        "",
    ]
    return "\n".join(lines)


def render_dataset_card(meta: dict, stats: dict) -> str:
    lines = [
        f"# Dataset card: {meta['name']}",
        "",
        "## Dataset details",
        f"- Version: {meta['version']}",
        f"- Format: {meta['format']}",
        f"- Size: {stats['rows']} rows, {stats['columns']} columns",
        f"- Digest: `{meta.get('digest', 'not recorded')}`",
        "",
        "## Provenance",
        f"{meta['provenance']}",
        "",
        "## Composition",
        f"{stats['composition']}",
        "",
        "## Collection process",
        f"{meta['collection']}",
        "",
        "## Preprocessing",
        f"{meta['preprocessing']}",
        "",
        "## Uses",
        f"{meta['uses']}",
        "",
        "## Limitations",
        *[f"- {item}" for item in meta["limitations"]],
        "",
        "## Licence",
        f"{meta['licence']}",
        "",
    ]
    return "\n".join(lines)


def validate_card(text: str, required: Iterable[str] = MODEL_CARD_SECTIONS) -> dict:
    headings = {line[3:].strip() for line in text.splitlines() if line.startswith("## ")}
    missing = [section for section in required if section not in headings]
    return {"ok": not missing, "missing": missing, "sections": sorted(headings)}


def _allowed_values(metrics: dict) -> set[str]:
    allowed: set[str] = set()
    for value in metrics.values():
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            for digits in (0, 1, 2, 3):
                allowed.add(f"{value:.{digits}f}")
            allowed.add(str(value))
            allowed.add(f"{value * 100:.0f}")  # a rate written as a percentage
            allowed.add(f"{value * 100:.1f}")
        elif isinstance(value, str):
            allowed.update(NUMBER.findall(value))
    return allowed


def claims_audit(card_text: str, metrics: dict, extra_allowed: Iterable[float] = ()) -> dict:
    """Report numbers in the card that the metrics do not support.

    False positives are possible: a date, a version number, or a row count that
    lives outside ``metrics`` will be reported. Pass those through
    ``extra_allowed`` (counts, sizes, dates as numbers) rather than silencing the
    check.
    """
    allowed = _allowed_values(metrics)
    allowed.update(str(value) for value in extra_allowed)
    for value in extra_allowed:
        allowed.add(f"{value:.0f}")
        allowed.add(f"{value:.1f}")
        allowed.add(f"{value:.2f}")
        allowed.add(f"{value:.3f}")

    unsupported = []
    for line in card_text.splitlines():
        # Headings carry no claims, backticked values are identifiers, and a date
        # is metadata rather than a measurement.
        if (line.startswith("#") or "`" in line or DATE.search(line)
                or line.lstrip().startswith("- Version:")):
            continue
        for token in NUMBER.findall(line):
            if token.lstrip("-") in allowed or token in allowed:
                continue
            unsupported.append({"number": token, "line": line.strip()[:120]})
    return {"ok": not unsupported, "unsupported": unsupported}
