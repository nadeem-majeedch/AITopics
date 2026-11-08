"""Project F - a file assistant that can only touch one test directory.

Architecture
------------
::

    designated root (a temporary directory, or outputs/agents/project_f)
      notes/plan.txt
      notes/budget.csv
      .env                      <- planted fixture, must never be read
      secret.pem                <- planted fixture, must never be read

    list_files(dir)        read-only, no approval
    read_text(path)        read-only, size-limited, secret names refused
    write_summary(path)    requires approval, write flag, size-limited
    delete_file(path)      requires approval AND is denied by policy here

Three independent controls, so one bug is not a breach:

1. **Policy**: a root list, resolved paths, rejected secret names, capability
   flags for write/shell/network.
2. **SandboxFS**: re-resolves every path through the policy and refuses
   oversized reads and writes.
3. **Approval**: ``write_summary`` and ``delete_file`` cannot run without a
   human saying yes, and the default approver says no.

The demo plants a ``.env`` file inside the allowed directory on purpose. The
path is inside the sandbox, so containment alone would allow it; the secret-name
rule is what refuses it. That is the difference between a sandbox and a policy.

Run
---
    python project_f_approved_file_assistant.py --selftest
    python project_f_approved_file_assistant.py            # approved run
    python project_f_approved_file_assistant.py --deny     # refused write
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_core import (  # noqa: E402
    Policy,
    PolicyViolation,
    SandboxFS,
    ScriptedApprover,
    ToolRegistry,
    ToolSpec,
    demo_root,
    object_schema,
)
from agent_core.cli import Checks, base_parser  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "outputs" / "agents" / "project_f"

LIST_INPUT = object_schema({"directory": {"type": "string", "default": "."}}, required=[])
READ_INPUT = object_schema({"path": {"type": "string", "minLength": 1, "maxLength": 200}})
WRITE_INPUT = object_schema(
    {
        "path": {"type": "string", "minLength": 1, "maxLength": 200},
        "text": {"type": "string", "minLength": 1, "maxLength": 4000},
    }
)
DELETE_INPUT = object_schema({"path": {"type": "string", "minLength": 1, "maxLength": 200}})


def build_policy(root: Path, *, allow_write: bool = True) -> Policy:
    return Policy(
        allowed_tools=frozenset({"list_files", "read_text", "write_summary", "delete_file"}),
        roots=(root.resolve(),),
        allow_write=allow_write,
        allow_network=False,
        allow_shell=False,
        require_approval=frozenset({"write_summary", "delete_file"}),
        max_read_bytes=8000,
        max_write_bytes=4000,
    )


def make_tools(fs: SandboxFS) -> list[ToolSpec]:
    def list_files(arguments: dict[str, Any]) -> dict[str, Any]:
        return {"entries": fs.list_dir(arguments.get("directory") or ".")}

    def read_text(arguments: dict[str, Any]) -> dict[str, Any]:
        text = fs.read_text(arguments["path"])
        return {
            "path": arguments["path"],
            "lines": len(text.splitlines()),
            "chars": len(text),
            "text": text[:3000],
        }

    def write_summary(arguments: dict[str, Any]) -> dict[str, Any]:
        written = fs.write_text(arguments["path"], arguments["text"])
        return {"path": arguments["path"], "bytes": written}

    def delete_file(arguments: dict[str, Any]) -> dict[str, Any]:
        # Even if a future policy allowed this, the operation stays behind the
        # approval gate and is logged. Here the policy refuses it first.
        raise PermissionError("delete is not implemented for this assistant")

    return [
        ToolSpec("list_files", "List files in a directory inside the workspace.", list_files,
                 LIST_INPUT, output_schema=object_schema({"entries": {"type": "array"}}),
                 side_effect="read"),
        ToolSpec("read_text", "Read a UTF-8 text file inside the workspace.", read_text,
                 READ_INPUT, output_schema=object_schema({"chars": {"type": "integer"}}, allow_extra=True),
                 side_effect="read"),
        ToolSpec("write_summary", "Write a summary file into the workspace. Needs approval.",
                 write_summary, WRITE_INPUT,
                 output_schema=object_schema({"bytes": {"type": "integer"}}, allow_extra=True),
                 side_effect="write", requires_approval=True),
        ToolSpec("delete_file", "Delete a file. Always refused in this configuration.",
                 delete_file, DELETE_INPUT, side_effect="write", requires_approval=True),
    ]


def build_registry(policy: Policy, approver) -> tuple[ToolRegistry, SandboxFS]:
    fs = SandboxFS(policy)
    registry = ToolRegistry(approver=approver, policy=policy)
    for spec in make_tools(fs):
        registry.register(spec)
    registry.allow("list_files", "read_text", "write_summary")
    return registry, fs


def plant_secrets(root: Path) -> None:
    """Fixtures that a real workspace might contain, planted for the demo."""

    (root / ".env").write_text("AGENT_API_KEY=sk-this-is-a-fake-fixture\n", encoding="utf-8")
    (root / "secret.pem").write_text("-----BEGIN PRIVATE KEY-----\nnot real\n", encoding="utf-8")


def summarise(registry: ToolRegistry) -> dict[str, Any]:
    listing = registry.call("list_files", {"directory": "."})
    notes = registry.call("list_files", {"directory": "notes"})
    plan = registry.call("read_text", {"path": "notes/plan.txt"})
    budget = registry.call("read_text", {"path": "notes/budget.csv"})
    return {
        "root": listing.value if listing.ok else listing.error,
        "notes": notes.value if notes.ok else notes.error,
        "plan": plan.value if plan.ok else plan.error,
        "budget": budget.value if budget.ok else budget.error,
    }


def approved_run(root: Path, approve: bool) -> dict[str, Any]:
    policy = build_policy(root)
    registry, _ = build_registry(policy, ScriptedApprover([approve, False, False]))
    facts = summarise(registry)
    summary_text = (
        "# Workspace summary\n\n"
        f"Files at root: {len(facts['root'].get('entries', []))}\n"
        f"Files in notes: {len(facts['notes'].get('entries', []))}\n"
        f"Plan lines: {facts['plan'].get('lines')}\n"
        f"Budget lines: {facts['budget'].get('lines')}\n"
    )
    written = registry.call("write_summary", {"path": "summary.md", "text": summary_text})
    return {
        "facts": facts,
        "written": written,
        "audit": [record.__dict__ for record in registry.audit],
    }


def demo(approve: bool) -> int:
    with demo_root("agent-f-") as root:
        plant_secrets(root)
        outcome = approved_run(root, approve)
        print(f"root: {root}")
        print(json.dumps(outcome["facts"], indent=2, default=str)[:800])
        print(f"\nwrite_summary -> {'ok' if outcome['written'].ok else outcome['written'].code}")
        print(f"summary exists: {(root / 'summary.md').exists()}")
        print("\naudit:")
        for record in outcome["audit"]:
            print(f"  {record['tool']:12s} ok={record['ok']} code={record['code']}")
    return 0


def selftest() -> int:
    checks = Checks("project F - approved file assistant")
    with demo_root("agent-f-") as root:
        plant_secrets(root)
        policy = build_policy(root)
        registry, fs = build_registry(policy, ScriptedApprover([True, True, True]))

        listing = registry.call("list_files", {"directory": "."})
        checks.check("lists the workspace", listing.ok and ".env" in listing.value["entries"],
                     str(listing.value))

        inside = registry.call("read_text", {"path": "notes/plan.txt"})
        checks.check("reads a file inside the root", inside.ok and "Week 1" in inside.value["text"])

        outside = registry.call("read_text", {"path": "../outside.txt"})
        checks.check("traversal refused by policy", not outside.ok and outside.code == "policy_denied",
                     str(outside.error))

        absolute = registry.call("read_text", {"path": "C:/Windows/win.ini"})
        checks.check("absolute path refused", not absolute.ok)

        env = registry.call("read_text", {"path": ".env"})
        checks.check("secret name refused although it is inside the root", not env.ok, str(env.error))
        pem = registry.call("read_text", {"path": "secret.pem"})
        checks.check("key file refused", not pem.ok)

        write = registry.call("write_summary", {"path": "summary.md", "text": "hello workspace"})
        checks.check("approved write succeeds", write.ok, str(write.error))
        checks.check("file appears", (root / "summary.md").read_text(encoding="utf-8") == "hello workspace")

        delete = registry.call("delete_file", {"path": "summary.md"})
        checks.check("delete refused even with approval available", not delete.ok, str(delete.error))

    # Write denied: policy flag and approval are separate controls.
    with demo_root("agent-f-deny-") as root:
        policy = build_policy(root)
        registry, _ = build_registry(policy, ScriptedApprover([False, False, False]))
        denied = registry.call("write_summary", {"path": "summary.md", "text": "should not exist"})
        checks.check("denied approval blocks the write", not denied.ok and denied.code == "approval_denied",
                     str(denied.error))
        checks.check("no file written", not (root / "summary.md").exists())

        read_only = build_policy(root, allow_write=False)
        registry2, _ = build_registry(read_only, ScriptedApprover([True]))
        blocked = registry2.call("write_summary", {"path": "summary.md", "text": "nope nope"})
        checks.check("write flag off blocks the write", not blocked.ok, str(blocked.error))
        checks.check("second file not written", not (root / "summary.md").exists())

    # A symlink that points outside the root is refused, where symlinks work.
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        root = base / "root"
        root.mkdir()
        target = base / "outside.txt"
        target.write_text("outside", encoding="utf-8")
        policy = build_policy(root)
        try:
            link = root / "escape.txt"
            link.symlink_to(target)
            try:
                policy.resolve("escape.txt")
                symlink_blocked = False
            except PolicyViolation:
                symlink_blocked = True
            checks.check("symlink escape refused", symlink_blocked)
        except (OSError, NotImplementedError):
            checks.check("symlink escape refused (skipped: no symlink privilege)", True)

    # Audit records contain tool names but not file contents.
    with demo_root("agent-f-audit-") as root:
        registry, _ = build_registry(build_policy(root), ScriptedApprover([True]))
        registry.call("read_text", {"path": "notes/plan.txt"})
        export = json.dumps([record.__dict__ for record in registry.audit])
        checks.check("audit names the tool", "read_text" in export)
        checks.check("audit excludes file contents", "Week 1" not in export)

    return checks.report()


def main() -> int:
    parser = base_parser("Human-approved file assistant in a designated directory")
    parser.add_argument("--deny", action="store_true", help="refuse the write (simulated reviewer)")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    return demo(approve=not args.deny)


if __name__ == "__main__":
    raise SystemExit(main())
