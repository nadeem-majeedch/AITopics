# Lab 1 - Train and inspect a tiny language model {#lab-1}

**Section:** [Language models](../index.md) · **Module:** M06 · **Time:** 5 hours

## Goal

Train the 239,040-parameter transformer, prove the causal mask works, and report a
loss curve and samples that another student can reproduce.

## Steps

1. Run `notebooks/llm-fine-tuning/m06_transformers.ipynb` from a clean kernel.
2. Record the parameter count and derive it from the architecture. The two must
   match; show the arithmetic.
3. Run the mask test. Then remove the mask and record what happens to the loss and
   to a sample. Restore the mask.
4. Train for 400 steps. Report loss and perplexity at steps 0, 100, 200, 300, 400.
5. Sample three completions at temperatures 0.5, 1.0, and 1.5, with the same
   prompt and seed.
6. Build a bigram baseline on the same corpus and compare validation perplexity.

## Deliverables

| File | Contents |
| --- | --- |
| `report.md` | Setup, parameter derivation, curve, samples, baseline comparison |
| `loss.csv` | step, train_loss, val_loss, lr |
| `checkpoint.pt` | weights + tokenizer vocabulary + config |
| `mask_test.py` | test that fails if attention reaches a future position |

## Required table

| Step | Train loss | Val loss | Perplexity | LR |
| --- | --- | --- | --- | --- |
| 0 | | | | |
| 100 | | | | |
| 200 | | | | |
| 300 | | | | |
| 400 | | | | |

## Marking

* **30%** mask test is real: removing the mask makes it fail.
* **25%** parameter arithmetic matches the implementation.
* **20%** curve and samples are complete and use fixed seeds.
* **15%** bigram baseline is implemented and compared on the same split.
* **10%** limitations discuss corpus size and memorisation.

## Stretch

Train two models with different `block_size` (64 and 128) at equal steps. Report
validation loss and the wall-clock difference. Explain which effect dominates.

## Rules

CPU is sufficient. Report the machine and the number of threads. Do not compare
perplexity with a different tokenizer.
