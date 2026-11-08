# CV01 - Digital images, pixels, channels, and formats {#cv01}

**Section path:** [Overview](index.md) · **Module 1** · [Labs](index.md#the-labs) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 3 hours: 1.5 h reading, 1.5 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | [F03 NumPy](../f03-numpy-pandas/index.md) |
| **You will produce** | A written answer to "what does one pixel value mean" and a small script that shows three ways image data is routinely mangled |

## Why this module exists

Almost every vision bug that looks like a modelling problem is a data-layout or
value-range problem. A model trained on `[0, 1]` floats and evaluated on `[0, 255]`
integers does not raise an error; it just performs badly, and you spend a day tuning
a learning rate that was never the issue. The same is true of `HWC` versus `CHW`
channel order, of BGR versus RGB, and of JPEG re-encoding a test set.

This module is short and mechanical on purpose. Everything later depends on you
being able to answer: *what are these numbers, in what order, in what range?*

## What an image actually is

A grayscale image is a 2-D array of intensities. A colour image is a 3-D array with a
channel axis. For 8-bit PNG or JPEG data, each value is an integer in `0..255`.

```python
import numpy as np
from vision_core import imaging

image = imaging.load_image("data/classification/images/shape_0000.png")
print(image.shape, image.dtype)        # (64, 64, 3) uint8
print(imaging.image_info(image))
```

Three conventions you must keep straight, because each has a different failure mode:

| Convention | Common form | Failure when confused |
| --- | --- | --- |
| Channel order | `RGB` vs `BGR` | colours swap; accuracy drops without any error |
| Axis order | `HWC` (images) vs `CHW` (PyTorch) | a 64x64 image becomes 3 rows of 64x64 |
| Value range | `0..255` uint8 vs `0..1` float | saturating gradients or a model that never learns |

`imaging.to_tensor` is the one conversion path in this section:

```python
tensor = imaging.to_tensor(image)      # (3, 64, 64) float32, already divided by 255
back = imaging.from_tensor(tensor)     # (64, 64, 3) uint8
```

If you build your own conversion, test the round trip. `from_tensor(to_tensor(x)) == x`
is a one-line test that catches most of this module's mistakes.

## Integer arithmetic will lie to you

NumPy does not promote `uint8` on overflow; it wraps.

```python
a = np.array([200], dtype=np.uint8)
print(a + 100)        # [44]  - wrapped, no warning
```

That is why `imaging.as_uint8` converts to float, clips to `0..1`, and only then
multiplies by 255 and casts. Any brightness or contrast operation you write must go
through a clipping step or it will produce the ring artefacts you can see when you
add 100 to a bright region of a photo.

## Grayscale is a weighted sum, not an average

```python
gray = 0.299 * R + 0.587 * G + 0.114 * B
```

The weights are Rec. 601 luma coefficients: the eye is far more sensitive to green
than to blue. A channel mean makes pure red and pure blue equally bright, which is
visibly wrong and measurably different:

```python
imaging.to_gray(red_only)    # 0.299
imaging.to_gray(blue_only)   # 0.114
```

The section's test suite asserts exactly these two numbers, because a "simplified"
implementation that averages channels is a common silent substitution.

## Formats: what you lose and when

| Format | Compression | Keeps exact pixels | Notes |
| --- | --- | --- | --- |
| PNG | lossless | yes | the right default for datasets and annotations |
| JPEG | lossy | no | quality 30 changes pixel values; edges smear |
| WebP | both modes | only lossless mode | smaller than PNG at similar quality |
| BMP/TIFF | usually none | yes | large; TIFF for scientific data |

Two consequences that matter for evaluation:

1. **Never re-encode a test set to JPEG between training and evaluation.** You are
   then measuring a different distribution, and the drop is attributable to the
   codec, not the model. `imaging.jpeg_roundtrip(image, quality=30)` exists so you
   can measure that drop deliberately instead of causing it by accident.
2. **Metadata is not pixels.** EXIF orientation, colour profiles, and DPI do not
   change the array you loaded unless something applied them. `imaging.load_image`
   applies EXIF orientation through Pillow; a reader that does not will feed rotated
   images to a model that was trained on upright ones.

## Resolution is information, and it is not free

An image resized from 512x512 to 64x64 keeps the layout and loses the detail. You
cannot recover it. Two quantities are worth computing before you pick an input size:

```text
pixels      = width * height
bytes/frame = pixels * channels * bytes_per_channel      # uint8: 1 byte per channel
```

A 64x64 RGB uint8 image is 12,288 bytes. A 512x512 one is 786,432 bytes - 64x more
compute per image through every layer of a convolutional network. Lab 8 measures this
relationship rather than asserting it: on this section's CPU, the same classifier runs
in 0.43 ms at 24x24, 0.44 ms at 32x32, and 0.59 ms at 48x48.

## The three manglings to reproduce

Before moving on, run this and explain each line in your own words:

```python
from vision_core import imaging
import numpy as np

img = imaging.load_image("data/classification/images/shape_0000.png")

print(imaging.to_tensor(img).shape)                    # 1. axis order changed
print(imaging.as_uint8(img.astype(np.uint8) + 100)[0, 0])   # 2. clipped, not wrapped
print(imaging.to_gray(img).mean(), img.mean())         # 3. luma != channel mean
```

Then break it on purpose: pass a `float32` array in `0..255` to `to_tensor` and
inspect the range. Nothing crashes. That is the lesson - the pipeline has no idea
what your numbers mean, which is why you have to.

## Common failure: the double normalization

```python
x = imaging.to_tensor(image)          # already /255
x = x / 255.0                         # second division: values now 0..0.004
```

The model still trains, the loss still falls, and the accuracy is terrible. If you
suspect this, print `x.min(), x.max(), x.mean()` at the input to the model. Every
preprocessing bug in this section is visible in those three numbers.

## Practice

1. Load one image, print shape, dtype, min, max, and per-channel mean.
2. Convert to tensor, convert back, assert equality with `np.array_equal`.
3. Compute storage for your dataset at 64x64 and at 224x224 RGB uint8.
4. Save the same image as PNG and JPEG quality 30; report the mean absolute pixel difference.

## Check yourself

1. Why does `uint8` addition of 100 to a bright pixel not raise an error?
2. A model trained on RGB is fed BGR data. Which metric degrades, and would the
   training loss have revealed the bug?
3. You resize a 4:3 photo to 1:1 to fit a model. Name two things that change.

## What comes next

[CV02](cv02-datasets-and-annotation-formats.md) turns a folder of images into a
dataset you can split without leaking, and introduces the annotation formats that
[CV09](cv09-boxes-iou-map.md) will later score.
