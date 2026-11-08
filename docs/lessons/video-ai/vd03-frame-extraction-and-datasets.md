# VD03 - Frame extraction and frame datasets {#vd03}

**Section path:** [Overview](index.md) · **Module 3** · [Lab 1](labs/lab-1-preprocessing.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 3 hours: 1 h reading, 2 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | [VD02](vd02-reading-and-writing.md) |
| **You will produce** | An extraction script whose output count you can predict before running it, and a contact sheet you have actually looked at |

## Why this module exists

"Extract every Nth frame" is one line of code and four separate decisions: how many frames,
which ones, how you record which ones, and how you keep frames from the same video out of each
other's evaluation split. Getting any of them wrong is invisible in the code and visible in
the results - as a dataset that looks bigger than it is, or a score that is 30 points too high.

## The arithmetic of sampling

Given a clip at `fps` frames per second, asking for one frame every `interval` seconds, the
number of frames to skip is

\[
\text{stride} = \operatorname{round}(\text{fps} \times \text{interval})
\]

and the interval you actually get is

\[
\text{interval}_{\text{actual}} = \frac{\text{stride}}{\text{fps}}
\]

The rounding is where students lose accuracy. At 10 fps and a requested 0.5 s interval the
stride is 5 and the interval is exactly 0.5 s. At 29.97 fps and a requested 1 s interval the
stride is 30 and the real interval is 1.001 s - a 0.1% error that does not matter for one clip
and does matter when you integrate a flow rate over an hour. At 25 fps and a requested 0.1 s
interval the stride rounds to 3 (because 2.5 must become an integer) and your interval is
0.12 s, a 20% error.

The section does the rounding in exactly one place, `video.sample_by_time`, which converts
seconds to a frame stride and then walks the file:

```python
from video_core import video

samples = video.sample_by_time("data/video/street_day.mp4", every_s=0.5)
print(len(samples), samples[1][0], samples[1][1])
# 12 5 0.5

info = video.probe("data/video/street_day.mp4")
stride = round(info.fps * 0.5)                 # 5 frames
print(stride, stride / info.fps)               # 5 0.5 - requested and actual agree
```

If you want the numbers before you sample, print them: `stride` and `stride / fps` are the two
values you should report. Lab 1 asserts they agree here - 0.5 s requested, 5 frames used,
0.5 s actual, 12 frames extracted from a 60-frame clip. Predict 12 before you run it; if you
cannot, re-read this paragraph. (60 frames / 5 = 12 samples at indices 0, 5, ..., 55.)

Note that `sample_by_time` is a convenience wrapper over the same sequential decode with a
stride, not a seeking sampler: on a long clip, "one frame per second" implemented by seeking
costs far more than reading and discarding.

### Stride versus time

Two samplers, two meanings:

| Sampler | Keeps frames | Good for | Breaks when |
| --- | --- | --- | --- |
| By stride | every `k`-th frame | fixed-rate cameras, cheap loops | rate varies between sources |
| By time | frames nearest `n * interval` | mixed sources, reporting in seconds | the interval is shorter than a frame |

Time-based sampling with a variable-rate source needs the container's timestamps, not
`index / fps`. The section's generated clips are constant-rate, so both agree - which is
exactly why the code asserts it rather than assuming it:

```python
for index, stamp, _ in video.iter_frames(path):
    assert abs(stamp - index / info.fps) < 0.11     # Lab 1's tolerance, in seconds
```

The same assertion is what catches a mislabelled clip in Lab 1's checks: it is the only place
where a wrong `fps` in the manifest becomes visible.

## How many frames is enough?

Two independent budgets:

**Compute.** A detector at 4 ms/frame (this section's small model, Lab 8) processes a
one-minute 30 fps clip in 7.2 seconds; at 58 ms/frame (the pretrained SSDLite baseline in
Lab 2) the same clip takes 104 seconds. Sampling every fifth frame cuts those to 1.4 s and
21 s.

**Arithmetic for counting.** A line counter needs to see each vehicle on both sides of the
line at least twice to have a direction, so with `d` frames of visibility you can stride up to
about `d / 2`. In this section's clips a vehicle is visible for roughly 40 frames, so stride 5
still works (Lab 8 measures a count error of 2 at stride 5) and stride 10 does not.

The honest procedure is: pick a stride from the compute budget, then **measure** the accuracy
loss at that stride on your validation video, and quote both numbers. Lab 8 does exactly this
for strides 1, 2, 3, and 5.

## Near-duplicate frames

At 10 fps, consecutive frames differ slightly; at 60 fps they differ hardly at all. A dataset
built from every frame of a 60 fps clip has 60 near-copies per second, which:

- inflates the dataset size without adding information;
- inflates accuracy if the split is random, because the test set contains near-copies of
  training frames;
- biases a classifier towards whatever the background is doing in that second.

A cheap guard is a frame-difference filter you can write in four lines:

```python
import numpy as np

def mean_abs_diff(a, b):
    return float(np.abs(a.astype(np.int16) - b.astype(np.int16)).mean()) / 255.0

kept, last = [], None
for index, stamp, frame in video.iter_frames(path):
    if last is None or mean_abs_diff(frame, last) > 0.02:
        kept.append(index)
        last = frame
```

Threshold 0.02 (2% of full scale, averaged over pixels) at 640x360 removes static footage and
keeps real motion; it is a starting point, not a law. Verify it on a contact sheet before
trusting the count: a threshold that is slightly too high deletes the slow vehicles first.

Even with deduplication, **splitting by frame is wrong** - the next section explains why and
what to do instead.

## The dataset layout this section uses

```
data/video/
  street_day.mp4            the clips, byte-identical on every regeneration
  street_day.json           manifest: per-frame boxes, track ids, crossings, checksums
  annotations/
    coco/instances_train.json
    yolo/{images,labels}/
    voc/Annotations/*.xml
  dataset_card.md           provenance, licence, counts, known limitations
```

The manifest is the source of truth; COCO, YOLO, and VOC exports are derived from it by
`video_core.labels`. Writing annotations in three formats is not busywork - it is the fastest
way to internalise the coordinate conventions, and Module 4 makes you convert between them by
hand once.

Every clip record carries a checksum, so a regenerated file is provably the same bytes:

```python
manifest["videos"]["street_day"]["sha256"] == video.checksum(path)
```

## Splitting: by video, never by frame

Frames from one clip share a camera, a lighting condition, a background, and often the same
vehicles seconds apart. A random frame split therefore puts near-copies of the same scene on
both sides.

The section's rule is one line, enforced by a check:

```python
splits = labels.split_by_video(records, fractions=(0.6, 0.2, 0.2), seed=0)
report = labels.video_leakage(splits)          # {'leaky': False, 'videos': {...}}
assert not report["leaky"]
```

`split_by_video` groups records by their `video` key **before** splitting, and
`video_leakage` verifies that no video appears in two splits and reports the counts. There is
also `labels.frame_split_leakage` for the case you want to *demonstrate* the bug - the tests
in `tests/test_video_ai.py` use it to prove the detector catches it.

With seven clips the split is by scene, and the test videos are deliberately the hard ones:

| Split | Clips | Why |
| --- | --- | --- |
| train | `street_day`, `street_dusk` | two lighting conditions, both easy-ish |
| val | `street_quiet` | used for threshold selection only - never for a reported score |
| test | `street_night`, `street_rain`, `street_shake`, `street_crowd` | four distinct distribution shifts |

The consequence is that test scores are pessimistic. That is the point: Lab 2's pretrained
detector scores 0.048 mAP on the day clip (in-domain-ish) and 0.000 on the night clip, and the
second number is the one that predicts deployment.

## Costs, and what a "small" dataset means here

| Representation | Size for 7 clips x 60 frames | Notes |
| --- | --- | --- |
| Video on disk | 4.2 MB | what the section ships (regenerated, Git-ignored) |
| Decoded frames in memory | 7 x 60 x 360 x 640 x 3 = 290 MB | why you stream, not load |
| Frames as JPEGs | ~11 MB | convenient for labelling tools |
| Frames as PNGs | ~40 MB | lossless, wasteful for synthetic scenes |
| Detector input tensors | 60 x 3 x 144 x 256 x 4 B = 26 MB per clip | float32 |

Streaming is the default for a reason: materialising 290 MB of frames to use 26 MB of tensors
is how a laptop runs out of memory at frame 4,000.

## Checks

- [ ] You can compute the stride and the actual interval for 25 fps / 0.1 s without a calculator.
- [ ] You predicted Lab 1's extraction count before running it, and were right.
- [ ] You can explain why a random frame split inflates accuracy.
- [ ] You have run `video_leakage` on a split you built and read the counts.
- [ ] You know how many frames a 1080p 30-minute clip would occupy in memory, and why that
      number decides your architecture.
