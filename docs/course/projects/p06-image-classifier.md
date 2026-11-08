# P06 - Image classification on a custom dataset

```markdown
**Projects:** [Index](index.md) · [Completion checklist](completion-checklist.md) · [Report template](report-template.md)
```

| | |
| --- | --- |
| **Difficulty** | Intermediate |
| **Effort** | 40-50 hours |
| **Hardware** | CPU is enough for the default 64x64 dataset; a GPU session helps for larger images |
| **Prerequisites** | [CV02 datasets and annotations](../../lessons/computer-vision/cv02-datasets-and-annotation-formats.md), [CV03 preprocessing and augmentation](../../lessons/computer-vision/cv03-preprocessing-and-augmentation.md), [CV05 classification from scratch](../../lessons/computer-vision/cv05-classification-from-scratch.md), [CV06 transfer learning](../../lessons/computer-vision/cv06-transfer-learning.md), [CV07 fine-tuning](../../lessons/computer-vision/cv07-fine-tuning.md), [CV14 evaluation and deployment](../../lessons/computer-vision/cv14-evaluation-robustness-deployment.md) |
| **Builds on** | Computer Vision labs 1-4 |

## 1. Problem statement and motivation

A small organisation has images it cares about - produce at a market stall, parts
on a bench, plants in a greenhouse, garments on a rail - and a person who sorts
them by eye. A classifier can pre-sort and flag uncertainty, saving time and
reducing mistakes, provided it is evaluated on the conditions it will actually see.

This project is the standard transfer-learning workflow done properly: a real
dataset you assembled, a documented split, augmentation that matches the
deployment, and an evaluation that separates "works on my test folder" from "works
on a phone photo at dusk".

**Decision supported:** a suggested category with a confidence, and an explicit
"not sure" that routes the image to a human.

## 2. Intended learning outcomes

1. Assemble and document an image dataset with a label guide and a licence record.
2. Build leakage-safe splits at the level of the source image, not the augmented copy.
3. Train a from-scratch baseline and a transfer-learning model, and compare them.
4. Apply augmentation deliberately and show what each transform does to errors.
5. Evaluate with per-class metrics, a confusion matrix, calibration, and slice analysis.
6. Measure robustness to brightness, blur, rotation, and background change.
7. Report size, latency, and confidence behaviour for a realistic deployment.

## 3. Difficulty and prerequisites

**Level:** Intermediate. 40-50 hours: 10 data, 8 baselines, 10 training, 12
evaluation, 10 writing and demo.

Requires CV02-CV07 and CV14. You should be able to explain what a pretrained
backbone has already learned and why freezing layers changes the result.

## 4. Scope and out-of-scope features

**In scope**

- 4-10 classes. The 120-image course smoke set is useful for the early labs but
  is not enough for a stable four-class capstone estimate. The provided P06 set
  has 960 images from 240 source groups, with 168/144/144 images in
  train/validation/test and 36 test images per class. For your own dataset, start
  with 40+ per class but aim for about 30 **test** images per class (roughly
  150-200 images per class at a 70/15/15 split), or use a larger public dataset.
- One from-scratch small CNN and one transfer-learning model.
- Documented augmentation policy and a split audit.
- Per-class metrics, confusion matrix, calibration, and at least three robustness slices.
- A single-image CLI and a batch mode that writes predictions with confidence.

**Out of scope**

- Detecting multiple objects per image (that is P07).
- Video input (P09, P11).
- Face recognition, identity inference, or any classification of people's
  sensitive attributes. Not acceptable in this course.
- Web deployment with authentication. A local CLI or a static demo is enough.
- Claims of production accuracy from a small convenience sample.

## 5. Dataset options, licences, and preparation

| Option | Source | Licence | Notes |
| --- | --- | --- | --- |
| A (default, offline) | `python scripts/make_vision_data.py` → `data/computer-vision/objects_p06/` (960 images, 4 classes, 240 source groups) for P06; `objects/` (120 images) remains the early-lab smoke set | CC0-1.0, generated | Stratified 168/144/144; 36 test images per class; small and fast on CPU |
| B | Fashion-MNIST via torchvision | MIT per the dataset repository | 28x28 greyscale; good for a first pass, weak for transfer learning stories |
| C | Your own photographs | Yours; consent required for any person visible | Best learning, most work; 40+ per class to start, 150-200 for 30 test per class, varied conditions |
| D | A public dataset | Record the exact licence string | Many "research only" sets cannot be used in a portfolio; check before downloading |

**Preparation**

!!! warning "Check class coverage before checkpoint 2"
    The 120-image `objects/` smoke set splits 84/18/18 by **source**, not by class.
    With only six test sources, a class can be absent from test: a pilot run of
    the 120-image set produced zero phone test images, so phone precision and
    recall were undefined. Use `objects_p06/` for the capstone, or run
    `src/prepare.py` and stop if any test class has zero images. Fix absence by
    assigning whole source groups per class to a stratified split (the helper is
    `vision_core.datasets.stratified_group_split`); that does not fix the sample
    size. For a usable estimate, collect 40+ images per class to start, and
    roughly 150-200 per class at a 70/15/15 split so the test split has about 30
    per class. Do not report a per-class metric computed from zero examples, and
    do not describe the 120-image set as a reliable four-class benchmark.

1. Generate option A and verify it: run the generator, then
   `python scripts/make_vision_data.py --check`. The check verifies every image
   against `objects_p06/manifest.json`, reports class counts and source overlap,
   and writes `manifest_check.json`. A non-zero exit status or any problem code
   means the data is not what the manifest describes; fix it before training.
2. Write a label guide before labelling: one paragraph per class, plus two
   boundary examples ("this is a mug, not a bowl, because...").
3. Split by source group. If one object was photographed ten times, all ten go to
   one split. Augmented copies never cross splits. Use
   `vision_core.datasets.stratified_group_split` so every class gets a source in
   validation and test; do not shuffle individual images.
4. Record image counts per class per split. Flag any class under 30 test images as
   too small for a reliable per-class estimate. The provided `objects_p06/` set
   has 36 per class; the 120-image smoke set cannot meet the target.
5. Resize consistently and record the interpolation method; store the resize
   decision in the config, not in a notebook cell.

## 6. Recommended baseline

**Majority class**, then **logistic regression on flattened pixels or simple colour
histograms**. Both are fast and expose whether the task is trivial. Then a small CNN
trained from scratch as the neural baseline, and finally transfer learning with a
frozen backbone followed by limited fine-tuning.

Report all four in one table. If transfer learning does not beat the from-scratch
CNN, investigate before concluding anything: check input normalisation, learning
rate, and whether the backbone was actually frozen.

## 7. Milestones

| # | Milestone | Evidence | Hours |
| --- | --- | --- | --- |
| 1 | Dataset and label guide | Counts, split audit, licence record | 10 |
| 2 | Baselines | Majority, pixel/colour model, small CNN | 8 |
| 3 | Transfer learning | Frozen then fine-tuned, same splits | 10 |
| 4 | Evaluation | Per-class metrics, confusion, calibration | 8 |
| 5 | Robustness | Brightness, blur, rotation, background slices | 8 |
| 6 | Package | CLI, model card, report, rerun | 6 |

## 8. Repository or folder structure

```text
capstone-p06/
  README.md
  requirements.txt
  configs/
    train.yaml            # image size, batch, lr, epochs, augmentation policy
  data/
    dataset-card.md
    label-guide.md
    splits.json           # image path -> split, grouped by source
  src/
    prepare.py            # verify counts, write splits, check leakage
    datasets.py           # transforms, loaders, deterministic sampling
    train.py              # scratch CNN or transfer, saves weights + log
    evaluate.py           # metrics, confusion, calibration, slices
    robustness.py         # perturbation sweep
    predict.py            # single image and batch
  tests/
    test_splits.py
    test_transforms.py
    test_predict.py
  reports/
    report.md
    model-card.md
  outputs/
    metrics.json
    confusion_test.csv
    robustness.json
```

## 9. Detailed development tasks

1. `prepare.py`: scan the dataset, verify every image opens, record dimensions and
   modes, and write `splits.json`. Refuse to proceed if a source group appears in
   two splits.
2. `datasets.py`: deterministic transforms for train and evaluation. Training
   augmentation: random crop or flip only if it preserves the label. Evaluation:
   resize and normalise only. Never augment the test set.
3. Train the small CNN: three or four convolutional blocks, global average pooling,
   dropout, early stopping on validation loss. Record the parameter count.
4. Transfer learning: load a small pretrained backbone available offline in your
   environment; if no weights can be downloaded, say so and use the from-scratch
   model as the main result rather than pretending.
5. Stage 1: freeze the backbone, train the head. Stage 2: unfreeze the last block
   with a ten-times smaller learning rate. Report both stages separately.
6. `evaluate.py`: accuracy, macro F1, per-class precision/recall/F1, confusion
   matrix with counts, top-2 accuracy, expected calibration error, and bootstrap
   confidence intervals for accuracy, macro F1, and each class. Save every number
   to `metrics.json`.
7. Calibration: reliability table with 10 bins and bin counts. Fit temperature
   scaling on **validation only**, report raw and calibrated ECE, and do not
   choose the temperature on test.
8. Robustness and inference strategy: for each perturbation (brightness ±40%,
   Gaussian blur with three strengths, rotation ±15°, background substitution if
   you have masks), report accuracy and macro F1 on the test set. Compare ordinary
   inference with a fixed test-time augmentation (for example identity, two
   brightness scales, and a horizontal flip) under the **same** conditions. A
   test-time change is not training augmentation. State that this is a synthetic
   stress test, not deployment evidence.
9. Slice analysis: by class, by source (if multiple), by image size, by brightness
   quartile. Report counts. Identify the worst slice and show three examples.
10. `predict.py`: print top-3 classes with probabilities; if max probability is
    below τ, print "uncertain - send to human". Choose τ from the validation
    precision/coverage curve.
11. Model card: intended use, classes, data provenance, metrics with intervals,
    calibration, worst slices, prohibited uses (no person classification, no safety
    certification).
12. Clean rerun and a short latency measurement: median and p95 ms per image on CPU.

## 10. Testing and evaluation plan

| Test | Proves | Pass condition |
| --- | --- | --- |
| Split leakage test | No source group crosses splits | Intersection empty |
| Manifest test | Every image matches its recorded digest and label | `--check` exits 0, or reports the exact failing files |
| Image integrity test | Corrupt files are caught | A truncated PNG raises a clear error |
| Transform test | Evaluation is deterministic | Same image twice gives identical tensor |
| Metric test | Your metrics are right | Hand-computed 6-image case matches |
| Checkpoint reload | The artifact works | Reloaded model reproduces 5 stored predictions |
| Calibration test | Bins are correct | Bin edges and counts verified on a toy array |
| CLI test | Inference works outside training | `predict.py image.png` prints top-3 and exits 0 |

Protocol: choose hyperparameters on validation; evaluate test once for the final
table. Robustness runs are reported separately and never used to pick the model.

## 11. Metrics

**Quantitative**

| Metric | Why |
| --- | --- |
| Macro F1 | Class balance matters more than raw accuracy |
| Per-class precision and recall | Finds the class that ruins the average |
| Confusion matrix (counts) | Shows which classes merge |
| Top-2 accuracy | Whether the right answer is at least considered |
| Expected calibration error, raw and calibrated | Confidence is shown to a human |
| Bootstrap 95% confidence intervals | Small-test uncertainty is visible |
| Test-time augmentation comparison | Whether inference-time averaging helps or hurts |
| Accuracy under each perturbation | Honest robustness evidence |
| Parameter count, model size, latency | Deployment constraints |

**Qualitative**

- Three misclassified images with an explanation of what the model likely used.
- Whether background or lighting is doing the classification, tested by a simple
  background swap or crop.
- A statement that a small convenience dataset cannot support claims about the
  real world.

## 12. Expected deliverables

- [ ] Dataset card, label guide, and split audit.
- [ ] Dataset manifest check output (`manifest_check.json`), including any warnings.
- [ ] Five-condition comparison table: majority, colour histogram, scratch CNN, frozen probe, fine-tuned.
- [ ] Training curves (loss and validation metric) with the epoch chosen marked.
- [ ] Confusion matrix, per-class table, bootstrap confidence intervals, and raw/calibrated calibration table.
- [ ] Robustness table across at least three perturbations, with ordinary versus test-time-augmented inference.
- [ ] A statement that the synthetic 960-image set is an educational prototype, not real-world evidence.
- [ ] Model card and report.
- [ ] CLI with uncertainty threshold.
- [ ] Tests passing.

### Submission package and P06 requirements

Copy the ten files from the [capstone submission package](submission-package.md)
and submit them at the three checkpoints: scope and dataset card at checkpoint 1;
running path, experiment log, reproducibility and draft cards at checkpoint 2;
evaluation report, threat review, release notes and final report at checkpoint 3.

P06-specific rules for those files:

- **Name the data limitation in every summary.** The supplied `objects_p06/` set is
  synthetic, generated by one renderer, with 960 images and 36 test images per
  class. Write "accuracy on a synthetic teaching set", never "real-world accuracy".
- **Record the generator check.** Run
  `python scripts/make_vision_data.py --check` and put the result in
  `reproducibility.md` and the dataset card. Report every warning (for example,
  identical variants of one source), not only the pass line.
- **Report the required evaluation.** Per-class precision, recall and F1 with
  bootstrap confidence intervals; the confusion matrix; raw and calibrated ECE with
  the temperature fitted on validation; and at least three perturbations under
  ordinary and test-time-augmented inference.
- **Keep test untouched.** Thresholds, temperature, and model selection come from
  validation. State how many times the test split was opened.
- **Do not present a synthetic result as evidence of real-world reliability.** If
  you use your own photographs instead, say how many sources, classes, and test
  images per class, and repeat the same tables.

## 13. Suggested extensions

- Compare two augmentation policies at equal training budget and report the
  difference with a confidence interval.
- Add a background-only control: train on images with the object masked out and see
  how much accuracy survives.
- Export the model to a smaller runtime format and measure the size/latency change.
- Add an active-learning loop: label the 20 most uncertain unlabelled images and
  measure the change.

## 14. Common failure modes and troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Validation accuracy near 1.0, test much lower | Augmented copies or one object in both splits | Split by source group; recheck `splits.json` |
| Model predicts one class | Class imbalance or learning rate too high | Class weights, lower LR, check per-class counts |
| Transfer learning worse than scratch | Wrong normalisation or frozen backbone with mismatched head | Match preprocessing; train the head first |
| Accuracy collapses under blur | Test distribution differs from training augmentation | Add mild blur to training only, re-evaluate |
| Confident wrong predictions | Overfitting or uncalibrated outputs | Early stopping, temperature scaling, abstention |
| Different results each run | Unseeded loaders or non-deterministic ops | Seed everything; document residual nondeterminism |
| Images load fine on Windows, fail on Linux | Case-sensitive paths or backslashes | Store relative POSIX paths |

## 15. Marking rubric

| Criterion | Weight | 4 - Excellent | 3 - Meets | 2 - Approaching | 1 - Not yet |
| --- | --- | --- | --- | --- | --- |
| Dataset and labelling | 20% | Licence, label guide, grouped splits, integrity checks | Documented dataset with clean splits | Weak documentation or small classes | Unlicensed or leaking data |
| Modelling | 20% | Baselines plus staged transfer learning, justified choices | Two models compared | One model, no baseline | Model unexplained |
| Evaluation | 25% | Per-class, calibration, slices, intervals | Correct metrics and confusion matrix | Accuracy only | Misleading evaluation |
| Robustness and failure analysis | 15% | Perturbation sweep and worst-slice examples | Basic robustness check | Mentioned only | Ignored |
| Reproducibility | 10% | Config-driven, seeded, one-command rerun | Minor manual steps | Undocumented | Cannot rerun |
| Communication | 10% | Model card and report precise about scope | Clear report | Thin | Overstated |

**Bands:** 90-100 portfolio-ready; 80-89 solid; 70-79 works, analysis thin; below
70 the evaluation cannot support the claim.

## 16. Self-review checklist

- [ ] Splits are grouped by source and the audit passes.
- [ ] `python scripts/make_vision_data.py --check` passes; any duplicate-variant
      warnings are reported.
- [ ] Test images were never augmented or used for tuning.
- [ ] Four models appear in one comparison table.
- [ ] Per-class metrics, the confusion matrix, and confidence intervals are reported.
- [ ] Calibration is measured, and thresholds and temperature come from validation.
- [ ] At least three perturbations are measured.
- [ ] The worst slice has examples and an explanation.
- [ ] Model card lists prohibited uses.
- [ ] No personal images or unlicensed material are committed.

## 17. Report template

Use the shared [report template](report-template.md), adding:

1. **Dataset** - collection, labelling, class counts, licence, known gaps.
2. **Model comparison** - four rows, with the training budget for each.
3. **Error analysis** - confusion pairs, three examples, background test.
4. **Robustness** - perturbation table, ordinary versus test-time-augmented inference, and what it does and does not prove.

## 18. Demonstration and presentation checklist

- [ ] Classify five images: four in-distribution, one blurry or dark.
- [ ] Show top-3 with probabilities and the abstention behaviour.
- [ ] Show the confusion matrix and the worst class.
- [ ] Show the robustness table and one failure image.
- [ ] Show model size and latency.
- [ ] State two limitations and one prohibited use.
- [ ] Answer: "Would you ship this to a warehouse tomorrow? Why not?"

**Demo trap:** choosing the five demo images after seeing which ones work. Use a
pre-declared set.

---

**Previous:** [P05 local assistant](p05-local-assistant-gui.md) · **Next:** [P07 object detector](p07-object-detector.md) · [Index](index.md)
