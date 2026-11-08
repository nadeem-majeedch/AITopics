"""Generation: prompt assembly, structured-output parsing, grounding, abstention.

The generation layer owns the policy decisions that a model cannot be trusted to
make on its own:

* refuse before calling the model when retrieval found nothing good enough;
* quarantine instruction-like evidence before it reaches the prompt;
* redact personal identifiers before the prompt is built;
* parse structured output, and fail closed when citations do not resolve;
* report a conflict when cited passages disagree rather than averaging them.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Sequence

from .citations import Citation, build_registry, strip_invalid_markers, validate
from .documents import Chunk, tokenize
from .guardrails import redact, scan_for_injection
from .model_client import ABSTAIN_TEXT, SYSTEM_PROMPT, ModelClient, content_words

NUMBER_WITH_UNIT = re.compile(r"(\d[\d,]*)\s*(days?|hours?|percent|credits?|weeks?)", re.IGNORECASE)


class OutputParseError(ValueError):
    """Raised when a model reply is not the structured object we asked for."""


@dataclass
class GenerationConfig:
    k: int = 4
    min_score: float = 0.12
    require_citations: bool = True
    require_lexical_overlap: bool = True
    max_answer_chars: int = 900
    disclose_conflicts: bool = True


@dataclass
class Answer:
    """Everything a caller needs to render, evaluate, or debug one turn."""

    text: str
    citations: list[Citation] = field(default_factory=list)
    abstained: bool = False
    conflict: bool = False
    conflict_note: str = ""
    dropped_citations: list[int] = field(default_factory=list)
    quarantined_chunks: list[str] = field(default_factory=list)
    retrieved: int = 0
    top_score: float = 0.0
    model: str = ""

    def as_dict(self) -> dict:
        return {
            "text": self.text,
            "citations": [citation.as_dict() for citation in self.citations],
            "abstained": self.abstained,
            "conflict": self.conflict,
            "conflict_note": self.conflict_note,
            "dropped_citations": self.dropped_citations,
            "quarantined_chunks": self.quarantined_chunks,
            "retrieved": self.retrieved,
            "top_score": round(self.top_score, 6),
            "model": self.model,
        }


def format_evidence(chunks: Sequence[Chunk]) -> str:
    """Numbered evidence block. Text is redacted before it enters the prompt."""
    lines: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        lines.append(f"[{index}] ({chunk.title} - {chunk.section})")
        lines.append(redact(chunk.text).strip())
        lines.append("")
    return "\n".join(lines).strip()


def build_messages(question: str, chunks: Sequence[Chunk], history: Sequence[dict[str, str]] | None = None) -> list[dict[str, str]]:
    """Assemble the system prompt, optional history, and the current turn."""
    evidence = format_evidence(chunks)
    user_turn = (
        "EVIDENCE:\n"
        f"{evidence}\n\n"
        f"QUESTION: {question}\n\n"
        "Reply with the JSON object described in the system prompt."
    )
    messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in history or []:
        messages.append(dict(turn))
    messages.append({"role": "user", "content": user_turn})
    return messages


def parse_model_output(raw: str) -> dict:
    """Parse the JSON object from a model reply, tolerating surrounding prose."""
    if not isinstance(raw, str) or not raw.strip():
        raise OutputParseError("empty model reply")
    text = raw.strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise OutputParseError("model reply contains no JSON object") from None
        try:
            payload = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise OutputParseError(f"model reply is not valid JSON: {exc}") from exc

    if not isinstance(payload, dict) or "answer" not in payload:
        raise OutputParseError("model reply is missing the 'answer' field")

    answer = payload.get("answer")
    if not isinstance(answer, str):
        raise OutputParseError("'answer' must be a string")

    raw_citations = payload.get("citations") or []
    if not isinstance(raw_citations, list):
        raise OutputParseError("'citations' must be a list")
    citations: list[int] = []
    for item in raw_citations:
        try:
            citations.append(int(item))
        except (TypeError, ValueError):
            raise OutputParseError(f"citation {item!r} is not an integer") from None

    return {"answer": answer, "citations": citations, "confident": bool(payload.get("confident", True))}


def detect_conflict(chunks: Sequence[Chunk], question: str) -> tuple[bool, str]:
    """Flag disagreement between cited passages about the same quantity.

    Only chunks that share content words with the question are compared, and only
    when the same unit carries different values in different documents. This is a
    narrow heuristic: it catches two policies that state different deadlines, and
    it does not attempt general contradiction detection.
    """
    asked = content_words(question)
    values: dict[str, dict[str, tuple[str, str]]] = {}

    for chunk in chunks:
        for sentence in re.split(r"(?<=[.!?])\s+", chunk.text):
            if not (asked & content_words(sentence)):
                continue
            for match in NUMBER_WITH_UNIT.finditer(sentence):
                value = match.group(1).replace(",", "")
                unit = match.group(2).lower().rstrip("s")
                per_unit = values.setdefault(unit, {})
                if chunk.doc_id not in per_unit:
                    per_unit[chunk.doc_id] = (value, chunk.doc_id)
                elif per_unit[chunk.doc_id][0] != value:
                    per_unit[f"{chunk.doc_id}#{chunk.chunk_id}"] = (value, chunk.doc_id)

    for unit, per_doc in values.items():
        distinct = {value for value, _ in per_doc.values()}
        documents = {doc_id for _, doc_id in per_doc.values()}
        if len(distinct) > 1 and len(documents) > 1:
            detail = ", ".join(f"{value} {unit}(s) in {doc_id}" for value, doc_id in per_doc.values())
            return True, f"Sources disagree about the {unit}: {detail}."

    return False, ""


def generate(
    question: str,
    chunks: Sequence[Chunk],
    scores: Sequence[float],
    client: ModelClient,
    config: GenerationConfig | None = None,
    history: Sequence[dict[str, str]] | None = None,
) -> Answer:
    """Run one grounded generation turn over already-retrieved chunks."""
    config = config or GenerationConfig()
    if not chunks:
        return Answer(text=ABSTAIN_TEXT, abstained=True, model=client.name)

    top_score = float(max(scores)) if scores else 0.0
    if top_score < config.min_score:
        return Answer(
            text=ABSTAIN_TEXT,
            abstained=True,
            retrieved=len(chunks),
            top_score=top_score,
            model=client.name,
        )

    if config.require_lexical_overlap:
        asked = content_words(question)
        supported = bool(asked) and any(asked & content_words(chunk.text) for chunk in chunks)
        if not supported:
            # No retrieved passage shares a content term with the question. A
            # similarity score alone is not evidence; refuse before the model runs.
            return Answer(
                text=ABSTAIN_TEXT,
                abstained=True,
                retrieved=len(chunks),
                top_score=top_score,
                model=client.name,
            )

    usable: list[Chunk] = []
    quarantined: list[str] = []
    for chunk in chunks:
        if scan_for_injection(chunk.text).flagged:
            quarantined.append(chunk.chunk_id)
        else:
            usable.append(chunk)

    if not usable:
        return Answer(
            text=ABSTAIN_TEXT,
            abstained=True,
            quarantined_chunks=quarantined,
            retrieved=len(chunks),
            top_score=top_score,
            model=client.name,
        )

    registry = build_registry(usable, scores[: len(usable)])
    messages = build_messages(question, usable, history)
    raw = client.complete(messages)

    try:
        payload = parse_model_output(raw)
    except OutputParseError:
        return Answer(
            text=ABSTAIN_TEXT,
            abstained=True,
            quarantined_chunks=quarantined,
            retrieved=len(chunks),
            top_score=top_score,
            model=client.name,
        )

    answer_text = payload["answer"].strip() or ABSTAIN_TEXT
    looks_like_refusal = answer_text.lower().startswith(("i do not", "i don't", "the documents do not"))
    if looks_like_refusal:
        return Answer(
            text=answer_text,
            abstained=True,
            quarantined_chunks=quarantined,
            retrieved=len(chunks),
            top_score=top_score,
            model=client.name,
        )

    outcome = validate(payload["citations"], answer_text, registry)
    dropped = outcome.invalid_numbers + outcome.fabricated_in_text

    if config.require_citations and not outcome.valid:
        return Answer(
            text=ABSTAIN_TEXT,
            abstained=True,
            dropped_citations=dropped,
            quarantined_chunks=quarantined,
            retrieved=len(chunks),
            top_score=top_score,
            model=client.name,
        )

    if outcome.fabricated:
        # Fail closed: an answer that invented a source is not shown.
        return Answer(
            text=ABSTAIN_TEXT,
            abstained=True,
            dropped_citations=dropped,
            quarantined_chunks=quarantined,
            retrieved=len(chunks),
            top_score=top_score,
            model=client.name,
        )

    cleaned = strip_invalid_markers(answer_text, registry)[: config.max_answer_chars].strip()
    conflict, note = (False, "")
    if config.disclose_conflicts:
        # Check the whole retrieved set, not only the chunk the model quoted:
        # a disagreement the user needs to see can sit in a passage the model
        # chose not to quote.
        conflict, note = detect_conflict(list(usable), question)

    return Answer(
        text=cleaned,
        citations=outcome.valid,
        abstained=False,
        conflict=conflict,
        conflict_note=note,
        quarantined_chunks=quarantined,
        retrieved=len(chunks),
        top_score=top_score,
        model=client.name,
    )


def render_answer(answer: Answer) -> str:
    """Plain-text rendering for a terminal, used by several projects."""
    lines = [answer.text]
    if answer.conflict and answer.conflict_note:
        lines.append("")
        lines.append(f"Note: {answer.conflict_note}")
    if answer.citations:
        lines.append("")
        lines.append("Sources:")
        lines.extend(f"  {citation.display()}" for citation in answer.citations)
    elif answer.abstained:
        lines.append("")
        lines.append("No sources cited: the documents do not support an answer.")
    return "\n".join(lines)
