"""From-scratch versus transfer learning, on a machine with no internet.

The honest problem: transfer learning means "start from a backbone trained on a
large dataset", and this section must not require a 100 MB download. Two paths
are provided, and the difference between them is stated in every lab that uses
it:

* **Offline stand-in (default).** A ``TinyCNN`` trunk is trained on a broad
  synthetic set of shapes and objects, saved as a checkpoint, then reused as the
  starting point for a narrow task. The *mechanism* is identical to ImageNet
  transfer: frozen features, then a linear probe, then partial unfreezing. The
  *benefit* is not identical, because the pretraining set is tiny and synthetic.
* **Real torchvision weights (optional).** :func:`torchvision_backbone` attempts
  to load pretrained weights and reports precisely why it could not, instead of
  raising a stack trace or silently training from random weights.

A student who reports "transfer learning gave +12 points" after using the
stand-in is overclaiming; the docs say so, and the labs print a reminder.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import torch
import torch.nn as nn

from .models import TinyCNN, load_checkpoint, save_checkpoint, set_seed
from .training import History, dataset_stats, prepare_inputs, train_classifier


@dataclass
class TransferResult:
    """The three conditions compared in Lab 3."""

    name: str
    history: History
    test_accuracy: float
    n_trainable_parameters: int
    seconds: float

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "test_accuracy": self.test_accuracy,
            "n_trainable_parameters": self.n_trainable_parameters,
            "seconds": round(self.seconds, 2),
            "epochs": self.history.epochs,
            "best_val_acc": self.history.best_val_acc,
            "overfitting_gap": self.history.overfitting_gap(),
        }


# ---------------------------------------------------------------------------
# Building the offline "pretrained" backbone
# ---------------------------------------------------------------------------


def build_pretrained_backbone(
    images: np.ndarray,
    labels: Sequence[int],
    num_classes: int,
    *,
    width: int = 16,
    epochs: int = 20,
    batch_size: int = 16,
    lr: float = 2e-3,
    seed: int = 0,
    out_path: str | Path | None = None,
    log: bool = True,
) -> tuple[TinyCNN, History]:
    """Pretrain a trunk on a broad synthetic set and optionally save it.

    This is the artefact every transfer lab starts from. It is saved as a state
    dict plus metadata, so a student can inspect it and so the labs never depend
    on a live download.
    """
    model = TinyCNN(num_classes=num_classes, width=width)
    # Use a slice of data for validation so the curve is meaningful even here.
    n_val = max(1, int(len(labels) * 0.2))
    history, model = train_classifier(
        model,
        images[:-n_val],
        list(labels)[:-n_val],
        images[-n_val:],
        list(labels)[-n_val:],
        epochs=epochs,
        batch_size=batch_size,
        lr=lr,
        seed=seed,
        log=log,
    )
    if out_path is not None:
        save_checkpoint(
            model,
            out_path,
            {
                "kind": "offline-pretrained-backbone",
                "honest_note": "tiny synthetic pretraining, NOT ImageNet",
                "classes": int(num_classes),
                "width": int(width),
                "val_acc": history.best_val_acc,
            },
        )
    return model, history


# ---------------------------------------------------------------------------
# Three conditions: scratch, frozen features, partial fine-tune
# ---------------------------------------------------------------------------


def build_head(model: TinyCNN, num_classes: int) -> TinyCNN:
    """Replace the classifier head for a new task and reset it."""
    model.classifier = nn.Linear(model.feature_dim, num_classes)
    return model


def freeze_trunk(model: TinyCNN) -> int:
    """Freeze everything except the classifier. Returns trainable parameter count."""
    for param in model.parameters():
        param.requires_grad = False
    for param in model.classifier.parameters():
        param.requires_grad = True
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def unfreeze_last_block(model: TinyCNN) -> int:
    """Frozen features plus block3 trainable: the usual middle ground."""
    freeze_trunk(model)
    for param in model.block3.parameters():
        param.requires_grad = True
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def train_linear_probe(
    backbone: TinyCNN,
    train_images: np.ndarray,
    train_labels: Sequence[int],
    val_images: np.ndarray,
    val_labels: Sequence[int],
    num_classes: int,
    *,
    epochs: int = 10,
    lr: float = 1e-2,
    seed: int = 0,
    log: bool = True,
) -> tuple[TinyCNN, History]:
    """Train only the head on frozen features.

    A higher learning rate is used deliberately: with a frozen trunk there is no
    risk of destroying pretrained filters, and the head is randomly initialized.
    """
    import copy

    model = copy.deepcopy(backbone)
    build_head(model, num_classes)
    n_trainable = freeze_trunk(model)
    mean, std = dataset_stats(train_images)
    history, model = train_classifier(
        model,
        train_images,
        train_labels,
        val_images,
        val_labels,
        epochs=epochs,
        lr=lr,
        seed=seed,
        normalize_stats=(mean, std),
        log=log,
    )
    history.extra["trainable_parameters"] = n_trainable
    return model, history


def train_partial_finetune(
    backbone: TinyCNN,
    train_images: np.ndarray,
    train_labels: Sequence[int],
    val_images: np.ndarray,
    val_labels: Sequence[int],
    num_classes: int,
    *,
    epochs: int = 10,
    lr: float = 1e-3,
    seed: int = 0,
    log: bool = True,
) -> tuple[TinyCNN, History]:
    """Unfreeze the last block and train it with the head at a lower learning rate."""
    import copy

    model = copy.deepcopy(backbone)
    build_head(model, num_classes)
    n_trainable = unfreeze_last_block(model)
    mean, std = dataset_stats(train_images)
    history, model = train_classifier(
        model,
        train_images,
        train_labels,
        val_images,
        val_labels,
        epochs=epochs,
        lr=lr,
        seed=seed,
        normalize_stats=(mean, std),
        log=log,
    )
    history.extra["trainable_parameters"] = n_trainable
    return model, history


def compare_scratch_vs_transfer(
    backbone: TinyCNN,
    train_images: np.ndarray,
    train_labels: Sequence[int],
    val_images: np.ndarray,
    val_labels: Sequence[int],
    test_images: np.ndarray,
    test_labels: Sequence[int],
    num_classes: int,
    *,
    seed: int = 0,
    epochs: int = 20,
    log: bool = True,
) -> list[TransferResult]:
    """Run the three conditions on identical data and return measured results.

    All three see the same train/val/test split, the same augmentation (none), and
    the same seed, so the only difference is where the weights started.
    """
    import copy
    import time

    from .training import predict

    results: list[TransferResult] = []
    mean, std = dataset_stats(train_images)

    started = time.perf_counter()
    scratch = TinyCNN(num_classes=num_classes, width=backbone.width)
    scratch_hist, scratch = train_classifier(
        scratch,
        train_images,
        train_labels,
        val_images,
        val_labels,
        epochs=epochs,
        lr=1e-3,
        seed=seed,
        normalize_stats=(mean, std),
        log=log,
    )
    scratch_pred, _ = predict(scratch, test_images, mean, std)
    results.append(
        TransferResult(
            "scratch",
            scratch_hist,
            float(np.mean(scratch_pred == np.asarray(test_labels))),
            sum(p.numel() for p in scratch.parameters()),
            time.perf_counter() - started,
        )
    )

    started = time.perf_counter()
    probe, probe_hist = train_linear_probe(
        copy.deepcopy(backbone), train_images, train_labels, val_images, val_labels, num_classes, seed=seed, log=log
    )
    probe_pred, _ = predict(probe, test_images, mean, std)
    results.append(
        TransferResult(
            "frozen features + linear probe",
            probe_hist,
            float(np.mean(probe_pred == np.asarray(test_labels))),
            int(probe_hist.extra.get("trainable_parameters", 0)),
            time.perf_counter() - started,
        )
    )

    started = time.perf_counter()
    tuned, tuned_hist = train_partial_finetune(
        copy.deepcopy(backbone), train_images, train_labels, val_images, val_labels, num_classes, seed=seed, log=log
    )
    tuned_pred, _ = predict(tuned, test_images, mean, std)
    results.append(
        TransferResult(
            "last block fine-tuned",
            tuned_hist,
            float(np.mean(tuned_pred == np.asarray(test_labels))),
            int(tuned_hist.extra.get("trainable_parameters", 0)),
            time.perf_counter() - started,
        )
    )
    return results


# ---------------------------------------------------------------------------
# Optional real pretrained weights
# ---------------------------------------------------------------------------


def torchvision_backbone(name: str = "resnet18") -> dict:
    """Try to load real pretrained weights; report the outcome honestly.

    Returns a dictionary with ``available``, ``reason``, ``model``, and
    ``feature_dim``. Never raises for the expected offline case - a lab that
    requires the internet must say so, not crash.
    """
    try:
        import torchvision.models as tvm
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"available": False, "reason": f"torchvision import failed: {exc}", "model": None, "feature_dim": 0}

    if not hasattr(tvm, name):
        return {"available": False, "reason": f"torchvision has no model {name!r}", "model": None, "feature_dim": 0}

    try:
        model = getattr(tvm, name)(weights="DEFAULT")
    except Exception as exc:  # downloads fail without network access
        return {
            "available": False,
            "reason": (
                "pretrained weights could not be loaded (no network access or download blocked). "
                f"Underlying error: {type(exc).__name__}: {exc}"
            ),
            "model": None,
            "feature_dim": 0,
        }

    for param in model.parameters():
        param.requires_grad = False
    feature_dim = getattr(model, "fc", None).in_features if hasattr(model, "fc") else 512
    model.fc = nn.Identity() if hasattr(model, "fc") else model
    return {"available": True, "reason": "loaded", "model": model.eval(), "feature_dim": int(feature_dim)}


def extract_features(backbone: nn.Module, images: np.ndarray, mean, std, batch_size: int = 32) -> np.ndarray:
    """Embedding vectors for a batch, from a model's ``features`` or forward pass."""
    x = prepare_inputs(images, mean, std)
    outputs = []
    backbone.eval()
    with torch.no_grad():
        for start in range(0, len(x), batch_size):
            chunk = x[start : start + batch_size]
            if hasattr(backbone, "features"):
                outputs.append(backbone.features(chunk))
            else:
                outputs.append(backbone(chunk))
    return torch.cat(outputs).cpu().numpy()
