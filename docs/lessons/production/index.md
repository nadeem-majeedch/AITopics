# Evaluation, security, and deployment (M16)

A model that scores well in a notebook is a hypothesis. This section turns it into
a service you can defend: intervals on every metric, calibration measured rather
than assumed, drift watched, guardrails tested on both attacks and benign traffic,
a card that can be audited, and an artifact whose bytes you can verify.

| | |
| --- | --- |
| **Level** | 5 - after at least one trained model |
| **Study time** | 22 hours: 10 h reading, 10 h lab, 2 h write-up |
| **Hardware** | CPU-only; the serving lab uses a loopback HTTP server |
| **Prerequisites** | [MT04](../model-training/mt04-evaluation-and-error-analysis.md), [PR01](pr01-metrics-and-intervals.md) |
| **You will produce** | An evaluation report, a model card, a manifest, and a measured endpoint |

## Lessons

| # | Lesson | Focus |
| --- | --- | --- |
| 1 | [PR01](pr01-metrics-and-intervals.md) | intervals and paired comparisons |
| 2 | [PR02](pr02-calibration.md) | ECE, Brier, temperature scaling |
| 3 | [PR03](pr03-drift.md) | PSI and a drift decision |
| 4 | [PR04](pr04-guardrails-and-cards.md) | adversarial recall/FPR and audited cards |
| 5 | [PR05](pr05-artifacts-and-serving.md) | manifests and p50/p95 latency |

Notebook: [M16 - Evaluation and serving](../../notebooks/production/m16_production.ipynb).

## Measured anchors

* churn model: AUC **0.778**, accuracy **0.790** (293/371), Wilson **[0.745,
  0.828]**, MAE **0.329 [0.308, 0.350]**;
* precision **0.658**, recall **0.475**, F1 **0.552** at threshold 0.5;
* ECE **0.067** raw, **0.075** after temperature **1.10**; the calibrated model is
  worse, and the paired interval excludes zero;
* drift: week 1 **hold**, week 2 **investigate** (usage PSI **1.171**, tickets
  **1.212**, region **0.492**);
* guard: attack recall **0.75**, benign false-positive rate **0.0**; four misses
  are documented;
* serving: **40/40** requests returned 200; p50 **15.53 ms**, p95 **16.72 ms** in the
  recorded run (an earlier run measured p95 16.31 ms; loopback latency jitters).

## The section's argument

1. **A point estimate is not a result.** Report n and an interval.
2. **Calibration is measured, not assumed.** A best practice can be a regression.
3. **Drift is a workflow, not a threshold.** Decide, then act.
4. **A guard is judged on both sides.** Recall without false positives is a
   broken product.
5. **An artifact without a digest is an unversioned dependency.**
6. **Latency is a distribution.** Report the tail.

## What this section does not cover

Kubernetes, autoscaling, multi-region deployment, and vendor-specific serving
stacks. It covers the evidence and contracts those systems need: verified
artifacts, measured latency, monitored drift, and a card a reviewer can check.

## Practical work

| Work | What it asks for |
| --- | --- |
| [Lab 1 - Evaluation and serving](labs/lab-1-evaluation-and-serving.md) | Intervals, calibration, drift, guard, card, manifest, and a measured endpoint |

## Assessment

[Assessment](assessment.md): one integrated lab (85%) and a release review (15%).

## Next

Continue to [M17 - Capstone](../capstone/index.md).
