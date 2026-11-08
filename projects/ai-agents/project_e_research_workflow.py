"""Project E - a multi-step research workflow with explicit source tracking.

This project is a workflow, not an autonomous agent, and that is the lesson. The
steps are known in advance, every step has one job, and the source ledger records
what was used, what was discarded, and why. Run it twice and you get the same
answer with the same step count.

Architecture
------------
::

    plan      question -> 2-4 search queries (content words only)
    retrieve  queries -> candidate documents, merged and deduplicated
    verify    candidates -> claims, each tied to a doc id, or a discard reason
    draft     claims -> answer with [doc-id] citations
    check     abstain if no citation; flag conflicts and quarantined text
    emit      answer + ledger + trace

The state machine is the control flow. There is no model deciding which step
comes next, so a failure is a bug in one step, not a surprise in the loop.

Source ledger
-------------
Every document the retriever returned is recorded once:

``used``         the claim built from it survived verification
``discarded``    with a reason (no relevant sentence, instruction-like, duplicate)
``quarantined``  instruction-like text was found and reported, never executed

Run
---
    python project_e_research_workflow.py --selftest
    python project_e_research_workflow.py "How much leave can be carried over?"
    python project_e_research_workflow.py --poisoned "What is the expense policy?"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_core import (  # noqa: E402
    Corpus,
    StateMachine,
    StepOutcome,
    WorkflowStop,
    find_instruction_like,
    poisoned_corpus,
    safe_corpus,
    tokenize,
)
from agent_core.cli import Checks, base_parser  # noqa: E402

MAX_CLAIMS = 3
MAX_WORDS = 120


def queries_for(question: str, limit: int = 3) -> list[str]:
    words = [word for word in tokenize(question) if len(word) > 2]
    if not words:
        return [question.strip()]
    # Keep the question's own word order, drop duplicates, cap the number of probes.
    ordered: list[str] = []
    for word in words:
        if word not in ordered:
            ordered.append(word)
    return [" ".join(ordered[:4]), " ".join(ordered[1:4])][:limit] or [question]


def split_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if len(part.strip()) > 30]


def best_sentence(text: str, terms: set[str]) -> tuple[str, int]:
    best, best_score = "", 0
    for sentence in split_sentences(text):
        score = len(terms & set(tokenize(sentence)))
        if score > best_score:
            best, best_score = sentence, score
    return best, best_score


def detect_number_conflicts(claims: list[dict[str, Any]]) -> list[str]:
    """Flag two claims that share context words but disagree on a quantity.

    Naive on purpose: it compares numbers around shared content words. It finds
    the obvious "25 days" vs "30 days" contradiction and nothing subtle; a real
    system needs entailment, and saying so is part of the lesson.
    """

    conflicts: list[str] = []
    for first in range(len(claims)):
        for second in range(first + 1, len(claims)):
            one, two = claims[first], claims[second]
            words_one, words_two = set(tokenize(one["claim"])), set(tokenize(two["claim"]))
            shared = words_one & words_two
            numbers_one = set(re.findall(r"\d+(?:\.\d+)?", one["claim"]))
            numbers_two = set(re.findall(r"\d+(?:\.\d+)?", two["claim"]))
            if len(shared) >= 2 and numbers_one and numbers_two and numbers_one != numbers_two:
                conflicts.append(
                    f"{one['doc_id']} says {sorted(numbers_one)} but {two['doc_id']} says "
                    f"{sorted(numbers_two)} about {', '.join(sorted(shared))}"
                )
    return conflicts


class ResearchWorkflow:
    """Six states, no autonomy, complete source accounting."""

    def __init__(self, corpus: Corpus, max_claims: int = MAX_CLAIMS) -> None:
        self.corpus = corpus
        self.max_claims = max_claims
        self.machine = StateMachine("research", max_transitions=8)
        self._build()

    def _build(self) -> None:
        machine = self.machine
        machine.add_state("plan", self._plan, next_states=("retrieve",))
        machine.add_state("retrieve", self._retrieve, next_states=("verify",))
        machine.add_state("verify", self._verify, next_states=("draft", "check"))
        machine.add_state("draft", self._draft, next_states=("check",))
        machine.add_state("check", self._check, next_states=("__end__",))
        machine.on_error_goto("retrieve", "check")
        machine.on_error_goto("verify", "check")

    # -- handlers --------------------------------------------------------
    def _plan(self, state: dict[str, Any]) -> StepOutcome:
        return StepOutcome("retrieve", {"queries": queries_for(state["question"])})

    def _retrieve(self, state: dict[str, Any]) -> StepOutcome:
        ledger: dict[str, dict[str, Any]] = {}
        for query in state["queries"]:
            for hit in self.corpus.search(query, k=3):
                entry = ledger.setdefault(
                    hit.doc.id,
                    {
                        "doc_id": hit.doc.id,
                        "title": hit.doc.title,
                        "trust": hit.doc.trust,
                        "source": hit.doc.source,
                        "score": 0.0,
                        "status": "candidate",
                        "reason": "",
                    },
                )
                entry["score"] = max(entry["score"], hit.score)
        state["ledger"] = ledger
        return StepOutcome("verify", {"candidates": len(ledger)})

    def _verify(self, state: dict[str, Any]) -> StepOutcome:
        terms = set(tokenize(state["question"]))
        claims: list[dict[str, Any]] = []
        for doc_id, entry in state["ledger"].items():
            doc = self.corpus.get(doc_id)
            if doc is None:
                entry["status"], entry["reason"] = "discarded", "document disappeared"
                continue
            flagged = find_instruction_like(doc.text)
            sentence, score = best_sentence(doc.text, terms)
            if score == 0:
                entry["status"], entry["reason"] = "discarded", "no sentence shares a query term"
                continue
            if entry["trust"] != "trusted":
                # Untrusted text can be quoted, but it never becomes the claim.
                entry["status"], entry["reason"] = "quarantined", "untrusted source"
                if flagged:
                    state.setdefault("warnings", []).append(
                        f"{doc_id} contains instruction-like text; treated as data"
                    )
                continue
            claims.append({"doc_id": doc_id, "claim": sentence, "score": score,
                           "trust": entry["trust"]})
            entry["status"], entry["reason"] = "used", "supports one claim"
            if flagged:
                state.setdefault("warnings", []).append(
                    f"{doc_id} contains instruction-like text; treated as data"
                )

        claims.sort(key=lambda item: (-item["score"], item["doc_id"]))
        claims = claims[: self.max_claims]
        for entry in state["ledger"].values():
            if entry["status"] == "used" and entry["doc_id"] not in {c["doc_id"] for c in claims}:
                entry["status"], entry["reason"] = "discarded", "beyond the claim limit"
        state["claims"] = claims
        state["conflicts"] = detect_number_conflicts(claims)
        return StepOutcome("draft", {"claim_count": len(claims)})

    def _draft(self, state: dict[str, Any]) -> StepOutcome:
        lines = [f"- {claim['claim']} [{claim['doc_id']}]" for claim in state["claims"]]
        text = "\n".join(lines)
        words = text.split()
        if len(words) > MAX_WORDS:
            text = " ".join(words[:MAX_WORDS]) + " ..."
        return StepOutcome("check", {"draft": text})

    def _check(self, state: dict[str, Any]) -> StepOutcome:
        if not state.get("claims"):
            raise WorkflowStop("abstained", "no trusted claim survived verification")
        citations = {claim["doc_id"] for claim in state["claims"]}
        draft = state.get("draft", "")
        if not all(f"[{doc_id}]" in draft for doc_id in citations):
            raise WorkflowStop("error", "draft is missing a citation")
        if state.get("warnings"):
            draft += "\n\nNote: " + "; ".join(state["warnings"])
        if state.get("conflicts"):
            draft += "\n\nConflicting quantities found: " + "; ".join(state["conflicts"])
        state["result"] = draft
        return StepOutcome("__end__", {"draft": draft})

    # -- public ----------------------------------------------------------
    def run(self, question: str):
        return self.machine.run("plan", {"question": question})

    def describe(self) -> str:
        return self.machine.describe()


def research(question: str, *, poisoned: bool = False):
    corpus = poisoned_corpus() if poisoned else safe_corpus()
    workflow = ResearchWorkflow(corpus)
    result = workflow.run(question)
    return result, workflow


def demo(question: str, poisoned: bool) -> int:
    result, workflow = research(question, poisoned=poisoned)
    print(workflow.describe())
    print(f"\nquestion: {question}")
    print(f"status  : {result.status}")
    print(f"steps   : {len(result.visited)} ({' -> '.join(result.visited)})")
    print("\nanswer:\n" + str(result.state.get("result", result.error or "(none)")))
    print("\nledger:")
    for entry in sorted(result.state.get("ledger", {}).values(), key=lambda row: row["doc_id"]):
        print(f"  {entry['doc_id']:6s} {entry['status']:11s} {entry['reason']}")
    return 0 if result.status == "done" else 1


def selftest() -> int:
    checks = Checks("project E - research workflow")

    result, workflow = research("How many days of paid leave can be carried over?")
    checks.check("workflow completes", result.status == "done", f"{result.status} {result.error}")
    checks.check("fixed steps", result.visited == ["plan", "retrieve", "verify", "draft", "check"],
                 str(result.visited))
    answer = str(result.state.get("result", ""))
    checks.check("answer cites a source", "[hb-01]" in answer, answer[:160])
    checks.check("answer contains the fact", "five days" in answer.lower(), answer)

    ledger = result.state.get("ledger", {})
    checks.check("ledger is complete", all(key in ledger for key in ("hb-01",)), str(list(ledger)))
    checks.check("used entries are recorded",
                 any(entry["status"] == "used" for entry in ledger.values()))
    checks.check("discarded entries have reasons",
                 all(entry["reason"] for entry in ledger.values() if entry["status"] == "discarded"))

    pets, _ = research("What is the office pets policy?")
    checks.check("abstains with no evidence", pets.status == "abstained", pets.status)

    poisoned_result, _ = research("Imported wiki page about the expense policy change", poisoned=True)
    warnings = " ".join(poisoned_result.state.get("warnings", []))
    checks.check("poisoned document quarantined", "instruction-like" in warnings, warnings)
    checks.check("no secret text in the answer", ".env" not in str(poisoned_result.state.get("result", "")))

    synthetic = [
        {"doc_id": "a-01", "claim": "Staff receive 25 days of paid leave per year."},
        {"doc_id": "a-02", "claim": "Staff receive 30 days of paid leave per year."},
    ]
    conflicts = detect_number_conflicts(synthetic)
    checks.check("conflict detection flags disagreeing numbers", len(conflicts) == 1, str(conflicts))

    same = [
        {"doc_id": "a-01", "claim": "Staff receive 25 days of paid leave per year."},
        {"doc_id": "a-02", "claim": "Staff receive 25 days of paid leave per year."},
    ]
    checks.check("conflict detection stays quiet when numbers agree",
                 detect_number_conflicts(same) == [])

    # Illegal transitions are a programming error, caught before a run.
    broken = StateMachine("broken")
    broken.add_state("start", lambda state: StepOutcome("nowhere"), next_states=("end",))
    broken.add_state("end", lambda state: StepOutcome(None))
    try:
        broken.run("start")
        illegal = False
    except Exception as exc:  # WorkflowError
        illegal = "illegal transition" in str(exc)
    checks.check("illegal transition is rejected", illegal)

    return checks.report()


def main() -> int:
    parser = base_parser("Multi-step research workflow with source tracking")
    parser.add_argument("question", nargs="*", help="question; omit for the demo")
    parser.add_argument("--poisoned", action="store_true", help="add the untrusted documents")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    question = " ".join(args.question) or "How many days of paid leave can be carried over?"
    return demo(question, args.poisoned)


if __name__ == "__main__":
    raise SystemExit(main())
