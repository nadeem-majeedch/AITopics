# VD07 - Object tracking and track IDs {#vd07}

**Section path:** [Overview](index.md) · **Module 7** · [Lab 3](labs/lab-3-tracking-and-counting.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 5 hours: 2 h reading, 3 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | [VD06](vd06-detection-on-frames.md), [F13](../index.md#foundation-sequence) |
| **You will produce** | A tracked video, a MOTA table, and a written explanation of one identity failure you caused |

## Why this module exists

A detector gives you boxes. A count needs *objects*, and "object" means "the same thing across
frames". Every subsequent quantity in this section - crossings, flow, speed, dwell time - is
computed per identity. When identity is wrong, every one of those numbers is wrong in a way that
looks plausible.

This is the module where the section's numbers stop being flattering. On the clean clip, the
tracker is the most accurate component in the pipeline. On the crowd clip it is worse than
useless, and the reason is instructive.

## The association problem

At frame *t* you have a set of detections and a set of existing tracks. You must decide which
detection continues which track. Three things make it hard:

1. **The detector is inconsistent.** A vehicle's box can vanish for two frames and return 8
   pixels to the right.
2. **Objects cross.** Two vehicles overlap; after the overlap, which box is which?
3. **New objects appear.** A vehicle enters frame; it must get a new ID, not steal an old one.

A tracker is a rule for that decision plus a memory of what happened before. The section
implements the classic, explainable version: **IoU association with Hungarian matching,
constant-velocity prediction, a confirmation delay, and a coasting allowance.**

## The sections's tracker, piece by piece

```python
from video_core.tracking import IoUTracker, track_detections

tracks = track_detections(detection_records, iou_threshold=0.30, max_age=6, min_hits=2)
```

`track_detections` wraps `IoUTracker.update` in a loop and returns, for every frame, the list
of confirmed tracks with their `track_id`, `box`, `label`, `hits`, and `trail`.

| Parameter | Value here | What it buys | What it costs when wrong |
| --- | --- | --- | --- |
| `iou_threshold` | 0.30 | matching tolerance per frame | too high → new ID on every jitter; too low → IDs swap on crossing |
| `max_age` | 6 frames | survives a 0.6 s occlusion | too high → a departed car's track steals the next car |
| `min_hits` | 2 | suppresses one-frame false positives | too high → fast vehicles never confirm before leaving frame |
| `velocity_smoothing` | 0.6 | predicts boxes forward before matching | too high → prediction overshoots on a turn |

### Velocity prediction, and why it matters

Matching against the *predicted* box instead of the last box is what lets a fast vehicle keep
its ID after the detector misses a frame:

```python
class Track:
    def predicted_box(self):
        dx, dy = self.velocity
        return [self.box[0] + dx, self.box[1] + dy, self.box[2] + dx, self.box[3] + dy]
```

At 10 fps a vehicle moving 12 px/frame is 24 pixels away after two missed frames. With 40-pixel
boxes, IoU between the last box and the new detection has already fallen below 0.3 - so without
prediction the track dies exactly when occlusion is most likely.

### Class-agnostic matching, label by vote

The section matches on geometry only, ignoring the detector's class, then settles the label by
majority vote over the track's lifetime:

```python
# from IoUTracker.update: cost is 1 - IoU against the predicted box, classes ignored
```

Why: the measured detector flips `car`/`truck` on consecutive frames of the same vehicle
(Module 6's class histogram shows 73 `truck` detections). If matching were class-aware, every
flip would end one track and start another - inflating the track count and therefore the
crossing count. Voting is both more stable and closer to what production trackers do.

### The dedupe step

Per-class NMS can still emit two overlapping boxes of different classes for one vehicle. Left
alone, that is two tracks for one car, and two crossings. `track_detections` applies a final
pass at a stricter IoU:

```python
def _dedupe(tracks, *, iou_threshold=0.60):
    """Keep the highest-scoring box when two confirmed tracks describe the same object."""
```

0.60 rather than the per-class NMS 0.30 because the two boxes are usually offset, not
identical: they describe the same vehicle with different hypotheses about its extent.

## Measuring identity: MOTA, IDSW, fragments

MOTA (multiple object tracking accuracy) compares the number of errors to the number of
ground-truth objects:

\[
\text{MOTA} = 1 - \frac{\text{FN} + \text{FP} + \text{IDSW}}{\text{GT}}
\]

This section computes it in `metrics.tracking_report`, along with:

- **IDSW** - the number of times a ground-truth object's assigned ID changes between
  consecutive frames it appears in.
- **Fragments** - the number of times an object's track is interrupted and resumed.
- **FP / FN** - detection-level false positives and negatives, after matching.

MOTA can be negative. That is not a bug; it means the tracker produced more errors than there
were objects, which is exactly what happens on hard footage.

The measured table from Lab 3:

| Video | vehicles | predicted tracks | IDSW | MOTA | counted | expected |
| --- | --- | --- | --- | --- | --- | --- |
| `street_day` | 6 | 14 | 5 | **0.658** | 6 | 6 |
| `street_crowd` | 8 | 18 | 8 | **-0.381** | 5 | 8 |
| `street_shake` | 6 | 15 | 3 | **-0.019** | 3 | 6 |

Read the columns together, not separately:

- **14 tracks for 6 vehicles** on the clean clip. The tracker is not creating identities from
  nothing - the detector drops boxes during overlaps, and each dropout that outlasts `max_age`
  becomes a new ID. MOTA is still positive because most frames are matched.
- **Crowd: MOTA -0.381.** 18 tracks, 8 switches, and only 5 of 8 vehicles counted. The failure
  is not detection - it is association. Vehicles overlap for many frames, and after the overlap
  the tracker hands the wrong ID to the wrong box.
- **Shake: -0.019.** The camera moves, so *every* box moves, and IoU association sees apparent
  motion that is not the objects'. Only 3 of 6 crossings survive.

Each of those is a different bug with a different fix, and no single number would have told you
which one you had.

## Tuning `max_age`, with the curve

Lab 3 sweeps it on the crowd clip:

| `max_age` | MOTA | IDSW | unique tracks | count error |
| --- | --- | --- | --- | --- |
| 2 | -0.263 | 8 | 33 | 11 |
| 6 | -0.381 | 8 | 18 | 11 |
| 12 | -0.444 | 6 | 17 | 11 |
| 20 | -0.492 | 6 | 16 | 11 |

The instructive part is what does *not* change: the count error stays at 11 for every setting.
Tuning `max_age` reduces the track count (33 → 16) and the switch count (8 → 6), and makes MOTA
*worse* because long-lived stale tracks generate false positives. There is no setting at which
this tracker counts the crowd correctly, because the problem is not the parameter - it is that
IoU alone cannot separate overlapping objects.

That is the honest finding, and writing it down is worth more than a tuned number: **a tracker
tuned on the easy clip gains nothing on the hard one, and you should report both.**

## What a better tracker would need

| Failure | What is missing | Cheap fix | Proper fix |
| --- | --- | --- | --- |
| Occlusion → new ID | appearance memory | longer `max_age` | appearance embedding + IoU cost |
| Crossing → swapped IDs | motion model | Kalman filter | motion + appearance, or a learned matcher |
| Camera shake → everything moves | global motion | none | stabilise, or subtract background motion |
| One vehicle, two IDs | box hypothesis merge | `_dedupe` | NMS across classes in the detector |

This section implements the cheap column, because it is explainable and it fails in ways you can
see. A Kalman filter (as in SORT/DeepSORT) is the natural next step and is a reasonable
extension exercise in Lab 3.

## From tracks to a review video

```python
from video_core import video
from video_core.tracking import track_detections

tracks = track_detections(records, max_age=6)
history: dict[int, list[tuple[float, float]]] = {}      # track_id -> recent centres
with video.VideoWriter("outputs/tracked.mp4", fps=10, size=(640, 360)) as w:
    for frame_index, frame_tracks in enumerate(tracks):
        frame = video.frame_at("data/video/street_day.mp4", frame_index)
        boxes = [t["box"] for t in frame_tracks]
        captions = [f"id{t['track_id']} {t['class']}" for t in frame_tracks]
        for t in frame_tracks:                          # keep the last 20 centres per id
            x1, y1, x2, y2 = t["box"]
            trail = history.setdefault(t["track_id"], [])
            trail.append(((x1 + x2) / 2, (y1 + y2) / 2))
            del trail[:-20]
        drawn = video.annotate_frame(frame, boxes, captions)
        w.write(video.draw_trails(drawn, list(history.values())))
```

Watch for two specific things, both visible only in motion: an ID that changes while the
vehicle is still in frame (a real switch), and two boxes on one vehicle (a duplicate track).

## Checks

- [ ] You can write the MOTA formula from memory and explain why it can be negative.
- [ ] You can explain what `max_age` trades against `min_hits`.
- [ ] You can say why matching ignores class, and how the label is decided instead.
- [ ] You can look at the crowd clip's numbers and say which component failed.
- [ ] You have found one identity error in your own tracked video and described its cause.
