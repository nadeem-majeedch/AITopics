# CV08 - Training and validating object detectors {#cv08}

**Section path:** [Overview](index.md) · **Module 8** · [Lab 5](labs/lab5-annotate-and-train-detector.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 6 hours: 2.5 h reading, 3.5 h practice |
| **Hardware** | CPU-only (80 epochs on 160 images takes seconds) |
| **Prerequisites** | CV02 (annotations), CV05, CV09 previewed |
| **You will produce** | A trained heatmap detector, its mAP at a fixed threshold, and the three failures that produced mAP of zero before it worked |

## Why this module exists

Classification has one label per image. Detection has a variable number of objects,
each with a class and a box, and the number is not known at inference. That single change
forces a different architecture, a different target, a different loss, and a different
metric.

This module builds a deliberately small CenterNet-style detector: a fully convolutional
network that outputs a per-class centre heatmap and a box-size map. It is small enough to
train on a CPU in seconds and complete enough that every real detector's parts are
present.

## The three pieces

```text
image 64x64
   |
   v  trunk: 2x stride-2 conv, 1x stride-1 conv  ->  16x16 feature grid
   |
   +--> heat head:  (C, 16, 16) logits, one channel per class
   +--> size head:  (2, 16, 16) box width/height as image fractions
```

1. **Targets.** Each ground-truth box becomes a Gaussian bump at its centre cell. Two
   nearby objects produce overlapping bumps, which is why decoding cannot simply take
   `argmax`.
2. **Loss.** Penalty-reduced focal loss on the heatmap, L1 on size at the bump.
3. **Decode.** sigmoid -> unique local maxima -> threshold -> read size -> build box -> NMS.

## Targets: why a Gaussian and not a 1

A one-hot cell punishes a prediction one cell from the true centre as hard as a
prediction in the corner. A Gaussian says "close is nearly right", which matches how the
decode step works: it looks for peaks, and a peak one cell off is still a usable box.

```python
heat, size, mask = detection_train.build_heatmap_target(boxes, 64, 64, 3, stride=4)
print(heat.shape, size.shape, mask.shape)     # (3,16,16) (2,16,16) (1,16,16)
```

The `mask` matters more than it looks. Size is regression, and regressing size at every
background cell teaches the network to predict the dataset-average box everywhere. The
mask restricts the size loss to cells where an object actually is.

Our first version supervised size at the single centre cell only. That is ~2 gradients
per object per batch, and the size head stayed at the dataset mean, capping mAP@0.5 at
**0.130**. Widening supervision to the whole bump (`gauss >= 0.5`) took the same
configuration to **0.268** at 60 epochs. A regression head needs enough supervision
signal; one cell per object is not enough.

## Loss: the imbalance is the problem

One 16x16x3 grid has 768 cells and typically 1-3 objects. Plain binary cross-entropy
collapses to "background everywhere" because that answer is 99% correct. The obvious fix
- weight positives heavily - fails in the opposite direction.

| Loss | What happened | mAP@0.5 |
| --- | --- | --- |
| BCE, `pos_weight=20` | saturated to "object everywhere": 397 predictions for 62 boxes | 0.006 |
| Focal (alpha 2, beta 4) | peaks only at objects | 0.324 |

Measured, not asserted. The focal loss's `(1 - target) ** beta` term down-weights cells
near a centre instead of treating them as hard negatives, and `(1 - p) ** alpha` stops
easy confident cells from dominating.

```python
detection_train.centernet_focal_loss(logits, target)
```

!!! note "Reproduce the failure"
    `train_detector(..., loss="bce", pos_weight=20.0)` is still available. Run it once
    and look at the prediction count. A model that outputs a box for every cell can
    still report a falling loss - which is why you inspect predictions, not just loss.

## Decoding: from scores to boxes

```python
boxes = detection.decode_heatmap(heat_logits, size_pred, stride=4, width=64, height=64,
                                 score_threshold=0.3)
```

The peak rule must require a **unique maximum**. With `>=` against neighbours, a flat or
saturated map makes every cell a peak - one box per cell, 397 predictions, precision
0.037. The section's decoder counts equal neighbours and rejects ties; the test suite
asserts that an all-zeros map yields zero boxes.

Then non-maximum suppression removes overlapping duplicates *within a class*. Two classes
firing on the same object are not suppressed, which is why this model's precision is
0.200 while its recall is 0.613.

## The measured result

```bash
python lab5_detector_training.py
```

| Metric | Value |
| --- | --- |
| Images | 200 (160 train / 40 test), 302 boxes total |
| Epochs / width | 80 / 24 |
| mAP@0.5 | **0.324** |
| Precision / recall @ 0.3 | 0.200 / 0.613 |
| Predictions / ground truth | 190 / 62 |
| AP50 per class | circle 0.334, square 0.104, triangle 0.532 |

Square is the hardest class; circles and triangles differ in corner structure, squares
are the least distinctive at 16x16 with a 4-pixel stride. Precision is limited by
cross-class duplicates, not by localisation - a diagnostic you can confirm by looking at
the predictions.

## Validating a detector

Three checks before you believe any mAP:

1. **Annotation audit.** `validate_annotations` on the whole set. A one-line inverted-box
   bug in the COCO reader produced 274 invalid annotations and mAP **0.000**; the loss
   curve looked plausible the whole time.
2. **Overfit sanity check.** Train on 5 images and confirm mAP near 1.0. If not, the
   decode or the metric is broken, not the model.
3. **Held-out split by source.** Objects in this dataset are independent scenes, but real
   video frames are not; split by video, not by frame.

## Practice

1. Train the reference detector. Record mAP, precision, recall, and prediction count.
2. Train with `loss="bce", pos_weight=20.0`. Report mAP and prediction count.
3. Supervise size at one cell only (revert the bump) and report mAP. Explain the gap.
4. Overfit five images. Report the mAP you reach; if it is below 0.9, debug the pipeline.

## Check yourself

1. Why does a heatmap detector need local-maximum extraction rather than a plain threshold?
2. Your loss falls smoothly but mAP stays at zero. Name three causes and the check that
   distinguishes them.
3. Precision 0.20, recall 0.61. What kind of error dominates, and what would you change?

## What comes next

[CV09](cv09-boxes-iou-map.md) takes the metrics apart: IoU, greedy matching, precision,
recall, AP, and why mAP@[.5:.95] is so much lower than mAP@0.5.
