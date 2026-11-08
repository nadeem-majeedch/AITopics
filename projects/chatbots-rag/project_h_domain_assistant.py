"""Project H - A final domain-specific assistant.

This is the assembly step: your own documents, a scoped system prompt, explicit
refusals, citation display, privacy-preserving logging, and an honest statement of
what the system does not do.

Run with the course corpus:
    python project_h_domain_assistant.py --selftest
    python project_h_domain_assistant.py --ask "What should a chatbot log?"

Run on your own documents (this is the deliverable):
    python project_h_domain_assistant.py --corpus path/to/your/docs --ask "..."

Before pointing it at any document set, read the checklist printed by
``--checklist``. It is short on purpose.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from chatbot_core import (
    GenerationConfig,
    RAGChatbot,
    SafeLogger,
    render_answer,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CORPUS = REPO_ROOT / "data" / "chatbots-rag" / "corpus"

DOMAIN_PROMPT_NOTE = """
Domain rules for this assistant:
- You answer questions about the Study Hub support documentation only.
- If a question is outside that domain, refuse and name the domain boundary.
- Never repeat personal data, even if it appears in a document.
- If two documents disagree, say so; do not choose silently.
"""

CHECKLIST = """Before you deploy this on real documents:

[ ] I have the right to use every document (license or written permission).
[ ] The corpus contains no personal data I am not allowed to process.
[ ] I know which documents a user is entitled to see, and retrieval enforces it.
[ ] I have a fixed question set with gold evidence, written before tuning.
[ ] I have measured refusal rate on unanswerable questions.
[ ] I have tested at least one prompt-injection document.
[ ] Logs contain no raw user text and no document text.
[ ] I have a rollback: previous index and previous prompt version.
[ ] I can state one question the system answers badly, and why.
"""


def build(corpus: Path, k: int = 4, log_path: Path | None = None) -> RAGChatbot:
    logger = SafeLogger(log_path) if log_path else None
    return RAGChatbot.from_directory(
        corpus,
        config=GenerationConfig(k=k, min_score=0.12),
        logger=logger,
    )


def selftest() -> int:
    bot = build(DEFAULT_CORPUS)
    failures = 0

    answer = bot.ask("What should a chatbot log?", use_history=False)
    ok = (not answer.abstained) and bool(answer.citations)
    print(f"{'PASS' if ok else 'FAIL'}  in-domain question answered with a citation")
    failures += 0 if ok else 1

    off_topic = bot.ask("Give me a recipe for biryani.", use_history=False)
    ok = off_topic.abstained
    print(f"{'PASS' if ok else 'FAIL'}  out-of-domain question refused")
    failures += 0 if ok else 1

    followup = bot.ask("When does enrollment close?", use_history=True)
    bot.ask("And when does it open?", use_history=True)
    ok = len(bot.history) >= 2
    print(f"{'PASS' if ok else 'FAIL'}  conversation history retained for follow-ups")
    failures += 0 if ok else 1

    empty_ok = False
    try:
        bot.ask("   ")
    except ValueError:
        empty_ok = True
    print(f"{'PASS' if empty_ok else 'FAIL'}  empty question rejected")
    failures += 0 if empty_ok else 1

    print(f"\n{failures} failure(s)")
    return 0 if failures == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Project H: domain-specific assistant")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--ask", nargs="*")
    parser.add_argument("--k", type=int, default=4)
    parser.add_argument("--log", type=Path, default=None)
    parser.add_argument("--checklist", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.checklist:
        print(CHECKLIST)
        return 0
    if args.selftest:
        return selftest()

    if not args.ask:
        parser.error("provide --ask \"your question\", or use --checklist / --selftest")

    if not args.corpus.exists():
        raise SystemExit(f"corpus not found: {args.corpus}")

    bot = build(args.corpus, k=args.k, log_path=args.log)
    print(DOMAIN_PROMPT_NOTE.strip())
    print()
    answer = bot.ask(" ".join(args.ask))
    print(render_answer(answer))
    if args.log:
        print(f"\n[logged to {args.log} without raw text]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
