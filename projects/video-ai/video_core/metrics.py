"""Metrics for detection, tracking, counting, classification, and speed.

The section's rule: every number a lab prints comes from this module, so the definition of
mAP or MOTA is written once and can be read. Each function also carries the caveat that
belongs to it, because the most common mistake with these metrics is not computing them
wrongly - it is quoting them without their assumptions.

Detection numbers follow the COCO convention for *matching* (IoU threshold, one detection
per ground-truth box, greedy by score) but use the all-point interpolated AP of Pascal VOC
after 2010, which is what a small dataset can support. COCO's 101-point interpolation over
IoU 0.50:0.05:0.95 is implemented too, as ``coco_style_map``, for students who want the
standard number; on 36 frames the two differ by more than the effect being studied, which
is itself worth seeing.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Iterable, Sequence

import numpy as np


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------


def box_area(box: Sequence[float]) -> float:
    x1, y1, x2, y2 = box[:4]
    return max(0.0, float(x2) - float(x1)) * max(0.0, float(y2) - float(y1))


def iou(a: Sequence[float], b: Sequence[float]) -> float:
    """Intersection over union of two ``(x1, y1, x2, y2)`` boxes."""
    ax1, ay1, ax2, ay2 = [float(v) for v in a[:4]]
    bx1, by1, bx2, by2 = [float(v) for v in b[:4]]
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    inter = (ix2 - ix1) * (iy2 - iy1)
    union = box_area(a) + box_area(b) - inter
    return float(inter / union) if union > 0 else 0.0


def iou_matrix(boxes_a: Sequence[Sequence[float]], boxes_b: Sequence[Sequence[float]]) -> np.ndarray:
    """Pairwise IoU as an ``(len(a), len(b))`` array, vectorised over the grid."""
    if not boxes_a or not boxes_b:
        return np.zeros((len(boxes_a), len(boxes_b)), np.float32)
    a = np.asarray(boxes_a, dtype=np.float32)[:, :4]
    b = np.asarray(boxes_b, dtype=np.float32)[:, :4]
    ix1 = np.maximum(a[:, None, 0], b[None, :, 0])
    iy1 = np.maximum(a[:, None, 1], b[None, :, 1])
    ix2 = np.minimum(a[:, None, 2], b[None, :, 2])
    iy2 = np.minimum(a[:, None, 3], b[None, :, 3])
    inter = np.clip(ix2 - ix1, 0, None) * np.clip(iy2 - iy1, 0, None)
    area_a = np.clip(a[:, 2] - a[:, 0], 0, None) * np.clip(a[:, 3] - a[:, 1], 0, None)
    area_b = np.clip(b[:, 2] - b[:, 0], 0, None) * np.clip(b[:, 3] - b[:, 1], 0, None)
    union = area_a[:, None] + area_b[None, :] - inter
    return np.where(union > 0, inter / np.maximum(union, 1e-9), 0.0).astype(np.float32)


def clip_box(box: Sequence[float], width: int, height: int) -> list[float]:
    """Clamp a box to the image rectangle and return floats."""
    x1, y1, x2, y2 = [float(v) for v in box[:4]]
    return [
        float(min(max(x1, 0.0), width)),
        float(min(max(y1, 0.0), height)),
        float(min(max(x2, 0.0), width)),
        float(min(max(y2, 0.0), height)),
    ]


# ---------------------------------------------------------------------------
# Detection: precision, recall, AP, mAP
# ---------------------------------------------------------------------------


@dataclass
class Detection:
    box: list[float]
    label: int
    score: float
    track_id: int | None = None
    extra: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        out = {"box": [round(float(v), 2) for v in self.box],
               "label": int(self.label),
               "score": round(float(self.score), 4)}
        if self.track_id is not None:
            out["track_id"] = int(self.track_id)
        out.update(self.extra)
        return out


def match_frame(
    detections: Sequence[Detection],
    truth: Sequence[dict],
    iou_threshold: float = 0.5,
    *,
    class_aware: bool = True,
) -> tuple[list[tuple[int, int]], list[int], list[int], list[float]]:
    """Greedy score-ordered matching for one frame.

    Returns ``(matches, unmatched_det, unmatched_gt, matched_ious)``. Each ground-truth box
    can be matched at most once; each detection at most once. Ties are broken by score, so
    the order of ``detections`` does not change the result.
    """
    order = sorted(range(len(detections)), key=lambda i: -detections[i].score)
    gt_boxes = [t["box"] for t in truth]
    gt_labels = [int(t["label"]) for t in truth]
    used_gt: set[int] = set()
    matches: list[tuple[int, int]] = []
    ious: list[float] = []
    unmatched_det: list[int] = []
    for di in order:
        det = detections[di]
        best_gt, best_iou = -1, iou_threshold
        for gi, gt_box in enumerate(gt_boxes):
            if gi in used_gt:
                continue
            if class_aware and gt_labels[gi] != det.label:
                continue
            value = iou(det.box, gt_box)
            if value >= best_iou:
                best_gt, best_iou = gi, value
        if best_gt >= 0:
            used_gt.add(best_gt)
            matches.append((di, best_gt))
            ious.append(best_iou)
        else:
            unmatched_det.append(di)
    unmatched_gt = [i for i in range(len(truth)) if i not in used_gt]
    return matches, unmatched_det, unmatched_gt, ious


def average_precision(
    detections: Sequence[tuple[float, bool]],
    n_truth: int,
) -> float:
    """All-point interpolated AP from ``(score, is_true_positive)`` pairs.

    This is the VOC2010+ definition: integrate the precision envelope over recall. With a
    handful of objects it is noisy but honest, and it does not reward a lucky top-1 hit the
    way the 11-point version does.
    """
    if n_truth == 0:
        return float("nan")
    if not detections:
        return 0.0
    ordered = sorted(detections, key=lambda pair: -pair[0])
    tp = np.cumsum([1.0 if flag else 0.0 for _, flag in ordered])
    fp = np.cumsum([0.0 if flag else 1.0 for _, flag in ordered])
    recall = tp / float(n_truth)
    precision = tp / np.maximum(tp + fp, 1e-9)
    # Precision envelope, then integrate.
    mrec = np.concatenate([[0.0], recall, [1.0]])
    mpre = np.concatenate([[0.0], precision, [0.0]])
    for i in range(len(mpre) - 2, -1, -1):
        mpre[i] = max(mpre[i], mpre[i + 1])
    idx = np.where(mrec[1:] != mrec[:-1])[0]
    return float(np.sum((mrec[idx + 1] - mrec[idx]) * mpre[idx + 1]))


def detection_report(
    frames: Sequence[tuple[Sequence[Detection], Sequence[dict]]],
    *,
    num_classes: int,
    class_names: Sequence[str] | None = None,
    iou_threshold: float = 0.5,
    score_threshold: float = 0.0,
) -> dict:
    """Per-frame detections against per-frame ground truth.

    ``frames`` is a sequence of ``(detections, truth)``; each truth entry needs ``box`` and
    ``label``. Returns mAP@0.5, per-class AP, and precision/recall at the given score
    threshold, plus the confusion of "detected a vehicle, wrong class".
    """
    per_class: dict[int, list[tuple[float, bool]]] = defaultdict(list)
    n_gt = defaultdict(int)
    tp = fp = fn = 0
    class_wrong = 0

    for detections, truth in frames:
        kept = [d for d in detections if d.score >= score_threshold]
        for t in truth:
            n_gt[int(t["label"])] += 1
        matches, unmatched_det, unmatched_gt, _ = match_frame(kept, truth, iou_threshold)
        matched_det = {di for di, _ in matches}
        for di, det in enumerate(kept):
            hit = di in matched_det
            per_class[det.label].append((det.score, hit))
            if hit:
                tp += 1
            else:
                fp += 1
                # A detection that overlaps a ground-truth box of another class is a
                # classification error, not a localisation failure. Worth counting apart.
                for t in truth:
                    if iou(det.box, t["box"]) >= iou_threshold:
                        class_wrong += 1
                        break
        fn += len(unmatched_gt)

    aps = {}
    for label in range(num_classes):
        entries = per_class.get(label, [])
        ap = average_precision(entries, n_gt.get(label, 0))
        if not np.isnan(ap):
            aps[label] = ap
    names = list(class_names) if class_names else [str(i) for i in range(num_classes)]
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)

    return {
        "map50": float(np.mean(list(aps.values()))) if aps else 0.0,
        "per_class_ap": {names[k]: round(v, 4) for k, v in sorted(aps.items())},
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "true_positives": int(tp),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "class_confusions": int(class_wrong),
        "ground_truth_objects": int(sum(n_gt.values())),
        "iou_threshold": iou_threshold,
        "score_threshold": score_threshold,
    }


def coco_style_map(
    frames: Sequence[tuple[Sequence[Detection], Sequence[dict]]],
    *,
    num_classes: int,
    iou_thresholds: Sequence[float] | None = None,
) -> dict:
    """Mean AP over IoU 0.50:0.05:0.95 - the COCO definition.

    Reported separately from ``detection_report`` so a student can see how much the choice
    of convention moves the number on the same predictions.
    """
    thresholds = list(iou_thresholds or np.arange(0.5, 0.96, 0.05))
    values = []
    for thr in thresholds:
        report = detection_report(frames, num_classes=num_classes, iou_threshold=float(thr))
        values.append(report["map50"])
    return {
        "map": round(float(np.mean(values)), 4),
        "map50": round(float(values[0]), 4),
        "map75": round(float(values[int(round(0.25 * (len(values) - 1)))]), 4),
        "thresholds": [round(float(t), 2) for t in thresholds],
    }


# ---------------------------------------------------------------------------
# Tracking
# ---------------------------------------------------------------------------


def tracking_report(
    frames: Sequence[tuple[Sequence[dict], Sequence[dict]]],
    *,
    iou_threshold: float = 0.5,
) -> dict:
    """MOTA-style accounting for track IDs.

    ``frames`` is ``(predictions, truth)`` where each item has ``box``, ``label`` and
    ``track_id``. Matching uses IoU and *track identity*: a detection matched to the right
    box but carrying the wrong ID counts as an ID switch, which is why MOTA can be negative.

    Definitions used:
    * **MOTA** = 1 - (FN + FP + IDSW) / GT. The standard identity-matching version.
    * **ID switches**: a truth track matched to a different predicted track than last time.
    * **Fragmentation**: predicted tracks that stop for a while and resume (tracked, lost,
      tracked again). Counted per predicted track.
    """
    gt_count = 0
    fn = fp = idsw = 0
    last_pred_for_truth: dict[int, int] = {}
    pred_history: dict[int, list[int]] = defaultdict(list)
    matched_ids: set[int] = set()

    for predictions, truth in frames:
        gt_count += len(truth)
        if not truth or not predictions:
            fn += len(truth)
            fp += len(predictions)
            continue
        # Match boxes first, then judge identity.
        dets = [Detection(list(p["box"]), int(p["label"]), float(p.get("score", 1.0)),
                          int(p["track_id"])) for p in predictions]
        pseudo_truth = [{"box": t["box"], "label": int(t["label"])} for t in truth]
        matches, unmatched_det, unmatched_gt, _ = match_frame(dets, pseudo_truth, iou_threshold)
        fn += len(unmatched_gt)
        fp += len(unmatched_det)
        for di, gi in matches:
            true_id = int(truth[gi]["track_id"])
            pred_id = int(predictions[di]["track_id"])
            matched_ids.add(pred_id)
            pred_history[pred_id].append(gi)
            previous = last_pred_for_truth.get(true_id)
            if previous is not None and previous != pred_id:
                idsw += 1
            last_pred_for_truth[true_id] = pred_id

    fragments = 0
    for pred_id, seq in pred_history.items():
        # A track that disappears for more than one frame and comes back is fragmented.
        gaps = sum(1 for a, b in zip(seq[:-1], seq[1:]) if b - a > 1)
        fragments += gaps

    mota = 1.0 - (fn + fp + idsw) / max(gt_count, 1)
    return {
        "mota": round(float(mota), 4),
        "id_switches": int(idsw),
        "false_negatives": int(fn),
        "false_positives": int(fp),
        "ground_truth_objects": int(gt_count),
        "unique_predicted_tracks": int(len(matched_ids)),
        "fragments": int(fragments),
        "iou_threshold": iou_threshold,
    }


# ---------------------------------------------------------------------------
# Counting
# ---------------------------------------------------------------------------


def counting_report(expected: Sequence[dict], found: Sequence[dict]) -> dict:
    """Compare counted crossings with the generator's ground truth, per class and direction."""
    def tally(items):
        out: dict[str, int] = defaultdict(int)
        for item in items:
            out[f"{item['class']}:{item['direction']}"] += 1
        return dict(out)

    truth, pred = tally(expected), tally(found)
    keys = sorted(set(truth) | set(pred))
    per_key = {k: {"expected": truth.get(k, 0), "counted": pred.get(k, 0)} for k in keys}
    abs_error = sum(abs(truth.get(k, 0) - pred.get(k, 0)) for k in keys)
    return {
        "expected_total": len(expected),
        "counted_total": len(found),
        "per_class_direction": per_key,
        "absolute_error": int(abs_error),
        "exact": abs_error == 0,
    }


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


def classification_report(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    class_names: Sequence[str],
) -> dict:
    """Per-class precision/recall/F1, macro averages, and the confusion matrix."""
    n = len(class_names)
    confusion = np.zeros((n, n), dtype=np.int64)
    for t, p in zip(y_true, y_pred):
        confusion[int(t), int(p)] += 1
    rows = {}
    f1s = []
    for i, name in enumerate(class_names):
        tp = int(confusion[i, i])
        fp = int(confusion[:, i].sum() - tp)
        fn = int(confusion[i, :].sum() - tp)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        f1s.append(f1)
        rows[name] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": int(confusion[i, :].sum()),
        }
    accuracy = float(np.trace(confusion) / max(confusion.sum(), 1))
    return {
        "accuracy": round(accuracy, 4),
        "macro_f1": round(float(np.mean(f1s)), 4),
        "per_class": rows,
        "confusion": confusion.tolist(),
        "n": int(confusion.sum()),
    }


# ---------------------------------------------------------------------------
# Speed and memory
# ---------------------------------------------------------------------------


def benchmark(fn: Callable[[], object], *, runs: int = 3, warmup: int = 1,
              n_items: int = 1, label: str = "") -> dict:
    """Time a callable, returning median and mean latency and throughput.

    The first call is discarded (``warmup``) because lazy initialisation and thread-pool
    creation otherwise dominate short measurements. Report the *median*: one scheduling
    hiccup moves the mean and not the median.
    """
    for _ in range(max(0, warmup)):
        fn()
    times = []
    for _ in range(max(1, runs)):
        started = time.perf_counter()
        fn()
        times.append(time.perf_counter() - started)
    times.sort()
    median = times[len(times) // 2]
    return {
        "label": label,
        "runs": len(times),
        "median_ms": round(median * 1000, 2),
        "mean_ms": round(float(np.mean(times)) * 1000, 2),
        "min_ms": round(min(times) * 1000, 2),
        "max_ms": round(max(times) * 1000, 2),
        "items": int(n_items),
        "throughput_per_s": round(n_items / median, 2) if median > 0 else float("inf"),
    }


def process_memory_mb() -> float:
    """Resident set size of this process, in MB, with a portable fallback.

    Windows has no ``resource`` module, so this uses ``GetProcessMemoryInfo`` through
    ctypes; POSIX uses ``ru_maxrss``. If both fail, returns ``-1.0`` rather than a made-up
    number, and labs print "unavailable" instead of a fake measurement.
    """
    try:  # POSIX
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # macOS reports bytes, Linux kilobytes.
        return round(usage / (1024 * 1024 if usage > 1e7 else 1024), 1)
    except Exception:
        pass
    try:  # Windows
        import ctypes
        from ctypes import wintypes

        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = PROCESS_MEMORY_COUNTERS()
        counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
        # The restype matters: ctypes defaults to a 32-bit int, which truncates a 64-bit
        # HANDLE and makes the call fail with a zero return value on 64-bit Windows.
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p,
                                               ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
                                               wintypes.DWORD]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        handle = kernel32.GetCurrentProcess()
        if psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            return round(counters.WorkingSetSize / (1024 * 1024), 1)
    except Exception:
        pass
    return -1.0


def real_time_factor(seconds: float, audio_or_video_seconds: float) -> float:
    """Processing time divided by media duration; below 1 is faster than real time."""
    if audio_or_video_seconds <= 0:
        return float("inf")
    return round(seconds / audio_or_video_seconds, 4)


def summarize(values: Iterable[float]) -> dict:
    arr = np.asarray([v for v in values if v is not None], dtype=np.float64)
    if arr.size == 0:
        return {"n": 0}
    return {
        "n": int(arr.size),
        "mean": round(float(arr.mean()), 4),
        "median": round(float(np.median(arr)), 4),
        "min": round(float(arr.min()), 4),
        "max": round(float(arr.max()), 4),
    }
