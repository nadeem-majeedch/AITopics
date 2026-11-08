# Project scope

**Project:** [replace: P03 / P06 / P12 and title]  
**Author:** [replace]  
**Date:** [replace: YYYY-MM-DD]  
**Checkpoint:** 1

## Problem and decision

[replace: one paragraph. What decision does this system support, and who makes it
today? State the decision in one sentence. If the system only produces a demo,
say what decision the demo is meant to inform.]

## Users and current process

| User | What they do now | Cost of the current process | What changes if this works |
| --- | --- | --- | --- |
| [replace] | [replace] | [replace: time, money, error rate] | [replace] |

## Motivation and evidence

[replace: why this is worth building, with at least one concrete observation from
the data or the workflow. Do not cite a paper's number as your motivation without
saying it is theirs.]

## Objectives

Write objectives that a measurement can fail.

1. [replace: e.g. "Reach macro F1 >= 0.80 on the frozen test split, with a 95%
   bootstrap interval that excludes 0.70."]
2. [replace]
3. [replace]

## Scope

**In scope**

- [replace]
- [replace]

**Out of scope**

- [replace: at least one thing a reader might assume the project does]
- [replace]

## Metric, threshold, and error costs

| Item | Value | Why |
| --- | --- | --- |
| Primary metric | [replace] | [replace] |
| Success threshold | [replace] | [replace] |
| Baseline to beat | [replace] | [replace] |
| Cost of a false positive | [replace] | [replace] |
| Cost of a false negative | [replace] | [replace] |
| Unit of prediction | [replace: image / ticket / task] | [replace] |
| Split unit | [replace: source group / template / task family] | [replace] |

## Data contract

| Field | Definition |
| --- | --- |
| Source | [replace: generated command or licence-cleared dataset] |
| Version / digest | [replace: manifest hash or dataset version] |
| Label definition | [replace: one sentence per class or target] |
| Available at prediction time | [replace] |
| Deliberately excluded | [replace: leakage-prone fields] |
| Licence | [replace: exact string and URL] |

## Risk register

At least six rows. "Owner" is a role, even in a solo project.

| # | Risk | Likelihood | Impact | Mitigation | Owner |
| --- | --- | --- | --- | --- | --- |
| 1 | [replace] | low/med/high | low/med/high | [replace] | [replace] |
| 2 | [replace] | | | | |
| 3 | [replace] | | | | |
| 4 | [replace] | | | | |
| 5 | [replace] | | | | |
| 6 | [replace] | | | | |

## Open questions

- [replace: what you do not know yet, and the experiment that would resolve it]

## Checkpoint 1 gate

- [ ] The decision and users are specific.
- [ ] The metric has a threshold and both error costs.
- [ ] Every class or target appears in the test split, or the metric is redefined.
- [ ] The split unit matches how the system will be used.
- [ ] The risk register has six rows with mitigations and owners.
