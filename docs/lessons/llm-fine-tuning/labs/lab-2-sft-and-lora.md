# Lab 2 - SFT and LoRA on the FAQ task {#lab-2}

**Section:** [Language models](../index.md) · **Modules:** M07-M08 · **Time:** 7 hours

## Goal

Fine-tune the base model with SFT, then with LoRA, and show that your labels are
shifted and masked correctly. Compare both against the base model on the same test
split.

## Steps

1. Render the chat template for five training pairs. Decode the token ids and
   confirm they reproduce the input string.
2. Implement shift-and-mask. Add a test that compares `labels[i]` with
   `input_ids[i+1]` and fails if the shift is missing.
3. Demonstrate the failure: train without the shift for 20 steps. Record the loss
   (it will be very low) and one generated answer (it will copy).
4. Train the correct SFT model with the notebook's settings. Report the four
   metrics: answer loss, exact match, first-12, word F1.
5. Train LoRA `r=4` on the attention projections at the same step budget. Report
   trainable parameters and the same four metrics.
6. Merge the adapter and report the maximum absolute difference between merged and
   unmerged logits. It should be below 1e-4.
7. Evaluate the base model on the same test pairs. Put all three rows in one table.

## Deliverables

| File | Contents |
| --- | --- |
| `report.md` | Template, shift/mask explanation, three-row table, failure analysis |
| `sft.py` | Training script with the shift/mask test |
| `adapter/` | LoRA weights + config |
| `merged.pt` | Merged model + metadata |
| `merge_check.txt` | Maximum difference and the prompts used |

## Required table

| Model | Trainable | Answer loss | Exact match | First-12 | Word F1 |
| --- | --- | --- | --- | --- | --- |
| base | 0 | | | | |
| full SFT | | | | | |
| LoRA r=4 | | | | | |

## Marking

* **25%** shift and mask are correct and tested; the failure is demonstrated.
* **25%** four metrics on three models, same test split.
* **20%** LoRA trainable parameters are reported and the merge check passes.
* **20%** failure analysis names a concrete case and a next action.
* **10%** limitations include test size (16 pairs) and template-based split.

## Stretch

Add a refusal example and an unanswerable question to the test set. Define the
scoring rule before running, then report whether the models abstain or hallucinate.

## Rules

Do not train on the test templates. Do not tune on the test split. If you use a
hosted model instead of the teaching model, report its revision and note that the
numbers are not comparable to the teaching table.
