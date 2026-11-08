# Lab 1 - A support agent with guardrails {#lab-1}

**Section:** [AI agents](../index.md) · **Module:** M15 · **Time:** 8 hours

## Goal

Build a support agent with three tools, an approval gate, run budgets, persistent
memory, and an evaluation suite that can fail.

## Required tools

| Tool | Side effect | Schema | Gate |
| --- | --- | --- | --- |
| `lookup_order` | read | `order_id` string, required | allowlist |
| `calculate` | none | `expression` string | allowlist |
| `write_note` | write | `path`, `text` | approval + path root |

You may add a fourth read-only tool. Do not add a network or shell tool.

## Steps

1. Implement the registry and tools. Use strict schemas with
   `additionalProperties: false`.
2. Add a policy with the three tools, `allow_write=True`, and `write_note` in
   `require_approval`.
3. Use `DenyAllApprover` by default. Demonstrate a denied write. Then use a
   scripted approver to demonstrate a granted write.
4. Attempt a write to `../escape.txt` with approval granted. Record the code.
5. Run a task that requires two tools. Print the trace and the stop reason.
6. Run a repeating model with a small step budget. Record the stop reason.
7. Add persistent memory. Store one user fact and one tool-sourced instruction.
   Prove the tool-sourced entry is not recalled at the user bar and can be purged.
8. Write three evaluation tasks: one happy path, one arithmetic path, and one
   negative control that must fail. Report the success rate and the failure.
9. Add a poisoned read tool. Show the observation envelope in the transcript and
   the flagged phrase.

## Deliverables

| File | Contents |
| --- | --- |
| `agent.py` | registry, tools, policy, loop wiring |
| `report.md` | traces, codes, evaluation table, failure analysis |
| `eval.json` | tasks and results |
| `transcript.txt` | one run with the untrusted envelope visible |

## Marking

* **25%** schemas and policy are least-privilege and tested.
* **20%** approval and path containment are demonstrated with traces.
* **20%** budgets stop at least one run with a declared reason.
* **20%** evaluation has a real failing case and correct per-task reasons.
* **15%** memory trust and purge are tested.

## Rules

No API key and no network. A scripted model is acceptable and preferred. Do not
weaken a guardrail to make a demo pass; report the failure instead.
