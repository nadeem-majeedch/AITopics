"""A small, dependency-free JSON Schema subset.

Tools need typed arguments. Without validation, a model that answers
``{"count": "five"}`` reaches your function and fails somewhere deep inside it,
where the error message no longer mentions the model or the tool. This module
checks a value against a schema *before* the tool runs and returns every problem
with a JSON-pointer-like path, so the failure can be fed back to the model as a
usable observation.

Supported keywords
------------------
``type`` (object, array, string, integer, number, boolean, null, or a list)
``properties``, ``required``, ``additionalProperties`` (bool only)
``items``, ``minItems``, ``maxItems``
``enum``, ``const``
``minimum``, ``maximum``
``minLength``, ``maxLength``, ``pattern`` (taken from ``re``)

Anything else (``title``, ``description``, ``default``, ``format``, ``$schema``)
is accepted and ignored. That is deliberate: a model sees ``description`` in the
prompt, but the description is documentation, not a constraint.

Deliberately unsupported: ``$ref``, ``allOf``/``anyOf``/``oneOf``, remote
references, and recursive schemas. Agent tool schemas should be flat enough to
read, and a validator you cannot reason about is not a security control.
"""

from __future__ import annotations

import re
from typing import Any

_TYPES = {"object", "array", "string", "integer", "number", "boolean", "null"}


class SchemaError(ValueError):
    """Raised by :meth:`Schema.validate` when a value does not match."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = list(errors)
        super().__init__("; ".join(self.errors))


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (list, tuple)):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _matches_type(value: Any, expected: str) -> bool:
    actual = _json_type(value)
    if expected == "number":
        return actual in ("number", "integer")
    if expected == "integer":
        # ``True`` is an int in Python; it is not an integer in JSON Schema.
        return actual == "integer"
    return actual == expected


def _preview(value: Any, limit: int = 40) -> str:
    text = repr(value)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def validate(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    """Return a list of human-readable problems; an empty list means valid."""

    errors: list[str] = []
    if not isinstance(schema, dict):
        return [f"{path}: schema must be an object"]

    expected = schema.get("type")
    if expected is not None:
        options = expected if isinstance(expected, list) else [expected]
        unknown = [opt for opt in options if opt not in _TYPES]
        if unknown:
            return [f"{path}: schema uses unsupported type {unknown[0]!r}"]
        if not any(_matches_type(value, opt) for opt in options):
            got = _json_type(value)
            wanted = " or ".join(str(opt) for opt in options)
            return [f"{path}: expected {wanted}, got {got} ({_preview(value)})"]

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: must equal {_preview(schema['const'])}")

    if "enum" in schema:
        allowed = list(schema["enum"])
        if value not in allowed:
            errors.append(f"{path}: must be one of {allowed}, got {_preview(value)}")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength {schema['minLength']}")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: longer than maxLength {schema['maxLength']}")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(f"{path}: does not match pattern {schema['pattern']!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: {value} is below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: {value} is above maximum {schema['maximum']}")

    if isinstance(value, (list, tuple)):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: has {len(value)} items, minimum is {schema['minItems']}")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: has {len(value)} items, maximum is {schema['maxItems']}")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(validate(item, item_schema, f"{path}[{index}]"))

    if isinstance(value, dict):
        properties = schema.get("properties") or {}
        if not isinstance(properties, dict):
            errors.append(f"{path}: properties must be an object")
            properties = {}
        for name in schema.get("required", []) or []:
            if name not in value:
                errors.append(f"{path}.{name}: required property is missing")
        for name, sub_schema in properties.items():
            if name in value:
                errors.extend(validate(value[name], sub_schema, f"{path}.{name}"))
        extra = [key for key in value if key not in properties]
        if extra and schema.get("additionalProperties", True) is False:
            for key in extra:
                errors.append(
                    f"{path}.{key}: unexpected property (additionalProperties is false)"
                )

    return errors


def schema_ok(value: Any, schema: dict[str, Any]) -> bool:
    return not validate(value, schema)


class Schema:
    """Convenience wrapper so a schema can validate and raise in one call."""

    def __init__(self, definition: dict[str, Any], name: str = "value") -> None:
        self.definition = definition
        self.name = name

    def errors(self, value: Any) -> list[str]:
        return validate(value, self.definition)

    def validate(self, value: Any) -> Any:
        errors = self.errors(value)
        if errors:
            raise SchemaError(errors)
        return value

    def is_valid(self, value: Any) -> bool:
        return not self.errors(value)


def object_schema(
    properties: dict[str, dict[str, Any]],
    required: list[str] | None = None,
    *,
    allow_extra: bool = False,
    description: str | None = None,
) -> dict[str, Any]:
    """Build a strict object schema. Strict by default, on purpose.

    ``additionalProperties: false`` turns a typo (``{"citty": "Paris"}``) into an
    error the model can see, instead of silently ignoring the argument and
    producing a confident wrong answer.
    """

    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "required": list(required if required is not None else properties.keys()),
        "additionalProperties": bool(allow_extra),
    }
    if description:
        schema["description"] = description
    return schema


STRING = {"type": "string"}
NUMBER = {"type": "number"}
INTEGER = {"type": "integer"}
BOOLEAN = {"type": "boolean"}
