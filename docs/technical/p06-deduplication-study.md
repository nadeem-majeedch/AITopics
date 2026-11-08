# P06 duplicate-variant deduplication study

**Date:** 2026-11-07  
**Scope:** the 57 duplicate-content warnings in `objects_p06`  
**Verdict:** **KEEP v1.0.0 as the recommended dataset.** Removing the duplicates
does not improve clean accuracy, calibration, or robustness. It is a safe optional
variant for audits, not a better default.

!!! note "This is a controlled experiment, not a dataset replacement"
    The original `data/computer-vision/objects_p06/` directory was not modified.
    The experimental datasets sit beside it, use their own manifests, and are not
    part of the course's default path. Historical pilot metrics are retained.

## 1. Question

`scripts/make_vision_data.py --check` reports 57 duplicate-content warnings on the
960-image P06 set. The warnings are same-source, same-label, same-split pairs (and
one triple), so the earlier interpretation was "redundant data, not leakage". This
study asks whether that redundancy is harmless, helpful, or worth removing:

1. Are the duplicates byte-identical or only visually similar?
2. Are they concentrated in a class, source, or split?
3. Does removing them change clean accuracy, calibration, robustness, or training
   cost under an otherwise identical training protocol?
4. Which dataset version should the course recommend?

## 2. What the duplicates are

| Measure | Value |
| --- | ---: |
| Files in the original set | 960 |
| Unique byte content | 902 |
| Duplicate groups | 57 |
| Extra files (files beyond one per group) | 58 |
| Groups of size 2 / 3 | 56 / 1 |
| Source groups involved | 55 |
| Sources contributing one extra / two extras | 52 / 3 |
| Groups crossing train/validation/test | **0** |
| Groups crossing a label | **0** |
| Groups spanning more than one source | **0** |
| Groups that are byte-identical | **57 / 57** |
| Groups that are pixel-identical after decoding | **57 / 57** |
| Pixel-identical groups not found by byte hash | **0** |

Every group is exactly the same PNG bytes, so it is also the same decoded image.
There is no "looks similar but differs in a few pixels" category in this dataset:
the duplicates are exact copies produced when two variants of one source receive
the same roll offset.

### Concentration

| Class | Groups | Extra files |
| --- | ---: | ---: |
| mug | 12 | 12 |
| bottle | 15 | 15 |
| book | 13 | 13 |
| phone | 17 | 18 |

| Split | Groups | Extra files |
| --- | ---: | ---: |
| train | 44 | 44 |
| validation | 5 | 6 |
| test | 8 | 8 |

The duplicates are not confined to one class or split. Phone has the most groups;
validation has one three-file group. Three sources contribute two extra files each
(`obj-11-195`, `obj-11-53`, `obj-11-63`); the other 52 affected sources contribute
one.

Representative groups:

```text
test/00009.png, test/00011.png          mug    obj-11-56
test/00025.png, test/00026.png          mug    obj-11-24
val/00112.png, val/00114.png, val/00115.png
                                        phone  obj-11-195
```

The full machine-readable record is `duplicate_analysis.json` and
`duplicate_groups.csv` in the local study output directory.

## 3. Experimental datasets

All three datasets preserve the original source-group assignment. No image moves
between splits, and no source group is split across datasets.

| Dataset | Policy | Images | Sources | Train / val / test | Unique content |
| --- | --- | ---: | ---: | --- | ---: |
| A `objects_p06` | original, unchanged | 960 | 240 | 672 / 144 / 144 | 902 |
| B `objects_p06_dedup` | one representative per byte-identical group; lowest path wins | 902 | 240 | 628 / 138 / 136 | 902 |
| C `objects_p06_balanced` | one representative per `(split, source)`; lowest path wins | 240 | 240 | 168 / 36 / 36 | 240 |

Selection is deterministic: sort the paths and keep the first. B keeps every file
that is not an extra copy, so it retains all 240 sources. C intentionally keeps one
image per source, which also removes every duplicate by construction.

### Class composition

| Dataset | Split | mug | bottle | book | phone |
| --- | --- | ---: | ---: | ---: | ---: |
| A | train / val / test | 168 / 36 / 36 | 168 / 36 / 36 | 168 / 36 / 36 | 168 / 36 / 36 |
| B | train | 159 | 156 | 157 | 156 |
| B | val | 36 | 35 | 35 | 32 |
| B | test | 33 | 34 | 35 | 34 |
| B | total | 228 | 225 | 227 | 222 |
| C | train / val / test | 42 / 9 / 9 | 42 / 9 / 9 | 42 / 9 / 9 | 42 / 9 / 9 |

B removes duplicates unevenly by class, so it is no longer exactly class-balanced.
C is exactly balanced because every source contributes one image and the source
split itself is class-stratified.

### Manifests

Each experimental dataset has its own `manifest.json` and a check report:

| Dataset | Manifest version | Check result |
| --- | --- | --- |
| A | `1.0.0` | 960 files, 0 problems, 57 warnings |
| B | `1.1.0-dedup` | 902 files, 0 problems, **0 warnings** |
| C | `1.1.0-source-balanced` | 240 files, 0 problems, **0 warnings** |

The B and C records were built by the same `vision_core.manifest` code as A. No
unexpected, missing, modified, or cross-split files were found.

## 4. Training protocol

| Setting | Value |
| --- | --- |
| Model | `TinyCNN`, width 16, 72,564 parameters |
| Epochs | 15 |
| Batch size | 16 |
| Optimizer | Adam, learning rate 1e-3 |
| Primary seed | 11 |
| Sensitivity seeds | 12, 13 |
| Initialization | `set_seed(seed)` before every model construction; all three datasets use the same initial weights for a given seed |
| Training data | each dataset's own train split (A 672, B 628, C 168) |
| Validation | the original 144-image validation split, unchanged |
| Test | the original 144-image test split, unchanged |
| Normalization | mean/std from the original train split, identical for all models |
| Hyperparameter selection | fixed before the experiment; no tuning on test |
| Temperature | fitted on the original validation split for each model |

The experimental manifests contain their own reduced validation and test splits.
The controlled comparison deliberately does **not** use them: scoring each model on
a different test set would confound the dataset comparison. Every model is trained
only on its dataset's train split and evaluated on the same untouched original
validation and test splits. The B and C train splits contain no image from the
reference validation or test splits.

The test split was used for evaluation only, never for choosing a model or a
hyperparameter. Seeds 12 and 13 repeat the fixed protocol to measure seed
sensitivity; no decision ranks datasets by their per-seed test score.

!!! note "The original condition is not the pilot's historical run"
    This study's original condition scores 0.9931, while the capstone pilot
    recorded 0.9792 for its scratch CNN. Both are honest runs of the same data and
    configuration, but the pilot constructed the model before `train_classifier`
    reset the seed; this study calls `set_seed` before construction so all three
    datasets share exactly the same initial weights. The difference is
    initialization, not a data change or a corrected metric. The pilot's
    historical numbers are retained unchanged and are not silently replaced.

## 5. Results

### 5.1 Clean test accuracy

Primary seed 11, 144 test images:

| Dataset | Accuracy | Macro precision | Macro recall | Macro F1 | 95% accuracy CI | 95% macro-F1 CI |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| A original | **0.9931** | 0.9932 | 0.9930 | **0.9931** | 0.9792-1.0000 | 0.9765-1.0000 |
| B dedup | **0.9931** | 0.9932 | 0.9930 | **0.9931** | 0.9792-1.0000 | 0.9765-1.0000 |
| C balanced | 0.9861 | 0.9869 | 0.9861 | 0.9861 | 0.9653-1.0000 | 0.9633-1.0000 |

B and A make the same predictions on all 144 test images: the paired difference is
exactly 0.0000 with a degenerate interval [0.0000, 0.0000]. C loses one image
relative to A: -0.0069 accuracy, 95% paired CI [-0.0208, 0.0000]. All three
intervals include the ceiling, so the differences are one or two images, not a
detectable generalization effect.

On the 136 unique-content test images (the duplicate groups collapsed):

| Dataset | Accuracy | Macro F1 |
| --- | ---: | ---: |
| A original | 0.9926 | 0.9925 |
| B dedup | 0.9926 | 0.9925 |
| C balanced | 0.9853 | 0.9850 |

Collapsing the duplicate test images changes nothing material for A or B, which
confirms that the eight duplicated test pairs were not hiding a different result.

### 5.2 Seed sensitivity

The clean-test result is stable across the three seeds:

| Dataset | Accuracies (seeds 11, 12, 13) | Mean | SD |
| --- | --- | ---: | ---: |
| A | 0.9931, 1.0000, 1.0000 | 0.9977 | 0.0040 |
| B | 0.9931, 1.0000, 1.0000 | 0.9977 | 0.0040 |
| C | 0.9861, 1.0000, 1.0000 | 0.9954 | 0.0080 |

Deduplication is neutral on clean accuracy at every seed. C is neutral at seeds 12
and 13 and loses one image at seed 11. No dataset has a repeatable accuracy
advantage.

### 5.3 Per-class metrics

Seed 11, on 36 test images per class:

| Dataset | Class | Precision | Recall | F1 | F1 95% CI |
| --- | --- | ---: | ---: | ---: | --- |
| A / B | mug | 1.0000 | 0.9722 | 0.9859 | 0.9508-1.0000 |
| A / B | bottle | 0.9730 | 1.0000 | 0.9863 | 0.9524-1.0000 |
| A / B | book | 1.0000 | 1.0000 | 1.0000 | 1.0000-1.0000 |
| A / B | phone | 1.0000 | 1.0000 | 1.0000 | 1.0000-1.0000 |
| C | mug | 1.0000 | 0.9444 | 0.9714 | 0.9259-1.0000 |
| C | bottle | 0.9474 | 1.0000 | 0.9730 | 0.9275-1.0000 |
| C | book | 1.0000 | 1.0000 | 1.0000 | 1.0000-1.0000 |
| C | phone | 1.0000 | 1.0000 | 1.0000 | 1.0000-1.0000 |

The only per-class change is that C misclassifies one additional mug as a bottle.
B's per-class metrics are identical to A's because its predictions are identical.

### 5.4 Confusion matrices

A and B, rows = true, columns = predicted (mug, bottle, book, phone):

```text
[[35,  1,  0,  0],
 [ 0, 36,  0,  0],
 [ 0,  0, 36,  0],
 [ 0,  0,  0, 36]]
```

C:

```text
[[34,  2,  0,  0],
 [ 0, 36,  0,  0],
 [ 0,  0, 36,  0],
 [ 0,  0,  0, 36]]
```

All errors are mug-to-bottle; book and phone are always right. There is no
class-level collapse hidden by the aggregate.

### 5.5 Calibration

Temperatures were fitted on the original validation split. Raw and calibrated ECE
use 10 bins on the 144-image test split:

| Dataset | Raw ECE | Temperature | Calibrated ECE |
| --- | ---: | ---: | ---: |
| A original | 0.0520 | 0.5 | **0.0105** |
| B dedup | 0.0783 | 0.5 | 0.0125 |
| C balanced | 0.1262 | 0.5 | 0.0237 |

Deduplication does not improve calibration: B's calibrated ECE is 0.0020 higher
than A's, and C's is 0.0132 higher. All three values are small, and the ranking is
well within the noise of 144 test images. There is no evidence for a calibration
benefit.

### 5.6 Robustness

Primary seed 11, accuracy under each degradation:

| Condition | A original | B dedup | C balanced |
| --- | ---: | ---: | ---: |
| Baseline | 0.9931 | 0.9931 | 0.9861 |
| Brightness 0.6 | 0.5069 | **0.7014** | 0.5903 |
| Brightness 1.4 | 0.7500 | **0.8958** | 0.7708 |
| Blur radius 1.5 | 0.5208 | 0.5208 | 0.5000 |
| Blur radius 3.0 | 0.5000 | 0.5000 | 0.5000 |

At seed 11, B looks much better under brightness: +0.1944 (95% paired CI
0.1042-0.2710) at brightness 0.6 and +0.1458 (0.0903-0.2153) at brightness 1.4.
That result does **not** survive the seed check. Mean accuracy across seeds 11, 12,
and 13:

| Condition | A mean | B mean | C mean | B - A | C - A |
| --- | ---: | ---: | ---: | ---: | ---: |
| Brightness 0.6 | 0.4884 | 0.5648 | 0.5116 | +0.0764 | +0.0232 |
| Brightness 1.4 | 0.8912 | 0.9167 | 0.8680 | +0.0255 | -0.0232 |
| Blur radius 1.5 | 0.5764 | 0.5046 | 0.5000 | -0.0718 | -0.0764 |
| Blur radius 3.0 | 0.5185 | 0.4769 | 0.5000 | -0.0416 | -0.0185 |

The per-seed brightness-0.6 values show why the mean is not a finding:

| Dataset | Seed 11 | Seed 12 | Seed 13 | Range |
| --- | ---: | ---: | ---: | ---: |
| A | 0.5069 | 0.6806 | 0.2778 | 0.4028 |
| B | 0.7014 | 0.6597 | 0.3333 | 0.3681 |
| C | 0.5903 | 0.5278 | 0.4167 | 0.1736 |

B is better than A at seed 11, slightly worse at seed 12, and better at seed 13;
the sign flips. On blur radius 1.5, B is never better and is 31 images worse at
seed 12; on blur radius 3.0 it is equal at seeds 11-12 and 2 images better at seed
13. The seed-11 brightness gain is therefore an initialization effect, not a
property of deduplication. No robustness claim is supported.

### 5.7 Training cost

| Dataset | Primary time | Mean of 3 seeds | Change vs A |
| --- | ---: | ---: | ---: |
| A 960 images | 4.30 s | 3.90 s | - |
| B 902 images | 3.63 s | 3.48 s | -10.8% |
| C 240 images | 1.19 s | 1.35 s | -65.4% |

Times are CPU seconds for 15 epochs and vary with machine load; the ordering is
stable. B removes 6.0% of the files and saves about 11% of training time. C removes
75% of the files and saves about 65% of training time. The time saving is real but
small in absolute terms; it is not a reason to change the dataset by itself.

## 6. Decision

**Recommended version: `objects_p06` v1.0.0, unchanged.**

Reasons:

1. **No generalization gain.** B and A have identical clean accuracy at all three
   seeds; the seed-11 paired difference is exactly zero. C loses one image at seed
   11 and is identical at seeds 12 and 13. No interval supports an improvement.
2. **No calibration gain.** B and C have higher calibrated ECE than A (0.0125 and
   0.0237 versus 0.0105). The differences are small, but the direction is not
   favourable.
3. **No robust gain.** The large seed-11 brightness result for B reverses at seed
   12 and does not appear on blur. Reporting it would be a single-seed artifact.
4. **B introduces a small class imbalance.** Deduplication removes 12-18 files per
   class, so B totals 222-228 images per class instead of 240. C is exactly
   balanced but removes 75% of the data and still does not improve any measured
   outcome.
5. **Continuity.** v1.0.0 has the historical pilot metrics, a 144-image test split,
   and the published lesson numbers. Switching versions without a measured benefit
   would invalidate comparisons for no gain.

**Optional variant:** B (`objects_p06_dedup`, version `1.1.0-dedup`) is a valid
choice when a student or auditor needs a dataset with zero duplicate content. It is
a strict subset of v1.0.0, preserves every source group and split, and does not
change clean accuracy. It is **not** the default and it should not be presented as
more accurate. C is an experiment only; its 240 images and 36-image own test split
are too small to recommend for the capstone.

Because the experiment does not support a change, the P06 dataset card and the P06
brief keep v1.0.0 as the default. The duplicate warnings remain documented and
checked rather than silently deleted.

## 7. Limitations

- **Synthetic, single-renderer data.** Every conclusion is about this icon set. It
  says nothing about duplicate photographs or real-world robustness.
- **Near-ceiling accuracy.** 143/144 or 142/144 correct leaves almost no room for a
  dataset effect on clean accuracy. The intervals are wide relative to the
  differences.
- **Three seeds, one architecture.** The seed check is enough to reject the
  brightness claim, not enough to estimate a small effect precisely.
- **The reference test split contains duplicate pairs.** The primary comparison
  counts them as separate images. The unique-content table (136 images) is the
  check against that; it agrees with the primary result.
- **Only brightness and blur were tested.** Rotation, background, and TTA were not
  part of this study.
- **B and C were built by a local study script, not the course generator.** They
  are reproducible from v1.0.0 and their selection maps are recorded, but they are
  not part of the default `make_vision_data.py` output.
- **No human review.** This is an agent-run experiment, not a student exercise or a
  human-marked result.

## 8. Reproduce

From the repository root, after the standard P06 data exists:

```bash
./.venv/Scripts/python.exe scripts/make_vision_data.py --check
./.venv/Scripts/python.exe tmp/p06-dedup-study/run_study.py
```

The script:

1. verifies the original manifest (960 files);
2. groups files by SHA-256 and decoded pixel hash;
3. refuses to continue if a duplicate group crosses a split, label, or source;
4. writes `objects_p06_dedup/` and `objects_p06_balanced/` beside the original,
   each with its own manifest and check report;
5. trains A, B, and C under the same configuration and seeds;
6. evaluates every model on the original unchanged validation/test splits;
7. writes `duplicate_analysis.json`, `duplicate_groups.csv`,
   `datasets_summary.json`, `selection_dedup.json`, `selection_balanced.json`, and
   `metrics.json` under `tmp/p06-dedup-study/outputs/`.

The original directory is never written to. The script refuses to clear any
directory other than the two named experimental outputs.

## 9. Related documents

- [Capstone pilot report](capstone-pilot-report.md)
- [Final audit](final-audit.md)
- [P06 brief](../course/projects/p06-image-classifier.md)
- Dataset manifest code: `projects/computer-vision/vision_core/manifest.py`
- Vision data generator: `scripts/make_vision_data.py`
