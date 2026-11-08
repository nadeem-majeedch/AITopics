# CV09 - Boxes, IoU, precision, recall, and mAP {#cv09}

**Section path:** [Overview](index.md) · **Module 9** · [Lab 6](labs/lab6-detector-thresholds.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 5 hours: 2 h reading, 3 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | CV08, F10 (precision, recall, ROC) |
| **You will produce** | Hand-computed IoU and AP values, and a threshold sweep with a written choice |

## Why this module exists

A detector outputs boxes with scores. Turning that into one number requires deciding
when a box "counts", how to match predictions to truth, and how to summarise a
precision-recall curve. Every one of those decisions is a place to fool yourself.

This module computes each quantity by hand on tiny examples, then checks the library
against your arithmetic. If your AP differs from the library's, one of you is wrong and
you will know which.

## IoU: the only thing that decides "hit"

Intersection over union, for boxes in `xyxy` pixel coordinates:

```text
IoU = area(intersection) / area(union)
    = inter / (A + B - inter)
```

Two 10x10 boxes offset by 5 pixels:

```text
inter = 5*5 = 25
union = 100 + 100 - 25 = 175
IoU   = 0.1429
```

```python
annotations.box_iou((0, 0, 10, 10), (5, 5, 15, 15))   # 0.142857...
```

Properties that matter:

- IoU is scale-free: a small and a large box can both score 0.8.
- IoU is 0 for any two boxes that do not overlap, so it cannot distinguish "slightly
  wrong" from "in another image".
- The threshold is a choice. 0.5 is the convention; 0.75 is stricter; segmentation-style
  tasks use 0.3 for loose boxes.

## Greedy matching, and why it must be greedy

For each image and class: sort predictions by score, and let each prediction claim the
highest-IoU unmatched ground-truth box above the threshold. One ground truth can be
claimed once.

```python
detection_train.quick_detector_metrics(model, records, classes, score_threshold=0.3)
```

The "once" is the whole subtlety. Without it, a model that emits ten copies of the same
box scores ten true positives against one object. The test suite asserts exactly this:
two identical predictions against one ground truth are `(tp=1, fp=1)`.

A prediction is a **false positive** if it matches nothing; an unmatched ground truth is
a **false negative**. Those two numbers, plus the threshold, define precision and recall:

```text
precision = tp / (tp + fp)      of the boxes I emitted, how many were right
recall    = tp / (tp + fn)      of the objects present, how many did I find
```

## AP: summarising a curve with one number

Sweep the score threshold from high to low. Each step either adds a true positive
(recall rises) or a false positive (precision falls). Average precision is the area under
that curve.

```python
metrics.average_precision([0.9, 0.8, 0.7], [1, 0, 1], n_positives=2)
# 0.8333   (all-point interpolation)
metrics.average_precision([0.9, 0.8, 0.7], [1, 0, 1], 2, method="11")
# 0.8485   (11-point interpolation)
```

| Step | score | tp | cumulative precision | recall |
| --- | --- | --- | --- | --- |
| 1 | 0.9 | 1 | 1.000 | 0.5 |
| 2 | 0.8 | 0 | 0.500 | 0.5 |
| 3 | 0.7 | 1 | 0.667 | 1.0 |

All-point AP = mean of the precision envelope at each recall step = `(1.0 + 0.5 + 0.667) / ...`
evaluated as the step area: 0.5 * 1.0 + 0.5 * 0.667 = **0.833**. The 11-point variant
samples recall at 0, 0.1, ..., 1.0 and gives **0.848**. Both are "AP"; the number is only
comparable within one convention, which is why papers state theirs.

### mAP and the threshold ladder

mAP is AP averaged over classes. `mAP@0.5` uses IoU 0.5; `mAP@[.5:.95]` averages over ten
IoU thresholds from 0.5 to 0.95. The second is much stricter because localisation must be
tight, not merely correct.

Measured on this section's detector (Lab 5/6):

| Metric | Value |
| --- | --- |
| mAP@0.5 | 0.324 |
| mAP@[.5:.95] | 0.088 |
| AP50 circle / square / triangle | 0.334 / 0.104 / 0.532 |

A 3.7x drop from 0.5 to the ladder is normal for a small model: boxes are approximately
right, not tightly right.

## The threshold sweep, and how to choose

Lab 6 decodes once at a permissive threshold and filters by score:

| score threshold | precision | recall | F1 | tp | fp | fn |
| --- | --- | --- | --- | --- | --- | --- |
| 0.05 | 0.103 | 0.613 | 0.177 | 38 | 330 | 24 |
| 0.30 | 0.200 | 0.613 | 0.302 | 38 | 152 | 24 |
| 0.50 | 0.320 | 0.516 | 0.395 | 32 | 68 | 30 |
| 0.70 | **0.568** | 0.339 | **0.424** | 21 | 16 | 41 |
| 0.90 | 0.667 | 0.194 | 0.300 | 12 | 6 | 50 |

The sweep says something the aggregate number hides: this model has two operating points
that are both defensible. At 0.70 it is precise and misses half the objects; at 0.30 it
finds 61% of objects and is wrong most of the time it speaks.

!!! note "There is no correct threshold, only a defensible one"
    Choose by cost: a missed defect (false negative) versus a false alarm that wastes a
    human review (false positive). Write the choice down with the cost reasoning. "We used
    0.5 because it is the default" is not a justification.

## Why mAP can hide a bad model

mAP is computed over the whole test set and is insensitive to class balance and object
size. A model that is excellent on large objects and blind to small ones can still post a
respectable mAP. Report, alongside it:

- per-class AP (a weak class disappears in the average),
- performance by object size bucket,
- the prediction count, because 190 predictions for 62 objects is a fact about the model
  that mAP alone conceals.

## Practice

1. Compute IoU by hand for `(0,0,10,10)` vs `(5,5,15,15)` and check with `box_iou`.
2. Reproduce the AP table above by stepping through scores manually, then check both AP
   conventions.
3. Run the sweep and choose a threshold for a use case you define (for example, a security
   camera where missing a person is worse than a false alarm).
4. Report per-class AP and explain the weakest class.

## Check yourself

1. Two predictions on one ground truth: what are tp and fp, and which rule enforces it?
2. Why is mAP@[.5:.95] lower than mAP@0.5, and what does a large gap tell you?
3. You raise the score threshold from 0.3 to 0.7. Which of tp, fp, fn can change, and in
   which direction?

## What comes next

[CV10](cv10-segmentation.md) replaces boxes with per-pixel labels, where "accuracy" is
even more misleading and IoU has to be computed per class.
