"""Deterministic workflows: a state machine you can read, test, and bound.

An agent decides *what to do next*; a workflow decides *that for it*. For most
business tasks the workflow is the better engineering choice: the steps are
known, the failure modes are enumerable, the cost is fixed, and a test can walk
every edge.

This module provides:

``StateMachine``
    Named states, one handler per state, explicit transitions, optional guards,
    a transition ceiling, and an error policy (``stop``, ``retry``, ``goto``).
    The handler returns a :class:`StepOutcome`; nothing is inferred.

``compare``
    A helper that runs a scripted decision list through the same task and prints
    the difference in steps, predictability, and failure surface. Used in VD09 to
    make the trade-off concrete instead of rhetorical.

A workflow state is a dict. Handlers receive it, return a partial update plus the
next state name, and may raise :class:`WorkflowStop` to finish early with a
result. That is enough structure for a multi-step pipeline and little enough to
keep the control flow visible in one screen.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

State = dict[str, Any]


class WorkflowStop(Exception):
    """Raised by a handler to end the run early with a result."""

    def __init__(self, status: str, reason: str = "") -> None:
        self.status = status
        self.reason = reason
        super().__init__(reason or status)


class WorkflowError(RuntimeError):
    pass


@dataclass
class StepOutcome:
    next_state: str | None
    update: State = field(default_factory=dict)


Handler = Callable[[State], StepOutcome]


@dataclass
class WorkflowResult:
    status: str
    state: State
    visited: list[str]
    attempts: dict[str, int]
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "visited": list(self.visited),
            "attempts": dict(self.attempts),
            "error": self.error,
            "state": {k: v for k, v in self.state.items() if k != "documents"},
        }


class StateMachine:
    """Explicit states, explicit edges, a hard transition ceiling."""

    def __init__(self, name: str, max_transitions: int = 20) -> None:
        self.name = name
        self.max_transitions = max_transitions
        self.states: dict[str, Handler] = {}
        self.edges: dict[str, tuple[str, ...]] = {}
        self.on_error: dict[str, str] = {}

    def add_state(self, name: str, handler: Handler, *, next_states: tuple[str, ...] = ()) -> None:
        if name in self.states:
            raise ValueError(f"state {name!r} already defined")
        self.states[name] = handler
        self.edges[name] = next_states

    def on_error_goto(self, state: str, target: str) -> None:
        self.on_error[state] = target

    def validate(self, start: str) -> None:
        if start not in self.states:
            raise WorkflowError(f"start state {start!r} is not defined")
        for name, targets in self.edges.items():
            for target in targets:
                if target not in self.states and target not in ("__end__",):
                    raise WorkflowError(f"{name!r} -> unknown state {target!r}")

    def run(self, start: str, initial: State | None = None) -> WorkflowResult:
        self.validate(start)
        state: State = dict(initial or {})
        current = start
        visited: list[str] = []
        attempts: dict[str, int] = {}

        for _ in range(self.max_transitions):
            if current == "__end__":
                return WorkflowResult("done", state, visited, attempts)
            if current not in self.states:
                raise WorkflowError(f"reached undefined state {current!r}")

            visited.append(current)
            attempts[current] = attempts.get(current, 0) + 1
            try:
                outcome = self.states[current](state)
            except WorkflowStop as stop:
                state["result"] = state.get("result") or stop.reason
                return WorkflowResult(stop.status, state, visited, attempts)
            except Exception as exc:  # noqa: BLE001 - workflow owners decide recoverability
                target = self.on_error.get(current)
                if target is None:
                    return WorkflowResult("error", state, visited, attempts, f"{current}: {exc}")
                state.setdefault("errors", []).append(f"{current}: {type(exc).__name__}: {exc}")
                current = target
                continue

            if outcome.next_state is not None and current in self.edges:
                allowed = self.edges[current]
                if allowed and outcome.next_state not in allowed and outcome.next_state != "__end__":
                    raise WorkflowError(
                        f"illegal transition {current!r} -> {outcome.next_state!r}; "
                        f"allowed: {allowed}"
                    )
            state.update(outcome.update)
            if outcome.next_state is None:
                return WorkflowResult("done", state, visited, attempts)
            current = outcome.next_state

        return WorkflowResult("transition_limit", state, visited, attempts,
                              f"exceeded {self.max_transitions} transitions")

    def describe(self) -> str:
        lines = [f"workflow {self.name}"]
        for name, targets in self.edges.items():
            arrow = ", ".join(targets) or "(end)"
            lines.append(f"  {name} -> {arrow}")
        return "\n".join(lines)


@dataclass
class Comparison:
    workflow_steps: int
    agent_steps: int
    workflow_status: str
    agent_status: str
    note: str


def compare(workflow: StateMachine, start: str, initial: State,
            agent_steps: list[str]) -> Comparison:
    """Run a workflow and describe a scripted agent attempt on the same task."""

    result = workflow.run(start, initial)
    return Comparison(
        workflow_steps=len(result.visited),
        agent_steps=len(agent_steps),
        workflow_status=result.status,
        agent_status="final" if agent_steps else "no decision",
        note=(
            "The workflow has a fixed step count and no way to invent an action. "
            "The agent can skip steps, repeat them, or choose an action nobody "
            "planned for; that flexibility is the reason to accept its variance."
        ),
    )
