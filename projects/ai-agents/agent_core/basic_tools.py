"""Reference tools: safe arithmetic, unit conversion, date arithmetic.

These are the smallest useful tools for teaching, and they are deliberately
boring. Two properties matter more than the maths:

* **No ``eval``.** Arithmetic is parsed with ``ast`` and only a fixed set of node
  types is accepted. A model cannot smuggle ``__import__`` into an expression.
* **Bounded.** Expression length, exponent size, and result magnitude are capped,
  so "compute 9**9**9" returns an error instead of consuming the machine.

The functions are pure and side-effect free, which is why they can be retried
without thinking about idempotency. Tools with real effects need that argument
made explicitly — see the approval gate in :mod:`agent_core.tools`.
"""

from __future__ import annotations

import ast
import datetime as dt
import operator
from typing import Any, Callable

from .schema import object_schema
from .tools import ToolFailure, ToolSpec

NUMBER = {"type": "number"}

_BIN_OPS: dict[type[ast.AST], Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

UNIT_FAMILY = {"km": "length", "mi": "length", "m": "length", "ft": "length",
               "c": "temperature", "f": "temperature",
               "kg": "mass", "lb": "mass"}
TO_BASE = {"km": 1000.0, "m": 1.0, "mi": 1609.344, "ft": 0.3048,
           "kg": 1.0, "lb": 0.45359237}


def _eval(node: ast.AST, depth: int = 0) -> float:
    if depth > 20:
        raise ToolFailure("expression is nested too deeply")
    if isinstance(node, ast.Expression):
        return _eval(node.body, depth + 1)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ToolFailure("only numeric constants are allowed")
        return float(node.value)
    if isinstance(node, ast.BinOp):
        op = _BIN_OPS.get(type(node.op))
        if op is None:
            raise ToolFailure("operator not allowed")
        left = _eval(node.left, depth + 1)
        right = _eval(node.right, depth + 1)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ToolFailure("exponent is limited to 100")
        if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)) and right == 0:
            raise ToolFailure("division by zero")
        return op(left, right)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _eval(node.operand, depth + 1)
        return value if isinstance(node.op, ast.UAdd) else -value
    raise ToolFailure(f"unsupported syntax: {type(node).__name__}")


def safe_arithmetic(expression: str) -> float:
    """Evaluate an arithmetic expression without ``eval``."""

    if not isinstance(expression, str):
        raise ToolFailure("expression must be a string")
    if len(expression) > 200:
        raise ToolFailure("expression is longer than 200 characters")
    if not expression.strip():
        raise ToolFailure("expression is empty")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ToolFailure(f"cannot parse expression: {exc.msg}") from exc
    value = _eval(tree)
    if abs(value) > 1e12:
        raise ToolFailure("result is larger than the tool's range")
    return float(value)


def unit_convert(value: float, source: str, target: str) -> float:
    source, target = source.lower(), target.lower()
    if source not in UNIT_FAMILY or target not in UNIT_FAMILY:
        raise ToolFailure(f"unknown unit: {source!r} or {target!r}")
    if UNIT_FAMILY[source] != UNIT_FAMILY[target]:
        raise ToolFailure(f"cannot convert {source} to {target}")
    if source == target:
        return float(value)
    if UNIT_FAMILY[source] == "temperature":
        celsius = float(value) if source == "c" else (float(value) - 32) * 5 / 9
        return celsius if target == "c" else celsius * 9 / 5 + 32
    return float(value) * TO_BASE[source] / TO_BASE[target]


def days_between(start: str, end: str) -> int:
    """Inclusive-free day difference between two ISO dates."""

    try:
        start_date = dt.date.fromisoformat(start)
        end_date = dt.date.fromisoformat(end)
    except ValueError as exc:
        raise ToolFailure(f"dates must be YYYY-MM-DD: {exc}") from exc
    return (end_date - start_date).days


def calculate_spec(*, timeout_s: float = 1.0) -> ToolSpec:
    return ToolSpec(
        name="calculate",
        description="Evaluate arithmetic (numbers and + - * / % ** parentheses).",
        input_schema=object_schema(
            {
                "expression": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 200,
                    "description": "Arithmetic expression, for example (12 * 3) + 4.",
                }
            }
        ),
        output_schema=object_schema({"value": NUMBER}),
        func=lambda arguments: {"value": round(safe_arithmetic(arguments["expression"]), 10)},
        timeout_s=timeout_s,
    )


def convert_spec(*, timeout_s: float = 1.0) -> ToolSpec:
    return ToolSpec(
        name="convert_units",
        description="Convert between km, m, mi, ft, c, f, kg, and lb.",
        input_schema=object_schema(
            {
                "value": {"type": "number", "minimum": -1_000_000, "maximum": 1_000_000},
                "from_unit": {"type": "string", "enum": sorted(UNIT_FAMILY)},
                "to_unit": {"type": "string", "enum": sorted(UNIT_FAMILY)},
            }
        ),
        output_schema=object_schema({"value": NUMBER, "unit": {"type": "string"}}),
        func=lambda arguments: {
            "value": round(
                unit_convert(arguments["value"], arguments["from_unit"], arguments["to_unit"]), 4
            ),
            "unit": arguments["to_unit"].lower(),
        },
        timeout_s=timeout_s,
    )


def days_between_spec(*, timeout_s: float = 1.0) -> ToolSpec:
    return ToolSpec(
        name="days_between",
        description="Number of days between two ISO dates (YYYY-MM-DD).",
        input_schema=object_schema(
            {
                "start": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
                "end": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
            }
        ),
        output_schema=object_schema({"days": {"type": "integer"}}),
        func=lambda arguments: {"days": days_between(arguments["start"], arguments["end"])},
        timeout_s=timeout_s,
    )


def all_specs() -> list[ToolSpec]:
    return [calculate_spec(), convert_spec(), days_between_spec()]


def add(a: int, b: int) -> int:  # tiny helper used by tests and docs
    return a + b


def unused(*_: Any) -> None:  # pragma: no cover - keeps linters quiet about Any import
    return None
