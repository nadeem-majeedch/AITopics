"""Feature batching, training loops, and the history object.

Everything is CPU-sized on purpose: the classifier trains in seconds and the CTC
recogniser in under a minute, so a student can run the experiment five times instead
of reading about it once.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Sequence

import numpy as np
import torch
import torch.nn as nn

from . import features, models, text
from .datasets import AudioRecord

DEFAULT_SR = 16_000


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


@dataclass
class History:
    """Per-epoch metrics plus the configuration that produced them."""

    train_loss: list[float] = field(default_factory=list)
    train_acc: list[float] = field(default_factory=list)
    val_loss: list[float] = field(default_factory=list)
    val_acc: list[float] = field(default_factory=list)
    seconds: list[float] = field(default_factory=list)
    config: dict = field(default_factory=dict)

    def add(self, train_loss: float, train_acc: float, val_loss: float, val_acc: float, seconds: float) -> None:
        self.train_loss.append(float(train_loss))
        self.train_acc.append(float(train_acc))
        self.val_loss.append(float(val_loss))
        self.val_acc.append(float(val_acc))
        self.seconds.append(float(seconds))

    @property
    def epochs(self) -> int:
        return len(self.val_acc)

    @property
    def best_epoch(self) -> int:
        return int(np.argmax(self.val_acc)) + 1 if self.val_acc else 0

    @property
    def best_val_acc(self) -> float:
        return float(max(self.val_acc)) if self.val_acc else 0.0

    @property
    def overfitting_gap(self) -> float:
        if not self.val_acc:
            return 0.0
        i = self.best_epoch - 1
        return float(self.train_acc[i] - self.val_acc[i])

    def to_dict(self) -> dict:
        return {
            "epochs": self.epochs,
            "train_loss": self.train_loss,
            "train_acc": self.train_acc,
            "val_loss": self.val_loss,
            "val_acc": self.val_acc,
            "seconds": self.seconds,
            "best_epoch": self.best_epoch,
            "best_val_acc": self.best_val_acc,
            "overfitting_gap": self.overfitting_gap,
            **self.config,
        }

    def ascii_plot(self, width: int = 48, height: int = 10) -> str:
        """Two curves on one character grid - train solid, validation dotted."""
        if not self.val_acc:
            return "(no history)"
        lines = []
        for row in range(height, -1, -1):
            threshold = row / height
            cells = []
            for step in range(min(width, len(self.val_acc))):
                train_v = self.train_acc[step]
                val_v = self.val_acc[step]
                train_on = abs(train_v - threshold) < 0.5 / height
                val_on = abs(val_v - threshold) < 0.5 / height
                cells.append("o" if val_on else ("*" if train_on else " "))
            lines.append(f"{threshold:4.1f} |" + "".join(cells))
        lines.append("     +" + "-" * min(width, len(self.val_acc)))
        lines.append(f"      epoch 1{' ' * max(0, min(width, len(self.val_acc)) - 12)}epoch {len(self.val_acc)}")
        lines.append("      * train accuracy    o validation accuracy")
        return "\n".join(lines)

    def plot_png(self, path: str, title: str = "training curves") -> str:
        """PNG curves without matplotlib, using Pillow."""
        from PIL import Image, ImageDraw

        width, height = 520, 260
        canvas = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        draw.text((6, 4), title, fill=(0, 0, 0))
        left, top, right, bottom = 40, 24, width - 12, height - 30
        draw.rectangle([left, top, right, bottom], outline=(200, 200, 200))
        for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
            y = bottom - frac * (bottom - top)
            draw.text((8, int(y) - 5), f"{frac:.2f}", fill=(120, 120, 120))
            draw.line([left, y, right, y], fill=(235, 235, 235))
        n = max(len(self.val_acc), 1)

        def points(values: Sequence[float]) -> list[tuple[float, float]]:
            return [
                (left + (i / max(n - 1, 1)) * (right - left), bottom - float(v) * (bottom - top))
                for i, v in enumerate(values)
            ]

        for values, colour in ((self.train_acc, (30, 90, 200)), (self.val_acc, (200, 70, 30))):
            pts = points(values)
            if len(pts) > 1:
                draw.line(pts, fill=colour, width=2)
            for x, y in pts:
                draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=colour)
        draw.text((left, bottom + 8), "epoch ->", fill=(80, 80, 80))
        draw.text((right - 150, bottom + 8), "blue train / red val", fill=(80, 80, 80))
        canvas.save(path)
        return path


# ---------------------------------------------------------------------------
# Feature batching
# ---------------------------------------------------------------------------


def mel_matrix(record: AudioRecord, n_mels: int = 40, sample_rate: int | None = None) -> np.ndarray:
    return features.mel_spectrogram(
        record.samples, sample_rate=sample_rate or record.sample_rate, n_mels=n_mels
    )


def build_inputs(
    records: Sequence[AudioRecord],
    n_mels: int = 40,
    max_frames: int | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Stack log-Mel features into ``(N, 1, n_mels, T)`` plus true frame counts.

    Clips are padded with the minimum value, not zero: after dB conversion a silent
    frame is about -80, and padding with 0 would look like a loud broadband burst.
    """
    mats = [mel_matrix(r, n_mels) for r in records]
    lengths = np.array([m.shape[0] for m in mats], dtype=np.int64)
    if max_frames is None:
        max_frames = int(lengths.max()) if len(mats) else 1
    floor = float(min(m.min() for m in mats)) if mats else -80.0
    stacked = np.full((len(mats), 1, n_mels, max_frames), floor, dtype=np.float32)
    for i, mat in enumerate(mats):
        usable = min(mat.shape[0], max_frames)
        stacked[i, 0, :, :usable] = mat[:usable].T
    return stacked, lengths, np.array([floor], dtype=np.float32)


def feature_stats(x: np.ndarray) -> tuple[float, float]:
    return float(x.mean()), float(x.std()) if x.std() > 1e-6 else 1.0


def normalize_inputs(x: np.ndarray, mean: float, std: float) -> np.ndarray:
    return ((np.asarray(x, dtype=np.float32) - mean) / max(std, 1e-6)).astype(np.float32)


def spec_augment(x: np.ndarray, rng: np.random.Generator, n_freq_masks: int = 2, n_time_masks: int = 2, freq_width: int = 6, time_width: int = 10) -> np.ndarray:
    """Mask bands of frequency and time (SpecAugment) in place on a copy.

    The augmentations the vision section applies to pixels do not exist here; masking
    spectrogram bands is the audio equivalent, and it teaches the model to stop
    depending on one frequency or one instant.
    """
    out = x.copy()
    n, _, n_mels, t = out.shape
    for i in range(n):
        for _ in range(n_freq_masks):
            width = int(rng.integers(0, freq_width + 1))
            if width and n_mels > width:
                start = int(rng.integers(0, n_mels - width))
                out[i, :, start : start + width, :] = 0.0
        for _ in range(n_time_masks):
            width = int(rng.integers(0, time_width + 1))
            if width and t > width:
                start = int(rng.integers(0, t - width))
                out[i, :, :, start : start + width] = 0.0
    return out


# ---------------------------------------------------------------------------
# Classification training
# ---------------------------------------------------------------------------


def _batch_indices(n: int, batch_size: int, rng: np.random.Generator) -> list[np.ndarray]:
    order = rng.permutation(n)
    return [order[i : i + batch_size] for i in range(0, n, batch_size)]


def accuracy(logits: torch.Tensor, targets: torch.Tensor) -> float:
    return float((logits.argmax(1) == targets).float().mean().item())


def train_classifier(
    model: nn.Module,
    train_x: np.ndarray,
    train_y: Sequence[int],
    val_x: np.ndarray,
    val_y: Sequence[int],
    *,
    epochs: int = 20,
    batch_size: int = 16,
    lr: float = 2e-3,
    seed: int = 0,
    augment: bool = True,
    class_weights: Sequence[float] | None = None,
    patience: int = 0,
    log: bool = True,
) -> tuple[History, nn.Module]:
    """Train a classifier on pre-batched features; keeps the best validation weights."""
    models.set_seed(seed)
    rng = np.random.default_rng(seed)
    x_train = torch.from_numpy(np.asarray(train_x, dtype=np.float32))
    y_train = torch.tensor(list(train_y), dtype=torch.long)
    x_val = torch.from_numpy(np.asarray(val_x, dtype=np.float32))
    y_val = torch.tensor(list(val_y), dtype=torch.long)

    weight = torch.as_tensor(list(class_weights), dtype=torch.float32) if class_weights is not None else None
    criterion = nn.CrossEntropyLoss(weight=weight)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    history = History(config={"batch_size": batch_size, "lr": lr, "seed": seed, "augment": augment})
    best_state = {k: v.clone() for k, v in model.state_dict().items()}
    best_acc = -1.0
    stale = 0

    for epoch in range(1, epochs + 1):
        started = time.perf_counter()
        model.train()
        total_loss, total_correct, total = 0.0, 0, 0
        for idx in _batch_indices(len(x_train), batch_size, rng):
            batch_x = x_train[idx].numpy()
            if augment:
                batch_x = spec_augment(batch_x, rng)
            xb = torch.from_numpy(batch_x)
            yb = y_train[idx]
            optimizer.zero_grad()
            logits = model(xb)
            loss = criterion(logits, yb)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item()) * len(idx)
            total_correct += int((logits.argmax(1) == yb).sum())
            total += len(idx)

        model.eval()
        with torch.no_grad():
            val_logits = model(x_val)
            val_loss = float(criterion(val_logits, y_val).item())
            val_acc = accuracy(val_logits, y_val)
        model.train()
        history.add(total_loss / max(total, 1), total_correct / max(total, 1), val_loss, val_acc, time.perf_counter() - started)
        if log:
            print(f"epoch {epoch:2d}  loss {history.train_loss[-1]:.4f}  train {history.train_acc[-1]:.3f}  val {val_acc:.3f}")
        if val_acc > best_acc:
            best_acc = val_acc
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            stale = 0
        else:
            stale += 1
            if patience and stale >= patience:
                if log:
                    print(f"early stop at epoch {epoch} (no improvement for {patience})")
                break

    model.load_state_dict(best_state)
    model.eval()
    return history, model


def predict(model: nn.Module, x: np.ndarray, batch_size: int = 32) -> tuple[np.ndarray, np.ndarray]:
    model.eval()
    probs = []
    with torch.no_grad():
        tensor = torch.from_numpy(np.asarray(x, dtype=np.float32))
        for start in range(0, len(tensor), batch_size):
            probs.append(torch.softmax(model(tensor[start : start + batch_size]), dim=1))
    if not probs:
        return np.zeros(0, dtype=np.int64), np.zeros((0, 1), dtype=np.float32)
    matrix = torch.cat(probs).numpy()
    return matrix.argmax(1), matrix


# ---------------------------------------------------------------------------
# CTC training
# ---------------------------------------------------------------------------


def encode_targets(records: Sequence[AudioRecord], vocab: Sequence[str]) -> tuple[list[list[int]], list[int]]:
    targets, lengths = [], []
    for record in records:
        encoded = text.encode_transcript(record.transcript, vocab)
        targets.append(encoded)
        lengths.append(len(encoded))
    return targets, lengths


def collate_ctc(targets: Sequence[Sequence[int]]) -> tuple[torch.Tensor, torch.Tensor]:
    """Flatten targets and return per-sample lengths, as CTC loss expects."""
    lengths = torch.tensor([len(t) for t in targets], dtype=torch.long)
    flat = torch.tensor([i for t in targets for i in t], dtype=torch.long)
    return flat, lengths


def output_lengths(frame_lengths: np.ndarray, stride_time: int) -> torch.Tensor:
    """Frames the model still has after temporal subsampling."""
    if stride_time <= 1:
        return torch.tensor(frame_lengths, dtype=torch.long)
    return torch.tensor(np.ceil(np.asarray(frame_lengths) / stride_time).astype(np.int64), dtype=torch.long)


def train_ctc(
    model: nn.Module,
    records: Sequence[AudioRecord],
    vocab: Sequence[str],
    val_records: Sequence[AudioRecord],
    *,
    n_mels: int = 40,
    epochs: int = 30,
    batch_size: int = 16,
    lr: float = 3e-3,
    seed: int = 0,
    augment: bool = False,
    log: bool = True,
) -> tuple[dict, nn.Module]:
    """Train a CTC recogniser. Returns ``(history_dict, model)``.

    The loss aligns transcript characters to frames automatically, which removes the
    need for frame-level labels. What it does not remove is the need for enough
    frames: a transcript longer than the model's output length is unrepresentable and
    the loss silently stays at infinity, so the frame budget is checked up front.
    """
    models.set_seed(seed)
    rng = np.random.default_rng(seed)
    stride = int(getattr(model, "stride_time", 1))
    x_all, frame_lengths, _floor = build_inputs(records, n_mels=n_mels)
    mean, std = feature_stats(x_all)
    x_all = normalize_inputs(x_all, mean, std)
    x_val, val_frames, _ = build_inputs(val_records, n_mels=n_mels, max_frames=x_all.shape[-1])
    # A validation clip can be longer than the widest training clip; it is truncated by
    # build_inputs, so its frame count has to be truncated too or CTC rejects the call.
    val_frames = np.minimum(val_frames, x_all.shape[-1])
    x_val = normalize_inputs(x_val, mean, std)

    targets, _ = encode_targets(records, vocab)
    in_lengths = output_lengths(frame_lengths, stride)
    for i, (length, target) in enumerate(zip(in_lengths.tolist(), targets)):
        if len(target) + 1 > length:
            raise ValueError(
                f"clip {i}: {len(target)} characters need at least {len(target) + 1} frames, model gives {length}. "
                "Lower stride_time or raise max_frames."
            )

    x_train_t = torch.from_numpy(x_all)
    val_targets, _ = encode_targets(val_records, vocab)
    x_val_t = torch.from_numpy(x_val)
    val_in_lengths = output_lengths(val_frames, stride)

    ctc = nn.CTCLoss(blank=0, zero_infinity=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    history: dict = {"loss": [], "val_loss": [], "seconds": [], "epochs": [], "frames": int(x_all.shape[-1]), "stride_time": stride}

    for epoch in range(1, epochs + 1):
        started = time.perf_counter()
        model.train()
        total, batches = 0.0, 0
        for idx in _batch_indices(len(x_train_t), batch_size, rng):
            batch_x = x_train_t[idx].numpy()
            if augment:
                batch_x = spec_augment(batch_x, rng)
            xb = torch.from_numpy(batch_x)
            log_probs = model(xb).log_softmax(2).transpose(0, 1)  # (T, B, V)
            batch_targets = [targets[i] for i in idx.tolist()]
            flat, target_lengths = collate_ctc(batch_targets)
            input_lengths = output_lengths(frame_lengths[idx], stride)
            loss = ctc(log_probs, flat, input_lengths, target_lengths)
            if not torch.isfinite(loss):
                raise RuntimeError("CTC loss is not finite; check frame budget and blank index")
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
            total += float(loss.item())
            batches += 1
        model.eval()
        with torch.no_grad():
            val_log_probs = model(x_val_t).log_softmax(2).transpose(0, 1)
            flat_val, val_target_lengths = collate_ctc(val_targets)
            val_loss = float(ctc(val_log_probs, flat_val, val_in_lengths, val_target_lengths).item())
        history["loss"].append(total / max(batches, 1))
        history["val_loss"].append(val_loss)
        history["seconds"].append(time.perf_counter() - started)
        history["epochs"].append(epoch)
        if log:
            print(f"epoch {epoch:2d}  ctc loss {history['loss'][-1]:.4f}  val {val_loss:.4f}")

    model.eval()
    history.update({"mean": mean, "std": std, "n_mels": n_mels, "total_seconds": float(sum(history["seconds"]))})
    return history, model
