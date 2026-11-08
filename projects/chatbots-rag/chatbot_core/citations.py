"""Citation handling: numbering, validation, and fabrication detection.

A citation is a promise that a claim came from a specific retrieved chunk. The
guard here is the only thing standing between that promise and a plausible-looking
invention, so it **fails closed**: when an answer cites something that was not
retrieved, the answer is replaced with a refusal rather than shown.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Sequence

from .documents import Chunk

BRACKET_CITATION = re.compile(r"\[(\d{1,3})\]")


@dataclass(frozen=True)
class Citation:
    number: int
    chunk_id: str
    title: str
    section: str
    source: str
    score: float = 0.0

    def as_dict(self) -> dict:
        return {
            "number": self.number,
            "chunk_id": self.chunk_id,
            "title": self.title,
            "section": self.section,
            "source": self.source,
            "score": round(self.score, 6),
        }

    def display(self) -> str:
        return f"[{self.number}] {self.title} - {self.section} ({self.source})"


@dataclass
class ValidationOutcome:
    """Result of checking a model's claimed citations."""

    valid: list[Citation] = field(default_factory=list)
    invalid_numbers: list[int] = field(default_factory=list)
    fabricated_in_text: list[int] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.valid) and not self.invalid_numbers and not self.fabricated_in_text

    @property
    def fabricated(self) -> bool:
        return bool(self.invalid_numbers or self.fabricated_in_text)


def build_registry(chunks: Sequence[Chunk], scores: Sequence[float] | None = None) -> dict[int, Citation]:
    """Number retrieved chunks 1..n, matching the prompt's evidence numbering."""
    registry: dict[int, Citation] = {}
    for index, chunk in enumerate(chunks, start=1):
        score = float(scores[index - 1]) if scores and index - 1 < len(scores) else 0.0
        registry[index] = Citation(
            number=index,
            chunk_id=chunk.chunk_id,
            title=chunk.title,
            section=chunk.section,
            source=chunk.source,
            score=score,
        )
    return registry


def validate(claimed: Sequence[int], answer_text: str, registry: dict[int, Citation]) -> ValidationOutcome:
    """Check claimed numbers and any inline ``[n]`` markers in the answer text.

    ``claimed`` comes from the structured output; inline markers are also scanned
    because a model can ignore the schema and write ``[99]`` in prose.
    """
    outcome = ValidationOutcome()
    for number in claimed:
        if number in registry:
            if registry[number] not in outcome.valid:
                outcome.valid.append(registry[number])
        else:
            outcome.invalid_numbers.append(int(number))

    for match in BRACKET_CITATION.finditer(answer_text or ""):
        number = int(match.group(1))
        if number not in registry:
            outcome.fabricated_in_text.append(number)

    return outcome


def strip_invalid_markers(answer_text: str, registry: dict[int, Citation]) -> str:
    """Remove inline citation markers that do not resolve to a retrieved chunk."""

    def replace(match: re.Match[str]) -> str:
        return match.group(0) if int(match.group(1)) in registry else ""

    return re.sub(r"\s{2,}", " ", BRACKET_CITATION.sub(replace, answer_text)).strip()
