"""Tools as ordinary Python functions, wrapped in a typed, auditable envelope.

A tool is a plain function plus a schema, a side-effect label, and a timeout.
The registry is the only code that calls tool functions, which is what makes
central enforcement possible:

* unknown or non-allowlisted tools never run;
* arguments are validated against the input schema before the call;
* return values are validated against the output schema before the agent sees
  them, so a broken tool cannot inject nonsense into the next step;
* exceptions become structured errors instead of crashing the run;
* retries are bounded and only applied to errors marked retryable;
* consequential tools pass through an approval callback first;
* every call produces one audit record.

Timeouts use a daemon thread and a queue. That is enough to stop *waiting* for a
stuck tool, which is what protects the loop's budget. It does not kill the
thread: Python cannot interrupt a blocked C call, so a truly hung tool keeps a
thread alive until it returns. The docs state this limitation rather than
pretending the timeout is a sandbox.
"""

from __future__ import annotations

import json
import queue
import threading
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable

from .policy import Policy
from .schema import SchemaError, validate

# Error codes the loop can reason about.
UNKNOWN_TOOL = "unknown_tool"
INVALID_ARGUMENTS = "invalid_arguments"
INVALID_OUTPUT = "invalid_output"
TOOL_ERROR = "tool_error"
TIMEOUT = "timeout"
APPROVAL_DENIED = "approval_denied"
POLICY_DENIED = "policy_denied"

SIDE_EFFECTS = ("none", "read", "write", "external", "execute")

RETRYABLE_CODES = {TIMEOUT, TOOL_ERROR}


@dataclass
class ToolResult:
    """What the loop receives for every attempted call."""

    name: str
    ok: bool
    value: Any = None
    error: dict[str, Any] | None = None
    attempts: int = 1
    duration_ms: float = 0.0

    @property
    def code(self) -> str | None:
        return None if self.error is None else str(self.error.get("code"))

    def observation(self, limit: int = 1200) -> str:
        """Compact text handed back to the model as the tool's observation."""

        if self.ok:
            if isinstance(self.value, (dict, list)):
                # JSON rather than repr: models and tests can parse it, and it
                # quotes strings correctly instead of using Python's single quotes.
                try:
                    text = json.dumps(self.value, ensure_ascii=False, default=str)
                except (TypeError, ValueError):
                    text = str(self.value)
            else:
                text = str(self.value)
        else:
            text = f"ERROR {self.error.get('code')}: {self.error.get('message')}"
            hint = (self.error or {}).get("hint")
            if hint:
                text += f" Hint: {hint}"
        return text if len(text) <= limit else text[: limit - 15] + " ...[truncated]"


@dataclass
class AuditRecord:
    """One line in the audit log. No secrets, no raw arguments by default."""

    tool: str
    ok: bool
    code: str | None
    attempts: int
    duration_ms: float
    argument_keys: tuple[str, ...] = ()
    approved: bool | None = None
    denied_reason: str | None = None


@dataclass
class ToolSpec:
    name: str
    description: str
    func: Callable[[dict[str, Any]], Any]
    input_schema: dict[str, Any]
    output_schema: dict[str, Any] | None = None
    side_effect: str = "none"
    requires_approval: bool = False
    timeout_s: float = 2.0
    retryable: bool = True

    def __post_init__(self) -> None:
        if self.side_effect not in SIDE_EFFECTS:
            raise ValueError(f"side_effect must be one of {SIDE_EFFECTS}")
        if not self.name.replace("_", "").isalnum() or not self.name.islower():
            raise ValueError("tool names must be lower_snake_case")

    def prompt_schema(self) -> dict[str, Any]:
        """The JSON-schema description a model is shown."""

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


class ApprovalRequest:
    def __init__(self, tool: ToolSpec, arguments: dict[str, Any]) -> None:
        self.tool = tool
        self.arguments = arguments

    def describe(self) -> str:
        return f"{self.tool.name}({', '.join(sorted(self.arguments))}) -> {self.tool.side_effect}"


Approver = Callable[[ApprovalRequest], bool]


class DenyAllApprover:
    """Default when no human is present: consequential actions are refused."""

    def __call__(self, request: ApprovalRequest) -> bool:  # pragma: no cover - trivial
        return False


class ScriptedApprover:
    """Deterministic approver for tests and demos."""

    def __init__(self, decisions: list[bool] | None = None, default: bool = False) -> None:
        self.decisions = list(decisions or [])
        self.default = default
        self.seen: list[str] = []

    def __call__(self, request: ApprovalRequest) -> bool:
        self.seen.append(request.describe())
        if self.decisions:
            return bool(self.decisions.pop(0))
        return self.default


class ConsoleApprover:
    """Interactive approver for a human-driven run. Never used by tests."""

    def __call__(self, request: ApprovalRequest) -> bool:
        answer = input(f"Approve tool call? {request.describe()} [y/N] ").strip().lower()
        return answer in ("y", "yes")


@dataclass
class ToolRegistry:
    """Registry plus enforcement point for every tool call."""

    tools: dict[str, ToolSpec] = field(default_factory=dict)
    approver: Approver | None = None
    policy: Policy | None = None
    allowed: set[str] | None = None
    audit: list[AuditRecord] = field(default_factory=list)
    clock: Callable[[], float] = time.perf_counter
    slow_threshold_ms: float = 0.0
    simulated_tools: dict[str, float] = field(default_factory=dict)

    def register(self, tool: ToolSpec) -> ToolSpec:
        if tool.name in self.tools:
            raise ValueError(f"tool {tool.name!r} already registered")
        self.tools[tool.name] = tool
        return tool

    def allow(self, *names: str) -> None:
        """Replace the allowlist. Tools not listed can never be called."""

        self.allowed = set(names)

    def get(self, name: str) -> ToolSpec | None:
        if self.allowed is not None and name not in self.allowed:
            return None
        return self.tools.get(name)

    def names(self) -> list[str]:
        listed = self.allowed if self.allowed is not None else set(self.tools)
        return sorted(n for n in listed if n in self.tools)

    def prompt_tools(self) -> list[dict[str, Any]]:
        return [self.tools[name].prompt_schema() for name in self.names()]

    def _record(self, record: AuditRecord) -> None:
        self.audit.append(record)

    def call(
        self,
        name: str,
        arguments: Any,
        *,
        max_attempts: int = 2,
        deadline: float | None = None,
        approval: bool | None = None,
    ) -> ToolResult:
        started = self.clock()
        spec = self.get(name)
        if spec is None:
            result = ToolResult(
                name=name,
                ok=False,
                error={
                    "code": UNKNOWN_TOOL,
                    "message": f"tool {name!r} is not available to this agent",
                    "hint": f"available tools: {', '.join(self.names()) or 'none'}",
                    "retryable": False,
                },
            )
            self._record(AuditRecord(name, False, UNKNOWN_TOOL, 1, 0.0))
            return result

        if not isinstance(arguments, dict):
            result = ToolResult(
                name=name,
                ok=False,
                error={
                    "code": INVALID_ARGUMENTS,
                    "message": f"arguments must be an object, got {type(arguments).__name__}",
                    "retryable": False,
                },
            )
            self._record(AuditRecord(name, False, INVALID_ARGUMENTS, 1, 0.0))
            return result

        problems = validate(arguments, spec.input_schema)
        if problems:
            result = ToolResult(
                name=name,
                ok=False,
                error={
                    "code": INVALID_ARGUMENTS,
                    "message": "arguments do not match the tool schema",
                    "details": problems,
                    "hint": "Fix the listed fields and call the tool again with valid JSON.",
                    "retryable": False,
                },
            )
            self._record(AuditRecord(name, False, INVALID_ARGUMENTS, 1, 0.0, tuple(sorted(arguments))))
            return result

        # Policy is enforced here as well as in the loop, so a direct
        # registry.call() cannot skip the allowlist, path containment, or the
        # capability flags. Defence in depth, not duplicated convenience.
        if self.policy is not None:
            decision = self.policy.check(name, arguments, spec)
            if not decision.allowed:
                result = ToolResult(
                    name=name,
                    ok=False,
                    error={
                        "code": POLICY_DENIED,
                        "message": decision.reason,
                        "hint": "Policy is not negotiable. Choose an allowed action.",
                        "retryable": False,
                    },
                )
                self._record(AuditRecord(name, False, POLICY_DENIED, 1, 0.0, tuple(sorted(arguments))))
                return result

        approved: bool | None = approval
        if spec.requires_approval and approval is None:
            approver = self.approver or DenyAllApprover()
            approved = bool(approver(ApprovalRequest(spec, arguments)))
        if spec.requires_approval:
            granted = bool(approved)
            if not granted:
                result = ToolResult(
                    name=name,
                    ok=False,
                    error={
                        "code": APPROVAL_DENIED,
                        "message": "a human did not approve this action",
                        "hint": "Do not retry the same action; ask the user or take a read-only path.",
                        "retryable": False,
                    },
                )
                self._record(
                    AuditRecord(name, False, APPROVAL_DENIED, 1, 0.0, tuple(sorted(arguments)), False)
                )
                return result

        attempts = 0
        last: ToolResult | None = None
        max_attempts = max(1, int(max_attempts))
        while attempts < max_attempts:
            attempts += 1
            if deadline is not None and self.clock() >= deadline:
                last = ToolResult(
                    name=name,
                    ok=False,
                    error={
                        "code": TIMEOUT,
                        "message": "run deadline reached before the tool could start",
                        "retryable": False,
                    },
                    attempts=attempts,
                    duration_ms=(self.clock() - started) * 1000.0,
                )
                break

            value, error = self._execute(spec, arguments)
            if error is None:
                output_problems = validate(value, spec.output_schema) if spec.output_schema else []
                if output_problems:
                    error = {
                        "code": INVALID_OUTPUT,
                        "message": f"tool {name!r} returned data that does not match its output schema",
                        "details": output_problems,
                        "hint": "The tool is faulty. Do not retry; report the failure.",
                        "retryable": False,
                    }
                else:
                    elapsed = (self.clock() - started) * 1000.0
                    result = ToolResult(name, True, value, None, attempts, elapsed)
                    self._record(
                        AuditRecord(
                            name, True, None, attempts, elapsed, tuple(sorted(arguments)), approved
                        )
                    )
                    return result

            elapsed = (self.clock() - started) * 1000.0
            last = ToolResult(name, False, None, error, attempts, elapsed)
            retryable = bool(spec.retryable and error.get("retryable"))
            if not retryable or attempts >= max_attempts:
                break
            if deadline is not None and self.clock() >= deadline:
                break

        assert last is not None
        self._record(
            AuditRecord(
                name,
                False,
                last.code,
                last.attempts,
                last.duration_ms,
                tuple(sorted(arguments)),
                approved,
            )
        )
        return last

    def _execute(self, spec: ToolSpec, arguments: dict[str, Any]) -> tuple[Any, dict[str, Any] | None]:
        """Run one attempt, converting every failure into an error dict."""

        simulated = self.simulated_tools.get(spec.name)
        if simulated is not None:
            # Deterministic latency for the evaluation harness.
            time.sleep(0)  # yield without consuming wall-clock budget
            if simulated > spec.timeout_s * 1000.0:
                return None, {
                    "code": TIMEOUT,
                    "message": f"tool {spec.name!r} exceeded its {spec.timeout_s:.2f}s timeout",
                    "retryable": True,
                }
            return spec.func(arguments), None

        box: queue.Queue[tuple[Any, BaseException | None]] = queue.Queue(maxsize=1)

        def target() -> None:
            try:
                box.put((spec.func(arguments), None))
            except BaseException as exc:  # noqa: BLE001 - the boundary must catch everything
                box.put((None, exc))

        thread = threading.Thread(target=target, name=f"tool-{spec.name}", daemon=True)
        thread.start()
        try:
            value, exc = box.get(timeout=max(0.001, spec.timeout_s))
        except queue.Empty:
            return None, {
                "code": TIMEOUT,
                "message": f"tool {spec.name!r} exceeded its {spec.timeout_s:.2f}s timeout",
                "retryable": True,
            }

        if exc is None:
            return value, None
        if isinstance(exc, ToolFailure):
            return None, {
                "code": TOOL_ERROR,
                "message": str(exc),
                "retryable": exc.retryable,
            }
        return None, {
            "code": TOOL_ERROR,
            "message": f"tool raised {type(exc).__name__}: {exc}",
            "retryable": False,
            "trace": traceback.format_exc(limit=2).splitlines()[-1],
        }


class ToolFailure(Exception):
    """Raise from a tool to return a controlled, possibly retryable error."""

    def __init__(self, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


def make_tool(
    name: str,
    description: str,
    func: Callable[[dict[str, Any]], Any],
    input_schema: dict[str, Any],
    *,
    output_schema: dict[str, Any] | None = None,
    side_effect: str = "none",
    requires_approval: bool = False,
    timeout_s: float = 2.0,
    retryable: bool = True,
) -> ToolSpec:
    """Decorator-free constructor, useful when tools are built at runtime."""

    return ToolSpec(
        name=name,
        description=description,
        func=func,
        input_schema=input_schema,
        output_schema=output_schema,
        side_effect=side_effect,
        requires_approval=requires_approval,
        timeout_s=timeout_s,
        retryable=retryable,
    )


def tool(
    name: str,
    description: str,
    input_schema: dict[str, Any],
    *,
    output_schema: dict[str, Any] | None = None,
    side_effect: str = "none",
    requires_approval: bool = False,
    timeout_s: float = 2.0,
    retryable: bool = True,
) -> Callable[[Callable[[dict[str, Any]], Any]], ToolSpec]:
    """Decorator that turns a normal function into a :class:`ToolSpec`."""

    def wrap(func: Callable[[dict[str, Any]], Any]) -> ToolSpec:
        return make_tool(
            name,
            description,
            func,
            input_schema,
            output_schema=output_schema,
            side_effect=side_effect,
            requires_approval=requires_approval,
            timeout_s=timeout_s,
            retryable=retryable,
        )

    return wrap
