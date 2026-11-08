"""Calibration, uncertainty, and abstention.

A model that says 0.9 should be right about 90% of the time. Accuracy alone
cannot tell you that, and a model can be accurate and badly calibrated at once —
which matters the moment a threshold or a human review queue depends on the
score.
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from . import metrics


def reliability(y_true: Sequence[int], probs: Sequence[float], n_bins: int = 10) -> list[dict]:
    """Bin predictions by confidence and compare mean confidence with observed rate."""
    y_true = np.asarray(y_true, dtype=float)
    probs = np.asarray(probs, dtype=float)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    bins = []
    for index in range(n_bins):
        low, high = edges[index], edges[index + 1]
        mask = (probs > low) & (probs <= high) if index else (probs >= low) & (probs <= high)
        count = int(mask.sum())
        if count == 0:
            bins.append({"bin": f"{low:.1f}-{high:.1f}", "n": 0, "confidence": float("nan"),
                         "observed": float("nan"), "gap": float("nan")})
            continue
        confidence = float(probs[mask].mean())
        observed = float(y_true[mask].mean())
        bins.append({"bin": f"{low:.1f}-{high:.1f}", "n": count, "confidence": confidence,
                     "observed": observed, "gap": abs(confidence - observed)})
    return bins


def expected_calibration_error(y_true: Sequence[int], probs: Sequence[float], n_bins: int = 10) -> float:
    """Weighted average gap between confidence and accuracy. Lower is better."""
    bins = reliability(y_true, probs, n_bins)
    total = sum(item["n"] for item in bins)
    if total == 0:
        return float("nan")
    return float(sum(item["n"] / total * item["gap"] for item in bins if item["n"]))


def brier(y_true: Sequence[int], probs: Sequence[float]) -> float:
    """Mean squared error of the probability itself. Lower is better."""
    y_true = np.asarray(y_true, dtype=float)
    probs = np.asarray(probs, dtype=float)
    return float(np.mean((probs - y_true) ** 2))


def _as_probability(p: np.ndarray, t: float) -> np.ndarray:
    """Temperature applied to a probability through its odds, not its logit."""
    p = np.clip(p, 1e-9, 1 - 1e-9)
    odds = p / (1 - p)
    scaled = odds ** (1.0 / t)
    return scaled / (1 + scaled)


def fit_temperature(probs: Sequence[float], y_true: Sequence[int],
                    grid: Sequence[float] | None = None) -> dict:
    """Choose one temperature on validation data to minimise log loss.

    Fitted on validation, never on test. The returned temperature is applied to
    test predictions unchanged, which is the only way the improvement is honest.
    """
    probs = np.asarray(probs, dtype=float)
    y_true = np.asarray(y_true, dtype=int)
    grid = grid or [round(0.5 + 0.05 * i, 2) for i in range(51)]  # 0.50 .. 3.00
    best = {"temperature": 1.0, "log_loss": metrics.log_loss(y_true, probs)}
    for temperature in grid:
        candidate = metrics.log_loss(y_true, _as_probability(probs, temperature))
        if candidate < best["log_loss"] - 1e-12:
            best = {"temperature": float(temperature), "log_loss": float(candidate)}
    return best


def apply_temperature(probs: Sequence[float], temperature: float) -> np.ndarray:
    return _as_probability(np.asarray(probs, dtype=float), temperature)


def abstention_curve(y_true: Sequence[int], probs: Sequence[float],
                     thresholds: Sequence[float] | None = None) -> list[dict]:
    """Accuracy on the answered subset as the abstention threshold rises.

    ``coverage`` is the share of cases the system answers. ``selective_accuracy``
    is accuracy on those cases. ``risk`` is the error rate on the answered set,
    which is what a review queue is trying to bound.
    """
    y_true = np.asarray(y_true, dtype=int)
    probs = np.asarray(probs, dtype=float)
    thresholds = thresholds or [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]
    curve = []
    for threshold in thresholds:
        confident = np.abs(probs - 0.5) * 2 >= (2 * threshold - 1) if threshold > 0.5 else np.ones(len(probs), dtype=bool)
        # Interpret the threshold as confidence in the predicted class.
        predicted = (probs >= 0.5).astype(int)
        confidence = np.where(predicted == 1, probs, 1 - probs)
        confident = confidence >= threshold
        answered = int(confident.sum())
        if answered == 0:
            curve.append({"threshold": float(threshold), "coverage": 0.0,
                          "selective_accuracy": float("nan"), "risk": float("nan")})
            continue
        correct = (predicted[confident] == y_true[confident]).mean()
        curve.append({"threshold": float(threshold), "coverage": answered / len(y_true),
                      "selective_accuracy": float(correct), "risk": float(1 - correct)})
    return curve


def confidence_histogram(probs: Sequence[float], n_bins: int = 10) -> list[int]:
    probs = np.asarray(probs, dtype=float)
    counts, _ = np.histogram(probs, bins=n_bins, range=(0.0, 1.0))
    return [int(count) for count in counts]


def entropy_of_binary(p: float) -> float:
    """Shannon entropy in bits; 1.0 is maximum uncertainty for a binary decision."""
    p = min(max(p, 1e-12), 1 - 1e-12)
    return float(-(p * math.log2(p) + (1 - p) * math.log2(1 - p)))
