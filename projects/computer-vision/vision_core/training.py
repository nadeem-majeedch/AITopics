"""Training loops, learning-curve histories, and plotting without matplotlib.

matplotlib is not a dependency of this section, so curves are drawn twice: as an
ASCII sparkline for terminal output, and as a PNG via Pillow when a file is
wanted. Both are generated from the same :class:`History`, so a lab's printed
numbers and its saved figure cannot disagree.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence

import numpy as np
import torch
import torch.nn as nn

from .imaging import IMAGENET_MEAN, IMAGENET_STD, denormalize, normalize, to_tensor
from .models import set_seed


@dataclass
class History:
    """Per-epoch training record. This is the artefact, not a side effect."""

    train_loss: list[float] = field(default_factory=list)
    train_acc: list[float] = field(default_factory=list)
    val_loss: list[float] = field(default_factory=list)
    val_acc: list[float] = field(default_factory=list)
    epoch_seconds: list[float] = field(default_factory=list)
    extra: dict = field(default_factory=dict)

    def record(self, train_loss: float, train_acc: float, val_loss: float, val_acc: float, seconds: float) -> None:
        self.train_loss.append(float(train_loss))
        self.train_acc.append(float(train_acc))
        self.val_loss.append(float(val_loss))
        self.val_acc.append(float(val_acc))
        self.epoch_seconds.append(float(seconds))

    @property
    def epochs(self) -> int:
        return len(self.train_loss)

    @property
    def best_epoch(self) -> int:
        """1-based index of the epoch with the best validation accuracy."""
        if not self.val_acc:
            return 0
        return int(np.argmax(self.val_acc)) + 1

    @property
    def best_val_acc(self) -> float:
        return max(self.val_acc) if self.val_acc else 0.0

    @property
    def best_val_loss(self) -> float:
        if not self.val_loss:
            return float("nan")
        return float(self.val_loss[int(np.argmin(self.val_loss))])

    def overfitting_gap(self) -> float:
        """Final train accuracy minus final validation accuracy.

        A positive, growing gap is overfitting. A gap near zero with a high loss
        on both is underfitting, which is the opposite problem with the opposite
        fix.
        """
        if not self.train_acc or not self.val_acc:
            return 0.0
        return float(self.train_acc[-1] - self.val_acc[-1])

    def to_dict(self) -> dict:
        return {
            "epochs": self.epochs,
            "train_loss": self.train_loss,
            "train_acc": self.train_acc,
            "val_loss": self.val_loss,
            "val_acc": self.val_acc,
            "epoch_seconds": self.epoch_seconds,
            "total_seconds": float(sum(self.epoch_seconds)),
            "best_epoch": self.best_epoch,
            "best_val_acc": self.best_val_acc,
            "overfitting_gap": self.overfitting_gap(),
            **self.extra,
        }

    def ascii_plot(self, metric: str = "val_acc", width: int = 48, height: int = 9) -> str:
        """A compact ASCII chart, because a printed curve beats a described one."""
        series = getattr(self, metric)
        if not series:
            return "(no data)"
        values = np.asarray(series, dtype=np.float64)
        lo, hi = float(values.min()), float(values.max())
        if hi - lo < 1e-9:
            hi = lo + 1e-9
        rows = []
        for r in range(height):
            level = hi - (hi - lo) * r / (height - 1)
            line = "".join(
                "#" if abs(v - level) <= (hi - lo) / (2 * (height - 1)) else " "
                for v in values[:width]
            )
            rows.append(f"{level:6.3f} |{line}")
        rows.append("       +" + "-" * min(len(values), width))
        return "\n".join(rows)

    def plot_png(self, path: str | Path, title: str = "training") -> Path:
        """Draw train/val curves to a PNG with Pillow (no plotting library)."""
        from PIL import Image, ImageDraw

        width, height = 640, 360
        margin = 40
        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([margin, margin, width - margin, height - margin], outline=(80, 80, 80))
        draw.text((margin, 10), title, fill=(0, 0, 0))

        series = [("train", self.train_acc, (200, 60, 60)), ("val", self.val_acc, (40, 90, 200))]
        max_len = max(len(s[1]) for s in series) or 1
        for label, values, colour in series:
            if not values:
                continue
            points = []
            for i, v in enumerate(values):
                x = margin + (width - 2 * margin) * (i / max(1, max_len - 1))
                y = height - margin - (height - 2 * margin) * float(np.clip(v, 0, 1))
                points.append((x, y))
            if len(points) > 1:
                draw.line(points, fill=colour, width=2)
            for p in points:
                draw.ellipse([p[0] - 2, p[1] - 2, p[0] + 2, p[1] + 2], fill=colour)
            draw.text((margin + 5, margin + 5 + 14 * len(series[: series.index((label, values, colour))])), label, fill=colour)

        draw.text((margin, height - margin + 8), "epochs ->", fill=(60, 60, 60))
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(path)
        return path


# ---------------------------------------------------------------------------
# Input preparation
# ---------------------------------------------------------------------------


def dataset_stats(images: np.ndarray) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Per-channel mean and std from the *training* split only.

    Computing statistics over the whole dataset leaks information from the test
    split into preprocessing. The difference is small and the habit is not.
    """
    arr = images.astype(np.float32) / 255.0
    if arr.ndim == 3:
        arr = arr[..., None]
    mean = tuple(float(v) for v in arr.mean(axis=(0, 1, 2)))
    std = tuple(float(v) for v in arr.std(axis=(0, 1, 2)))
    return mean, std


def prepare_inputs(
    images: np.ndarray,
    mean: Sequence[float] = IMAGENET_MEAN,
    std: Sequence[float] = IMAGENET_STD,
) -> torch.Tensor:
    """NHWC uint8 -> NCHW float32 normalized tensor. The only conversion path."""
    if images.ndim == 3:
        images = images[..., None]
    normalized = np.stack([to_tensor(normalize(img, mean, std)) for img in images])
    return torch.from_numpy(normalized.astype(np.float32))


def preview_image(tensor: torch.Tensor, index: int = 0, mean: Sequence[float] = IMAGENET_MEAN, std: Sequence[float] = IMAGENET_STD) -> np.ndarray:
    """Turn a normalized sample back into a viewable uint8 image."""
    from .imaging import as_uint8, from_tensor

    array = from_tensor(tensor[index].detach().cpu().numpy())
    return as_uint8(denormalize(array, mean, std))


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------


def train_classifier(
    model: nn.Module,
    train_images: np.ndarray,
    train_labels: Sequence[int],
    val_images: np.ndarray,
    val_labels: Sequence[int],
    *,
    epochs: int = 8,
    batch_size: int = 32,
    lr: float = 1e-3,
    seed: int = 0,
    augment_fn: Callable[[np.ndarray, np.random.Generator], np.ndarray] | None = None,
    class_weights: Sequence[float] | None = None,
    patience: int = 0,
    normalize_stats: tuple[Sequence[float], Sequence[float]] | None = None,
    log: bool = True,
) -> tuple[History, nn.Module]:
    """Train a classifier and return the history plus the best-accuracy weights.

    ``patience > 0`` enables early stopping on validation accuracy. The returned
    model is restored to the best epoch, not the last one - the last epoch is
    usually the more overfitted one, and reporting it inflates nothing but the
    gap.
    """
    set_seed(seed)
    mean, std = normalize_stats if normalize_stats else dataset_stats(train_images)

    x_train = prepare_inputs(train_images, mean, std)
    y_train = torch.as_tensor(list(train_labels), dtype=torch.long)
    x_val = prepare_inputs(val_images, mean, std)
    y_val = torch.as_tensor(list(val_labels), dtype=torch.long)

    weight = torch.as_tensor(list(class_weights), dtype=torch.float32) if class_weights else None
    criterion = nn.CrossEntropyLoss(weight=weight)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    history = History(extra={"batch_size": batch_size, "lr": lr, "seed": seed, "train_size": int(len(y_train)), "val_size": int(len(y_val))})

    rng = np.random.default_rng(seed)
    best_state, best_acc, since_improved = None, -1.0, 0

    for epoch in range(1, epochs + 1):
        started = time.perf_counter()
        model.train()
        order = rng.permutation(len(y_train))
        total_loss, correct = 0.0, 0
        for start in range(0, len(order), batch_size):
            idx = order[start : start + batch_size]
            # Augmentation happens on uint8 arrays, before normalization, so the
            # same pipeline can also be used on test-time degradations.
            if augment_fn is not None:
                batch_raw = np.stack([train_images[i] for i in idx])
                batch_raw = np.stack([augment_fn(img, rng) for img in batch_raw])
                xb = prepare_inputs(batch_raw, mean, std)
            else:
                xb = x_train[idx]
            yb = y_train[idx]
            optimizer.zero_grad()
            logits = model(xb)
            loss = criterion(logits, yb)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item()) * len(yb)
            correct += int((logits.argmax(1) == yb).sum())

        train_loss = total_loss / max(1, len(y_train))
        train_acc = correct / max(1, len(y_train))

        model.eval()
        with torch.no_grad():
            val_logits = model(x_val)
            val_loss = float(criterion(val_logits, y_val).item())
            val_acc = float((val_logits.argmax(1) == y_val).float().mean())

        history.record(train_loss, train_acc, val_loss, val_acc, time.perf_counter() - started)
        if log:
            print(f"epoch {epoch:2d}  train_loss {train_loss:.4f}  train_acc {train_acc:.3f}  val_loss {val_loss:.4f}  val_acc {val_acc:.3f}")

        if val_acc > best_acc:
            best_acc = val_acc
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            since_improved = 0
        else:
            since_improved += 1
            if patience and since_improved >= patience:
                if log:
                    print(f"early stop at epoch {epoch} (no improvement for {patience})")
                break

    if best_state is not None:
        model.load_state_dict(best_state)
    model.eval()
    return history, model


def predict(model: nn.Module, images: np.ndarray, mean: Sequence[float], std: Sequence[float], batch_size: int = 64) -> tuple[np.ndarray, np.ndarray]:
    """Return predicted class indices and softmax probabilities."""
    x = prepare_inputs(images, mean, std)
    model.eval()
    probs = []
    with torch.no_grad():
        for start in range(0, len(x), batch_size):
            probs.append(torch.softmax(model(x[start : start + batch_size]), dim=1))
    prob_array = torch.cat(probs).numpy()
    return prob_array.argmax(1), prob_array
