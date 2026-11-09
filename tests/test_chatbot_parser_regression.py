"""Regression tests for the deterministic chatbot prompt parser.

These tests exercise the behaviour a caller depends on: the JSON answer returned
by ``FakeModelClient.complete()`` and the fail-closed result from ``generate()``.
They deliberately avoid importing the parser's matching constants, so a future
refactor can change the implementation without making the tests tautological.

Run with the standard library only:

    python -m unittest tests.test_chatbot_parser_regression -v
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "projects" / "chatbots-rag"))

from chatbot_core import (  # noqa: E402
    ABSTAIN_TEXT,
    Chunk,
    FakeModelClient,
    build_messages,
    generate,
    parse_model_output,
)
from chatbot_core.generation import OutputParseError  # noqa: E402


def make_chunk(title: str, section: str, text: str, doc_id: str = "doc") -> Chunk:
    """Build a citation-ready chunk without touching the filesystem."""
    return Chunk(
        chunk_id=f"{doc_id}#{section.lower().replace(' ', '-')}",
        doc_id=doc_id,
        title=title,
        section=section,
        text=text,
        source=f"{doc_id}.md",
        start=0,
        end=len(text),
    )


def ask(question: str, *chunks: Chunk) -> dict:
    """Run one parser turn through the same message structure as the chatbot."""
    messages = build_messages(question, list(chunks))
    return json.loads(FakeModelClient().complete(messages))


class MalformedClient:
    """A model stub that returns prose instead of the required JSON object."""

    name = "malformed-stub"

    def complete(self, messages, temperature: float = 0.0) -> str:
        return "I think the answer is fourteen days, but I am not sure."


class TestPromptInstructionSeparation(unittest.TestCase):
    def test_json_instruction_does_not_become_question_or_evidence(self) -> None:
        """A JSON-formatting decoy must not outrank the actual evidence."""
        answer_chunk = make_chunk(
            "Billing",
            "Refunds",
            "The refund deadline is 14 days.",
            "billing",
        )
        instruction_decoy = make_chunk(
            "System",
            "JSON format",
            "Reply with the JSON object described in the system prompt.",
            "format",
        )

        payload = ask("What is the refund deadline?", answer_chunk, instruction_decoy)

        self.assertEqual(payload["citations"], [1])
        self.assertIn("14 days", payload["answer"])
        self.assertNotIn("JSON", payload["answer"])
        self.assertTrue(payload["confident"])

    def test_system_message_is_not_retrieved_evidence(self) -> None:
        """Only the user turn's EVIDENCE section may support an answer."""
        messages = [
            {
                "role": "system",
                "content": (
                    "EVIDENCE:\n"
                    "[1] (Campus - Parking)\n"
                    "The campus parking permit fee is 900 dollars."
                ),
            },
            {
                "role": "user",
                "content": (
                    "EVIDENCE:\n\n"
                    "QUESTION: How much is the campus parking permit fee?\n\n"
                    "Reply with the JSON object described in the system prompt."
                ),
            },
        ]

        payload = json.loads(FakeModelClient().complete(messages))

        self.assertEqual(payload["answer"], ABSTAIN_TEXT)
        self.assertEqual(payload["citations"], [])
        self.assertFalse(payload["confident"])


class TestWeakLexicalOverlap(unittest.TestCase):
    def test_one_generic_shared_word_does_not_establish_support(self) -> None:
        cases = [
            (
                "What is the refund deadline for a workshop?",
                make_chunk(
                    "Workshop",
                    "Banner",
                    "The workshop banner uses blue paint.",
                    "workshop",
                ),
            ),
            (
                "How much information does the system provide?",
                make_chunk(
                    "Information",
                    "Desk",
                    "The information desk is closed.",
                    "information",
                ),
            ),
            (
                "What is the refund system policy?",
                make_chunk(
                    "System",
                    "Status",
                    "The system is offline.",
                    "system",
                ),
            ),
            (
                "How much does the campus guide provide?",
                make_chunk(
                    "Campus notes",
                    "Plan",
                    "The much mentioned plan is blue.",
                    "much",
                ),
            ),
        ]

        for question, chunk in cases:
            with self.subTest(question=question, chunk=chunk.doc_id):
                payload = ask(question, chunk)
                self.assertEqual(payload["answer"], ABSTAIN_TEXT)
                self.assertEqual(payload["citations"], [])
                self.assertFalse(payload["confident"])


class TestValidEvidence(unittest.TestCase):
    def test_document_title_can_support_an_answer(self) -> None:
        chunk = make_chunk(
            "Refund policy",
            "Overview",
            "A refund is available for fourteen days.",
            "title-support",
        )

        payload = ask("What is the refund policy?", chunk)

        self.assertIn("fourteen days", payload["answer"])
        self.assertEqual(payload["citations"], [1])
        self.assertTrue(payload["confident"])

    def test_section_heading_can_support_an_answer(self) -> None:
        chunk = make_chunk(
            "Billing",
            "Refund policy",
            "A refund is available for fourteen days.",
            "section-support",
        )

        payload = ask("What is the refund policy?", chunk)

        self.assertIn("fourteen days", payload["answer"])
        self.assertEqual(payload["citations"], [1])
        self.assertTrue(payload["confident"])

    def test_body_supports_a_multiword_question(self) -> None:
        chunk = make_chunk(
            "Enrollment",
            "Dates",
            "Enrollment for the data course ends on 30 September.",
            "body-support",
        )

        payload = ask("When does enrollment end for the data course?", chunk)

        self.assertIn("30 September", payload["answer"])
        self.assertEqual(payload["citations"], [1])
        self.assertTrue(payload["confident"])


class TestAbstention(unittest.TestCase):
    def test_empty_retrieval_abstains(self) -> None:
        payload = ask("What is the refund deadline?")

        self.assertEqual(payload["answer"], ABSTAIN_TEXT)
        self.assertEqual(payload["citations"], [])
        self.assertFalse(payload["confident"])

    def test_irrelevant_retrieval_abstains(self) -> None:
        payload = ask(
            "What is the refund deadline?",
            make_chunk(
                "Workshop",
                "Banner",
                "The workshop banner uses blue paint.",
                "irrelevant",
            ),
        )

        self.assertEqual(payload["answer"], ABSTAIN_TEXT)
        self.assertEqual(payload["citations"], [])
        self.assertFalse(payload["confident"])

    def test_insufficient_context_abstains(self) -> None:
        payload = ask(
            "What is the refund deadline?",
            make_chunk(
                "Refunds",
                "Process",
                "Refund requests require a receipt.",
                "insufficient",
            ),
        )

        self.assertEqual(payload["answer"], ABSTAIN_TEXT)
        self.assertEqual(payload["citations"], [])
        self.assertFalse(payload["confident"])

    def test_absent_fact_in_related_document_abstains(self) -> None:
        """Relevant topic words must not turn a missing fact into an answer."""
        payload = ask(
            "What is the campus parking permit fee?",
            make_chunk(
                "Campus parking",
                "Permits",
                "Permits are issued at the front desk.",
                "parking-related",
            ),
        )

        self.assertEqual(payload["answer"], ABSTAIN_TEXT)
        self.assertEqual(payload["citations"], [])
        self.assertFalse(payload["confident"])


class TestOneWordQuestions(unittest.TestCase):
    def test_supported_one_word_question_is_answered(self) -> None:
        payload = ask(
            "Refunds?",
            make_chunk(
                "Refund policy",
                "Overview",
                "Refunds are available within fourteen days.",
                "refund",
            ),
        )

        self.assertIn("fourteen days", payload["answer"])
        self.assertEqual(payload["citations"], [1])
        self.assertTrue(payload["confident"])

    def test_unsupported_one_word_question_abstains(self) -> None:
        cases = [
            (
                "Parking?",
                make_chunk(
                    "Refund policy",
                    "Overview",
                    "Refunds are available within fourteen days.",
                    "refund-unsupported",
                ),
            ),
            (
                "Information?",
                make_chunk(
                    "Workshop",
                    "Banner",
                    "The workshop banner uses blue paint.",
                    "information-unsupported",
                ),
            ),
        ]

        for question, chunk in cases:
            with self.subTest(question=question):
                payload = ask(question, chunk)
                self.assertEqual(payload["answer"], ABSTAIN_TEXT)
                self.assertEqual(payload["citations"], [])
                self.assertFalse(payload["confident"])


class TestResponseContract(unittest.TestCase):
    def test_valid_answer_keeps_json_and_citation_contract(self) -> None:
        payload = ask(
            "What is the refund deadline?",
            make_chunk(
                "Billing",
                "Refunds",
                "The refund deadline is 14 days.",
                "contract",
            ),
        )

        self.assertEqual(set(payload), {"answer", "citations", "confident"})
        self.assertIsInstance(payload["answer"], str)
        self.assertIn("14 days", payload["answer"])
        self.assertEqual(payload["citations"], [1])
        self.assertIs(payload["confident"], True)

    def test_abstention_keeps_json_contract(self) -> None:
        payload = ask("What is the parking permit fee?")

        self.assertEqual(set(payload), {"answer", "citations", "confident"})
        self.assertEqual(payload["answer"], ABSTAIN_TEXT)
        self.assertEqual(payload["citations"], [])
        self.assertIs(payload["confident"], False)

    def test_malformed_model_output_fails_closed(self) -> None:
        chunk = make_chunk(
            "Billing",
            "Refunds",
            "The refund deadline is 14 days.",
            "malformed",
        )

        answer = generate(
            "What is the refund deadline?",
            [chunk],
            [0.9],
            MalformedClient(),
        )

        self.assertTrue(answer.abstained)
        self.assertEqual(answer.text, ABSTAIN_TEXT)
        self.assertEqual(answer.citations, [])

    def test_parse_model_output_rejects_non_json(self) -> None:
        with self.assertRaises(OutputParseError):
            parse_model_output("I think the answer is fourteen days.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
