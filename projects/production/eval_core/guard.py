"""Input screening for an AI endpoint: size, encoding, structure, and injection.

Order matters. Cheap structural checks run first, because they are deterministic
and have almost no false positives; the instruction-pattern check runs last,
because it is a heuristic and the lesson is explicit that it will miss attacks.

Nothing here is a security boundary on its own. It is a filter whose measured
recall and false-positive rate you report, next to the controls that do the real
work: least privilege, schema validation, output encoding, and human approval.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field

MAX_CHARS = 4000
MAX_JSON_LIMIT = 1000
ALLOWED_JSON_KEYS = frozenset({"query", "limit"})

INJECTION_PATTERNS = (
    (r"ignore\s+(?:all\s+)?(?:the\s+)?(?:previous|prior|above|earlier)\s+(?:instructions|rules|prompts)", "override"),
    (r"\b(?:system|assistant|developer)\s*:", "role_spoof"),
    (r"\byou\s+are\s+now\b", "role_spoof"),
    (r"\bdeveloper\s+mode\b", "role_spoof"),
    (r"\b(?:reveal|print|show)\b[^.\n]{0,40}\b(?:api[_ ]?key|secret|system prompt)\b", "exfiltration"),
    (r"\bsend\s+all\s+(?:records|data|customers)\b", "exfiltration"),
    (r"\brepeat\s+the\s+(?:text|words)\s+above\b", "extraction"),
    (r"<!--[\s\S]{0,200}?\b(?:assistant|system|instructions?)\b[\s\S]{0,200}?-->", "hidden_instruction"),
    (r"\bDAN\b", "jailbreak"),
)

INJECTION_REGEXES = tuple((re.compile(pattern, re.IGNORECASE), family) for pattern, family in INJECTION_PATTERNS)

CONTROL_CHARS = re.compile(r"[\u0000-\u0008\u000b\u000c\u000e-\u001f\u202a-\u202e\u2066-\u2069]")
HTML_TAG = re.compile(r"<\s*(script|iframe|img|svg|object)\b", re.IGNORECASE)
PATH_ESCAPE = re.compile(r"(^|[\\/])\.\.([\\/]|$)|^file:|^[a-zA-Z]:[\\/]|^//|^/etc/|^/proc/")


@dataclass
class Verdict:
    allowed: bool
    family: str
    reason: str
    normalised: str = ""
    matched: list[str] = field(default_factory=list)


def normalize(payload: str) -> str:
    """NFKC-normalise, so lookalike characters cannot hide a keyword."""
    return unicodedata.normalize("NFKC", payload)


def detect_injection(text: str) -> list[str]:
    """Return the injection families that matched, strongest first."""
    matches = []
    for regex, family in INJECTION_REGEXES:
        if regex.search(text):
            matches.append(family)
    return matches


def screen(payload: str, *, max_chars: int = MAX_CHARS) -> Verdict:
    if not isinstance(payload, str):
        return Verdict(False, "type", f"payload must be text, got {type(payload).__name__}")

    normalised = normalize(payload).strip()

    if len(normalised) > max_chars:
        return Verdict(False, "limits", f"{len(normalised)} characters exceeds the {max_chars} limit",
                       normalised[:80])
    if CONTROL_CHARS.search(payload):
        return Verdict(False, "unicode_control", "bidirectional or control characters in input", normalised[:80])

    stripped = normalised.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            document = json.loads(stripped)
        except json.JSONDecodeError as error:
            return Verdict(False, "malformed_json", f"invalid JSON: {error.msg} at column {error.colno}",
                           normalised[:80])
        violation = _validate_tool_document(document)
        if violation:
            return Verdict(False, "schema_violation", violation, normalised[:80])
        # A well-formed tool call can still carry an injection in its string
        # arguments, so the text checks below still run on the raw payload.
        families = detect_injection(normalised)
        if families:
            return Verdict(False, "prompt_injection", f"instruction pattern: {families[0]}", normalised[:80], families)
        return Verdict(True, "ok", "valid tool call", normalised[:80])

    if HTML_TAG.search(normalised):
        return Verdict(False, "unsafe_output", "markup that could become script if rendered", normalised[:80])
    if PATH_ESCAPE.search(normalised.replace("\\", "/")):
        return Verdict(False, "path_traversal", "path outside the permitted directory or a URL scheme",
                       normalised[:80])

    families = detect_injection(normalised)
    if families:
        return Verdict(False, "prompt_injection", f"instruction pattern: {families[0]}", normalised[:80], families)

    return Verdict(True, "ok", "accepted", normalised[:80])


def _validate_tool_document(document) -> str:
    """A deliberately tiny schema, written as code because that is what runs."""
    if not isinstance(document, dict):
        return "tool call must be a JSON object"
    unknown = set(document) - ALLOWED_JSON_KEYS
    if unknown:
        return f"unexpected field(s): {', '.join(sorted(unknown))}"
    if "query" not in document:
        return "missing required field 'query'"
    if not isinstance(document["query"], str):
        return f"'query' must be a string, got {type(document['query']).__name__}"
    if len(document["query"]) > 200:
        return "'query' exceeds 200 characters"
    if "limit" in document:
        limit = document["limit"]
        if not isinstance(limit, int) or isinstance(limit, bool):
            return f"'limit' must be an integer, got {type(limit).__name__}"
        if not 1 <= limit <= MAX_JSON_LIMIT:
            return f"'limit' must be between 1 and {MAX_JSON_LIMIT}"
    return ""


def evaluate_cases(cases: list[dict]) -> dict:
    """Run every labelled case and report recall on attacks, false positives on benign."""
    rows = []
    for case in cases:
        verdict = screen(case["payload"])
        expected_block = case["expected"] == "block"
        rows.append(
            {
                "id": case["id"],
                "kind": case["kind"],
                "expected": case["expected"],
                "blocked": not verdict.allowed,
                "family": verdict.family,
                "reason": verdict.reason,
                "correct": (not verdict.allowed) == expected_block,
            }
        )
    attacks = [row for row in rows if row["expected"] == "block"]
    benign = [row for row in rows if row["expected"] == "allow"]
    return {
        "rows": rows,
        "attacks": len(attacks),
        "attacks_blocked": sum(1 for row in attacks if row["blocked"]),
        "recall": sum(1 for row in attacks if row["blocked"]) / len(attacks) if attacks else float("nan"),
        "benign": len(benign),
        "benign_allowed": sum(1 for row in benign if not row["blocked"]),
        "false_positive_rate": sum(1 for row in benign if row["blocked"]) / len(benign) if benign else float("nan"),
        "accuracy": sum(1 for row in rows if row["correct"]) / len(rows) if rows else float("nan"),
        "families": sorted({row["family"] for row in attacks if row["blocked"]}),
    }
