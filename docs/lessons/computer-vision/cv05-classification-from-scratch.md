# CV05 - Image classification from scratch {#cv05}

**Section path:** [Overview](index.md) · **Module 5** · [Lab 2](labs/lab2-cnn-learning-curves.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 5 hours: 2 h reading, 3 h practice |
| **Hardware** | CPU-only (whole lab runs in under 5 seconds) |
| **Prerequisites** | CV04, F10 (metrics) |
| **You will produce** | A trained classifier, two learning curves, and a one-paragraph judgement of whether the task was too easy |

## Why this module exists

Training a classifier is a loop with five decisions: split, loss, optimizer, schedule,
and stopping rule. Most courses show one working configuration. This module makes you
choose, then shows what each choice did to the curve.

The lab is small on purpose - 210 training images, 25 epochs, 3 seconds - so you can
run ten versions and compare them instead of waiting for one.

## The loop, with the parts that matter

```python
from vision_core import models, training

model = models.TinyCNN(num_classes=3, width=16)
history, model = training.train_classifier(
    model,
    train_images, train_labels,
    val_images, val_labels,
    epochs=25, batch_size=16, lr=2e-3, seed=0,
    augment_fn=my_augment,
)
```

`train_classifier` returns a `History` object, not just a model. The history is the
artifact:

```python
print(history.ascii_plot())        # curves in the terminal
history.plot_png("outputs/curves.png")
print(history.best_epoch, history.best_val_acc, history.overfitting_gap())
```

`overfitting_gap()` is `train_acc - val_acc` at the best epoch. A large positive gap
means memorisation; a near-zero or negative gap means the model is still limited by
capacity or training time, not by data.

### Measured curves on this data

| Quantity | Value |
| --- | --- |
| Epochs | 25 (batch 16, lr 2e-3, augmentation on) |
| Best epoch | 12 |
| Best validation accuracy | 1.000 |
| Test accuracy at best epoch | 1.000 |
| Overfitting gap | -0.029 |
| Total training time | 3.0 s on CPU |

!!! warning "A perfect score is information, not success"
    Test accuracy 1.000 on 45 images means the task is too easy to discriminate between
    models. The three shapes are separable with local features, the augmentation is
    mild, and 210 images is enough. Read the numbers as "this configuration learned the
    task", not as "this model is excellent".

    The lab's extension asks you to make it hard: drop to 30 training images, disable
    augmentation, or add a fourth confusable class. Then the curves have something to
    separate.

## Reading a learning curve

Four shapes, four diagnoses:

| Shape | Diagnosis | First action |
| --- | --- | --- |
| Both curves flat and high | under-fitting, or a label bug | check labels, then capacity |
| Train falls, val flat | not learning generalisable features | more augmentation, less capacity |
| Train falls, val rises | overfitting | early stop, augment, regularise |
| Both fall, then both spike | learning rate too high | lower lr, add warmup |

The section's lab reports the first shape for the shapes task: both curves reach 1.0 by
epoch 12 and stay there. That is the honest reading, and it is why Lab 2's write-up asks
you to construct a harder variant before you interpret anything.

## Loss, optimizer, and the choices nobody explains

- **Cross-entropy on logits.** Do not apply softmax before the loss; PyTorch's
  `CrossEntropyLoss` includes it. Double-softmax makes gradients tiny and training slow.
- **Adam at 2e-3** for these small models. SGD needs a tuned schedule to match it here;
  the lab is about the loop, not about squeezing the last point.
- **Batch size 16** for 210 images gives 14 steps per epoch. Batch 64 gives 4, and the
  model then needs more epochs to see the same number of updates. Steps per epoch, not
  epochs, is what the optimizer experiences.
- **Class weights** when the classes are imbalanced. This dataset is balanced (70/70/70),
  so weights are off; CV10 shows what happens when they are missing.

## Splitting and the number you may report

```python
splits = dataio.classification_splits()        # grouped by source, 210/45/45
```

Report the **test** number once, at the end. The validation split exists to choose the
epoch; touching test to choose anything turns it into a validation set and your reported
number becomes optimistic. Lab 1 measures what ignoring this costs: 0.822 grouped versus
0.933 with a leaky split.

## Error analysis, not just accuracy

Accuracy hides which mistakes were made. After training:

```python
pred, probs = training.predict(model, test_images, mean, std)
report = metrics.classification_report(test_labels, pred, datasets.SHAPE_CLASSES)
print(report["per_class"], report["confusion_matrix"])
```

Two questions to answer in your write-up:

1. Which class pair is most confused, and is that pair geometrically similar?
2. For the wrong predictions, is the model confidently wrong (probability > 0.9) or
   uncertain? Confident errors are the ones that hurt in deployment.

## Practice

1. Train the reference configuration. Record best epoch, best val accuracy, test
   accuracy, and total seconds.
2. Remove augmentation and retrain. Report the test accuracy change.
3. Cut the training set to 30 images and retrain. Describe both curves.
4. Add a fourth class that is visually similar to an existing one (for example a
   rotated square). Report confusion between the pair.

## Check yourself

1. Best validation accuracy is 1.000 at epoch 12 and 1.000 at epoch 25. Which model do
   you ship, and why does the answer matter more on a harder task?
2. Your train accuracy is 0.99 and validation is 0.61. Name two changes and what each
   one targets.
3. What is wrong with reporting the best test accuracy across 20 epochs of training?

## What comes next

[CV06](cv06-transfer-learning.md) asks whether a model trained on a *different* task can
give you a better starting point than training from scratch - and measures the answer
instead of assuming it.
