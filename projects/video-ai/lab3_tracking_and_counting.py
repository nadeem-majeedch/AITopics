"""Lab 3 - Detect, track, and count vehicles crossing a virtual line.

Goal: turn per-frame boxes into *vehicles* - objects with an identity that survives frames -
and count how many of them cross a line. Then break the system on purpose to see what
breaks first.

The pipeline is four small pieces, each of which can fail separately:

    detect -> associate (IoU tracker) -> settle the class by voting -> count crossings

Three failure modes are measured rather than described:

* **Occlusion** (``street_crowd``): a bus hides a car, the detector misses it, the track
  coasts on predicted velocity, and - if the occlusion outlasts ``max_age`` - the vehicle
  comes back with a new ID and is counted twice.
* **Camera movement** (``street_shake``): every box shifts with the frame, so a tracker that
  compares absolute positions sees motion that is not there.
* **Fragmentation**: one vehicle producing several IDs. The lab reports the count of GT
  vehicles that received more than one predicted ID, which is the honest version of "tracking
  accuracy" for a counting application.

It also sweeps ``max_age``, the single tracker parameter that trades "survives occlusion"
against "keeps dead tracks alive", so the trade-off is a table instead of a claim.

The detector is trained in-section on frames from ``street_day`` and ``street_dusk``. That
makes ``street_day`` an *in-domain* video: its mAP is optimistic, and this lab says so. Lab 4
is where held-out evaluation happens.

Run:

    python lab3_tracking_and_counting.py             # ~15 s after the detector is cached
    python lab3_tracking_and_counting.py --selftest  # checks only, no video output
    python lab3_tracking_and_counting.py --video street_crowd

Output:

    outputs/tracked_<video>.mp4          boxes, track IDs, trails, and the counting line
    outputs/lab3_tracking.json           metrics, counts, limitation tables
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lab_support as support
from video_core import counting, detect, metrics, tracking, video


def pipeline(name: str, model, *, stride: int = 1, limit: int | None = None,
             max_age: int = 6, min_hits: int = 2) -> dict:
    """Detect, track, and count on one video. Returns everything the report needs."""
    records = support.detect_scene(name, model, stride=stride, limit=limit)
    detections = detect.to_metric_detections(records)
    predictions = tracking.track_detections(detections, max_age=max_age, min_hits=min_hits)

    gt_objects = [g["objects"] for g in support.scene(name)["frames_gt"]]
    if limit:
        gt_objects = gt_objects[:len(predictions)]
    track_report = tracking.tracker_report(predictions, gt_objects)
    unique = tracking.unique_track_count(predictions)

    line = support.counting_truth(name)
    counted = counting.run_counter(predictions, line["p1"], line["p2"])
    count_report = metrics.counting_report(line["expected_crossings"], counted["events"])

    # Fragmentation, stated plainly: how many real vehicles got more than one predicted ID?
    gt_ids = sorted({o["track_id"] for frame in gt_objects for o in frame})
    ids_per_gt: dict[int, set[int]] = {gid: set() for gid in gt_ids}
    for frame_preds, frame_gt in zip(predictions, gt_objects):
        for pred in frame_preds:
            best, best_id = 0.0, None
            for obj in frame_gt:
                value = metrics.iou(pred["box"], obj["box"])
                if value > best:
                    best, best_id = value, obj["track_id"]
            if best_id is not None and best >= 0.3:
                ids_per_gt[best_id].add(int(pred["track_id"]))
    fragmented = {gid: sorted(ids) for gid, ids in ids_per_gt.items() if len(ids) > 1}

    detection_quality = support.detection_scores(name, records)
    return {
        "video": name,
        "frames": len(predictions),
        "detection": detection_quality,
        "tracking": track_report,
        "unique_tracks": unique,
        "counting": count_report,
        "counts": counted["counts"],
        "flow": counting.flow_summary(counted["counts"],
                                      duration_s=len(predictions) / support.scene(name)["fps"]),
        "speeds": counting.speed_estimates(predictions, fps=support.scene(name)["fps"]),
        "gt_vehicles": len(gt_ids),
        "gt_ids_per_vehicle": {int(k): sorted(v) for k, v in ids_per_gt.items()},
        "fragmented_vehicles": {int(k): v for k, v in fragmented.items()},
        "predictions": predictions,
        "records": records,
        "line": line,
    }


def write_tracked_video(result: dict, *, out_name: str) -> Path:
    """Draw boxes, track IDs, trails, and the counting line onto the source video."""
    name = result["video"]
    source = support.video_path(name)
    info = video.probe(source)
    out_path = support.OUT / out_name
    p1, p2 = result["line"]["p1"], result["line"]["p2"]

    # Trails are rebuilt from the predictions rather than stored in the tracker: the drawing
    # code needs a short window of history, and keeping that out of the tracker keeps the
    # tracker's state minimal.
    history: dict[int, list[tuple[float, float]]] = {}
    counter = counting.LineCounter(p1, p2)
    running = [0]
    frames_written = 0
    with video.VideoWriter(out_path, info.fps, (info.width, info.height)) as writer:
        for (_, _, frame), predictions in zip(
                video.iter_frames(source, limit=result["frames"]), result["predictions"]):
            for pred in predictions:
                x1, y1, x2, y2 = pred["box"]
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                trail = history.setdefault(int(pred["track_id"]), [])
                trail.append((cx, cy))
                if len(trail) > 16:
                    trail.pop(0)
            counter.update(predictions, frames_written)
            drawn = video.draw_trails(frame, list(history.values()))
            cv2.line(drawn, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (0, 215, 255), 2)
            cv2.putText(drawn, f"counted so far {running[0]}",
                        (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 215, 255), 2)
            running[0] = len(counter.events)
            drawn = video.annotate_frame(
                drawn, [p["box"] for p in predictions],
                [f"#{p['track_id']} {p['class']}" for p in predictions],
                colour=(80, 200, 120))
            writer.write(drawn)
            frames_written += 1
    result["tracked_video"] = out_name
    result["tracked_frames"] = frames_written
    return out_path


def max_age_sweep(name: str, model, ages: list[int]) -> list[dict]:
    """How long a track may coast before it is retired: the occlusion trade-off, measured."""
    records = support.detect_scene(name, model)
    detections = detect.to_metric_detections(records)
    gt_objects = [g["objects"] for g in support.scene(name)["frames_gt"]]
    line = support.counting_truth(name)
    rows = []
    for age in ages:
        predictions = tracking.track_detections(detections, max_age=age)
        report = tracking.tracker_report(predictions, gt_objects)
        count_report = metrics.counting_report(
            line["expected_crossings"],
            counting.run_counter(predictions, line["p1"], line["p2"])["events"])
        rows.append({
            "max_age": age,
            "mota": report["mota"],
            "id_switches": report["id_switches"],
            "unique_tracks": tracking.unique_track_count(predictions)["unique_tracks"],
            "count_error": count_report["absolute_error"],
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--video", default="street_day")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-age", type=int, default=6)
    parser.add_argument("--selftest", action="store_true", help="checks only, no video output")
    args = parser.parse_args()
    # The whole clip, even in the smoke test: the crossing counts are asserted
    # against ground truth, and a truncated clip cannot reach them. Processing
    # the full street clip takes a few seconds, so there is nothing to save.
    limit = args.limit
    draw = not args.selftest

    support.rule("detector")
    model, info = support.train_tiny_detector(log=False)
    print(f"  TinyDetector {'loaded from cache' if info['cached'] else 'trained from scratch'}"
          f"  ({info['cache_key']})")
    print(f"  parameters : {support.detector_params(model):,}")
    print("  trained on : street_day + street_dusk frames (train split)")
    print("  note       : results on street_day are in-domain and therefore optimistic;")
    print("               Lab 4 evaluates on videos the model has never seen.")

    support.rule(f"pipeline on {args.video}")
    result = pipeline(args.video, model, limit=limit, max_age=args.max_age)
    d, t = result["detection"], result["tracking"]
    print(f"  frames     : {result['frames']}")
    print(f"  detection  : mAP@0.5 {d['map50']:.3f}  precision {d['precision']:.3f}  "
          f"recall {d['recall']:.3f}")
    print(f"  tracking   : MOTA {t['mota']:.3f}  ID switches {t['id_switches']}  "
          f"fragments {t['fragments']}  FP {t['false_positives']}  FN {t['false_negatives']}")
    print(f"  identities : {result['unique_tracks']['unique_tracks']} predicted tracks for "
          f"{result['gt_vehicles']} real vehicles")
    if result["fragmented_vehicles"]:
        print("  fragmented : vehicles that got more than one ID: "
              f"{result['fragmented_vehicles']}")

    support.rule("counting")
    c = result["counting"]
    support.table([{"class:direction": k, "expected": v["expected"], "counted": v["counted"],
                    "error": v["counted"] - v["expected"]}
                   for k, v in c["per_class_direction"].items()],
                  ["class:direction", "expected", "counted", "error"])
    print(f"  total      : counted {c['counted_total']} of {c['expected_total']} "
          f"(cell error {c['absolute_error']}, exact {c['exact']})")
    if c["counted_total"] == c["expected_total"] and c["absolute_error"]:
        print("  note       : the total is right but some vehicles are filed under the wrong")
        print("               class or direction - a car counted as a truck. A dashboard")
        print("               would show a correct total and a wrong breakdown.")
    print(f"  flow       : {result['flow']['rate_per_s']} vehicles/s over "
          f"{result['flow']['duration_s']} s -> {result['flow']['per_hour']} per hour "
          "(extrapolated, not a forecast)")
    if result["speeds"]["tracks_measured"]:
        print(f"  speed      : median {result['speeds']['median_px_per_s']} px/s across "
              f"{result['speeds']['tracks_measured']} tracks "
              "(no metres: the camera is uncalibrated)")

    if draw:
        out = write_tracked_video(result, out_name=f"tracked_{args.video}.mp4")
        print(f"  video      : {out.name} ({result['tracked_frames']} frames)")

    support.rule("limitations: occlusion, camera movement, fragmentation")
    rows = []
    for name in ["street_day", "street_crowd", "street_shake"]:
        other = result if name == args.video else pipeline(name, model, max_age=args.max_age)
        rows.append({
            "video": name,
            "vehicles": other["gt_vehicles"],
            "tracks": other["unique_tracks"]["unique_tracks"],
            "id_switches": other["tracking"]["id_switches"],
            "mota": other["tracking"]["mota"],
            "counted": other["counting"]["counted_total"],
            "expected": other["counting"]["expected_total"],
        })
    support.table(rows, ["video", "vehicles", "tracks", "id_switches", "mota", "counted",
                         "expected"])
    print("  crowd   : more vehicles per frame and real overlap -> more ID switches and")
    print("            more tracks than vehicles; a count that relies on IDs drifts up.")
    print("  shake   : every box shifts with the camera, so association sees motion. The")
    print("            usual fixes are frame-differencing the background or tracking the")
    print("            dominant global motion; neither is free.")

    support.rule("max_age sweep (how long a track may coast)")
    sweep = max_age_sweep("street_crowd", model, [2, 6, 12, 20])
    support.table(sweep, ["max_age", "mota", "id_switches", "unique_tracks", "count_error"])
    print("  Too small: an occluded vehicle is retired and re-created with a new ID.")
    print("  Too large: tracks survive after their vehicle has left frame, and a stale")
    print("  track can steal the next vehicle's detections. Six frames at 10 fps is 0.6 s,")
    print("  which is about as long as this footage hides a car behind a bus.")

    results: list[bool] = []
    results.append(support.check("detector found most vehicles in-domain",
                                 d["map50"] > 0.5, f"mAP {d['map50']:.3f}"))
    results.append(support.check("tracking beats 'no tracker' (MOTA > 0)",
                                 t["mota"] > 0.0, f"MOTA {t['mota']:.3f}"))
    results.append(support.check("total crossings match ground truth",
                                 c["counted_total"] == c["expected_total"],
                                 f"{c['counted_total']} vs {c['expected_total']}"))
    # The total can be right while individual class:direction cells are wrong, because the
    # detector confuses car and truck on a few frames. That is worth bounding, not hiding.
    results.append(support.check("per-class attribution is within two crossings",
                                 c["absolute_error"] <= 2,
                                 f"cell error {c['absolute_error']}"))
    results.append(support.check("every frame of the video was processed",
                                 result["frames"] == support.scene(args.video)["frames"]
                                 or limit is not None))
    if draw:
        out = support.OUT / result["tracked_video"]
        results.append(support.check("tracked video is readable",
                                     out.exists() and video.probe(out).frame_count > 0,
                                     out.name))
    results.append(support.check("crowd scene is harder than the clean scene",
                                 rows[1]["id_switches"] >= rows[0]["id_switches"],
                                 f"{rows[1]['id_switches']} vs {rows[0]['id_switches']} IDs"))

    stored = {k: v for k, v in result.items() if k not in {"predictions", "records"}}
    support.write_report("lab3_tracking.json", {
        "lab": "vehicle detection, tracking, and counting",
        "detector": info,
        "primary": stored,
        "limitations": rows,
        "max_age_sweep_crowd": sweep,
        "checks": results,
    })
    return support.all_checks(results)


if __name__ == "__main__":
    raise SystemExit(main())
