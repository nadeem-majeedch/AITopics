# VD06 - Object detection on video frames {#vd06}

**Section path:** [Overview](index.md) · **Module 6** · [Lab 2](labs/lab-2-object-detection.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 1.5 h reading, 2.5 h practice |
| **Hardware** | CPU-only; one 13 MB checkpoint download on first run |
| **Prerequisites** | [VD05](vd05-image-vs-temporal-models.md) |
| **You will produce** | A detector run over two clips with per-frame timing, an annotated video, and an mAP you can explain |

## Why this module exists

Detection on video is detection on frames, plus everything around it: which frames, how fast,
what to do with the boxes, and how to know whether the numbers mean anything. The detector
itself is the easy part - torchvision loads one in three lines. The hard part is that a
detector's accuracy on video is a property of the *clip*, not the model, and this module makes
that concrete with a measured failure.

## The two detectors in this section

| | `TinyDetector` | `SSDLiteDetector` |
| --- | --- | --- |
| Parameters | 138,579 | 3,440,060 |
| Trained on | this section's train frames only | COCO 2017, by torchvision |
| Classes | 4 traffic classes | 91 COCO classes, 4 of them mapped to traffic |
| Input | 256x144 | 320x320 |
| CPU latency here | ~4.3 ms/frame | ~58.7 ms/frame |
| Honest description | trained from scratch for this task | a pretrained general-purpose detector |

The pretrained one exists because **you must measure a baseline before you train**. It is not
there to succeed; it is there to show what "an off-the-shelf detector on footage it has never
seen" actually scores, so that your own model's score has a reference point.

```python
from video_core.detect import SSDLiteDetector, TinyDetector

det = SSDLiteDetector(score_threshold=0.30)
if not det.load():
    print("pretrained detector unavailable:", det.load_error)   # offline machine
else:
    dets = det.predict(frame, traffic_only=True)
    print([(d.label, round(d.score, 3), [round(v) for v in d.box]) for d in dets][:3])
```

`load()` returns `False` with a reason rather than raising, because a lab must still run on a
machine with no network. Every later call then returns an empty list, and the report says the
baseline was unavailable - which is honest, and different from "the baseline scored 0.000".
Do not let those two states share a code path in your own project.

## COCO to traffic: the mapping that decides your numbers

SSDLite's output is a set of COCO categories. Only four of them are vehicles:

```python
from video_core.detect import COCO_TRAFFIC_IDS
print(sorted(COCO_TRAFFIC_IDS))     # [3, 4, 6, 8] -> car, motorcycle, bus, truck
```

With `traffic_only=True` the detector drops everything else. That is not cosmetic. On the day
clip, the raw COCO model returns 81 detections of which 73 map to a vehicle class - and the
73 vehicle detections are all labelled `truck`:

```
classes: {'truck': 73, 'tv': 6, 'chair': 2}
```

A model that calls every vehicle a truck has learned that "box-shaped thing on a road" is the
most likely of its four options given its training prior. Precision looks respectable (0.562)
and recall is 0.114: it finds one vehicle in nine, and mostly calls it the wrong thing. This is
what a domain gap looks like when you print the class histogram instead of only the mAP.

## Measuring: what mAP@0.5 hides

`metrics.detection_report` returns mAP@0.5, precision, recall, per-class AP, and a confusion
count. The measured result on the two clips Lab 2 uses:

```
street_day   mAP@0.5 0.048   precision 0.562   recall 0.114
             TP 41  FP 32  FN 319  wrong-class 27
             per-class AP {'car': 0.0, 'motorcycle': 0.0, 'truck': 0.144}
street_night mAP@0.5 0.000   precision 0.000   recall 0.000
             TP 0   FP 4   FN 360  wrong-class 0
```

Three things to read from that table, in this order:

1. **FN dominates.** 319 misses out of 360 ground-truth objects on the day clip. Any system
   built on this detector would be blind to 89% of traffic, and the mAP (0.048) is a summary of
   that fact, not a separate one.
2. **The class histogram is wrong.** 27 detections matched a real vehicle's box but named the
   wrong class. Because matching is class-aware (`metrics.match_frame` refuses to pair a car
   detection with a truck ground truth), those count as both a false positive and a false
   negative. That is the strict convention, and it is the right one for counting.
3. **Night is zero, not "a bit worse".** Four detections in total. The zero is not noise - it
   is the model having no representation for a dark scene with headlights.

A single number would have hidden all three. Print the components.

## Timings, and what they mean for a deployment

```
street_day   ~59.8 ms/frame median -> ~16.7 fps, real-time factor 0.62
street_night ~54.1 ms/frame median -> ~18.3 fps, real-time factor 0.56
```

(Timings move by a few percent between runs on the same machine; the accuracy numbers in the
table above do not.)

Real-time factor (RTF) is processing time divided by clip duration: 0.6 means it processes
faster than the clip plays, so a 10 fps camera at 640x360 can be handled by one core with
headroom. Lab 8 profiles the same question properly - median, p95, warm-up, memory - and finds
that the small detector is 13.8x faster at a fraction of the size, which is why the section's
own pipeline uses it.

Note what these numbers are not: they are latency on one machine, for one resolution, with one
thread, on a cold-ish cache. Do not generalise them. Do report them with the machine and the
settings, which is what Lab 8's harness exists to enforce.

## Thresholds: a decision, not a default

A detector emits scores, and someone must choose a cut. 0.30 is a reasonable starting point for
SSDLite on COCO-like data; it is a bad choice for a model with a domain gap, where lowering it
to 0.10 buys recall by flooding the tracker with false positives.

The rule this section uses: **choose the threshold on the validation video, and never on test.**
Lab 4 does this explicitly and reports the winner (0.6 by best F1 on `street_quiet`), then
applies that single number to four unseen test videos. If you tune on test, your test score is a
training score with extra steps.

## From detections to something a human can check

Numbers do not catch the failure where every box is offset by 20 pixels. A review video does:

```python
from video_core import video
from video_core.detect import detect_video
from video_core.labels import LABELS

records = detect_video("data/video/street_day.mp4", detector, stride=1)
with video.VideoWriter("outputs/annotated.mp4", fps=10, size=(640, 360)) as w:
    for rec in records:
        frame = video.frame_at("data/video/street_day.mp4", rec["frame"])
        boxes = [d["box"] for d in rec["detections"]]
        # Detection.as_dict() carries the numeric label; LABELS turns it back into a name.
        captions = [f"{LABELS[d['label']]} {d['score']:.2f}" for d in rec["detections"]]
        w.write(video.annotate_frame(frame, boxes, captions))
```

Two details worth copying: the loop uses `rec["frame"]` (the source index) rather than a
counter, and writing is separated from detecting so the same detections can feed a report and a
video without being computed twice. Lab 2 writes `annotated_street_day.mp4` this way - watch it
before you believe any metric.

## Why a video detector is still a frame detector here

The boxes in frame *t* are computed from frame *t* alone. Nothing is smoothed, nothing is
predicted, and a detection that flickers off for one frame is simply gone. That produces the
fragmentation Lab 3 measures: 14 predicted tracks for 6 real vehicles, partly because the
detector drops boxes mid-occlusion.

The fix is not a bigger model. It is a tracker, which is Module 7's subject - and it is cheaper
and far easier to debug than a temporal detector. This is the section's recurring architectural
claim: **per-frame detection plus explicit temporal logic beats an end-to-end temporal model for
small-data, explainable problems.**

## Common mistakes

| Mistake | Symptom | Fix |
| --- | --- | --- |
| Comparing to ground truth with mismatched class indices | mAP 0.000 while boxes look right | use `LABEL_TO_INDEX`; COCO is 1-based |
| Tuning the threshold on the test split | test score 10 points above validation | choose on val, apply once |
| Reporting only mAP | misses 89% recall and a wrong class histogram | print TP/FP/FN and the histogram |
| Ignoring `load()`'s return | silent empty results on an offline machine | branch on it, and say so in the report |
| Drawing boxes with the wrong frame index | boxes trail the vehicles by one frame | use the source index `rec["frame"]` |
| Quoting fps without the machine | numbers that nobody can reproduce | report CPU, threads, resolution |

## Checks

- [ ] You can state `TinyDetector`'s and SSDLite's parameter counts and CPU latencies.
- [ ] You can explain why 27 wrong-class detections cost both a FP and an FN.
- [ ] You know which split the threshold is chosen on, and why.
- [ ] You have watched the annotated video and found at least one frame where the model fails.
- [ ] You can say what "real-time factor 0.615" implies for a 10 fps camera.
