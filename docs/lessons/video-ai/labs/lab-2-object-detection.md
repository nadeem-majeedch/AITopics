# Lab 2 - Object detection on video frames with a pretrained detector

**Section path:** [Overview](../index.md) · Modules [VD06](../vd06-detection-on-frames.md), [VD05](../vd05-image-vs-temporal-models.md) · **Lab 2** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 10% of the section assessment |
| **Time** | 2 hours |
| **Hardware** | CPU-only; ~40 s for 120 frames. One 13 MB checkpoint download on first run |
| **Code** | `projects/video-ai/lab2_object_detection.py` |
| **Prerequisites** | [Lab 1](lab-1-preprocessing.md), VD06 |

## Objectives

1. Run a real pretrained detector (COCO SSDLite320-MobileNetV3) over a video and export an
   annotated video you can review.
2. Measure per-frame latency, throughput, and real-time factor on your own machine.
3. Score the detections against frame-exact ground truth: mAP@0.5, precision, recall, TP/FP/FN,
   and the class histogram.
4. Explain the gap between "it runs" and "it works" using the two clips this lab uses.

## Prerequisites

- Lab 1 complete; data generated in `projects/video-ai/data/video/`.
- Network access on the first run, or a warm `TORCH_HOME` cache. The lab points `TORCH_HOME` at
  `projects/video-ai/.cache/torch`, so weights land inside the project and never in your home
  directory.
- Ground truth: `data/video/street_day.json` carries per-frame boxes, classes, and track IDs.

## Procedure

### 1. Run it

```bash
cd projects/video-ai
python lab2_object_detection.py
```

| Flag | Meaning |
| --- | --- |
| `--video street_rain` | one clip instead of day + night |
| `--limit 40` | stop after N frames |
| `--threshold 0.3` | score cut (default 0.30) |
| `--selftest` | 20 frames, assertions only, no video output |

### 2. Watch the annotated video

```
outputs/annotated_street_day.mp4
outputs/annotated_street_night.mp4
```

Pause on a frame with several vehicles. Count what the detector found, then compare with the
ground-truth count printed in the report. On `street_day` the report says 73 vehicle detections
against 360 ground-truth objects across 60 frames - about 1.2 per frame where there are 6.

### 3. Read the numbers in this order

1. **Recall** - 0.114. One vehicle in nine is found.
2. **Class histogram** - `{'truck': 73, 'tv': 6, 'chair': 2}`. Every vehicle is called a truck.
3. **TP/FP/FN** - 41 / 32 / 319. The misses dominate everything else.
4. **mAP@0.5** - 0.048. A summary of the above, not extra information.
5. **Speed** - ~59.8 ms/frame, 16.7 fps, RTF 0.615. This one is genuinely fine.

### 4. Run the night clip and compare

```bash
python lab2_object_detection.py --video street_night
```

Four detections in 60 frames, all wrong. The reported domain gap (0.048 → 0.000) is the number
Lab 4 tries to move.

### 5. Try the detector with `traffic_only=False`

Edit the call or use the module directly:

```python
from video_core.video import frame_at
from video_core.detect import SSDLiteDetector

det = SSDLiteDetector(score_threshold=0.3); det.load()
dets = det.predict(frame_at("data/video/street_day.mp4", 20), traffic_only=False)
print([(d.extra.get("coco_name"), round(d.score, 2)) for d in dets])
```

Seeing `tv` and `chair` on a road tells you what the model's priors are. That is useful when you
write the failure analysis, and it is why the mapping to four traffic classes exists.

## Expected output

```
=== detector
  ssdlite320_mobilenet_v3_large, COCO 2017, 3,440,060 parameters

=== street_day
  frames     : 60 processed, 81 detections (73 of them mapped to vehicle classes)
  classes    : {'truck': 73, 'tv': 6, 'chair': 2}
  speed      : 59.84 ms/frame median -> 16.69 fps, RTF 0.615
  accuracy   : mAP@0.5 0.048  precision 0.562  recall 0.114
               TP 41  FP 32  FN 319  wrong-class 27
               per-class AP {'car': 0.0, 'motorcycle': 0.0, 'truck': 0.1441}
  annotated  : annotated_street_day.mp4 (60 frames)

=== street_night
  frames     : 60 processed, 4 detections (4 of them mapped to vehicle classes)
  classes    : {'truck': 4}
  speed      : 54.14 ms/frame median -> 18.29 fps, RTF 0.562
  accuracy   : mAP@0.5 0.000  precision 0.000  recall 0.000
               TP 0  FP 4  FN 360  wrong-class 0
  annotated  : annotated_street_night.mp4 (60 frames)

  domain gap : mAP@0.5 0.048 (day) vs 0.000 (night) -> gap 0.048
  6/6 checks passed
```

Your milliseconds will differ - possibly by 2x - and that is expected. Report your own.

## Evaluation

| Criterion | Marks | Evidence |
| --- | --- | --- |
| Lab runs, 6/6 checks | 3 | output |
| Annotated video reviewed; one specific failure named | 3 | "at frame 34 the bus is detected as two trucks" |
| Class histogram interpreted | 2 | why all `truck`, and what it costs |
| Timing reported with machine and settings | 2 | your ms/frame, threads, resolution |

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `pretrained detector unavailable: ...` | no network and no cached weights | connect once, or accept the baseline-unavailable path and say so |
| Download is very slow | first-run checkpoint | it is a one-off; check `projects/video-ai/.cache/torch` afterwards |
| `torchvision` import error | mismatched torch/torchvision | same version pair as `requirements/video.txt` |
| mAP is 0.000 on day too | class index mismatch in your own evaluation | use `LABEL_TO_INDEX`; COCO labels are 1-based |
| Annotated video is empty | `--limit 0` or writer failure | check `outputs/`, look for a `VideoError` reason |
| Machine runs out of memory | several detector instances loaded | reuse one instance; RSS ~150 MB per model |

## Extensions

1. **Threshold sweep.** Evaluate at 0.10, 0.30, 0.50 and plot precision, recall, and F1 against
   threshold. At which threshold does recall reach 0.30, and how many detections does that cost?
2. **Crop and upscale.** Detect on the night clip after a gamma correction (e.g.
   `frame ** 0.6`) and report whether recall moves. Explain the result in one sentence.
3. **Stride and count.** Run with every second frame and compare detections per frame. Does the
   detector miss more when frames are further apart? (It should not - it has no memory - which
   is itself the finding.)
4. **Ground-truth sanity check.** Draw the *ground truth* boxes on 10 frames and confirm they are
   tight. A wrong ground truth makes every metric meaningless, and it is the first thing to
   check when mAP looks impossible.

## Submit

- Full lab output.
- Your annotated video reviewed, with one named failure and the frame index.
- A table of your machine's timings: ms/frame, fps, RTF, resolution, thread count.
- Two sentences on the class histogram: what the model thinks it sees, and what that implies for
  any downstream count.
