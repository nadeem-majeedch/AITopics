"""Project B - A simple LLM chatbot in Python.

This project isolates the four things every generative chatbot needs:

1. a model client behind one interface,
2. a system instruction,
3. bounded conversation history,
4. a refusal path when the model cannot answer.

It uses the *fake* extractive client by default so it runs with no download and no
key. Select a real backend when you have one:

    python project_b_llm_chatbot.py --backend local --model HuggingFaceTB/SmolLM2-360B-Instruct
    python project_b_llm_chatbot.py --backend api --consent   # reads CHATBOT_API_KEY

Run:
    python project_b_llm_chatbot.py --selftest
    python project_b_llm_chatbot.py --interactive

Read the code in this order: ``SYSTEM_PROMPT``, ``ChatSession``, ``main``.
"""

from __future__ import annotations

import argparse
import json
import sys
import time

from chatbot_core import (
    ABSTAIN_TEXT,
    SYSTEM_PROMPT,
    ConversationHistory,
    FakeModelClient,
    get_client,
    render_answer,
)
from chatbot_core.generation import Answer

# The system prompt is intentionally short: role, scope, refusal rule, format.
# Module 5 explains why long prompts fail differently from short ones.
COURSE_SYSTEM_PROMPT = (
    SYSTEM_PROMPT
    + "\nYou have no retrieved documents in this project. If you do not know, say so."
)


class ChatSession:
    """A single conversation with bounded history and explicit turn accounting."""

    def __init__(self, client, max_turns: int = 8, max_chars: int = 4000) -> None:
        self.client = client
        self.history = ConversationHistory(max_turns=max_turns, max_chars=max_chars)
        self.turns = 0

    def send(self, message: str) -> Answer:
        if not message.strip():
            raise ValueError("message cannot be empty")
        messages = [{"role": "system", "content": COURSE_SYSTEM_PROMPT}]
        messages.extend(self.history.messages())
        messages.append({"role": "user", "content": message})

        started = time.perf_counter()
        raw = self.client.complete(messages).strip()
        latency_ms = (time.perf_counter() - started) * 1000.0
        self.turns += 1

        text = self._unwrap(raw)
        abstained = not text or ABSTAIN_TEXT in text
        self.history.add_exchange(message, text or ABSTAIN_TEXT)
        return Answer(
            text=text or ABSTAIN_TEXT,
            abstained=abstained,
            model=getattr(self.client, "name", "unknown"),
            retrieved=0,
            top_score=0.0,
        )

    @staticmethod
    def _unwrap(raw: str) -> str:
        """Show the answer field when the model returned the structured object."""
        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw
        if isinstance(payload, dict) and isinstance(payload.get("answer"), str):
            return payload["answer"].strip()
        return raw


def selftest() -> int:
    session = ChatSession(FakeModelClient(), max_turns=4)
    failures = 0

    reply = session.send("What is the refund window for a workshop?")
    print("turn 1:", reply.text[:90])
    if reply.abstained:
        # The fake client has no retrieval in this project, so a refusal is the
        # correct behaviour and the test asserts exactly that.
        print("PASS  refused without evidence")
    else:
        print("FAIL  answered without evidence")
        failures += 1

    try:
        session.send("   ")
    except ValueError:
        print("PASS  rejected empty message")
    else:
        print("FAIL  empty message accepted")
        failures += 1

    for index in range(6):
        session.send(f"question {index}")
    if session.history.dropped_turns > 0:
        print(f"PASS  history bounded (dropped {session.history.dropped_turns} turns)")
    else:
        print("FAIL  history grew without bound")
        failures += 1

    print(f"\n{failures} failure(s)")
    return 0 if failures == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Project B: minimal LLM chatbot")
    parser.add_argument("--backend", default="fake", choices=["fake", "local", "api"])
    parser.add_argument("--model", default=None, help="local model id (local backend only)")
    parser.add_argument("--consent", action="store_true", help="required for the api backend")
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("message", nargs="*")
    args = parser.parse_args()

    if args.selftest:
        return selftest()

    if args.model:
        import os

        os.environ["CHATBOT_LOCAL_MODEL"] = args.model
    client = get_client(args.backend, consent_to_send=args.consent)
    session = ChatSession(client)
    print(f"backend: {client.name}")

    if args.interactive:
        print("Type 'quit' to exit.")
        for line in sys.stdin:
            if line.strip().lower() in {"quit", "exit"}:
                break
            if line.strip():
                print(render_answer(session.send(line)))
        return 0

    if not args.message:
        parser.error("provide a message, or use --interactive or --selftest")
    print(render_answer(session.send(" ".join(args.message))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
