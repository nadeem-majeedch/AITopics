# Lab 3 - Compare training from scratch with transfer learning

**Section path:** [Overview](../index.md) · Module [CV06](../cv06-transfer-learning.md) · **Lab 3** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 12% of the section assessment |
| **Time** | 4 hours |
| **Hardware** | CPU-only (all three conditions in ~0.7 s after the backbone) |
| **Code** | `projects/computer-vision/lab3_scratch_vs_transfer.py` |
| **Prerequisite** | CV05, CV06 |

## The task

Train the same four-class task three ways on one split, and decide which you would ship:

1. **from scratch** - random init, whole network trainable,
2. **frozen trunk + linear probe** - one 260-parameter head,
3. **last block fine-tuned** - trunk mostly frozen, final block and head trainable.

Report accuracy **and** trainable parameters for each. The parameter column is the point.

!!! warning "What the pretrained trunk is here"
    There is no ImageNet download in this environment. The lab trains a backbone on the
    synthetic shape set (20 epochs, **0.976** validation accuracy) and reuses it as the
    "pretrained" model. The mechanics are identical to real transfer learning; the
    features are not.

## Setup

```bash
python scripts/make_vision_data.py
cd projects/computer-vision
python lab3_scratch_vs_transfer.py
```

Classes: bottle, mug, ball, book. Split: 84 train / 18 val / 18 test, grouped by source,
seed 1. Backbone checkpoint is written to `outputs/pretrained_backbone.pt`; subsequent
runs reuse it unless `--rebuild`.

## Run it

```bash
python lab3_scratch_vs_transfer.py --epochs 20
```

Verified output:

```text
condition                         test_acc  trainable  seconds
---------------------------------------------------------------
scratch                              0.500      72564      0.5
frozen features + linear probe       0.500        260      0.1
last block fine-tuned                0.722      55812      0.1

best condition: last block fine-tuned (0.722)
results: .../outputs/lab3_transfer_comparison.json

0 failure(s)
PASS  three conditions measured with differing parameter budgets
```

Backbone record in the JSON:

```text
backbone: val_acc 0.976, epochs 20, honest_note "synthetic pretraining"
```

## What the numbers say

1. **260 parameters match 72,564.** If a linear head on frozen features reaches the same
   accuracy, the deployment choice is the probe: 280x smaller, trains in a tenth of a
   second.
2. **The probe is at chance for this task.** Four classes, 0.500 means half right - the
   frozen features are not linearly separable enough here. "Transfer learning helps" would
   be a false summary of this row.
3. **Fine-tuning the last block wins.** 0.722 with 55,812 trainable parameters. Adaptation
   matters more than a bigger head.
4. **18 test images.** One image is 0.056 accuracy. Do not read differences under ~0.11 as
   real.

## Test cases

| Check | Expected | Verification |
| --- | --- | --- |
| Three conditions run | 3 rows printed | stdout |
| Parameter counts differ | 72,564 / 260 / 55,812 | printed table |
| Accuracies in [0, 1] | yes | printed |
| Backbone reused, not retrained | second run skips training | timing / log |
| JSON written | valid, contains all three | `lab3_transfer_comparison.json` |
| Determinism | same seed, same numbers | rerun |

## Rubric

| Criterion | Marks | What earns full marks |
| --- | --- | --- |
| Three conditions correctly built | 25 | frozen parameters provably frozen; probe really is one layer |
| Parameter accounting | 20 | counts verified with `count_parameters`, explained |
| Interpretation | 25 | explains probe-at-chance, and why fine-tuning wins |
| Recommendation | 15 | chooses a condition for a stated deployment constraint |
| Honesty about pretraining | 15 | states the backbone is synthetic, and what that limits |

## Extensions

1. Freeze the trunk but leave it in `.train()` mode. Report whether the probe result moves
   and explain why it can.
2. Fine-tune the last block with lr 2e-2 instead of 2e-4. Report the curves.
3. Train the backbone for 5 epochs instead of 20. Does transfer still win?
4. Compute the accuracy per class for the best condition and say which class carries the
   gain.

## Submit

```text
cv-lab3/
  README.md
  comparison.json
  analysis.md      # table, interpretation, recommendation with a constraint
```

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Probe never learns | optimizer built before freezing | freeze, then build the optimizer |
| All three identical | same model object reused | rebuild the model per condition |
| `TinyCNN` shape error | width mismatch with the checkpoint | pass the same `width` used to train it |
