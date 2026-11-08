"""Small PyTorch models for audio classification and character-level ASR.

Two architectures, both CPU-sized:

* ``TinyAudioCNN`` - log-Mel in, class probabilities out. The baseline classifier.
* ``TinyCRNN`` - log-Mel in, a time series of character logits out, trained with CTC.
  The convolution stack sees local spectral patterns; the bidirectional GRU sees the
  sequence. CTC removes the need for frame-level alignments, which is exactly why
  speech recognition stopped needing them.
"""

from __future__ import annotations

from pathlib import Path

import torch
import torch.nn as nn


def set_seed(seed: int) -> None:
    """Seed every RNG and pin torch to one thread.

    Pinning the thread count is unusual, and it is here for a reason: multi-threaded CPU
    convolution reduces in a different order each run, and the tiny differences compound
    during training. Two runs of the same lab then report WER 0.0 and WER 0.3, which makes
    the lessons unverifiable. One thread costs a second or two per training run and buys
    reproducible numbers; call ``torch.set_num_threads(n)`` yourself if you want speed.
    """
    import random

    import numpy as np

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(False)
    torch.set_num_threads(1)


class TinyAudioCNN(nn.Module):
    """Four conv blocks over a (1, n_mels, frames) input, then global pooling."""

    def __init__(self, num_classes: int = 4, width: int = 16, dropout: float = 0.2, n_mels: int = 40):
        super().__init__()
        self.num_classes = num_classes
        self.width = width
        self.n_mels = n_mels

        def block(cin: int, cout: int) -> nn.Sequential:
            return nn.Sequential(
                nn.Conv2d(cin, cout, 3, padding=1, bias=False),
                nn.BatchNorm2d(cout),
                nn.ReLU(inplace=True),
                nn.Conv2d(cout, cout, 3, padding=1, bias=False),
                nn.BatchNorm2d(cout),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(2),
            )

        self.block1 = block(1, width)
        self.block2 = block(width, width * 2)
        self.block3 = block(width * 2, width * 4)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(width * 4, num_classes)

    def features(self, x: torch.Tensor) -> torch.Tensor:
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        return torch.flatten(self.pool(x), 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.dropout(self.features(x)))


class TinyCRNN(nn.Module):
    """Convolutional feature extractor + BiGRU + per-frame character logits.

    Input is ``(B, 1, n_mels, T)``; output is ``(B, T', vocab_size)`` where ``T'`` is
    the pooled time axis. CTC needs ``T'`` to be at least as long as the transcript,
    so the pooling here is along frequency only - the time axis is never strided.
    """

    def __init__(
        self,
        vocab_size: int,
        n_mels: int = 40,
        width: int = 16,
        hidden: int = 64,
        dropout: float = 0.1,
        rnn_layers: int = 1,
        stride_time: int = 2,
    ):
        super().__init__()
        self.vocab_size = vocab_size
        self.n_mels = n_mels
        self.stride_time = stride_time

        self.conv1 = nn.Sequential(
            nn.Conv2d(1, width, 3, padding=1, bias=False),
            nn.BatchNorm2d(width),
            nn.ReLU(inplace=True),
            nn.Conv2d(width, width, 3, padding=1, bias=False),
            nn.BatchNorm2d(width),
            nn.ReLU(inplace=True),
            nn.MaxPool2d((2, 1)),
        )
        self.conv2 = nn.Sequential(
            nn.Conv2d(width, width * 2, 3, padding=1, bias=False),
            nn.BatchNorm2d(width * 2),
            nn.ReLU(inplace=True),
            nn.Conv2d(width * 2, width * 2, 3, padding=1, bias=False),
            nn.BatchNorm2d(width * 2),
            nn.ReLU(inplace=True),
            nn.MaxPool2d((2, 1)),
        )
        self.rnn = nn.GRU(
            input_size=width * 2 * (n_mels // 4),
            hidden_size=hidden,
            num_layers=rnn_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if rnn_layers > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout)
        self.out = nn.Linear(hidden * 2, vocab_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # (B, 1, F, T) -> (B, C, F', T)
        h = self.conv1(x)
        h = self.conv2(h)
        b, c, f, t = h.shape
        h = h.permute(0, 3, 1, 2).reshape(b, t, c * f)  # time-major
        if self.stride_time > 1:
            h = h[:, :: self.stride_time, :]
        h, _ = self.rnn(h)
        return self.out(self.dropout(h))


# ---------------------------------------------------------------------------
# Introspection and persistence
# ---------------------------------------------------------------------------


def count_parameters(model: nn.Module, trainable_only: bool = True) -> int:
    return sum(p.numel() for p in model.parameters() if (p.requires_grad or not trainable_only))


def model_disk_bytes(model: nn.Module) -> int:
    import io

    buffer = io.BytesIO()
    torch.save(model.state_dict(), buffer)
    return len(buffer.getvalue())


def model_size_mb(model: nn.Module) -> float:
    return model_disk_bytes(model) / (1024 * 1024)


def summarize_model(model: nn.Module) -> dict:
    total = count_parameters(model, trainable_only=False)
    return {
        "class": type(model).__name__,
        "parameters_total": total,
        "parameters_trainable": count_parameters(model),
        "size_mb": round(model_size_mb(model), 4),
    }


def save_checkpoint(model: nn.Module, path: str | Path, meta: dict | None = None) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "meta": meta or {}}, path)
    return path


def load_checkpoint(model: nn.Module, path: str | Path) -> dict:
    payload = torch.load(Path(path), map_location="cpu", weights_only=False)
    model.load_state_dict(payload["state_dict"])
    model.eval()
    return payload.get("meta", {})
