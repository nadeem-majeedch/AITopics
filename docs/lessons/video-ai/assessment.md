# Assessment - Video AI {#assessment}

**Section path:** [Overview](index.md) · **Assessment**

Eight labs worth 90%, plus a documented capstone worth 10%. Every mark is tied to a measurement
you can reproduce with one command, not to prose quality alone.

## Weights

| Item | Weight | Deliverable |
| --- | --- | --- |
| [Lab 1](labs/lab-1-preprocessing.md) - preprocessing and data audit | 8% | metadata table, extraction counts, contact sheet |
| [Lab 2](labs/lab-2-object-detection.md) - detection on frames | 10% | per-frame timing, annotated video, mAP with TP/FP/FN |
| [Lab 3](labs/lab-3-tracking-and-counting.md) - tracking and counting | 15% | MOTA table, `max_age` sweep, count report with cell error |
| [Lab 4](labs/lab-4-domain-adaptation.md) - domain adaptation | 14% | three-way comparison on four held-out videos, threshold curve |
| [Lab 5](labs/lab-5-garment-attributes.md) - attribute model | 10% | clean metrics, robustness sweep, responsible-scope statement |
| [Lab 6](labs/lab-6-action-recognition.md) - temporal modelling | 13% | frame vs vote vs temporal, per-class table, confusion analysis |
| [Lab 7](labs/lab-7-integrated-analytics.md) - integrated application | 10% | working CLI, config, summary JSON, five rejected inputs |
| [Lab 8](labs/lab-8-performance.md) - performance | 10% | three levers measured, capacity budget, rejected optimisation |
| Capstone - documented system | 10% | model card + governance statement + reproduction command |

Labs 4 and 6 are the pair that carries the section's main argument: fine-tuning an image model
(frame-level) versus training a temporal model (clip-level). A submission that conflates them
loses the marks for both, however good the numbers are.

## Grading bands

| Band | Mark | Descriptor |
| --- | --- | --- |
| Excellent | 85-100 | Every number reproducible; interpretation explains the mechanism; limitations stated before they are asked for; one experiment beyond the brief |
| Good | 70-84 | Correct results, clear write-up, limitations mentioned but thin |
| Pass | 50-69 | Runs and reports numbers, but interprets weakly or omits sample sizes, thresholds, and strides |
| Fail | < 50 | Numbers not reproducible, frame-level split, metrics mismatched to the task, or tables copied from the manual |

## What every submission must contain

1. **A reproduction command** that regenerates the headline number, including the stride and
   threshold it used.
2. **Sample sizes next to every metric.** "MOTA 0.658" is not a result; "MOTA 0.658 on 60 frames,
   6 vehicles, 14 predicted tracks, `max_age=6`, `iou_threshold=0.30`" is.
3. **The split the number came from.** Validation numbers and test numbers are different
   claims; label each one.
4. **A limitation you found yourself**, with the measurement that showed it. "Crowd footage
   undercounts by 3 of 8" is a limitation; "performance may vary" is not.
5. **A run log from your machine**, not the manual's output. Your milliseconds will differ; that
   is expected and must be reported.

## Marking rubric for the two hardest labs

### Lab 3 - tracking and counting

| Criterion | Marks | Evidence |
| --- | --- | --- |
| Pipeline runs on three scenes and writes reports | 3 | `outputs/lab3_tracking.json` |
| MOTA/IDSW/fragment table with track counts | 3 | the three-scene table |
| Count error separated into total and per-cell | 3 | 6/6 total, cell error 2 |
| `max_age` sweep with an interpretation of what does *not* change | 3 | the 4-row sweep |
| Tracked video reviewed, one identity failure explained | 3 | a named failure, e.g. a split at the line |

### Lab 4 - domain adaptation

| Criterion | Marks | Evidence |
| --- | --- | --- |
| Three models evaluated on four held-out videos | 3 | the comparison table |
| Threshold chosen on validation with the curve shown | 3 | the 0.3-0.7 sweep |
| Transferred-tensor count reported | 2 | 404 tensors |
| Honest conclusion: improved vs zero-shot, lost to in-domain | 3 | both statements, with numbers |
| Explicit statement that no temporal model was trained | 2 | one sentence, in the report |

## Capstone: a documented video system

Choose one task you can evaluate honestly in the time available.

| Option | Task | Metric | Evidence required |
| --- | --- | --- | --- |
| A | Line counter on your own consented footage | count error per class:direction | split by video, tracked review video |
| B | Action classifier on the section's synthetic clips plus your own | clip accuracy + per-class F1 | frame baseline reported alongside |
| C | Attribute model on vehicle colours (no people) | macro F1 + robustness sweep | degradation table, scope statement |
| D | Deployment profile of an existing lab | median/p95, RSS, capacity budget | measured on your machine, with settings |

Every option requires: a model card ([template](model-card.md)), a governance statement
([template](governance.md)), and a single command that regenerates the headline number.

### What a capstone is marked on

| Component | Weight within capstone | Notes |
| --- | --- | --- |
| Correct, reproducible measurement | 40% | the command runs, the number matches |
| Interpretation | 25% | explains *why*, not just *what* |
| Limitation analysis | 20% | the weakest number, named by you |
| Responsible scope | 15% | out-of-scope uses, data provenance, retention |

## Academic integrity

- Report your own measurements. Copying the manual's numbers when your run differs is
  fabrication; grading is on interpretation, and mismatched numbers are visible.
- You may discuss approaches, but the code and write-up are yours.
- Any external video, dataset, or pretrained weight must be cited with its licence. A model card
  without a licence line is incomplete.
- **Never submit footage of identifiable people without written consent**, including
  screenshots, review videos, and demos. The section's synthetic clips exist so that this is
  never necessary.
- Do not use the pipeline to identify, re-identify, or infer attributes of any person. The
  schema has no field for it, and adding one is a fail condition, not a bonus.

## Resubmission

A failed lab may be resubmitted once, with the original submission and a short note on what was
wrong. Resubmissions that change the numbers without changing the code are treated as
fabrication.
