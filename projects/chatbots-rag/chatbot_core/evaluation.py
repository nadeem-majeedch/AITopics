"""Evaluation: a fixed question set, documented metrics, and a JSON report.

The point of this module is to replace "this answer looks better" with numbers
that another student can reproduce. It measures retrieval and generation
separately, because they fail in different ways:

* retrieval fails when the gold document is never returned (``hit_at_k``);
* generation fails when the right document was returned and the answer misstates
  it, or cites nothing (``answer_correct``, ``citation_precision``);
* refusal behaviour is scored on its own, because a system that answers
  everything looks good on correctness and terrible on ``abstention_correct``.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from .chatbot import RAGChatbot
from .generation import Answer


@dataclass
class QuestionScore:
    question_id: str
    question: str
    answerable: bool
    abstained: bool
    answer_correct: bool
    citation_precision: float | None
    citation_recall: float | None
    hit_at_k: bool
    cited_doc_ids: list[str] = field(default_factory=list)
    retrieved_doc_ids: list[str] = field(default_factory=list)
    latency_ms: float = 0.0

    def as_dict(self) -> dict:
        return {
            "id": self.question_id,
            "question": self.question,
            "answerable": self.answerable,
            "abstained": self.abstained,
            "answer_correct": self.answer_correct,
            "citation_precision": None if self.citation_precision is None else round(self.citation_precision, 4),
            "citation_recall": None if self.citation_recall is None else round(self.citation_recall, 4),
            "hit_at_k": self.hit_at_k,
            "cited_doc_ids": self.cited_doc_ids,
            "retrieved_doc_ids": self.retrieved_doc_ids,
            "latency_ms": round(self.latency_ms, 3),
        }


def load_questions(path: Path | str) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("question file must contain a JSON list")
    for item in data:
        for key in ("id", "question", "answerable", "gold_doc_ids", "must_contain"):
            if key not in item:
                raise ValueError(f"question {item.get('id', '?')} is missing {key!r}")
    return data


def score_answer(
    item: dict,
    answer: Answer,
    retrieved_doc_ids: Sequence[str],
    latency_ms: float,
) -> QuestionScore:
    """Score one answer against one gold item. Refusals are scored, not skipped."""
    text = answer.text.lower()
    cited = [citation.chunk_id for citation in answer.citations]
    cited_docs = sorted({citation.source.rsplit(".", 1)[0] for citation in answer.citations})
    gold = list(item["gold_doc_ids"])

    if item["answerable"]:
        supported = all(str(needle).lower() in text for needle in item["must_contain"])
        answer_correct = supported and not answer.abstained
    else:
        answer_correct = answer.abstained

    if cited_docs:
        overlap = [doc for doc in cited_docs if doc in gold]
        precision = len(overlap) / len(cited_docs)
        recall = len(overlap) / len(gold) if gold else None
    else:
        precision = None
        recall = 0.0 if gold else None

    hit = any(doc in gold for doc in retrieved_doc_ids) if gold else True

    return QuestionScore(
        question_id=str(item["id"]),
        question=str(item["question"]),
        answerable=bool(item["answerable"]),
        abstained=answer.abstained,
        answer_correct=answer_correct,
        citation_precision=precision,
        citation_recall=recall,
        hit_at_k=hit,
        cited_doc_ids=cited_docs,
        retrieved_doc_ids=list(retrieved_doc_ids),
        latency_ms=latency_ms,
    )


def _mean(values: Iterable[float | None]) -> float | None:
    cleaned = [value for value in values if value is not None]
    return round(sum(cleaned) / len(cleaned), 4) if cleaned else None


def evaluate(bot: RAGChatbot, questions: Sequence[dict], *, name: str = "system") -> dict:
    """Run the whole question set and return per-question rows plus aggregates."""
    rows: list[QuestionScore] = []
    for item in questions:
        started = time.perf_counter()
        retrieved = bot.retrieve_doc_ids(str(item["question"]))
        answer = bot.ask(str(item["question"]), use_history=False)
        latency_ms = (time.perf_counter() - started) * 1000.0
        rows.append(score_answer(item, answer, retrieved, latency_ms))

    answerable = [row for row in rows if row.answerable]
    unanswerable = [row for row in rows if not row.answerable]

    aggregate = {
        "system": name,
        "questions": len(rows),
        "answer_accuracy": _mean(1.0 if row.answer_correct else 0.0 for row in rows),
        "answer_accuracy_answerable": _mean(1.0 if row.answer_correct else 0.0 for row in answerable),
        "abstention_correct": _mean(1.0 if row.answer_correct else 0.0 for row in unanswerable),
        "abstention_rate_unanswerable": _mean(1.0 if row.abstained else 0.0 for row in unanswerable),
        "false_answer_rate_unanswerable": _mean(0.0 if row.abstained else 1.0 for row in unanswerable),
        "citation_precision": _mean(row.citation_precision for row in rows),
        "citation_recall": _mean(row.citation_recall for row in answerable),
        "hit_at_k": _mean(1.0 if row.hit_at_k else 0.0 for row in rows),
        "mean_latency_ms": _mean(row.latency_ms for row in rows),
        "k": bot.config.k,
        "min_score": bot.config.min_score,
        "model": bot.client.name,
    }
    return {"aggregate": aggregate, "rows": [row.as_dict() for row in rows]}


def compare(systems: dict[str, RAGChatbot], questions: Sequence[dict]) -> dict:
    """Evaluate several configurations on the same question set (Project G)."""
    return {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "systems": {name: evaluate(bot, questions, name=name) for name, bot in systems.items()},
    }


def write_report(report: dict, path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return path


def format_table(report: dict) -> str:
    """A compact text table for terminals and lab reports."""
    aggregate = report["aggregate"]
    keys = [
        "answer_accuracy",
        "answer_accuracy_answerable",
        "abstention_correct",
        "false_answer_rate_unanswerable",
        "citation_precision",
        "citation_recall",
        "hit_at_k",
        "mean_latency_ms",
    ]
    lines = [f"system: {aggregate['system']}  (n={aggregate['questions']}, k={aggregate['k']})", ""]
    width = max(len(key) for key in keys)
    for key in keys:
        value = aggregate.get(key)
        rendered = "n/a" if value is None else f"{value:.4f}"
        lines.append(f"{key.ljust(width)}  {rendered}")
    return "\n".join(lines)
