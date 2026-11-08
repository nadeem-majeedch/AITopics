"""Sandboxes and a shell simulator that never executes anything.

There are three separate ideas in this file and they should not be confused:

``SandboxFS``
    A real directory on disk, reached only through a :class:`Policy`. Every
    path is resolved and checked before it is opened, reads are size-limited,
    writes are atomic and size-limited, and secret-looking names are refused.

``VirtualFileSystem``
    An in-memory tree for demonstrations that must not touch the disk at all.

``SimulatedShell``
    A *parser*. It accepts a tiny allowlist of read-only commands, refuses shell
    metacharacters, and returns synthetic output. It never imports ``subprocess``
    and never runs a program. Its purpose is to show, safely, why handing a model
    an unrestricted shell is a design failure — the demo command
    ``tidy-up: ; rm -rf /`` is rejected, and you can read the rejection instead
    of losing a filesystem.
"""

from __future__ import annotations

import os
import shlex
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from .policy import Policy, PolicyViolation


class SandboxError(PermissionError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


@dataclass
class SandboxFS:
    """Filesystem access limited to ``policy.roots``."""

    policy: Policy
    max_read_bytes: int = 64_000
    max_write_bytes: int = 16_000

    def _path(self, raw: str) -> Path:
        try:
            return self.policy.resolve(raw)
        except PolicyViolation as exc:
            raise SandboxError(exc.reason) from exc

    def read_text(self, raw: str) -> str:
        path = self._path(raw)
        if not path.exists():
            raise SandboxError(f"no such file: {raw!r}")
        if not path.is_file():
            raise SandboxError(f"not a regular file: {raw!r}")
        size = path.stat().st_size
        limit = min(self.max_read_bytes, self.policy.max_read_bytes)
        if size > limit:
            raise SandboxError(f"file is {size} bytes, over the {limit}-byte read limit")
        return path.read_text(encoding="utf-8", errors="replace")

    def write_text(self, raw: str, text: str) -> int:
        if not self.policy.allow_write:
            raise SandboxError("writes are disabled for this run")
        path = self._path(raw)
        limit = min(self.max_write_bytes, self.policy.max_write_bytes)
        data = text.encode("utf-8")
        if len(data) > limit:
            raise SandboxError(f"write is {len(data)} bytes, over the {limit}-byte limit")
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(data)
        os.replace(temporary, path)
        return len(data)

    def list_dir(self, raw: str = ".") -> list[str]:
        path = self._path(raw)
        if not path.exists():
            raise SandboxError(f"no such directory: {raw!r}")
        if not path.is_dir():
            raise SandboxError(f"not a directory: {raw!r}")
        return sorted(entry.name + ("/" if entry.is_dir() else "") for entry in path.iterdir())

    def exists(self, raw: str) -> bool:
        try:
            return self._path(raw).exists()
        except SandboxError:
            return False


class VirtualFileSystem:
    """In-memory files for demos that should not touch disk."""

    def __init__(self, files: dict[str, str] | None = None) -> None:
        self.files: dict[str, str] = dict(files or {})

    def read(self, path: str) -> str:
        if path not in self.files:
            raise SandboxError(f"no such file: {path!r}")
        return self.files[path]

    def write(self, path: str, text: str) -> None:
        self.files[path] = text

    def list(self) -> list[str]:
        return sorted(self.files)


@contextmanager
def demo_root(prefix: str = "agent-demo-") -> Iterator[Path]:
    """Create a throwaway directory with the fixtures the labs expect."""

    root = Path(tempfile.mkdtemp(prefix=prefix))
    try:
        (root / "notes").mkdir()
        (root / "readme.md").write_text(
            "# Demo workspace\n\nThis folder exists only for the agent labs.\n"
            "- notes/plan.txt\n- notes/budget.csv\n",
            encoding="utf-8",
        )
        (root / "notes" / "plan.txt").write_text(
            "Week 1: outline the task.\nWeek 2: collect sources.\nWeek 3: write the report.\n",
            encoding="utf-8",
        )
        (root / "notes" / "budget.csv").write_text(
            "item,amount\nlicence,120\nhosting,80\n", encoding="utf-8"
        )
        yield root
    finally:
        # Best-effort cleanup; the directory is under the OS temp dir.
        for path in sorted(root.rglob("*"), reverse=True):
            try:
                path.unlink() if path.is_file() else path.rmdir()
            except OSError:
                pass
        try:
            root.rmdir()
        except OSError:
            pass


@dataclass
class ShellResult:
    command: str
    exit_code: int
    stdout: str
    denied_reason: str | None = None

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


@dataclass
class SimulatedShell:
    """A parser, not an executor. Refuses anything outside a read-only allowlist."""

    fs: SandboxFS | None = None
    allowed: tuple[str, ...] = ("ls", "cat", "wc", "head")
    history: list[ShellResult] = field(default_factory=list)

    FORBIDDEN_BINARIES = {
        "rm", "mv", "cp", "dd", "mkfs", "chmod", "chown", "sudo", "su", "kill",
        "curl", "wget", "nc", "ssh", "scp", "git", "pip", "python", "python3",
        "bash", "sh", "zsh", "powershell", "cmd", "eval", "exec",
    }
    FORBIDDEN_CHARS = (";", "|", "&", ">", "<", "$(", "`", "\n", "\r")

    def run(self, command: str) -> ShellResult:
        result = self._run(command)
        self.history.append(result)
        return result

    def _deny(self, command: str, reason: str) -> ShellResult:
        return ShellResult(command=command, exit_code=126, stdout="", denied_reason=reason)

    def _run(self, command: str) -> ShellResult:
        if not isinstance(command, str) or not command.strip():
            return self._deny(str(command), "empty command")
        for meta in self.FORBIDDEN_CHARS:
            if meta in command:
                return self._deny(command, f"shell metacharacter {meta!r} is not allowed")
        try:
            argv = shlex.split(command)
        except ValueError as exc:
            return self._deny(command, f"cannot parse command: {exc}")
        if not argv:
            return self._deny(command, "empty command")

        binary = Path(argv[0]).name.lower()
        if binary in self.FORBIDDEN_BINARIES:
            return self._deny(command, f"binary {binary!r} is not permitted")
        if binary not in self.allowed:
            return self._deny(command, f"only {', '.join(self.allowed)} are permitted")

        if self.fs is None:
            return ShellResult(command=command, exit_code=0, stdout="(no filesystem attached)")

        try:
            if binary == "ls":
                target = argv[1] if len(argv) > 1 else "."
                return ShellResult(command, 0, "\n".join(self.fs.list_dir(target)))
            if binary == "cat":
                if len(argv) < 2:
                    return self._deny(command, "cat needs a file name")
                return ShellResult(command, 0, self.fs.read_text(argv[1]))
            if binary in ("wc", "head"):
                if len(argv) < 2:
                    return self._deny(command, f"{binary} needs a file name")
                text = self.fs.read_text(argv[1])
                if binary == "wc":
                    return ShellResult(command, 0, str(len(text.splitlines())))
                return ShellResult(command, 0, "\n".join(text.splitlines()[:5]))
        except SandboxError as exc:
            return ShellResult(command, 2, "", denied_reason=exc.reason)

        return self._deny(command, "unhandled command")
