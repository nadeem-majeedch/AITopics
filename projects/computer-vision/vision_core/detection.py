"""Decoding a heatmap into boxes, and evaluating a detector over thresholds.

A detector's output tensor is not a detection. This module turns peaks into
boxes, removes duplicates, and then scores the result at several confidence
thresholds - because "the precision is 0.8" is meaningless until you say at which
threshold and on which classes.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
import torch
import torch.nn.functional as F

from .annotations import Annotation, clip_box
from .datasets import ImageRecord
from .metrics import (
    DetectionResult,
    evaluate_detections,
    greedy_match,
    mean_average_precision,
    non_max_suppression,
    pr_curve,
)
from .training import prepare_inputs


def decode_heatmap(
    heat_logits: np.ndarray,
    size_pred: np.ndarray,
    *,
    stride: int = 4,
    width: int = 64,
    height: int = 64,
    score_threshold: float = 0.3,
    max_detections: int = 10,
    nms_iou: float = 0.45,
) -> list[Annotation]:
    """Convert one image's heatmap logits into annotated boxes.

    Steps, in order: sigmoid -> 3x3 local maxima -> keep cells above threshold ->
    read the size head at each cell -> build boxes -> NMS. Every step is needed;
    skipping local maxima yields a box per pixel of the blob.
    """
    heat = 1.0 / (1.0 + np.exp(-np.asarray(heat_logits, dtype=np.float64)))
    if heat.ndim == 2:
        heat = heat[None]
    n_classes, gh, gw = heat.shape

    # Local maxima: a cell is a peak if it equals the max of its 3x3 neighbourhood.
    peaks = np.zeros_like(heat, dtype=bool)
    for c in range(n_classes):
        plane = heat[c]
        padded = np.pad(plane, 1, mode="constant", constant_values=-1.0)
        is_peak = np.ones_like(plane, dtype=bool)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                is_peak &= plane >= padded[1 + dy : 1 + dy + gh, 1 + dx : 1 + dx + gw]
        # Ties must not count as peaks. A flat or saturating map makes every cell
        # equal to its neighbours; with >= alone that is a box per cell.
        ties = np.zeros_like(plane, dtype=np.int32)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                ties += (plane == padded[1 + dy : 1 + dy + gh, 1 + dx : 1 + dx + gw]).astype(np.int32)
        peaks[c] = is_peak & (ties == 0)

    candidates: list[Annotation] = []
    for c in range(n_classes):
        coords = np.argwhere(peaks[c] & (heat[c] >= score_threshold))
        if coords.size == 0:
            continue
        scores = heat[c][coords[:, 0], coords[:, 1]]
        order = np.argsort(-scores)[:max_detections]
        for pick in order:
            gy, gx = int(coords[pick][0]), int(coords[pick][1])
            bw = float(np.clip(size_pred[0, gy, gx] * width, 2.0, width))
            bh = float(np.clip(size_pred[1, gy, gx] * height, 2.0, height))
            cx = (gx + 0.5) * stride
            cy = (gy + 0.5) * stride
            box = clip_box((cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2), width, height)
            candidates.append(Annotation(class_id=c, box=box, score=float(scores[pick])))

    return non_max_suppression(candidates, iou_threshold=nms_iou)[:max_detections]


def predict_records(
    model: torch.nn.Module,
    records: Sequence[ImageRecord],
    *,
    stride: int = 4,
    score_threshold: float = 0.3,
    nms_iou: float = 0.45,
    batch_size: int = 16,
) -> list[DetectionResult]:
    """Run the detector over annotated records and return predictions vs truth."""
    model.eval()
    images = np.stack([r.image for r in records])
    x = prepare_inputs(images)
    results: list[DetectionResult] = []

    with torch.no_grad():
        for start in range(0, len(x), batch_size):
            chunk = x[start : start + batch_size]
            heat, size = model(chunk)  # (N, C, gh, gw), (N, 2, gh, gw)
            heat_np = heat.cpu().numpy()
            size_np = size.cpu().numpy()
            for i in range(chunk.shape[0]):
                rec = records[start + i]
                h, w = rec.image.shape[:2]
                preds = decode_heatmap(
                    heat_np[i],
                    size_np[i],
                    stride=stride,
                    width=w,
                    height=h,
                    score_threshold=score_threshold,
                    nms_iou=nms_iou,
                )
                truth = [Annotation(_class_id(o["class"]), tuple(o["xyxy"])) for o in rec.meta["boxes"]]
                results.append(DetectionResult(predictions=preds, ground_truth=truth))
    return results


def threshold_sweep(
    results: Sequence[DetectionResult],
    class_names: Sequence[str],
    thresholds: Sequence[float] = (0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9),
    iou_threshold: float = 0.5,
) -> list[dict]:
    """Precision, recall, F1, and counts at each score threshold.

    Lowering the threshold raises recall and lowers precision; the sweep makes
    that trade visible instead of leaving students to pick 0.5 by habit.
    """
    rows = []
    for t in thresholds:
        metrics = evaluate_detections(results, class_names, iou_threshold=iou_threshold, score_threshold=float(t))
        rows.append(
            {
                "threshold": float(t),
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1": metrics["f1"],
                "tp": metrics["tp"],
                "fp": metrics["fp"],
                "fn": metrics["fn"],
            }
        )
    return rows


def best_threshold(rows: Sequence[dict], metric: str = "f1") -> dict:
    """The sweep row with the best chosen metric, with ties broken by threshold."""
    if not rows:
        return {}
    return max(rows, key=lambda r: (r[metric], -r["threshold"]))


def detector_report(
    results: Sequence[DetectionResult],
    class_names: Sequence[str],
    thresholds: Sequence[float] = (0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9),
    score_threshold: float = 0.3,
) -> dict:
    """Everything Lab 6 reports: fixed-threshold metrics, sweep, mAP, PR points."""
    at_fixed = evaluate_detections(results, class_names, 0.5, score_threshold)
    sweep = threshold_sweep(results, class_names, thresholds)
    map50 = mean_average_precision(results, class_names, (0.5,))
    map_full = mean_average_precision(results, class_names, tuple(np.arange(0.5, 1.0, 0.05)))
    curve = pr_curve(results, class_names, 0.5)
    return {
        "at_threshold": at_fixed,
        "sweep": sweep,
        "best_f1": best_threshold(sweep, "f1"),
        "map50": map50["map"],
        "map50_95": map_full["map"],
        "per_class_ap50": map50["per_class_ap50"],
        "pr_points": curve,
        "n_images": len(results),
        "n_predictions": sum(len(r.predictions) for r in results),
        "n_ground_truth": sum(len(r.ground_truth) for r in results),
    }


def format_sweep(rows: Sequence[dict]) -> str:
    """Fixed-width table, since the course avoids a table-formatting dependency."""
    header = f"{'thresh':>7} {'precision':>10} {'recall':>8} {'f1':>6} {'tp':>5} {'fp':>5} {'fn':>5}"
    lines = [header, "-" * len(header)]
    for r in rows:
        lines.append(
            f"{r['threshold']:>7.2f} {r['precision']:>10.3f} {r['recall']:>8.3f} {r['f1']:>6.3f} "
            f"{r['tp']:>5d} {r['fp']:>5d} {r['fn']:>5d}"
        )
    return "\n".join(lines)


def _class_id(name: str) -> int:
    from .detection_train import SHAPE_INDEX

    return SHAPE_INDEX[name]
