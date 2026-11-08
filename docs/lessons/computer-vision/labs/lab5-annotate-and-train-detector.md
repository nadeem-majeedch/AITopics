# Lab 5 - Annotate images and train an object detector

**Section path:** [Overview](../index.md) · Module [CV08](../cv08-training-detectors.md) · **Lab 5** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 15% of the section assessment |
| **Time** | 5 hours |
| **Hardware** | CPU-only (80 epochs on 160 images: a few seconds) |
| **Code** | `projects/computer-vision/lab5_detector_training.py` |
| **Prerequisite** | CV02, CV08 |

## The task

Take an annotated detection set, **audit the annotations**, train a heatmap detector, and
report mAP@0.5. The audit is not a formality: in this section's own development, an
inverted-box bug in the COCO reader produced 274 invalid annotations and mAP of exactly
0.000 while the loss curve looked perfectly healthy.

Deliverables:

1. an annotation audit with zero problems,
2. YOLO labels exported from the COCO file and read back, boxes agreeing to a pixel,
3. a trained checkpoint and its mAP@0.5, precision, recall,
4. a note on the three failures you had to fix to get a non-zero mAP.

## Setup

```bash
python scripts/make_vision_data.py
cd projects/computer-vision
python lab5_detector_training.py
```

```text
data/detection/
  images/det_0000.png ... det_0199.png      # 64x64 RGB
  annotations_coco.json                     # 302 boxes, categories 1..3
```

Classes: circle, square, triangle. 200 images, 1-2 objects each, boxes from the rendered
mask extents. Licence CC0-1.0 (generated).

### Manual annotation, if you use your own images

1. Pick 60-150 images; annotate with one tool (CVAT, Label Studio, LabelImg) and one
   convention.
2. Write the class definitions **before** annotating, including "partially visible" and
   "too small to label".
3. Annotate 10, then re-annotate blind the next day; below ~85% agreement means the
   definition is wrong.
4. Export COCO, run the audit, fix every problem, then train.
5. Version the annotations and a manifest with image hashes; keep large images out of git.

## Run it

```bash
python lab5_detector_training.py --epochs 80
```

Verified output:

```text
images 200  train 160  test 40
boxes  302  classes ('circle', 'square', 'triangle')
annotation check: 0 problem(s)

=== test metrics at score threshold 0.30, IoU 0.50
mAP@0.5     0.324
precision   0.200
recall      0.613
predictions 190 for 62 ground-truth boxes
  AP50 circle   0.334
  AP50 square   0.104
  AP50 triangle 0.532

checkpoint .../outputs/detector.pt
report     .../outputs/lab5_detector_report.json

0 failure(s)
PASS  detector trained, decoded, and scored on held-out images
```

Model: `TinyHeatmapDetector`, width 24, stride 4, 16x16 output grid, focal loss
(alpha 2, beta 4), size L1 weight 0.5, 80 epochs, batch 16, lr 2e-3.

## How the pieces fit

| Stage | Function | What to check |
| --- | --- | --- |
| Target | `build_heatmap_target` | Gaussian peak at the box centre; size supervised over the bump |
| Loss | `centernet_focal_loss` | peaks only at objects; not saturated |
| Decode | `decode_heatmap` | unique maxima, no box-per-cell |
| Score | `quick_detector_metrics` | mAP, per-class AP, prediction count |

## The three failures behind this number

Reproduce them; they are the lab's real content.

| Failure | Symptom | Cause |
| --- | --- | --- |
| Invalid annotations | audit reports 274 problems, mAP 0.000 | COCO reader converted an already-`xywh` bbox |
| Saturated heatmap | 397 predictions for 62 boxes, mAP 0.006 | `pos_weight=20` BCE pushed every cell positive |
| Flat-map peaks | a box per cell on a uniform heatmap | `>=` neighbour test counts ties as peaks |

```bash
python lab5_detector_training.py --epochs 20 --loss bce --pos-weight 20   # see failure 2
```

## Test cases

| Check | Expected | Verification |
| --- | --- | --- |
| Annotation audit | 0 problems | printed |
| YOLO round trip | boxes within 1 px | your export/read check |
| mAP in [0, 1] | yes | printed |
| Predictions produced | > 0 and not one per cell | printed count vs 24x24 grid |
| Checkpoint | loads, reproduces the metrics | reload and re-score |
| Determinism | same seed, same mAP | rerun |
| Per-class AP | three values | printed |

```bash
python -m unittest tests.test_computer_vision.TestHeatmapDetection -v
```

## Rubric

| Criterion | Marks | What earns full marks |
| --- | --- | --- |
| Annotation quality and audit | 25 | zero problems, YOLO export verified, definitions written |
| Training pipeline | 25 | targets, loss, decode each explained and traceable |
| Measured metrics | 20 | mAP, per-class AP, precision/recall, N stated |
| Failure analysis | 20 | three failures reproduced and diagnosed, not just cited |
| Reproducibility | 10 | seeds fixed, versions recorded, checkpoint reloads |

## Extensions

1. Overfit five images and confirm mAP near 1.0. If not, the pipeline is broken.
2. Train with `loss="bce", pos_weight=20`. Report prediction count and mAP.
3. Revert size supervision to the single centre cell. Report the mAP drop.
4. Lower the score threshold to 0.05 and report how precision and recall move.

## Submit

```text
cv-lab5/
  README.md
  audit.txt              # annotation audit output
  labels/                # YOLO labels exported from COCO
  metrics.md             # mAP, per-class AP, precision, recall, N
  failures.md            # the three failures, with numbers
```

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| mAP exactly 0.000 | invalid boxes or a saturated heatmap | run the audit; inspect the prediction count |
| 300+ predictions | peak rule counting ties, or BCE saturation | check both |
| `width` mismatch on load | checkpoint trained with width 24 | construct the model with the same width |
