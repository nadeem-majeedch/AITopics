"""Small PyTorch models sized for laptop CPUs.

Every model here trains in seconds to a couple of minutes on 8 CPU threads, which
is what makes the labs repeatable in a classroom. They are deliberately tiny: the
goal is to see *mechanisms* (what a convolution does, why a heatmap needs NMS),
not to reach state-of-the-art accuracy.

The same models are used for the from-scratch and fine-tuning labs, so students
can compare like with like instead of comparing a toy against ResNet-50.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
import torch.nn as nn


def set_seed(seed: int) -> None:
    """Seed Python, NumPy, and torch so runs are reproducible."""
    import random

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(False)


class TinyCNN(nn.Module):
    """A three-block convolutional classifier.

    Structure: ``conv-bn-relu`` twice, then max-pool, three times, then global
    average pooling and a linear layer. Global pooling (rather than a flatten)
    keeps the parameter count independent of input size, which is why the same
    model works at 32x32 for classification and 64x64 for features.

    ``features(x)`` returns the pooled embedding, used by the transfer and
    similarity labs; ``forward`` adds the classifier.
    """

    def __init__(self, num_classes: int = 3, in_channels: int = 3, width: int = 16, dropout: float = 0.1):
        super().__init__()
        self.num_classes = num_classes
        self.width = width

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

        self.block1 = block(in_channels, width)
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

    @property
    def feature_dim(self) -> int:
        return self.width * 4


class TinyHeatmapDetector(nn.Module):
    """A fully convolutional detector that predicts a centre heatmap and box size.

    Output stride is 4, so a 64x64 input gives a 16x16 heatmap. Two heads:

    * ``heat`` - one channel per class, logits; a peak means "an object centre".
    * ``size`` - two channels, box width and height as a fraction of the image,
      read only at the peak location.

    This is a deliberately simplified CenterNet. The teaching point is the
    decode step: a network that outputs a grid of scores is not a detector until
    peaks become boxes and overlapping boxes become one through NMS.
    """

    def __init__(self, num_classes: int = 3, width: int = 16, stride: int = 4):
        super().__init__()
        self.num_classes = num_classes
        self.stride = stride
        self.trunk = nn.Sequential(
            nn.Conv2d(3, width, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(width),
            nn.ReLU(inplace=True),
            nn.Conv2d(width, width * 2, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(width * 2),
            nn.ReLU(inplace=True),
            nn.Conv2d(width * 2, width * 2, 3, padding=1, bias=False),
            nn.BatchNorm2d(width * 2),
            nn.ReLU(inplace=True),
        )
        self.heat = nn.Conv2d(width * 2, num_classes, 1)
        self.size = nn.Conv2d(width * 2, 2, 1)
        nn.init.constant_(self.heat.bias, -4.0)  # start pessimistic: mostly background

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        feat = self.trunk(x)
        return self.heat(feat), self.size(feat)


class TinyUNet(nn.Module):
    """A two-level U-Net for semantic segmentation.

    The skip connection is the whole point: the encoder knows *what* is in the
    image, the decoder needs to know *where*, and pooling destroyed that. Whether removing it
    costs IoU on this data is measurable, not guaranteed; ``segmentation_demo.py``
    runs the ablation at the same budget and prints both numbers.
    """

    def __init__(self, num_classes: int = 3, in_channels: int = 3, width: int = 8, use_skip: bool = True):
        super().__init__()
        self.use_skip = use_skip
        self.enc1 = nn.Sequential(nn.Conv2d(in_channels, width, 3, padding=1), nn.ReLU(inplace=True))
        self.enc2 = nn.Sequential(nn.Conv2d(width, width * 2, 3, stride=2, padding=1), nn.ReLU(inplace=True))
        self.enc3 = nn.Sequential(nn.Conv2d(width * 2, width * 4, 3, stride=2, padding=1), nn.ReLU(inplace=True))
        self.up2 = nn.ConvTranspose2d(width * 4, width * 2, 2, stride=2)
        self.dec2 = nn.Sequential(nn.Conv2d(width * 4 if use_skip else width * 2, width * 2, 3, padding=1), nn.ReLU(inplace=True))
        self.up1 = nn.ConvTranspose2d(width * 2, width, 2, stride=2)
        self.dec1 = nn.Sequential(nn.Conv2d(width * 2 if use_skip else width, width, 3, padding=1), nn.ReLU(inplace=True))
        self.head = nn.Conv2d(width, num_classes, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        e1 = self.enc1(x)
        e2 = self.enc2(e1)
        e3 = self.enc3(e2)
        d2 = self.up2(e3)
        d2 = self.dec2(torch.cat([d2, e2], 1) if self.use_skip else d2)
        d1 = self.up1(d2)
        d1 = self.dec1(torch.cat([d1, e1], 1) if self.use_skip else d1)
        return self.head(d1)


# ---------------------------------------------------------------------------
# Introspection helpers - used by the deployment lab
# ---------------------------------------------------------------------------


def count_parameters(model: nn.Module, trainable_only: bool = True) -> int:
    return sum(p.numel() for p in model.parameters() if (p.requires_grad or not trainable_only))


def model_disk_bytes(model: nn.Module) -> int:
    """Exact serialized size of the state dict, in bytes.

    Reported instead of ``params * 4`` because the two differ once you include
    buffers and the pickle overhead, and because the deployment question is about
    bytes on disk and in memory, not about a formula.
    """
    import io

    buffer = io.BytesIO()
    torch.save(model.state_dict(), buffer)
    return len(buffer.getvalue())


def model_size_mb(model: nn.Module) -> float:
    return model_disk_bytes(model) / (1024 * 1024)


def summarize_model(model: nn.Module) -> dict:
    total = count_parameters(model, trainable_only=False)
    trainable = count_parameters(model)
    return {
        "class": type(model).__name__,
        "parameters_total": total,
        "parameters_trainable": trainable,
        "size_mb": round(model_size_mb(model), 4),
        "estimated_int8_mb": round(total / (1024 * 1024), 4),
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
