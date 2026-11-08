"""Evaluation beyond a single accuracy number: robustness, calibration, errors.

An accuracy computed on a clean, synthetic test split is one narrow measurement.
This module adds the two that change decisions:

* **Robustness** - the same test set under brightness shift, noise, blur,
  compression, and occlusion. Accuracy that collapses under a mild brightness
  change describes a model that learned the lighting of the training set.
* **Calibration** - whether predicted confidence matches observed accuracy. A
  deployment threshold is only meaningful if it is calibrated.

Plus error analysis, which is what actually improves a model: not "accuracy is
0.81" but "these 12 images were called circle when they are triangle, and they
are all the ones with the softest edges".
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import torch

from .datasets import ImageRecord
from .imaging import IMAGENET_MEAN, IMAGENET_STD, add_noise, adjust_brightness, blur, jpeg_roundtrip, occlude
from .metrics import classification_report, expected_calibration_error
from .training import predict


def robustness_suite(
    model: torch.nn.Module,
    images: np.ndarray,
    labels: Sequence[int],
    mean: Sequence[float] = IMAGENET_MEAN,
    std: Sequence[float] = IMAGENET_STD,
    class_names: Sequence[str] | None = None,
) -> dict:
    """Accuracy under a fixed set of degradations, each applied to the same images.

    The conditions are deliberately mild. A model that survives 0.7x brightness but
    not 0.4x is telling you something specific about its training data; one that
    fails at 0.9x is unusable.
    """
    labels = list(labels)
    conditions: list[tuple[str, callable]] = [
        ("clean", lambda imgs: imgs),
        ("brightness 1.3x", lambda imgs: np.stack([adjust_brightness(i, 1.3) for i in imgs])),
        ("brightness 0.7x", lambda imgs: np.stack([adjust_brightness(i, 0.7) for i in imgs])),
        ("gaussian noise 0.08", lambda imgs: np.stack([add_noise(i, 0.08, seed=k) for k, i in enumerate(imgs)])),
        ("blur radius 1.2", lambda imgs: np.stack([blur(i, 1.2) for i in imgs])),
        ("jpeg quality 30", lambda imgs: np.stack([jpeg_roundtrip(i, 30) for i in imgs])),
        (
            "occlusion 25%",
            lambda imgs: np.stack(
                [occlude(i, (0, 0, i.shape[1] // 2, i.shape[0] // 2)) for i in imgs]
            ),
        ),
    ]

    clean_accuracy = None
    rows = []
    for name, transform in conditions:
        degraded = transform(images)
        predicted, _ = predict(model, degraded, mean, std)
        accuracy = float(np.mean(np.asarray(predicted) == np.asarray(labels)))
        if clean_accuracy is None:
            clean_accuracy = accuracy
        rows.append({"condition": name, "accuracy": accuracy, "delta": accuracy - clean_accuracy})

    worst = min(rows, key=lambda r: r["accuracy"])
    return {
        "conditions": rows,
        "clean_accuracy": clean_accuracy,
        "worst_condition": worst["condition"],
        "worst_accuracy": worst["accuracy"],
        "max_drop": clean_accuracy - worst["accuracy"],
    }


def format_robustness(report: dict) -> str:
    lines = [f"{'condition':<22} {'accuracy':>9} {'delta':>8}", "-" * 41]
    for row in report["conditions"]:
        lines.append(f"{row['condition']:<22} {row['accuracy']:>9.3f} {row['delta']:>+8.3f}")
    lines.append(f"\nworst: {report['worst_condition']} (drop {report['max_drop']:.3f})")
    return "\n".join(lines)


@dataclass
class ErrorCase:
    index: int
    true_label: int
    predicted: int
    confidence: float

    def as_dict(self) -> dict:
        return {
            "index": self.index,
            "true": self.true_label,
            "predicted": self.predicted,
            "confidence": round(self.confidence, 4),
        }


def error_analysis(
    model: torch.nn.Module,
    images: np.ndarray,
    labels: Sequence[int],
    class_names: Sequence[str],
    mean: Sequence[float] = IMAGENET_MEAN,
    std: Sequence[float] = IMAGENET_STD,
    top_n: int = 10,
) -> dict:
    """Per-class report, most confused class pairs, and the most confident errors.

    Sorting errors by confidence is the highest-value trick in this module: a
    wrong answer at 0.99 confidence is a different bug from a wrong answer at 0.36.
    """
    predicted, probs = predict(model, images, mean, std)
    predicted = list(map(int, predicted))
    labels = list(map(int, labels))
    report = classification_report(labels, predicted, class_names)

    pairs: dict[str, int] = {}
    for truth, pred in zip(labels, predicted):
        if truth != pred:
            key = f"{class_names[truth]} -> {class_names[pred]}"
            pairs[key] = pairs.get(key, 0) + 1

    errors = [
        ErrorCase(i, labels[i], predicted[i], float(probs[i][predicted[i]]))
        for i in range(len(labels))
        if labels[i] != predicted[i]
    ]
    errors.sort(key=lambda e: -e.confidence)

    return {
        "report": report,
        "confusion_pairs": dict(sorted(pairs.items(), key=lambda kv: -kv[1])),
        "most_confident_errors": [e.as_dict() for e in errors[:top_n]],
        "n_errors": len(errors),
        "n_samples": len(labels),
    }


def calibration_summary(
    confidences: Sequence[float],
    correct: Sequence[int],
    n_bins: int = 5,
) -> dict:
    """ECE plus the per-bin table, so the gap can be seen, not just quoted."""
    conf = np.asarray(confidences, dtype=np.float64)
    hit = np.asarray(correct, dtype=np.float64)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    rows = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (conf > lo) & (conf <= hi)
        if mask.sum() == 0:
            continue
        rows.append(
            {
                "bin": f"{lo:.2f}-{hi:.2f}",
                "n": int(mask.sum()),
                "mean_confidence": float(conf[mask].mean()),
                "accuracy": float(hit[mask].mean()),
                "gap": float(conf[mask].mean() - hit[mask].mean()),
            }
        )
    return {"ece": expected_calibration_error(list(conf), list(hit), n_bins), "bins": rows, "n": int(conf.size)}


def format_calibration(report: dict) -> str:
    lines = [f"{'bin':>10} {'n':>5} {'confidence':>11} {'accuracy':>9} {'gap':>7}", "-" * 46]
    for row in report["bins"]:
        lines.append(
            f"{row['bin']:>10} {row['n']:>5} {row['mean_confidence']:>11.3f} {row['accuracy']:>9.3f} {row['gap']:>+7.3f}"
        )
    lines.append(f"\nECE: {report['ece']:.4f}")
    return "\n".join(lines)


def worst_examples(images: np.ndarray, analysis: dict, limit: int = 5) -> list[np.ndarray]:
    """Raw arrays for the most confident mistakes, for saving into a report."""
    return [images[e["index"]] for e in analysis["most_confident_errors"][:limit]]


def save_worst_examples(directory: str | Path, images: np.ndarray, analysis: dict, class_names: Sequence[str], limit: int = 5) -> list[Path]:
    """Write the confident mistakes as PNGs named with their truth and prediction."""
    from .imaging import save_image

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for e in analysis["most_confident_errors"][:limit]:
        name = f"err_{e['index']:03d}_{class_names[e['true']]}_as_{class_names[e['predicted']]}.png"
        written.append(save_image(images[e["index"]], directory / name))
    return written
