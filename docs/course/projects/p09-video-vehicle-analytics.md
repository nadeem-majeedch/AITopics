# P09 - Video analytics for vehicle detection, counting, and tracking

```markdown
**Projects:** [Index](index.md) · [Completion checklist](completion-checklist.md) · [Report template](report-template.md)
```

| | |
| --- | --- |
| **Difficulty** | Advanced |
| **Effort** | 55-70 hours |
| **Hardware** | CPU for the course clips (short, low resolution); a GPU speeds detection |
| **Prerequisites** | [VD02 reading and writing video](../../lessons/video-ai/vd02-reading-and-writing.md), [VD03 frame extraction](../../lessons/video-ai/vd03-frame-extraction-and-datasets.md), [VD06 detection on frames](../../lessons/video-ai/vd06-detection-on-frames.md), [VD07 tracking](../../lessons/video-ai/vd07-tracking-and-track-ids.md), [VD08 counting](../../lessons/video-ai/vd08-counting-and-traffic-flow.md), [VD14 evaluation](../../lessons/video-ai/vd14-evaluation-and-deployment.md), [VD15 responsible analytics](../../lessons/video-ai/vd15-responsible-video-analytics.md) |
| **Builds on** | Video AI labs 1, 2, 3, and 7 |
| **Hard constraint** | No face recognition, no person re-identification, no covert use. Read the governance page first. |

## 1. Problem statement and motivation

A council, campus, or site manager wants to know how many vehicles use an entrance
and when. Manual counts are expensive and rare. A camera plus a detector plus a
tracker can produce counts per direction per hour, provided the system handles
occlusion, parked cars, and the same vehicle crossing a line twice.

The engineering is in the counting logic and the evaluation, not in the detector.
A detector with 0.8 mAP can produce counts that are off by 40% if the line crossing
logic double-counts, and nobody notices without ground truth.

**Decision supported:** hourly traffic counts and peak identification. Not
enforcement, not identification of drivers or owners.

## 2. Intended learning outcomes

1. Read video frames deterministically and extract a clip manifest with timestamps.
2. Run detection per frame and track objects with stable ids, handling gaps.
3. Implement line or zone crossing logic that counts each object once.
4. Build ground truth for a short clip and compute counting error, MOTA, and IDF1.
5. Analyse failure conditions: night, rain, occlusion, camera shake, parked vehicles.
6. Measure throughput (FPS) and state the trade-off against accuracy.
7. Apply privacy controls: no faces stored, plates blurred, retention documented.

## 3. Difficulty and prerequisites

**Level:** Advanced. 55-70 hours: 10 video pipeline, 12 detection and tracking, 10
counting, 14 ground truth and evaluation, 8 robustness, 10 packaging and writing.

Requires VD06-VD08 and VD14. Ground truth annotation is the bottleneck; budget for
it honestly.

## 4. Scope and out-of-scope features

**In scope**

- One to four fixed-camera clips of public or consented footage, 30-120 seconds each.
- Vehicle detection (car, truck, bus, motorcycle) on frames.
- Multi-object tracking with ids and a documented association method.
- Directional counting across one or two virtual lines.
- Ground truth for at least one clip, annotated by you, with an annotation guide.
- Counting and tracking metrics, plus a condition breakdown.
- Privacy: blur faces and plates before writing any output image.

**Out of scope**

- Speed estimation or enforcement. Camera calibration for speed is a different
  project and is legally sensitive.
- Identifying vehicles (plate recognition) or people.
- Multi-camera re-identification.
- Live streaming infrastructure.
- Any deployment on real public space without authorisation.

## 5. Dataset options, licences, and preparation

| Option | Source | Licence | Notes |
| --- | --- | --- | --- |
| A (default, offline) | `projects/video-ai/data/video/street_*.mp4` with annotations in `annotations/` | CC0-1.0, generated | Seven synthetic clips: day, dusk, night, rain, shake, crowd, quiet |
| B | Public traffic footage | Record the exact licence; many are "research only" | Check whether derivative output may be published |
| C | Your own recording | Consent or private-property permission; no faces if avoidable | Keep it short; delete raw footage when done unless retention is agreed |

**Preparation**

1. Verify the clips: duration, fps, resolution, frame count. Record them in a
   manifest.
2. Watch each clip once and write down the conditions you see. This becomes your
   condition labels.
3. Choose one clip as the evaluation clip and annotate it: every vehicle, every
   frame or every fifth frame, with a consistent id per vehicle across frames.
4. Write the annotation guide: what counts as a vehicle, how to handle a vehicle
   entering or leaving frame, what to do with parked cars, minimum visible size.
5. Annotate 20 frames twice, a day apart, and report agreement on vehicle counts
   and box IoU.
6. Define the counting lines in image coordinates and draw them in a debug image.

## 6. Recommended baseline

**Detector only, no tracking:** count detections per frame and report the average,
plus the naive line-crossing count that increments whenever a detection centre is
near the line. This baseline usually over-counts badly, and the size of the error
is the motivation for tracking.

If a pretrained detector is unavailable offline, use the course's detection model
on frames and say so. A tracking baseline is a simple IoU-based association with a
maximum age; implement it before reaching for a library.

## 7. Milestones

| # | Milestone | Evidence | Hours |
| --- | --- | --- | --- |
| 1 | Clip manifest and privacy pipeline | Manifest, blurred sample frame, retention note | 8 |
| 2 | Detection per frame | Detections jsonl, per-frame timing | 10 |
| 3 | Tracking | Stable ids, ID switch examples | 12 |
| 4 | Counting | Line crossing, per-direction counts, double-count test | 8 |
| 5 | Ground truth and metrics | Annotation guide, agreement, MAE/MOTA/IDF1 | 14 |
| 6 | Robustness and package | Condition table, FPS, report, demo | 12 |

## 8. Repository or folder structure

```text
capstone-p09/
  README.md
  requirements.txt
  configs/
    pipeline.yaml         # detector confidence, iou, max_age, line coords
  data/
    dataset-card.md
    manifest.csv          # clip, fps, frames, resolution, condition, licence
    privacy.md            # what is blurred, where outputs live, retention
  annotations/
    clip_a_frames.json    # ground truth boxes and track ids
    guide.md
  src/
    frames.py             # decode, timestamps, frame hashing
    privacy.py            # face/plate blur before any write
    detect.py             # per-frame detections
    track.py              # IoU association, id lifecycle
    count.py              # line crossing with side history
    evaluate.py           # counting error, MOTA, IDF1
    render.py             # annotated video with blurred faces/plates
  tests/
    test_counting.py
    test_tracking.py
    test_privacy.py
  reports/
    report.md
    system-card.md
  outputs/
    counts.csv
    metrics.json
    annotated/            # blurred
```

## 9. Detailed development tasks

1. `frames.py`: decode with timestamps, not frame indices alone. Hash the first
   frame of each clip and record it so a swapped file is detectable.
2. `privacy.py`: detect and blur faces and plates on every frame before it is
   written to disk. Test with a frame containing a synthetic face region and assert
   the output region is blurred.
3. `detect.py`: run the detector at a fixed confidence, write one JSON line per
   frame with boxes, scores, and classes. Record per-frame inference time.
4. `track.py`: IoU-based association with a maximum age and a minimum hits rule.
   Log births, deaths, and ID switches. Print the id lifecycle for one vehicle.
5. `count.py`: represent each line as a segment with a normal. Track each object's
   side over time; count a crossing only when the sign changes between consecutive
   matched frames. Ignore objects that appear on both sides without a matched
   transition. Test with a synthetic trajectory that crosses twice (must count once)
   and one that jitters across the line (must not count repeatedly).
6. Ground truth: annotate boxes and track ids for one clip. Store as JSON with the
   same schema as predictions so evaluation is mechanical.
7. `evaluate.py`: counting MAE and percentage error per direction; MOTA and IDF1
   using your own matching at IoU 0.5; ID switch count. State the matching rule.
8. Condition analysis: run the pipeline on all seven clips and report counts,
   detection counts, and tracking stability per condition. Do not compare counts to
   ground truth where you have none; report the difference between clips instead.
9. Robustness: downsample resolution by 2x and 4x, and report the count change.
   Report frame-skipping (process every second frame) and its effect.
10. Throughput: FPS end to end (decode + detect + track), and the share spent in
    detection. State whether it is real time on your hardware.
11. `render.py`: write an annotated video with boxes, ids, and counting lines.
    Faces and plates blurred. No audio.
12. System card: purpose limitation, data, counts, error, privacy controls,
    retention, access, prohibited uses (enforcement, identification, surveillance).

## 10. Testing and evaluation plan

| Test | Proves | Pass condition |
| --- | --- | --- |
| Counting unit test | Double counting is prevented | Synthetic crossing counted once; jitter not counted |
| Tracking test | Association is sane | Two synthetic objects keep distinct ids |
| Privacy test | Blur is applied before write | Output frame region is blurred; no unblurred frame on disk |
| Frame hash test | The clip is the expected one | Hash matches the manifest |
| Metric test | Counting error is right | Hand case: 10 true, 12 predicted, MAE 2, 20% error |
| Determinism | Reruns agree | Same config gives identical counts |

Protocol: tune confidence and tracking parameters on one clip, evaluate counts on
the annotated clip, and report every other clip descriptively. Do not tune on the
evaluation clip and present the result as generalisation.

## 11. Metrics

**Quantitative**

| Metric | Why |
| --- | --- |
| Counting MAE and percentage error per direction | The user-facing number |
| MOTA and IDF1 | Tracking quality behind the counts |
| ID switches | The usual cause of over-counting |
| Detection mAP@0.5 on annotated frames | Separates detection from counting errors |
| FPS and detection share | Feasibility |
| Counts per clip per condition | Descriptive robustness |

**Qualitative**

- A frame sequence where a vehicle is missed and the count consequence.
- Whether parked vehicles or slow traffic cause repeated counts.
- Privacy statement: what is stored, for how long, who can see it.

## 12. Expected deliverables

- [ ] Clip manifest with conditions and licences.
- [ ] Privacy pipeline with a blurred sample and a written retention policy.
- [ ] Detection and tracking outputs with ids.
- [ ] Counting logic with unit tests for double counting.
- [ ] Ground truth for at least one clip plus an annotation guide and agreement score.
- [ ] Metrics table: counting error, MOTA, IDF1, mAP, FPS.
- [ ] Condition comparison across all clips.
- [ ] Annotated video with blurred faces and plates.
- [ ] System card and report.

## 13. Suggested extensions

- Add a second camera view and merge counts with a documented deduplication rule.
- Add queue length or occupancy estimation in a zone, with a different ground truth.
- Compare two association methods (IoU vs appearance embedding) and report ID switches.
- Add an alert when counts exceed a threshold, and evaluate false alert rate.

## 14. Common failure modes and troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Counts double the truth | Counting every detection near the line | Require a matched side transition |
| Counts jitter up and down | Line exactly on a stop line, objects hovering | Add hysteresis or a minimum displacement |
| IDs change every few frames | Association threshold too strict | Increase IoU threshold or max age; check detection stability |
| Same vehicle counted twice | Track lost and reborn | Merge by proximity and time window; report the rule |
| Night clip counts near zero | Detector confidence too high for low light | Report the condition; do not silently lower the threshold |
| FPS far below real time | Decoding or detection per frame | Skip frames, resize, or batch; report the accuracy cost |
| Unblurred face in output | Blur applied after annotation or on a copy | Blur at the earliest write point; test the pipeline |
| Ground truth takes forever | Annotating every frame | Annotate every fifth frame and state the evaluation protocol |

## 15. Marking rubric

| Criterion | Weight | 4 - Excellent | 3 - Meets | 2 - Approaching | 1 - Not yet |
| --- | --- | --- | --- | --- | --- |
| Pipeline correctness | 20% | Detection, tracking, and counting verified with unit tests | Working pipeline | Partly working | No counts |
| Counting logic | 20% | Double-count and jitter cases handled and tested | Counting works on the clip | Over/under-counts without analysis | Naive count |
| Evaluation | 20% | Ground truth, agreement, MAE, MOTA, IDF1, conditions | Counting error measured | Counts without ground truth | No evaluation |
| Privacy and governance | 15% | Blur enforced at write, retention and access documented, prohibited uses stated | Basic privacy controls | Mentioned only | No privacy controls |
| Performance analysis | 10% | FPS, detection share, resolution and frame-skip trade-offs | FPS measured | Rough timing | None |
| Communication | 15% | System card and report precise, failures shown | Clear report | Thin | Overstated |

**Bands:** 90-100 portfolio-ready; 80-89 solid; 70-79 counts work, evidence thin;
below 70 the counts are unverified.

## 16. Self-review checklist

- [ ] Every clip has a licence or consent record.
- [ ] Faces and plates are blurred before any frame is written.
- [ ] Counting handles a vehicle crossing twice and a jittering detection.
- [ ] Ground truth exists for at least one clip, with an agreement score.
- [ ] Counting error is reported per direction, not just total.
- [ ] MOTA/IDF1 are reported with the matching rule stated.
- [ ] Night/rain/shake clips are discussed.
- [ ] FPS is measured end to end.
- [ ] Prohibited uses are listed: enforcement, identification, covert surveillance.
- [ ] No raw footage of identifiable people is committed.

## 17. Report template

Use the shared [report template](report-template.md), adding:

1. **Purpose and governance** - who wants the counts, why, and what is forbidden.
2. **Counting logic** - the line representation, side history, and double-count rule.
3. **Ground truth** - annotation guide, agreement, and clip conditions.
4. **Results** - counting error, MOTA/IDF1, mAP, FPS, per clip.
5. **Privacy** - blur method, storage, retention, access.

## 18. Demonstration and presentation checklist

- [ ] Play the annotated clip with boxes, ids, and counts.
- [ ] Show a vehicle crossing the line twice and explain why it counts once.
- [ ] Show the counts table with ground truth error.
- [ ] Show the night clip and its failure.
- [ ] Show the blur in a zoomed frame.
- [ ] State the purpose limitation in one sentence.
- [ ] Answer: "Could this be used for enforcement? What stops it?"

**Demo trap:** demoing a clip you tuned on. Say which clip was used for tuning.

---

**Previous:** [P08 speech transcription](p08-speech-transcription.md) · **Next:** [P10 garment attributes](p10-garment-attributes.md) · [Index](index.md)
