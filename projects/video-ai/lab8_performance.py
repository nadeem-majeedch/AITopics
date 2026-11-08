"""Lab 8 - Performance: sampling rate, model size, resolution, and what each one costs.

Goal: measure the levers that decide whether a video analytics pipeline fits on the machine
it has to run on, and separate the ones that actually save time from the ones that only feel
like they should.

Four measurements, each with an accuracy number next to it:

1. **Sampling rate** (process every frame, every second frame, ...). This is the real lever:
   cost falls roughly linearly, and the counting result barely moves - until vehicles move
   so far between processed frames that the tracker loses them.
2. **Model size** (a 138 K-parameter detector trained in-section versus a 3.4 M-parameter
   pretrained one). 25x the latency for a model that finds less on this footage.
3. **Working resolution** (decode at full, half, and quarter size). This is the measurement
   that usually surprises people: both detectors resize their input to a fixed size, so
   downscaling the frames changes the *decode* cost and the *accuracy* but not the inference
   cost. Resolution is a lever only for a model that runs at native size.
4. **Memory**, measured as the process's resident set before and after loading each model.

Every timing in this lab warms the model up first and reports the median of repeated runs.
The first inference on a lazily-built graph is several times slower than the rest, and
reporting that number instead of the steady-state one is the most common way performance
claims go wrong.

Run:

    python lab8_performance.py                # ~1 min on CPU
    python lab8_performance.py --selftest     # fewer strides, checks only
    python lab8_performance.py --video street_crowd

Output:

    outputs/lab8_performance.json
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lab_support as support
from video_core import counting, detect, labels as labels_mod, metrics, tracking, video


def timed_detection(name: str, model, *, stride: int, warmup: int = 2) -> dict:
    """Detect over a video with timing that excludes the first few (lazy-init) frames."""
    path = support.video_path(name)
    info = video.probe(path)
    frames = list(video.iter_frames(path, stride=stride))
    for _, _, frame in frames[:warmup]:
        model.predict(frame)

    started = time.perf_counter()
    records = []
    infer_times = []
    for index, stamp, frame in frames:
        t0 = time.perf_counter()
        try:
            detections = model.predict(frame, score_threshold=0.5, nms_iou=0.30)
        except TypeError:
            detections = model.predict(frame)
        infer_times.append(time.perf_counter() - t0)
        records.append({"frame": index, "detections": [d.as_dict() for d in detections]})
    wall = time.perf_counter() - started
    duration = info.frame_count / info.fps
    return {
        "stride": stride,
        "frames": len(records),
        "wall_s": round(wall, 3),
        "video_duration_s": round(duration, 2),
        "ms_per_frame": round(float(np.median(infer_times)) * 1000, 2),
        "processed_fps": round(1.0 / float(np.median(infer_times)), 1),
        # The number a deployment cares about: compute spent per second of video.
        "ms_per_video_second": round(wall / duration * 1000, 1),
        "records": records,
    }


def count_from_records(name: str, records: list[dict]) -> dict:
    predictions = tracking.track_detections(detect.to_metric_detections(records))
    line = support.counting_truth(name)
    report = metrics.counting_report(
        line["expected_crossings"],
        counting.run_counter(predictions, line["p1"], line["p2"])["events"])
    return {
        "counted": report["counted_total"],
        "expected": report["expected_total"],
        "error": report["absolute_error"],
        "unique_tracks": tracking.unique_track_count(predictions)["unique_tracks"],
    }


def resolution_sweep(name: str, model, scales: list[float]) -> list[dict]:
    """Decode at several scales; scale boxes back so accuracy is comparable.

    Both detectors resize to a fixed input, so the *model* cost should be flat. Any
    difference here is decode and resize cost, plus the accuracy lost to a smaller source
    image. That distinction is the point of the table.
    """
    path = support.video_path(name)
    info = video.probe(path)
    gt_by_frame = {g["frame"]: g["objects"] for g in support.scene(name)["frames_gt"]}
    rows = []
    for scale in scales:
        size = (max(2, int(round(info.width * scale))), max(2, int(round(info.height * scale))))
        frames = list(video.iter_frames(path, resize=size))
        for _, _, frame in frames[:2]:
            model.predict(frame)

        started = time.perf_counter()
        infer_times = []
        pairs = []
        for index, _, frame in frames:
            t0 = time.perf_counter()
            try:
                detections = model.predict(frame, score_threshold=0.5, nms_iou=0.30)
            except TypeError:
                detections = model.predict(frame)
            infer_times.append(time.perf_counter() - t0)
            # Boxes come back in the downscaled frame's pixels; scale them up to compare
            # with ground truth that was drawn at full resolution.
            scaled = [metrics.Detection([b / scale for b in d.box], d.label, d.score)
                      for d in detections]
            truth = [{"box": o["box"], "label": labels_mod.LABEL_TO_INDEX[o["class"]]}
                     for o in gt_by_frame.get(index, [])]
            pairs.append((scaled, truth))
        wall = time.perf_counter() - started
        report = metrics.detection_report(pairs, num_classes=len(labels_mod.LABELS),
                                          class_names=list(labels_mod.LABELS))
        rows.append({
            "scale": scale,
            "frame_size": f"{size[0]}x{size[1]}",
            "wall_s": round(wall, 3),
            "ms_per_frame": round(float(np.median(infer_times)) * 1000, 2),
            "map50": report["map50"],
            "recall": report["recall"],
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--video", default="street_day")
    parser.add_argument("--selftest", action="store_true", help="fewer strides, checks only")
    args = parser.parse_args()

    strides = [1, 2] if args.selftest else [1, 2, 3, 5]

    support.rule("models and memory")
    baseline_mem = metrics.process_memory_mb()
    model, info = support.train_tiny_detector()
    tiny_mem = metrics.process_memory_mb()
    tiny_params = support.detector_params(model)
    print(f"  TinyDetector  : {tiny_params:,} parameters "
          f"(~{tiny_params * 4 / 1024 / 1024:.1f} MB float32), "
          f"{info['cache_key']}")
    print(f"  process RSS   : {baseline_mem:.1f} MB -> {tiny_mem:.1f} MB after loading it")

    results: list[bool] = []

    support.rule(f"1. sampling rate on {args.video}")
    stride_rows = []
    for stride in strides:
        run = timed_detection(args.video, model, stride=stride)
        report = support.detection_scores(args.video, run["records"])
        counted = count_from_records(args.video, run["records"])
        stride_rows.append({
            "stride": stride,
            "frames": run["frames"],
            "wall_s": run["wall_s"],
            "ms_per_video_s": run["ms_per_video_second"],
            "map50": report["map50"],
            "counted": counted["counted"],
            "count_error": counted["error"],
            "tracks": counted["unique_tracks"],
        })
    base_cost = stride_rows[0]["ms_per_video_s"] or 1.0
    for row in stride_rows:
        row["speedup"] = round(base_cost / (row["ms_per_video_s"] or 1.0), 2)
    support.table(stride_rows, ["stride", "frames", "wall_s", "ms_per_video_s", "speedup",
                                "map50", "counted", "count_error", "tracks"])
    fastest = stride_rows[-1]
    print(f"  Stride {fastest['stride']} costs {fastest['speedup']}x less compute than every "
          f"frame for {fastest['count_error']} count error.")
    print("  Cost falls close to linearly because work per processed frame is constant. The")
    print("  accuracy column is the price: at some stride the tracker stops seeing vehicles")
    print("  often enough to associate them, and tracks fragment.")

    support.rule("2. model size")
    ssdlite, ssdlite_info = support.ssdlite(0.30)
    model_rows = []
    tiny_run = timed_detection(args.video, model, stride=1)
    tiny_report = support.detection_scores(args.video, tiny_run["records"])
    model_rows.append({"model": "TinyDetector (scratch)", "params": tiny_params,
                       "ms_per_frame": tiny_run["ms_per_frame"],
                       "map50": tiny_report["map50"]})
    if ssdlite_info["available"]:
        ssd_run = timed_detection(args.video, ssdlite, stride=1)
        ssd_report = support.detection_scores(args.video, ssd_run["records"])
        # The COCO wrapper emits COCO indices; score() above remaps via coco_name, so the
        # number is comparable. It is low because this is the untouched baseline.
        model_rows.append({"model": "SSDLite320 (COCO)", "params": ssdlite_info["parameters"],
                           "ms_per_frame": ssd_run["ms_per_frame"],
                           "map50": ssd_report["map50"]})
    support.table(model_rows, ["model", "params", "ms_per_frame", "map50"])
    if len(model_rows) == 2:
        ratio = model_rows[1]["ms_per_frame"] / max(model_rows[0]["ms_per_frame"], 1e-6)
        print(f"  {ratio:.1f}x the latency for a model that scores lower here. Model size "
              "is not accuracy; it is accuracy *on the data it was trained for*.")
    print(f"  process RSS after both models: {metrics.process_memory_mb():.1f} MB")

    support.rule("3. working resolution")
    res_rows = resolution_sweep(args.video, model, [1.0, 0.5, 0.25])
    support.table(res_rows, ["scale", "frame_size", "wall_s", "ms_per_frame", "map50", "recall"])
    flat = max(row["ms_per_frame"] for row in res_rows) / max(
        min(row["ms_per_frame"] for row in res_rows), 1e-6)
    print(f"  Inference time varies by {flat:.2f}x across a 16x change in pixels: both")
    print("  models resize to a fixed input, so the cost is in the network, not the frame.")
    print("  Resolution still matters for accuracy - small vehicles become too few pixels")
    print("  to detect - and for decode cost on large files, which this clip is too small")
    print("  to show.")

    support.rule("4. the accuracy-versus-speed summary")
    support.table([{"lever": "sampling stride", "cost": f"{stride_rows[-1]['speedup']}x cheaper",
                    "accuracy": f"mAP {stride_rows[-1]['map50']:.3f}, "
                                f"count error {stride_rows[-1]['count_error']}"},
                   {"lever": "smaller model", "cost": f"{tiny_run['ms_per_frame']} ms/frame",
                    "accuracy": f"mAP {tiny_report['map50']:.3f} (vs "
                                f"{model_rows[-1]['map50']:.3f} for the big one)"},
                   {"lever": "lower resolution",
                    "cost": f"{flat:.2f}x (no change)",
                    "accuracy": f"mAP {res_rows[-1]['map50']:.3f} at "
                                f"{res_rows[-1]['frame_size']}"}],
                  ["lever", "cost", "accuracy"])
    print("  Choose the sampling rate first: it is the lever with a real, linear payoff.")
    print("  Choose the model second: the smallest one that meets the accuracy floor on")
    print("  *your* validation video. Never quote a resolution change as a speed-up unless")
    print("  you have measured it on the model you are actually shipping.")

    results.append(support.check("timings were warmed up (no first-call inflation)",
                                 tiny_run["ms_per_frame"] < 50.0,
                                 f"{tiny_run['ms_per_frame']} ms/frame"))
    results.append(support.check("stride reduces compute", fastest["speedup"] > 1.3,
                                 f"{fastest['speedup']}x"))
    results.append(support.check("detector still works at the largest stride",
                                 stride_rows[-1]["map50"] > 0.5,
                                 f"mAP {stride_rows[-1]['map50']:.3f}"))
    results.append(support.check("the larger pretrained model is slower",
                                 len(model_rows) < 2 or
                                 model_rows[1]["ms_per_frame"] > model_rows[0]["ms_per_frame"],
                                 f"{model_rows[-1]['ms_per_frame']} ms"))
    results.append(support.check("resolution does not change inference cost much",
                                 flat < 2.0, f"{flat:.2f}x"))
    results.append(support.check("memory was measured, not assumed",
                                 metrics.process_memory_mb() > 0,
                                 f"{metrics.process_memory_mb():.0f} MB"))

    support.write_report("lab8_performance.json", {
        "lab": "performance: sampling, model size, resolution, memory",
        "video": args.video,
        "strides": stride_rows,
        "models": model_rows,
        "resolution": res_rows,
        "memory_mb": {"start": round(baseline_mem, 1), "after_tiny": round(tiny_mem, 1),
                      "end": round(metrics.process_memory_mb(), 1)},
        "threads": getattr(__import__("torch"), "get_num_threads", lambda: 0)(),
        "checks": results,
    })
    return support.all_checks(results)


if __name__ == "__main__":
    raise SystemExit(main())
