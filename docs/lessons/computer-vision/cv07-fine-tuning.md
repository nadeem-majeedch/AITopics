# CV07 - Fine-tuning a pretrained image classifier {#cv07}

**Section path:** [Overview](index.md) · **Module 7** · [Lab 4](labs/lab4-finetune-everyday-objects.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 2 h reading, 2 h practice |
| **Hardware** | CPU-only for the section's backbone; GPU optional for real pretrained weights |
| **Prerequisites** | CV06, CV05 |
| **You will produce** | A fine-tuned four-class model, its model card, and a robustness table produced by perturbation, not assertion |

## Why this module exists

CV06 showed that a frozen trunk plus a small head can match a from-scratch network, and
that unfreezing the last block beats both. This module turns that into a procedure you
can defend: which layers, which learning rates, how many epochs, and what evidence
suggests you should stop.

## Layer groups and differential learning rates

A fine-tune is not one learning rate. The trunk holds features worth preserving; the
head starts random and must move fast.

| Group | Typical lr | Rationale |
| --- | --- | --- |
| Head / classifier | 1e-3 to 2e-3 | random init, needs to move |
| Last block | 1e-4 to 3e-4 | adapt features gently |
| Earlier blocks | 0 to 1e-5 | usually frozen |
| BatchNorm running stats | frozen | `.eval()` on the trunk |

```python
transfer.freeze_trunk(backbone)
transfer.unfreeze_last_block(backbone)
model = transfer.build_head(backbone, num_classes=4)
optimizer = torch.optim.Adam([
    {"params": (p for p in model.block3.parameters() if p.requires_grad), "lr": 2e-4},
    {"params": model.classifier.parameters(), "lr": 2e-3},
])
```

Two failure modes this ordering prevents: destroying pretrained features with a
head-sized learning rate, and starving the head with a trunk-sized one.

## The run, and its measured result

```bash
python lab4_finetune_objects.py --epochs 12
```

| Quantity | Value |
| --- | --- |
| Classes | bottle, mug, ball, book |
| Train / val / test | 84 / 18 / 18 |
| Epochs | 12, batch 16, lr 2e-3 (head), 2e-4 (last block) |
| Test accuracy | **0.500** (chance is 0.250) |
| Model card | written and complete |

0.500 is a modest number and worth stating plainly: 18 test images, a synthetic dataset,
and a 12-epoch budget. The lab's value is the *procedure* - train, evaluate per class,
perturb, record, document - not a headline accuracy.

## When to stop

Three stopping rules, in order of preference:

1. **Validation plateau with a patience window.** Stop after N epochs without
   improvement; keep the best weights, not the last ones.
2. **Fixed budget, reported honestly.** "12 epochs chosen in advance" is legitimate.
   "We stopped when the number looked good" is not.
3. **Gap threshold.** If `train_acc - val_acc` exceeds ~0.15 on a small dataset, more
   epochs will usually hurt.

`training.train_classifier` supports a patience window:

```python
history, model = training.train_classifier(..., patience=5)
print(history.best_epoch)     # the epoch you actually ship
```

## Robustness is part of the evaluation, not a bonus

After fine-tuning, perturb the test set the way deployment will:

```python
report = evaluation.robustness_suite(model, test_images, test_labels, mean, std)
```

Measured on this lab's model:

| Condition | Accuracy | Change vs clean |
| --- | --- | --- |
| clean | 0.500 | - |
| brightness 1.3x | 0.500 | +0.000 |
| brightness 0.7x | 0.500 | +0.000 |
| gaussian noise 0.08 | 0.611 | +0.111 |
| blur radius 1.2 | 0.500 | +0.000 |
| jpeg quality 30 | 0.500 | +0.000 |
| occlusion 25% | 0.667 | +0.167 |

Two honest observations. First, the perturbations mostly *do not hurt* this model - it
is at 0.500 and stays there, which is what a weak model looks like: it is wrong the same
way regardless of input quality. Second, noise and occlusion "improve" accuracy, which
on 18 images is noise in the measurement, not a real effect. Report the number and say
so; do not write "occlusion improves robustness".

!!! warning "Do not fine-tune on your test set, ever"
    A tempting loop: evaluate, notice a failure case, add it to training, re-evaluate,
    report the improvement. That is test-set tuning and it invalidates the number. If a
    failure case teaches you something, add it to *train* and accept that the test score
    may not move.

## Documentation you owe

Every fine-tuned model ships with a card. The template is in
[Model card and dataset card](model-card.md), and Lab 4 generates one:

```text
outputs/lab4_model_card.md    complete=True    missing=[]
```

The card records intended use, out-of-scope use, the exact training configuration, the
metrics with their dataset and sample size, known failure modes, and the licence of the
data. A model without a card is a model nobody can audit.

## Practice

1. Fine-tune with the head lr at 2e-2 and report what happens to the curves.
2. Compare `patience=3` against a fixed 12 epochs. Which model do you ship, and on what
   evidence?
3. Add one perturbed copy of each *training* image (brightness 0.7) and retrain. Does
   the brightness accuracy change?
4. Fill in the model card for your run and list every field you could not fill honestly.

## Check yourself

1. Why does the trunk need `.eval()` even when its parameters are frozen?
2. Your fine-tune reaches 0.95 train and 0.62 validation. Name two changes and the
   mechanism each one uses.
3. Why is "occlusion 25% improved accuracy by 0.167" a claim you should not make?

## What comes next

[CV08](cv08-training-detectors.md) leaves classification behind: the output is no longer
one label per image but a variable number of boxes, and that changes the loss, the
targets, and the evaluation.
