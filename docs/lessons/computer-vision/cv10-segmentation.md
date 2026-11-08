# CV10 - Image segmentation and segmentation metrics {#cv10}

**Section path:** [Overview](index.md) · **Module 10** · [Assessment](assessment.md) · Hands-on: `segmentation_demo.py`

| | |
| --- | --- |
| **Study time** | 5 hours: 2 h reading, 3 h practice |
| **Hardware** | CPU-only (three training runs in ~18 s) |
| **Prerequisites** | CV04, CV09 |
| **You will produce** | A segmented mask set, a control baseline, and a written explanation of why the first run "worked" at 0.96 accuracy while predicting no objects |

## Why this module exists

Detection says *where objects are*. Segmentation says *which pixels belong to what*.
The output is a label per pixel, the metric is per-class IoU, and the failure mode is
specific: with 95% background, a model that predicts background everywhere scores 0.95
accuracy while being useless.

This module's hands-on program is built around that failure, and around the wrong
diagnosis for it.

## Three kinds of segmentation

| Kind | Output | Example |
| --- | --- | --- |
| Semantic | one class per pixel, no instances | road / sky / building |
| Instance | one mask per object | each car separately |
| Panoptic | both | scene understanding |

This section implements semantic segmentation: three classes, `background`, `object`,
`shadow`. The shadow class exists deliberately - it is small, adjacent to objects, and
makes "two classes would be easy" false.

## The architecture, and the skip connection

```python
model = models.TinyUNet(num_classes=3, width=16, use_skip=True)
```

An encoder halves resolution twice (to learn *what*), a decoder restores it (to say
*where*). Without a skip connection the decoder only has the bottleneck, which knows what
is present but has thrown away the fine boundaries.

```text
enc1 (64x64, w)  -------------------------> concat -> dec1 -> head (64x64, 3)
   enc2 (32x32, 2w) --> concat -> dec2 ---^
      enc3 (16x16, 4w) --> up --> ...
```

The section's ablation is measured rather than asserted, because on 2-3% foreground masks
the result is not guaranteed:

| Run (120 epochs, width 16, class weights) | mIoU | object IoU |
| --- | --- | --- |
| With skip | 0.705 | 0.457 |
| No skip | 0.622 | 0.331 |

Here the skip is worth ~0.08 mIoU. Re-run it yourself; small synthetic masks make this
number move, and the lab asks you to report what you got rather than to reproduce ours.

## The metric: per-class IoU, pooled

```python
report = segmentation.evaluate_segmenter(model, test_records)
print(report["pixel_accuracy"], report["mean_iou"], report["per_class_iou"])
```

- **Pixel accuracy** - fraction of correctly labelled pixels. Dominated by background.
- **IoU per class** - `tp / (tp + fp + fn)` for one class. Ignores the background majority.
- **mIoU** - mean of per-class IoU over classes *present* in the data.
- **Boundary F1** - agreement within a pixel tolerance of the true boundary; catches masks
  that are right in area but ragged at the edges.

Aggregation is over a pooled confusion matrix, not the mean of per-image IoUs: a class
absent from one image should not get a free vote in the average.

## The run that looks fine and is not

Measured by `segmentation_demo.py` on this section's 80 images (60 train / 20 test):

| Configuration | Pixel acc | mIoU | object IoU | shadow IoU |
| --- | --- | --- | --- | --- |
| All-background control | 0.953 | 0.318 | 0.000 | 0.000 |
| Threshold rule | 0.901 | 0.309 | 0.010 | 0.000 |
| 12 epochs, no weights | 0.961 | 0.431 | **0.000** | 0.331 |
| 12 epochs, class weights | 0.879 | 0.478 | 0.183 | 0.374 |
| 120 epochs, no weights | **0.982** | **0.762** | 0.538 | 0.764 |
| 120 epochs, class weights | 0.969 | 0.705 | 0.457 | 0.687 |
| 120 epochs, weights, no skip | 0.945 | 0.622 | 0.331 | 0.592 |

Read it in order:

1. **The control scores 0.953 pixel accuracy.** Anything that reports pixel accuracy
   alone is reporting the background fraction. `object IoU = 0.000` is the honest signal.
2. **At 12 epochs, unweighted, object IoU is exactly 0.000** - the model found shadows
   and nothing else. This is the collapse every tutorial tells you is class imbalance.
3. **Adding class weights at 12 epochs helps** (object 0.183), which appears to confirm
   the diagnosis.
4. **At 120 epochs, the *unweighted* run wins overall** (mIoU 0.762 vs 0.705).

So the collapse was **under-training**, not imbalance. Class weighting is a real tool -
it trades background IoU for foreground recall - but "add class weights" is a hypothesis
to test, not a rule to apply. The demo prints this conclusion from the numbers rather than
asserting it.

!!! warning "The transferable rule"
    Before changing the loss, train longer and re-measure. Loss-shaping is a common
    answer to a problem whose cause is the training budget. And always report a control
    baseline: without the all-background row, 0.96 accuracy looks like success.

## Class imbalance, honestly

Measured pixel fractions in the training split: background **0.9532**, object **0.0224**,
shadow **0.0245**. A 42:1 ratio.

Options, in increasing order of effort:

| Option | Effect | Cost |
| --- | --- | --- |
| More epochs | fixes under-training (measured above) | compute |
| Inverse-frequency class weights | raises foreground IoU, lowers background IoU | one line |
| Focal / Dice loss | targets hard pixels directly | new loss, more tuning |
| Two-stage: detect then segment | sidesteps the ratio | more moving parts |

## Practice

1. Run `python segmentation_demo.py`. Record the table.
2. Explain in three sentences why the 12-epoch unweighted run had object IoU 0.000 and
   pixel accuracy 0.961.
3. Compute mIoU by hand from the printed confusion matrix in
   `outputs/segmentation_report.json` and check it against the reported value.
4. Overlay a predicted mask on its image (`segmentation.overlay_mask`) and describe two
   boundary errors boundary F1 could detect but mIoU would not.

## Check yourself

1. Why is pixel accuracy a poor headline metric for this dataset, in one sentence with the
   measured numbers?
2. Your mIoU is 0.76 but object IoU is 0.54. Which class needs work, and what does mIoU
   hide?
3. A class is absent from the test set. What should mIoU do with it, and why is the
   pooled-confusion-matrix choice defensible?

## What comes next

[CV11](cv11-face-detection-vs-recognition.md) applies detection and embedding to faces -
where the technical distinctions carry legal and ethical weight, and where the measured
per-group failure is the most important number in the section.
