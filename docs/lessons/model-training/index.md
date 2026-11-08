# Training models from scratch and engineering data (M04-M05)

This section turns the training loop from a framework call into an instrument you
can read. It then treats data as an artifact with defects, provenance, and a
license, not as a file that happened to be on disk.

The two modules are deliberately paired. A training result is only as good as the
split and the labels behind it, and most "model" failures in student projects are
data failures wearing a model costume.

| | |
| --- | --- |
| **Level** | 1 - after neural-network foundations |
| **Study time** | 30 hours: 14 h reading, 14 h labs, 2 h write-up |
| **Hardware** | CPU-only. A GPU shortens the optional runs but is not required |
| **Prerequisites** | [F11](../f11-neural-networks/index.md), [F12](../f12-backpropagation/index.md), [F10](../f10-metrics-validation/index.md) |
| **You will produce** | A trained CNN with an ablation table, a dataset audit, and a dataset card |

## Modules

| Module | Question | Lessons | Notebook |
| --- | --- | --- | --- |
| M04 | How does a training run actually work, and what does it cost? | [MT01](mt01-training-loop.md) - [MT05](mt05-checkpoints-and-compute.md) | [Open notebook](../../notebooks/model-training/m04_training_from_scratch.ipynb) |
| M05 | Is the data fit to train on, and can you prove it? | [MT06](mt06-dataset-audit.md) - [MT10](mt10-dataset-cards.md) | [Open notebook](../../notebooks/model-training/m05_data_engineering.ipynb) |

## Measured anchors

These numbers come from the [M04 notebook](../../notebooks/model-training/m04_training_from_scratch.ipynb)
and the [M05 notebook](../../notebooks/model-training/m05_data_engineering.ipynb), on a CPU. They are
anchors for comparison, not benchmarks:

* the curated image split is 300 images (210/45/45); the plain CNN has 72,499
  parameters and scores **0.956** on its test split;
* a random split shares **91** source images with test and scores **0.867**; a
  grouped split shares **0** and scores **0.622** - a leakage premium of **0.244**;
* the messy ticket audit starts at **650** rows, finds **10** blanks and **49**
  duplicate texts, and cleans to **600** rows with **200** per class;
* flipping **60%** of training labels drops accuracy from **1.000** to **0.382**.

If your run is far from these, check the seed, the split, and the preprocessing
before concluding that your model is different.

## The section's argument

1. **The loop is simple; the invariants are not.** Zeroing gradients, evaluation
   mode, and no-grad validation are not optional details.
2. **Augmentation encodes assumptions.** A transform is a claim about what does not
   change the label. Write the claim down.
3. **The split decides the question.** Random rows, grouped entities, and future
   periods answer different questions. Report the one you actually asked.
4. **Data defects are measurable.** Counts, overlaps, kappa, and noise curves turn
   "the data is messy" into evidence.
5. **Provenance is part of the model.** A card and a digest make the result
   reproducible.

## How to study this section

Read MT01-MT05 with the notebook open. Run each cell, change one thing, and record
the result. Then read MT06-MT10 and audit a dataset you already have; the audit is
more useful on your own data than on the teaching file.

## Practical work

| Work | What it asks for |
| --- | --- |
| [Lab 1 - Training ablation](labs/lab-1-training-ablation.md) | A controlled ablation with one factor changed per run |
| [Lab 2 - Dataset audit](labs/lab-2-dataset-audit.md) | An audit, leakage probe, and dataset card for your own data |

## Assessment

[Assessment](assessment.md): two labs (80%) and a short defense (20%). Both labs
require a reproduction command and a table with sample sizes.

## What this section does not cover

Distributed training, mixed-precision kernel engineering, and large-scale data
pipelines. It covers the layer that decides whether a training result is
believable: a loop you can inspect, a split that answers the deployment question,
and data whose defects you have counted.

## Next

Continue to [M06 - Transformers and language models](../llm-fine-tuning/index.md).
