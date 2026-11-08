"""Detection, segmentation, classification, and face metrics - computed by hand.

Every function here is implemented from the definitions rather than imported
from a framework, because the point of Modules 9, 10, and 11 is that you can
compute these numbers yourself and defend them. The tests in
``tests/test_computer_vision.py`` check them against hand-calculated values.

Definitions used (write these down; they differ between papers):

* **IoU** - intersection area / union area, in pixels, on xyxy boxes.
* **Match** - a prediction matches a ground truth of the same class when their
  IoU is at least the threshold. One ground truth matches at most one prediction
  (greedy by score), which is what COCO and VOC do.
* **AP** - area under the precision-recall curve at one IoU threshold.
* **mAP@0.5** - mean AP across classes at IoU 0.5.
* **mAP@[.5:.95]** - mean over IoU thresholds 0.50, 0.55, ..., 0.95.
* **Dice / IoU (segmentation)** - per-class overlap between predicted and true masks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

import numpy as np

from .annotations import Annotation, Box, box_iou


# ---------------------------------------------------------------------------
# Detection: matching, precision, recall, AP, mAP
# ---------------------------------------------------------------------------


@dataclass
class DetectionResult:
    """Predictions and ground truth for one image."""

    predictions: list[Annotation] = field(default_factory=list)
    ground_truth: list[Annotation] = field(default_factory=list)


def greedy_match(
    predictions: Sequence[Annotation],
    ground_truth: Sequence[Annotation],
    iou_threshold: float = 0.5,
) -> list[tuple[int, int, float]]:
    """Greedily match predictions to ground truth, highest score first.

    Returns ``(prediction_index, gt_index, iou)``. Each ground truth is used at
    most once, so a detector that fires twice on one object gains nothing from
    the second box - it becomes a false positive.
    """
    if not 0.0 <= iou_threshold <= 1.0:
        raise ValueError(f"iou_threshold must be in 0-1, got {iou_threshold}")

    order = sorted(range(len(predictions)), key=lambda i: -predictions[i].score)
    used: set[int] = set()
    matches = []
    for pi in order:
        pred = predictions[pi]
        best_j, best_iou = -1, 0.0
        for gi, gt in enumerate(ground_truth):
            if gi in used or gt.class_id != pred.class_id:
                continue
            iou = box_iou(pred.box, gt.box)
            if iou > best_iou:
                best_j, best_iou = gi, iou
        if best_j >= 0 and best_iou >= iou_threshold:
            used.add(best_j)
            matches.append((pi, best_j, best_iou))
    return matches


def score_image(
    predictions: Sequence[Annotation],
    ground_truth: Sequence[Annotation],
    iou_threshold: float = 0.5,
) -> dict:
    """Per-image true positives, false positives, and false negatives."""
    matches = greedy_match(predictions, ground_truth, iou_threshold)
    tp = len(matches)
    fp = len(predictions) - tp
    fn = len(ground_truth) - tp
    return {"tp": tp, "fp": fp, "fn": fn, "matches": matches}


def precision_recall(tp: int, fp: int, fn: int) -> tuple[float, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return precision, recall


def f1_score(precision: float, recall: float) -> float:
    return 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0


def average_precision(
    scores: Sequence[float],
    true_positives: Sequence[int],
    n_positives: int,
    method: str = "all",
) -> float:
    """Area under the precision-recall curve.

    ``method="all"`` uses the COCO/VOC2010 continuous interpolation: precision is
    made monotone decreasing from the right, then integrated over recall. This
    is the value reported as ``AP`` unless a source says otherwise.
    ``method="11"`` is the older VOC2007 11-point sampling, kept because
    textbooks still quote it and it gives a different number for the same data.
    """
    if n_positives <= 0:
        return 0.0
    scores_arr = np.asarray(scores, dtype=np.float64)
    tp_arr = np.asarray(true_positives, dtype=np.float64)
    if scores_arr.shape != tp_arr.shape:
        raise ValueError("scores and true_positives must have the same length")
    if scores_arr.size == 0:
        return 0.0

    order = np.argsort(-scores_arr, kind="mergesort")
    tp_sorted = tp_arr[order]
    cum_tp = np.cumsum(tp_sorted)
    cum_fp = np.cumsum(1.0 - tp_sorted)
    recall = cum_tp / float(n_positives)
    precision = cum_tp / np.maximum(cum_tp + cum_fp, 1e-12)

    if method == "11":
        ap = 0.0
        for r in np.linspace(0.0, 1.0, 11):
            mask = recall >= r
            ap += (precision[mask].max() if mask.any() else 0.0) / 11.0
        return float(ap)
    if method != "all":
        raise ValueError(f"unknown method {method!r}; use 'all' or '11'")

    mrec = np.concatenate(([0.0], recall, [1.0]))
    mpre = np.concatenate(([0.0], precision, [0.0]))
    for i in range(len(mpre) - 2, -1, -1):
        mpre[i] = max(mpre[i], mpre[i + 1])
    idx = np.where(mrec[1:] != mrec[:-1])[0]
    return float(np.sum((mrec[idx + 1] - mrec[idx]) * mpre[idx + 1]))


def evaluate_detections(
    results: Sequence[DetectionResult],
    class_names: Sequence[str],
    iou_threshold: float = 0.5,
    score_threshold: float = 0.0,
) -> dict:
    """Dataset-level detection metrics at one IoU and one score threshold."""
    tp = fp = fn = 0
    per_class = {name: {"tp": 0, "fp": 0, "fn": 0} for name in class_names}

    for result in results:
        preds = [p for p in result.predictions if p.score >= score_threshold]
        matches = greedy_match(preds, result.ground_truth, iou_threshold)
        matched_pi = {m[0] for m in matches}
        matched_gi = {m[1] for m in matches}
        for pi, pred in enumerate(preds):
            name = class_names[pred.class_id]
            if pi in matched_pi:
                tp += 1
                per_class[name]["tp"] += 1
            else:
                fp += 1
                per_class[name]["fp"] += 1
        for gi, gt in enumerate(result.ground_truth):
            if gi not in matched_gi:
                fn += 1
                per_class[class_names[gt.class_id]]["fn"] += 1

    precision, recall = precision_recall(tp, fp, fn)
    return {
        "iou_threshold": iou_threshold,
        "score_threshold": score_threshold,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1_score(precision, recall),
        "per_class": per_class,
    }


def mean_average_precision(
    results: Sequence[DetectionResult],
    class_names: Sequence[str],
    iou_thresholds: Sequence[float] = (0.5,),
) -> dict:
    """mAP over classes and IoU thresholds, plus per-class AP at 0.5.

    Implementation follows COCO's structure: for each class, collect every
    prediction with its score, sort globally, mark true positives using greedy
    matching at that IoU, then integrate the PR curve.
    """
    per_threshold: dict[float, float] = {}
    per_class_at_50: dict[str, float] = {}

    for threshold in iou_thresholds:
        aps = []
        for class_id, name in enumerate(class_names):
            scores: list[float] = []
            tps: list[int] = []
            n_positives = 0
            for result in results:
                gts = [g for g in result.ground_truth if g.class_id == class_id]
                preds = [p for p in result.predictions if p.class_id == class_id]
                n_positives += len(gts)
                matches = greedy_match(preds, gts, threshold)
                matched = {m[0] for m in matches}
                for pi, pred in enumerate(preds):
                    scores.append(pred.score)
                    tps.append(1 if pi in matched else 0)
            if n_positives == 0:
                continue
            ap = average_precision(scores, tps, n_positives)
            aps.append(ap)
            if abs(threshold - 0.5) < 1e-9:
                per_class_at_50[name] = ap
        per_threshold[float(threshold)] = float(np.mean(aps)) if aps else 0.0

    return {
        "map": float(np.mean(list(per_threshold.values()))) if per_threshold else 0.0,
        "per_iou": per_threshold,
        "per_class_ap50": per_class_at_50,
        "n_iou_thresholds": len(iou_thresholds),
    }


def non_max_suppression(predictions: Sequence[Annotation], iou_threshold: float = 0.45) -> list[Annotation]:
    """Greedy NMS per class: keep the highest score, drop heavy overlaps.

    NMS is why a heatmap detector can emit one box per object instead of one per
    local maximum. It is also a hyperparameter: raise it and duplicates survive,
    lower it and two genuinely adjacent objects collapse into one.
    """
    kept: list[Annotation] = []
    for class_id in sorted({p.class_id for p in predictions}):
        remaining = sorted([p for p in predictions if p.class_id == class_id], key=lambda a: -a.score)
        while remaining:
            best = remaining.pop(0)
            kept.append(best)
            remaining = [p for p in remaining if box_iou(best.box, p.box) <= iou_threshold]
    return sorted(kept, key=lambda a: -a.score)


def pr_curve(results: Sequence[DetectionResult], class_names: Sequence[str], iou_threshold: float = 0.5) -> list[dict]:
    """Precision/recall at a sweep of score thresholds (the curve Lab 6 plots)."""
    all_scores = sorted({p.score for r in results for p in r.predictions}, reverse=True)
    if not all_scores:
        return []
    points = []
    for threshold in all_scores:
        metrics = evaluate_detections(results, class_names, iou_threshold, threshold)
        points.append(
            {
                "score_threshold": float(threshold),
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1": metrics["f1"],
                "tp": metrics["tp"],
                "fp": metrics["fp"],
                "fn": metrics["fn"],
            }
        )
    return points


# ---------------------------------------------------------------------------
# Segmentation metrics
# ---------------------------------------------------------------------------


def confusion_matrix(pred_mask: np.ndarray, true_mask: np.ndarray, n_classes: int) -> np.ndarray:
    """Rows = ground truth, columns = prediction, counts over all pixels."""
    if pred_mask.shape != true_mask.shape:
        raise ValueError(f"mask shape mismatch: {pred_mask.shape} vs {true_mask.shape}")
    pred = pred_mask.reshape(-1).astype(np.int64)
    true = true_mask.reshape(-1).astype(np.int64)
    if pred.max(initial=0) >= n_classes or true.max(initial=0) >= n_classes:
        raise ValueError(f"mask contains a class id >= {n_classes}")
    matrix = np.zeros((n_classes, n_classes), dtype=np.int64)
    np.add.at(matrix, (true, pred), 1)
    return matrix


def segmentation_report(pred_mask: np.ndarray, true_mask: np.ndarray, class_names: Sequence[str]) -> dict:
    """Pixel accuracy, per-class IoU and Dice, mean IoU, and frequency-weighted IoU.

    Pixel accuracy is dominated by the background class and is therefore
    misleading on imbalanced masks - which is exactly why the mean IoU is also
    reported. If a student reports only pixel accuracy, an all-background
    predictor looks excellent.
    """
    n = len(class_names)
    cm = confusion_matrix(pred_mask, true_mask, n)
    total = cm.sum()
    tp = np.diag(cm).astype(np.float64)
    fp = cm.sum(axis=0) - tp
    fn = cm.sum(axis=1) - tp

    iou = np.where((tp + fp + fn) > 0, tp / np.maximum(tp + fp + fn, 1e-12), np.nan)
    dice = np.where((2 * tp + fp + fn) > 0, 2 * tp / np.maximum(2 * tp + fp + fn, 1e-12), np.nan)
    freq = cm.sum(axis=1).astype(np.float64) / max(total, 1)

    present = ~np.isnan(iou)
    return {
        "pixel_accuracy": float(tp.sum() / max(total, 1)),
        "per_class_iou": {name: (None if np.isnan(iou[i]) else float(iou[i])) for i, name in enumerate(class_names)},
        "per_class_dice": {name: (None if np.isnan(dice[i]) else float(dice[i])) for i, name in enumerate(class_names)},
        "mean_iou": float(np.nanmean(iou)) if present.any() else 0.0,
        "frequency_weighted_iou": float(np.nansum(freq * iou)),
        "confusion_matrix": cm.tolist(),
    }


def boundary_f1(pred_mask: np.ndarray, true_mask: np.ndarray, tolerance: int = 1) -> float:
    """F1 over boundary pixels within a pixel tolerance.

    Region IoU hides boundary quality: a mask that is one pixel too fat scores
    well on Dice and badly here. Implemented with a cheap 4-neighbour edge test.
    """
    def edges(mask: np.ndarray) -> np.ndarray:
        m = mask.astype(bool)
        e = np.zeros_like(m)
        e[1:, :] |= m[1:, :] != m[:-1, :]
        e[:-1, :] |= m[:-1, :] != m[1:, :]
        e[:, 1:] |= m[:, 1:] != m[:, :-1]
        e[:, :-1] |= m[:, :-1] != m[:, 1:]
        return e

    pred_e, true_e = edges(pred_mask), edges(true_mask)
    if tolerance > 0:
        dilated = true_e.copy()
        for _ in range(tolerance):
            d = dilated.copy()
            d[1:, :] |= dilated[:-1, :]
            d[:-1, :] |= dilated[1:, :]
            d[:, 1:] |= dilated[:, :-1]
            d[:, :-1] |= dilated[:, 1:]
            dilated = d
        matched = (pred_e & dilated).sum()
    else:
        matched = (pred_e & true_e).sum()
    denom = pred_e.sum() + true_e.sum()
    return float(2 * matched / denom) if denom else 0.0


# ---------------------------------------------------------------------------
# Classification metrics
# ---------------------------------------------------------------------------


def classification_report(y_true: Sequence[int], y_pred: Sequence[int], class_names: Sequence[str]) -> dict:
    """Accuracy, per-class precision/recall/F1, macro and weighted averages."""
    y_true_arr = np.asarray(y_true)
    y_pred_arr = np.asarray(y_pred)
    if y_true_arr.shape != y_pred_arr.shape:
        raise ValueError("y_true and y_pred must have the same length")
    n = len(class_names)
    cm = confusion_matrix(y_pred_arr, y_true_arr, n)
    tp = np.diag(cm).astype(np.float64)
    fp = cm.sum(axis=0) - tp
    fn = cm.sum(axis=1) - tp

    precision = np.where((tp + fp) > 0, tp / np.maximum(tp + fp, 1e-12), 0.0)
    recall = np.where((tp + fn) > 0, tp / np.maximum(tp + fn, 1e-12), 0.0)
    f1 = np.where((precision + recall) > 0, 2 * precision * recall / np.maximum(precision + recall, 1e-12), 0.0)
    support = cm.sum(axis=1)

    per_class = {
        name: {
            "precision": float(precision[i]),
            "recall": float(recall[i]),
            "f1": float(f1[i]),
            "support": int(support[i]),
        }
        for i, name in enumerate(class_names)
    }
    macro = float(np.mean([per_class[n_]["f1"] for n_ in class_names]))
    weighted = float(np.average([per_class[n_]["f1"] for n_ in class_names], weights=np.maximum(support, 1)))
    return {
        "accuracy": float(tp.sum() / max(cm.sum(), 1)),
        "macro_f1": macro,
        "weighted_f1": weighted,
        "per_class": per_class,
        "confusion_matrix": cm.tolist(),
    }


def expected_calibration_error(confidences: Sequence[float], correct: Sequence[int], n_bins: int = 10) -> float:
    """Gap between predicted confidence and observed accuracy, over confidence bins.

    A model that says 0.9 and is right 60% of the time is dangerous even at high
    accuracy, because the confidence is what a deployment threshold relies on.
    """
    conf = np.asarray(confidences, dtype=np.float64)
    hit = np.asarray(correct, dtype=np.float64)
    if conf.size == 0:
        return 0.0
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (conf > lo) & (conf <= hi)
        if mask.sum() == 0:
            continue
        ece += (mask.sum() / conf.size) * abs(hit[mask].mean() - conf[mask].mean())
    return float(ece)


# ---------------------------------------------------------------------------
# Face metrics: verification and identification
# ---------------------------------------------------------------------------


def verification_metrics(scores: Sequence[float], same_identity: Sequence[bool], threshold: float) -> dict:
    """FAR, FRR, TAR, and accuracy for one decision threshold.

    Decision rule: a pair is declared a match when ``score >= threshold``.
    ``same_identity`` is the ground truth. FAR counts false matches (a different
    person accepted) and FRR counts false rejections (the same person refused).
    Which of the two matters more is a policy question, not a metric question.
    """
    s = np.asarray(scores, dtype=np.float64)
    same = np.asarray(same_identity, dtype=bool)
    if s.shape != same.shape:
        raise ValueError("scores and same_identity must have the same length")
    if s.size == 0:
        return {"threshold": threshold, "far": 0.0, "frr": 0.0, "tar": 0.0, "accuracy": 0.0, "n": 0}

    accept = s >= threshold
    impostor = ~same
    far = float((accept & impostor).sum() / max(impostor.sum(), 1))
    frr = float((~accept & same).sum() / max(same.sum(), 1))
    tar = 1.0 - frr
    accuracy = float((accept == same).mean())
    return {"threshold": float(threshold), "far": far, "frr": frr, "tar": tar, "accuracy": accuracy, "n": int(s.size)}


def roc_points(scores: Sequence[float], same_identity: Sequence[bool], n_thresholds: int = 200) -> list[dict]:
    """FAR/FRR across thresholds, from strict to permissive."""
    s = np.asarray(scores, dtype=np.float64)
    if s.size == 0:
        return []
    lo, hi = float(s.min()), float(s.max())
    if hi - lo < 1e-9:
        return [verification_metrics(s, same_identity, hi)]
    return [verification_metrics(s, same_identity, float(t)) for t in np.linspace(hi, lo, n_thresholds)]


def equal_error_rate(scores: Sequence[float], same_identity: Sequence[bool]) -> dict:
    """Threshold where FAR and FRR cross, plus the EER value itself.

    Reported with the threshold, never alone: an EER of 4% at a threshold nobody
    would deploy is a number, not a recommendation.
    """
    points = roc_points(scores, same_identity)
    if not points:
        return {"eer": 0.0, "threshold": 0.0}
    best = min(points, key=lambda p: abs(p["far"] - p["frr"]))
    return {"eer": float((best["far"] + best["frr"]) / 2.0), "threshold": float(best["threshold"]), "far": best["far"], "frr": best["frr"]}


def identification_metrics(
    probe_embeddings: np.ndarray,
    probe_labels: Sequence[str],
    gallery_embeddings: np.ndarray,
    gallery_labels: Sequence[str],
    metric: str = "cosine",
) -> dict:
    """Rank-1 accuracy and the false-match rate at rank 1.

    Identification is a 1:N search, so its characteristic failure is not "is
    this the same person" but "is the nearest neighbour the wrong person". Both
    numbers are needed; rank-1 alone hides how often a stranger is matched.
    """
    probes = np.asarray(probe_embeddings, dtype=np.float64)
    gallery = np.asarray(gallery_embeddings, dtype=np.float64)
    if probes.ndim != 2 or gallery.ndim != 2:
        raise ValueError("embeddings must be 2-D (n_samples, dim)")
    if probes.shape[1] != gallery.shape[1]:
        raise ValueError(f"embedding dim mismatch: {probes.shape[1]} vs {gallery.shape[1]}")

    if metric == "cosine":
        p = probes / np.maximum(np.linalg.norm(probes, axis=1, keepdims=True), 1e-12)
        g = gallery / np.maximum(np.linalg.norm(gallery, axis=1, keepdims=True), 1e-12)
        sims = p @ g.T
    elif metric == "euclidean":
        sims = -np.linalg.norm(probes[:, None, :] - gallery[None, :, :], axis=2)
    else:
        raise ValueError(f"unknown metric {metric!r}; use 'cosine' or 'euclidean'")

    top = np.argmax(sims, axis=1)
    predicted = [gallery_labels[i] for i in top]
    correct = [pred == truth for pred, truth in zip(predicted, probe_labels)]
    known = set(gallery_labels)
    impostor_probes = [i for i, label in enumerate(probe_labels) if label not in known]
    false_matches = sum(1 for i in impostor_probes if predicted[i] != "unknown")
    return {
        "rank1_accuracy": float(np.mean(correct)) if correct else 0.0,
        "n_probes": len(probe_labels),
        "n_impostor_probes": len(impostor_probes),
        "false_match_rate": float(false_matches / len(impostor_probes)) if impostor_probes else 0.0,
        "predictions": predicted,
    }
