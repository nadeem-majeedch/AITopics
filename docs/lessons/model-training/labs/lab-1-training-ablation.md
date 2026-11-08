# Lab 1 - Training ablation and a defensible checkpoint {#lab-1}

**Section:** [Model training](../index.md) · **Modules:** M04 · **Time:** 6 hours

## Goal

Train the notebook's CNN under at least four configurations, select one on
validation, and hand in a checkpoint that a fresh process can load and use.

## What to build

1. Copy the M04 notebook into your own working directory. Keep the curated split
   and seed; do not regenerate the dataset until the baseline reproduces.
2. Run a **learning-rate sweep** at `3e-4`, `1e-3`, `3e-3`, `1e-2` for 4 epochs.
3. Run a **two-by-two ablation**: augmentation on/off and the best two learning
   rates. Report validation accuracy and the train/validation gap.
4. Save the selected model with a checkpoint containing class names, input size,
   normalisation mean/std, epoch, and the measured validation score.
5. Load the checkpoint in a new Python process. Compare predictions on the test set
   with the in-memory model; they must match exactly.

## Deliverables

| File | Contents |
| --- | --- |
| `report.md` | Question, configurations, table, selection rule, limitations |
| `ablation.csv` | One row per run: lr, augmentation, epochs, val_acc, gap, seconds |
| `checkpoint.pt` | Selected weights plus metadata |
| `reload_check.py` | Script that loads the checkpoint and prints the equality result |

## Required table

| Run | LR | Aug | Epochs | Val acc | Train loss | Gap | Seconds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | | | | | | | |
| no-aug | | | | | | | |
| best-lr | | | | | | | |

## Marking

* **30%** sweep and ablation are controlled (one factor at a time, fixed seed).
* **25%** selection uses validation, and the test split is touched once.
* **20%** checkpoint metadata is complete and reload is exact.
* **15%** interpretation names a mechanism, not just a ranking.
* **10%** limitations include the 45-image validation split and its interval.

## Stretch

Repeat the winning configuration with two more seeds and report the range. If the
range crosses the difference between the top two configurations, say so: the
ranking is not resolved.

## Rules

* No fabricated numbers. If a run fails, report it and exclude it with a reason.
* CPU is sufficient; if you use a GPU, report the device and dtype.
* Do not change the test split to improve the result.
