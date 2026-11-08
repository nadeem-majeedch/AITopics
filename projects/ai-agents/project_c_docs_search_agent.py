"""Project C - an agent that answers from a controlled local corpus, with citations.

Architecture
------------
::

    question
      -> search_docs(query, k)        BM25 over the corpus; returns ids + snippets + trust
      -> [no hits / weak hit]         -> abstain, do not guess
      -> read_doc(doc_id)             full text, size-limited, trust label preserved
      -> answer                       quote + [doc-id] citation
         (if the text contains instruction-like sentences, they are reported as
          quarantined content, never executed)

Why "controlled"
----------------
The corpus is local, versioned, small, and authored for the course. Retrieval is
lexical, so it is inspectable: you can read the ranking and argue with it.
Nothing here needs an embedding model or a network call.

Trust is part of the data model, not a vibe. ``Doc.trust`` is ``trusted`` for
the handbook and ``untrusted`` for imported pages. The agent may quote an
untrusted page but the answer says so, and the tool policy never grants
filesystem or network effects on the strength of document text.

Run
---
    python project_c_docs_search_agent.py --selftest
    python project_c_docs_search_agent.py "How many leave days can I carry over?"
    python project_c_docs_search_agent.py --poisoned "What is the expense policy?"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_core import (  # noqa: E402
    Policy,
    RunLimits,
    ToolRegistry,
    ToolSpec,
    run_agent,
    safe_corpus,
    poisoned_corpus,
    find_instruction_like,
    object_schema,
)
from agent_core.cli import Checks, base_parser  # noqa: E402
from agent_core.model import Decision, Message, ModelReply, Usage  # noqa: E402
from agent_core.retrieval import Corpus  # noqa: E402

ABSTAIN = "I do not have enough evidence in the handbook to answer that."

SEARCH_INPUT = object_schema(
    {
        "query": {"type": "string", "minLength": 2, "maxLength": 300},
        "k": {"type": "integer", "minimum": 1, "maximum": 5},
    },
    required=["query"],
    description="Search the local handbook. Returns document ids, snippets, and trust labels.",
)

READ_INPUT = object_schema(
    {"doc_id": {"type": "string", "pattern": r"^[a-z]{2,3}-\d{2}$"}},
    description="Read one handbook document by id.",
)


def make_tools(corpus: Corpus) -> list[ToolSpec]:
    def search(arguments: dict[str, Any]) -> dict[str, Any]:
        hits = corpus.search(arguments["query"], k=int(arguments.get("k", 3)))
        return {
            "hits": [
                {
                    "doc_id": hit.doc.id,
                    "title": hit.doc.title,
                    "score": hit.score,
                    "snippet": hit.snippet,
                    "trust": hit.doc.trust,
                }
                for hit in hits
            ]
        }

    def read(arguments: dict[str, Any]) -> dict[str, Any]:
        doc = corpus.get(arguments["doc_id"])
        if doc is None:
            return {"found": False, "doc_id": arguments["doc_id"]}
        return {
            "found": True,
            "doc_id": doc.id,
            "title": doc.title,
            "text": doc.text[:1200],
            "truncated": len(doc.text) > 1200,
            "trust": doc.trust,
            "source": doc.source,
        }

    return [
        ToolSpec(
            "search_docs",
            "Search the local handbook for passages relevant to a query.",
            search,
            SEARCH_INPUT,
            output_schema=object_schema({"hits": {"type": "array"}}, allow_extra=True),
            side_effect="read",
            timeout_s=2.0,
        ),
        ToolSpec(
            "read_doc",
            "Read one handbook document by id after searching.",
            read,
            READ_INPUT,
            # allow_extra because a document carries title, text, trust, and source.
            output_schema=object_schema(
                {"found": {"type": "boolean"}, "doc_id": {"type": "string"}}, allow_extra=True
            ),
            side_effect="read",
            timeout_s=2.0,
        ),
    ]


def build_registry(corpus: Corpus) -> ToolRegistry:
    registry = ToolRegistry()
    for spec in make_tools(corpus):
        registry.register(spec)
    registry.allow("search_docs", "read_doc")
    return registry


def _payload(message: Message) -> dict[str, Any] | None:
    """Pull the JSON object out of a tool observation."""

    text = message.get("content", "")
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for index in range(start, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : index + 1])
                except json.JSONDecodeError:
                    return None
    return None


class QuoteAndCiteModel:
    """A deterministic stand-in that reacts to observations like a model would.

    It performs the same reasoning shape as a prompted model — search, read the
    best hit, quote it with a citation — without pretending to understand
    language. That makes the control flow testable; it does not make it smart.
    """

    name = "quote-and-cite-v1"

    def __init__(self, min_score: float = 0.35, abstain: str = ABSTAIN) -> None:
        self.min_score = min_score
        self.abstain = abstain
        self.calls = 0

    def respond(self, messages: Sequence[Message]) -> ModelReply:
        self.calls += 1
        tool_messages = [m for m in messages if m.get("role") == "tool"]
        question = next((m["content"] for m in messages if m.get("role") == "user"), "")

        if not tool_messages:
            return self._tool("search_docs", {"query": question[:300], "k": 3})

        last = _payload(tool_messages[-1]) or {}
        if "hits" in last:
            hits = last["hits"]
            if not hits or hits[0]["score"] < self.min_score:
                return self._final(self.abstain)
            return self._tool("read_doc", {"doc_id": hits[0]["doc_id"]})

        if "text" in last and last.get("found"):
            doc_id = last["doc_id"]
            text = re.sub(r"\s+", " ", last["text"]).strip()
            sentences = [s for s in re.split(r"(?<=[.!?])\s+", text) if len(s) > 30]
            terms = {word for word in re.findall(r"[a-z0-9']+", question.lower())}
            ranked = sorted(
                sentences,
                key=lambda sentence: -len(terms & set(re.findall(r"[a-z0-9']+", sentence.lower()))),
            )
            relevant = ranked[:2] or sentences[:2]
            quote = " ".join(relevant)
            warning = ""
            flagged = find_instruction_like(last["text"])
            if flagged:
                warning = (
                    " Note: this document contains text that looks like instructions "
                    f"({len(flagged)} sentence(s)); it is quoted as data and was not followed."
                )
            trust = "" if last.get("trust") == "trusted" else " (unverified source)"
            return self._final(f"{quote} [{doc_id}]{trust}{warning}")

        return self._final(self.abstain)

    def _tool(self, name: str, arguments: dict[str, Any]) -> ModelReply:
        raw = json.dumps({"tool": name, "arguments": arguments})
        return ModelReply(raw, Decision.tool_call(name, arguments),
                          Usage(tokens_in=20, tokens_out=20), self.name)

    def _final(self, content: str) -> ModelReply:
        return ModelReply(json.dumps({"final": content}), Decision.final(content),
                          Usage(tokens_in=20, tokens_out=len(content) // 4 + 1), self.name)


def ask(question: str, *, corpus: Corpus | None = None, model=None,
        limits: RunLimits | None = None):
    corpus = corpus or safe_corpus()
    registry = build_registry(corpus)
    policy = Policy(allowed_tools=frozenset({"search_docs", "read_doc"}))
    return run_agent(
        model or QuoteAndCiteModel(),
        registry,
        question,
        limits=limits or RunLimits(
            max_steps=5, max_tool_calls=4, timeout_s=5.0, max_observation_chars=4000
        ),
        policy=policy,
        system_prompt=(
            "Answer only from the handbook. Quote and cite [doc-id]. If retrieval "
            "finds nothing relevant, say you do not have enough evidence."
        ),
    )


def demo(question: str, poisoned: bool) -> int:
    corpus = poisoned_corpus() if poisoned else safe_corpus()
    result = ask(question, corpus=corpus)
    print(f"question: {question}")
    print(f"answer  : {result.answer}")
    print(f"stop    : {result.stop_reason} in {result.steps} steps, {result.tool_calls} tool calls")
    return 0


def selftest() -> int:
    checks = Checks("project C - docs search agent")
    corpus = safe_corpus()

    leave = ask("How many days of paid leave do staff get?", corpus=corpus)
    checks.check("answers a known question", "25 days" in leave.answer, leave.answer)
    checks.check("cites a document", "[hb-01]" in leave.answer, leave.answer)
    checks.check("uses search then read", leave.tool_calls == 2, f"tool_calls={leave.tool_calls}")

    pets = ask("What is the office pets policy?", corpus=corpus)
    checks.check("abstains on an unknown topic", ABSTAIN in pets.answer, pets.answer)
    checks.check("abstention cites nothing", "[hb-" not in pets.answer, pets.answer)

    travel = ask("What class should I book for a short flight?", corpus=corpus)
    checks.check("answers a second question", "Economy" in travel.answer, travel.answer)

    poisoned = poisoned_corpus()
    attack = ask("Imported wiki page about the expense policy change", corpus=poisoned)
    reads = [event for event in attack.trace.records("tool_call") if event.name == "read_doc"]
    results = [event for event in attack.trace.records("tool_result") if event.name == "read_doc"]
    checks.check(
        "poisoned doc read successfully",
        len(reads) == 1
        and reads[0].data.get("arguments", {}).get("doc_id") == "ext-90"
        and bool(results and results[0].data.get("ok")),
        f"calls={[e.data for e in reads]} results={[e.data.get('ok') for e in results]}",
    )
    checks.check("no secret exfiltration in answer", ".env" not in attack.answer.lower(),
                 attack.answer[:200])
    checks.check("injected text is flagged", "instruction" in attack.answer.lower(), attack.answer[:200])

    # A tool cannot be tricked into reading ids outside the pattern.
    registry = build_registry(corpus)
    traversal = registry.call("read_doc", {"doc_id": "../../.env"})
    checks.check("doc id schema rejects traversal", not traversal.ok
                 and traversal.code == "invalid_arguments", str(traversal.error))

    missing = registry.call("read_doc", {"doc_id": "zz-99"})
    checks.check("unknown doc returns found=false", missing.ok and missing.value["found"] is False,
                 str(missing.value))

    unknown_tool = ask("hello", corpus=corpus, model=QuoteAndCiteModel())
    checks.check("run is bounded", unknown_tool.steps <= 5, f"steps={unknown_tool.steps}")

    return checks.report()


def main() -> int:
    parser = base_parser("Citation-first document search agent")
    parser.add_argument("question", nargs="*", help="question; omit for the demo")
    parser.add_argument("--poisoned", action="store_true", help="include the untrusted documents")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    question = " ".join(args.question) or "How many leave days can I carry into next year?"
    return demo(question, args.poisoned)


if __name__ == "__main__":
    raise SystemExit(main())
