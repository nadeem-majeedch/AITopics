"""Metric implementations for the Production AI section.

These are written out rather than imported so that each definition in the lesson
maps to code you can read. They are checked against scikit-learn in the section's
unit tests, which is the only reason to trust a hand-written metric.

All functions take plain sequences or NumPy arrays and return plain Python types.
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence

import numpy as np


# --------------------------------------------------------------------------- #
# Classification
# --------------------------------------------------------------------------- #
def confusion(y_true: Sequence[int], y_pred: Sequence[int], positive: int = 1) -> dict:
    """Confusion counts for the positive class."""
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    tp = int(((y_true == positive) & (y_pred == positive)).sum())
    fp = int(((y_true != positive) & (y_pred == positive)).sum())
    fn = int(((y_true == positive) & (y_pred != positive)).sum())
    tn = int(((y_true != positive) & (y_pred != positive)).sum())
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def precision_recall_f1(y_true, y_pred, positive: int = 1) -> dict:
    c = confusion(y_true, y_pred, positive)
    precision = c["tp"] / (c["tp"] + c["fp"]) if c["tp"] + c["fp"] else 0.0
    recall = c["tp"] / (c["tp"] + c["fn"]) if c["tp"] + c["fn"] else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def accuracy(y_true, y_pred) -> float:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    return float((y_true == y_pred).mean()) if len(y_true) else 0.0


def macro_f1(y_true, y_pred) -> float:
    labels = sorted(set(np.asarray(y_true).tolist()) | set(np.asarray(y_pred).tolist()))
    return float(np.mean([precision_recall_f1(y_true, y_pred, label)["f1"] for label in labels]))


def roc_auc(y_true: Sequence[int], scores: Sequence[float]) -> float:
    """Rank-based AUC, ties averaged. 0.5 is chance."""
    y_true = np.asarray(y_true, dtype=int)
    scores = np.asarray(scores, dtype=float)
    positives = y_true == 1
    n_pos = int(positives.sum())
    n_neg = int((~positives).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores), dtype=float)
    sorted_scores = scores[order]
    i = 0
    while i < len(scores):
        j = i
        while j + 1 < len(scores) and sorted_scores[j + 1] == sorted_scores[i]:
            j += 1
        ranks[order[i : j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return float((ranks[positives].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def average_precision(y_true: Sequence[int], scores: Sequence[float]) -> float:
    """Area under the precision-recall curve with step interpolation."""
    y_true = np.asarray(y_true, dtype=int)
    scores = np.asarray(scores, dtype=float)
    if y_true.sum() == 0:
        return float("nan")
    order = np.argsort(-scores, kind="mergesort")
    y = y_true[order]
    tp = np.cumsum(y)
    fp = np.cumsum(1 - y)
    precision = tp / np.maximum(tp + fp, 1)
    recall = tp / y.sum()
    return float(np.sum(np.diff(np.concatenate([[0.0], recall])) * precision))


def log_loss(y_true: Sequence[int], probs: Sequence[float], eps: float = 1e-12) -> float:
    y_true = np.asarray(y_true, dtype=float)
    p = np.clip(np.asarray(probs, dtype=float), eps, 1 - eps)
    return float(-np.mean(y_true * np.log(p) + (1 - y_true) * np.log(1 - p)))


# --------------------------------------------------------------------------- #
# Regression
# --------------------------------------------------------------------------- #
def mae(y_true, y_pred) -> float:
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))


def rmse(y_true, y_pred) -> float:
    return float(math.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2)))


def r2(y_true, y_pred) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    ss_res = float(((y_true - y_pred) ** 2).sum())
    ss_tot = float(((y_true - y_true.mean()) ** 2).sum())
    return float(1 - ss_res / ss_tot) if ss_tot else float("nan")


# --------------------------------------------------------------------------- #
# Uncertainty
# --------------------------------------------------------------------------- #
def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% interval for a proportion. Correct at small n, unlike normal approx."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = successes / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def bootstrap_ci(values: Iterable[float], n_boot: int = 2000, alpha: float = 0.05,
                 seed: int = 0) -> tuple[float, float, float]:
    """Percentile bootstrap of the mean. Returns (point, low, high)."""
    data = np.asarray(list(values), dtype=float)
    if len(data) == 0:
        return (float("nan"),) * 3
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(data), size=(n_boot, len(data)))
    means = data[draws].mean(axis=1)
    low, high = np.quantile(means, [alpha / 2, 1 - alpha / 2])
    return (float(data.mean()), float(low), float(high))


def paired_bootstrap_diff(a: Sequence[float], b: Sequence[float], n_boot: int = 2000,
                          seed: int = 0) -> dict:
    """Bootstrap the paired difference mean(a - b).

    Pairing matters: both models saw the same rows, so resample rows, not scores.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if len(a) != len(b):
        raise ValueError("paired samples must have equal length")
    diff = a - b
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(diff), size=(n_boot, len(diff)))
    means = diff[draws].mean(axis=1)
    low, high = np.quantile(means, [0.025, 0.975])
    return {
        "difference": float(diff.mean()),
        "low": float(low),
        "high": float(high),
        "includes_zero": bool(low <= 0.0 <= high),
    }


# --------------------------------------------------------------------------- #
# Retrieval / ranking
# --------------------------------------------------------------------------- #
def recall_at_k(ranked: Sequence[str], relevant: Sequence[str], k: int) -> float:
    if not relevant:
        return float("nan")
    return len(set(ranked[:k]) & set(relevant)) / len(set(relevant))


def reciprocal_rank(ranked: Sequence[str], relevant: Sequence[str]) -> float:
    for position, doc in enumerate(ranked, start=1):
        if doc in relevant:
            return 1.0 / position
    return 0.0


def ndcg_at_k(ranked: Sequence[str], relevant: Sequence[str], k: int) -> float:
    gains = [1.0 if doc in relevant else 0.0 for doc in ranked[:k]]
    dcg = sum(gain / math.log2(position + 1) for position, gain in enumerate(gains, start=1))
    ideal = sum(1.0 / math.log2(position + 1) for position in range(1, min(k, len(relevant)) + 1))
    return dcg / ideal if ideal else float("nan")


# --------------------------------------------------------------------------- #
# Formatting
# --------------------------------------------------------------------------- #
def fmt(value: float, digits: int = 3) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "n/a"
    return f"{value:.{digits}f}"


def table(rows: list[dict], columns: list[str]) -> str:
    """Render a list of dicts as a Markdown table, right-aligning numbers."""
    widths = [len(c) for c in columns]
    cells: list[list[str]] = []
    for row in rows:
        line = []
        for column in columns:
            value = row.get(column, "")
            text = fmt(value) if isinstance(value, float) else str(value)
            line.append(text)
            widths[columns.index(column)] = max(widths[columns.index(column)], len(text))
        cells.append(line)
    head = "| " + " | ".join(c.ljust(w) for c, w in zip(columns, widths)) + " |"
    sep = "| " + " | ".join("-" * w for w in widths) + " |"
    body = ["| " + " | ".join(c.rjust(w) if _numeric(c) else c.ljust(w)
                              for c, w in zip(line, widths)) + " |" for line in cells]
    return "\n".join([head, sep, *body])


def _numeric(text: str) -> bool:
    try:
        float(text)
        return True
    except ValueError:
        return False
