"""Detector training, heatmap target construction, and threshold sweeps.

The detector is a centre-heatmap network (see ``models.TinyHeatmapDetector``).
Three steps carry almost all of the teaching weight:

1. **Targets.** Each ground-truth box becomes a Gaussian bump on a low-resolution
   grid. Two boxes close together produce overlapping bumps, which is why the
   decode step cannot simply take ``argmax``.
2. **Decode.** Peaks become boxes: threshold the sigmoid, find local maxima,
   read the size head at each peak, then apply NMS.
3. **Thresholding.** The score threshold is a *choice* with a cost curve, not a
   constant. Lab 6 sweeps it and reports precision and recall at each point.
"""

from __future__ import annotations

import time
from typing import Sequence

import numpy as np
import torch
import torch.nn as nn

from .annotations import Annotation
from .datasets import ImageRecord
from .metrics import evaluate_detections, mean_average_precision
from .models import TinyHeatmapDetector, set_seed
from .training import prepare_inputs

# Class index order for the synthetic detection corpus; must match
# ``datasets.SHAPE_CLASSES`` so YOLO labels and predictions agree.
SHAPE_INDEX: dict[str, int] = {"circle": 0, "square": 1, "triangle": 2}


# ---------------------------------------------------------------------------
# Target construction
# ---------------------------------------------------------------------------


def gaussian_radius(size: float, stride: int) -> float:
    """Radius in heatmap cells for an object of ``size`` pixels."""
    return float(max(1.0, (size / stride) * 0.6))


def build_heatmap_target(
    boxes: Sequence[Annotation],
    width: int,
    height: int,
    num_classes: int,
    stride: int = 4,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Create ``(heat, size, mask)`` targets for one image.

    ``heat`` is a clean Gaussian per object centre, ``size`` holds normalized
    width/height at those centres, and ``mask`` marks the cells whose size loss
    should count. Without the mask the network learns to predict size everywhere,
    including empty background, and the size head dominates the loss.
    """
    gw, gh = width // stride, height // stride
    heat = np.zeros((num_classes, gh, gw), dtype=np.float32)
    size = np.zeros((2, gh, gw), dtype=np.float32)
    mask = np.zeros((1, gh, gw), dtype=np.float32)

    yy, xx = np.mgrid[0:gh, 0:gw]
    for ann in boxes:
        if not 0 <= ann.class_id < num_classes:
            continue
        x1, y1, x2, y2 = ann.box
        bw, bh = max(1.0, x2 - x1), max(1.0, y2 - y1)
        cx, cy = (x1 + x2) / 2.0 / stride, (y1 + y2) / 2.0 / stride
        radius = gaussian_radius(max(bw, bh), stride)
        gauss = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * radius**2)))
        heat[ann.class_id] = np.maximum(heat[ann.class_id], gauss)

        # Supervise size on the whole bump, not one cell: a single cell per object
        # is ~2 gradients per batch and the size head stays at the dataset mean.
        region = gauss >= 0.5
        size[0][region] = bw / width
        size[1][region] = bh / height
        mask[0][region] = 1.0
    return heat, size, mask


def records_to_targets(
    records: Sequence[ImageRecord],
    num_classes: int,
    stride: int = 4,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Stack targets for a list of records - one place where the class map is applied."""
    heats, sizes, masks = [], [], []
    for rec in records:
        h, w = rec.image.shape[:2]
        boxes = [Annotation(SHAPE_INDEX[o["class"]], tuple(o["xyxy"])) for o in rec.meta["boxes"]]
        heat, size, mask = build_heatmap_target(boxes, w, h, num_classes, stride)
        heats.append(heat)
        sizes.append(size)
        masks.append(mask)
    return np.stack(heats), np.stack(sizes), np.stack(masks)


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------


def centernet_focal_loss(logits: torch.Tensor, target: torch.Tensor, alpha: float = 2.0, beta: float = 4.0) -> torch.Tensor:
    """Penalty-reduced focal loss (Zhou et al., CenterNet).

    ``target`` is a Gaussian, not 0/1, so cells *near* a centre are down-weighted
    by ``(1 - target)`` instead of being punished as hard negatives. Positive cells
    get ``(1 - p) ** alpha`` so easy, already-confident cells stop dominating.
    """
    prob = torch.sigmoid(logits).clamp(1e-4, 1.0 - 1e-4)
    pos = -((1.0 - prob) ** alpha) * torch.log(prob) * ((target >= 1.0).float())
    neg = -((1.0 - target) ** beta) * (prob**alpha) * torch.log(1.0 - prob) * ((target < 1.0).float())
    n_pos = (target >= 1.0).float().sum().clamp(min=1.0)
    return (pos + neg).sum() / n_pos


def train_detector(
    records: Sequence[ImageRecord],
    num_classes: int,
    *,
    stride: int = 4,
    width: int = 16,
    epochs: int = 10,
    batch_size: int = 16,
    lr: float = 2e-3,
    seed: int = 0,
    heatmap_weight: float = 1.0,
    size_weight: float = 0.1,
    loss: str = "focal",
    pos_weight: float = 1.0,
    log: bool = True,
) -> tuple[TinyHeatmapDetector, dict]:
    """Train the heatmap detector on annotated records.

    Loss: the CenterNet penalty-reduced focal loss on the heatmap plus L1 on box
    size at centre cells only.

    The imbalance here is roughly 1 positive cell to 250 background cells, so the
    loss matters as much as the architecture. Plain BCE collapses to "background
    everywhere"; BCE with a large ``pos_weight`` does the opposite and saturates
    every cell to "object", which yields a box per cell and mAP of zero. Passing
    ``loss="bce"`` reproduces both failures and is the Lab 5 error analysis.
    """
    set_seed(seed)
    model = TinyHeatmapDetector(num_classes=num_classes, width=width, stride=stride)

    x_all = prepare_inputs(np.stack([r.image for r in records]))
    heat_np, size_np, mask_np = records_to_targets(records, num_classes, stride)
    y_heat = torch.from_numpy(heat_np)
    y_size = torch.from_numpy(size_np)
    y_mask = torch.from_numpy(mask_np)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    rng = np.random.default_rng(seed)
    history: dict = {"loss": [], "heat_loss": [], "size_loss": [], "seconds": [], "epochs": epochs}

    for epoch in range(1, epochs + 1):
        started = time.perf_counter()
        model.train()
        order = rng.permutation(len(records))
        totals = np.zeros(3)
        for start in range(0, len(order), batch_size):
            idx = order[start : start + batch_size]
            optimizer.zero_grad()
            heat_logits, size_pred = model(x_all[idx])

            if loss == "focal":
                heat_loss = centernet_focal_loss(heat_logits, y_heat[idx])
            else:
                heat_loss = nn.functional.binary_cross_entropy_with_logits(
                    heat_logits, y_heat[idx], pos_weight=torch.tensor(float(pos_weight))
                )
            size_loss = (torch.abs(size_pred - y_size[idx]) * y_mask[idx]).sum() / y_mask[idx].sum().clamp(min=1.0)
            loss = heatmap_weight * heat_loss + size_weight * size_loss
            loss.backward()
            optimizer.step()
            totals += [float(loss.item()), float(heat_loss.item()), float(size_loss.item())]

        n_batches = max(1, int(np.ceil(len(order) / batch_size)))
        history["loss"].append(totals[0] / n_batches)
        history["heat_loss"].append(totals[1] / n_batches)
        history["size_loss"].append(totals[2] / n_batches)
        history["seconds"].append(time.perf_counter() - started)
        if log:
            print(
                f"epoch {epoch:2d}  loss {history['loss'][-1]:.4f}  "
                f"heat {history['heat_loss'][-1]:.4f}  size {history['size_loss'][-1]:.4f}"
            )

    model.eval()
    history["total_seconds"] = float(sum(history["seconds"]))
    return model, history


def quick_detector_metrics(
    model: nn.Module,
    records: Sequence[ImageRecord],
    class_names: Sequence[str],
    stride: int = 4,
    score_threshold: float = 0.3,
) -> dict:
    """Convenience wrapper: decode, then report mAP and fixed-threshold metrics."""
    from .detection import predict_records

    results = predict_records(model, records, stride=stride, score_threshold=score_threshold)
    map50 = mean_average_precision(results, class_names, (0.5,))
    fixed = evaluate_detections(results, class_names, 0.5, score_threshold)
    return {
        "map50": map50["map"],
        "per_class_ap50": map50["per_class_ap50"],
        "precision": fixed["precision"],
        "recall": fixed["recall"],
        "f1": fixed["f1"],
        "n_predictions": sum(len(r.predictions) for r in results),
    }
