"""Garment attributes: a narrow, observable label set, and where it breaks.

Two rules drove every design choice in this module.

**Narrow and observable.** The label set is garment *category* (shirt, trousers, jacket, hat)
and garment *colour* (six colours). Both are things a person can point at and agree on.
Nothing here infers body shape, age, gender, ethnicity, health, or identity, and the model
has no output that could be reinterpreted as any of those. Lab 5 asks students to keep it
that way when they extend the label set.

**Measured under perturbation.** A colour classifier at 99% on clean images tells you
nothing about a shopping arcade at night. The evaluation in :func:`robustness_sweep` varies
one factor at a time - brightness (lighting), occlusion, and background - and reports the
accuracy for each level. That table, not the headline number, is the honest summary of the
model, and it is the table Lab 5 asks students to explain.

The model is a small two-head CNN trained from scratch on synthetic garments, so there are
no dataset licences to negotiate. Module 10 and Lab 5 explain how to swap in a licensed
real dataset (DeepFashion, Fashion-MNIST as the toy option) and what changes.
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from . import metrics
from . import synth
from .detect import set_seed


class GarmentNet(nn.Module):
    """Shared trunk, two heads: one for category, one for colour.

    Two heads rather than one joint 24-way classifier because the tasks have different
    difficulty and different failure modes: category survives colour changes, colour does
    not survive lighting changes. Separate heads make that visible in the metrics.
    """

    def __init__(self, num_categories: int = len(synth.GARMENT_CATEGORIES),
                 num_colours: int = len(synth.GARMENT_COLOURS), width: int = 16) -> None:
        super().__init__()
        w = width
        self.trunk = nn.Sequential(
            nn.Conv2d(3, w, 3, 2, 1), nn.BatchNorm2d(w), nn.ReLU(inplace=True),
            nn.Conv2d(w, 2 * w, 3, 2, 1), nn.BatchNorm2d(2 * w), nn.ReLU(inplace=True),
            nn.Conv2d(2 * w, 4 * w, 3, 2, 1), nn.BatchNorm2d(4 * w), nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(1),
        )
        self.category_head = nn.Linear(4 * w, num_categories)
        self.colour_head = nn.Linear(4 * w, num_colours)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        feat = self.trunk(x).flatten(1)
        return self.category_head(feat), self.colour_head(feat)


def as_float01(images: np.ndarray) -> np.ndarray:
    """Accept either uint8 [0,255] or float [0,1] and return float [0,1].

    The generators return float [0,1]; a video frame arrives as uint8. Supporting both
    quietly is worth four lines here, because the alternative is a lab that silently
    trains on images 255x too bright.
    """
    arr = np.asarray(images, dtype=np.float32)
    if arr.size and float(arr.max()) > 1.5:
        arr = arr / 255.0
    return arr


def _to_tensor(images: np.ndarray) -> torch.Tensor:
    """NHWC -> NCHW float [0,1]."""
    arr = torch.from_numpy(as_float01(images))
    return arr.permute(0, 3, 1, 2).contiguous()


def perturb(images: np.ndarray, *, brightness: float = 1.0, occlusion: float = 0.0,
            background: float = 0.0, seed: int = 0) -> np.ndarray:
    """Apply one degradation to a batch of garment images.

    ``occlusion`` draws a black rectangle over the given fraction of the image's area from
    the left edge - the "another shopper walked in front of you" case. ``background`` blends
    the image towards a mid-grey, which is the cheap way to say "the shop's background
    changed and the garment no longer dominates the frame".

    Returns float32 in ``[0, 1]``, the same convention as :func:`synth.garment_dataset`.
    """
    out = as_float01(images).copy()
    if brightness != 1.0:
        out = np.clip(out * brightness, 0.0, 1.0)
    if background:
        out = out * (1.0 - background) + 0.5 * background
    if occlusion > 0:
        rng = np.random.default_rng(seed)
        h, w = out.shape[1:3]
        for i in range(len(out)):
            frac = float(rng.uniform(0.5, 1.0)) * occlusion
            cut = int(round(frac * w))
            if cut > 0:
                start = int(rng.integers(0, max(w - cut, 1)))
                out[i, :, start:start + cut, :] = 0.0
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def train_garment_model(images: np.ndarray, categories: np.ndarray, colours: np.ndarray, *,
                        epochs: int = 14, lr: float = 2e-3, seed: int = 0,
                        log: bool = False) -> tuple[GarmentNet, dict]:
    set_seed(seed)  # before construction, for reproducible init
    model = GarmentNet()
    optimiser = torch.optim.Adam(model.parameters(), lr=lr)
    x = _to_tensor(images)
    yc = torch.from_numpy(categories).long()
    yk = torch.from_numpy(colours).long()
    history = {"loss": [], "category_acc": [], "colour_acc": []}
    n = len(x)
    for epoch in range(1, epochs + 1):
        model.train()
        order = np.random.default_rng(seed + epoch).permutation(n)
        total, batches = 0.0, 0
        for start in range(0, n, 64):
            idx = order[start:start + 64]
            logits_c, logits_k = model(x[idx])
            loss = F.cross_entropy(logits_c, yc[idx]) + F.cross_entropy(logits_k, yk[idx])
            optimiser.zero_grad()
            loss.backward()
            optimiser.step()
            total += float(loss.detach())
            batches += 1
        history["loss"].append(round(total / max(batches, 1), 4))
        if log and (epoch == 1 or epoch % 4 == 0 or epoch == epochs):
            cat_pred, col_pred = predict_garments(model, images)
            history["category_acc"].append(round(float(np.mean(cat_pred == categories)), 3))
            history["colour_acc"].append(round(float(np.mean(col_pred == colours)), 3))
            print(f"  garment epoch {epoch:2d} loss {history['loss'][-1]:.3f} "
                  f"cat {history['category_acc'][-1]:.3f} col {history['colour_acc'][-1]:.3f}")
    model.eval()
    return model, history


@torch.no_grad()
def predict_garments(model: GarmentNet, images: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    model.eval()
    logits_c, logits_k = model(_to_tensor(images))
    return logits_c.argmax(1).numpy(), logits_k.argmax(1).numpy()


def robustness_sweep(model: GarmentNet, images: np.ndarray, categories: np.ndarray,
                     colours: np.ndarray) -> list[dict]:
    """One factor at a time: clean, dim, dark, occluded, and background-shifted frames."""
    conditions = [
        ("clean", {}),
        ("brightness_x0.7", {"brightness": 0.7}),
        ("brightness_x0.45", {"brightness": 0.45}),
        ("occlusion_30pct", {"occlusion": 0.3}),
        ("occlusion_55pct", {"occlusion": 0.55}),
        ("background_40pct", {"background": 0.4}),
        ("dark_plus_occlusion", {"brightness": 0.55, "occlusion": 0.35}),
    ]
    rows = []
    for name, kwargs in conditions:
        degraded = perturb(images, seed=3, **kwargs)
        cat_pred, col_pred = predict_garments(model, degraded)
        rows.append({
            "condition": name,
            "category_acc": round(float(np.mean(cat_pred == categories)), 3),
            "colour_acc": round(float(np.mean(col_pred == colours)), 3),
        })
    return rows


def category_report(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    return metrics.classification_report(y_true, y_pred, synth.GARMENT_CATEGORIES)


def colour_report(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    return metrics.classification_report(y_true, y_pred, synth.GARMENT_COLOURS)


def class_confusions(y_true: np.ndarray, y_pred: np.ndarray, names: list[str],
                     *, top: int = 4) -> list[dict]:
    """The most frequent mistakes as ``true -> predicted`` pairs with counts."""
    pairs: dict[tuple[int, int], int] = {}
    for t, p in zip(y_true.tolist(), y_pred.tolist()):
        if t != p:
            pairs[(t, p)] = pairs.get((t, p), 0) + 1
    ordered = sorted(pairs.items(), key=lambda kv: -kv[1])[:top]
    return [{"true": names[t], "predicted": names[p], "count": int(c)} for (t, p), c in ordered]


def sensitive_attribute_statement() -> str:
    """Reusable text for reports: what this model does *not* predict, and why."""
    return (
        "Label set: garment category and garment colour only. The model has no output for "
        "gender, age, ethnicity, body shape, health, mood, or identity, and no code path "
        "that could produce one. Predicting sensitive attributes from appearance is "
        "unreliable (it is guessing, not measuring) and is unlawful for many purposes "
        "under GDPR Art. 9 and equivalent regimes. If a task appears to need it, the task "
        "needs redesigning, not a bigger model."
    )
