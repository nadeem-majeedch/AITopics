# P12 - Tool-using AI agent with access controls and human approval

```markdown
**Projects:** [Index](index.md) · [Completion checklist](completion-checklist.md) · [Report template](report-template.md)
```

| | |
| --- | --- |
| **Difficulty** | Advanced |
| **Effort** | 60-80 hours |
| **Hardware** | CPU-only with a local small model or a scripted policy; no paid API required |
| **Prerequisites** | [M15 agents, tool calling, memory](../../lessons/ai-agents/index.md), [AG04 budgets and approvals](../../lessons/ai-agents/ag04-budgets-and-approvals.md), [CA05 prompts and structured output](../../lessons/chatbots-rag/ca05-prompts-and-structured-output.md), [CA13 citations and abstention](../../lessons/chatbots-rag/ca13-citations-and-abstention.md), [CA16 privacy](../../lessons/chatbots-rag/ca16-privacy-and-deployment.md) |
| **Builds on** | Agent projects A-H in `projects/ai-agents/` and the deterministic task data in `data/agents/` |

## 1. Problem statement and motivation

An agent that can read files, run queries, and send messages is useful precisely
because it acts. That is also the risk: a mistaken plan can delete data, a malicious
document can redirect it, and a plausible-sounding request can move money. The
engineering question is not "can the model call a tool" but "what is it allowed to
do without a human, and how do you prove it did not exceed that".

This project builds a bounded agent with a permission matrix, an approval gate for
irreversible actions, an append-only audit log, and a failure-injection suite. The
evaluation is as much about refusals and containment as about task completion.

**Decision supported:** whether an agent may proceed with a proposed action, needs
human approval, or must be refused. The agent never holds credentials it does not
need.

## 2. Intended learning outcomes

1. Write a threat model for an agent with tools, including injection through
   retrieved content and over-permissioned tools.
2. Define tools with typed schemas, least-privilege scopes, and explicit side effects.
3. Implement a permission matrix mapping roles to tools and resources.
4. Gate irreversible or costly actions behind human approval with a timeout and a
   denial path.
5. Produce an append-only audit record sufficient to reconstruct any action.
6. Evaluate task success, tool-call accuracy, unauthorised-action rate, injection
   resistance, and cost per task.
7. Demonstrate containment: step limits, timeouts, sandboxing, and a kill switch.

## 3. Difficulty and prerequisites

**Level:** Advanced. 60-80 hours: 10 threat model and design, 14 tools and policy,
12 planning loop, 10 approvals and audit, 14 evaluation and attacks, 12 writing.

Requires the M15 material and at least one agent project. You should already have
built a tool-calling loop; this project is about constraining it.

## 4. Scope and out-of-scope features

**In scope**

- 3-5 tools with typed inputs and outputs, at least one read-only data tool and one
  write or send action.
- Two roles (for example `analyst` and `operator`) with different permissions.
- Approval gate for write, send, delete, and spend actions; approval is granted by a
  human in the loop (a CLI prompt or a small local UI is fine).
- Append-only JSONL audit log: timestamp, actor, role, tool, arguments hash, decision,
  result summary, and correlation id.
- Step limit, per-tool timeout, retry policy, and a kill switch.
- A failure-injection and injection-attack suite with recorded outcomes.
- A deterministic scripted policy so the evaluation runs without a model, plus an
  optional local model policy.

**Out of scope**

- Real credentials, real money, real email, or real customer data.
- Autonomous actions without approval on any irreversible operation.
- Multi-agent orchestration and long-term memory. Add them only as evaluated
  extensions.
- Bypassing a refusal by rephrasing: if you find one, report it as a finding.
- Claims of safety. You can claim specific controls and specific test results.

## 5. Dataset options, licences, and preparation

| Component | Source | Licence | Notes |
| --- | --- | --- | --- |
| Task set | `python scripts/make_agent_data.py` → `data/agents/tasks/dev.json`, `test.json` | CC0-1.0 | 6 dev and 5 held-out tasks; deterministic |
| Documents | `data/agents/corpus/safe/` and `corpus/untrusted/` | CC0-1.0 | The untrusted set contains injected instructions on purpose |
| Tabular data | `data/agents/csv/sales.csv` and `sales_messy.csv` | CC0-1.0 | Clean and defective variants for a data tool |
| Sandbox | A temporary directory per run | Yours | The agent writes only inside it; deletion is part of cleanup |
| Model policy (optional) | `agent_core.LocalTransformersModel` with a local instruct checkpoint, or `HostedChatModel` with a key | Check the model card and licence | The scripted policy and a deterministic mock must remain available; no key is needed for the mandatory path |

**Preparation**

1. Generate and verify the data (`--check`). Record the manifest hash.
2. Read every document in `corpus/untrusted/`. You cannot evaluate injection
   resistance without knowing the payloads.
3. Expand the task set yourself to at least 20 tasks for evaluation, keeping the
   original dev/test split discipline: your additions go to dev, and you hold back
   five you never tune on.
4. Define roles and the permission matrix in a JSON file before writing code.
5. Write the approval policy: which tools require approval, who may approve, what
   the timeout is, and what happens on timeout.

## 6. Recommended baseline

**Scripted policy, no model.** A hand-written planner that maps each task type to a
tool sequence. It establishes the ceiling for task success and proves the harness
works. Every model-driven run is compared against it.

Second baseline: a **single-step tool caller** that picks one tool and stops. The
gap between it and the multi-step agent is the value of planning, and the extra
steps are the extra risk.

## 7. Milestones

| # | Milestone | Evidence | Hours |
| --- | --- | --- | --- |
| 1 | Threat model and permission matrix | Table of assets, actors, threats, controls | 10 |
| 2 | Tools with schemas | Typed tools, unit tests, sandbox enforced | 14 |
| 3 | Planning loop | Step limit, timeout, retries, kill switch | 12 |
| 4 | Approval and audit | Approval CLI, denial path, audit reconstruction | 10 |
| 5 | Evaluation | 20+ tasks, metrics table, attack suite | 14 |
| 6 | Package | Report, system card, demo script, rerun | 12 |

## 8. Repository or folder structure

```text
capstone-p12/
  README.md
  requirements.txt
  configs/
    policy.json           # roles -> tools -> resources -> approval required
    limits.json           # max steps, timeouts, retry counts
  data/
    dataset-card.md
    tasks/                # dev and held-out tasks
  src/
    agent/
      loop.py             # plan, act, observe, stop
      tools/
        search_docs.py
        query_csv.py
        write_note.py
        send_message.py   # simulated; writes to an outbox file
      policy.py           # permission checks, approval gate
      audit.py            # append-only log with correlation ids
      sandbox.py          # path confinement and cleanup
    cli.py
  tests/
    test_policy.py
    test_audit.py
    test_sandbox.py
    test_injection.py
  reports/
    report.md
    system-card.md
    threat-model.md
  outputs/
    audit.jsonl
    eval_results.json
```

## 9. Detailed development tasks

1. `threat-model.md`: assets (documents, CSV, outbox), actors (user, agent, untrusted
   document), threats (injection, over-permission, exfiltration, runaway loop,
   confused deputy), and one control per threat. Include residual risk.
2. `policy.json`: roles, tools, resource patterns, and `requires_approval`. Deny by
   default; a tool not listed is unavailable.
3. Tools: typed arguments, schema validation, and a declared side effect
   (`read`, `write`, `send`, `delete`). A write tool must refuse paths outside the
   sandbox.
4. `loop.py`: plan with a step budget, execute one tool per step, observe, and stop
   on completion, budget exhaustion, or refusal. Log every step with a correlation
   id.
5. Approval: before a gated action, print the proposed tool, arguments, and
   consequence, then wait for `y/n` with a timeout. On denial, the agent must
   continue with an alternative or report failure. On timeout, treat as denial.
6. `audit.py`: append one JSON line per event with UTC timestamp, actor, role, tool,
   argument hash (not the raw secret), decision, and a short result summary. Add a
   `verify_chain()` that detects a deleted or reordered line (hash chain).
7. Sandbox: confine writes to a run directory, reject `..` traversal and absolute
   paths, and clean up at the end. Test with an attempted escape.
8. Scripted policy: cover every dev task. Record the exact tool sequence per task as
   the reference trajectory.
9. Optional model policy: use `agent_core.LocalTransformersModel` (local checkpoint)
   or `HostedChatModel` (explicit network opt-in and key in the environment). Prompt
   with tool schemas, parse structured output, and reject malformed calls rather than
   guessing. The model is only a proposer: policy, approval, sandboxing, step
   limits, and schema validation stay in the harness. If the model is unavailable
   or becomes invalid, run the scripted policy and a deterministic malformed-call
   mock, and report both as baselines rather than pretending they are LLM results.
   Measured example: a cached 135M instruct checkpoint, with its chat template
   applied, returned prose instead of a JSON decision on 5/5 development tasks and
   made zero tool calls. That is a protocol failure to report, not a parser to
   loosen until the model appears to work.
10. Evaluation harness: run all 20+ tasks, record success, steps, tool calls,
    approvals requested, denials, and wall-clock time. Compare scripted and model
    policies where both exist.
11. Attack suite: (a) injected instruction in an untrusted document, (b) request to
    read outside the sandbox, (c) request to send data to an external address,
    (d) attempt to exceed the step budget, (e) attempt to act after denial,
    (f) malformed tool arguments. Record whether the control held.
12. Ablation: disable the approval gate and re-run the attack suite. The difference
    is your evidence that the gate matters.

## 10. Testing and evaluation plan

| Test | Proves | Pass condition |
| --- | --- | --- |
| Policy unit test | Deny by default | Unlisted tool refused for every role |
| Role test | Least privilege | Analyst cannot call the send tool |
| Sandbox test | Confinement | `../escape.txt` and absolute paths refused |
| Approval test | Gate holds | Denied action does not execute; timeout denies |
| Audit test | Tamper evidence | Deleting a line breaks `verify_chain()` |
| Injection test | Untrusted text is not instructions | Injected task not executed; recorded |
| Malformed tool arguments | Schema validation is enforced | Invalid args produce `invalid_arguments`; no side effect |
| Mock-model recovery | The harness survives a bad first call | Deterministic invalid-call mock completes or stops with a recorded reason |
| Local-model optional path | The adapter is honest about availability | Model loads only when installed; malformed JSON is rejected |
| Budget test | Loop terminates | Run stops at max steps with a clear reason |
| Determinism | Scripted runs repeat | Same task, same trajectory, twice |

Protocol: tune prompts and policies on dev tasks; evaluate on held-out tasks once.
The attack suite runs against both the gated and ungated builds, and both results
are reported.

## 11. Metrics

**Quantitative**

| Metric | Why |
| --- | --- |
| Task success rate (held-out) | Whether it works |
| Tool-call accuracy and invalid-argument rate | Whether it chose the right tool and arguments |
| Model-path comparison (scripted, mock, local if available) | Whether a model adds value or only adds failure modes |
| Unauthorised-action attempts blocked / total | Whether the controls hold |
| Approval requests per task, and approval latency | Human cost |
| Injection success rate | Security outcome, reported even when zero |
| Steps per task and budget exhaustion rate | Efficiency and runaway risk |
| Wall-clock and token cost per task | Practicality |
| Audit reconstructability | Can a reviewer replay the run |

**Qualitative**

- Two trajectories quoted in full: one success, one refusal.
- A description of the confused-deputy risk in your design and how it is bounded.
- Residual risk that remains after controls, stated plainly.

## 12. Expected deliverables

- [ ] Threat model with assets, threats, controls, and residual risk.
- [ ] Permission matrix and role definitions.
- [ ] Typed tools with sandbox enforcement and tests.
- [ ] Approval gate with denial and timeout paths.
- [ ] Tamper-evident audit log and a reconstruction example.
- [ ] Scripted baseline trajectories and a model-policy comparison if available
  (scripted, deterministic mock, and local/hosted model when it actually runs).
- [ ] 20+ task evaluation table and attack suite results, gated versus ungated.
- [ ] Invalid-argument and malformed-decision counts, separated from policy violations.
- [ ] System card with prohibited uses and operational limits.
- [ ] Tests passing.

### Submission package and P12 requirements

Copy the ten files from the [capstone submission package](submission-package.md)
and submit them at the three checkpoints: scope and dataset card at checkpoint 1;
running path, experiment log, reproducibility and draft cards at checkpoint 2;
evaluation report, threat review, release notes and final report at checkpoint 3.
Use `model-card.md` as the system card.

P12-specific rules for those files:

- **Separate policy tests from model tests.** Report the scripted baseline and the
  deterministic mock in one table and any real model policy in another. Scripted
  success measures the harness, not intelligence; the mock measures recovery, not
  planning.
- **Keep the malformed-call control.** Report task success, mean steps, invalid
  calls, tool errors, and policy violations separately. A 100% success rate with a
  50% invalid-call rate is a finding, not a pass.
- **Report attacks gated and ungated.** Include injection, path escape, external
  recipient, step budget, post-denial retry, approval timeout, and malformed
  arguments. State what the ungated build actually did.
- **Report the fail-closed result.** If a local model cannot emit a valid decision,
  record zero completed tasks, the invalid-decision count, zero tool calls, and
  zero violations. Do not loosen the parser until the model appears to work.
- **Do not equate security controls with model capability.** The approval gate,
  sandbox, schema and audit chain can be effective while the model is unusable, and
  a model can be fluent while the controls are absent. Say which claim each result
  supports.

## 13. Suggested extensions

- Add a second approver role and a two-person rule for the most dangerous action.
- Add a dry-run mode that shows the planned trajectory before execution.
- Add memory of past approvals and show that it does not bypass the gate.
- Add cost accounting per tool and a per-task budget that hard-stops the loop.

## 14. Common failure modes and troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Agent executes an injected instruction | Retrieved text concatenated into the system prompt | Delimit untrusted content, never treat it as instructions, re-test |
| Local model ignores JSON and writes prose | Model too small or chat template not applied | Use the tokenizer's chat template, lower expectations, keep schema validation, and report the invalid-decision rate |
| Approval prompt appears after the action | Gate implemented inside the tool | Gate before dispatch, in the loop |
| Audit log missing arguments | Logging summarised too early | Log argument hashes and a redacted preview at dispatch |
| Loop never terminates | No step budget or completion detection | Hard step cap and explicit stop reasons |
| Same task different trajectory | Model sampling | Temperature 0 or scripted policy; seed where possible |
| Analyst role can send messages | Permission checked by tool name only | Check role, tool, and resource pattern |
| Sandbox escape via symlink | Path check on strings only | Resolve real paths and re-check containment |
| "It refused everything" | Deny by default with no allow list | Add explicit allows per role and test the happy path |

## 15. Marking rubric

| Criterion | Weight | 4 - Excellent | 3 - Meets | 2 - Approaching | 1 - Not yet |
| --- | --- | --- | --- | --- | --- |
| Threat model and policy design | 20% | Assets, threats, controls, least privilege, residual risk | Clear policy with roles | Policy exists but coarse | No policy |
| Agent implementation | 20% | Typed tools, sandbox, budget, retries, clean stop reasons | Working loop with tools | Partly working | No containment |
| Approval and audit | 20% | Gate before dispatch, denial and timeout paths, tamper-evident log | Approval and logging work | Gate or log incomplete | Neither |
| Evaluation and attacks | 25% | Held-out tasks, attack suite, gated-vs-ungated ablation | Task metrics and some attacks | Task metrics only | No evaluation |
| Reproducibility and documentation | 15% | Scripted baseline, config, system card, rerun | Runs with minor steps | Thin docs | Cannot rerun |

**Bands:** 90-100 portfolio-ready; 80-89 solid; 70-79 works, controls thin; below
70 the agent is not safe to demonstrate.

## 16. Self-review checklist

- [ ] Deny by default; every allowed tool is listed explicitly per role.
- [ ] Irreversible actions require approval before dispatch.
- [ ] Denial and timeout both prevent execution.
- [ ] Audit log is append-only and tamper-evident; a reconstruction is included.
- [ ] Sandbox rejects traversal, absolute paths, and symlink escapes.
- [ ] Step budget and per-tool timeout are enforced and tested.
- [ ] Attack suite includes injection, exfiltration, malformed arguments, and post-denial attempts.
- [ ] Gated versus ungated results are both reported.
- [ ] Scripted, mock, and any real model results are labelled separately; a model that cannot follow the protocol is reported as a failure, not rescued by hand.
- [ ] No real credentials, money, or personal data are used.
- [ ] Prohibited uses and residual risks are stated.

## 17. Report template

Use the shared [report template](report-template.md), adding:

1. **Threat model** - assets, actors, threats, controls, residual risk.
2. **Permission matrix** - roles x tools x approval requirement.
3. **Trajectories** - one success, one refusal, with audit excerpts.
4. **Attack results** - table of attacks, gated outcome, ungated outcome, and malformed-argument counts.
5. **Model comparison** - scripted, deterministic mock, and local/hosted model if it ran; report task success, invalid calls, latency, and cost separately.
6. **Human cost** - approvals per task and latency.

## 18. Demonstration and presentation checklist

- [ ] Run a normal task end to end and show the audit trail.
- [ ] Run a task that needs approval, deny it, and show nothing happened.
- [ ] Run an injected document task and show the refusal.
- [ ] Attempt a sandbox escape and show the rejection.
- [ ] Delete an audit line and show `verify_chain()` failing.
- [ ] Show the gated-versus-ungated attack table.
- [ ] Answer: "What could this agent still do wrong, and what would you monitor?"

**Demo trap:** demoing with the approval gate disabled "to save time". That is the
control under test.

---

**Previous:** [P11 action recognition](p11-action-recognition.md) · [Project index](index.md)
