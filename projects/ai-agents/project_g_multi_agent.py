"""Project G - researcher, analyst, and reviewer with a bounded revision loop.

Architecture
------------
::

    task
      |
      v
    researcher  --search corpus--> notes + citations (corpus access granted)
      |                              handoff 1
      v
    analyst     --no corpus-------> claims, each with [doc-id]
      |                              handoff 2
      v
    reviewer    --no corpus-------> accept | revise(issues) | reject
      |                              handoff 3
      +-- revise and rounds left --> analyst revises (researcher widens search)
      +-- accept -----------------> report
      +-- rounds exhausted -------> unresolved, reported honestly

Why three roles and not ten
---------------------------
Each handoff costs tokens, latency, and context. Two handoffs are enough to show
the shape: one role gathers evidence, one interprets it, one checks it. Adding
more roles adds coordination failure modes faster than it adds capability.

Controls that make this safe to run
-----------------------------------
* ``max_rounds`` bounds the revision loop; exhausting it is a status, not a hang.
* The analyst and reviewer are not given the corpus, so they cannot invent
  sources to satisfy the reviewer.
* The reviewer's issues are structured text, and every issue must be echoed in
  the next round's analysis header, so a revision cannot be silent.
* All messages go through a blackboard with a sender, so the transcript is the
  audit log.

The roles here are deterministic (no model). ``agent_core.multi_agent`` accepts
any callable with the same signature, so a model-backed reviewer can be dropped
in without changing the coordinator.

Run
---
    python project_g_multi_agent.py --selftest
    python project_g_multi_agent.py "How much notice is needed for leave?"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_core import (  # noqa: E402
    Role,
    RoleOutput,
    Team,
    Trace,
    analyst_role,
    researcher_role,
    reviewer_role,
    safe_corpus,
)
from agent_core.cli import Checks, base_parser  # noqa: E402

TASK = "How many days of leave can be carried over, and how much notice is needed?"


def build_team(corpus=None, *, required_citations: int = 2, max_rounds: int = 2,
               trace: Trace | None = None) -> Team:
    corpus = corpus or safe_corpus()
    roles = [
        researcher_role(corpus, k=3),
        analyst_role(),
        reviewer_role(required_citations=required_citations),
    ]
    return Team(roles, max_rounds=max_rounds, trace=trace)


def report_text(result) -> str:
    header = [
        f"# Research report ({result.status})",
        "",
        f"Rounds: {result.rounds}. Citations: {', '.join(result.citations) or 'none'}.",
        "",
    ]
    return "\n".join(header) + result.report


def demo(task: str) -> int:
    trace = Trace(run_id="team-demo")
    team = build_team(trace=trace)
    result = team.run(task)
    print(report_text(result))
    print("\n--- blackboard ---")
    for message in result.messages:
        print(f"{message.sender:10s} -> {message.recipient:11s} [{message.kind}] "
              f"{message.content.splitlines()[0][:90]}")
    print("\n--- trace ---")
    print(json.dumps(trace.summary(), indent=2))
    return 0 if result.status == "accepted" else 1


def selftest() -> int:
    checks = Checks("project G - multi-agent workflow")

    result = build_team().run(TASK)
    checks.check("accepted after revision", result.status == "accepted", result.status)
    checks.check("exactly two rounds", result.rounds == 2, f"rounds={result.rounds}")
    checks.check("two citations", len(result.citations) >= 2, str(result.citations))
    checks.check("report cites sources", "[hb-" in result.report, result.report[:120])
    checks.check("reviewer messages present",
                 any(m.kind == "review" for m in result.messages),
                 str([m.kind for m in result.messages]))
    checks.check("revision happened", any(m.kind == "review" and m.meta.get("verdict") == "revise"
                                          for m in result.messages))

    trace = Trace(run_id="bound")
    impossible = build_team(required_citations=9, max_rounds=1, trace=trace)
    stuck = impossible.run(TASK)
    checks.check("unreachable reviewer demand stays bounded",
                 stuck.status in ("unresolved", "rejected"), stuck.status)
    checks.check("rounds are bounded", stuck.rounds <= 2, f"rounds={stuck.rounds}")
    handoffs = [e for e in trace.records("handoff")]
    checks.check("every handoff traced", len(handoffs) == 3 * stuck.rounds, f"{len(handoffs)} handoffs")

    # The analyst must not be able to reach the corpus on its own.
    captured: dict[str, object] = {}

    def snooping_analyst(task: str, context) -> RoleOutput:
        captured["corpus"] = context.corpus
        return RoleOutput("- claim without a source", citations=[])

    team = Team(
        [
            researcher_role(safe_corpus()),
            Role("analyst", "look for evidence", snooping_analyst),
            reviewer_role(required_citations=2),
        ],
        max_rounds=0,
    )
    team.run(TASK)
    checks.check("analyst receives no corpus", captured["corpus"] is None, repr(captured["corpus"]))

    # A reviewer that always rejects cannot make the team loop forever.
    always = Role("reviewer", "reject everything",
                  lambda task, context: RoleOutput("no", verdict="reject", issues=["never good enough"]))
    stubborn = Team([researcher_role(safe_corpus()), analyst_role(), always], max_rounds=3)
    stubborn_result = stubborn.run(TASK)
    checks.check("rejection ends after the round budget",
                 stubborn_result.status == "rejected" and stubborn_result.rounds <= 4,
                 f"{stubborn_result.status} rounds={stubborn_result.rounds}")

    # Message accounting: three handoffs per round, no side channel.
    checks.check("blackboard has one message per handoff",
                 len(result.messages) == 3 * result.rounds,
                 f"{len(result.messages)} messages, {result.rounds} rounds")

    return checks.report()


def main() -> int:
    parser = base_parser("Research team with a reviewer veto")
    parser.add_argument("task", nargs="*", help="question; omit for the demo")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    return demo(" ".join(args.task) or TASK)


if __name__ == "__main__":
    raise SystemExit(main())
