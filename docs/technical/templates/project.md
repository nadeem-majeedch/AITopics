# Project specification template

!!! note "Template guidance"
    Use this template for a capstone proposal or a project brief. Students may
    adapt it for the M17 proposal; contributors may use it under `projects/`.
    Replace every prompt and delete this box.

# [Project title]

**Author:** [name or team]  
**Path:** [learning path]  
**Hardware:** [label and backup plan]  
**Proposed date:** [YYYY-MM-DD]

## 1. Problem and users

[What problem does this system solve? Who uses it? What decision or task does it
support? Describe the current process and why it is inadequate.]

## 2. Scope

**In scope:**

- [Capability]
- [Capability]

**Out of scope:**

- [Capability deliberately excluded]
- [Capability deliberately excluded]

[State one constraint that protects users, data, or compute.]

## 3. Data

| Item | Plan |
| --- | --- |
| Source | [public dataset, consented collection, or synthetic] |
| License | [name and URL] |
| Size | [rows, images, hours, tokens] |
| Labels | [who labels, guidelines, quality checks] |
| Personal data | [none / describe, with consent and redaction plan] |
| Storage | [local, Drive, or repository pointer; no raw data in Git] |

## 4. Model or system design

[Describe the baseline, the proposed approach, and one alternative. Explain why
the baseline is a fair comparison.]

## 5. Evaluation

| Item | Plan |
| --- | --- |
| Primary metric | [metric] |
| Baseline | [baseline result] |
| Test set | [size and construction] |
| Error analysis | [how errors will be categorized] |
| Safety or fairness check | [what will be measured] |
| Success threshold | [number and justification] |

## 6. Responsible AI and security

- [Privacy and consent]
- [Bias and representation]
- [Misuse and prohibited use]
- [Secrets and access control]
- [Limitations to disclose]

## 7. Deliverables

- [ ] Reproducible repository with a README.
- [ ] Technical report.
- [ ] Model or dataset card.
- [ ] Evaluation table and error analysis.
- [ ] Demo.
- [ ] Reflection and limitations.

## 8. Milestones

| Week | Milestone | Evidence |
| --- | --- | --- |
| [1] | Proposal approved | This document |
| [2] | Data and baseline | Baseline metric |
| [3] | Main implementation | Working system |
| [4] | Evaluation and demo | Report and demo |
| [5] | Final package | Submission tree |

## 9. Risks

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| [Risk] | [low/medium/high] | [low/medium/high] | [Action] |
| [Risk] | [low/medium/high] | [low/medium/high] | [Action] |

## 10. Approval

**Reviewer:** [name]  
**Decision:** [approved / revise / rejected]  
**Notes:** [feedback]
