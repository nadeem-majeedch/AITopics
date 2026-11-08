# Lab 1 - The capstone package {#lab-1}

**Section:** [Capstone](../index.md) · **Module:** M17 · **Time:** 40 hours

## Goal

Deliver a complete system: a scoped decision, a reproducible build, a measured
evaluation, a threat review, and a defended release recommendation.

All three checkpoints submit files from the shared
[capstone submission package](../../../course/projects/submission-package.md):
the same ten files for every project. The short names below (`scope.md`,
`release.md`) refer to those package files.

## Checkpoint 1 - Scope (8 h)

Produce `submission/project-scope.md` with:

* the decision supported and who makes it;
* the metric, threshold, and cost of a false positive and a false negative;
* the unit of prediction and the split strategy;
* the data contract: sources, digests, label definition, features available at
  prediction time;
* the baseline and what "better" means;
* a risk register with at least six rows, each with a mitigation and an owner.

Gate: the marker accepts the scope or returns it with specific gaps. For a
classification task, every class must appear in the test split; a class with zero
test examples fails the gate because its per-class metric is undefined.

## Checkpoint 2 - Build (22 h)

Produce a running path and the evidence:

1. Load data, apply the split, train a baseline, evaluate on validation.
2. Train the candidate model. Save the artifact.
3. Run one controlled comparison (2x2 or a one-factor sweep) and report every
   cell.
4. Keep `submission/experiments.csv` with run id, code digest, data digest, config, metrics,
   decision, notes.
5. Write the evidence section of `submission/evaluation-report.md` with the baseline, the candidate, and one rejected change.

Gate: the path runs from a clean checkout and the log explains every reported run.

## Checkpoint 3 - Evaluate, secure, package (10 h)

1. Freeze the test set and scoring rule at the top of `submission/evaluation-report.md` **before** the run.
2. Run the final evaluation once. Report n, intervals, and a paired comparison with
   the baseline.
3. Report at least one slice (subgroup or condition) and the failures you
   inspected.
4. Generate the model card and run the claims audit.
5. Write the manifest and verify it; tamper with a copy and record the failure.
6. Complete the threat review with residual risk and an owner.
7. Write `submission/release-notes.md`: recommendation, evidence, monitoring,
   rollback trigger, limitations.
8. Package: `submission/README.md` with a one-line reproduction command, pinned
   dependencies, `configs/`, `artifacts/`, and the complete `submission/` directory.

Gate: a second person runs the reproduction command and reaches the reported
metric within its interval.

## Deliverables

| File | Contents |
| --- | --- |
| `submission/project-scope.md` | decision, metric, data contract, risk register |
| `submission/dataset-card.md` | origin, licence, counts, privacy, limitations |
| `submission/experiments.csv` | one row per run, including rejected runs |
| `submission/model-card.md` | intended use, training, evaluation, risks |
| `submission/evaluation-report.md` | frozen test, metrics with intervals and slices, failures |
| `submission/threat-and-responsible-use-review.md` | threats, controls, residual risk, owners |
| `submission/reproducibility.md` | environment, seeds, commands, expected outputs |
| `submission/README.md` | what, why, reproduce, limitations |
| `submission/release-notes.md` | recommendation, monitoring, rollback |
| `submission/final-report.md` | the 10-12 page technical report |
| `manifest.json` | digests for data, model, card, preprocessing |

## Marking

See the [assessment](../assessment.md). Checkpoint weights are 20/35/45.

## Rules

No public deployment is required. Do not tune on test. Do not hand-edit generated
cards. Cite every external dataset and model with its licence.
