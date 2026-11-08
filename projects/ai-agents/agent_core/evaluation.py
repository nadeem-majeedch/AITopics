"""Evaluation harness: task success, tool errors, steps, tokens, cost, latency.

An agent demo is an anecdote. This module turns a folder of tasks into numbers
with a fixed definition of success, so a change to a prompt, a tool schema, or a
policy can be judged instead of admired.

Design choices that matter:

* **Success is defined before the run**, in the task: required substrings,
  required tools, forbidden tools, and a step ceiling. Judging afterwards is how
  demos become unfalsifiable.
* **Every case records why it failed.** A failing case returns a list of reasons
  (``missing: "25 days"``, ``used forbidden tool: shell``), not just a boolean.
* **Costs are explicit.** ``PRICES`` holds per-million-token prices for the
  models used in the course; local and scripted models cost zero, and a hosted
  price is passed in by the caller, never guessed.
* **Latency is measured, not invented.** Numbers move between runs; the report
  says so, and tests assert on deterministic counters instead.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

from .loop import RunResult
from .trace import Trace

# USD per million tokens, input/output. Only used for hosted models.
PRICES: dict[str, tuple[float, float]] = {
    "scripted-v1": (0.0, 0.0),
    "rule-planner-v1": (0.0, 0.0),
    "looping-v1": (0.0, 0.0),
    "local": (0.0, 0.0),
}

DEFAULT_HOSTED_PRICE = (0.0, 0.0)  # never invent a price for an unknown endpoint


@dataclass
class EvalTask:
    id: str
    prompt: str
    expect_substrings: tuple[str, ...] = ()
    expect_tools: tuple[str, ...] = ()
    forbid_tools: tuple[str, ...] = ()
    max_steps: int = 6
    max_tool_calls: int = 6
    note: str = ""


@dataclass
class CaseResult:
    task_id: str
    passed: bool
    failures: list[str] = field(default_factory=list)
    stop_reason: str = ""
    answer: str = ""
    steps: int = 0
    tool_calls: int = 0
    tool_errors: int = 0
    retries: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    trace_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvalReport:
    cases: list[CaseResult]
    split: str = "dev"
    meta: dict[str, Any] = field(default_factory=dict)

    def aggregate(self) -> dict[str, Any]:
        total = len(self.cases)
        if not total:
            return {"cases": 0}
        passed = sum(1 for case in self.cases if case.passed)
        tool_calls = sum(case.tool_calls for case in self.cases)
        tool_errors = sum(case.tool_errors for case in self.cases)
        latencies = [case.latency_ms for case in self.cases]
        return {
            "cases": total,
            "passed": passed,
            "success_rate": round(passed / total, 4),
            "tool_calls": tool_calls,
            "tool_errors": tool_errors,
            "tool_error_rate": round(tool_errors / tool_calls, 4) if tool_calls else 0.0,
            "retries": sum(case.retries for case in self.cases),
            "mean_steps": round(sum(case.steps for case in self.cases) / total, 2),
            "mean_tokens_in": round(sum(case.tokens_in for case in self.cases) / total, 1),
            "mean_tokens_out": round(sum(case.tokens_out for case in self.cases) / total, 1),
            "total_cost_usd": round(sum(case.cost_usd for case in self.cases), 6),
            "p50_latency_ms": round(statistics.median(latencies), 2),
            "p95_latency_ms": round(sorted(latencies)[max(0, int(0.95 * total) - 1)], 2),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "split": self.split,
            "meta": self.meta,
            "aggregate": self.aggregate(),
            "cases": [case.to_dict() for case in self.cases],
        }

    def to_json(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return target

    def to_markdown(self) -> str:
        agg = self.aggregate()
        header = (
            "| task | pass | stop | steps | tools | errors | tokens in/out | cost USD | latency ms |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"
        )
        rows = [
            f"| {case.task_id} | {'yes' if case.passed else 'no'} | {case.stop_reason} | "
            f"{case.steps} | {case.tool_calls} | {case.tool_errors} | "
            f"{case.tokens_in}/{case.tokens_out} | {case.cost_usd:.6f} | {case.latency_ms:.1f} |"
            for case in self.cases
        ]
        summary = (
            f"\n**{agg.get('passed', 0)}/{agg.get('cases', 0)} passed** "
            f"({agg.get('success_rate', 0):.1%}), tool error rate "
            f"{agg.get('tool_error_rate', 0):.1%}, mean steps {agg.get('mean_steps', 0)}, "
            f"p50 latency {agg.get('p50_latency_ms', 0)} ms, total cost "
            f"${agg.get('total_cost_usd', 0):.6f}.\n"
        )
        return header + "\n" + "\n".join(rows) + "\n" + summary


Runner = Callable[[EvalTask], RunResult]


def score_case(task: EvalTask, result: RunResult) -> CaseResult:
    """Compare one run against the task's pre-registered expectations."""

    failures: list[str] = []
    answer_lower = result.answer.lower()
    for expected in task.expect_substrings:
        if expected.lower() not in answer_lower:
            failures.append(f"missing expected text: {expected!r}")

    used = [event.name for event in result.trace.records("tool_call")]
    for required in task.expect_tools:
        if required not in used:
            failures.append(f"required tool not used: {required}")
    for forbidden in task.forbid_tools:
        if forbidden in used:
            failures.append(f"forbidden tool used: {forbidden}")
    if result.steps > task.max_steps:
        failures.append(f"steps {result.steps} > {task.max_steps}")
    if result.tool_calls > task.max_tool_calls:
        failures.append(f"tool calls {result.tool_calls} > {task.max_tool_calls}")

    summary = result.trace.summary()
    return CaseResult(
        task_id=task.id,
        passed=not failures,
        failures=failures,
        stop_reason=result.stop_reason,
        answer=result.answer[:400],
        steps=result.steps,
        tool_calls=result.tool_calls,
        tool_errors=summary["tool_errors"],
        retries=summary["retries"],
        tokens_in=summary["tokens_in"],
        tokens_out=summary["tokens_out"],
        cost_usd=summary["cost_usd"],
        latency_ms=summary["total_latency_ms"],
    )


def evaluate(tasks: Sequence[EvalTask], runner: Runner, *,
             split: str = "dev", trace_dir: str | Path | None = None,
             meta: dict[str, Any] | None = None) -> EvalReport:
    """Run every task and return a report. Traces are optional but recommended."""

    cases: list[CaseResult] = []
    directory = Path(trace_dir) if trace_dir else None
    for task in tasks:
        result = runner(task)
        case = score_case(task, result)
        if directory is not None:
            path = directory / f"{task.id}.jsonl"
            result.trace.to_jsonl(path)
            case.trace_path = str(path)
        cases.append(case)
    return EvalReport(cases=cases, split=split, meta=dict(meta or {}))


def load_tasks(path: str | Path) -> list[EvalTask]:
    """Load tasks from JSON so the evaluation set is data, not code."""

    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    tasks: list[EvalTask] = []
    for row in rows:
        tasks.append(
            EvalTask(
                id=str(row["id"]),
                prompt=str(row["prompt"]),
                expect_substrings=tuple(row.get("expect_substrings", ())),
                expect_tools=tuple(row.get("expect_tools", ())),
                forbid_tools=tuple(row.get("forbid_tools", ())),
                max_steps=int(row.get("max_steps", 6)),
                max_tool_calls=int(row.get("max_tool_calls", 6)),
                note=str(row.get("note", "")),
            )
        )
    return tasks


def save_tasks(tasks: Iterable[EvalTask], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps([asdict(task) for task in tasks], indent=2), encoding="utf-8"
    )
    return target


def merge_traces(paths: Sequence[str | Path]) -> Trace:
    """Combine per-case traces into one trace for a whole evaluation run."""

    merged = Trace(run_id="evaluation")
    for path in paths:
        part = Trace.from_jsonl(path)
        merged.events.extend(part.events)
    return merged
