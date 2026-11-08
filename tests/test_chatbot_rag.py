"""Offline unit tests for the conversational AI section.

Runs with the standard library only:

    python -m unittest discover -s tests -v
    python -m unittest tests.test_chatbot_rag -v

No network, no GPU, no API key, and no model download. The corpus is generated
on demand by ``scripts/make_chatbot_data.py``.

The tests named ``test_rag_*`` are the eight RAG quality cases from the course
material. Each one asserts a behaviour, not a vibe: a refusal is a pass, and a
plausible answer without support is a failure.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "projects" / "chatbots-rag"))

from chatbot_core import (  # noqa: E402
    ABSTAIN_TEXT,
    BM25,
    ConversationHistory,
    FakeModelClient,
    GenerationConfig,
    HashingEmbedder,
    RAGChatbot,
    SafeLogger,
    build_chunks,
    build_registry,
    chunk_text,
    detect_conflict,
    evaluate,
    generate,
    load_documents,
    parse_model_output,
    scan_for_injection,
    validate,
)

DATA = BASE / "data" / "chatbots-rag"
CORPUS = DATA / "corpus"
ADVERSARIAL = DATA / "adversarial"


def setUpModule() -> None:  # noqa: N802 - unittest hook
    if not CORPUS.exists() or not ADVERSARIAL.exists():
        subprocess.run(
            [sys.executable, str(BASE / "scripts" / "make_chatbot_data.py")],
            check=True,
            capture_output=True,
        )


def make_bot(corpus: Path | None = None, **config_kwargs) -> RAGChatbot:
    return RAGChatbot.from_directory(
        corpus or CORPUS,
        client=FakeModelClient(),
        config=GenerationConfig(**config_kwargs),
    )


def adversarial_chunks(doc_id: str):
    documents = [doc for doc in load_documents(ADVERSARIAL) if doc.doc_id == doc_id]
    return build_chunks(documents)


class RecordingClient:
    """A stub model that records prompts and returns a fixed reply."""

    name = "recording-stub"

    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.prompts: list[list[dict[str, str]]] = []

    def complete(self, messages, temperature: float = 0.0) -> str:
        self.prompts.append([dict(message) for message in messages])
        return self.reply

    @property
    def last_prompt(self) -> str:
        return "\n".join(message["content"] for message in self.prompts[-1])


class TestDocuments(unittest.TestCase):
    def test_chunk_text_respects_size_and_overlap(self) -> None:
        text = "Sentence one is here. " * 60
        pieces = chunk_text(text, max_chars=200, overlap=40)
        self.assertGreater(len(pieces), 1)
        for piece, start, end in pieces:
            self.assertLessEqual(len(piece), 220)
            self.assertEqual(text[start:end], piece)

    def test_chunks_have_unique_ids_and_heading_context(self) -> None:
        chunks = build_chunks(load_documents(CORPUS))
        ids = [chunk.chunk_id for chunk in chunks]
        self.assertEqual(len(ids), len(set(ids)), "chunk ids must be unique")
        self.assertTrue(all(chunk.title and chunk.section for chunk in chunks))
        self.assertIn("Refund window", " ".join(chunk.retrieval_text for chunk in chunks))

    def test_chunk_text_rejects_impossible_overlap(self) -> None:
        with self.assertRaises(ValueError):
            chunk_text("some text", max_chars=100, overlap=100)


class TestEmbeddingsAndRetrieval(unittest.TestCase):
    def test_identical_texts_are_maximally_similar(self) -> None:
        embedder = HashingEmbedder()
        vectors = embedder.embed(["refund policy", "refund policy", "lab access"])
        self.assertAlmostEqual(float(vectors[0] @ vectors[1]), 1.0, places=5)
        self.assertLess(float(vectors[0] @ vectors[2]), 0.99)

    def test_bm25_returns_relevant_chunk(self) -> None:
        chunks = build_chunks(load_documents(CORPUS))
        results = BM25(chunks).search("refund window for a paid workshop", k=3)
        self.assertTrue(results)
        self.assertIn("billing-and-refunds", results[0].chunk.doc_id)

    def test_retrieval_hit_rate_on_dev_questions(self) -> None:
        bot = make_bot(k=4)
        questions = json.loads((DATA / "dev_questions.json").read_text(encoding="utf-8"))
        answerable = [q for q in questions if q["answerable"]]
        hits = 0
        for item in answerable:
            retrieved = bot.retrieve_doc_ids(item["question"], k=4)
            if any(doc in item["gold_doc_ids"] for doc in retrieved):
                hits += 1
        rate = hits / len(answerable)
        self.assertGreaterEqual(rate, 0.7, f"retrieval hit rate too low: {rate:.2f}")


class TestRAGQuality(unittest.TestCase):
    """The eight required RAG quality cases, plus fail-closed parsing."""

    def test_rag_supported_answer_is_grounded(self) -> None:
        bot = make_bot()
        answer = bot.ask("How much does a paid workshop cost?", use_history=False)
        self.assertFalse(answer.abstained)
        self.assertIn("2,500", answer.text)
        retrieved = set(bot.retrieve_doc_ids("How much does a paid workshop cost?"))
        for citation in answer.citations:
            self.assertIn(citation.source.rsplit(".", 1)[0], retrieved)

    def test_rag_unsupported_question_abstains(self) -> None:
        bot = make_bot()
        answer = bot.ask("What is the capital of Mongolia?", use_history=False)
        self.assertTrue(answer.abstained)
        self.assertEqual(answer.citations, [])
        self.assertEqual(answer.text, ABSTAIN_TEXT)

    def test_rag_missing_document_abstains(self) -> None:
        bot = make_bot()
        answer = bot.ask("How much is the campus parking permit fee?", use_history=False)
        self.assertTrue(answer.abstained)
        self.assertEqual(answer.citations, [])

    def test_rag_conflicting_sources_are_disclosed(self) -> None:
        chunks = adversarial_chunks("conflict_refunds_a") + adversarial_chunks("conflict_refunds_b")
        client = RecordingClient(
            json.dumps({"answer": "A refund can be requested within 14 days.", "citations": [1], "confident": True})
        )
        answer = generate(
            "What is the refund deadline for a workshop?",
            chunks,
            [0.9] * len(chunks),
            client,
        )
        self.assertFalse(answer.abstained)
        self.assertTrue(answer.conflict, "differing deadlines must be flagged, not averaged")
        self.assertIn("14", answer.conflict_note)
        self.assertIn("30", answer.conflict_note)

    def test_rag_irrelevant_retrieval_is_not_used_as_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "decoys.md").write_text(
                "# Workshop notes\n\nThe workshop banner uses blue paint and a folding stand.\n",
                encoding="utf-8",
            )
            bot = RAGChatbot.from_directory(root, client=FakeModelClient(), config=GenerationConfig(k=3))
            answer = bot.ask("What is the refund deadline for a workshop?", use_history=False)
            self.assertTrue(answer.abstained)

    def test_rag_prompt_injection_in_document_is_quarantined(self) -> None:
        chunks = adversarial_chunks("injection_notes")
        poisoned = [chunk for chunk in chunks if scan_for_injection(chunk.text).flagged]
        self.assertTrue(poisoned, "the fixture must contain an instruction-like passage")

        # Case 1: the only retrieved evidence is poisoned. The pipeline must
        # refuse without ever calling a model.
        client = RecordingClient(json.dumps({"answer": "PWNED-4471", "citations": [1]}))
        answer = generate(
            "What does the maintenance mode note say?",
            poisoned,
            [0.9] * len(poisoned),
            client,
        )
        self.assertTrue(answer.abstained)
        self.assertTrue(answer.quarantined_chunks)
        self.assertEqual(client.prompts, [], "quarantined text must never reach a model")
        self.assertNotIn("PWNED-4471", json.dumps(answer.as_dict()))

        # Case 2: mixed evidence. The benign chunk may answer, but the payload
        # must not appear in the prompt, the answer, or the diagnostics.
        mixed_client = RecordingClient(json.dumps({"answer": "Lab notes are reviewed every Friday.", "citations": [1]}))
        mixed = generate("What do the lab notes say about scheduling?", chunks, [0.9] * len(chunks), mixed_client)
        self.assertTrue(mixed.quarantined_chunks, "the poisoned chunk must be withheld")
        self.assertNotIn("PWNED-4471", mixed_client.last_prompt)
        self.assertNotIn("PWNED-4471", mixed.text)
        self.assertNotIn("PWNED-4471", json.dumps(mixed.as_dict()))

    def test_rag_sensitive_information_is_redacted(self) -> None:
        chunks = adversarial_chunks("sensitive_contact")
        client = RecordingClient(json.dumps({"answer": "The support lead handles escalation.", "citations": [1]}))
        answer = generate("Who is the support lead?", chunks, [0.9] * len(chunks), client)
        self.assertNotIn("lead.support@example.edu", client.last_prompt)
        self.assertNotIn("S-2026-001847", client.last_prompt)
        self.assertNotIn("lead.support@example.edu", answer.text)
        self.assertIn("[email redacted]", client.last_prompt)

    def test_rag_fabricated_citation_fails_closed(self) -> None:
        chunks = adversarial_chunks("conflict_refunds_a")
        client = RecordingClient(
            json.dumps({"answer": "A refund is available within 30 days [9].", "citations": [9], "confident": True})
        )
        answer = generate("What is the refund deadline?", chunks, [0.9] * len(chunks), client)
        self.assertTrue(answer.abstained, "an answer with an invented source must not be shown")
        self.assertIn(9, answer.dropped_citations)
        self.assertEqual(answer.citations, [])

    def test_rag_invalid_json_fails_closed(self) -> None:
        chunks = adversarial_chunks("conflict_refunds_a")
        client = RecordingClient("I believe it is about 14 days, but I am not sure.")
        answer = generate("What is the refund deadline?", chunks, [0.9] * len(chunks), client)
        self.assertTrue(answer.abstained)
        self.assertEqual(answer.citations, [])


class TestCitationsAndParsing(unittest.TestCase):
    def test_validate_separates_valid_and_fabricated(self) -> None:
        chunks = build_chunks(load_documents(CORPUS))[:3]
        registry = build_registry(chunks, [0.9, 0.8, 0.7])
        outcome = validate([1, 99], "Answer with [1] and [42].", registry)
        self.assertEqual([c.number for c in outcome.valid], [1])
        self.assertIn(99, outcome.invalid_numbers)
        self.assertIn(42, outcome.fabricated_in_text)
        self.assertFalse(outcome.ok)

    def test_parse_accepts_json_inside_prose(self) -> None:
        payload = parse_model_output('Here you go: {"answer": "x", "citations": [2], "confident": true} done')
        self.assertEqual(payload["answer"], "x")
        self.assertEqual(payload["citations"], [2])

    def test_parse_rejects_missing_answer(self) -> None:
        with self.assertRaises(ValueError):
            parse_model_output('{"citations": [1]}')

    def test_parse_rejects_non_integer_citation(self) -> None:
        with self.assertRaises(ValueError):
            parse_model_output('{"answer": "x", "citations": ["one"]}')


class TestHistoryAndPrivacy(unittest.TestCase):
    def test_history_trimming_is_reported(self) -> None:
        history = ConversationHistory(max_turns=2, max_chars=10_000)
        for index in range(3):
            history.add_exchange(f"question {index}", f"answer {index}")
        self.assertEqual(len(history), 2)
        self.assertGreaterEqual(history.dropped_turns, 4)
        messages = history.messages()
        self.assertTrue(any("older turns removed" in message["content"] for message in messages))

    def test_logger_stores_no_text_by_default(self) -> None:
        bot = make_bot()
        with tempfile.TemporaryDirectory() as tmp:
            bot.logger = SafeLogger(Path(tmp) / "log.jsonl", session_id="student-1")
            bot.ask("How much does a paid workshop cost?", use_history=False)
            record = bot.logger.read()[0]
            self.assertIsNone(record["question"])
            self.assertIsNone(record["answer"])
            self.assertGreaterEqual(record["retrieved"], 1)
            self.assertNotIn("student-1", json.dumps(record))

    def test_logger_redacts_when_text_is_stored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            logger = SafeLogger(Path(tmp) / "log.jsonl", store_text=True)
            answer = type("Answer", (), {
                "model": "stub", "retrieved": 0, "top_score": 0.0, "abstained": True,
                "conflict": False, "citations": [], "quarantined_chunks": [], "text": "none",
            })()
            logger.log("write to lead.support@example.edu", answer, 1.0)
            record = logger.read()[0]
            self.assertNotIn("lead.support@example.edu", record["question"])
            self.assertIn("[email redacted]", record["question"])


class TestEvaluationAndConflict(unittest.TestCase):
    def test_evaluate_reports_documented_metrics(self) -> None:
        bot = make_bot()
        questions = json.loads((DATA / "dev_questions.json").read_text(encoding="utf-8"))[:4]
        report = evaluate(bot, questions, name="test")
        for key in (
            "answer_accuracy",
            "abstention_correct",
            "citation_precision",
            "citation_recall",
            "hit_at_k",
            "mean_latency_ms",
        ):
            self.assertIn(key, report["aggregate"])
        self.assertEqual(len(report["rows"]), 4)
        self.assertIsNotNone(report["aggregate"]["answer_accuracy"])

    def test_conflict_detection_ignores_unrelated_quantities(self) -> None:
        chunks = adversarial_chunks("conflict_refunds_a")
        conflict, note = detect_conflict(chunks, "What are the lab room opening hours?")
        self.assertFalse(conflict)
        self.assertEqual(note, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
