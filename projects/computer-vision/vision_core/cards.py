"""Model card and dataset card templates.

A model card is a one-page statement of what a model is for, what it was trained
on, how it was measured, and where it fails. It is deliberately short: a card
nobody reads provides no accountability.

The templates are plain Markdown with ``{{placeholder}}`` fields, filled by
:func:`render`. Nothing here is generated automatically from the model, because
"how it fails" and "who it should not be used on" are judgements a person must
write down.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

MODEL_CARD_TEMPLATE = """# Model card: {{model_name}}

| Field | Value |
| --- | --- |
| Version | {{version}} |
| Date | {{date}} |
| Author | {{author}} |
| Task | {{task}} |
| Architecture | {{architecture}} |
| Parameters | {{parameters}} |
| Input | {{input_spec}} |
| Output | {{output_spec}} |
| Licence | {{licence}} |

## Intended use

{{intended_use}}

## Out of scope

{{out_of_scope}}

## Training data

{{training_data}}

## Evaluation

| Metric | Value | Dataset | Notes |
| --- | --- | --- | --- |
{{metrics_table}}

## Failure modes observed

{{failure_modes}}

## Robustness

{{robustness}}

## Privacy and safety

{{safety}}

## Limitations

{{limitations}}

## Reproduction

```
{{reproduce_command}}
```

## Review

{{review}}
"""

DATASET_CARD_TEMPLATE = """# Dataset card: {{name}}

| Field | Value |
| --- | --- |
| Version | {{version}} |
| Created | {{date}} |
| Source | {{source}} |
| Licence | {{licence}} |
| Attribution | {{attribution}} |
| Size | {{size}} |
| Classes | {{classes}} |
| Splits | {{splits}} |

## How it was produced

{{provenance}}

## Annotation process

{{annotation}}

## Known issues

{{issues}}

## Personal data

{{personal_data}}

## Intended use

{{intended_use}}
"""


def render(template: str, **fields: object) -> str:
    """Substitute ``{{key}}`` placeholders; leave unknown ones visible.

    Leaving an unfilled field as ``{{key}}`` rather than blanking it is
    intentional: a card with an obvious hole is better than a card that looks
    complete and is not.
    """
    out = template
    for key, value in fields.items():
        out = out.replace("{{" + key + "}}", str(value))
    return out


def metrics_table(rows: Iterable[dict]) -> str:
    """Build the metric table body from ``{name, value, dataset, note}`` rows."""
    lines = []
    for row in rows:
        lines.append(f"| {row.get('name', '')} | {row.get('value', '')} | {row.get('dataset', '')} | {row.get('note', '')} |")
    return "\n".join(lines) if lines else "| _none recorded_ | | | |"


def write_model_card(path: str | Path, **fields: object) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if "metrics_table" in fields and not isinstance(fields["metrics_table"], str):
        fields["metrics_table"] = metrics_table(fields["metrics_table"])  # type: ignore[arg-type]
    path.write_text(render(MODEL_CARD_TEMPLATE, **fields), encoding="utf-8")
    return path


def write_dataset_card(path: str | Path, **fields: object) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(DATASET_CARD_TEMPLATE, **fields), encoding="utf-8")
    return path


def card_from_json(path: str | Path) -> dict:
    """Load a card's fields from JSON, for labs that store measurements."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def check_card(path: str | Path) -> dict:
    """Report which required fields are still unfilled.

    Used by the labs' selftests and by the assessment: a submitted card with
    ``{{limitations}}`` still in it has not been written.
    """
    text = Path(path).read_text(encoding="utf-8")
    required = ("intended_use", "out_of_scope", "training_data", "failure_modes", "limitations", "safety")
    missing = [key for key in required if "{{" + key + "}}" in text]
    return {"path": str(path), "missing": missing, "complete": not missing, "chars": len(text)}
