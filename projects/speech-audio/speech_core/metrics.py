"""Classification, verification, calibration, and latency metrics.

The speech section needs four kinds of measurement that the vision section did not:
verification error rates (speaker tasks), calibration (confidence is shown to users),
word error counts (already in ``text``), and latency (a voice interface that answers
in 2 seconds feels broken).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


def confusion_matrix(y_true: Sequence[int], y_pred: Sequence[int], n_classes: int) -> np.ndarray:
    matrix = np.zeros((n_classes, n_classes), dtype=np.int64)
    for truth, pred in zip(y_true, y_pred):
        if 0 <= truth < n_classes and 0 <= pred < n_classes:
            matrix[int(truth), int(pred)] += 1
    return matrix


def classification_report(y_true: Sequence[int], y_pred: Sequence[int], class_names: Sequence[str]) -> dict:
    """Accuracy, per-class precision/recall/F1, and the confusion matrix."""
    n = len(class_names)
    matrix = confusion_matrix(y_true, y_pred, n)
    per_class = {}
    for i, name in enumerate(class_names):
        tp = int(matrix[i, i])
        fp = int(matrix[:, i].sum() - tp)
        fn = int(matrix[i, :].sum() - tp)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[name] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": int(matrix[i, :].sum()),
        }
    accuracy = float(np.trace(matrix) / max(matrix.sum(), 1))
    return {"accuracy": accuracy, "per_class": per_class, "confusion_matrix": matrix.tolist(), "n": int(matrix.sum())}


def top_confusions(report: dict, class_names: Sequence[str], k: int = 3) -> list[tuple[str, str, int]]:
    matrix = np.array(report["confusion_matrix"])
    pairs = []
    for i, name in enumerate(class_names):
        for j, other in enumerate(class_names):
            if i != j and matrix[i, j] > 0:
                pairs.append((name, other, int(matrix[i, j])))
    pairs.sort(key=lambda row: row[2], reverse=True)
    return pairs[:k]


# ---------------------------------------------------------------------------
# Verification / identification
# ---------------------------------------------------------------------------


def verification_metrics(scores: Sequence[float], same_identity: Sequence[bool], threshold: float) -> dict:
    """FAR, FRR, and accuracy at one threshold.

    ``accuracy`` is dominated by the impostor pairs when genuine pairs are rare,
    which is why FAR and FRR are reported separately.
    """
    if len(scores) != len(same_identity):
        raise ValueError("scores and labels must have the same length")
    if not len(scores):
        return {"far": 0.0, "frr": 0.0, "accuracy": 0.0, "threshold": float(threshold), "n": 0}
    scores_arr = np.asarray(scores, dtype=np.float64)
    same = np.asarray(same_identity, dtype=bool)
    accept = scores_arr >= threshold
    taut = np.sum(accept & ~same)
    impostors = max(int(np.sum(~same)), 1)
    frr_num = np.sum(~accept & same)
    genuine = max(int(np.sum(same)), 1)
    far = float(taut / impostors)
    frr = float(frr_num / genuine)
    correct = int(np.sum(accept & same) + np.sum(~accept & ~same))
    return {
        "threshold": float(threshold),
        "far": far,
        "frr": frr,
        "tar": float(np.sum(accept & same) / genuine),
        "accuracy": correct / len(scores_arr),
        "n": len(scores_arr),
        "n_same": int(np.sum(same)),
    }


def roc_points(scores: Sequence[float], same_identity: Sequence[bool], n_points: int = 40) -> list[dict]:
    scores_arr = np.asarray(scores, dtype=np.float64)
    if scores_arr.size == 0:
        return []
    thresholds = np.linspace(float(scores_arr.min()), float(scores_arr.max()), n_points)
    return [verification_metrics(scores, same_identity, float(t)) for t in thresholds]


def equal_error_rate(scores: Sequence[float], same_identity: Sequence[bool], n_points: int = 200) -> dict:
    """Threshold where FAR and FRR are closest; the crossing is interpolated."""
    points = roc_points(scores, same_identity, n_points)
    if not points:
        return {"eer": 1.0, "threshold": 0.0, "far": 1.0, "frr": 1.0}
    best = min(points, key=lambda row: abs(row["far"] - row["frr"]))
    return {
        "eer": float((best["far"] + best["frr"]) / 2.0),
        "threshold": best["threshold"],
        "far": best["far"],
        "frr": best["frr"],
    }


def identification_accuracy(
    probe_embeddings: np.ndarray,
    probe_labels: Sequence[str],
    gallery_embeddings: np.ndarray,
    gallery_labels: Sequence[str],
) -> dict:
    """Rank-1 accuracy for closed-set 1:N identification."""
    if len(probe_embeddings) == 0 or len(gallery_embeddings) == 0:
        return {"rank1": 0.0, "n_probes": 0}
    probes = np.asarray(probe_embeddings, dtype=np.float64)
    gallery = np.asarray(gallery_embeddings, dtype=np.float64)
    probes = probes / np.maximum(np.linalg.norm(probes, axis=1, keepdims=True), 1e-9)
    gallery = gallery / np.maximum(np.linalg.norm(gallery, axis=1, keepdims=True), 1e-9)
    scores = probes @ gallery.T
    best = scores.argmax(axis=1)
    correct = sum(1 for i, idx in enumerate(best) if gallery_labels[idx] == probe_labels[i])
    return {"rank1": correct / len(probes), "n_probes": len(probes), "gallery": len(gallery)}


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------


def expected_calibration_error(confidences: Sequence[float], correct: Sequence[int], n_bins: int = 10) -> float:
    """Weighted gap between confidence and accuracy across confidence bins.

    A model that says 0.9 and is right 70% of the time is overconfident, and any
    interface that shows the number as a percentage is lying to its user.
    """
    conf = np.clip(np.asarray(confidences, dtype=np.float64), 0.0, 1.0)
    hit = np.asarray(correct, dtype=np.float64)
    if conf.size == 0:
        return 0.0
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    total = 0.0
    for i in range(n_bins):
        mask = (conf > bins[i]) & (conf <= bins[i + 1]) if i else (conf >= bins[i]) & (conf <= bins[i + 1])
        if not mask.any():
            continue
        total += mask.mean() * abs(hit[mask].mean() - conf[mask].mean())
    return float(total)


# ---------------------------------------------------------------------------
# Latency
# ---------------------------------------------------------------------------


@dataclass
class LatencyStats:
    label: str
    label_name: str
    median_ms: float
    p90_ms: float
    min_ms: float
    max_ms: float
    runs: int
    real_time_factor: float = 0.0

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "median_ms": round(self.median_ms, 4),
            "p90_ms": round(self.p90_ms, 4),
            "min_ms": round(self.min_ms, 4),
            "max_ms": round(self.max_ms, 4),
            "runs": self.runs,
            "real_time_factor": round(self.real_time_factor, 5),
        }


def benchmark(fn: Callable[[], object], runs: int = 10, warmup: int = 1, label: str = "", audio_seconds: float = 0.0) -> LatencyStats:
    """Median and p90 wall time, after discarding warmup runs."""
    for _ in range(max(0, warmup)):
        fn()
    times = []
    for _ in range(max(1, runs)):
        started = time.perf_counter()
        fn()
        times.append((time.perf_counter() - started) * 1000.0)
    arr = np.array(times)
    rtf = (float(np.median(arr)) / 1000.0) / audio_seconds if audio_seconds > 0 else 0.0
    return LatencyStats(
        label=label,
        label_name=label,
        median_ms=float(np.median(arr)),
        p90_ms=float(np.percentile(arr, 90)),
        min_ms=float(arr.min()),
        max_ms=float(arr.max()),
        runs=len(arr),
        real_time_factor=rtf,
    )


def format_table(rows: Sequence[dict], columns: Sequence[str]) -> str:
    if not rows:
        return "(no rows)"
    widths = {col: max(len(col), *(len(_fmt(row.get(col))) for row in rows)) for col in columns}
    header = "  ".join(f"{col:<{widths[col]}}" for col in columns)
    lines = [header, "-" * len(header)]
    for row in rows:
        lines.append("  ".join(f"{_fmt(row.get(col)):<{widths[col]}}" for col in columns))
    return "\n".join(lines)


def _fmt(value) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)
