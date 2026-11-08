"""Project B - a model-powered agent with two safe tools.

Architecture
------------
::

    user task
        |
        v
    model.respond(messages) -> {"tool": ..., "arguments": {...}} | {"final": ...}
        |
        v
    policy.check(tool, args)          allowlist + capability + path rules
        |
        v
    registry.call(...)                schema -> execute -> output schema -> retry
        |
        v
    observation appended to messages  (labelled untrusted data)
        |
        v
    ... loop until final, or a limit is hit

Tools
-----
``days_between``  ISO dates in, integer days out
``calculate``     arithmetic with an AST evaluator, no ``eval``

Both are pure, so retries are safe. Neither has an external effect, so no
approval gate is required here; Project F adds one for writes.

Three model options
-------------------
``--selftest`` / default   deterministic scripted replies (offline, free)
``--local``                optional ``transformers`` model on your machine
``--hosted --allow-network`` optional OpenAI-compatible endpoint

The loop, the tools, the schemas, and the limits are identical in all three
cases. That is the point of putting the model behind a decision protocol.

Run
---
    python project_b_two_tools_agent.py --selftest
    python project_b_two_tools_agent.py
    python project_b_two_tools_agent.py --hosted --allow-network "how many days from 2026-01-01 to 2026-02-01?"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_core import (  # noqa: E402
    Policy,
    RepeatingModel,
    RunLimits,
    ScriptedModel,
    ToolRegistry,
    run_agent,
    transcript_text,
)
from agent_core.basic_tools import calculate_spec, days_between_spec  # noqa: E402
from agent_core.cli import Checks, base_parser, choose_model  # noqa: E402
from agent_core.model import Model  # noqa: E402

TASK = "How many days are there from 2026-11-03 to 2026-12-25, and what is 3 times that?"

PLAN = [
    {"tool": "days_between", "arguments": {"start": "2026-11-03", "end": "2026-12-25"}},
    {"tool": "calculate", "arguments": {"expression": "52 * 3"}},
    {"final": "There are 52 days from 2026-11-03 to 2026-12-25, and 3 x 52 = 156."},
]


def build_registry(allowed: tuple[str, ...] = ("days_between", "calculate")) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(days_between_spec())
    registry.register(calculate_spec())
    registry.allow(*allowed)
    return registry


def build_policy(allowed: tuple[str, ...] = ("days_between", "calculate")) -> Policy:
    return Policy(allowed_tools=frozenset(allowed))


def build_model(args: argparse.Namespace | None = None) -> Model:
    """Return the requested model, falling back to the offline script."""

    if args is not None:
        chosen = choose_model(args)
        if chosen is not None:
            return chosen
    return ScriptedModel(PLAN)


def run(task: str = TASK, model: Model | None = None, *,
        limits: RunLimits | None = None, policy: Policy | None = None,
        registry: ToolRegistry | None = None):
    registry = registry or build_registry()
    policy = policy if policy is not None else build_policy()
    limits = limits or RunLimits(max_steps=6, max_tool_calls=4, timeout_s=5.0, max_tokens=4000)
    return run_agent(
        model or ScriptedModel(PLAN),
        registry,
        task,
        limits=limits,
        policy=policy,
        system_prompt=(
            "You answer questions using two tools. Prefer one tool call per fact. "
            "When you have both numbers, reply with a final answer that states them."
        ),
    )


def demo() -> int:
    result = run()
    print(transcript_text(result.messages))
    print("\n--- result ---")
    print(json.dumps(result.summary(), indent=2))
    print("\n--- trace summary ---")
    print(json.dumps(result.trace.summary(), indent=2))
    return 0 if result.ok else 1


def selftest() -> int:
    checks = Checks("project B - two-tool agent")

    result = run()
    checks.check("agent finishes", result.stop_reason == "final", result.stop_reason)
    checks.check("both tools used", result.tool_calls == 2, f"tool_calls={result.tool_calls}")
    checks.check("answer has the day count", "52" in result.answer, result.answer)
    checks.check("answer has the product", "156" in result.answer, result.answer)

    # 1. Invalid arguments come back as a structured error the model can fix.
    fixing_model = ScriptedModel(
        [
            {"tool": "days_between", "arguments": {"start": "03-11-2026", "end": "2026-12-25"}},
            {"tool": "days_between", "arguments": {"start": "2026-11-03", "end": "2026-12-25"}},
            {"final": "52 days."},
        ]
    )
    fixed = run(model=fixing_model)
    invalid = [
        event for event in fixed.trace.records("tool_result") if event.data.get("code") == "invalid_arguments"
    ]
    checks.check("bad date format rejected", len(invalid) == 1, f"{len(invalid)} invalid results")
    checks.check("agent recovered after fixing arguments", fixed.ok, fixed.stop_reason)

    # 2. A tool the policy forbids is refused before execution.
    narrow = run(policy=Policy(allowed_tools=frozenset({"days_between"})))
    blocked = [event for event in narrow.trace.records("policy") if not event.data.get("allowed", True)]
    checks.check("policy blocked the second tool", len(blocked) >= 1, f"{len(blocked)} blocks")
    checks.check("run still ends", narrow.stop_reason in ("final", "step_limit", "repeated_action"),
                 narrow.stop_reason)

    # 3. Loop detection.
    looping = RepeatingModel("days_between", {"start": "2026-11-03", "end": "2026-12-25"})
    loop_run = run(model=looping, limits=RunLimits(max_steps=10, max_tool_calls=10, max_repeats=2))
    checks.check("repeated action stops the run", loop_run.stop_reason == "repeated_action",
                 loop_run.stop_reason)
    checks.check("loop was cut before step limit", loop_run.steps < 10, f"steps={loop_run.steps}")

    # 4. Step ceiling.
    limited = run(limits=RunLimits(max_steps=1, max_tool_calls=1))
    checks.check("step ceiling honoured", limited.steps == 1 and limited.stop_reason == "step_limit",
                 f"{limited.steps} / {limited.stop_reason}")

    # 5. Unknown tool.
    unknown_model = ScriptedModel([{"tool": "shell", "arguments": {"cmd": "whoami"}}])
    unknown = run(model=unknown_model, limits=RunLimits(max_steps=2))
    tool_events = [event for event in unknown.trace.records("policy") if event.name == "shell"]
    checks.check("unknown tool never executed", unknown.tool_calls == 0 and bool(tool_events),
                 f"tool_calls={unknown.tool_calls}")

    # 6. Unparseable reply is retried once, then the run gives up.
    broken = ScriptedModel(["not json at all", "still not json"])
    failed = run(model=broken, limits=RunLimits(max_steps=4))
    checks.check("invalid decisions stop the run", failed.stop_reason == "invalid_decisions",
                 failed.stop_reason)

    # 7. Tool output is presented as untrusted data.
    checks.check(
        "observation is labelled untrusted",
        any("UNTRUSTED TOOL OUTPUT" in message["content"] for message in result.messages),
    )

    # 8. Trace contains the audit trail we need.
    kinds = {event.kind for event in result.trace.events}
    checks.check("trace has model, tool, and stop events",
                 {"model", "tool_call", "tool_result", "stop"} <= kinds, str(sorted(kinds)))

    return checks.report()


def main() -> int:
    parser = base_parser("Model-powered two-tool agent")
    parser.add_argument("task", nargs="*", help="task text; omit for the demo")
    args = parser.parse_args()
    if args.selftest:
        return selftest()

    model = build_model(args)
    task = " ".join(args.task) if args.task else TASK
    result = run(task, model=model)
    print(transcript_text(result.messages))
    print("\n" + json.dumps(result.summary(), indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
