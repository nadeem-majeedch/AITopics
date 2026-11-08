# Assessment - Evaluation and production (M16) {#assessment}

**Section path:** [Overview](index.md) · **Assessment**

One integrated lab worth 85% and a release review worth 15%.

## Weights

| Item | Weight | Deliverable |
| --- | --- | --- |
| [Lab 1](labs/lab-1-evaluation-and-serving.md) - evaluation and serving | 85% | metrics with intervals, calibration, drift, guard, card, manifest, endpoint |
| Release review | 15% | a go/no-go recommendation with evidence and a rollback plan |

## Grading bands

| Band | Mark | Descriptor |
| --- | --- | --- |
| Excellent | 85-100 | Every claim traceable; negative results reported; guard misses analyzed; release decision follows from evidence |
| Good | 70-84 | Complete report with intervals and artifacts; limitations thin |
| Pass | 50-69 | Metrics and endpoint work, but calibration or drift lacks a decision |
| Fail | < 50 | Point estimates only; card numbers not traceable; manifest missing or failing; guard recall without FPR |

## Required evidence

1. Every headline metric with n and a 95% interval.
2. A calibration table with bin counts and a keep/reject decision.
3. A drift report for two windows with a decision and next action.
4. Guard recall **and** false-positive rate, plus the missed attacks.
5. A model card that passes section validation and claims audit.
6. A manifest that verifies, plus a tamper test.
7. p50 and p95 latency from at least 30 requests.
8. A rollback artifact with a digest.

## Release review

Recommend release or no-release. Include:

* the metric that decides it and its interval;
* the known failure modes and who owns them;
* the monitoring signals and thresholds;
* the rollback trigger and procedure;
* the limitations that remain after release.

A "yes" with no rollback or monitoring fails the review even if the metrics are
good.

## What the marker will try

* Tamper with one artifact and run your verification.
* Fit calibration on the test split and ask why the number improved.
* Add a benign request that trips the guard.
* Ask for the p95, not the mean.
* Ask which artifact is currently served and whether it matches the card digest.
