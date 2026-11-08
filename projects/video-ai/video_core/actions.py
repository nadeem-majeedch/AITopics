"""Action recognition: a per-frame baseline against a model that sees time.

The section's central claim about video models is made checkable here: **a classifier that
sees one frame cannot tell an action from a state.** On this dataset, "moving right" and
"moving left" produce identical single frames, so the frame baseline is at chance and the
sequence model is not. That is not an artefact of synthetic data - a photo of a person
standing cannot distinguish walking from standing still, and every real action dataset has
the same structure.

Two models, one feature extractor's worth of code:

``FrameClassifier``
    2-D CNN on a single 64x64 frame. This is the "image model applied to video" baseline,
    and it is what most quick demos actually are.

``TemporalClassifier``
    The same 2-D CNN applied to every frame of a clip, then a GRU over the per-frame
    features. This is a genuine temporal model: it is trained end-to-end on clips and its
    input is a sequence, so the gradient can teach the CNN which features are worth tracking
    over time.

Neither is pretrained. A Kinetics-pretrained 3-D CNN would be the real-world choice, and
Module 11 says why it is not used here (weights size, licence, and the fact that it has no
class for "rectangle approaches the camera").
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from . import metrics
from . import synth
from .detect import set_seed


class FrameClassifier(nn.Module):
    """Single-frame CNN: the baseline that ignores time entirely."""

    def __init__(self, num_classes: int = len(synth.ACTION_CLASSES), width: int = 16) -> None:
        super().__init__()
        w = width
        self.features = nn.Sequential(
            nn.Conv2d(1, w, 3, 2, 1), nn.BatchNorm2d(w), nn.ReLU(inplace=True),
            nn.Conv2d(w, 2 * w, 3, 2, 1), nn.BatchNorm2d(2 * w), nn.ReLU(inplace=True),
            nn.Conv2d(2 * w, 4 * w, 3, 2, 1), nn.BatchNorm2d(4 * w), nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(1),
        )
        self.head = nn.Linear(4 * w, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # (B, 1, H, W)
        feat = self.features(x).flatten(1)
        return self.head(feat)


class TemporalClassifier(nn.Module):
    """Per-frame CNN followed by a GRU over the clip.

    The CNN is the same shape as :class:`FrameClassifier`'s, deliberately: the only
    difference between the two experiments is whether the model is allowed to see more than
    one frame, so a difference in accuracy is attributable to time and nothing else.
    """

    def __init__(self, num_classes: int = len(synth.ACTION_CLASSES), width: int = 16,
                 hidden: int = 64) -> None:
        super().__init__()
        w = width
        self.frame_encoder = nn.Sequential(
            nn.Conv2d(1, w, 3, 2, 1), nn.BatchNorm2d(w), nn.ReLU(inplace=True),
            nn.Conv2d(w, 2 * w, 3, 2, 1), nn.BatchNorm2d(2 * w), nn.ReLU(inplace=True),
            nn.Conv2d(2 * w, 4 * w, 3, 2, 1), nn.BatchNorm2d(4 * w), nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(1),
        )
        self.rnn = nn.GRU(4 * w, hidden, batch_first=True)
        self.head = nn.Linear(hidden, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # (B, T, 1, H, W)
        b, t, c, h, w = x.shape
        flat = x.reshape(b * t, c, h, w)
        feats = self.frame_encoder(flat).reshape(b, t, -1)
        out, _ = self.rnn(feats)
        return self.head(out[:, -1])


def _to_tensor(clips: np.ndarray) -> torch.Tensor:
    """Add the channel axis: ``(N, H, W)`` becomes ``(N, 1, H, W)``.

    Clips are already ``(N, T, H, W)`` and pass through untouched - the channel axis is the
    second, not the last, so a blanket ``unsqueeze`` would be wrong for either case.
    """
    arr = torch.from_numpy(clips.astype(np.float32))
    if arr.ndim == 3:
        arr = arr.unsqueeze(1)
    return arr


def _to_clip_tensor(clips: np.ndarray) -> torch.Tensor:
    """``(N, T, H, W)`` -> ``(N, T, 1, H, W)``, the layout the GRU model expects."""
    arr = torch.from_numpy(clips.astype(np.float32))
    if arr.ndim == 4:
        arr = arr.unsqueeze(2)
    return arr


def train_frame_model(x: np.ndarray, y: np.ndarray, *, epochs: int = 12, lr: float = 2e-3,
                      seed: int = 0, log: bool = False) -> tuple[FrameClassifier, dict]:
    """Train the single-frame baseline on individual frames (not clips)."""
    set_seed(seed)  # before construction
    model = FrameClassifier()
    optimiser = torch.optim.Adam(model.parameters(), lr=lr)
    # Frames are flattened out of clips: the baseline never sees two of them together.
    frame_list = x.reshape(-1, *x.shape[-2:])
    labels = np.repeat(y, x.shape[1])
    tensors = _to_tensor(frame_list)
    targets = torch.from_numpy(labels).long()
    history = {"loss": []}
    n = len(tensors)
    for epoch in range(1, epochs + 1):
        model.train()
        order = np.random.default_rng(seed + epoch).permutation(n)
        total, batches = 0.0, 0
        for start in range(0, n, 64):
            idx = order[start:start + 64]
            logits = model(tensors[idx])
            loss = F.cross_entropy(logits, targets[idx])
            optimiser.zero_grad()
            loss.backward()
            optimiser.step()
            total += float(loss.detach())
            batches += 1
        history["loss"].append(round(total / max(batches, 1), 4))
        if log and (epoch == 1 or epoch == epochs):
            print(f"  frame model epoch {epoch:2d} loss {history['loss'][-1]:.4f}")
    model.eval()
    return model, history


def train_temporal_model(x: np.ndarray, y: np.ndarray, *, epochs: int = 16, lr: float = 2e-3,
                         seed: int = 0, log: bool = False) -> tuple[TemporalClassifier, dict]:
    """Train the sequence model on whole clips."""
    set_seed(seed)  # before construction
    model = TemporalClassifier()
    optimiser = torch.optim.Adam(model.parameters(), lr=lr)
    tensors = _to_clip_tensor(x)
    targets = torch.from_numpy(y).long()
    history = {"loss": []}
    n = len(tensors)
    for epoch in range(1, epochs + 1):
        model.train()
        order = np.random.default_rng(seed + epoch).permutation(n)
        total, batches = 0.0, 0
        for start in range(0, n, 32):
            idx = order[start:start + 32]
            logits = model(tensors[idx])
            loss = F.cross_entropy(logits, targets[idx])
            optimiser.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimiser.step()
            total += float(loss.detach())
            batches += 1
        history["loss"].append(round(total / max(batches, 1), 4))
        if log and (epoch == 1 or epoch == epochs):
            print(f"  temporal model epoch {epoch:2d} loss {history['loss'][-1]:.4f}")
    model.eval()
    return model, history


@torch.no_grad()
def predict_temporal(model: TemporalClassifier, x: np.ndarray) -> np.ndarray:
    model.eval()
    logits = model(_to_clip_tensor(x))
    return logits.argmax(dim=1).numpy()


@torch.no_grad()
def predict_frames(model: FrameClassifier, x: np.ndarray) -> np.ndarray:
    """Per-frame predictions for every clip, shape ``(N, T)``."""
    model.eval()
    n, t = x.shape[0], x.shape[1]
    flat = x.reshape(n * t, *x.shape[-2:])
    logits = model(_to_tensor(flat))
    return logits.argmax(dim=1).numpy().reshape(n, t)


def frame_vote_predictions(model: FrameClassifier, x: np.ndarray) -> np.ndarray:
    """Majority vote over frames - the strongest thing a frame model can do on a clip."""
    per_frame = predict_frames(model, x)
    votes = []
    for row in per_frame:
        counts = np.bincount(row, minlength=len(synth.ACTION_CLASSES))
        votes.append(int(counts.argmax()))
    return np.asarray(votes)


def stability(predictions: np.ndarray) -> dict:
    """How often a clip's frames all agree, and how many distinct labels appear per clip."""
    agree = [len(set(row.tolist())) == 1 for row in predictions]
    distinct = [len(set(row.tolist())) for row in predictions]
    return {
        "clips_all_frames_agree": int(sum(agree)),
        "clips": int(len(agree)),
        "fraction_agree": round(float(np.mean(agree)), 3),
        "mean_distinct_labels_per_clip": round(float(np.mean(distinct)), 3),
    }


def split_by_seed(n_per_class: int = 40, *, train_fraction: float = 0.75,
                  seed: int = 7) -> dict[str, np.ndarray]:
    """Clips for train/test, generated from disjoint seed ranges.

    Splitting by *seed* rather than by position is the discrete equivalent of splitting by
    video: no clip in test shares its random draw with a clip in train.
    """
    x_all, y_all, names = synth.action_dataset(n_per_class=n_per_class, seed=seed)
    n = len(y_all)
    n_train = int(round(train_fraction * n))
    order = np.random.default_rng(seed).permutation(n)
    train_idx, test_idx = order[:n_train], order[n_train:]
    return {
        "x_train": x_all[train_idx], "y_train": y_all[train_idx],
        "x_test": x_all[test_idx], "y_test": y_all[test_idx],
        "classes": names,
    }


def evaluate_clip_classifier(y_true: np.ndarray, y_pred: np.ndarray,
                             class_names: list[str]) -> dict:
    return metrics.classification_report(y_true, y_pred, class_names)
