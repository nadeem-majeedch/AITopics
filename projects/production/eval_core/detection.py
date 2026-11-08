"""Object-detection metrics: IoU, matching, precision/recall, AP, and mAP.

Detection evaluation is not classification with extra steps. A prediction is
right only if its class matches *and* its box overlaps the ground truth enough,
and one ground-truth box may be matched by only one prediction. The matching
rule is part of the metric, so it is a parameter here, never an assumption.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Sequence

import numpy as np


def iou(box_a: Sequence[float], box_b: Sequence[float]) -> float:
    """Intersection over union for two [x1, y1, x2, y2] boxes."""
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    inter_x1, inter_y1 = max(ax1, bx1), max(ay1, by1)
    inter_x2, inter_y2 = min(ax2, bx2), min(ay2, by2)
    inter_w, inter_h = max(0.0, inter_x2 - inter_x1), max(0.0, inter_y2 - inter_y1)
    intersection = inter_w * inter_h
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - intersection
    return float(intersection / union) if union > 0 else 0.0


def _boxes(record: dict, field: str) -> list[dict]:
    return record.get(field) or []


def match_image(gt_boxes: Sequence[dict], predictions: Sequence[dict], iou_threshold: float = 0.5,
                score_threshold: float = 0.0) -> dict:
    """Greedy one-to-one matching inside a single image.

    Predictions are considered best-first; each ground-truth box can be claimed
    once. Greedy matching is the convention, and it is why a duplicate detection
    on a true object counts as a false positive rather than another true positive.
    """
    kept = sorted((p for p in predictions if p["score"] >= score_threshold),
                  key=lambda p: -p["score"])
    claimed = [False] * len(gt_boxes)
    true_positives = 0
    details = []
    for prediction in kept:
        best_index, best_iou = -1, 0.0
        for index, truth in enumerate(gt_boxes):
            if claimed[index] or truth["class"] != prediction["class"]:
                continue
            overlap = iou(truth["box"], prediction["box"])
            if overlap > best_iou:
                best_index, best_iou = index, overlap
        if best_index >= 0 and best_iou >= iou_threshold:
            claimed[best_index] = True
            true_positives += 1
            details.append({"prediction": prediction, "matched": True, "iou": best_iou})
        else:
            details.append({"prediction": prediction, "matched": False, "iou": best_iou})
    return {
        "tp": true_positives,
        "fp": len(kept) - true_positives,
        "fn": len(gt_boxes) - true_positives,
        "details": details,
    }


def count_ground_truth(gt_images: Sequence[dict], cls: str) -> int:
    return sum(1 for image in gt_images for box in _boxes(image, "boxes") if box["class"] == cls)


def _class_predictions(gt_images: Sequence[dict], pred_images: Sequence[dict],
                       cls: str) -> list[tuple[float, str, Sequence[float]]]:
    """All predictions of one class, sorted by score, with their image id."""
    truth_by_image = {image["image_id"]: image for image in gt_images}
    rows = []
    for image in pred_images:
        if image["image_id"] not in truth_by_image:
            continue
        for detection in _boxes(image, "detections"):
            if detection["class"] == cls:
                rows.append((float(detection["score"]), image["image_id"], detection["box"]))
    rows.sort(key=lambda row: -row[0])
    return rows


def average_precision(gt_images: Sequence[dict], pred_images: Sequence[dict], cls: str,
                      iou_threshold: float = 0.5) -> dict:
    """All-point interpolated AP for one class at one IoU threshold."""
    total_gt = count_ground_truth(gt_images, cls)
    if total_gt == 0:
        return {"class": cls, "ap": float("nan"), "ground_truth": 0, "predictions": 0}

    predictions = _class_predictions(gt_images, pred_images, cls)
    truth_by_image = {image["image_id"]: image for image in gt_images}
    claimed: dict[str, list[bool]] = {}
    for image in gt_images:
        claimed[image["image_id"]] = [False] * sum(
            1 for box in _boxes(image, "boxes") if box["class"] == cls
        )

    matched_truth: dict[str, list[dict]] = {
        image["image_id"]: [box for box in _boxes(image, "boxes") if box["class"] == cls]
        for image in gt_images
    }

    tp_flags: list[int] = []
    for score, image_id, box in predictions:
        truths = matched_truth[image_id]
        flags = claimed[image_id]
        best_index, best_iou = -1, 0.0
        for index, truth in enumerate(truths):
            if flags[index]:
                continue
            overlap = iou(truth["box"], box)
            if overlap > best_iou:
                best_index, best_iou = index, overlap
        if best_index >= 0 and best_iou >= iou_threshold:
            flags[best_index] = True
            tp_flags.append(1)
        else:
            tp_flags.append(0)

    if not tp_flags:
        return {"class": cls, "ap": 0.0, "ground_truth": total_gt, "predictions": 0}

    tp = np.cumsum(tp_flags)
    fp = np.cumsum(1 - np.asarray(tp_flags))
    precision = tp / np.maximum(tp + fp, 1)
    recall = tp / total_gt

    # All-point interpolation: precision is made monotone from the right.
    precision_envelope = np.maximum.accumulate(precision[::-1])[::-1]
    ap = float(np.sum(np.diff(np.concatenate([[0.0], recall])) * precision_envelope))
    return {"class": cls, "ap": ap, "ground_truth": total_gt, "predictions": len(tp_flags)}


def mean_ap(gt_images: Sequence[dict], pred_images: Sequence[dict], classes: Sequence[str],
            iou_threshold: float = 0.5) -> dict:
    per_class = [average_precision(gt_images, pred_images, cls, iou_threshold) for cls in classes]
    valid = [item["ap"] for item in per_class if not np.isnan(item["ap"])]
    return {
        "iou": iou_threshold,
        "per_class": per_class,
        "mAP": float(np.mean(valid)) if valid else float("nan"),
    }


def precision_recall_at(gt_images: Sequence[dict], pred_images: Sequence[dict], classes: Sequence[str],
                        iou_threshold: float = 0.5, score_threshold: float = 0.5) -> dict:
    """Operating-point metrics at one confidence threshold, pooled over classes."""
    tp = fp = fn = 0
    for truth_image, pred_image in zip(gt_images, pred_images):
        truths = [box for box in _boxes(truth_image, "boxes") if box["class"] in classes]
        predictions = [d for d in _boxes(pred_image, "detections") if d["class"] in classes]
        result = match_image(truths, predictions, iou_threshold, score_threshold)
        tp += result["tp"]
        fp += result["fp"]
        fn += result["fn"]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"score_threshold": score_threshold, "tp": tp, "fp": fp, "fn": fn,
            "precision": precision, "recall": recall, "f1": f1}


def threshold_sweep(gt_images: Sequence[dict], pred_images: Sequence[dict], classes: Sequence[str],
                    iou_threshold: float = 0.5,
                    thresholds: Sequence[float] = (0.2, 0.3, 0.4, 0.5, 0.6, 0.7)) -> list[dict]:
    return [precision_recall_at(gt_images, pred_images, classes, iou_threshold, threshold)
            for threshold in thresholds]


def class_balance(gt_images: Sequence[dict], classes: Sequence[str]) -> dict:
    counts = defaultdict(int)
    for image in gt_images:
        for box in _boxes(image, "boxes"):
            if box["class"] in classes:
                counts[box["class"]] += 1
    return {cls: counts[cls] for cls in classes}
