# Capstone (M17)

The capstone is one integrated system, built and defended end to end. It is not a
larger lab; it is the evidence that you can take a decision from a sentence to a
measured, packaged, monitored service.

| | |
| --- | --- |
| **Level** | 5 - final |
| **Study time** | 40 hours: 8 h scoping, 22 h build, 10 h evaluation and packaging |
| **Hardware** | depends on the chosen project |
| **Prerequisites** | M04-M08, M15-M16, and one applied vertical (M09-M14) |
| **You will produce** | A reproducible repository, an evaluation report, a threat review, and a defended release decision |

## Lessons

| # | Lesson | Focus |
| --- | --- | --- |
| 1 | [CP01](cp01-scoping-and-data.md) | decision, metric, data contract, risk register |
| 2 | [CP02](cp02-build-and-evidence.md) | end-to-end path, controlled experiments, log |
| 3 | [CP03](cp03-evaluation-and-packaging.md) | final evaluation, threats, packaging, release |

## What "complete" means

A capstone is complete when a reviewer can clone the repository, run one command,
reproduce the headline metric within its stated interval, inspect the failures, and
see a rollback path. "It works on my machine" is not a submission.

## Checkpoints

| Checkpoint | Due | Evidence |
| --- | --- | --- |
| 1 - Scope | end of CP01 | one-page scope, data contract, risk register |
| 2 - Build | end of CP02 | end-to-end path, baseline, experiment log, 2x2 comparison |
| 3 - Defense | end of CP03 | final evaluation, card, manifest, threat review, release decision |

Each checkpoint is marked before the next begins. A failed checkpoint is revised,
not skipped.

## Acceptable projects

Choose a project that supports a decision and has measurable failure cost. The
[capstone options](../../course/projects.md) list twelve specifications; you may
propose your own with the same structure. Do not choose a project only because a
dataset is convenient.

## Practical work

| Work | What it asks for |
| --- | --- |
| [Lab 1 - Capstone package](labs/lab-1-capstone-package.md) | Three gated checkpoints from scope to defended release |

## Assessment

[Assessment](assessment.md): checkpoints 20/35/45, with the defense weighted
inside checkpoint 3.

## After the capstone

There is no M18. The next step is a real deployment with a real owner, or
contributing a lesson back to this course using the
[quality standards](../../planning/quality-standards.md).
