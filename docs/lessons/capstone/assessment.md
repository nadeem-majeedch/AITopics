# Assessment - Capstone (M17) {#assessment}

**Section path:** [Overview](index.md) · **Assessment**

Three checkpoints, each gated. The final grade is the weighted sum; a failed
checkpoint must be revised before the next is marked.

## Weights

| Checkpoint | Weight | Deliverable |
| --- | --- | --- |
| 1 - Scope and data | 20% | `project-scope.md`, `dataset-card.md` |
| 2 - Build and evidence | 35% | end-to-end path, `experiments.csv`, `reproducibility.md`, draft cards |
| 3 - Evaluation, security, packaging | 45% | `evaluation-report.md`, final card, manifest, `threat-and-responsible-use-review.md`, `release-notes.md`, `final-report.md`, defense |

The file names and a final checklist are in the
[capstone submission package](../../course/projects/submission-package.md).
Every project submits the same ten files.

## Rubric

| Criterion | Weight within checkpoint 3 | Excellent | Pass | Fail |
| --- | --- | --- | --- | --- |
| Evaluation quality | 30% | Frozen test, intervals, paired comparison, slices, inspected failures | Metrics with n and intervals | Point estimates, test reused for tuning |
| Reproducibility | 25% | One command, pinned deps, digests, configs per run | Runs with minor manual steps | Cannot be reproduced |
| Security and ethics | 20% | Threat table with residual risk, data minimisation, guard measured both ways | Threats listed, guard tested | No threat review, guard only on attacks |
| Packaging | 15% | Card, manifest, rollback, verified tamper test | Card and manifest present | No artifact integrity |
| Communication and defense | 10% | Decision follows evidence; limitations stated plainly | Clear report | Claims unsupported by measurements |

## Checkpoint 1 gate

* The task supports a decision, not a demo.
* The metric has a threshold and a failure cost.
* The split matches the deployment unit.
* The risk register has at least six rows with mitigations.

## Checkpoint 2 gate

* An end-to-end path exists: data to one prediction.
* A baseline is measured on the same split.
* The experiment log records code, data digest, config, metrics, and decision.
* One controlled comparison (2x2 or equivalent) is reported in full.

## Checkpoint 3 gate

* The test set and rule were frozen before the final run.
* Every headline metric has n and an interval.
* The model card passes validation and claims audit.
* The manifest verifies and a tamper test fails.
* The threat review includes residual risk and an owner.
* The release recommendation includes monitoring and rollback.
* The defense answers: what decision, what evidence, what happens when wrong.

## Defense

Fifteen minutes: ten of presentation, five of questions. The marker will ask for
the interval on the deciding metric, the worst failure you found, the rollback
trigger, and one thing you would do with another month.

## Academic integrity

Report your own runs. If you reuse a pretrained model or a public dataset, cite it
and state the licence. Do not present a downloaded evaluation as your own
measurement.
