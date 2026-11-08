# P07 - Fine-tuned object detector for everyday objects

```markdown
**Projects:** [Index](index.md) · [Completion checklist](completion-checklist.md) · [Report template](report-template.md)
```

| | |
| --- | --- |
| **Difficulty** | Advanced |
| **Effort** | 50-65 hours |
| **Hardware** | CPU-trainable on the small course set (minutes); a GPU session for real images |
| **Prerequisites** | [CV02 annotations](../../lessons/computer-vision/cv02-datasets-and-annotation-formats.md), [CV05 classification from scratch](../../lessons/computer-vision/cv05-classification-from-scratch.md), [CV08 training detectors](../../lessons/computer-vision/cv08-training-detectors.md), [CV09 boxes, IoU, mAP](../../lessons/computer-vision/cv09-boxes-iou-map.md), [CV14 evaluation](../../lessons/computer-vision/cv14-evaluation-robustness-deployment.md) |
| **Builds on** | Computer Vision labs 5 and 6 |

## 1. Problem statement and motivation

Counting and locating objects is the core of most practical vision systems: parts on
a bench, boxes on a pallet, cups on a tray. A classifier says "there is a cup
somewhere"; a detector says "there is a cup here, and here, and nothing there".

Detection is also where students most often report a number they cannot defend.
mAP is an average over classes and thresholds, and a single number hides the class
that never works. This project requires the full evaluation: per-class AP, IoU
threshold sweeps, small-object slices, and an operating point chosen for a stated
cost.

**Decision supported:** which regions contain an object, at what confidence, and
when the system should flag an image for a human.

## 2. Intended learning outcomes

1. Convert and validate annotations between formats (COCO, YOLO, and your internal
   record), and catch box errors before training.
2. Train a small detector from scratch, then adapt a pretrained one if available.
3. Implement IoU, matching, precision/recall curves, and AP correctly, and verify
   them against a hand-computed example.
4. Report mAP@0.5, mAP@0.5:0.95, per-class AP, and the effect of score threshold.
5. Analyse failures by size, occlusion, class, and background.
6. Choose an operating threshold from a cost argument and document it.
7. Package inference with visual output and a latency measurement.

## 3. Difficulty and prerequisites

**Level:** Advanced. 50-65 hours: 12 data and annotations, 10 baselines, 14
training, 14 evaluation, 10 packaging and writing.

Requires CV08 and CV09. If you cannot compute AP by hand for a five-box example,
do that first; the rest of the project depends on it.

## 4. Scope and out-of-scope features

**In scope**

- 2-5 object classes, 150+ annotated images (or the course's generated set).
- A from-scratch heatmap or anchor-free detector as the offline baseline.
- Optional adaptation of a pretrained detector, with the licence recorded.
- Full detection evaluation and an operating point.
- A CLI that writes annotated images and a JSON predictions file.
- A documented annotation guide and an inter-annotator check on 20 images.

**Out of scope**

- Instance segmentation or panoptic labels.
- Tracking across frames (P09).
- Real-time video throughput claims without measuring on the target machine.
- Detecting people for surveillance, face recognition, or identity inference.
- Training on scraped images without a licence record.

## 5. Dataset options, licences, and preparation

| Option | Source | Licence | Notes |
| --- | --- | --- | --- |
| A (default, offline) | `python scripts/make_vision_data.py` → `data/computer-vision/detection/` (images, YOLO labels, COCO json, `data.yaml`) | CC0-1.0, generated | 3 classes, small images, fast training |
| B | Your own annotated photos | Yours; consent for people | Best learning; 150+ images, varied lighting |
| C | A public detection set | Record the exact licence; many are research-only | COCO images carry per-image Flickr licences; check before redistributing |

**Preparation**

1. Generate option A and verify the dataset card.
2. Validate annotations: every box inside the image, width and height positive,
   class id in range, no duplicate boxes above 0.95 IoU within an image. Write the
   validator before training.
3. Convert formats once and test round-trip equality (COCO → internal → COCO) so
   you know the conversion is lossless for your fields.
4. Split by source image, stratified by class presence. Record per-class instance
   counts per split.
5. Write the annotation guide: what counts as an object, what to do with partial
   occlusion, minimum box size, and whether groups count as one or many.
6. Label 20 images twice, a day apart, and report agreement (box count difference
   and mean IoU of matched boxes). This is your label-noise estimate.

## 6. Recommended baseline

**Zero-shot pretrained detector** (if weights are available offline): run it on the
test set and report per-class AP for the classes it knows. This establishes what
"no training" achieves.

**From-scratch heatmap detector** on the course data: a small convolutional network
predicting objectness and box offsets on a grid, decoded to boxes. This is the
baseline you must beat with any adaptation, and it runs on CPU.

## 7. Milestones

| # | Milestone | Evidence | Hours |
| --- | --- | --- | --- |
| 1 | Annotations validated | Validator output, round-trip test, agreement score | 12 |
| 2 | Metrics from scratch | Hand-checked AP, IoU tests | 8 |
| 3 | From-scratch detector | Training curve, mAP@0.5 on test | 12 |
| 4 | Adaptation | Pretrained fine-tune or justified alternative | 12 |
| 5 | Evaluation | Per-class AP, threshold sweep, size slices | 10 |
| 6 | Package | CLI, annotated outputs, model card, report | 11 |

## 8. Repository or folder structure

```text
capstone-p07/
  README.md
  requirements.txt
  configs/
    train.yaml            # grid size, epochs, lr, augmentation, score threshold
  data/
    dataset-card.md
    label-guide.md
    annotations/          # converted json; raw images not committed
    splits.json
  src/
    validate_annotations.py
    convert.py            # COCO <-> YOLO <-> internal
    metrics.py            # iou, match, ap, map
    train.py
    decode.py             # heatmap/offset to boxes, nms
    evaluate.py
    predict.py            # images -> json + annotated png
  tests/
    test_iou.py
    test_ap_hand_checked.py
    test_convert_roundtrip.py
  reports/
    report.md
    model-card.md
  outputs/
    metrics.json
    per_class_ap.csv
    threshold_sweep.csv
```

## 9. Detailed development tasks

1. `validate_annotations.py`: schema and geometry checks, duplicate detection, and
   a summary table per class. Exit non-zero on failure so it can run in CI.
2. `metrics.py`: implement IoU, greedy matching by descending score at a fixed IoU,
   precision/recall arrays, and AP by the interpolation rule you state explicitly
   (11-point or all-point). Verify against a hand-computed 5-box example in a test.
3. `convert.py`: conversions with explicit field mapping. Round-trip test must be
   exact for integer pixel coordinates; document any rounding.
4. `decode.py`: turn network outputs into boxes, apply non-maximum suppression, and
   test with two overlapping boxes where the correct suppression is known.
5. `train.py`: from-scratch detector on the course set. Log loss components
   (objectness, box regression) separately; a single total loss hides which head
   is failing.
6. Adaptation: if a pretrained detector is available, fine-tune with a small
   learning rate and report the frozen-backbone variant too. If not, document the
   constraint and compare two from-scratch configurations instead. Do not claim a
   fine-tune you did not run.
7. `evaluate.py`: mAP@0.5, mAP@0.5:0.95, per-class AP, and AP by object size
   (small/medium/large using your own area thresholds, stated). Save everything.
8. Threshold sweep: precision, recall, F1, and false positives per image across
   score thresholds 0.05-0.95. Choose the operating point from a cost statement:
   what does a missed object cost versus a false alarm?
9. Failure analysis: 20 worst images by false negatives, 20 by false positives.
   Categorise: occlusion, truncation, small size, unusual background, label error,
   class confusion. Report counts and show six examples.
10. `predict.py`: write annotated PNGs with boxes, labels, scores, and a manifest
    JSON. Include the threshold used in the output filename or metadata.
11. Model card: classes, intended use, mAP with the IoU definition, worst slices,
    latency, prohibited uses (surveillance, safety-critical counting without human
    check).
12. Measure latency per image (median, p95) and model size at the chosen threshold.

## 10. Testing and evaluation plan

| Test | Proves | Pass condition |
| --- | --- | --- |
| IoU unit test | Geometry is correct | Hand cases: identical 1.0, disjoint 0.0, half-overlap known value |
| AP hand-check | Averaging is correct | 5-box example matches the documented value |
| Conversion round-trip | No silent data loss | Re-converted annotations equal the originals |
| Annotation validator | Bad boxes are caught | Out-of-bounds box and zero-area box both fail |
| NMS test | Suppression works | Overlapping duplicates collapse to one box |
| Determinism | Training is repeatable | Same seed, same first-epoch loss within tolerance |
| Reload test | Artifact works | Saved weights reproduce 5 stored predictions |

Protocol: select the operating point on validation, then report test metrics at
that point plus the full sweep. Test is evaluated once for the final numbers.

## 11. Metrics

**Quantitative**

| Metric | Why |
| --- | --- |
| mAP@0.5 | Standard comparability |
| mAP@0.5:0.95 | Penalises loose localisation |
| Per-class AP | Finds the class hidden by the average |
| AP by object size | Small objects are the usual failure |
| Precision/recall at the chosen threshold | Operational behaviour |
| False positives per image | Operator workload |
| Latency median/p95, model size | Deployment constraint |

**Qualitative**

- Six failure images with a one-line cause each.
- Whether boxes are systematically loose or tight (mean IoU of true positives).
- Label quality, including the agreement score and what it implies for the ceiling.

## 12. Expected deliverables

- [ ] Annotation guide and validator.
- [ ] Format conversion with a round-trip test.
- [ ] Hand-checked AP implementation and test.
- [ ] Two detector configurations compared.
- [ ] Per-class AP, size slices, and threshold sweep.
- [ ] Failure taxonomy with examples.
- [ ] Annotated predictions and JSON manifest.
- [ ] Model card and report.
- [ ] Tests passing.

## 13. Suggested extensions

- Add a class and measure how much the existing classes degrade (catastrophic
  forgetting in a small model).
- Compare anchor-free and heatmap decoding at equal parameter count.
- Add test-time augmentation and report the latency cost against the AP gain.
- Export to ONNX or a quantised format and re-measure (links to P06/P07 deployment
  work).

## 14. Common failure modes and troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| mAP 0.0 | Coordinate convention mismatch (xywh vs xyxy, normalised vs pixels) | Print one decoded box on one image and compare with the label |
| mAP suspiciously high | Test images in training split, or labels leaked into inputs | Audit splits; confirm no filename-based shortcuts |
| Boxes all predicted at image centre | Box loss not learning | Check offset parameterisation and loss weights |
| Many duplicate boxes | NMS missing or IoU threshold too high | Apply NMS and test it explicitly |
| Small objects never detected | Grid too coarse or images downscaled too far | Increase resolution or grid; report the size slice |
| Training loss falls, mAP does not | Objectness learning, box regression failing | Log loss components separately |
| Per-class AP differs wildly | Class imbalance in instances | Report instance counts; consider sampling |

## 15. Marking rubric

| Criterion | Weight | 4 - Excellent | 3 - Meets | 2 - Approaching | 1 - Not yet |
| --- | --- | --- | --- | --- | --- |
| Data and annotation quality | 20% | Validator, guide, agreement score, clean splits | Valid annotations with documentation | Minor annotation issues | Unvalidated or unlicensed data |
| Detection implementation | 20% | Correct decoding, NMS, training with separated losses | Working detector | Partly working | Does not train |
| Metrics correctness | 20% | Hand-checked AP, per-class and size slices, threshold sweep | Correct mAP and per-class AP | mAP only | Metric wrong or absent |
| Failure analysis | 15% | Taxonomy with counts and examples, label-noise discussion | Basic error analysis | Anecdotes | None |
| Packaging and reproducibility | 15% | CLI, annotated outputs, config, one-command rerun | Runs with minor steps | Undocumented | Cannot rerun |
| Communication | 10% | Model card precise about IoU, slices, limits | Clear report | Thin | Overstated |

**Bands:** 90-100 portfolio-ready; 80-89 solid; 70-79 detector works, analysis
thin; below 70 the metric is not trustworthy.

## 16. Self-review checklist

- [ ] Annotation validator runs and catches deliberately bad boxes.
- [ ] AP is verified against a hand-computed example.
- [ ] Splits are by source image and contain no duplicates.
- [ ] mAP is reported with its IoU definition and per-class breakdown.
- [ ] Small-object performance is reported separately.
- [ ] The operating threshold comes from a cost statement.
- [ ] Failures are categorised with counts.
- [ ] Model card lists prohibited uses and latency.
- [ ] No unlicensed images are committed.

## 17. Report template

Use the shared [report template](report-template.md), adding:

1. **Annotation quality** - guide, agreement score, and error rate found by the validator.
2. **Metrics implementation** - the hand-checked example and the AP rule used.
3. **Detection results** - per-class AP, size slices, threshold sweep.
4. **Failure taxonomy** - categories, counts, six images.

## 18. Demonstration and presentation checklist

- [ ] Run inference on three images and show annotated output.
- [ ] Show a false negative and a false positive, and explain each.
- [ ] Show the threshold sweep and the chosen operating point.
- [ ] Show per-class AP and the worst class.
- [ ] Show latency and model size.
- [ ] Answer: "What would it take to count objects on a moving conveyor?"

**Demo trap:** showing only images where detection looks good. Bring the two worst.

---

**Previous:** [P06 image classifier](p06-image-classifier.md) · **Next:** [P08 speech transcription](p08-speech-transcription.md) · [Index](index.md)
