"""Semantic segmentation: a trained U-Net, a threshold baseline, and metrics.

Two segmenters share one interface so they can be compared on identical masks:

* :func:`threshold_baseline` - a classical method with no training at all. Useful
  because it shows how much of the task a hand-written rule already solves, and
  because it fails in ways that are easy to explain.
* :class:`~vision_core.models.TinyUNet` - trained with cross-entropy per pixel.

``per_class`` metrics matter more than pixel accuracy here: the background is
most of the image, so an all-background predictor can exceed 70% pixel accuracy
while being useless. That is measured, not asserted.
"""

from __future__ import annotations

import time
from typing import Sequence

import numpy as np
import torch
import torch.nn as nn

from .datasets import SEGMENTATION_CLASSES, ImageRecord
from .metrics import segmentation_report
from .models import TinyUNet, set_seed
from .training import prepare_inputs


# ---------------------------------------------------------------------------
# Classical baseline
# ---------------------------------------------------------------------------


def threshold_baseline(image: np.ndarray, tolerance: int = 18) -> np.ndarray:
    """Segment object vs background by distance from the background colour.

    The background is estimated as the median colour of the image border, which
    is true for the synthetic corpus and false in general. This is the method's
    honest limitation, and Lab 5's error analysis asks students to trigger it.
    """
    arr = image.astype(np.float32)
    h, w = arr.shape[:2]
    border = np.concatenate([arr[0, :], arr[-1, :], arr[:, 0], arr[:, -1]]).reshape(-1, 3)
    background = np.median(border, axis=0)
    distance = np.abs(arr - background).sum(axis=2)
    mask = np.zeros((h, w), dtype=np.uint8)
    mask[distance > tolerance * 3] = 1
    return mask


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------


def train_segmenter(
    records: Sequence[ImageRecord],
    *,
    num_classes: int = len(SEGMENTATION_CLASSES),
    width: int = 8,
    epochs: int = 8,
    batch_size: int = 8,
    lr: float = 2e-3,
    seed: int = 0,
    use_skip: bool = True,
    class_weights: Sequence[float] | None = None,
    log: bool = True,
) -> tuple[TinyUNet, dict]:
    """Train the U-Net with per-pixel cross-entropy.

    ``class_weights`` matter because the shadow class is a small fraction of
    pixels; without weighting, the model learns to ignore it and the shadow IoU
    is near zero.
    """
    set_seed(seed)
    model = TinyUNet(num_classes=num_classes, width=width, use_skip=use_skip)
    images = np.stack([r.image for r in records])
    masks = np.stack([r.meta["mask"] for r in records])
    x = prepare_inputs(images)
    y = torch.from_numpy(masks.astype(np.int64))

    # ``is not None``, not truthiness: a NumPy array has no single truth value.
    weight = torch.as_tensor(list(class_weights), dtype=torch.float32) if class_weights is not None else None
    criterion = nn.CrossEntropyLoss(weight=weight)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    history: dict = {"loss": [], "pixel_accuracy": [], "seconds": []}
    rng = np.random.default_rng(seed)
    n_train = max(1, int(len(records) * 0.8))

    for epoch in range(1, epochs + 1):
        started = time.perf_counter()
        model.train()
        order = rng.permutation(n_train)
        total = 0.0
        for start in range(0, len(order), batch_size):
            idx = order[start : start + batch_size]
            optimizer.zero_grad()
            logits = model(x[idx])
            loss = criterion(logits, y[idx])
            loss.backward()
            optimizer.step()
            total += float(loss.item())

        model.eval()
        with torch.no_grad():
            val_logits = model(x[n_train:])
            preds = val_logits.argmax(1)
            acc = float((preds == y[n_train:]).float().mean())
        history["loss"].append(total / max(1, int(np.ceil(len(order) / batch_size))))
        history["pixel_accuracy"].append(acc)
        history["seconds"].append(time.perf_counter() - started)
        if log:
            print(f"epoch {epoch:2d}  loss {history['loss'][-1]:.4f}  val_pixel_acc {acc:.3f}")

    history["total_seconds"] = float(sum(history["seconds"]))
    model.eval()
    return model, history


# ---------------------------------------------------------------------------
# Inference and evaluation
# ---------------------------------------------------------------------------


def predict_masks(model: nn.Module, records: Sequence[ImageRecord], batch_size: int = 8) -> np.ndarray:
    """Predicted class mask (HxW uint8) for each record."""
    images = np.stack([r.image for r in records])
    x = prepare_inputs(images)
    outputs = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(x), batch_size):
            outputs.append(model(x[start : start + batch_size]).argmax(1))
    return torch.cat(outputs).numpy().astype(np.uint8)


def evaluate_segmenter(
    model: nn.Module | None,
    records: Sequence[ImageRecord],
    class_names: Sequence[str] = SEGMENTATION_CLASSES,
    *,
    baseline: bool = False,
) -> dict:
    """Aggregate metrics over a record set, for either segmenter.

    Aggregation is over the pooled confusion matrix, not the mean of per-image
    IoUs: classes absent from a particular image should not get a free vote.
    """
    from .metrics import confusion_matrix

    n = len(class_names)
    total = np.zeros((n, n), dtype=np.int64)
    per_image = []
    for rec, pred in zip(records, _masks_for(model, records, baseline)):
        total += confusion_matrix(pred, rec.meta["mask"], n)
        per_image.append(segmentation_report(pred, rec.meta["mask"], class_names)["mean_iou"])

    tp = np.diag(total).astype(np.float64)
    fp = total.sum(axis=0) - tp
    fn = total.sum(axis=1) - tp
    iou = np.where((tp + fp + fn) > 0, tp / np.maximum(tp + fp + fn, 1e-12), np.nan)
    dice = np.where((2 * tp + fp + fn) > 0, 2 * tp / np.maximum(2 * tp + fp + fn, 1e-12), np.nan)
    return {
        "pixel_accuracy": float(tp.sum() / max(total.sum(), 1)),
        "mean_iou": float(np.nanmean(iou)),
        "per_class_iou": {name: (None if np.isnan(iou[i]) else float(iou[i])) for i, name in enumerate(class_names)},
        "per_class_dice": {name: (None if np.isnan(dice[i]) else float(dice[i])) for i, name in enumerate(class_names)},
        "mean_image_iou": float(np.mean(per_image)) if per_image else 0.0,
        "confusion_matrix": total.tolist(),
        "n_images": len(records),
    }


def _masks_for(model: nn.Module | None, records: Sequence[ImageRecord], baseline: bool):
    if baseline:
        return [threshold_baseline(r.image) for r in records]
    if model is None:
        raise ValueError("a model is required unless baseline=True")
    return predict_masks(model, records)


def all_background_baseline(records: Sequence[ImageRecord], class_names: Sequence[str] = SEGMENTATION_CLASSES) -> dict:
    """The 'predict background everywhere' control.

    Reported in the module because it is the fastest way to show that pixel
    accuracy alone cannot distinguish a segmenter from a constant.
    """
    n = len(class_names)
    total = np.zeros((n, n), dtype=np.int64)
    from .metrics import confusion_matrix

    for rec in records:
        zeros = np.zeros_like(rec.meta["mask"], dtype=np.uint8)
        total += confusion_matrix(zeros, rec.meta["mask"], n)
    tp = np.diag(total).astype(np.float64)
    fp = total.sum(axis=0) - tp
    fn = total.sum(axis=1) - tp
    iou = np.where((tp + fp + fn) > 0, tp / np.maximum(tp + fp + fn, 1e-12), np.nan)
    return {
        "pixel_accuracy": float(tp.sum() / max(total.sum(), 1)),
        "mean_iou": float(np.nanmean(iou)),
        "per_class_iou": {name: (None if np.isnan(iou[i]) else float(iou[i])) for i, name in enumerate(class_names)},
    }


def overlay_mask(image: np.ndarray, mask: np.ndarray, alpha: float = 0.45) -> np.ndarray:
    """Colour a predicted mask over the image, for visual inspection."""
    colours = np.array([[0, 0, 0], [60, 200, 90], [80, 120, 220]], dtype=np.float32)
    base = image.astype(np.float32) / 255.0
    colour_layer = colours[np.clip(mask, 0, len(colours) - 1)]
    blended = base * (1 - alpha) + colour_layer * alpha
    return (np.clip(blended, 0, 1) * 255).astype(np.uint8)
