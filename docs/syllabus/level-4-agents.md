# Level 4 - AI agents

**Module:** M15 | **Hours:** 24 | **Hardware:** CPU or API

An agent is more than a chatbot with tools. It is a system that observes,
decides, acts, checks results, and recovers from failure within explicit
permission boundaries. This level teaches you to build that system and to
measure whether it actually completes tasks.

!!! note "Level outcome"
    You can build a tool-using agent with typed tools, bounded autonomy, memory,
    observability, and an evaluation suite that includes failure and injection
    tests.

## Readiness check

- Can you call a language model programmatically and control its context?
- Can you build a RAG pipeline and evaluate retrieval and generation?
- Can you write typed Python functions and validate JSON?
- Can you reason about permissions, secrets, and untrusted input?

If not, complete M06, M09, and M10 first.

---

## M15 - AI agents, tool calling, memory, and workflows {#m15}

**Published material:** [AI agents overview](../lessons/ai-agents/index.md).

**Level 4 | 24 hours | CPU or API | Prerequisite: M06, M09, M10**

### Learning objectives

By the end of this module, you can:

1. Explain the agent loop: observe, plan, act, observe, and stop.
2. Design typed tool schemas with clear descriptions, inputs, outputs, and errors.
3. Implement tool calling with validation, timeouts, retries, and idempotency.
4. Compare ReAct-style reasoning with explicit plan-and-execute workflows.
5. Add short-term conversation memory and a justified long-term memory strategy.
6. Enforce least-privilege permissions and sandbox risky tools.
7. Add tracing, structured logs, cost tracking, and step limits.
8. Evaluate task success, tool accuracy, trajectory quality, and safety.
9. Test prompt injection, tool abuse, data exfiltration, and runaway loops.

### Prerequisites

- M06 (language model behavior and decoding).
- M09 (chat state, prompts, guardrails).
- M10 (retrieval and untrusted documents).
- Comfort with Python typing, JSON, and APIs.

### Study time

| Theory | Guided notebook | Lab | Assessment | Total |
| --- | --- | --- | --- | --- |
| 4 h | 8 h | 11 h | 1 h | 24 h |

### Required theory

- What counts as an agent; autonomy levels and bounded agency.
- The agent loop and stopping conditions.
- Tool/function calling: schemas, arguments, results, and errors.
- JSON Schema and Pydantic validation.
- ReAct, plan-and-execute, reflection, and when workflows beat autonomy.
- State machines and graph-based workflows.
- Short-term memory, summarization, and context compression.
- Long-term memory: episodic, semantic, and vector-backed; retrieval and
  forgetting.
- Multi-agent systems: benefits, coordination cost, and failure modes.
- Sandboxing, least privilege, secrets management, and human approval.
- Prompt injection, indirect injection, tool abuse, and data exfiltration.
- Observability: traces, spans, tool calls, tokens, latency, and cost.
- Evaluation: task success, tool-call accuracy, trajectory efficiency, safety,
  and reproducibility.
- Framework options: a minimal custom loop, LangGraph, smolagents, PydanticAI.
  Choose based on transparency and maintenance, not fashion.

### Guided notebook

**Notebook:** `notebooks/ai-agents/m15_agents.ipynb`, executed on Windows 11 CPU.
The lesson sequence is [AG01-AG05](../lessons/ai-agents/index.md).

The notebook builds a scripted-model agent harness with three tools, strict
schemas, a policy with path containment, an approval gate, run budgets, and
persistent memory with provenance. It demonstrates a `final` run, a
`repeated_action` stop, `approval_denied`, `policy_denied`, an untrusted-output
envelope, and a three-task evaluation that scores 2/3 because a negative control
fails.

**Tools:** local and sandboxed; no network, payments, or credentials.

**Hardware:** CPU-only; no API key is required.

### Independent lab

**Brief:** Build an agent that completes a bounded multi-step task and evaluate
it rigorously.

Required evidence:

- Task definition, users, success criteria, and non-goals.
- At least three tools with schemas, validation, and documented failure modes.
- A permission model: what the agent can read, write, and execute.
- Step limits, timeouts, retries, and a human-approval path for risky actions.
- Short-term memory and a justified long-term memory design.
- Traces for at least five runs, including one failure.
- An evaluation set of 30 or more held-out tasks.
- Metrics: task success, tool-call accuracy, steps per task, latency, and cost.
- Failure-injection tests: tool timeout, malformed output, empty result, and
  conflicting instructions.
- Prompt-injection tests, including indirect injection through retrieved content.
- A security review of secrets, file access, and network access.

**Constraints:** No autonomous spending, credential use, or irreversible actions.
No real personal data. Tools must be sandboxed or read-only unless explicitly
approved. The agent must fail safely, not loop forever.

### Assessment criteria

Module score: knowledge check 20%, guided notebook 30%, lab 40%, reflection 10%.
The lab uses the [standard rubric](../course/assessments.md#lab-rubric).

Module-specific must-haves:

- Tool schemas validate inputs and return structured errors.
- The agent has hard step and time limits.
- Risky actions require approval or are impossible by design.
- Evaluation includes failure and injection cases, not only happy paths.
- Traces make failures diagnosable.

### Deliverables

- Agent implementation with typed tools.
- Permission and sandbox design note.
- Evaluation set and results.
- Failure-injection and prompt-injection report.
- Trace samples and cost/latency summary.
- Security review.

### Next step

M16 - Evaluation, security, responsible AI, and deployment.

### Risks and notes

- **Excessive agency is a design bug.** Do not give an agent credentials or
  write access it does not need.
- **Prompt injection is not solved.** Treat tool outputs and retrieved text as
  untrusted.
- **Loops cost money.** Enforce step, token, and time budgets.
- **Framework lock-in:** understand the loop before adopting a framework.
- **Evaluation is hard.** A demo that works once is not evidence.

---

## Level 4 completion checklist

- [ ] I can explain and implement the agent loop.
- [ ] I can design typed tools with validation and errors.
- [ ] I can add bounded memory without uncontrolled context growth.
- [ ] I can enforce permissions and sandbox risky tools.
- [ ] I can trace tool calls and measure cost and latency.
- [ ] I can evaluate task success and failure modes.
- [ ] I have tested prompt injection and tool abuse.
- [ ] I have a portfolio artifact for M15.

Proceed to [Level 5 - Production and capstone](level-5-production.md).
