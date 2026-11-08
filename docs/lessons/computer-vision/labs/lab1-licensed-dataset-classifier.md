# Lab 1 - Build a classifier from a small, licensed dataset

**Section path:** [Overview](../index.md) · Module [CV02](../cv02-datasets-and-annotation-formats.md) · **Lab 1** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 8% of the section assessment |
| **Time** | 3 hours |
| **Hardware** | CPU-only |
| **Code** | `projects/computer-vision/lab1_dataset_and_splits.py` |
| **Prerequisite** | CV01, CV02 |

## The task

Build a three-class image dataset you can defend, split it two ways, and measure how much
the careless split inflates the score.

You must produce:

1. a **grouped split** (no source crosses train/val/test) and a **leaky split** (random per
   image),
2. a leakage audit for both, with shared-source and look-alike counts,
3. the same model trained on both, with two test accuracies and the difference,
4. a licence and attribution block for the data.

## Setup

```bash
pip install -r requirements/vision.txt
python scripts/make_vision_data.py       # ~2.3 s, deterministic
```

```text
data/classification/
  images/shape_0000.png ... shape_0299.png
  manifest.json          # source_id, label, split, hashes
  dataset_card.json      # licence CC0-1.0, sizes, class balance
```

The generated data is **CC0-1.0**: 300 images rendered from 100 sources (three variants
each), three classes (circle, square, triangle), 64x64 RGB. Each source is one rendered
object; its variants differ in position, scale, colour, noise, and blur.

If you use your own images instead, read "Manual annotation and licensing" in
[CV02](../cv02-datasets-and-annotation-formats.md) first and record the same fields.

## Run it

```bash
cd projects/computer-vision
python lab1_dataset_and_splits.py
```

Verified output on Windows 11, Python 3.12.10, torch 2.14.1+cpu:

```text
=== leakage audit
grouped by source : shared sources 0, cross-split look-alikes 1
random per image  : shared sources 91, cross-split look-alikes 14

=== test accuracy after the same training budget
grouped split : 0.822   (this is the number you may report)
leaky split   : 0.933   (inflated: test images have near-copies in train)
inflation     : +0.111

300 images from 100 sources; 0 failure(s)
PASS  source-level grouping removes the hard leak in this dataset
```

Wall time: about 3 seconds. Both runs use 12 epochs, batch 16, lr 2e-3, identical seed.

## What to do with those numbers

1. **0.111 is the size of the lie.** The leaky number is not a bug in the training code;
   it is what you get when test images are near-copies of training images. The model is
   not generalising, it is recalling.
2. **One look-alike remains in the grouped split.** Different sources can still look
   similar. The audit reports `soft_leaky` separately because near-duplicates across
   sources are sometimes legitimate and always worth reporting.
3. **Report 0.822.** If you report 0.933 you are describing a dataset that does not exist.

## Test cases

| Check | Expected | How to verify |
| --- | --- | --- |
| Grouped split shares no source | 0 shared sources | audit output |
| Leaky split does share | > 0 shared sources | audit output |
| Grouped split wins on honest measurement | leaky accuracy >= grouped | printed accuracies |
| Audit flags hard leakage | `hard_leaky == True` for leaky | `datasets.audit_leakage` |
| Manifest complete | 300 records, every field present | inspect `manifest.json` |
| Licence recorded | CC0-1.0 in `dataset_card.json` | inspect the card |
| Reproducible | two runs give identical numbers | run twice |

The section's automated suite also covers this lab's primitives:

```bash
python -m unittest tests.test_computer_vision -v
```

## Rubric

| Criterion | Marks | What earns full marks |
| --- | --- | --- |
| Correct split construction | 25 | grouped split provably free of source overlap |
| Leakage audit and interpretation | 25 | both counts reported; inflation explained in mechanism, not just number |
| Licence and attribution block | 15 | SPDX id, source, changes, redistribution status |
| Reproducibility | 15 | fixed seeds, two runs identical, versions recorded |
| Written analysis | 20 | says what the number would be on a harder task, and why this one saturates |

## Extensions

1. Make the task harder (30 training images, or a fourth class) and re-measure the
   inflation. Does the leak matter more or less when the task is hard?
2. Replace the `dhash` near-duplicate check with a stricter one and see how many extra
   pairs appear.
3. Add a per-source class balance report: are any sources mislabelled relative to their
   variants?

## Submit

```text
cv-lab1/
  README.md          # equipment, versions, exact commands, what is verified
  split_report.md    # two audits, two accuracies, the difference, the interpretation
  licence.md         # data licence, attribution, redistribution
  run_log.txt        # the full output shown above, from your machine
```

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `data/` missing | generator not run | `python scripts/make_vision_data.py` |
| Identical accuracies | split not rebuilt between runs | rebuild records inside each branch |
| Audit reports 0 shared sources for the leaky split | grouped split used twice | check which split function each branch calls |
