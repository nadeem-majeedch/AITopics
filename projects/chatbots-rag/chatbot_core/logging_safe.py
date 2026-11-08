"""Privacy-preserving instrumentation.

A chatbot log answers "what happened?" without becoming a copy of what users typed.
By default this logger stores counts, timings, and hashed identifiers only. Raw
question text is stored only when a caller explicitly opts in, and even then it is
redacted first.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .generation import Answer
from .guardrails import redact


def hash_text(value: str, salt: str = "course") -> str:
    """Stable pseudonym for a user or session identifier."""
    return hashlib.sha256(f"{salt}:{value}".encode("utf-8")).hexdigest()[:16]


@dataclass
class LogRecord:
    timestamp_utc: str
    session_id: str
    model: str
    retrieved: int
    top_score: float
    abstained: bool
    conflict: bool
    citations: int
    quarantined: int
    latency_ms: float
    question: str | None = None
    answer: str | None = None


class SafeLogger:
    """Append-only JSONL logger with a documented, minimal field set."""

    def __init__(
        self,
        path: Path | str,
        *,
        store_text: bool = False,
        session_id: str = "anonymous",
    ) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.store_text = store_text
        self.session_id = hash_text(session_id)

    def log(self, question: str, answer: Answer, latency_ms: float) -> LogRecord:
        record = LogRecord(
            timestamp_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            session_id=self.session_id,
            model=answer.model,
            retrieved=answer.retrieved,
            top_score=round(answer.top_score, 6),
            abstained=answer.abstained,
            conflict=answer.conflict,
            citations=len(answer.citations),
            quarantined=len(answer.quarantined_chunks),
            latency_ms=round(latency_ms, 3),
            question=redact(question)[:200] if self.store_text else None,
            answer=redact(answer.text)[:200] if self.store_text else None,
        )
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record), ensure_ascii=True) + "\n")
        return record

    def read(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
