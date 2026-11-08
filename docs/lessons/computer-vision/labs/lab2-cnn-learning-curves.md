# Lab 2 - Train a basic CNN and inspect learning curves

**Section path:** [Overview](../index.md) · Modules [CV04](../cv04-convolutional-networks.md), [CV05](../cv05-classification-from-scratch.md) · **Lab 2** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 10% of the section assessment |
| **Time** | 3 hours |
| **Hardware** | CPU-only (reference run: 3.0 s) |
| **Code** | `projects/computer-vision/lab2_cnn_learning_curves.py` |
| **Prerequisite** | CV03, CV04 |

## The task

Train a small CNN from scratch, record every epoch, and read the curves. Then change one
thing at a time until you can explain the shape of the curve rather than just report it.

Deliverables:

1. learning curves (PNG and the raw history JSON),
2. best epoch, best validation accuracy, test accuracy, overfitting gap, wall time,
3. an ASCII plot from the terminal (no matplotlib dependency),
4. a comparison with one variant where augmentation is off.

## Setup

```bash
python scripts/make_vision_data.py      # if not already run
cd projects/computer-vision
python lab2_cnn_learning_curves.py
```

The model is `TinyCNN(num_classes=3, width=16)` - 72,499 parameters, three
`conv-bn-relu` pairs with max-pool, global average pooling, one linear layer. Training
uses 210 images, validates on 45, tests on 45, all grouped by source.

## Run it

```bash
python lab2_cnn_learning_curves.py --epochs 25
python lab2_cnn_learning_curves.py --selftest      # 6 epochs, for CI
```

Verified output:

```text
best epoch 18  best val_acc 1.000
test accuracy 1.000  overfitting gap +0.035
total training time 2.8s
figure: .../outputs/lab2_learning_curves.png
history: .../outputs/lab2_history.json

0 failure(s)
PASS  training ran, curves recorded, model evaluated
```

Artifacts written to `projects/computer-vision/outputs/`:

| File | Contents |
| --- | --- |
| `lab2_learning_curves.png` | train/val loss and accuracy, generated with Pillow |
| `lab2_history.json` | 25 epochs of loss, accuracy, per-epoch seconds, config |

```text
history keys: epochs, train_loss, train_acc, val_loss, val_acc, epoch_seconds,
              total_seconds, best_epoch, best_val_acc, overfitting_gap,
              batch_size, lr, seed, train_size, val_size, test_accuracy, augmented
```

## Reading the result

`overfitting_gap = -0.029` is negative: validation accuracy is slightly *above* training
accuracy. That is normal with dropout and augmentation, and it tells you the model was
still improving, not memorising.

Test accuracy of 1.000 on 45 images is a saturated task. The lab's value is the
infrastructure: history, curves, best-epoch selection, reproducible seeds. Treat 1.000 as
"this configuration solved this dataset", not as a model quality claim.

Terminal curves (abridged, from the same run):

```text
loss  1.05 |*                                                       |
      0.79 | *                                                     |
      0.52 |   **                                                  |
      0.26 |      *******                                          |
      0.00 |             *****************************************  |
           +--------------------------------------------------------+
             epoch 1                                         epoch 25
```

## Test cases

| Check | Expected | Verification |
| --- | --- | --- |
| History length | equals `--epochs` | JSON `len(val_acc)` |
| Best epoch within range | `1 <= best_epoch <= epochs` | printed |
| Test accuracy in [0, 1] | yes | printed |
| PNG written and non-empty | > 1 KB | file size |
| JSON parseable | valid | `json.load` |
| Determinism | two runs with `--seed 0` match | compare JSON |
| ASCII plot | 25 rows, no crash | stdout |

```bash
python -m unittest tests.test_computer_vision.TestTrainingAndModels -v
```

## Rubric

| Criterion | Marks | What earns full marks |
| --- | --- | --- |
| Runs and reproduces | 20 | both artifacts produced; two runs identical |
| Curve interpretation | 25 | identifies the shape and what it implies about task difficulty |
| Variant experiment | 20 | augmentation off, both accuracies reported, difference quantified |
| Best-epoch reasoning | 15 | explains why the best epoch, not the last, is shipped |
| Write-up honesty | 20 | states the dataset is too easy and names a harder variant |

## Extensions

1. `--no-augment` and compare. Reference: 0.889 without augmentation at 25 epochs vs 1.000
   with it.
2. Cut training to 30 images. Report when validation first exceeds training.
3. Add a fourth, confusable class (rotated square) and describe the new confusion.
4. Set `patience=3` and report which epoch you would ship and why.

## Submit

```text
cv-lab2/
  README.md            # commands, versions, wall time
  curves.png
  history.json
  analysis.md          # curve shape, variant comparison, what would make this hard
```

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| No PNG written | outputs dir missing | script creates it; check permissions |
| Curves flat at 1.000 from epoch 3 | task too easy | that is the honest result; do the harder variant |
| Different numbers on rerun | seed not fixed | pass `--seed 0` |
