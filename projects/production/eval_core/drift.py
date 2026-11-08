"""Distribution shift detection: PSI and the two-sample Kolmogorov-Smirnov test.

Both statistics answer "has the input distribution moved?" and neither answers
"is the model still good?". They are early-warning signals that tell you when to
go and measure quality, not a substitute for measuring it.
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np

# Common rule of thumb for PSI on binned features. It is a heuristic, not a law:
# small samples produce large PSI values with no real change, which the lab shows.
PSI_MODERATE = 0.10
PSI_SIGNIFICANT = 0.25


def population_stability_index(expected: Sequence[float], actual: Sequence[float],
                               bins: int = 10, eps: float = 1e-6) -> float:
    """PSI between two numeric samples, binned on the expected sample's quantiles."""
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    if len(expected) < bins or len(actual) == 0:
        return float("nan")
    edges = np.quantile(expected, np.linspace(0, 1, bins + 1))
    edges = np.unique(edges)
    if len(edges) < 3:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    expected_counts, _ = np.histogram(expected, bins=edges)
    actual_counts, _ = np.histogram(actual, bins=edges)
    expected_share = np.clip(expected_counts / expected_counts.sum(), eps, None)
    actual_share = np.clip(actual_counts / actual_counts.sum(), eps, None)
    return float(np.sum((actual_share - expected_share) * np.log(actual_share / expected_share)))


def categorical_psi(expected: Sequence[str], actual: Sequence[str], eps: float = 1e-6) -> float:
    levels = sorted(set(expected) | set(actual))
    n_expected, n_actual = len(expected), len(actual)
    total = 0.0
    for level in levels:
        p = max(sum(1 for value in expected if value == level) / n_expected, eps)
        q = max(sum(1 for value in actual if value == level) / n_actual, eps)
        total += (q - p) * math.log(q / p)
    return float(total)


def ks_statistic(expected: Sequence[float], actual: Sequence[float]) -> dict:
    """Two-sample KS distance and its asymptotic p-value.

    The p-value assumes independent samples and a continuous distribution; treat
    it as an indicator, not a decision. With thousands of rows almost any shift is
    'significant', which is why PSI is reported alongside it.
    """
    a = np.sort(np.asarray(expected, dtype=float))
    b = np.sort(np.asarray(actual, dtype=float))
    if len(a) == 0 or len(b) == 0:
        return {"statistic": float("nan"), "p_value": float("nan")}
    grid = np.concatenate([a, b])
    cdf_a = np.searchsorted(a, grid, side="right") / len(a)
    cdf_b = np.searchsorted(b, grid, side="right") / len(b)
    d = float(np.max(np.abs(cdf_a - cdf_b)))
    n_eff = len(a) * len(b) / (len(a) + len(b))
    try:
        p_value = 2 * sum((-1) ** (k - 1) * math.exp(-2 * k * k * n_eff * d * d) for k in range(1, 101))
    except OverflowError:  # pragma: no cover - extreme inputs only
        p_value = 0.0
    return {"statistic": d, "p_value": float(min(max(p_value, 0.0), 1.0))}


def classify_psi(value: float) -> str:
    if value != value:  # NaN
        return "unknown"
    if value >= PSI_SIGNIFICANT:
        return "significant"
    if value >= PSI_MODERATE:
        return "moderate"
    return "stable"


def numeric_drift(train: Sequence[float], live: Sequence[float], feature: str) -> dict:
    psi = population_stability_index(train, live)
    ks = ks_statistic(train, live)
    return {
        "feature": feature,
        "kind": "numeric",
        "psi": psi,
        "status": classify_psi(psi),
        "ks": ks["statistic"],
        "ks_p": ks["p_value"],
        "train_mean": float(np.mean(train)),
        "live_mean": float(np.mean(live)),
    }


def categorical_drift(train: Sequence[str], live: Sequence[str], feature: str) -> dict:
    psi = categorical_psi(train, live)
    return {
        "feature": feature,
        "kind": "categorical",
        "psi": psi,
        "status": classify_psi(psi),
        "ks": float("nan"),
        "ks_p": float("nan"),
        "train_mean": float("nan"),
        "live_mean": float("nan"),
    }


def drift_report(train_rows: Sequence[dict], live_rows: Sequence[dict], numeric: Sequence[str],
                 categorical: Sequence[str]) -> dict:
    features = [numeric_drift([row[name] for row in train_rows], [row[name] for row in live_rows], name)
                for name in numeric]
    features += [categorical_drift([str(row[name]) for row in train_rows],
                                   [str(row[name]) for row in live_rows], name)
                 for name in categorical]
    worst = max(features, key=lambda item: (item["psi"] if item["psi"] == item["psi"] else -1))
    return {
        "features": features,
        "worst": worst["feature"],
        "significant": [item["feature"] for item in features if item["status"] == "significant"],
        "decision": "investigate" if any(item["status"] == "significant" for item in features) else "hold",
    }
