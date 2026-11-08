# Assessment - Training and data engineering (M04-M05) {#assessment}

**Section path:** [Overview](index.md) · **Assessment**

Two labs worth 80% and a short defense worth 20%. Every mark is tied to a
measurement you can reproduce with one command.

## Weights

| Item | Weight | Deliverable |
| --- | --- | --- |
| [Lab 1](labs/lab-1-training-ablation.md) - training ablation | 40% | learning-rate and augmentation table, checkpoint, reload check |
| [Lab 2](labs/lab-2-dataset-audit.md) - dataset audit and card | 40% | audit table, cleaning log, split probe, dataset card |
| Defense | 20% | 10-minute walkthrough of two decisions and one failure |

## Grading bands

| Band | Mark | Descriptor |
| --- | --- | --- |
| Excellent | 85-100 | Numbers reproducible; interpretation explains the mechanism; limitations stated before asked; one controlled experiment beyond the brief |
| Good | 70-84 | Correct results and clear write-up; limitations mentioned but thin |
| Pass | 50-69 | Runs and reports numbers, but omits sample sizes, seeds, or the leakage probe |
| Fail | < 50 | Numbers not reproducible; random split presented as deployment estimate; data defects asserted without counts |

## What every submission must contain

1. **A reproduction command** with the seed and the exact notebook or script.
2. **Sample sizes** next to every metric, and the split strategy named.
3. **A checkpoint reload check**: identical predictions before and after a save.
4. **A cleaning log** with one reason per dropped row and counts that reconcile.
5. **A dataset card** with a digest and a section on out-of-scope use.
6. **One rejected alternative** with the measurement that rejected it.

## Lab 1 - what the marker checks

* The sweep varies one factor at a time.
* The selected configuration is chosen on validation, not test.
* The augmentation claim names the invariance it assumes.
* Step times include hardware, dtype, batch size, and warmup.
* The train/validation gap is reported for both models.

## Lab 2 - what the marker checks

* The audit runs on the raw file and the counts reconcile to the cleaned file.
* The label map rejects unknown labels instead of silently mapping them.
* Both random and grouped splits are reported, with an overlap probe for each.
* The near-duplicate count is interpreted as template reuse, not "bad data".
* The card is generated from measurements and includes a digest.

## Defense

Bring two decisions and one failure:

* why this learning rate and schedule;
* why this split answers your deployment question;
* a run that failed or surprised you, and what you changed.

The failure is marked for the diagnosis, not for being hidden. A submission that
claims every run succeeded is usually a submission that did not look.

## Academic integrity

You may use the notebooks and libraries. You may not present a table you did not
run. If you reuse a published number, label it as external and cite it. Fabricated
metrics fail the assessment regardless of the rest of the work.
