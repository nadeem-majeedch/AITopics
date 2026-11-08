"""Splitting data, and auditing a split for leakage.

Two ideas are kept separate on purpose:

* ``stratified_split`` makes a split that is honest *if the rows are independent*.
* ``leak_audit`` asks whether they are. It cannot prove independence; it reports
  features that behave like the label and duplicate rows that straddle the split.

The lesson (EP02) is that the second question matters more than the ratio you
choose for the first.
"""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from typing import Sequence

import numpy as np

from . import metrics


def stratified_split(rows: list[dict], key: str, fractions: tuple[float, float, float] = (0.6, 0.2, 0.2),
                     seed: int = 7) -> tuple[list[dict], list[dict], list[dict]]:
    """Split rows by label so every split has the same class balance."""
    if abs(sum(fractions) - 1.0) > 1e-9:
        raise ValueError("fractions must sum to 1")
    rng = random.Random(seed)

    by_class: dict = defaultdict(list)
    for row in rows:
        by_class[row[key]].append(row)

    train: list[dict] = []
    val: list[dict] = []
    test: list[dict] = []
    for label, group in by_class.items():
        shuffled = list(group)
        rng.shuffle(shuffled)
        n = len(shuffled)
        n_train = int(round(n * fractions[0]))
        n_val = int(round(n * fractions[1]))
        train.extend(shuffled[:n_train])
        val.extend(shuffled[n_train : n_train + n_val])
        test.extend(shuffled[n_train + n_val :])
    rng.shuffle(train)
    rng.shuffle(val)
    rng.shuffle(test)
    return train, val, test


def random_split(rows: list[dict], fractions: tuple[float, float, float] = (0.6, 0.2, 0.2),
                 seed: int = 7) -> tuple[list[dict], list[dict], list[dict]]:
    """Row-wise split with no grouping. Correct only when rows are independent."""
    rng = random.Random(seed)
    shuffled = list(rows)
    rng.shuffle(shuffled)
    n = len(shuffled)
    a = int(round(n * fractions[0]))
    b = a + int(round(n * fractions[1]))
    return shuffled[:a], shuffled[a:b], shuffled[b:]


def duplicate_overlap(train: list[dict], test: list[dict], feature_columns: Sequence[str]) -> dict:
    """Fraction of test rows whose feature vector also occurs in train.

    This is the leakage that ``stratified_split`` cannot see: two rows are the
    same customer exported twice, so the model has memorised the test row.
    """
    def signature(row: dict) -> tuple:
        return tuple(row[column] for column in feature_columns)

    train_signatures = {signature(row) for row in train}
    matched = sum(1 for row in test if signature(row) in train_signatures)
    return {
        "test_rows": len(test),
        "matched": matched,
        "fraction": matched / len(test) if test else 0.0,
    }


def class_balance(rows: list[dict], key: str) -> dict:
    counts = Counter(row[key] for row in rows)
    total = len(rows) or 1
    return {label: count / total for label, count in sorted(counts.items())}


def single_feature_strength(rows: list[dict], feature: str, target_key: str = "churned") -> dict:
    """How much a single column tells you about the label.

    * categorical: the majority-class share inside the most informative level
    * numeric: |AUC - 0.5| * 2, so 0 means no signal and 1 means perfect ranking

    A value near 1 is not proof of leakage; a feature can be genuinely predictive.
    It is a reason to ask whether the feature is available at prediction time.
    """
    values = [row[feature] for row in rows]
    labels = [int(row[target_key]) for row in rows]
    if all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in values):
        unique = sorted(set(values))
        if len(unique) <= 2:
            purity = _purity([str(value) for value in values], labels)
            return {"type": "binary", "score": purity, "detail": f"purity {purity:.3f}"}
        auc = metrics.roc_auc(labels, [float(value) for value in values])
        strength = abs(auc - 0.5) * 2
        return {"type": "numeric", "score": strength, "detail": f"auc {auc:.3f}"}
    purity = _purity([str(value) for value in values], labels)
    return {"type": "categorical", "score": purity, "detail": f"purity {purity:.3f}"}


def _purity(values: list[str], labels: list[int]) -> float:
    """Weighted majority share: 1.0 means the column determines the label."""
    groups: dict[str, list[int]] = defaultdict(list)
    for value, label in zip(values, labels):
        groups[value].append(label)
    total = len(labels)
    correct = sum(max(Counter(group).values()) for group in groups.values())
    return correct / total if total else 0.0


def missingness_by_label(rows: list[dict], feature: str, target_key: str = "churned") -> dict:
    """Fill rate per label. A column filled only for positives is a label in disguise."""
    filled = defaultdict(int)
    totals = defaultdict(int)
    for row in rows:
        label = int(row[target_key])
        totals[label] += 1
        if str(row[feature]).strip() != "":
            filled[label] += 1
    return {label: filled[label] / totals[label] for label in sorted(totals)}


def leak_audit(rows: list[dict], features: Sequence[str], target_key: str = "churned",
               threshold: float = 0.95) -> list[dict]:
    """Rank features by how suspiciously well they predict the label."""
    findings = []
    for feature in features:
        strength = single_feature_strength(rows, feature, target_key)
        fill = missingness_by_label(rows, feature, target_key)
        fill_gap = max(fill.values()) - min(fill.values()) if fill else 0.0
        suspicious = strength["score"] >= threshold or fill_gap >= 0.5
        reason = []
        if strength["score"] >= threshold:
            reason.append(f"{strength['detail']} (single column nearly determines the label)")
        if fill_gap >= 0.5:
            reason.append(f"fill rate differs by {fill_gap:.0%} between labels")
        findings.append(
            {
                "feature": feature,
                "type": strength["type"],
                "score": strength["score"],
                "detail": strength["detail"],
                "fill_gap": fill_gap,
                "suspicious": suspicious,
                "reason": "; ".join(reason) or "no strong single-column signal",
            }
        )
    return sorted(findings, key=lambda item: item["score"], reverse=True)


def bootstrap_accuracy_ci(rows: list[dict], correct: np.ndarray, seed: int = 0) -> dict:
    """Mean accuracy with a percentile bootstrap interval."""
    mean, low, high = metrics.bootstrap_ci(np.asarray(correct, dtype=float), seed=seed)
    return {"accuracy": mean, "low": low, "high": high, "n": len(correct)}
