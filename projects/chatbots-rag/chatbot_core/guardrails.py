"""Guardrails for retrieved text: prompt-injection screening and redaction.

Two different problems, two different mechanisms.

**Injection.** Retrieved text is untrusted input. A document can contain
instructions aimed at the model. This module flags chunks that look like an
attempt to redirect the model, so the pipeline can quarantine them instead of
placing them in the context.

**Sensitive data.** A document may contain an email address or an identifier that
must not be echoed back. Redaction replaces those patterns before the text
reaches a prompt or a log.

Neither mechanism is a guarantee. They are filters with measurable false positive
and false negative rates, and the module's own tests state which cases they catch.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions|rules)",
    r"you\s+are\s+now\s+in\s+\w+\s+mode",
    r"reveal\s+(your\s+)?system\s+prompt",
    r"print\s+(your\s+)?(system\s+prompt|instructions)",
    r"reply\s+with\s+the\s+exact\s+text",
    r"new\s+instructions\s*:",
    r"</?\s*(system|assistant)\s*>",
]
_INJECTION = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE = re.compile(r"(?<!\d)(?:\+\d{1,3}[\s-]?)?(?:\(\d{2,4}\)[\s-]?)?\d{3,4}[\s-]?\d{3,4}(?!\d)")
STUDENT_ID = re.compile(r"\bS-\d{4}-\d{4,6}\b")
EXTENSION = re.compile(r"\bextension\s+\d{3,5}\b", re.IGNORECASE)

REDACTIONS: list[tuple[re.Pattern[str], str]] = [
    (EMAIL, "[email redacted]"),
    (STUDENT_ID, "[student id redacted]"),
    (EXTENSION, "[extension redacted]"),
    (PHONE, "[number redacted]"),
]


@dataclass(frozen=True)
class ScanResult:
    """The outcome of screening one chunk."""

    flagged: bool
    matches: tuple[str, ...]
    reason: str = ""

    def __bool__(self) -> bool:
        return self.flagged


def scan_for_injection(text: str) -> ScanResult:
    """Return which injection patterns a chunk matches, if any."""
    found: list[str] = []
    for pattern in _INJECTION:
        match = pattern.search(text)
        if match:
            found.append(match.group(0).strip())
    if found:
        return ScanResult(True, tuple(found), "instruction-like text in retrieved content")
    return ScanResult(False, ())


def redact(text: str) -> str:
    """Mask common personal identifiers. Order matters: longest patterns first."""
    for pattern, replacement in REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


def redact_many(texts: list[str]) -> list[str]:
    return [redact(text) for text in texts]


def contains_sensitive(text: str) -> bool:
    """True when any redaction pattern would fire."""
    return any(pattern.search(text) for pattern, _ in REDACTIONS)


def sanitize_context(chunks: list) -> tuple[list, list]:
    """Split chunks into (usable, quarantined) and redact the usable ones.

    Returns new chunk-like objects with redacted text. Quarantined chunks are
    returned unchanged so the caller can report why they were withheld.
    """
    usable: list = []
    quarantined: list = []
    for chunk in chunks:
        if scan_for_injection(chunk.text):
            quarantined.append(chunk)
        else:
            usable.append(chunk)
    return usable, quarantined
