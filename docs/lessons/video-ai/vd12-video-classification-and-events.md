# VD12 - Video classification and event detection {#vd12}

**Section path:** [Overview](index.md) · **Module 12** · [Lab 6](labs/lab-6-action-recognition.md) · [Lab 7](labs/lab-7-integrated-analytics.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 1.5 h reading, 2.5 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | [VD11](vd11-action-recognition.md) |
| **You will produce** | A clip-level classifier and an event rule, each with its own metric and its own false-alarm rate |

## Why this module exists

Two different products are routinely confused:

- **Video classification**: "what is this clip about?" One label for a whole window.
- **Event detection**: "when did X happen?" A start time, an end time, and a confidence.

They need different data, different metrics, and different failure handling. A classifier with
95% clip accuracy tells you almost nothing about whether an event detector will fire at the
right moment - and the second is what most deployments actually need.

## Video classification

The simplest useful form: take a window of frames, produce one label.

```python
from video_core.actions import TemporalClassifier, predict_temporal

labels = predict_temporal(model, clips)      # (N,) - one label per clip
report = metrics.classification_report(y_test, labels, class_names)
```

Measured in Lab 6: 0.813 clip accuracy with a CNN+GRU over 8 frames, versus 0.507 for
majority-voted per-frame predictions.

Three design choices decide the result more than the architecture does:

| Choice | Effect | Here |
| --- | --- | --- |
| Window length | must cover the event; too long dilutes it | 8 frames (0.7 s at 10 fps) |
| Window stride | overlap trades samples for correlated data | 50% in training |
| Aggregation | vote, mean logits, or learned head | learned GRU (Lab 6) |

A classifier trained on non-overlapping windows and evaluated on sliding windows sees a
distribution shift it was never trained for. If your product slides a window, train on sliding
windows.

## Event detection

An event is a time interval with a label. For the section's traffic pipeline the event is
"a vehicle crossed the line", computed by the counter:

```python
from video_core.counting import run_counter

events = run_counter(tracks, line["p1"], line["p2"])["events"]
# [{'track_id': 1, 'class': 'truck', 'frame': 8, 'direction': 'positive', ...}, ...]
```

That is an event detector whose "model" is a geometric rule. It is worth studying as one,
because the operational questions are identical to a learned detector's:

- **Did it fire at the right time?** Frame 8 versus ground-truth frame 8 - a timing error of 0.
- **Did it fire when nothing happened?** A false alarm - measured as extra events.
- **Did it miss a real event?** A miss - measured as missing events.
- **Did it fire twice for one event?** A duplicate - the reason the counter records only the
  first crossing per track.

### Event metrics: point events versus intervals

| Event type | Matching rule | Metrics |
| --- | --- | --- |
| **Point** (crossing, trigger) | within ±N frames of truth | precision, recall, F1, mean timing error |
| **Interval** (fight, stopped vehicle) | temporal IoU ≥ threshold | precision, recall, mean IoU, latency to onset |

For point events, a tolerance window is unavoidable: a crossing detected one frame late is not
an error, and the tolerance must be stated. The section's line counter is frame-exact against
synthetic truth, so its tolerance is 0 - which is a property of the data, not of the method.
On real footage a ±5-frame tolerance at 10 fps is a reasonable starting point.

For interval events, temporal IoU is the honest measure:

\[
\text{tIoU} = \frac{|A \cap B|}{|A \cup B|} \quad \text{in frames}
\]

and a match requires `tIoU ≥ 0.3-0.5` depending on how much boundary error the application
tolerates. Reporting only "did it fire" hides a detector that fires ten seconds early.

### Debouncing, and why it is not cheating

Real event detectors fire repeatedly for one event - a stopped vehicle detected as "stopped"
every frame, a crossing re-triggered by a jittering box. A cooldown or hysteresis rule
("suppress the same label within N frames of the last event") is standard, and it is legitimate
**as long as it is reported**:

- State the cooldown window, in frames and in seconds.
- Report the metrics with and without it, or state plainly that the cooldown is part of the
  system being evaluated.
- Do not tune the cooldown on the test set. It is a hyperparameter like any other.

The line counter's one-event-per-track rule is exactly this, implemented structurally rather
than as a post-filter, which is why it is easier to reason about.

## From clip labels to events

The bridge between the two tasks is a sliding window with a decision rule:

```python
# pseudo-code for turning a clip classifier into an event detector
for start in range(0, n_frames - window + 1, step):
    clip = frames[start:start + window]
    label, score = classify(clip)
    if label == target and score >= threshold:
        emit_event(start_frame=start, frame=start + window, score=score)
```

Every parameter in that loop is a decision with a measurable consequence:

| Parameter | Too small | Too large |
| --- | --- | --- |
| `window` | cannot see the event | dilutes it; late detection |
| `step` | compute cost, duplicate events | misses events between windows |
| `threshold` | false alarms | misses |

The latency of the resulting detector is `window + step` frames, by construction. If your
product promises a 1-second alert and your window is 8 frames at 10 fps, you have already spent
0.8 s before the classifier runs.

## Evaluation that matches the product

| Product claim | Metric that tests it | Metric that does not |
| --- | --- | --- |
| "classifies clips correctly" | clip accuracy, per-class F1 | per-frame accuracy |
| "detects crossings" | event precision/recall, timing error | mAP of the detector |
| "alerts within 1 s" | latency distribution (median, p95) | throughput |
| "does not spam" | false alarms per hour | precision on a balanced test set |

That last row deserves emphasis: precision on a balanced test set is a poor proxy for false
alarms per hour in deployment, where events are rare. A detector with 0.9 precision on a test set
that is 50% events will produce a flood of false alarms on footage that is 1% events. Compute
the base-rate arithmetic explicitly in your report - it is the single most common reason a
working model fails in production.

## Lab 7's integrated pipeline as an event system

Lab 7 wires detection, tracking, counting, and reporting into one configurable program, with
exit codes that distinguish outcomes:

```
0  the run completed and a summary was written (whether or not anything crossed)
2  the input video could not be used (missing, truncated, not decodable)
3  the configuration was invalid
```

The measured run: 60 frames in about 1.5 s (~22 ms/frame, ~45 fps), 347 detections, 6
crossings.
The exit codes matter for the same reason the error paths do: an event system that reports
"no events" for an unreadable file will look like calm traffic during an outage. Lab 7 feeds it
a missing path, a truncated MP4, an HTML page named `.mp4`, an empty file, and video bytes with a
`.txt` name; each is rejected with a named reason and exit 2, before any output is written.

## Checks

- [ ] You can state the difference between clip classification and event detection in one line each.
- [ ] You can name the metric that tests timing, and the one that does not.
- [ ] You can explain why a debounce rule must be reported, not hidden.
- [ ] You can compute the latency a sliding-window detector adds.
- [ ] You can do the base-rate arithmetic for 0.9 precision on 1%-event footage.
