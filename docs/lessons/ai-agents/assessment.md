# Assessment - AI agents (M15) {#assessment}

**Section path:** [Overview](index.md) · **Assessment**

One lab worth 80% and a failure review worth 20%.

## Weights

| Item | Weight | Deliverable |
| --- | --- | --- |
| [Lab 1](labs/lab-1-support-agent.md) - support agent | 80% | three tools, approval gate, budget, memory, evaluation suite |
| Failure review | 20% | a trace of a denied or failed run and what it proves |

## Grading bands

| Band | Mark | Descriptor |
| --- | --- | --- |
| Excellent | 85-100 | Harness is least-privilege; all three stop modes demonstrated; evaluation includes a failing case; interpretation is precise |
| Good | 70-84 | Working agent and tests; one guardrail thin |
| Pass | 50-69 | Agent works on happy path, but budgets or approval are untested |
| Fail | < 50 | Tool output trusted as instructions; no denial test; evaluation cannot fail |

## Required evidence

1. A trace with a `final` stop and at least two tool calls.
2. A trace with `approval_denied` and one with `policy_denied`.
3. A trace stopped by a budget or `repeated_action`.
4. A memory test proving a tool-sourced instruction is not recalled as a user
   fact.
5. An injection attempt with the observation envelope visible in the transcript.
6. An evaluation report with per-task pass/fail and one deliberate failure.

## What the marker will try

* Call a tool with a typo and a missing field.
* Approve a write to `../escape.txt`.
* Return a tool output containing "ignore previous instructions".
* Ask for a fact stored with `trust="tool"`.
* Rerun the evaluation with the negative control removed and check that you notice
  the suite now passes everything.

## Failure review

Choose one denied or failed run and explain:

* which layer stopped it (schema, policy, approval, budget, scorer);
* what would have happened without that layer;
* what the trace records that the transcript does not.

A review that says "the agent made a mistake" without naming the layer scores zero.
