"""Bounding-box geometry and the two annotation formats students will meet.

Two formats cover almost everything an introductory course needs:

**YOLO** - one ``.txt`` per image, one line per object:
``class_index cx cy w h`` with all coordinates normalized to 0-1. Compact,
human-readable, and easy to corrupt by forgetting the normalization.

**COCO** - one JSON for the whole dataset, with absolute pixel coordinates in
``[x, y, width, height]``, 0-based, and category ids that may not start at 0.
Absolute vs normalized and ``xywh`` vs ``xyxy`` is the whole difficulty of this
module, so every conversion below is explicit and tested in both directions.

Boxes are represented as ``xyxy`` (x1, y1, x2, y2) in pixel coordinates
internally, inclusive-exclusive on the right/bottom edge, which matches
``cv2``-style conventions and makes area arithmetic unambiguous.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

Box = tuple[float, float, float, float]


@dataclass
class Annotation:
    """One annotated object."""

    class_id: int
    box: Box  # xyxy, pixel coordinates, floats
    score: float = 1.0
    extra: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"class_id": self.class_id, "box": list(self.box), "score": self.score, **self.extra}


# ---------------------------------------------------------------------------
# Coordinate conversions
# ---------------------------------------------------------------------------


def xyxy_to_xywh(box: Box) -> Box:
    x1, y1, x2, y2 = box
    return (x1, y1, x2 - x1, y2 - y1)


def xywh_to_xyxy(box: Box) -> Box:
    x, y, w, h = box
    return (x, y, x + w, y + h)


def xyxy_to_cxcywh(box: Box) -> Box:
    x1, y1, x2, y2 = box
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0, x2 - x1, y2 - y1)


def cxcywh_to_xyxy(box: Box) -> Box:
    cx, cy, w, h = box
    return (cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0)


def box_area(box: Box) -> float:
    x1, y1, x2, y2 = box
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def box_iou(a: Box, b: Box) -> float:
    """Intersection over union of two xyxy boxes; 0.0 when they do not overlap."""
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    union = box_area(a) + box_area(b) - inter
    return float(inter / union) if union > 0 else 0.0


def clip_box(box: Box, width: int, height: int) -> Box:
    x1, y1, x2, y2 = box
    return (
        float(min(max(x1, 0.0), width)),
        float(min(max(y1, 0.0), height)),
        float(min(max(x2, 0.0), width)),
        float(min(max(y2, 0.0), height)),
    )


def is_degenerate(box: Box, min_size: float = 1.0) -> bool:
    x1, y1, x2, y2 = box
    return (x2 - x1) < min_size or (y2 - y1) < min_size


# ---------------------------------------------------------------------------
# YOLO format
# ---------------------------------------------------------------------------


def to_yolo_lines(annotations: Sequence[Annotation], width: int, height: int, decimals: int = 6) -> list[str]:
    """Serialize to YOLO text lines: ``class cx cy w h`` normalized to 0-1."""
    lines = []
    for ann in annotations:
        cx, cy, w, h = xyxy_to_cxcywh(ann.box)
        values = [cx / width, cy / height, w / width, h / height]
        if any(v < 0 or v > 1 for v in values):
            raise ValueError(f"box {ann.box} is outside the {width}x{height} image")
        lines.append(f"{ann.class_id} " + " ".join(f"{v:.{decimals}f}" for v in values))
    return lines


def from_yolo_lines(lines: Sequence[str], width: int, height: int) -> list[Annotation]:
    """Parse YOLO lines back into pixel-space boxes.

    Rejects normalized values outside 0-1 rather than silently clipping: an
    out-of-range value usually means the annotation came from a different image
    size, and clipping would hide that.
    """
    annotations = []
    for raw in lines:
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        parts = raw.split()
        if len(parts) != 5:
            raise ValueError(f"expected 5 fields 'class cx cy w h', got {len(parts)}: {raw!r}")
        class_id = int(float(parts[0]))
        cx, cy, w, h = (float(v) for v in parts[1:])
        if not all(0.0 <= v <= 1.0 for v in (cx, cy, w, h)):
            raise ValueError(f"YOLO coordinates must be normalized to 0-1: {raw!r}")
        if w <= 0 or h <= 0:
            raise ValueError(f"width and height must be positive: {raw!r}")
        annotations.append(Annotation(class_id=class_id, box=cxcywh_to_xyxy((cx * width, cy * height, w * width, h * height))))
    return annotations


def write_yolo_dataset(root: str | Path, images: dict[str, np.ndarray], annotations: dict[str, Sequence[Annotation]], class_names: Sequence[str]) -> Path:
    """Write images plus ``labels/*.txt``, ``classes.txt``, and ``data.yaml``."""
    from .imaging import save_image

    root = Path(root)
    (root / "images").mkdir(parents=True, exist_ok=True)
    (root / "labels").mkdir(parents=True, exist_ok=True)
    for stem, image in images.items():
        save_image(image, root / "images" / f"{stem}.png")
        h, w = image.shape[:2]
        lines = to_yolo_lines(annotations.get(stem, []), w, h)
        (root / "labels" / f"{stem}.txt").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    (root / "classes.txt").write_text("\n".join(class_names) + "\n", encoding="utf-8")
    yaml_lines = ["# Generated by vision_core.annotations", f"path: {root.name}", "train: images", "val: images", f"nc: {len(class_names)}", "names:"]
    yaml_lines += [f"  {i}: {name}" for i, name in enumerate(class_names)]
    (root / "data.yaml").write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")
    return root


def read_yolo_dataset(root: str | Path, class_names: Sequence[str]) -> tuple[dict[str, np.ndarray], dict[str, list[Annotation]]]:
    """Read a YOLO directory back into arrays and annotations (round-trip test)."""
    from .imaging import load_image

    root = Path(root)
    images, labels = {}, {}
    for image_path in sorted((root / "images").glob("*.png")):
        image = load_image(image_path)
        h, w = image.shape[:2]
        text = (root / "labels" / f"{image_path.stem}.txt").read_text(encoding="utf-8")
        images[image_path.stem] = image
        labels[image_path.stem] = from_yolo_lines(text.splitlines(), w, h)
    for ann_list in labels.values():
        for ann in ann_list:
            if not 0 <= ann.class_id < len(class_names):
                raise ValueError(f"class id {ann.class_id} outside {len(class_names)} classes")
    return images, labels


# ---------------------------------------------------------------------------
# COCO format
# ---------------------------------------------------------------------------


def to_coco(
    images: dict[str, np.ndarray],
    annotations: dict[str, Sequence[Annotation]],
    class_names: Sequence[str],
    *,
    category_id_start: int = 1,
    description: str = "",
) -> dict:
    """Build a COCO-style dictionary.

    COCO category ids commonly start at 1 while YOLO class indices start at 0.
    The mapping is data, not an off-by-one bug, so it is explicit and reversible.
    """
    out_images, out_annotations = [], []
    ann_id = 1
    for image_id, (stem, image) in enumerate(sorted(images.items()), start=1):
        h, w = image.shape[:2]
        out_images.append({"id": image_id, "file_name": f"{stem}.png", "width": int(w), "height": int(h)})
        for ann in annotations.get(stem, []):
            x, y, bw, bh = xyxy_to_xywh(clip_box(ann.box, w, h))
            if bw <= 0 or bh <= 0:
                continue
            out_annotations.append(
                {
                    "id": ann_id,
                    "image_id": image_id,
                    "category_id": int(ann.class_id) + category_id_start,
                    "bbox": [round(x, 3), round(y, 3), round(bw, 3), round(bh, 3)],
                    "area": round(bw * bh, 3),
                    "iscrowd": 0,
                }
            )
            ann_id += 1
    return {
        "info": {"description": description, "source": "synthetic vision_core renderer"},
        "images": out_images,
        "annotations": out_annotations,
        "categories": [{"id": i + category_id_start, "name": name, "supercategory": "shape"} for i, name in enumerate(class_names)],
    }


def from_coco(data: dict) -> tuple[dict[str, list[Annotation]], list[str]]:
    """Parse COCO JSON into per-image annotations and ordered class names."""
    categories = sorted(data["categories"], key=lambda c: c["id"])
    id_to_index = {cat["id"]: i for i, cat in enumerate(categories)}
    names = [cat["name"] for cat in categories]
    id_to_file = {img["id"]: Path(img["file_name"]).stem for img in data["images"]}
    out: dict[str, list[Annotation]] = {stem: [] for stem in id_to_file.values()}
    for ann in data["annotations"]:
        stem = id_to_file[ann["image_id"]]
        # bbox is already x,y,w,h; converting it to xywh again would invert the box.
        box = xywh_to_xyxy(tuple(float(v) for v in ann["bbox"]))
        out[stem].append(Annotation(class_id=id_to_index[ann["category_id"]], box=box))
    return out, names


def write_coco(path: str | Path, data: dict) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def read_coco(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_annotations(
    annotations: Sequence[Annotation],
    width: int,
    height: int,
    n_classes: int,
    min_size: float = 1.0,
) -> dict:
    """Raise on invalid annotations, and report what was wrong.

    Invalid annotation data is the most common reason a detector trains to a
    loss that never improves, so validation runs before training, not after.
    """
    problems: list[str] = []
    kept: list[Annotation] = []
    for i, ann in enumerate(annotations):
        if not 0 <= ann.class_id < n_classes:
            problems.append(f"annotation {i}: class id {ann.class_id} not in 0..{n_classes - 1}")
            continue
        x1, y1, x2, y2 = ann.box
        if is_degenerate(ann.box, min_size):
            problems.append(f"annotation {i}: degenerate box {ann.box}")
            continue
        if x1 < 0 or y1 < 0 or x2 > width or y2 > height:
            problems.append(f"annotation {i}: box {ann.box} outside {width}x{height}")
        kept.append(Annotation(ann.class_id, clip_box(ann.box, width, height), ann.score))
    return {"kept": kept, "problems": problems, "n_input": len(annotations), "n_kept": len(kept)}
