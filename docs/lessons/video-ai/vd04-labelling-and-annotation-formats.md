# VD04 - Labelling video and annotation formats {#vd04}

**Section path:** [Overview](index.md) · **Module 4** · [Lab 4](labs/lab-4-domain-adaptation.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 1.5 h reading, 2.5 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | [VD03](vd03-frame-extraction-and-datasets.md) |
| **You will produce** | One frame's annotations in four formats, a validation report, and a split that provably leaks nothing |

## Why this module exists

A video annotation is not a box. It is a box **plus a time** plus, if you want to count
anything, an identity. Each of those three can be lost in a format conversion, and all three
losses are silent.

The section's ground truth is a JSON record per frame:

```json
{"frame": 12,
 "objects": [{"track_id": 3, "class": "truck", "box": [412.0, 190.0, 516.0, 246.0]}]}
```

`street_day` has 6 vehicles over 60 frames, so its ground truth is 360 objects - the 360 that
Lab 2's pretrained detector fails on 319 times. Knowing that number before you look at a
metric is half of reading the metric correctly.

## The four formats you will meet

| Format | Box convention | Origin | Where it comes from |
| --- | --- | --- | --- |
| This section's JSON | `[x1, y1, x2, y2]` pixels | top-left | generated / exported by the labs |
| COCO JSON | `[x, y, w, h]` pixels | top-left | torchvision detection datasets, pycocotools |
| YOLO text | `cx cy w h`, normalised 0-1 | centre | YOLO-family trainers |
| Pascal VOC XML | `xmin ymin xmax ymax`, **1-based** | top-left | older detectors, some annotation tools |

Three conversions, three different opportunities to be wrong by one or by a factor of the
frame size:

```python
from video_core import labels

box = [412.0, 190.0, 516.0, 246.0]
coco = labels.to_coco_box(box)          # [412.0, 190.0, 104.0, 56.0]
back = labels.from_coco_box(coco)       # [412.0, 190.0, 516.0, 246.0]
yolo = labels.to_yolo(box, 640, 360)    # [0.725, 0.606, 0.1625, 0.1556]
```

### The one bug everyone ships once

Reading a COCO `w` as if it were `x2` gives boxes that are too small by exactly the object's
`x` coordinate. For an object near the left edge, `x` is small and the box looks fine. For an
object on the right, the box is 400 pixels too narrow. The detector trained on that data
learns a bias towards the left of the frame, and the only symptom is a low mAP with no error
message anywhere.

The guard is `validate_records`, which checks the result against the frame:

```python
report = labels.validate_records(records, width=640, height=360)
print(report["objects"], report["ok"], report["problems"][:2])
# 360 True []
```

It catches non-positive boxes, boxes outside the frame (with 1 px of tolerance for rounding),
and classes not in the schema. Run it on every conversion. It is cheap and it is the only
part of the labelling pipeline that fails loudly.

YOLO's normalisation has a second failure mode: if the frame is resized and the boxes are not
rescaled, everything still validates - normalised boxes are in range whatever their aspect -
but every object is in the wrong place. Validation cannot catch that; only a visual check
can. Which is why every conversion in this section is followed by an annotated frame you look
at, not just a JSON file you trust.

## Identity: the part video adds

Image labelling needs a class and a box. Video labelling needs **the same ID across frames**,
because:

- counting is deduplicating by ID (Lab 3);
- speed is displacement per ID over time (Lab 3);
- an ID switch is a measurable tracking error (MOTA, IDSW);
- ground truth with IDs is what makes those metrics computable at all.

Annotation rule for this section: an ID is assigned when a vehicle first appears and ends when
it leaves the frame **for good**. A vehicle hidden behind a bus for three frames keeps its ID.
A vehicle that leaves and re-enters ten seconds later gets a new one - unless you have a
re-identification requirement, which this course does not cover.

The section's generator produces exact IDs, so `track_id` is free and provably consistent:

```python
truth = support.ground_truth("street_day")     # 60 records with track ids
print(sorted({obj["track_id"] for rec in truth for obj in rec["objects"]}))
# [1, 2, 3, 4, 5, 6]
```

When you annotate real footage you will not be this lucky. Plan for IDs to be the most
expensive part of the job, and budget a review pass whose only purpose is ID consistency.

### Inter-annotator agreement, briefly

Two people labelling "car vs truck" disagree on vans and pickups; two people labelling the
same object's edge disagree by 2-4 pixels. Both disagreements are data, not noise to be
wished away:

- **Class agreement** - report Cohen's kappa on a double-labelled sample. Below about 0.8, the
  label definition needs rewriting before more data is collected.
- **Box agreement** - report mean IoU between annotators. Below 0.75, your metric's ceiling is
  already visible: a detector cannot out-score its own ground truth.

This section's synthetic labels have zero annotator disagreement, which is precisely why the
labs can be graded exactly - and precisely why they are not a substitute for a real labelling
project.

## Exporting, and what each exporter preserves

```python
from video_core import labels

labels.write_coco("data/video/annotations/coco/instances_train.json", records,
                  image_name="street_day")
labels.write_yolo("data/video/annotations/yolo", records, width=640, height=360)
labels.write_voc("data/video/annotations/voc/Annotations/street_day_0012.xml",
                 records[12], width=640, height=360, image_name="street_day_0012.jpg")
```

| Exporter | Keeps `track_id`? | Notes |
| --- | --- | --- |
| `write_coco` | yes, as a non-standard `track_id` field | pycocotools ignores it; your code should not |
| `write_yolo` | **no** | YOLO text lines have no ID field; a separate ID file is needed |
| `write_voc` | **no** | VOC has no ID concept |
| `read_coco` | yes, if present | round-trips the section's own export |

Losing the ID on the way to YOLO is the most common real-world data loss in this domain. If
your trainer needs YOLO format and your metric needs IDs, keep the JSON as the source of truth
and generate YOLO as a build artefact - never edit the YOLO files by hand.

## Splitting without leakage

Three splits, chosen by video name, in `labels.split_by_video`. The check that matters:

```python
splits = labels.split_by_video(records, fractions=(0.6, 0.2, 0.2), seed=0)
print(labels.video_leakage(splits))
# {'videos': {'train': 2, 'val': 1, 'test': 4}, 'overlaps': {}, 'leaky': False}
```

And the demonstration of the bug it prevents:

```python
leaky = labels.frame_split_leakage(records, {"train": records[:40], "test": records[40:]})
print(leaky)
# {'shared_frame_ids': 0, 'leaky': False}   <- frame *indices* restart per video
```

Read that second result carefully: `frame_split_leakage` compares frame **indices**, and this
section's records all start at frame 0, so a naive comparison finds nothing. That is the trap.
The leak is not shared indices, it is shared *scenes*: two frames 3 apart from `street_day`
are near-identical images. The function exists to make the point that index comparison is not
enough - and `tests/test_video_ai.py` uses a synthetic case where indices do overlap to prove
the detector works when there is something to detect.

The rule that actually protects you is structural: **group by video before splitting, and
never let the same video's name appear in two splits.** Everything else is a heuristic.

The section's split is deliberately adversarial:

| Split | Videos | Conditions |
| --- | --- | --- |
| train | `street_day`, `street_dusk` | clear day, low sun |
| val | `street_quiet` | clear day, fewer vehicles |
| test | `street_night`, `street_rain`, `street_shake`, `street_crowd` | night, rain, camera shake, congestion |

A model that scores well on train and poorly on test is not broken - it is telling you that
the test set is where the deployment lives. Lab 2 makes that number explicit (0.048 day,
0.000 night) before any training happens.

## Annotation quality checklist

Before any model sees your labels:

- [ ] Every box is validated (`validate_records` returns `ok: True`).
- [ ] Ten random frames have been viewed with boxes drawn on them.
- [ ] IDs are consistent across occlusions in a five-second sample you watched end to end.
- [ ] Class definitions are written down, including the van/pickup cases.
- [ ] Occluded and truncated objects have a documented policy (include, exclude, or flag).
- [ ] The split is by video, and `video_leakage` says `leaky: False`.
- [ ] The dataset card states provenance, licence, and known gaps.

## Checks

- [ ] You can convert a box through all four formats and back, by hand, without running code.
- [ ] You can name the failure mode that validation cannot catch, and the check that does.
- [ ] You can explain why `track_id` survives COCO but not YOLO or VOC.
- [ ] You can state the split rule in one sentence and defend it against "but we need more data".
- [ ] You have looked at an annotated frame from your own pipeline in the last hour.
