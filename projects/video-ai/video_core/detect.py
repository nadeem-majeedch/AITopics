"""Detectors: one trained in this section, one pretrained on COCO.

Two detectors, because the section needs both and they answer different questions.

``TinyDetector``
    An anchor-based single-shot detector written here and trained here on the synthetic
    traffic frames. It is small enough to train on a laptop CPU in under a minute and it
    reaches a useful mAP on this domain. It is **not** pretrained and must not be described
    as such: every weight in it was learned from the frames in ``data/video``.

``SSDLiteDetector``
    ``torchvision``'s SSDLite320-MobileNetV3, pretrained on COCO (80 classes). The
    torchvision code is BSD-3-Clause. The pretrained weights have no separately stated
    licence in torchvision's documentation, which warns that weights can inherit terms
    from their training dataset; no weights are redistributed with this course. It is a
    genuine pretrained detector and it is genuinely bad on this section's synthetic
    frames: COCO has no "flat vector art" class. Modules 6, 7 and 14 use that failure
    rather than hiding it, and Lab 4 fine-tunes this model on 40 synthetic frames to
    measure how much of the gap adaptation closes.

The distinction the section keeps insisting on: running inference with a pretrained model
is not fine-tuning, and fine-tuning an *image* detector on extracted frames is not training
a *video* model. Both statements live here as docstrings so they can be cited.

Weight downloads are redirected to ``<project>/.cache/torch`` so a lab does not scatter
files through the user's home directory, and failure to download is reported as a reason
string rather than an exception traceback.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from . import labels as labels_mod
from . import metrics
from . import video as video_mod

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = PROJECT_ROOT / ".cache"
# Must be set before torchvision touches the hub; setdefault so a user override wins.
os.environ.setdefault("TORCH_HOME", str(CACHE_ROOT / "torch"))

# Detection input is small on purpose: 256x144 keeps a CPU training epoch near a few
# seconds and is still four times the size of the smallest vehicle in the scene.
INPUT_W, INPUT_H = 256, 144
STRIDE = 8
GRID_W, GRID_H = INPUT_W // STRIDE, INPUT_H // STRIDE
# Three anchor shapes per cell, covering a motorcycle through a bus. Widths/heights are in
# input pixels, so they stay meaningful when the source video is resized.
ANCHORS = ((36, 26), (76, 40), (150, 66))


def set_seed(seed: int = 0) -> None:
    """Seed every RNG this section uses, and pin torch to one thread.

    Call this **before** constructing a model. Weights are drawn from the global torch RNG,
    so seeding after construction leaves the initial point up to the process and every
    reported number drifts between runs - a bug that cost this course a day to find in the
    speech section, and is repeated here in the docs so it is not repeated in a project.
    """
    import random

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)


# ---------------------------------------------------------------------------
# Anchors
# ---------------------------------------------------------------------------


def build_anchors(width: int = INPUT_W, height: int = INPUT_H) -> torch.Tensor:
    """Corner-format anchors for every cell and shape, ordered ``(cy, cx, shape)``."""
    stride = width / GRID_W
    boxes = []
    for gy in range(GRID_H):
        for gx in range(GRID_W):
            cx = (gx + 0.5) * stride
            cy = (gy + 0.5) * (height / GRID_H)
            for aw, ah in ANCHORS:
                boxes.append([cx - aw / 2, cy - ah / 2, cx + aw / 2, cy + ah / 2])
    return torch.tensor(boxes, dtype=torch.float32)


def encode_targets(anchors: torch.Tensor, boxes: torch.Tensor, labels_t: torch.Tensor,
                   iou_pos: float = 0.5, iou_neg: float = 0.3) -> tuple[torch.Tensor, ...]:
    """Assign ground truth to anchors.

    An anchor is positive when it overlaps a ground-truth box at IoU >= ``iou_pos``; the
    best-overlapping anchor for each box is positive even if it falls short, so small
    objects are never dropped for lack of a well-shaped anchor. Anchors with IoU below
    ``iou_neg`` are negatives; the band in between is ignored by the objectness loss, which
    stops half-fitting anchors from fighting the positives.
    """
    n_anchors = anchors.shape[0]
    obj = torch.zeros(n_anchors, dtype=torch.float32)
    cls = torch.zeros(n_anchors, dtype=torch.long)
    reg = torch.zeros((n_anchors, 4), dtype=torch.float32)
    ignore = torch.zeros(n_anchors, dtype=torch.bool)
    if boxes.numel() == 0:
        return obj, cls, reg, ignore

    ious = _iou_torch(anchors, boxes)               # (A, G)
    best_gt_iou, best_gt = ious.max(dim=1)          # per anchor
    obj[best_gt_iou >= iou_pos] = 1.0
    ignore[(best_gt_iou >= iou_neg) & (best_gt_iou < iou_pos)] = True

    # Force one anchor per ground-truth box.
    best_anchor_per_gt = ious.argmax(dim=0)         # (G,)
    for gt_idx in range(boxes.shape[0]):
        anchor_idx = int(best_anchor_per_gt[gt_idx])
        obj[anchor_idx] = 1.0
        ignore[anchor_idx] = False
        cls[anchor_idx] = int(labels_t[gt_idx])

    positive = obj > 0.5
    if positive.any():
        pos_anchors = anchors[positive]
        # Recover which box each positive anchor was assigned to.
        assigned = ious[positive].argmax(dim=1)
        target_boxes = boxes[assigned]
        reg[positive] = _encode_boxes(pos_anchors, target_boxes)
        cls[positive] = labels_t[assigned]
    return obj, cls, reg, ignore


def _encode_boxes(anchors: torch.Tensor, boxes: torch.Tensor) -> torch.Tensor:
    aw = (anchors[:, 2] - anchors[:, 0]).clamp(min=1e-3)
    ah = (anchors[:, 3] - anchors[:, 1]).clamp(min=1e-3)
    acx = anchors[:, 0] + aw / 2
    acy = anchors[:, 1] + ah / 2
    bw = (boxes[:, 2] - boxes[:, 0]).clamp(min=1e-3)
    bh = (boxes[:, 3] - boxes[:, 1]).clamp(min=1e-3)
    bcx = boxes[:, 0] + bw / 2
    bcy = boxes[:, 1] + bh / 2
    return torch.stack([(bcx - acx) / aw, (bcy - acy) / ah,
                        torch.log(bw / aw), torch.log(bh / ah)], dim=1)


def decode_boxes(anchors: torch.Tensor, deltas: torch.Tensor) -> torch.Tensor:
    aw = (anchors[:, 2] - anchors[:, 0]).clamp(min=1e-3)
    ah = (anchors[:, 3] - anchors[:, 1]).clamp(min=1e-3)
    acx = anchors[:, 0] + aw / 2
    acy = anchors[:, 1] + ah / 2
    cx = deltas[:, 0] * aw + acx
    cy = deltas[:, 1] * ah + acy
    w = torch.exp(deltas[:, 2].clamp(-4, 4)) * aw
    h = torch.exp(deltas[:, 3].clamp(-4, 4)) * ah
    return torch.stack([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], dim=1)


def _iou_torch(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    ix1 = torch.max(a[:, None, 0], b[None, :, 0])
    iy1 = torch.max(a[:, None, 1], b[None, :, 1])
    ix2 = torch.min(a[:, None, 2], b[None, :, 2])
    iy2 = torch.min(a[:, None, 3], b[None, :, 3])
    inter = (ix2 - ix1).clamp(min=0) * (iy2 - iy1).clamp(min=0)
    area_a = (a[:, 2] - a[:, 0]).clamp(min=0) * (a[:, 3] - a[:, 1]).clamp(min=0)
    area_b = (b[:, 2] - b[:, 0]).clamp(min=0) * (b[:, 3] - b[:, 1]).clamp(min=0)
    return inter / (area_a[:, None] + area_b[None, :] - inter).clamp(min=1e-6)


# ---------------------------------------------------------------------------
# The section's detector
# ---------------------------------------------------------------------------


class TinyDetector(nn.Module):
    """Single-scale anchor detector: a small CNN trunk and three prediction heads.

    Deliberately close to the detectors in the computer vision section, and deliberately
    not a black box: ``forward`` returns raw per-anchor predictions, and every step from
    those tensors to a box on screen happens in this file.

    Input is ``(B, 3, 144, 256)`` RGB in ``[0, 1]``; output is ``(obj, cls, reg)`` with
    shapes ``(B, A)``, ``(B, A, 4)``, ``(B, A, 4)`` where ``A = 32*18*3``.
    """

    def __init__(self, num_classes: int = 4, width: int = 24, anchors: Sequence[tuple[int, int]] = ANCHORS):
        super().__init__()
        self.num_classes = num_classes
        self.width = width
        self.anchor_shapes = tuple(anchors)
        w = width

        def block(cin: int, cout: int, stride: int) -> nn.Sequential:
            return nn.Sequential(
                nn.Conv2d(cin, cout, 3, stride, 1, bias=False),
                nn.BatchNorm2d(cout),
                nn.ReLU(inplace=True),
            )

        # 144x256 -> 72x128 -> 36x64 -> 18x32 (stride 8 overall)
        self.trunk = nn.Sequential(
            block(3, w, 2),
            block(w, 2 * w, 2),
            block(2 * w, 4 * w, 2),
            block(4 * w, 4 * w, 1),
        )
        n_anchors = len(self.anchor_shapes)
        self.obj_head = nn.Conv2d(4 * w, n_anchors, 1)
        self.cls_head = nn.Conv2d(4 * w, n_anchors * num_classes, 1)
        self.reg_head = nn.Conv2d(4 * w, n_anchors * 4, 1)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        feat = self.trunk(x)
        b, _, h, w = feat.shape
        obj = self.obj_head(feat).permute(0, 2, 3, 1).reshape(b, -1)
        cls = self.cls_head(feat).permute(0, 2, 3, 1).reshape(b, -1, self.num_classes)
        reg = self.reg_head(feat).permute(0, 2, 3, 1).reshape(b, -1, 4) * 0.5
        return obj, cls, reg

    # -- inference ---------------------------------------------------------
    @torch.no_grad()
    def predict(self, frame_bgr: np.ndarray, *, score_threshold: float = 0.30,
                nms_iou: float = 0.45, max_detections: int = 30) -> list[metrics.Detection]:
        """Detect vehicles in one BGR frame of any size.

        The frame is resized to the training resolution and the boxes are scaled back, so
        the rest of the pipeline never has to know the model's input size.
        """
        self.eval()
        h0, w0 = frame_bgr.shape[:2]
        tensor = frame_to_tensor(frame_bgr)
        obj, cls, reg = self(tensor)
        return _decode_predictions(obj[0], cls[0], reg[0], (w0, h0),
                                   score_threshold=score_threshold, nms_iou=nms_iou,
                                   max_detections=max_detections)

    # -- persistence -------------------------------------------------------
    def save(self, path: str | Path, extra: dict | None = None) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "state_dict": self.state_dict(),
            "config": {"num_classes": self.num_classes, "width": self.width,
                       "anchors": list(self.anchor_shapes), "input": [INPUT_W, INPUT_H]},
            "extra": dict(extra or {}),
        }
        torch.save(payload, path)
        return path

    @classmethod
    def load(cls, path: str | Path) -> "TinyDetector":
        payload = torch.load(Path(path), map_location="cpu", weights_only=False)
        cfg = payload.get("config", {})
        model = cls(num_classes=int(cfg.get("num_classes", 4)),
                    width=int(cfg.get("width", 24)),
                    anchors=[tuple(a) for a in cfg.get("anchors", ANCHORS)])
        model.load_state_dict(payload["state_dict"])
        model.eval()
        model.extra = payload.get("extra", {})  # type: ignore[attr-defined]
        return model


_ANCHOR_CACHE: dict[tuple[int, int], torch.Tensor] = {}


def anchors_for(width: int = INPUT_W, height: int = INPUT_H) -> torch.Tensor:
    key = (width, height)
    if key not in _ANCHOR_CACHE:
        _ANCHOR_CACHE[key] = build_anchors(width, height)
    return _ANCHOR_CACHE[key]


def frame_to_tensor(frame_bgr: np.ndarray) -> torch.Tensor:
    """BGR uint8 frame -> ``(1, 3, 144, 256)`` float tensor in ``[0, 1]`` RGB."""
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, (INPUT_W, INPUT_H), interpolation=cv2.INTER_AREA)
    arr = resized.astype(np.float32) / 255.0
    return torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)


def _decode_predictions(obj: torch.Tensor, cls: torch.Tensor, reg: torch.Tensor,
                        size: tuple[int, int], *, score_threshold: float,
                        nms_iou: float, max_detections: int) -> list[metrics.Detection]:
    anchors = anchors_for()
    prob = torch.sigmoid(obj)
    keep = prob > 0.05
    if not bool(keep.any()):
        return []
    idx = keep.nonzero(as_tuple=True)[0]
    boxes = decode_boxes(anchors[idx], reg[idx])
    scores_all = F.softmax(cls[idx], dim=1)
    class_scores, class_ids = scores_all.max(dim=1)
    scores = prob[idx] * class_scores

    # Scale from model input pixels back to the source frame.
    sx = size[0] / INPUT_W
    sy = size[1] / INPUT_H
    boxes[:, [0, 2]] *= sx
    boxes[:, [1, 3]] *= sy

    results: list[metrics.Detection] = []
    from torchvision.ops import nms

    # Per-class NMS first, which is the convention every detector uses. Then a second,
    # class-agnostic pass: a model that is 70% sure a box is a car and 65% sure it is a
    # truck will survive per-class NMS twice and hand the tracker two boxes for one vehicle.
    # That duplicate is what fragments tracks and inflates a vehicle count, so it is
    # cheaper to remove here than to explain later.
    for class_id in class_ids.unique().tolist():
        mask = (class_ids == class_id) & (scores >= score_threshold)
        if not bool(mask.any()):
            continue
        sel = mask.nonzero(as_tuple=True)[0]
        keep_idx = nms(boxes[sel], scores[sel], nms_iou)
        for j in keep_idx.tolist():
            row = sel[j]
            box = boxes[row].tolist()
            results.append(metrics.Detection(
                box=metrics.clip_box(box, size[0], size[1]),
                label=int(class_id),
                score=float(scores[row]),
            ))
    results.sort(key=lambda d: -d.score)
    if len(results) > 1:
        boxes_all = torch.tensor([d.box for d in results], dtype=torch.float32)
        scores_all2 = torch.tensor([d.score for d in results], dtype=torch.float32)
        keep_all = nms(boxes_all, scores_all2, min(0.9, nms_iou + 0.10))
        results = [results[i] for i in keep_all.tolist()]
    return results[:max_detections]


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------


@dataclass
class DetectionSample:
    frame: np.ndarray                     # BGR, any size
    boxes: list[list[float]]
    labels: list[int]


def _prepare_training_frame(frame: np.ndarray, boxes: Sequence[Sequence[float]],
                            rng: np.random.Generator) -> tuple[torch.Tensor, torch.Tensor]:
    """Resize a frame to the model input, apply photometric augmentation, scale boxes."""
    h0, w0 = frame.shape[:2]
    sx, sy = INPUT_W / w0, INPUT_H / h0
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, (INPUT_W, INPUT_H), interpolation=cv2.INTER_AREA).astype(np.float32)

    # Brightness and contrast only: geometric augmentation would need box transforms, and
    # the vehicle shapes are already varied by the generator.
    gain = float(rng.uniform(0.75, 1.25))
    bias = float(rng.uniform(-18, 18))
    resized = np.clip(resized * gain + bias, 0, 255) / 255.0
    tensor = torch.from_numpy(resized).permute(2, 0, 1)

    scaled = torch.tensor([[b[0] * sx, b[1] * sy, b[2] * sx, b[3] * sy] for b in boxes],
                          dtype=torch.float32).reshape(-1, 4)
    return tensor, scaled


def train_detector(
    samples: Sequence[DetectionSample],
    *,
    epochs: int = 12,
    batch_size: int = 8,
    lr: float = 1.5e-3,
    width: int = 24,
    seed: int = 0,
    log: bool = True,
) -> tuple[TinyDetector, dict]:
    """Train ``TinyDetector`` from scratch on labelled frames.

    Loss is the same three-part objective every single-shot detector uses: focal loss on
    objectness, cross-entropy on the class of positive anchors only, and smooth-L1 on the
    box offsets of positive anchors only. Focal loss matters here - with 1,728 anchors and
    roughly six vehicles per frame, a plain BCE would be dominated by background and the
    model would learn to predict "nothing" extremely confidently.
    """
    set_seed(seed)  # before construction, see the docstring
    model = TinyDetector(width=width)
    rng = np.random.default_rng(seed)
    optimiser = torch.optim.Adam(model.parameters(), lr=lr)
    anchors = anchors_for()
    history = {"loss": [], "obj_loss": [], "cls_loss": [], "reg_loss": [], "epochs": []}

    prepared = []
    for sample in samples:
        tensor, boxes = _prepare_training_frame(sample.frame, sample.boxes, rng)
        prepared.append((tensor, boxes, torch.tensor(sample.labels, dtype=torch.long)))

    n = len(prepared)
    for epoch in range(1, epochs + 1):
        model.train()
        order = np.random.default_rng(seed + epoch).permutation(n)
        totals = np.zeros(3)
        batches = 0
        for start in range(0, n, batch_size):
            batch_ids = order[start:start + batch_size]
            images = torch.stack([prepared[i][0] for i in batch_ids])
            obj_t, cls_t, reg_t, ignore = [], [], [], []
            for i in batch_ids:
                _, boxes, labels_t = prepared[i]
                o, c, r, ig = encode_targets(anchors, boxes, labels_t)
                obj_t.append(o)
                cls_t.append(c)
                reg_t.append(r)
                ignore.append(ig)
            obj_t = torch.stack(obj_t)
            cls_t = torch.stack(cls_t)
            reg_t = torch.stack(reg_t)
            ignore_t = torch.stack(ignore)

            obj_logits, cls_logits, reg_pred = model(images)
            obj_loss = _focal_loss(obj_logits, obj_t, ignore_t)
            positive = obj_t > 0.5
            if bool(positive.any()):
                cls_loss = F.cross_entropy(cls_logits[positive], cls_t[positive])
                reg_loss = F.smooth_l1_loss(reg_pred[positive], reg_t[positive], beta=0.2)
            else:
                cls_loss = torch.zeros(())
                reg_loss = torch.zeros(())
            loss = obj_loss + cls_loss + 2.0 * reg_loss
            optimiser.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimiser.step()
            totals += np.array([float(obj_loss.detach()), float(cls_loss.detach()),
                                float(reg_loss.detach())])
            batches += 1
        means = totals / max(batches, 1)
        history["obj_loss"].append(round(means[0], 4))
        history["cls_loss"].append(round(means[1], 4))
        history["reg_loss"].append(round(means[2], 4))
        history["loss"].append(round(float(means.sum()), 4))
        history["epochs"].append(epoch)
        if log:
            print(f"epoch {epoch:2d}  loss {history['loss'][-1]:.4f}  "
                  f"(obj {means[0]:.4f}  cls {means[1]:.4f}  reg {means[2]:.4f})")
    model.eval()
    return model, history


def _focal_loss(logits: torch.Tensor, targets: torch.Tensor,
                ignore: torch.Tensor, alpha: float = 0.25, gamma: float = 2.0) -> torch.Tensor:
    ce = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")
    prob = torch.sigmoid(logits)
    p_t = prob * targets + (1 - prob) * (1 - targets)
    alpha_t = alpha * targets + (1 - alpha) * (1 - targets)
    loss = alpha_t * (1 - p_t).pow(gamma) * ce
    loss = loss.masked_fill(ignore, 0.0)
    n_pos = (targets > 0.5).sum().clamp(min=1.0)
    return loss.sum() / n_pos


# ---------------------------------------------------------------------------
# The pretrained detector
# ---------------------------------------------------------------------------


# COCO category ids (torchvision order) for the four classes this section cares about.
COCO_TRAFFIC_IDS = {"car": 3, "motorcycle": 4, "bus": 6, "truck": 8}


class SSDLiteDetector:
    """COCO-pretrained SSDLite320-MobileNetV3, used here as an honest baseline.

    It is a real pretrained detector: 3.44 M parameters, trained on COCO 2017 by the
    torchvision authors. The torchvision code is BSD-3-Clause. The COCO weights have no
    separately stated licence, are downloaded at runtime rather than redistributed with
    this repository, and must be treated as unresolved until the exact upstream terms are
    checked. It is fast enough on CPU (roughly 40-90 ms per 320x320 frame on a laptop) to
    run in a lab.

    What it is not: a traffic detector, or a video model. On this section's synthetic
    frames it detects almost nothing, which is the point of the comparison in Module 6.
    """

    def __init__(self, *, score_threshold: float = 0.30, device: str = "cpu") -> None:
        self.score_threshold = score_threshold
        self.device = device
        self._model = None
        self._categories = None
        self.load_error: str | None = None

    # -- lifecycle ---------------------------------------------------------
    @property
    def available(self) -> bool:
        return self._model is not None

    def load(self) -> bool:
        """Download (first time) and load the weights. Returns ``True`` on success.

        On failure ``load_error`` carries a one-line reason and every later call returns an
        empty list, so a lab can print "pretrained detector unavailable: <reason>" and keep
        running instead of crashing for a student without network access.
        """
        if self._model is not None:
            return True
        try:
            from torchvision.models.detection import (
                SSDLite320_MobileNet_V3_Large_Weights,
                ssdlite320_mobilenet_v3_large,
            )

            weights = SSDLite320_MobileNet_V3_Large_Weights.DEFAULT
            model = ssdlite320_mobilenet_v3_large(weights=weights).to(self.device).eval()
            self._model = model
            self._categories = list(weights.meta["categories"])
            return True
        except Exception as exc:  # noqa: BLE001 - report, do not crash the lab
            self.load_error = f"{type(exc).__name__}: {exc}"
            return False

    @property
    def categories(self) -> list[str]:
        return list(self._categories or [])

    def info(self) -> dict:
        n_params = sum(p.numel() for p in self._model.parameters()) if self._model else 0
        return {
            "name": "ssdlite320_mobilenet_v3_large",
            "pretrained_on": "COCO 2017 (80 classes)",
            "parameters": int(n_params),
            "available": self.available,
            "load_error": self.load_error,
            "torch_home": os.environ.get("TORCH_HOME"),
        }

    # -- inference ---------------------------------------------------------
    @torch.no_grad()
    def predict(self, frame_bgr: np.ndarray,
                *, traffic_only: bool = False) -> list[metrics.Detection]:
        """Detect objects in one BGR frame.

        ``traffic_only`` keeps the four vehicle classes and remaps their labels into this
        section's ``LABELS`` order; otherwise every COCO class above the score threshold is
        returned with its COCO index, which is what you want when inspecting what the model
        thinks it sees.
        """
        if self._model is None and not self.load():
            return []
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        tensor = torch.from_numpy(rgb.astype(np.float32) / 255.0).permute(2, 0, 1)
        out = self._model([tensor.to(self.device)])[0]
        results: list[metrics.Detection] = []
        for box, score, label in zip(out["boxes"], out["scores"], out["labels"]):
            value = float(score)
            if value < self.score_threshold:
                continue
            coco_label = int(label)
            if traffic_only:
                name = next((n for n, i in COCO_TRAFFIC_IDS.items() if i == coco_label), None)
                if name is None:
                    continue
                results.append(metrics.Detection(box.tolist(),
                                                 labels_mod.LABEL_TO_INDEX[name], value))
            else:
                results.append(metrics.Detection(box.tolist(), coco_label - 1, value,
                                                 extra={"coco_name": self._categories[coco_label]}))
        return results


# ---------------------------------------------------------------------------
# Fine-tuning the pretrained detector (Lab 4)
# ---------------------------------------------------------------------------


# torchvision reserves label 0 for background; our four classes move up by one.
TORCHVISION_LABELS = {name: i + 1 for i, name in enumerate(labels_mod.LABELS)}


def _pretrained_ssdlite(num_classes: int):
    """A torchvision SSDLite with a fresh head, plus whatever COCO weights still fit.

    Changing the number of classes changes the shape of the classification head, so the
    head cannot be copied; the backbone and the box regression layers can, and copying them
    is the entire difference between "train a detector from nothing" and "fine-tune a
    detector". This function is where that difference actually happens, which is why it is
    forty lines of explicit copying instead of one call to a helper.
    """
    from torchvision.models.detection import (
        SSDLite320_MobileNet_V3_Large_Weights,
        ssdlite320_mobilenet_v3_large,
    )

    weights = SSDLite320_MobileNet_V3_Large_Weights.DEFAULT
    model = ssdlite320_mobilenet_v3_large(weights=None, num_classes=num_classes)
    source = ssdlite320_mobilenet_v3_large(weights=weights)
    target_state = model.state_dict()
    copied, skipped = 0, 0
    for key, value in source.state_dict().items():
        if key in target_state and target_state[key].shape == value.shape:
            target_state[key] = value
            copied += 1
        else:
            skipped += 1
    model.load_state_dict(target_state)
    model.eval()
    return model, {"copied_tensors": copied, "fresh_tensors": skipped}


def _ssd_targets(frame: np.ndarray, boxes: Sequence[Sequence[float]],
                 labels: Sequence[int]) -> tuple[torch.Tensor, dict]:
    """Frame and boxes in the 320x320 space SSDLite expects at training time."""
    h0, w0 = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, (320, 320), interpolation=cv2.INTER_AREA)
    tensor = torch.from_numpy(resized.astype(np.float32) / 255.0).permute(2, 0, 1)
    sx, sy = 320.0 / w0, 320.0 / h0
    scaled = torch.tensor([[b[0] * sx, b[1] * sy, b[2] * sx, b[3] * sy] for b in boxes],
                          dtype=torch.float32).reshape(-1, 4)
    target = {
        "boxes": scaled,
        "labels": torch.tensor([TORCHVISION_LABELS[labels_mod.LABELS[int(l)]] for l in labels],
                               dtype=torch.int64),
    }
    return tensor, target


class TrafficSSDLite(SSDLiteDetector):
    """SSDLite320-MobileNetV3 fine-tuned on four vehicle classes.

    What "fine-tuned" means here, precisely: the COCO backbone and regression layers keep
    their pretrained weights, a new 5-way classification head (four classes plus background)
    is added, and the whole network is trained on labelled frames from this section's
    training videos. It is *not* trained on video clips and it has no temporal component:
    this is image-model fine-tuning applied to frames, which is what Lab 4 measures.
    """

    def __init__(self, *, score_threshold: float = 0.30, device: str = "cpu") -> None:
        super().__init__(score_threshold=score_threshold, device=device)
        self.pretrained_transfer: dict = {}

    def build(self) -> bool:
        try:
            import torchvision  # noqa: F401  (imported for a clear error if missing)

            model, transfer = _pretrained_ssdlite(num_classes=len(labels_mod.LABELS) + 1)
            self._model = model.to(self.device)
            self._categories = ["background", *labels_mod.LABELS]
            self.pretrained_transfer = transfer
            return True
        except Exception as exc:  # noqa: BLE001
            self.load_error = f"{type(exc).__name__}: {exc}"
            return False

    def save(self, path: str | Path, extra: dict | None = None) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"state_dict": self._model.state_dict(),
                    "extra": dict(extra or {}),
                    "transfer": self.pretrained_transfer}, path)
        return path

    def load_weights(self, path: str | Path) -> bool:
        payload = torch.load(Path(path), map_location=self.device, weights_only=False)
        if self._model is None and not self.build():
            return False
        self._model.load_state_dict(payload["state_dict"])
        self._model.eval()
        self.pretrained_transfer = payload.get("transfer", {})
        return True

    @torch.no_grad()
    def predict(self, frame_bgr: np.ndarray, *, traffic_only: bool = True,
                score_threshold: float | None = None,
                nms_iou: float | None = None) -> list[metrics.Detection]:
        """Detect vehicles. Unlike the COCO model, every label is already in our space."""
        if self._model is None:
            return []
        threshold = self.score_threshold if score_threshold is None else score_threshold
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        tensor = torch.from_numpy(rgb.astype(np.float32) / 255.0).permute(2, 0, 1)
        out = self._model([tensor.to(self.device)])[0]
        results: list[metrics.Detection] = []
        for box, score, label in zip(out["boxes"], out["scores"], out["labels"]):
            value = float(score)
            if value < threshold:
                continue
            index = int(label) - 1
            if index < 0 or index >= len(labels_mod.LABELS):
                continue
            results.append(metrics.Detection(box.tolist(), index, value))
        return results


def finetune_traffic_detector(
    samples: Sequence[DetectionSample],
    *,
    epochs: int = 3,
    lr: float = 1e-4,
    batch_size: int = 4,
    seed: int = 0,
    log: bool = True,
) -> tuple[TrafficSSDLite, dict]:
    """Fine-tune SSDLite on labelled frames and return the wrapper plus a loss history."""
    set_seed(seed)
    detector = TrafficSSDLite()
    if not detector.build():
        raise RuntimeError(f"could not build the detector: {detector.load_error}")

    model = detector._model
    model.train()
    # Only parameters that require gradients are trained; with a small learning rate and few
    # epochs this behaves like careful adaptation rather than a full re-train.
    params = [p for p in model.parameters() if p.requires_grad]
    optimiser = torch.optim.SGD(params, lr=lr, momentum=0.9, weight_decay=5e-4)
    prepared = [_ssd_targets(sample.frame, sample.boxes, sample.labels) for sample in samples]

    history: dict = {"loss": [], "epochs": []}
    n = len(prepared)
    for epoch in range(1, epochs + 1):
        order = np.random.default_rng(seed + epoch).permutation(n)
        total, batches = 0.0, 0
        for start in range(0, n, batch_size):
            idx = order[start:start + batch_size]
            images = [prepared[i][0] for i in idx]
            targets = [prepared[i][1] for i in idx]
            loss_dict = model(images, targets)
            loss = sum(loss_dict.values())
            optimiser.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 5.0)
            optimiser.step()
            total += float(loss.detach())
            batches += 1
        history["loss"].append(round(total / max(batches, 1), 4))
        history["epochs"].append(epoch)
        if log:
            print(f"  epoch {epoch:2d}  loss {history['loss'][-1]:.4f}  "
                  f"({batches} batches)")
    model.eval()
    return detector, history


# ---------------------------------------------------------------------------
# Video utilities shared by the labs
# ---------------------------------------------------------------------------


def detect_video(
    path: str | Path,
    detector,
    *,
    stride: int = 1,
    limit: int | None = None,
    traffic_only: bool = True,
) -> list[dict]:
    """Run a detector over a video and return one record per processed frame.

    Each record carries the source frame index, its timestamp, the detections, and the time
    the detector took. Nothing is drawn here: review, metrics and writing are separate so
    the same detections can feed a report and an annotated video without being computed
    twice.
    """
    records: list[dict] = []
    import time

    for index, stamp, frame in video_mod.iter_frames(path, stride=stride, limit=limit):
        started = time.perf_counter()
        if isinstance(detector, SSDLiteDetector):
            dets = detector.predict(frame, traffic_only=traffic_only)
        else:
            dets = detector.predict(frame)
        elapsed = time.perf_counter() - started
        records.append({
            "frame": index,
            "t_s": round(stamp, 3),
            "detections": [d.as_dict() for d in dets],
            "seconds": elapsed,
        })
    return records


def to_metric_detections(records: Sequence[dict]) -> list[list[metrics.Detection]]:
    return [[metrics.Detection(list(d["box"]), int(d["label"]), float(d["score"]),
                               d.get("track_id"))
             for d in rec["detections"]] for rec in records]


def truth_to_metric(gt_records: Sequence[dict]) -> list[list[dict]]:
    return [[{"box": obj["box"], "label": labels_mod.LABEL_TO_INDEX[obj["class"]],
              "track_id": obj.get("track_id")} for obj in rec["objects"]]
            for rec in gt_records]
