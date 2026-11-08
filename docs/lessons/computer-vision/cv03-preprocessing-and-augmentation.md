# CV03 - Preprocessing, resizing, normalization, and augmentation {#cv03}

**Section path:** [Overview](index.md) · **Module 3** · [Lab 2](labs/lab2-cnn-learning-curves.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 2 h reading, 2 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | CV01, CV02 |
| **You will produce** | A preprocessing function with a written contract, and an augmentation experiment with two measured accuracies |

## Why this module exists

Preprocessing is where a model's arithmetic assumptions meet your data. Three
decisions quietly decide whether training works: what shape the input is, what range
its values are in, and whether the *evaluation* path applies exactly the same
transform as training. The last one is the classic bug - train with resizing, evaluate
without it, and the accuracy drop is blamed on generalization.

## Resizing without destroying the task

Three options, three different costs:

| Method | Preserves aspect ratio | Introduces padding | Distorts objects |
| --- | --- | --- | --- |
| Stretch to square | no | no | yes |
| Center crop | yes | no | no, but crops content away |
| Letterbox | yes | yes | no |

`imaging.resize` stretches; `imaging.letterbox` pads. Letterbox returns the mapping as
well as the image, because annotations must be transformed with the same numbers:

```python
out, mapping = imaging.letterbox(image, (32, 32))
# 20x10 image -> scale 1.6 -> 32x16 content, 8 rows of padding split top and bottom
print(mapping)     # {'scale': 1.6, 'resized': (32, 16), 'pad': (0, 8), ...}
```

Any box in original pixels maps as `x' = x * scale + pad_x`. If you forget the pad,
your boxes drift and your detector trains on misaligned targets - a failure that looks
like a weak model.

## Normalization: from the training split only

```python
mean, std = training.dataset_stats(train_images)      # per-channel, from train only
x = training.prepare_inputs(images, mean, std)        # NCHW float32, normalized
```

Two rules, both testable:

1. **Statistics come from the training split.** Computing them over the whole dataset
   leaks the test distribution into preprocessing. The effect is tiny and the habit is
   not, which is why `dataset_stats` takes whichever array you give it and the labs
   pass only training images.
2. **One conversion path.** `prepare_inputs` is the only function that turns uint8
   `NHWC` into normalized `NCHW`. Any second path will eventually disagree with the
   first; the double-normalization bug in CV01 is exactly that.

The section's test suite asserts `mean[0] == 1.0` for an all-red image, so channel
order in the statistics cannot silently swap.

## Augmentation: what it buys and what it costs

Augmentation is a prior: "these variations do not change the label". If that statement
is false for your task, augmentation teaches the model something false.

| Transform | Safe when | Dangerous when |
| --- | --- | --- |
| Horizontal flip | object identity is mirror-invariant | text, digits, handedness matter |
| Small rotation | orientation is incidental | orientation *is* the label |
| Brightness / contrast | lighting varies in deployment | colour is the label (ripeness, hazard) |
| Gaussian noise | sensor noise is expected | fine texture is the signal |
| Blur | camera shake / focus varies | sharpness is the signal |
| JPEG artifacts | images arrive compressed | you are evaluating a codec claim |

```python
config = imaging.AugmentConfig(hflip_p=0.5, rotate_deg=10, max_shift=2, brightness=0.2)
augmented = imaging.augment(image, config, np.random.default_rng(7))
```

The generator is passed in, never global. That makes augmentation **reproducible**:
same seed, same pixels. The suite asserts it, because a stochastic pipeline you cannot
reproduce is a pipeline you cannot debug.

### Measured effect

Same model, same split, same 25 epochs; only the augmentation toggle changes:

| Training | Test accuracy |
| --- | --- |
| No augmentation | 0.889 |
| Flip + shift + rotate + brightness | **1.000** |

That is a 0.111 gain on 45 test images, which is 5 images. Treat the direction as
informative and the magnitude as noisy - a distinction Module 14 makes systematically.

## The validation transform is not the training transform

```text
train:  resize -> random crop -> flip/rotate/brightness -> normalize
eval:   resize (or letterbox) -> center crop            -> normalize
```

Random transforms must never run at evaluation. Center-crop consistency matters more
than which eval transform you choose. Write the contract down:

```python
def preprocess(image, *, training: bool):
    """HxWx3 uint8 -> 3xHxW float32.

    training=True applies random augmentation; evaluation is deterministic.
    Both paths resize and normalize with the training-split statistics.
    """
```

## Practice

1. Letterbox a 20x10 image to 32x32. Report `scale`, resized size, and pad. Transform
   one box with the mapping and verify it lands on the object.
2. Compute train-split mean/std, then show what changes if you compute them over all
   splits instead. Is the difference large? Does that make it acceptable?
3. Run the augmentation toggle experiment above. Report both accuracies and the
   number of test images, then state how much of the difference you trust.
4. Break reproducibility: use `np.random` instead of a seeded `Generator` and show
   that two runs differ.

## Check yourself

1. Your detector's boxes are consistently shifted 4 pixels down after resizing. What
   did you forget?
2. Why is brightness augmentation unsafe for a ripeness classifier but safe for a
   handwritten-digit classifier?
3. You compute normalization statistics over train+val+test. Name the leak and
   whether it can inflate the reported test score.

## What comes next

[CV04](cv04-convolutional-networks.md) explains the layer that makes image models
different from the MLPs in F11-F12, and why parameter sharing is not an optimization
detail but the reason vision works on small data.
