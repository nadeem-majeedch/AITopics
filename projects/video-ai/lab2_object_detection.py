"""Lab 2 - Object detection on video frames with a pretrained detector.

Goal: run a real, pretrained object detector over a video, draw what it finds, export an
annotated video, and measure how fast it runs. Then measure how *well* it runs, which is
the uncomfortable part. The detector's code licence is clear; its weight terms are not,
and this lab does not redistribute the weights.

The model is SSDLite320-MobileNetV3 from torchvision, trained on COCO 2017 (80 classes,
3.44 M parameters). The torchvision code is BSD-3-Clause. The pretrained weights have no
separately stated licence and are downloaded at runtime. It has never seen this section's
synthetic frames. Two numbers come out of the lab:

* **Speed**, which is fine: tens of milliseconds per frame on CPU, several frames per
  second, comfortably faster than the 10 fps test footage.
* **Accuracy**, which is not: on the day scene it finds 73 vehicles in 360 ground-truth
  boxes and calls every single one a truck, so a quarter of its hits overlap a vehicle the
  lab calls a car or a bus. On the night scene it returns four boxes and matches none of
  them. The same predictions are scored against frame-exact ground truth, so the gap is
  measured rather than asserted.

That is the honest starting point for every "just run a pretrained model on your video"
tutorial: it works when your video looks like the training data, and traffic cameras at
night do not. Lab 4 fine-tunes this model and shows what changes - and what does not.

Run:

    python lab2_object_detection.py                # ~40 s on CPU (60 frames x 2 videos)
    python lab2_object_detection.py --selftest     # 20 frames, assertions only
    python lab2_object_detection.py --video street_rain --limit 40

Output:

    outputs/annotated_<video>.mp4          boxes drawn on every processed frame
    outputs/lab2_frame_<video>.png         one annotated frame, for the write-up
    outputs/lab2_object_detection.json     detections, metrics, timings
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lab_support as support
from video_core import labels as labels_mod, metrics, video

# The four COCO names this section cares about, for filtering what gets drawn.
TRAFFIC_NAMES = {"car", "motorcycle", "bus", "truck"}


def summarise_classes(records: list[dict]) -> dict:
    """What the detector *says* it sees, including classes nobody asked for.

    Keeping the non-vehicle classes is deliberate: "traffic light" and "person" appearing
    all over a road scene is the most legible evidence that the model's prior is about
    photographs, not about this footage.
    """
    counts = Counter()
    for rec in records:
        for det in rec["detections"]:
            counts[det.get("coco_name", str(det["label"]))] += 1
    return dict(counts.most_common(12))


def score(records: list[dict], name: str) -> dict:
    """Score only the detections that fall in our four vehicle classes.

    The full pass keeps every COCO class so the histogram is honest, but grading against
    ground truth needs one label space. This maps ``car``/``bus``/``truck``/``motorcycle``
    onto the section's label indices and drops the rest; anything the model called a
    "traffic light" is simply not a vehicle prediction and must not be counted as a true
    positive at the right box.
    """
    gt_by_frame = {g["frame"]: g["objects"] for g in support.scene(name)["frames_gt"]}
    pairs = []
    for rec in records:
        dets = []
        for det in rec["detections"]:
            coco = det.get("coco_name")
            if coco not in TRAFFIC_NAMES:
                continue
            dets.append(metrics.Detection(list(det["box"]),
                                          labels_mod.LABEL_TO_INDEX[coco],
                                          float(det["score"])))
        truth = [{"box": o["box"], "label": labels_mod.LABEL_TO_INDEX[o["class"]]}
                 for o in gt_by_frame.get(rec["frame"], [])]
        pairs.append((dets, truth))
    return metrics.detection_report(pairs, num_classes=len(labels_mod.LABELS),
                                    class_names=list(labels_mod.LABELS))


def run_video(name: str, model, *, limit: int | None, draw: bool) -> dict:
    path = support.video_path(name)
    entry = support.scene(name)
    info = video.probe(path)

    records: list[dict] = []
    started = time.perf_counter()
    writer = None
    out_path = support.OUT / f"annotated_{name}.mp4"
    first_frame = None
    if draw:
        support.OUT.mkdir(parents=True, exist_ok=True)
        writer = video.VideoWriter(out_path, info.fps, (info.width, info.height))

    try:
        for index, stamp, frame in video.iter_frames(path, limit=limit):
            t0 = time.perf_counter()
            detections = model.predict(frame, traffic_only=False)
            elapsed = time.perf_counter() - t0
            records.append({
                "frame": index,
                "t_s": round(stamp, 3),
                "detections": [d.as_dict() for d in detections],
                "seconds": round(elapsed, 5),
            })
            if writer is not None:
                # Only vehicle classes get drawn: an annotated video covered in thirty
                # "traffic light" boxes teaches nothing about detection. The full class
                # histogram is still reported, so nothing is hidden - it is just not drawn.
                traffic = [d for d in detections
                           if d.extra.get("coco_name") in TRAFFIC_NAMES]
                boxes = [d.box for d in traffic]
                captions = [f"{d.extra['coco_name']} {d.score:.2f}" for d in traffic]
                drawn = video.annotate_frame(frame, boxes, captions, colour=(60, 200, 240))
                writer.write(drawn)
                if first_frame is None and traffic:
                    first_frame = drawn
    finally:
        total = time.perf_counter() - started
        if writer is not None:
            writer.close()

    seconds = data = None
    if records:
        seconds = [r["seconds"] for r in records]
        data = {
            "video": name,
            "frames_processed": len(records),
            "frames_in_video": entry["frames"],
            "detections": sum(len(r["detections"]) for r in records),
            "detections_per_frame": round(
                sum(len(r["detections"]) for r in records) / len(records), 3),
            "vehicle_detections": sum(
                1 for r in records for d in r["detections"]
                if d.get("coco_name") in TRAFFIC_NAMES),
            "class_counts": summarise_classes(records),
            "mean_ms_per_frame": round(float(np.mean(seconds)) * 1000, 2),
            "median_ms_per_frame": round(float(np.median(seconds)) * 1000, 2),
            "fps_processed": round(1.0 / float(np.mean(seconds)), 2),
            "wall_seconds": round(total, 2),
            "real_time_factor": round(total / (len(records) / info.fps), 3),
            "annotated_video": out_path.name if draw else None,
            "annotated_frames": writer.frames_written if writer else 0,
            "metrics": score(records, name),
            "records": records,
        }
        if first_frame is not None and draw:
            frame_path = support.OUT / f"lab2_frame_{name}.png"
            cv2.imwrite(str(frame_path), first_frame)
            data["sample_frame"] = frame_path.name
    return data or {"video": name, "frames_processed": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--video", default=None, help="process one video (default: day + night)")
    parser.add_argument("--limit", type=int, default=None, help="stop after N frames")
    parser.add_argument("--threshold", type=float, default=0.30, help="score threshold")
    parser.add_argument("--selftest", action="store_true", help="20 frames, no video output")
    args = parser.parse_args()

    names = [args.video] if args.video else ["street_day", "street_night"]
    limit = 20 if args.selftest else args.limit

    support.rule("pretrained detector")
    model, info = support.ssdlite(args.threshold)
    if not info["available"]:
        print("  weights unavailable - this lab needs the pretrained checkpoint")
        print(f"  reason: {info['load_error']}")
        print("  connect to the network once (weights are ~13 MB) and re-run")
        return 1
    print(f"  model      : {info['name']}")
    print(f"  trained on : {info['pretrained_on']}")
    print(f"  parameters : {info['parameters']:,}")
    print(f"  weights in : {info['torch_home']}")
    print("  licence    : torchvision code BSD-3-Clause; pretrained weight terms unresolved")
    print("  note       : this is an *inference* run. Nothing has been fine-tuned;")
    print("               Lab 4 does the fine-tuning and says exactly what it changes.")

    results: list[bool] = []
    per_video = []
    for name in names:
        support.rule(name)
        data = run_video(name, model, limit=limit, draw=not args.selftest)
        if not data.get("frames_processed"):
            results.append(support.check(f"{name}: frames processed", False))
            continue
        m = data["metrics"]
        print(f"  frames     : {data['frames_processed']} processed, "
              f"{data['detections']} detections "
              f"({data['vehicle_detections']} of them mapped to vehicle classes)")
        print(f"  classes    : {data['class_counts']}")
        print(f"  speed      : {data['median_ms_per_frame']} ms/frame median "
              f"-> {data['fps_processed']} fps, RTF {data['real_time_factor']}")
        print(f"  accuracy   : mAP@0.5 {m['map50']:.3f}  precision {m['precision']:.3f}  "
              f"recall {m['recall']:.3f}")
        print(f"               TP {m['true_positives']}  FP {m['false_positives']}  "
              f"FN {m['false_negatives']}  wrong-class {m['class_confusions']}")
        if m["per_class_ap"]:
            print(f"               per-class AP {m['per_class_ap']}")
        if data.get("annotated_video"):
            print(f"  annotated  : {data['annotated_video']} "
                  f"({data['annotated_frames']} frames)")

        results.append(support.check(f"{name}: every frame processed",
                                     data["frames_processed"] >= min(20, support.scene(name)["frames"])))
        results.append(support.check(f"{name}: a positive FPS was measured",
                                     data["fps_processed"] > 1.0,
                                     f"{data['fps_processed']} fps"))
        if not args.selftest:
            out = support.OUT / (data["annotated_video"] or "missing")
            results.append(support.check(f"{name}: annotated video is readable",
                                         out.exists() and video.probe(out).frame_count
                                         == data["frames_processed"],
                                         f"{out.name}"))
        per_video.append({k: v for k, v in data.items() if k != "records"})

    if len(per_video) == 2:
        day, night = per_video[0], per_video[1]
        gap = day["metrics"]["map50"] - night["metrics"]["map50"]
        print(f"\n  domain gap : mAP@0.5 {day['metrics']['map50']:.3f} (day) vs "
              f"{night['metrics']['map50']:.3f} (night) -> gap {gap:.3f}")

    support.rule("what this tells you")
    print("  The pretrained model is fast and mostly wrong on this footage. Both halves")
    print("  matter: a demo that only reports speed looks successful, and a demo that only")
    print("  reports green boxes on one lucky frame looks accurate. The next labs either")
    print("  adapt the model (Lab 4) or build the parts detection does not provide")
    print("  (tracking and counting, Lab 3).")

    support.write_report("lab2_object_detection.json", {
        "lab": "object detection with a pretrained detector",
        "model": info,
        "score_threshold": args.threshold,
        "videos": per_video,
        "checks": results,
    })
    return support.all_checks(results)


if __name__ == "__main__":
    raise SystemExit(main())
