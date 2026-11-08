"""Bounded multi-agent collaboration: roles, handoffs, and a reviewer veto.

Multi-agent systems are not free. Every handoff costs tokens and latency, loses
context, and creates a new place for instructions to hide. The pattern worth
teaching is therefore narrow:

* **few roles, each with one job and one output schema**;
* **a shared blackboard**, so no agent talks to another behind the coordinator's
  back and every message is traceable to a sender;
* **bounded rounds**, so the researcher/analyst/reviewer loop cannot spin;
* **a reviewer with a veto**, whose issues are structured and must be addressed;
* **no tool escalation**: a role can only use tools that the coordinator granted
  it, even when the role's prose asks for more.

The default roles are deterministic so the workflow is testable offline. A role
is just a callable ``(task, context) -> RoleOutput``, so a model-backed role can
be swapped in without touching the coordinator.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Callable, Sequence

from .retrieval import Corpus, Hit, find_instruction_like
from .trace import Trace

VERDICTS = ("accept", "revise", "reject")


@dataclass
class RoleOutput:
    content: str
    citations: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    verdict: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "citations": list(self.citations),
            "issues": list(self.issues),
            "verdict": self.verdict,
            "meta": dict(self.meta),
        }


@dataclass
class Role:
    name: str
    goal: str
    handler: Callable[[str, "Context"], RoleOutput]
    allowed_tools: tuple[str, ...] = ()
    max_output_chars: int = 2000
    can_search: bool = False  # only roles granted retrieval receive the corpus


@dataclass
class Message:
    sender: str
    recipient: str
    content: str
    kind: str = "note"
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Context:
    """What a role may see. Deliberately narrower than "everything"."""

    task: str
    corpus: Corpus | None = None
    notes: list[str] = field(default_factory=list)
    analysis: str = ""
    issues: list[str] = field(default_factory=list)
    round: int = 1
    max_notes: int = 6


class Blackboard:
    """Append-only message log shared by the team."""

    def __init__(self) -> None:
        self.messages: list[Message] = []

    def post(self, sender: str, recipient: str, content: str, *,
             kind: str = "note", **meta: Any) -> Message:
        message = Message(sender, recipient, content, kind, meta)
        self.messages.append(message)
        return message

    def by(self, role: str) -> list[Message]:
        return [message for message in self.messages if message.sender == role]

    def transcript(self, limit: int = 12) -> str:
        lines = []
        for message in self.messages[-limit:]:
            lines.append(f"{message.sender} -> {message.recipient} [{message.kind}]: {message.content}")
        return "\n".join(lines)


@dataclass
class TeamResult:
    status: str
    report: str
    rounds: int
    messages: list[Message]
    citations: list[str]
    issues: list[str] = field(default_factory=list)
    trace: Trace | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "rounds": self.rounds,
            "citations": list(self.citations),
            "issues": list(self.issues),
            "messages": len(self.messages),
            "report": self.report,
        }


class Team:
    """Coordinator that runs researcher → analyst → reviewer, with revision."""

    def __init__(self, roles: Sequence[Role], *, max_rounds: int = 2,
                 trace: Trace | None = None) -> None:
        self.roles = {role.name: role for role in roles}
        missing = {"researcher", "analyst", "reviewer"} - set(self.roles)
        if missing:
            raise ValueError(f"team is missing roles: {sorted(missing)}")
        self.max_rounds = max(0, int(max_rounds))
        self.trace = trace or Trace(run_id="team")

    def run(self, task: str, corpus: Corpus | None = None) -> TeamResult:
        board = Blackboard()
        context = Context(task=task, corpus=corpus)
        self.trace.record("run_start", "team", task=task[:160])

        report = ""
        verdict = "reject"
        rounds = 0

        for round_index in range(1, self.max_rounds + 2):
            rounds = round_index
            context.round = round_index
            context.issues = []
            # A reviewer asking for more evidence is the most common revision.
            # Each round widens the search by one document, within a hard cap.
            context.max_notes = min(1 + round_index - 1, 3)
            self.trace.record("handoff", "researcher", round=round_index)
            research = self._invoke("researcher", context)
            board.post("researcher", "analyst", research.content, kind="notes",
                       citations=research.citations)

            context.notes = [research.content]
            self.trace.record("handoff", "analyst", round=round_index)
            analysis = self._invoke("analyst", context)
            board.post("analyst", "reviewer", analysis.content, kind="analysis",
                       citations=analysis.citations)

            context.analysis = analysis.content
            self.trace.record("handoff", "reviewer", round=round_index)
            review = self._invoke("reviewer", context)
            board.post("reviewer", "coordinator", review.content, kind="review",
                       verdict=review.verdict, issues=review.issues)

            verdict = review.verdict or "reject"
            report = analysis.content
            if verdict == "accept":
                break
            if round_index > self.max_rounds:
                break
            context.issues = list(review.issues)

        status = "accepted" if verdict == "accept" else (
            "rejected" if verdict == "reject" else "unresolved"
        )
        citations = sorted({cite for message in board.messages for cite in message.meta.get("citations", [])})
        issues = [issue for message in board.messages if message.kind == "review" for issue in message.meta.get("issues", [])]
        self.trace.record("run_end", "team", status=status, rounds=rounds, messages=len(board.messages))
        return TeamResult(status, report, rounds, board.messages, citations, issues, self.trace)

    def _invoke(self, role_name: str, context: Context) -> RoleOutput:
        role = self.roles[role_name]
        # A role sees the corpus only if the coordinator granted it. The analyst
        # cannot quietly start searching to justify its own conclusion.
        scoped = context if role.can_search else replace(context, corpus=None)
        output = role.handler(scoped.task, scoped)
        if len(output.content) > role.max_output_chars:
            output.content = output.content[: role.max_output_chars] + "..."
        return output


# --------------------------------------------------------------------------
# Deterministic default roles
# --------------------------------------------------------------------------

def researcher_role(corpus: Corpus, *, k: int = 3) -> Role:
    """Search, quote, cite. Never summarise without a source id."""

    def handler(task: str, context: Context) -> RoleOutput:
        hits: list[Hit] = corpus.search(task, k=min(max(1, context.max_notes), k))
        if not hits:
            return RoleOutput("No matching documents.", citations=[], meta={"hits": 0})
        lines: list[str] = []
        citations: list[str] = []
        flagged: list[str] = []
        for hit in hits:
            flagged.extend(find_instruction_like(hit.doc.text))
            lines.append(f"{hit.cite()}: {hit.snippet}")
            citations.append(hit.doc.id)
        if flagged:
            # Quarantine, do not delete: the reviewer must see what arrived.
            lines.append(
                "QUARANTINED (instruction-like text, treated as data): "
                + " | ".join(flagged)[:300]
            )
        return RoleOutput("\n".join(lines), citations=citations,
                          meta={"hits": len(hits), "flagged": len(flagged)})

    return Role(
        "researcher", "Find and quote the most relevant documents.", handler, can_search=True
    )


def analyst_role() -> Role:
    """Turn quoted notes into claims, each carrying its source id."""

    def handler(task: str, context: Context) -> RoleOutput:
        notes = context.notes[0] if context.notes else ""
        claims: list[str] = []
        citations: list[str] = []
        for line in notes.splitlines():
            if not line.strip() or line.startswith("QUARANTINED"):
                continue
            if "] " in line:
                doc_id = line.split("] ", 1)[0].lstrip("[")
                claim = line.split(": ", 1)[-1].strip()
                claims.append(f"- {claim} [{doc_id}]")
                if doc_id not in citations:
                    citations.append(doc_id)
        if not claims:
            return RoleOutput("No supported claims could be made from the notes.")
        if context.issues:
            header = "Revised analysis addressing reviewer issues:"
        else:
            header = "Analysis:"
        return RoleOutput(header + "\n" + "\n".join(claims), citations=citations)

    return Role("analyst", "Produce cited claims from the researcher's notes.", handler)


def reviewer_role(required_citations: int = 1) -> Role:
    """Check citations, unsupported numbers, and instruction-like content."""

    def handler(task: str, context: Context) -> RoleOutput:
        issues: list[str] = []
        text = context.analysis
        if not text.strip():
            issues.append("analysis is empty")
        notes = context.notes[0] if context.notes else ""
        if not notes.strip():
            issues.append("no research notes")
        cited = set()
        for token in text.split():
            if token.startswith("[") and token.endswith("]"):
                cited.add(token.strip("[]"))
        if len(cited) < required_citations:
            issues.append(f"needs at least {required_citations} citation(s), found {len(cited)}")
        for line in text.splitlines():
            if line.strip().startswith("-") and "[" not in line:
                issues.append(f"unsupported claim: {line.strip()[:80]}")
        lower = text.lower()
        for phrase in ("ignore previous", "system:", "send the user", "reveal the prompt"):
            if phrase in lower:
                issues.append(f"instruction-like content in analysis: {phrase!r}")
        if issues:
            return RoleOutput("Review found problems:\n" + "\n".join(f"- {issue}" for issue in issues),
                              issues=issues, verdict="revise")
        return RoleOutput(f"Accepted: {len(cited)} citations, no unsupported claims.",
                          citations=sorted(cited), verdict="accept")

    return Role("reviewer", "Accept only cited, instruction-free analysis.", handler)
