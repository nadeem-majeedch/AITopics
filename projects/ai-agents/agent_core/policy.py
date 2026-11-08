"""Policy enforcement: the gate between a proposed action and a real effect.

Policy is evaluated *by the harness*, not by the model. The model proposes; the
policy decides. Every rule here is deny-by-default, because a default-allow
agent is one prompt injection away from being someone else's agent.

The four questions a call has to answer:

1. Is this tool in the allowlist for this run?
2. Is this side effect permitted (no network, no shell, no writes outside the
   sandbox)?
3. Does every path argument resolve inside an allowed root, after symlinks are
   followed?
4. Does a human need to approve this specific call?

``Policy.check`` returns a :class:`PolicyDecision`; it never raises for a normal
denial. Raising is reserved for programming errors, so a denial is data the loop
can log, explain, and recover from.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

PATH_KEYS = ("path", "file", "filename", "directory", "dir", "target")

# Names that must never be read by an agent tool, even inside a sandbox root.
SECRET_PATTERNS = (
    r"(^|/)\.env$",
    r"\.env\.",
    r"(^|/)id_(rsa|ed25519|ecdsa)$",
    r"\.pem$",
    r"(^|/)\.ssh(/|$)",
    r"(^|/)secrets?(/|$)",
    r"(^|/)credentials",
    r"(^|/)\.aws(/|$)",
    r"(^|/)\.git(/|$)",
)


class PolicyViolation(PermissionError):
    """Raised only when policy is used as an assertion, not as a gate."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str = ""
    requires_approval: bool = False
    resolved_paths: tuple[str, ...] = ()

    def __bool__(self) -> bool:
        return self.allowed


def _looks_secret(path: str) -> bool:
    lowered = path.replace("\\", "/").lower()
    return any(re.search(pattern, lowered) for pattern in SECRET_PATTERNS)


@dataclass
class Policy:
    """Capability limits for one agent run."""

    allowed_tools: frozenset[str]
    roots: tuple[Path, ...] = field(default_factory=tuple)
    allow_network: bool = False
    allow_write: bool = False
    allow_shell: bool = False
    require_approval: frozenset[str] = field(default_factory=frozenset)
    max_read_bytes: int = 64_000
    max_write_bytes: int = 16_000
    max_args_bytes: int = 8_000
    denied_tools: frozenset[str] = field(default_factory=frozenset)

    @classmethod
    def strict(cls) -> "Policy":
        """Read-only, no network, no shell, no writes. The safe default."""

        return cls(allowed_tools=frozenset(), allow_network=False, allow_write=False)

    @classmethod
    def for_sandbox(
        cls,
        root: Path,
        tools: Iterable[str],
        *,
        allow_write: bool = False,
        require_approval: Iterable[str] = (),
    ) -> "Policy":
        return cls(
            allowed_tools=frozenset(tools),
            roots=(Path(root).resolve(),),
            allow_network=False,
            allow_write=allow_write,
            allow_shell=False,
            require_approval=frozenset(require_approval),
        )

    def resolve(self, raw_path: str) -> Path:
        """Resolve a path argument and prove it is inside an allowed root."""

        if not self.roots:
            raise PolicyViolation("no filesystem root is configured for this run")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise PolicyViolation("path must be a non-empty string")
        if "\x00" in raw_path:
            raise PolicyViolation("path contains a null byte")

        root_list = [root.resolve() for root in self.roots]
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = root_list[0] / candidate
        resolved = candidate.resolve(strict=False)

        inside = any(resolved == root or root in resolved.parents for root in root_list)
        if not inside:
            raise PolicyViolation(f"path escapes the sandbox: {raw_path!r}")
        if _looks_secret(str(resolved)):
            raise PolicyViolation("path looks like a credential or secret file")

        # Reject symlinks that leave the root even when the link itself is inside.
        if resolved.is_symlink():
            target = os.path.realpath(resolved)
            if not any(Path(target) == root or root in Path(target).parents for root in root_list):
                raise PolicyViolation("symlink points outside the sandbox")
        return resolved

    def check(self, tool_name: str, arguments: dict[str, Any], tool: Any | None = None) -> PolicyDecision:
        """Decide whether a proposed call may proceed."""

        if tool_name in self.denied_tools:
            return PolicyDecision(False, f"tool {tool_name!r} is explicitly denied")
        if tool_name not in self.allowed_tools:
            return PolicyDecision(False, f"tool {tool_name!r} is not in this run's allowlist")
        if tool is None:
            return PolicyDecision(False, f"tool {tool_name!r} is not registered")

        side_effect = getattr(tool, "side_effect", "none")
        if side_effect == "external" and not self.allow_network:
            return PolicyDecision(False, "external calls are disabled for this run")
        if side_effect == "execute" and not self.allow_shell:
            return PolicyDecision(False, "command execution is disabled for this run")
        if side_effect == "write" and not self.allow_write:
            return PolicyDecision(False, "write access is disabled for this run")

        encoded = repr(arguments)
        if len(encoded.encode("utf-8")) > self.max_args_bytes:
            return PolicyDecision(False, "arguments exceed the configured size budget")

        resolved: list[str] = []
        for key in PATH_KEYS:
            raw = arguments.get(key)
            if isinstance(raw, str):
                try:
                    resolved.append(str(self.resolve(raw)))
                except PolicyViolation as exc:
                    return PolicyDecision(False, str(exc.reason))

        needs_approval = tool_name in self.require_approval or bool(
            getattr(tool, "requires_approval", False)
        )
        return PolicyDecision(
            True,
            "allowed",
            requires_approval=needs_approval,
            resolved_paths=tuple(resolved),
        )


def describe(policy: Policy) -> str:
    """Human-readable policy summary, used in agent cards and audit logs."""

    roots = ", ".join(str(root) for root in policy.roots) or "(none)"
    flags = [
        f"network={'on' if policy.allow_network else 'off'}",
        f"write={'on' if policy.allow_write else 'off'}",
        f"shell={'on' if policy.allow_shell else 'off'}",
    ]
    approval = ", ".join(sorted(policy.require_approval)) or "(none)"
    return (
        f"tools={sorted(policy.allowed_tools)}\n"
        f"roots={roots}\n"
        f"{' '.join(flags)}\n"
        f"approval_required={approval}\n"
        f"max_read={policy.max_read_bytes}B max_write={policy.max_write_bytes}B"
    )
