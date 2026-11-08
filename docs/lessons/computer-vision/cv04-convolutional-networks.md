# CV04 - Convolutional neural networks {#cv04}

**Section path:** [Overview](index.md) · **Module 4** · [Lab 2](labs/lab2-cnn-learning-curves.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 5 hours: 2.5 h reading, 2.5 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | F11, F12 (neural networks, backpropagation), CV03 |
| **You will produce** | A parameter count you computed by hand and matched in code, and a feature-map inspection |

## Why this module exists

A fully connected layer on a 64x64x3 image needs 12,288 weights per output unit. It
also learns each pixel position independently, so a cat in the top-left and a cat in
the bottom-right are unrelated inputs to that layer. Convolution fixes both problems at
once: the same small filter slides over the image (parameter sharing, translation
equivariance) and it looks only at a local neighbourhood (locality).

Everything in the rest of this section is a convolution stack plus a training loop.
Knowing the arithmetic means you can predict a model's size, its cost, and the output
shape of any layer without running it.

## The arithmetic you must be able to do

For a convolution with input size `H x W`, kernel `k`, padding `p`, stride `s`:

```text
H_out = floor((H + 2p - k) / s) + 1
params = (k * k * C_in + 1) * C_out          # +1 per output channel for bias
```

Worked example: this section's classifier, `TinyCNN(width=16)`, on a 64x64 input. Each
block is `conv-bn-relu, conv-bn-relu, maxpool(2)`; every convolution is 3x3, stride 1,
padding 1, and carries no bias (the batch-norm layer supplies it):

| Layer | Config | Output | Params |
| --- | --- | --- | --- |
| block1 conv1 | 3 -> 16 | 16 x 64 x 64 | 432 |
| block1 conv2 | 16 -> 16 | 16 x 64 x 64 | 2,304 |
| block2 conv1 | 16 -> 32 | 32 x 32 x 32 | 4,608 |
| block2 conv2 | 32 -> 32 | 32 x 32 x 32 | 9,216 |
| block3 conv1 | 32 -> 64 | 64 x 16 x 16 | 18,432 |
| block3 conv2 | 64 -> 64 | 64 x 16 x 16 | 36,864 |
| gap + fc | 64 -> 3 | 3 | 195 |

`models.count_parameters(model)` reports **72,499** for this three-class model, and
**72,564** for the four-class model in Lab 3 (a 4-output classifier is 65 parameters
larger). The 448 missing from the table above is batch-norm weight and bias, two per
channel across six batch-norm layers. Compute one layer by hand, then check it against
`count_parameters`. If your number is off by a factor of `C_in`, you forgot that every
output channel sees every input channel.

## Receptive field: how much of the image a neuron sees

Track two numbers: receptive field `r` and jump `j` (how far apart two input pixels are
after all the strides so far). For a kernel `k`: `r += (k - 1) * j`. For a 2x2 max-pool
with stride 2: `r += j`, then `j *= 2`.

```text
start                     r = 1   j = 1
conv1 (k3 s1)          -> r = 3   j = 1
conv2 (k3 s1)          -> r = 5   j = 1
maxpool(2)             -> r = 6   j = 2
conv3, conv4 (k3 s1)   -> r = 14  j = 2
maxpool(2)             -> r = 16  j = 4
conv5, conv6 (k3 s1)   -> r = 32  j = 4
maxpool(2)             -> r = 36  j = 8
```

The deepest feature sees a **36x36** patch of a 64x64 image - comfortably larger than
the 12-20 pixel objects in this section's data, and one reason the classifier works at
all. The global average pool then merges every position, so the decision uses the whole
image even though no single deep neuron does.

!!! note "Receptive field explains a whole class of bugs"
    If your objects are 120 pixels wide in a 224x224 input and your deepest receptive
    field is 36, the model cannot see a whole object. The symptom is a model that learns
    textures and local parts but never the shape. More depth, more stride, or a larger
    input are the three fixes; measure before choosing.

## Batch normalization, honestly

`nn.BatchNorm2d` normalizes each channel using batch statistics during training and
running statistics at inference. Two consequences:

- It stabilizes training at higher learning rates, which is why every model here has it.
- The output during training depends on batch composition. Batch size 1 is not "the
  same model with less data"; it is a different normalization.

If results shift between training and inference, the first thing to check is
`model.eval()`. Forgetting it is the second most common bug in this section after
preprocessing.

## Feature maps: what the network actually sees

```python
import torch
from vision_core import models, training

model = models.TinyCNN(num_classes=3, width=16)
x = training.prepare_inputs(images[:8])          # (8, 3, 64, 64)
with torch.no_grad():
    maps = model.block3(model.block2(model.block1(x)))
print(maps.shape)                                # (8, 64, 8, 8)
print(model.features(x).shape)                   # (8, 64) - pooled embedding
```

Note the second shape: `features()` returns the **pooled 64-d embedding**, which is what
the transfer and similarity labs consume. Spatial maps come from the block stack.
Conflating the two produces a shape error that looks mysterious.

Early channels respond to edges and colour boundaries, later channels to combinations.
You can check this without any plotting library: print each channel's mean and standard
deviation across inputs. A channel that is near zero for every input is dead - a real
outcome when the learning rate is too high.

## Why this beats an MLP here

| Property | MLP on pixels | CNN |
| --- | --- | --- |
| Params for one 64x64x3 -> 64 layer | 786,496 | 36,928 (3x3 conv, 64 -> 64) |
| Translation behaviour | learns each position separately | shared filter, equivariant by construction |
| Small-data behaviour | memorises | exploits locality |

The labs make this concrete rather than rhetorical: the scratch classifier has 72,564
parameters and reaches 0.500 on the four-class object task (Lab 3), a 260-parameter
linear probe on a pretrained trunk also reaches 0.500, and fine-tuning that trunk
reaches 0.722 (CV06, CV07). Parameter count alone predicts nothing; what the parameters
are attached to is the point.

## Practice

1. By hand, compute output shapes and parameter counts for the table above. Verify with
   `count_parameters`.
2. Remove the second convolution from each block and report the new parameter count and
   test accuracy. Explain the direction of the change.
3. Compute the receptive field after each layer. At what depth does the model first see
   a whole 16x16 object?
4. Inspect per-channel statistics of the third block. Find a channel that is near zero
   for every input, or explain why none are.

## Check yourself

1. A 3x3 convolution with 32 input and 64 output channels: how many weights, and how
   many multiply-adds for a 16x16 output?
2. Why does removing BatchNorm usually hurt more at high learning rates than at low ones?
3. Your deepest neuron sees 36x36 and your objects are 120x120. Name two changes that
   increase the receptive field and one cost of each.

## What comes next

[CV05](cv05-classification-from-scratch.md) trains this network end to end and reads its
learning curves - including what it means when the curves say the task was too easy.
