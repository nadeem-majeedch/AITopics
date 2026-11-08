"""Project A - A rule-based FAQ chatbot.

The point of this project is to build the *simplest useful* conversational system
first, so that later modules have an honest baseline to beat. There is no model
here: intents are patterns, answers are fixed text, and the only intelligence is
deliberate, inspectable precedence.

Run:
    python project_a_faq_bot.py "how do I enroll"
    python project_a_faq_bot.py --interactive
    python project_a_faq_bot.py --selftest

What to look for:

* exact and normalized matching both hit the enrollment intent;
* a question containing two trigger words returns the higher-priority intent;
* an unknown question returns the fallback, not a guess.

The known limitation is the whole lesson: a rule list cannot generalise. Ask it
"can I get my money back" and compare with a keyword the author did not think of.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field

FALLBACK = (
    "I only answer questions about enrollment, workshops, labs, and assessment. "
    "For anything else, contact support during working hours."
)


@dataclass(frozen=True)
class Intent:
    name: str
    patterns: tuple[str, ...]
    answer: str
    priority: int = 0

    def matches(self, text: str) -> bool:
        return any(re.search(pattern, text) for pattern in self.patterns)


INTENTS: tuple[Intent, ...] = (
    Intent(
        name="refund",
        patterns=(r"\brefund", r"\bmoney back\b", r"\bcancel.*workshop"),
        answer="Paid workshop refunds are available within 14 days of purchase if "
        "you have attended at most one session.",
        priority=30,
    ),
    Intent(
        name="enroll",
        patterns=(r"\benrol", r"\bsign up\b", r"\bregister\b"),
        answer="Enrollment opens on the first Monday of each month and closes on "
        "the fifteenth. You need a verified email address.",
        priority=20,
    ),
    Intent(
        name="assessment",
        patterns=(r"\bassessment\b", r"\bgrad", r"\bmarks?\b", r"\bweights?\b"),
        answer="A module is scored as knowledge check 20%, guided notebook 30%, "
        "independent lab 40%, and reflection 10%.",
        priority=20,
    ),
    Intent(
        name="lab_hours",
        patterns=(r"\blab\b.*\b(hours|open|close)", r"\bopening hours\b"),
        answer="Lab rooms are open 08:00 to 21:00 on weekdays. Weekend access "
        "needs a booking made at least one day in advance.",
        priority=15,
    ),
    Intent(
        name="workshop_cost",
        patterns=(r"\bcost\b", r"\bprice\b", r"\bhow much\b"),
        answer="A paid workshop costs 2,500 credits and runs for three sessions. "
        "Credits never expire.",
        priority=10,
    ),
    Intent(
        name="greeting",
        patterns=(r"^\s*(hi|hello|hey)\b",),
        answer="Hello. Ask me about enrollment, workshops, labs, or assessment.",
        priority=0,
    ),
)


def normalize(text: str) -> str:
    """Lowercase and collapse whitespace; rules match against this form."""
    return re.sub(r"\s+", " ", text.lower()).strip()


@dataclass
class RuleBot:
    """Deterministic intent matcher with an explicit fallback."""

    intents: tuple[Intent, ...] = INTENTS
    fallback: str = FALLBACK
    log: list[dict] = field(default_factory=list)

    def respond(self, text: str) -> str:
        if not text or not text.strip():
            raise ValueError("message cannot be empty")
        normalized = normalize(text)
        candidates = [intent for intent in self.intents if intent.matches(normalized)]
        if not candidates:
            self.log.append({"message": normalized, "intent": None})
            return self.fallback
        chosen = sorted(candidates, key=lambda intent: -intent.priority)[0]
        self.log.append({"message": normalized, "intent": chosen.name, "ambiguous": len(candidates) > 1})
        return chosen.answer


def selftest() -> int:
    bot = RuleBot()
    cases = [
        ("How do I enroll?", "Enrollment opens"),
        ("can I get a refund?", "refunds are available"),
        ("how much does a workshop cost", "2,500"),
        ("what are the assessment weights", "knowledge check 20%"),
        ("what is the weather today", "I only answer questions"),
        ("", None),
    ]
    failures = 0
    for message, expected in cases:
        if expected is None:
            try:
                bot.respond(message)
            except ValueError:
                print(f"PASS  rejection of empty input")
                continue
            print(f"FAIL  empty input was accepted")
            failures += 1
            continue
        reply = bot.respond(message)
        ok = expected.lower() in reply.lower()
        print(f"{'PASS' if ok else 'FAIL'}  {message!r} -> {reply[:60]}...")
        failures += 0 if ok else 1

    ambiguous = bot.respond("I want a refund for the workshop I enrolled in")
    print(f"\nAmbiguity check: {bot.log[-1]}")
    print(f"Answer: {ambiguous[:80]}...")
    print(f"\n{len(cases) - failures}/{len(cases)} checks passed")
    return 0 if failures == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Project A: rule-based FAQ chatbot")
    parser.add_argument("message", nargs="*", help="one question; omit for --interactive")
    parser.add_argument("--interactive", action="store_true", help="read questions from stdin")
    parser.add_argument("--selftest", action="store_true", help="run the built-in checks and exit")
    args = parser.parse_args()

    if args.selftest:
        return selftest()

    bot = RuleBot()
    if args.interactive:
        print("Rule-based FAQ bot. Type 'quit' to exit.")
        for line in sys.stdin:
            if line.strip().lower() in {"quit", "exit"}:
                break
            if line.strip():
                print(f"bot> {bot.respond(line)}")
        return 0

    if not args.message:
        parser.error("provide a question, or use --interactive or --selftest")
    print(bot.respond(" ".join(args.message)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
