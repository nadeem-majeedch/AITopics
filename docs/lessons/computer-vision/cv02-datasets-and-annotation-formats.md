# CV02 - Image datasets and annotation formats {#cv02}

**Section path:** [Overview](index.md) · **Module 2** · [Lab 1](labs/lab1-licensed-dataset-classifier.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 2 h reading, 2 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | CV01 |
| **You will produce** | A split you can defend, an audit that shows whether it leaks, and one image in both YOLO and COCO form |

## Why this module exists

A dataset is not a folder of images. It is images, labels, provenance, a licence, and
a rule for which images may appear together in training and test. Most published
"state of the art" numbers that fail to reproduce fail on one of those, not on the
architecture.

The specific failure this module prevents: **source-level leakage**. If you photograph
one mug five times, split by image, and report 95% accuracy, you have mostly measured
whether the model can recognise that mug. Your test set contains near-copies of your
training set.

## What this section's data is

Every image in this section is generated deterministically by
`scripts/make_vision_data.py`. No download, no account, no personal data.

| Property | Value |
| --- | --- |
| Licence of generated images | CC0-1.0 (public domain dedication) |
| Creates | shapes, "everyday objects", detection scenes, segmentation masks, synthetic faces |
| Seeds | fixed per dataset, so reruns are byte-identical |
| Size | 300 classification images from 100 sources; 120 object images; 200 detection images with 302 boxes; 80 segmentation images; 64 synthetic faces from 8 identities |

The classification set is built the way a real one is: **100 sources**, each rendered
into several variants (position, scale, colour, noise, blur). Variants of one source
share an identity. The `source_id` field carries that fact, and the split honours it.

!!! note "Why synthetic data is the right call here"
    Real datasets are better for final projects and worse for teaching the pipeline:
    they arrive pre-split, pre-cleaned, and often already leaky. Synthetic data lets
    you *see* the leak, measure it, and fix it in one lab. Lab 1 asks you to repeat the
    exercise on a licensed real dataset of your own choosing, and states what to record.

## The record type

Every loader in this section returns the same object, so labs can share code:

```python
@dataclass
class ImageRecord:
    image: np.ndarray            # HWC uint8
    label: int                   # class index, -1 when the task is not classification
    source_id: str               # identity that must not cross the split boundary
    meta: dict                   # boxes, mask, identity name, ...
```

`source_id` is the field that makes leakage auditable. If your dataset does not have
one, derive it (a product id, a video id, a photographer+session id) and write down how.

## Splitting: grouped, not random

```python
from vision_core import datasets, dataio

records = dataio.classification_records()
grouped = datasets.group_split(records, seed=0)     # 70/15/15 by source
naive = datasets.random_split(records, seed=0)      # 70/15/15 by image - leaky
```

Measured on this section's 300 images / 100 sources:

| Split rule | Shared sources between train and test | Cross-split look-alike pairs | Test accuracy after the same budget |
| --- | --- | --- | --- |
| Grouped by source | 0 | 1 | **0.822** |
| Random per image | 91 | 14 | 0.933 (inflated) |

The 0.111 difference is the leak, measured rather than asserted. Note that the leaky
number is the *flattering* one; that is exactly why leakage survives in student
projects and in papers.

The audit has two severities, and the distinction is worth internalising:

- `hard_leaky` - the same source appears in two splits. Always fixable, never acceptable.
- `soft_leaky` - different sources that are near-identical by perceptual hash. Sometimes
  legitimate (two photos of the same product from different sellers), sometimes not.
  Report it and decide deliberately.

```python
audit = datasets.audit_leakage(naive)
print(audit["hard_leaky"], audit["n_shared_sources"], audit["cross_split_near_duplicate_count"])
```

## Annotation formats

Classification needs a label per image. Detection and segmentation need geometry, and
the geometry has three competing conventions you will meet in the wild:

| Format | Box representation | Class ids | Where you meet it |
| --- | --- | --- | --- |
| YOLO (`.txt` per image) | `cx cy w h`, normalized 0..1 | 0-based index | Ultralytics, most detector tutorials |
| COCO (`.json`) | `x y w h`, pixels, top-left origin | category ids, commonly 1-based | torchvision, Detectron2, most benchmarks |
| Pascal VOC (`.xml`) | `xmin ymin xmax ymax`, pixels | names, 1-based in files | older detection code |

This section implements YOLO and COCO round trips, including the 0-based/1-based
mismatch, because that mismatch is the single most common annotation bug:

```python
lines = annotations.to_yolo_lines(anns, width=64, height=64)
anns_back = annotations.from_yolo_lines(lines, 64, 64)
coco = annotations.to_coco(images, {"img": anns}, ("circle", "square", "triangle"))
parsed, names = annotations.from_coco(coco)
```

```text
YOLO:  class 0 -> "0 cx cy w h"      (index, must be 0 <= i < n_classes)
COCO:  class 0 -> "category_id": 1    (id, must be looked up, never assumed)
```

A detector trained on COCO ids used directly as indices will treat category 3 as
class 3 of 3 and crash, or worse, silently train on the wrong label.

## Validate before you train

Invalid annotations are the most common reason a detector's loss never improves. The
validator reports rather than raises, and its contract is precise:

| Problem | Action |
| --- | --- |
| class id outside `0..n_classes-1` | dropped, reported |
| degenerate box (`w` or `h` below `min_size`) | dropped, reported |
| box outside the image | **clipped**, reported, kept |

```python
report = annotations.validate_annotations(boxes, width, height, n_classes)
print(report["n_input"], report["n_kept"], report["problems"])
```

This is not hypothetical. While building this section, a one-line bug in the COCO
reader applied the `xyxy -> xywh` conversion to a bbox that was already `xywh`. Every
box came back inverted. The detector trained to mAP **0.000** and the only visible
symptom was the annotation audit reporting 274 invalid boxes. Fixing that line took
mAP from 0.000 to 0.324. **The audit was the debugging tool; the loss curve was not.**

## Manual annotation, if you use your own images

1. Choose 60-150 images for a first detector. Fewer than 50 cannot support a val split.
2. Use one tool and one convention. Record the tool, its version, and the export format.
3. Define the class list in writing *before* annotating, including what "partially
   visible" and "too small to label" mean. Ambiguity here becomes label noise.
4. Annotate 10 images, then re-annotate them a day later without looking. Agreement
   below ~85% means the definition, not the annotator, needs fixing.
5. Export, run `validate_annotations`, and fix every problem before training.
6. Keep the images out of version control if they are large; version the annotations
   and a manifest with hashes instead.

## Licence and attribution

Record, for every dataset you use:

```text
name, version/date, URL, licence (SPDX id if possible), attribution string,
what you changed, how you split it, and whether redistribution is allowed.
```

Synthetic data here is CC0-1.0, so you may redistribute it freely. Popular real
datasets are not: check each one before you put images in a public repository. The
dataset card template in [Model card and dataset card](model-card.md) has the fields.

## Practice

1. Reproduce the audit table above: build both splits, print shared sources and
   look-alike counts, train briefly on each, and report both accuracies.
2. Take one annotated image, export it to YOLO and to COCO, read both back, and show
   the boxes agree to within a pixel.
3. Deliberately corrupt three annotations (inverted box, class 9, box off the edge)
   and confirm the validator catches all three.
4. Write the licence block for this section's data and for one real dataset you
   would like to use.

## Check yourself

1. Why can a random per-image split report 0.933 when the honest number is 0.822?
2. Your COCO file has `category_id: 3` and three classes. What index is it, and what
   would you assert in code to make that safe?
3. Name one dataset where near-duplicates across splits are legitimate, and one where
   they are not.

## What comes next

[CV03](cv03-preprocessing-and-augmentation.md) turns these images into model input -
and shows why the normalization statistics must come from the training split alone.
