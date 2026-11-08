# Lab 4 - Fine-tune a pretrained model on everyday objects

**Section path:** [Overview](../index.md) · Module [CV07](../cv07-fine-tuning.md) · **Lab 4** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 12% of the section assessment |
| **Time** | 4 hours |
| **Hardware** | CPU-only (reference run: ~4 s) |
| **Code** | `projects/computer-vision/lab4_finetune_objects.py` |
| **Prerequisite** | CV06 |

## The task

Fine-tune a pretrained trunk to classify four everyday objects, then do the part most
tutorials skip: perturb the test set, write the model card, and decide whether the result
is good enough to ship.

Deliverables:

1. a fine-tuned checkpoint,
2. a per-class classification report on the held-out split,
3. a robustness table across seven conditions,
4. a completed model card.

## Setup

```bash
python scripts/make_vision_data.py
cd projects/computer-vision
python lab3_scratch_vs_transfer.py --epochs 20      # writes outputs/pretrained_backbone.pt
python lab4_finetune_objects.py --epochs 12
```

Classes: bottle, mug, ball, book (32x32 crops, 84/18/18). The trunk is the synthetic
pretrained backbone from Lab 3 (see [CV06](../cv06-transfer-learning.md) for what that
does and does not represent).

Training configuration: head lr 2e-3, last block lr 2e-4, batch 16, 12 epochs, seed 0.

## Run it

Verified output (tail; the report above it lists per-class precision/recall):

```text
clean                      0.500   +0.000
brightness 1.3x            0.500   +0.000
brightness 0.7x            0.500   +0.000
gaussian noise 0.08        0.611   +0.111
blur radius 1.2            0.500   +0.000
jpeg quality 30            0.500   +0.000
occlusion 25%              0.667   +0.167

worst: clean (drop 0.000)

model: .../outputs/lab4_objects.pt
card: .../outputs/lab4_model_card.md  complete=True  missing=[]

0 failure(s)
PASS  fine-tuned model saved and documented with measured metrics
```

| Quantity | Value |
| --- | --- |
| Test accuracy (clean) | 0.500 |
| Chance level | 0.250 |
| Test images | 18 |
| Checkpoint size | ~305 KB |
| Model card | complete, no missing fields |

## Interpreting a modest result

0.500 on four classes and 18 images is two images away from 0.389. It is better than
chance and not evidence of a good classifier. What the lab actually demonstrates:

1. **The procedure works end to end** - train, evaluate per class, perturb, document.
2. **Robustness is flat** because the model is weak: it is wrong the same way regardless of
   brightness or blur. That is what an underfit model looks like, and it is worth being able
   to recognise.
3. **Noise and occlusion "improve" accuracy** by one image each. On 18 images that is
   measurement noise, not robustness. Say so in your write-up; do not claim a gain.

!!! warning "Do not tune on the test split"
    If you evaluate, notice a failure, add that image to training, and re-evaluate, the
    second number is not a test result. Add the case to training and accept that the test
    score may not move.

## Test cases

| Check | Expected | Verification |
| --- | --- | --- |
| Checkpoint written | file > 100 KB | `outputs/lab4_objects.pt` |
| Per-class report | 4 classes with precision/recall | stdout |
| Robustness table | 7 conditions | stdout |
| Best/worst identified | printed | `worst:` line |
| Model card complete | `missing=[]` | `cards.check_card` |
| Reload works | checkpoint loads, same accuracy | load and re-evaluate |
| No test tuning | test split untouched during tuning | your log |

## Rubric

| Criterion | Marks | What earns full marks |
| --- | --- | --- |
| Working fine-tune | 20 | trains, saves, reloads, same accuracy |
| Evaluation quality | 25 | per-class metrics + N stated + chance level named |
| Robustness analysis | 20 | table reproduced; noise-vs-signal distinction stated |
| Model card | 25 | every field filled with measured values; out-of-scope uses named |
| Honest conclusion | 10 | refuses to call 0.500 a deployable model |

## Extensions

1. Add brightness-0.7 augmented copies of the **training** images and retrain. Does the
   brightness row change?
2. Compare 12 epochs with `patience=3`. Which model do you ship and on what evidence?
3. Replace the classifier with a 2-layer MLP head. Report accuracy and parameter count.
4. Produce three labelled error cases and group them by cause.

## Submit

```text
cv-lab4/
  README.md
  model_card.md
  robustness.md
  error_cases/       # three images with true/predicted/confidence
  analysis.md
```

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `FileNotFoundError` for backbone | Lab 3 not run | run Lab 3 first |
| Accuracy exactly 0.250 | head trained on frozen random trunk | check backbone val accuracy |
| Card `missing=[...]` | template fields left empty | fill them with measured values |
