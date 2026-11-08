# Threat and responsible-use review

**Project:** [replace]  
**System version:** [replace]  
**Checkpoint:** 3

## Scope

[replace: one paragraph naming what the system does, what it can reach (files,
network, messages, money), and who is affected by a wrong output. If the system
only classifies an image, say that the blast radius is a wrong label, not an
action.]

## Assets and actors

| Asset | Why it matters | Who can reach it |
| --- | --- | --- |
| [replace: model, data, credentials, user files, outbox] | | |

| Actor | Goal | Capability |
| --- | --- | --- |
| User | [replace] | [replace] |
| Untrusted document or input | [replace] | [replace] |
| Operator / approver | [replace] | [replace] |

## Threat table

| # | Threat | Likelihood | Impact | Control | Residual risk | Owner |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | [replace: injected instruction causes an unauthorised action] | | | [replace] | [replace] | |
| 2 | [replace: path traversal outside the work directory] | | | | | |
| 3 | [replace: malformed arguments reach a tool] | | | | | |
| 4 | [replace: denial is bypassed by a retry] | | | | | |
| 5 | [replace: sensitive data in logs or prompts] | | | | | |
| 6 | [replace] | | | | | |

"Residual risk" is what remains after the control, not a restatement of the
control. Every row needs an owner.

## Privacy

- Data minimisation: [replace]
- Retention and deletion: [replace]
- Logging and redaction: [replace]
- Third parties or external APIs: [replace: none / name and data sent]
- Personal data in prompts or outputs: [replace]

## Safety and fairness

- Groups or conditions under-represented in the data: [replace]
- Measured disparity, or "not measured because...": [replace]
- Worst realistic harm from a wrong output: [replace]
- Human override or appeal: [replace]

## Security boundaries (required for P12 and any acting system)

| Boundary | Implementation | Test |
| --- | --- | --- |
| Tool allow-list | [replace] | [replace: test name] |
| Approval before irreversible action | [replace] | [replace] |
| Denial and timeout block execution | [replace] | [replace] |
| Filesystem confinement | [replace] | [replace] |
| Step and time limits | [replace] | [replace] |
| Audit integrity | [replace] | [replace] |

Report gated **and** ungated results. A control that was never attacked has not
been tested. State whether the policy is scripted, mocked, or model-driven, and do
not present scripted success as model capability.

## Misuse and prohibited uses

- [replace: prohibited use 1]
- [replace: prohibited use 2]
- [replace: prohibited use 3]

## Monitoring and response

- What is logged: [replace]
- Alert condition: [replace]
- Rollback or kill switch: [replace]
- Incident owner: [replace]

## Sign-off

| Question | Answer |
| --- | --- |
| Is the residual risk acceptable for a course prototype? | [replace: yes/no and why] |
| Would you deploy this to real users today? | [replace: no, and what would have to change] |
| What is the most important control to keep? | [replace] |
