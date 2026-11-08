"""Project E - A chatbot that answers questions about course documents.

Projects A-D work on a small synthetic corpus. This one points the same pipeline
at documents that already exist in the repository, which is harder: they are
longer, they link to each other, and a question can match a paragraph that is
about the *topic* without answering it.

Run:
    python project_e_course_docs_bot.py "What assessment weight does the lab carry?"
    python project_e_course_docs_bot.py --index-stats
    python project_e_course_docs_bot.py --selftest

The corpus is the course's own published material, so there is no licensing or
privacy question. When you point this at your own documents, read Module 16 first.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from chatbot_core import (
    GenerationConfig,
    RAGChatbot,
    build_chunks,
    load_documents,
    render_answer,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CORPUS = REPO_ROOT / "docs"


def build(corpus: Path = DEFAULT_CORPUS, k: int = 4, max_chars: int = 700) -> RAGChatbot:
    if not corpus.exists():
        raise SystemExit(f"corpus not found: {corpus}")
    return RAGChatbot.from_directory(
        corpus,
        config=GenerationConfig(k=k, min_score=0.10),
        max_chars=max_chars,
        overlap=100,
    )


def index_stats(corpus: Path = DEFAULT_CORPUS) -> dict:
    documents = load_documents(corpus)
    chunks = build_chunks(documents, max_chars=700, overlap=100)
    sizes = [len(chunk.text) for chunk in chunks]
    return {
        "documents": len(documents),
        "chunks": len(chunks),
        "mean_chunk_chars": round(sum(sizes) / len(sizes), 1) if sizes else 0,
        "smallest_chunk": min(sizes) if sizes else 0,
        "largest_chunk": max(sizes) if sizes else 0,
        "documents_by_area": {
            area: sum(1 for doc in documents if area in doc.source)
            for area in ("lessons", "syllabus", "course", "technical", "planning")
        },
    }


def selftest() -> int:
    # A small, bounded slice of the repository keeps this check stable. Pointing
    # the selftest at all of docs/ makes the expected answer depend on whichever
    # pages happen to rank first, which is not a property worth asserting.
    corpus = REPO_ROOT / "docs" / "lessons" / "f01-python-ai"
    bot = build(corpus)
    failures = 0

    # On a real corpus the honest selftest asserts pipeline properties, not
    # wording: any answer shown must cite something that was actually retrieved
    # for this turn, and an off-topic question must be refused. Exact-fact recall
    # is what the lab measures with a question set, not what a smoke test claims.
    answered_with_citations = 0
    for question in (
        "What hardware does this unit need?",
        "How many hours of study does the unit take?",
        "What Python packages does this unit require?",
    ):
        answer = bot.ask(question, use_history=False)
        print(f"\nQ: {question}\nA: {answer.text[:180]}")
        if answer.abstained:
            print("  refused (allowed on a real corpus; record it in your lab)")
            continue
        retrieved = set(bot.retrieve_doc_ids(question))
        resolved = all(citation.source.rsplit(".", 1)[0] in retrieved for citation in answer.citations)
        ok = bool(answer.citations) and resolved
        print("  PASS  citations resolve to retrieved documents" if ok else "  FAIL  unresolved citation")
        failures += 0 if ok else 1
        answered_with_citations += 1 if ok else 0

    if answered_with_citations == 0:
        print("\nFAIL  no in-domain question was answered with a resolving citation")
        failures += 1

    off_topic = bot.ask("Who won the 2018 world cup?", use_history=False)
    print(f"\nQ: Who won the 2018 world cup?\nA: {off_topic.text[:120]}")
    print("PASS  refused" if off_topic.abstained else "FAIL  answered an out-of-domain question")
    failures += 0 if off_topic.abstained else 1

    print(f"\nanswered with resolving citations: {answered_with_citations}")
    print(f"{failures} failure(s)")
    return 0 if failures == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Project E: chatbot over course documents")
    parser.add_argument("question", nargs="*")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--k", type=int, default=4)
    parser.add_argument("--index-stats", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.index_stats:
        for key, value in index_stats(args.corpus).items():
            print(f"{key}: {value}")
        return 0

    if args.selftest:
        return selftest()

    if not args.question:
        parser.error("provide a question, --index-stats, or --selftest")

    bot = build(args.corpus, k=args.k)
    answer = bot.ask(" ".join(args.question), use_history=False)
    print(render_answer(answer))
    print(f"\n[retrieved={answer.retrieved} top_score={answer.top_score:.3f} model={answer.model}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
