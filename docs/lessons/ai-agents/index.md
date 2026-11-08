# AI agents: tools, loops, memory, and evaluation (M15)

An agent is a bounded control loop around a model. This section builds the harness
in plain Python and then attacks it: budgets, approvals, untrusted tool output,
poisoned memory, and an evaluation suite with a deliberate failure.

Everything runs offline. The "model" is scripted so a failure is attributable to
the harness, not to sampling.

| | |
| --- | --- |
| **Level** | 4 - after language models |
| **Study time** | 18 hours: 9 h reading, 8 h lab, 1 h report |
| **Hardware** | CPU-only; no API key required |
| **Prerequisites** | [LF07](../llm-fine-tuning/lf07-evaluating-assistants.md), [AG01](ag01-agent-loop.md) |
| **You will produce** | A support agent with three tools, a denial trace, and a scored evaluation |

## Lessons

| # | Lesson | Focus |
| --- | --- | --- |
| 1 | [AG01](ag01-agent-loop.md) | the loop and the decision protocol |
| 2 | [AG02](ag02-tool-schemas.md) | strict schemas, side effects, least privilege |
| 3 | [AG03](ag03-memory-and-state.md) | bounded window, persistent trust, purge |
| 4 | [AG04](ag04-budgets-and-approvals.md) | stop reasons and human gates |
| 5 | [AG05](ag05-injection-and-evaluation.md) | indirect injection and task scoring |

Notebook: [M15 - Tool-using agents](../../notebooks/ai-agents/m15_agents.ipynb).

## Measured anchors

* a two-tool task ends with `final` after 3 steps and 2 tool calls;
* a repeating model is stopped with `repeated_action`, not the full step budget;
* an unapproved write returns `approval_denied`; a path escape returns
  `policy_denied` even with approval;
* memory recall at the user bar blocks document- and tool-sourced entries;
* the evaluation suite scores 2/3, catching the deliberate negative control.

## The section's argument

1. **The model proposes; the harness decides.** Schema validation, policy, and
   approval are code, not prompt text.
2. **Every run stops for a named reason.** "It finished" is not a reason.
3. **Tool output is untrusted.** Envelope it, flag it, and limit what a compromised
   run can do.
4. **Memory needs provenance and a purge.** A fact from a web page is not a user
   preference.
5. **Evaluation needs a case that can fail.** Otherwise it measures nothing.

## What this section does not cover

Training an agent with reinforcement learning, multi-agent orchestration at scale,
and hosted tool ecosystems. The package includes a small multi-agent blackboard and
a workflow state machine for further study; the lab focuses on the single-agent
harness that everything else builds on.

## Practical work

| Work | What it asks for |
| --- | --- |
| [Lab 1 - Support agent](labs/lab-1-support-agent.md) | Three tools, approval, budgets, memory, and a failing evaluation case |

## Assessment

[Assessment](assessment.md): one lab (80%) and a failure review (20%).

## Next

Continue to [M16 - Evaluation and production](../production/index.md).
