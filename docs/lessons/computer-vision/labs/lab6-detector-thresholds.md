# Lab 6 - Evaluate a detector at different confidence thresholds

**Section path:** [Overview](../index.md) · Module [CV09](../cv09-boxes-iou-map.md) · **Lab 6** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 10% of the section assessment |
| **Time** | 3 hours |
| **Hardware** | CPU-only |
| **Code** | `projects/computer-vision/lab6_detector_thresholds.py` |
| **Prerequisite** | Lab 5 (or it trains its own small detector) |

## The task

A detector outputs scores; a product needs a decision. Sweep the score threshold, tabulate
precision, recall, and F1 at each point, and **choose** a threshold with a written
justification.

Deliverables:

1. the sweep table,
2. mAP@0.5 and mAP@[.5:.95],
3. the chosen threshold, the use case, and the cost reasoning,
4. a note on which error (false positive or false negative) your choice favours.

## Setup

```bash
cd projects/computer-vision
python lab5_detector_training.py        # writes outputs/detector.pt
python lab6_detector_thresholds.py
```

The lab loads Lab 5's checkpoint when present, so both labs score the same model. Without
it, it trains a small detector of its own.

## Run it

Verified output:

```text
 thresh  precision   recall     f1    tp    fp    fn
----------------------------------------------------
   0.05      0.103    0.613  0.177    38   330    24
   0.10      0.125    0.613  0.208    38   265    24
   0.20      0.165    0.613  0.260    38   192    24
   0.30      0.200    0.613  0.302    38   152    24
   0.50      0.320    0.516  0.395    32    68    30
   0.70      0.568    0.339  0.424    21    16    41
   0.90      0.667    0.194  0.300    12     6    50

best F1 0.424 at threshold 0.70 (precision 0.568, recall 0.339, tp 21, fp 16, fn 41)
mAP@0.5        0.324
mAP@[.5:.95]   0.088
  AP50 circle   0.334
  AP50 square   0.104
  AP50 triangle 0.532

report: .../outputs/lab6_thresholds.json
0 failure(s)
PASS  precision/recall trade-off measured across thresholds
```

## Reading the sweep

1. **Recall is flat from 0.05 to 0.30 at 0.613.** Lowering the threshold below 0.30 adds
   only false positives: the model already emits every object it will ever find by 0.30.
   That is a fact about the model's confidence distribution, and it is invisible in mAP.
2. **F1 peaks at 0.70**, not at the 0.5 default. On this model the default is a bad choice
   by the lab's own metric.
3. **The ends are both useless**: at 0.05 you emit 368 boxes for 62 objects; at 0.90 you
   find 12 of 62.
4. **mAP@[.5:.95] 0.088** shows localisation is loose - boxes are approximately right,
   which is what a 4-pixel stride buys you.

!!! note "F1 is not the objective, it is a summary"
    F1 weights precision and recall equally. A security camera does not. Choose the
    threshold from the cost of the two error types, then use F1 only as a sanity check.

## Choosing, with the reasoning written down

Example answer for a hypothetical use case - *sorting conveyor, 30 items/s, human review of
every positive*:

> False positives cost a human glance (~2 s). False negatives cost a missed item (~a
> material loss). At 0.70 the model emits 37 boxes for 62 objects with 57% precision:
> 16 wasted glances per 62 items and 41 misses. At 0.30 it emits 190 boxes with 20%
> precision: far more wasted glances, but 38 finds. If missed items are the expensive
> error, 0.30 wins despite the ugly precision; if human attention is the bottleneck, 0.70
> wins. We chose 0.30 because a missed recyclable contaminates a whole batch.

Note that the answer depends on a number the model cannot supply. That is the lesson.

## Test cases

| Check | Expected | Verification |
| --- | --- | --- |
| Sweep covers the range | >= 5 thresholds from <= 0.05 to >= 0.9 | printed table |
| Monotone precision | precision non-decreasing as threshold rises | table |
| Monotone recall | recall non-increasing as threshold rises | table |
| Best F1 identified | printed with threshold | stdout |
| mAP ladder reported | both mAP values | stdout |
| JSON written | valid, includes every row | `lab6_thresholds.json` |

## Rubric

| Criterion | Marks | What earns full marks |
| --- | --- | --- |
| Correct sweep | 20 | table reproduced; monotonicity holds |
| Metric reading | 25 | explains the flat recall region and the F1 peak |
| Threshold choice | 30 | named use case, explicit costs, choice follows from them |
| Alternative considered | 15 | argues the opposite choice and says what would change the decision |
| Presentation | 10 | table + paragraph, numbers cited exactly |

## Extensions

1. Compute the sweep at IoU 0.3 and 0.75. Which threshold survives both?
2. Add a per-class sweep. Does the best threshold differ by class?
3. Plot precision-recall as ASCII. Where is the knee?
4. Choose a threshold that keeps false positives under 10 per image and report the recall
   you pay.

## Submit

```text
cv-lab6/
  README.md
  sweep.md          # table plus the chosen threshold
  decision.md       # use case, costs, choice, counter-argument
  thresholds.json
```

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| All thresholds give identical F1 | decoded once at a high threshold | decode permissively, then filter by score |
| best F1 at 0.05 | model emits few high-confidence boxes | report it; that is a finding, not a bug |
| mAP differs from Lab 5 | different checkpoint used | check the "loaded detector from" line |
