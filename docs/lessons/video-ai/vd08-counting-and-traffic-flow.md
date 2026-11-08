# VD08 - Counting vehicles and analysing traffic flow {#vd08}

**Section path:** [Overview](index.md) · **Module 8** · [Lab 3](labs/lab-3-tracking-and-counting.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 1.5 h reading, 2.5 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | [VD07](vd07-tracking-and-track-ids.md) |
| **You will produce** | A per-class, per-direction count with a measured error, and a flow number labelled as an extrapolation |

## Why this module exists

Counting is the task most video analytics is actually bought for, and the one where a pipeline
most often reports a confident wrong number. The failure is rarely arithmetic. It is one of
three things: the line is in the wrong place, an identity was duplicated, or a per-hour figure
was extrapolated from eight seconds of video without saying so.

This module covers the tripwire design, the exact crossing rule, the arithmetic of flow, and
the honesty requirements.

## Counting is a tracker question, not a detector question

A detector says "vehicle here". A count says "one more vehicle has passed". Those differ by
identity, which is Module 7's subject:

- One vehicle visible for 40 frames is 40 detections and **one** count.
- One vehicle that loses its ID halfway is two tracks and **two** counts.
- Two vehicles overlapping for 10 frames may produce three tracks and **three** counts.

Lab 3 measures exactly that progression: 6 vehicles, 14 predicted tracks, and a correct total
of 6 crossings - because the counter records only the *first* crossing per track, and because
the duplicates happen away from the line. In the crowd clip the same logic gives 5 of 8,
because the duplicates and the missed detections happen *at* the line.

## The tripwire, defined precisely

A counting line is two points. A track crosses when its anchor point changes side. The side
test is a signed area:

\[
s(p) = (y_2 - y_1)(p_x - x_1) - (x_2 - x_1)(p_y - y_1)
\]

```python
from video_core.counting import LineCounter

counter = LineCounter((320, 0), (320, 360))     # vertical line down the middle
print(counter.side((400, 180)))                 # positive: right of a top-to-bottom line
print(counter.side((200, 180)))                 # negative
```

Two conventions to fix before you use it, and to write into your report:

1. **Orientation.** The order of the two points defines which side is positive. A vertical line
   specified top → bottom makes the right of the frame positive. Swap the points and every
   direction flips - the total stays right, the two direction columns swap.
2. **Anchor.** Default is the bottom-centre of the box: the road-contact point, which is the
   point that actually crosses a painted line. The alternative is the box centre, which shifts
   every event by half a vehicle length and changes the count for a line near the frame edge.

```python
LineCounter((320, 0), (320, 360), anchor="center")   # the other convention
```

### The crossing rule, including the degenerate case

A naive rule is `previous_side != current_side`. It double-counts: a vehicle that jitters across
the line and back produces two events. The section's rule is a strict sign change, with an
explicit guard for the point that sits exactly on the line:

```python
value = self.side(point)
if value == 0.0:
    continue                      # no side to record; keep the last real one
previous = self.sides.get(tid)
self.sides[tid] = value
if previous is None or tid in self.counted:
    continue
if (previous < 0 <= value) or (previous > 0 >= value):
    direction = "positive" if value > 0 else "negative"
```

Three properties follow, and all three are tested in `tests/test_video_ai.py`:

- **Once per track.** `self.counted` makes a second crossing by the same ID impossible.
- **Direction from the new side**, not from the old one - the side the vehicle is now on.
- **A track that pauses on the line** records nothing while `value == 0`, then counts once when
  it leaves. Without the guard, that pause produced an event with direction `negative` from a
  position that had no side at all - a real bug this section shipped and then found, which is
  why the guard has a comment explaining it.

## Reading a count report

```python
from video_core.counting import run_counter, flow_summary

line = synth.counting_line(cfg)            # {'p1': [352.0, 135.9], 'p2': [352.0, 342.0], ...}
result = run_counter(tracked_frames, line["p1"], line["p2"])
print(result["counts"])     # {'truck:positive': 3, 'motorcycle:negative': 1, ...}
print(result["total"])      # 6
print(result["event_frames"])   # which frame each crossing happened in
```

`result["events"]` carries `track_id`, `class`, `frame`, `direction`, and the anchor point - the
audit trail. If a number looks wrong, the events tell you which track produced it, and the
tracked video shows you that track.

The measured report for `street_day`:

| class:direction | expected | counted | error |
| --- | --- | --- | --- |
| car:negative | 1 | 1 | 0 |
| motorcycle:negative | 1 | 1 | 0 |
| motorcycle:positive | 1 | 1 | 0 |
| truck:negative | 1 | 0 | -1 |
| truck:positive | 2 | 3 | +1 |
| **total** | **6** | **6** | **0** |

The total is exactly right and two cells are wrong: a vehicle counted in the right place but
filed under the wrong class - a car called a truck, as Module 6 predicted from the detector's
class histogram. This is the most under-reported failure in real deployments, because a
dashboard that shows "6 vehicles" looks perfect while its breakdown is wrong.

Report both numbers. The section's Lab 3 has two separate checks for exactly this reason:
*total crossings match* and *per-class attribution is within two*.

## Flow: units, and what may be extrapolated

```python
flow = flow_summary(result["counts"], duration_s=6.0, lanes=1)
# {'total': 6, 'rate_per_s': 1.0, 'per_hour': 3600.0, 'per_lane_per_hour': 3600.0,
#  'extrapolated': True, 'note': 'per-hour figures extrapolate a few seconds of video; ...'}
```

1 vehicle per second becomes 3,600 vehicles per hour. The arithmetic is right and the claim is
absurd: a six-second clip cannot estimate an hourly rate, because traffic is not stationary over
an hour. The section's rule is that the per-hour number is always returned with
`extrapolated: True` and a note, and always printed next to the duration it came from.

For real reporting you need at least:

- a window long enough to include the variation you care about (typically 15+ minutes for a
  peak-hour estimate);
- an explicit statement that flow is per direction and per lane, and how lanes were counted;
- a confidence interval, or at minimum the count and the window so the reader can compute one.

## Speed, and the number you must not invent

`speed_estimates` fits a least-squares line through each track's centres and multiplies by fps:

```python
speeds = speed_estimates(tracked_frames, fps=10.0)
print(speeds["tracks"][0])       # {'track_id': 1, 'speed_px_per_s': 25.52, 'frames': 44}
```

Lab 3 measures a median of 25.52 px/s across 14 tracks. That is a **pixel** speed. Converting to
km/h requires `pixels_per_metre`, which requires a calibrated camera: a known road marking, a
known lane width, or a homography to the ground plane. Without calibration the metres column is
omitted rather than guessed:

```python
speed_estimates(tracked_frames, fps=10.0, pixels_per_metre=18.0)   # only if you know 18
```

A speed in km/h from an uncalibrated camera is the most confidently wrong number in traffic
analytics, because perspective means the scale changes within the frame: a vehicle near the
horizon moves 6 px where one near the camera moves 40 px, at the same real speed. If your line
and your speed must both be right, calibrate - Module 14 covers what that involves.

## Choosing the line

Three rules that prevent most counting mistakes, all of which you can check against Lab 3's
failure cases:

1. **Put the line where vehicles are separated**, not where they overlap. A line across a
   congested junction counts tracks, not vehicles.
2. **Keep the line away from the frame edges.** A vehicle entering the frame may be detected
   late and its first side ambiguous; a line near the edge turns that into a missed count.
3. **Give the line a margin at both ends.** Vehicles passing outside the line's extent are
   not counted, which is the behaviour you want for a single lane - but must document if your
   camera sees several.

## Counting with occlusion, measured

| Scene | Vehicles | Predicted tracks | Counted | Error |
| --- | --- | --- | --- | --- |
| clean day | 6 | 14 | 6 | 0 |
| crowd | 8 | 18 | 5 | -3 |
| camera shake | 6 | 15 | 3 | -3 |

More tracks and *fewer* counts is the signature of fragmentation at the line: a vehicle's track
ends before it reaches the tripwire, and the new track starts on the far side, so no sign change
is ever observed. That is a specific, diagnosable failure - look at `event_frames` and the
tracked video, and you will find vehicles that were never counted because their ID changed
exactly at the line.

## Checks

- [ ] You can state the side test and say what swapping the two points does to a report.
- [ ] You can explain why the counter records the *first* crossing per track.
- [ ] You can describe the two ways a correct total can hide wrong per-class numbers.
- [ ] You can say what a per-hour figure from a 6-second clip is, and is not.
- [ ] You can name the calibration input needed before quoting km/h.
- [ ] You can explain "more tracks, fewer counts" without notes.
