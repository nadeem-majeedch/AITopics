"""Project F - A RAG assistant that displays source citations.

The difference between a demo and a trustworthy assistant is what happens around
the answer: which evidence was used, which was withheld, and whether the sources
agree. This project renders all three.

Run:
    python project_f_cited_assistant.py "What is the refund deadline?"
    python project_f_cited_assistant.py --show-withheld "What do the lab notes say about maintenance?"
    python project_f_cited_assistant.py --selftest

Try the adversarial corpus with ``--corpus data/chatbots-rag/adversarial`` to see
a quarantined passage, a conflict, and redaction in the same interface.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from chatbot_core import GenerationConfig, RAGChatbot

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CORPUS = REPO_ROOT / "data" / "chatbots-rag" / "corpus"


def build(corpus: Path, k: int = 4, min_score: float = 0.12) -> RAGChatbot:
    return RAGChatbot.from_directory(corpus, config=GenerationConfig(k=k, min_score=min_score))


def render(answer, show_withheld: bool = False) -> str:
    """Render an answer with its evidence, not just its text."""
    lines: list[str] = []

    if answer.abstained:
        lines.append("ANSWER (refused):")
        lines.append(f"  {answer.text}")
    else:
        lines.append("ANSWER:")
        lines.append(f"  {answer.text}")

    if answer.citations:
        lines.append("")
        lines.append("SOURCES:")
        for citation in answer.citations:
            lines.append(f"  [{citation.number}] {citation.title} - {citation.section}")
            lines.append(f"      file: {citation.source}  score: {citation.score:.3f}")
    else:
        lines.append("")
        lines.append("SOURCES: none (no retrieved passage supports an answer)")

    if answer.conflict:
        lines.append("")
        lines.append("CONFLICT:")
        lines.append(f"  {answer.conflict_note}")

    if answer.dropped_citations:
        lines.append("")
        lines.append(f"DROPPED CITATIONS: {answer.dropped_citations} (not in the retrieved set)")

    if show_withheld and answer.quarantined_chunks:
        lines.append("")
        lines.append("WITHHELD EVIDENCE (instruction-like content):")
        for chunk_id in answer.quarantined_chunks:
            lines.append(f"  {chunk_id}")

    lines.append("")
    lines.append(f"[retrieved={answer.retrieved} top_score={answer.top_score:.3f} model={answer.model}]")
    return "\n".join(lines)


def selftest() -> int:
    bot = build(DEFAULT_CORPUS)
    failures = 0

    supported = bot.ask("How much does a paid workshop cost?", use_history=False)
    text = render(supported)
    checks = [
        ("answer is not a refusal", not supported.abstained),
        ("a source is shown", "SOURCES:" in text and bool(supported.citations)),
        ("the section name is shown", any(c.section for c in supported.citations)),
        ("the file path is shown", any(c.source.endswith(".md") for c in supported.citations)),
    ]
    for label, ok in checks:
        print(f"{'PASS' if ok else 'FAIL'}  {label}")
        failures += 0 if ok else 1

    refused = bot.ask("What is the capital of Mongolia?", use_history=False)
    refused_text = render(refused)
    ok = refused.abstained and "none (no retrieved passage supports an answer)" in refused_text
    print(f"{'PASS' if ok else 'FAIL'}  refusal shows no sources")
    failures += 0 if ok else 1

    # k covers the whole adversarial set so the poisoned passage is always in the
    # retrieved window; the check is about withholding, not about ranking.
    adversarial = build(REPO_ROOT / "data" / "chatbots-rag" / "adversarial", k=8)
    injected = adversarial.ask("What do the lab notes say about maintenance mode?", use_history=False)
    ok = bool(injected.quarantined_chunks) and "PWNED-4471" not in injected.text
    print(f"{'PASS' if ok else 'FAIL'}  poisoned passage withheld from the answer")
    failures += 0 if ok else 1

    print(f"\n{failures} failure(s)")
    return 0 if failures == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Project F: RAG assistant with citations")
    parser.add_argument("question", nargs="*")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--k", type=int, default=4)
    parser.add_argument("--show-withheld", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        return selftest()
    if not args.question:
        parser.error("provide a question or --selftest")

    bot = build(args.corpus, k=args.k)
    answer = bot.ask(" ".join(args.question), use_history=False)
    print(render(answer, show_withheld=args.show_withheld))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
