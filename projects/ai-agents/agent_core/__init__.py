"""Small, auditable building blocks for the AI agents section.

Nothing here needs an API key, a model download, or a GPU. The offline path is
the default; hosted and local models are opt-in adapters behind the same
``respond`` protocol.

Modules
-------
``schema``        JSON-schema subset, with paths in error messages
``tools``         ToolSpec, registry, validation, retries, timeouts, approval
``model``         decision protocol; scripted, rule, local, hosted models
``loop``          bounded agent loop with an explicit set of stop reasons
``memory``        short-term window, persistent memory with trust and purge
``retrieval``     controlled corpus, BM25 search, injection heuristics
``workflow``      explicit state machine for deterministic pipelines
``policy``        allowlists, path containment, capability flags
``sandbox``       sandboxed filesystem and a shell *simulator*
``trace``         structured events, redaction, JSONL persistence
``evaluation``    task sets, scoring, aggregate metrics, reports
``multi_agent``   roles, blackboard, bounded revision with a reviewer veto
"""

from .evaluation import EvalReport, EvalTask, CaseResult, evaluate, load_tasks, save_tasks
from .loop import RunLimits, RunResult, run_agent, transcript_text
from .memory import MemoryEntry, PersistentMemory, ShortTermMemory
from .model import (
    Decision,
    HostedChatModel,
    LocalTransformersModel,
    ModelReply,
    RepeatingModel,
    RuleModel,
    ScriptedModel,
    Usage,
    build_system_prompt,
    parse_decision,
)
from .multi_agent import (
    Blackboard,
    Role,
    RoleOutput,
    Team,
    TeamResult,
    analyst_role,
    researcher_role,
    reviewer_role,
)
from .policy import Policy, PolicyDecision, PolicyViolation, describe
from .retrieval import (
    Corpus,
    Doc,
    Hit,
    chunk_text,
    find_instruction_like,
    poisoned_corpus,
    safe_corpus,
    tokenize,
)
from .sandbox import SandboxFS, SandboxError, SimulatedShell, VirtualFileSystem, demo_root
from .schema import Schema, SchemaError, object_schema, validate
from .tools import (
    ApprovalRequest,
    POLICY_DENIED,
    ConsoleApprover,
    ScriptedApprover,
    ToolFailure,
    ToolRegistry,
    ToolResult,
    ToolSpec,
    tool,
)
from .trace import Trace, redact
from .workflow import StateMachine, StepOutcome, WorkflowStop

__all__ = [
    "ApprovalRequest",
    "Blackboard",
    "CaseResult",
    "ConsoleApprover",
    "Corpus",
    "Decision",
    "Doc",
    "EvalReport",
    "EvalTask",
    "Hit",
    "HostedChatModel",
    "LocalTransformersModel",
    "MemoryEntry",
    "ModelReply",
    "PersistentMemory",
    "Policy",
    "PolicyDecision",
    "PolicyViolation",
    "RepeatingModel",
    "Role",
    "RoleOutput",
    "RuleModel",
    "RunLimits",
    "RunResult",
    "SandboxError",
    "SandboxFS",
    "Schema",
    "SchemaError",
    "ScriptedApprover",
    "ScriptedModel",
    "ShortTermMemory",
    "SimulatedShell",
    "StateMachine",
    "StepOutcome",
    "Team",
    "TeamResult",
    "ToolFailure",
    "ToolRegistry",
    "ToolResult",
    "ToolSpec",
    "Trace",
    "Usage",
    "VirtualFileSystem",
    "WorkflowStop",
    "analyst_role",
    "build_system_prompt",
    "chunk_text",
    "demo_root",
    "describe",
    "evaluate",
    "find_instruction_like",
    "load_tasks",
    "object_schema",
    "parse_decision",
    "poisoned_corpus",
    "redact",
    "researcher_role",
    "reviewer_role",
    "run_agent",
    "safe_corpus",
    "save_tasks",
    "tool",
    "tokenize",
    "transcript_text",
    "validate",
]

__version__ = "1.0.0"
