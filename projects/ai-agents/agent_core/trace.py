"""Structured traces: the difference between "it failed" and "here is why".

A trace is an append-only list of events. Each event has a kind, a name, a
timestamp, a duration, and a payload. The names used by this course are::

    run_start   run_end   model       tool_call   tool_result
    policy      approval    error     retry       stop

``Trace.summary()`` turns the events into the numbers you need for an evaluation
report: steps, tool calls, tool errors, retries, approvals, denials, tokens,
cost, and total latency.

Everything written to disk goes through :func:`redact`, which replaces values of
keys that look like credentials. Redaction is a last line of defence, not a
licence to put secrets in a trace in the first place.

The JSONL format is one JSON object per line, so a trace can be tailed, grepped,
and loaded by pandas without a custom parser.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "password",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "client_secret",
}


def redact(value: Any, depth: int = 0) -> Any:
    """Recursively replace suspicious values with ``***``."""

    if depth > 6:
        return "***"
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            if str(key).lower() in SENSITIVE_KEYS:
                clean[str(key)] = "***"
            else:
                clean[str(key)] = redact(item, depth + 1)
        return clean
    if isinstance(value, (list, tuple)):
        return [redact(item, depth + 1) for item in value]
    if isinstance(value, str) and value.startswith("sk-") and len(value) > 12:
        return "***"
    return value


@dataclass
class Event:
    kind: str
    name: str
    ts: float
    duration_ms: float = 0.0
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "name": self.name,
            "ts": round(self.ts, 6),
            "duration_ms": round(self.duration_ms, 3),
            "data": redact(self.data),
        }


class Trace:
    """Collect events for one run (or several, keyed by ``run_id``)."""

    def __init__(self, run_id: str = "run-1", clock=time.time) -> None:
        self.run_id = run_id
        self.events: list[Event] = []
        self.clock = clock

    def record(self, kind: str, name: str, duration_ms: float = 0.0, **data: Any) -> Event:
        event = Event(kind=kind, name=name, ts=self.clock(), duration_ms=duration_ms, data=data)
        self.events.append(event)
        return event

    def records(self, kind: str) -> list[Event]:
        return [event for event in self.events if event.kind == kind]

    def summary(self) -> dict[str, Any]:
        tool_calls = self.records("tool_call")
        tool_results = self.records("tool_result")
        errors = [e for e in tool_results if not e.data.get("ok", True)]
        # A retried call that eventually succeeded still had failed attempts;
        # count them, or the error rate hides exactly the flakiness it exists for.
        transient = sum(
            max(0, int(e.data.get("attempts", 1)) - 1)
            for e in tool_results
            if e.data.get("ok", True)
        )
        retries = self.records("retry")
        approvals = [e for e in self.records("approval") if e.data.get("approved")]
        denials = [e for e in self.records("approval") if e.data.get("approved") is False]
        policy_blocks = [e for e in self.records("policy") if not e.data.get("allowed", True)]
        model_events = self.records("model")
        tokens_in = sum(int(e.data.get("tokens_in", 0)) for e in model_events)
        tokens_out = sum(int(e.data.get("tokens_out", 0)) for e in model_events)
        cost = sum(float(e.data.get("cost_usd", 0.0)) for e in model_events)
        stop = self.records("stop")
        return {
            "run_id": self.run_id,
            "events": len(self.events),
            "model_calls": len(model_events),
            "steps": len(model_events),
            "tool_calls": len(tool_calls),
            "tool_errors": len(errors) + transient,
            "retries": len(retries),
            "approvals_granted": len(approvals),
            "approvals_denied": len(denials),
            "policy_blocks": len(policy_blocks),
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": round(cost, 6),
            "total_latency_ms": round(sum(e.duration_ms for e in self.events), 3),
            "stop_reason": stop[-1].data.get("reason") if stop else None,
        }

    def to_jsonl(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="\n") as handle:
            for event in self.events:
                handle.write(json.dumps({"run_id": self.run_id, **event.to_dict()}, sort_keys=True))
                handle.write("\n")
        return target

    @classmethod
    def from_jsonl(cls, path: str | Path) -> "Trace":
        events: list[Event] = []
        run_id = "unknown"
        with Path(path).open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                run_id = row.pop("run_id", run_id)
                events.append(
                    Event(
                        kind=row["kind"],
                        name=row["name"],
                        ts=float(row["ts"]),
                        duration_ms=float(row.get("duration_ms", 0.0)),
                        data=row.get("data", {}),
                    )
                )
        trace = cls(run_id=run_id)
        trace.events = events
        return trace

    def span(self, kind: str, name: str, **data: Any) -> Iterator[Event]:
        """Context manager that records one event with a measured duration."""

        return _Span(self, kind, name, data)


class _Span:
    def __init__(self, trace: Trace, kind: str, name: str, data: dict[str, Any]) -> None:
        self.trace = trace
        self.kind = kind
        self.name = name
        self.data = data
        self.start = 0.0
        self.event: Event | None = None

    def __enter__(self) -> Event:
        self.start = time.perf_counter()
        self.event = self.trace.record(self.kind, self.name, **self.data)
        return self.event

    def __exit__(self, *exc_info: Any) -> bool:
        if self.event is not None:
            self.event.duration_ms = (time.perf_counter() - self.start) * 1000.0
        return False
