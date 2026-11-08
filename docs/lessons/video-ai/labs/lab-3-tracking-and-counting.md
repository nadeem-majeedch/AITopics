# Lab 3 - Detect, track, and count vehicles crossing a line

**Section path:** [Overview](../index.md) · Modules [VD07](../vd07-tracking-and-track-ids.md), [VD08](../vd08-counting-and-traffic-flow.md) · **Lab 3** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 15% of the section assessment |
| **Time** | 4 hours |
| **Hardware** | CPU-only; ~20 s for the full run including three scenes |
| **Code** | `projects/video-ai/lab3_tracking_and_counting.py` |
| **Prerequisites** | [Lab 2](lab-2-object-detection.md), VD07, VD08 |

## Objectives

1. Turn per-frame boxes into identities that survive occlusion, using IoU association with
   velocity prediction, confirmation delay, and a coasting allowance.
2. Count line crossings per class and per direction, once per track.
3. Measure tracking quality with MOTA, ID switches, fragments, and track count versus real
   vehicle count.
4. Separate **total** count error from **per-class** attribution error.
5. Sweep `max_age` and explain what changes and, more importantly, what does not.
6. Review a tracked video and explain one identity failure by name.

## Prerequisites

- Lab 2 complete.
- TinyDetector cache present (`outputs/cache/tiny_w24_e30_s2_seed0.pt`); the lab trains it if
  missing (about 20 s).
- Ground truth with track IDs in `data/video/*.json`, and counting expectations from
  `synth.counting_line`.

## Procedure

### 1. Run the pipeline

```bash
cd projects/video-ai
python lab3_tracking_and_counting.py
```

| Flag | Meaning |
| --- | --- |
| `--video street_crowd` | pipeline on one clip |
| `--max-age 12` | tracker coasting allowance, in frames |
| `--limit 30` | stop after N frames |
| `--selftest` | Full clip, checks only, no annotated video |

### 2. Read the three tables in order

**Pipeline (quality):** mAP 0.918, MOTA 0.658, 5 ID switches, 6 fragments, 14 tracks for 6
vehicles. Note that mAP is high while identity is only fair - the detector is the strong part.

**Counting (the product):** 6 of 6 total, but two cells wrong (a truck counted positive instead
of a car negative). The lab prints the note:

```
note: the total is right but some vehicles are filed under the wrong class or direction -
      a dashboard would show a correct total and a wrong breakdown.
```

**Limitations (three scenes):** the table that matters.

| Scene | Vehicles | Tracks | IDSW | MOTA | Counted |
| --- | --- | --- | --- | --- | --- |
| `street_day` | 6 | 14 | 5 | 0.658 | 6 |
| `street_crowd` | 8 | 18 | 8 | -0.381 | 5 |
| `street_shake` | 6 | 15 | 3 | -0.019 | 3 |

### 3. Sweep `max_age`

The lab runs 2, 6, 12, and 20 on the crowd scene:

| `max_age` | MOTA | IDSW | Tracks | Count error |
| --- | --- | --- | --- | --- |
| 2 | -0.263 | 8 | 33 | 11 |
| 6 | -0.381 | 8 | 18 | 11 |
| 12 | -0.444 | 6 | 17 | 11 |
| 20 | -0.492 | 6 | 16 | 11 |

Write down what does **not** change. The count error is 11 at every setting: this tracker cannot
count the crowd correctly, and the parameter is not the reason. A lab report that says "we tuned
`max_age` and improved MOTA" has misread this table.

### 4. Watch the tracked video

```
outputs/tracked_street_day.mp4
```

Look for an ID that changes while the vehicle is still visible, and a frame where one vehicle
carries two boxes. Both appear in this clip; find one of each and note the frame.

### 5. Verify the counting rule

```python
from video_core.counting import LineCounter

c = LineCounter((100, 0), (100, 200))
print(c.side((150, 100)) > 0, c.side((50, 100)) < 0)     # True True
```

Then check the once-per-track rule and the on-the-line guard by feeding a track that pauses
exactly on the line:

```python
c = LineCounter((100, 0), (100, 200))
for f, x in enumerate([80, 95, 100, 105, 120]):
    c.update([{"track_id": 1, "box": [x - 10, 150, x + 10, 190], "label": 0, "class": "car"}], f)
print(len(c.events))   # 1 - not 0, not 2
```

## Expected output

```
=== pipeline on street_day
  frames     : 60
  detection  : mAP@0.5 0.918  precision 0.931  recall 0.897
  tracking   : MOTA 0.658  ID switches 5  fragments 6  FP 81  FN 37
  identities : 14 predicted tracks for 6 real vehicles

=== counting
  class:direction      expected  counted  error
  car:negative         1         1        0
  motorcycle:negative  1         1        0
  motorcycle:positive  1         1        0
  truck:negative       1         0        -1
  truck:positive       2         3        1
  total      : counted 6 of 6 (cell error 2, exact False)
  flow       : 1.0 vehicles/s over 6.0 s -> 3600.0 per hour (extrapolated, not a forecast)
  speed      : median 25.52 px/s across 14 tracks (no metres: the camera is uncalibrated)

  [PASS] detector found most vehicles in-domain  (mAP 0.918)
  [PASS] tracking beats 'no tracker' (MOTA > 0)  (MOTA 0.658)
  [PASS] total crossings match ground truth  (6 vs 6)
  [PASS] per-class attribution is within two crossings  (cell error 2)
  [PASS] every frame of the video was processed
  [PASS] tracked video is readable  (tracked_street_day.mp4)
  [PASS] crowd scene is harder than the clean scene  (8 vs 5 IDs)

  7/7 checks passed
```

## Evaluation

| Criterion | Marks | Evidence |
| --- | --- | --- |
| Full run, 7/7 checks | 3 | output |
| Three-scene table reproduced | 3 | with track counts, not just MOTA |
| Total vs per-cell count error explained | 3 | 6/6 with cell error 2 |
| `max_age` sweep interpreted, including the invariant | 3 | "count error stayed at 11" |
| One identity failure described from the video | 3 | frame index + cause |

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `MOTA` is very negative everywhere | boxes are being matched to the wrong ground truth | check `LABEL_TO_INDEX` and the IoU threshold (0.5 for scoring) |
| Counted 0 | line placed outside the vehicles' path | use `synth.counting_line(cfg)` |
| Duplicate tracks everywhere | NMS too permissive for this data | check `_dedupe` ran; verify score threshold |
| Count error doubles | one vehicle crossed twice because its ID split at the line | look at `event_frames`; try larger `max_age` |
| `--max-age 2` gives 33 tracks | expected: occlusion outlives the allowance | that row is the point of the sweep |
| Speed in km/h missing | no calibration | pass `pixels_per_metre`, or accept px/s |

## Extensions

1. **Appearance gating.** Add a colour histogram to the association cost and re-run the crowd
   scene. Report MOTA and count error before/after. Does it help where IoU alone failed?
2. **Kalman filter.** Replace the constant-velocity prediction with a 2D Kalman filter
   (position + velocity). Measure on `street_shake`.
3. **Two lines.** Count vehicles entering and leaving a zone (region counting, not tripwire).
   Report the difference between entries and exits and explain why it need not be zero.
4. **Calibration.** Assume a 3.5 m lane and measure `pixels_per_metre` at the line, then report
   speeds in km/h with the assumption written down.
5. **Cross-class NMS.** Move the dedupe step into the detector and re-measure the track count.

## Submit

- Full output plus `outputs/lab3_tracking.json`.
- The three-scene table and the `max_age` sweep, with your interpretation of the invariant.
- One identity failure from the tracked video: frame, vehicle, cause, and the parameter that
  would (or would not) fix it.
- The counting report with total and cell error, and one sentence on what a dashboard would get
  wrong.
