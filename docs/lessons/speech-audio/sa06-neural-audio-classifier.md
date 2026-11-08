# SA06 - A basic neural audio classifier {#sa06}

**Section path:** [Overview](index.md) · **Module 6** · [Lab A](labs/lab-a-environmental-sound-classifier.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 2 h reading, 2 h practice |
| **Hardware** | CPU-only (14 epochs take about 9 seconds at one thread) |
| **Prerequisites** | SA03, SA05, F11-F12 |
| **You will produce** | A trained classifier with a learning curve, a per-class report, and a robustness table |

## Why this module exists

The convolutional classifier on log-Mel features is the workhorse of audio: keyword
spotting, environmental sound, machine fault detection, and the encoder of many speech
systems. It is small enough to read completely - 72,276 parameters, 0.29 MB - and it
demonstrates the two things that distinguish audio from images: the input is a
time-frequency map, and the augmentations must respect that structure.

## The model

```python
from speech_core import models

model = models.TinyAudioCNN(num_classes=4, width=16, n_mels=40)
print(models.count_parameters(model))         # 72,276
print(round(models.model_size_mb(model), 3))  # 0.289
```

Four blocks, each `conv3x3 -> BN -> ReLU -> conv3x3 -> BN -> ReLU -> maxpool(2)`, then a
global average pool and one linear layer. Input `(1, 40, T)`: 40 Mel bands by time.

Two details matter more than the depth:

* **Pooling both axes** shrinks time as well as frequency, so the model becomes
  time-shift tolerant but also loses temporal precision. That is acceptable for "what sound
  is this" and unacceptable for "when did it start".
* **Global average pooling instead of flattening** keeps the parameter count independent
  of clip length. A flattened 40x101 input into a 64-unit layer would be 259k parameters
  on its own.

Per-layer arithmetic, with `width=16`:

| Block | Output shape | Parameters (conv only) |
| --- | --- | --- |
| input | 1 x 40 x 101 | - |
| block1 (2 conv, pool) | 16 x 20 x 50 | 144 + 2,304 |
| block2 (2 conv, pool) | 32 x 10 x 25 | 4,608 + 9,216 |
| block3 (2 conv, pool) | 64 x 5 x 12 | 18,432 + 36,864 |
| global average pool | 64 | 0 |
| linear | 4 | 260 |
| batch-norm weights/biases | - | 448 |

The reported total is 72,276: convolutions 71,568, linear 260, batch-norm 448. Compute one
block by hand and check it; an order-of-magnitude error usually means forgetting that every
output channel sees every input channel.

## Features and batching

```python
from speech_core import training

x_train, lengths, floor = training.build_inputs(train_records, n_mels=40)
mean, std = training.feature_stats(x_train)
x_train = training.normalize_inputs(x_train, mean, std)
```

`build_inputs` stacks log-Mel matrices into `(N, 1, 40, T_max)`, padding with the minimum
feature value rather than zero. Padding with zero after dB conversion creates a loud
broadband stripe, and the model will happily learn from it.

`feature_stats` returns the training mean and standard deviation: **-30.95 and 22.95** for
this corpus. Carry them with the model. A classifier evaluated with unnormalised inputs does
not error; it returns confident nonsense, which is worse.

## SpecAugment: the audio augmentation that matters

Image augmentation (crop, flip, colour jitter) has no audio analogue. The augmentation that
works is masking bands of frequency and spans of time:

```python
import numpy as np
from speech_core import training

rng = np.random.default_rng(0)
augmented = training.spec_augment(x_train, rng, n_freq_masks=2, n_time_masks=2,
                                  freq_width=6, time_width=10)
```

Two frequency masks up to 6 bands wide and two time masks up to 10 frames wide force the
model to use redundant evidence. It is the audio equivalent of cutout, and it is the single
most effective regulariser for small audio datasets.

## The training loop

```python
from speech_core import models, training

history, model = training.train_classifier(
    models.TinyAudioCNN(num_classes=4, width=16),
    x_train, [r.label for r in train_records],
    x_val, [r.label for r in val_records],
    epochs=14, batch_size=16, lr=2e-3, seed=0, augment=True, log=False,
)
print(history.best_epoch, round(history.best_val_acc, 3))     # 3 1.0
print(round(sum(history.seconds), 2))                         # 8.88 s on this CPU
```

The loop keeps the weights from the best validation epoch, which matters when the corpus is
small enough to memorise in a few epochs. `history.ascii_plot()` prints the curves without
matplotlib, and `history.plot_png()` writes them with Pillow.

On this corpus the curve saturates by epoch 3 and stays there. A validation accuracy of
1.000 that early is a warning: either the task is easy or the split leaks. The audit from
[SA04](sa04-segmentation-and-datasets.md) is what distinguishes the two.

## Measured results

Verified run (`python lab_a_env_classifier.py`, Windows 11, torch 2.14.1+cpu):

```text
grouped split accuracy : 0.944  (36 held-out clips, sources never seen)
leaky split accuracy   : 1.000  (+0.056)
training               : 14 epochs, 8.88 s, best epoch 3
```

The leaky split gains 0.056, and that is worth understanding rather than hiding. The three
variants of each source differ in noise, gain, and time offset, so a random split does not
hand the model an identical copy; the gain comes from a test `rain` clip whose source the
leaky model already saw. Compare with the image corpus in the computer vision section, where
the same mistake added 0.111. Leakage hurts in proportion to how much the variants share -
which is never zero, and never a reason to use it.

Per-class report on the grouped split:

| Class | Precision | Recall | F1 | Support |
| --- | --- | --- | --- | --- |
| alarm | 1.000 | 1.000 | 1.000 | 3 |
| rain | 1.000 | 0.833 | 0.909 | 12 |
| footsteps | 1.000 | 1.000 | 1.000 | 15 |
| birdsong | 0.750 | 1.000 | 0.857 | 6 |

Support is tiny (3-15 clips), so one error changes a class recall by 0.07-0.33. That is a
property of the test set, not of the model.

Robustness, same model, perturbed test clips:

| Condition | Accuracy | Drop vs clean | Mean confidence |
| --- | --- | --- | --- |
| clean | 0.944 | 0.000 | 0.816 |
| 20 dB SNR | 0.944 | 0.000 | 0.804 |
| 10 dB SNR | 0.889 | 0.056 | 0.739 |
| 5 dB SNR | 0.667 | 0.278 | 0.626 |
| -12 dB gain | 0.778 | 0.167 | 0.731 |
| slower 1.15x | 0.944 | 0.000 | 0.778 |
| narrowband 4 kHz | 0.972 | -0.028 | 0.715 |

Two observations you should be able to explain:

* Confidence falls before accuracy does (0.816 -> 0.739 at 10 dB, for 0.056 accuracy).
  Confidence is a leading indicator, but only if it is calibrated - see SA14.
* A gain change costs accuracy even though the features are logarithmic. The network was
  trained on narrow level statistics and never saw a 12 dB shift; augmentation with random
  gain is the fix.

These numbers reproduce exactly, and getting there needed two things. `models.set_seed` pins
torch to one thread, because multi-threaded CPU convolution reduces in a different order each
run. Just as important, it has to be called *before* the network is constructed: initial
weights are drawn from the global RNG, so seeding afterwards leaves the starting point up to
the process. Get that wrong and two runs of Lab D reported WER 0.03 and 0.31 from identical
code - the most expensive kind of bug in a course, because every number in it silently
becomes unverifiable. On 36 test clips even a reproducible number is still a small sample:
report the seed and the split with any number you quote.

## Debugging advice

| Symptom | Cause | Fix |
| --- | --- | --- |
| Validation accuracy 1.0 at epoch 1 | leaky split or duplicated clips | `audit_leakage`, inspect the manifest |
| Accuracy 0.25 (chance) forever | unnormalised features, or wrong label order | print `x.mean()`, check `class_balance` |
| Loss NaN after a few steps | learning rate too high for batch 16 | `lr=1e-3`, gradient clipping |
| Train 1.0, val 0.4 | too few sources | more variants, SpecAugment, dropout |
| Predictions differ between runs | no seed | `models.set_seed(0)` at the top |
| Slow on CPU | `width=32` and long clips | `width=16`, trim silence |

## Exercises

1. Recompute the parameter count for `width=8` and `width=32` from the table's pattern and
   check with `count_parameters`.
2. Train with `augment=False` and compare the epoch at which validation peaks.
3. Add a time-mask width of 25 frames (a quarter of a second). Does accuracy survive?
4. Replace global average pooling with max pooling and compare robustness to 5 dB SNR.

Next: [SA07 - Speech to text and automatic speech recognition](sa07-asr-and-stt.md)
