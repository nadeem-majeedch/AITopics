"""Annotation formats, conversions, validation, and split hygiene.

Four representations of the same thing exist in every video project, and students lose more
time to converting between them than to modelling:

===========================  ==========================================  =====================
Format                       Box convention                              Used by
===========================  ==========================================  =====================
COCO JSON                    ``[x, y, w, h]``, pixels, origin top-left    torchvision, pycocotools
YOLO text                    ``cx cy w h`` normalised to ``[0, 1]``      YOLO trainers
Pascal VOC XML               ``xmin, ymin, xmax, ymax``, 1-based         older detectors
This section's JSONL         ``[x1, y1, x2, y2]``, pixels                lab ground truth
===========================  ==========================================  =====================

The functions below convert between them and, more importantly, *check* the result. The
classic bug is a silent convention mismatch - a COCO ``w`` read as ``x2`` gives boxes that
are too small by the x offset - and it produces a detector that trains to mAP 0.05 with no
error message. ``validate_records`` is the guard: it rejects boxes outside the frame,
non-positive sizes, and labels not in the schema.

Splitting is by **video**, not by frame. Consecutive frames of one video are near-duplicates,
so a per-frame split leaks the test set into training and inflates every metric. Module 4
measures how much; ``split_by_video`` is the function that prevents it.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

# The label schema for the traffic section. Index order is the contract with the detector:
# ``label`` fields are indices into this list everywhere.
LABELS = ("car", "motorcycle", "bus", "truck")
LABEL_TO_INDEX = {name: i for i, name in enumerate(LABELS)}


def to_coco_box(box: Sequence[float]) -> list[float]:
    """``[x1, y1, x2, y2]`` -> COCO ``[x, y, w, h]``."""
    x1, y1, x2, y2 = [float(v) for v in box[:4]]
    return [x1, y1, x2 - x1, y2 - y1]


def from_coco_box(box: Sequence[float]) -> list[float]:
    """COCO ``[x, y, w, h]`` -> ``[x1, y1, x2, y2]``."""
    x, y, w, h = [float(v) for v in box[:4]]
    return [x, y, x + w, y + h]


def to_yolo(box: Sequence[float], width: int, height: int) -> list[float]:
    """``[x1, y1, x2, y2]`` -> normalised ``[cx, cy, w, h]``."""
    x1, y1, x2, y2 = [float(v) for v in box[:4]]
    cx = (x1 + x2) / 2.0 / width
    cy = (y1 + y2) / 2.0 / height
    return [cx, cy, (x2 - x1) / width, (y2 - y1) / height]


def from_yolo(values: Sequence[float], width: int, height: int) -> list[float]:
    """Normalised ``[cx, cy, w, h]`` -> ``[x1, y1, x2, y2]``."""
    cx, cy, w, h = [float(v) for v in values[:4]]
    return [(cx - w / 2) * width, (cy - h / 2) * height,
            (cx + w / 2) * width, (cy + h / 2) * height]


def validate_records(records: Iterable[dict], *, width: int, height: int,
                     labels: Sequence[str] = LABELS) -> dict:
    """Check annotated objects against the frame they belong to.

    Returns a report instead of raising, because a lab wants to *show* the broken records:
    an annotation tool that writes ``x2 < x1`` or a box 3 px outside the frame is a normal
    part of real datasets and the fix is to catch it before training, not after.
    """
    problems: list[str] = []
    n = 0
    for rec in records:
        for obj in rec.get("objects", []):
            n += 1
            box = obj.get("box")
            if not box or len(box) != 4:
                problems.append(f"frame {rec.get('frame')}: box is not 4 numbers: {box}")
                continue
            x1, y1, x2, y2 = [float(v) for v in box]
            if x2 <= x1 or y2 <= y1:
                problems.append(f"frame {rec.get('frame')}: non-positive box {box}")
            if x1 < -1 or y1 < -1 or x2 > width + 1 or y2 > height + 1:
                problems.append(f"frame {rec.get('frame')}: box outside {width}x{height}: {box}")
            if obj.get("class") not in labels:
                problems.append(f"frame {rec.get('frame')}: unknown class {obj.get('class')!r}")
    return {"objects": n, "problems": problems, "ok": not problems}


# ---------------------------------------------------------------------------
# COCO
# ---------------------------------------------------------------------------


def write_coco(
    path: str | Path,
    records: Sequence[dict],
    *,
    image_name: str,
    labels: Sequence[str] = LABELS,
) -> Path:
    """Write per-frame annotations as one COCO ``instances`` file.

    ``records`` are ``[{"frame": int, "objects": [{"track_id", "class", "box"}]}]``. Frame
    ``i`` becomes image ``i`` with ``file_name`` ``<image_name>_<i:04d>.jpg`` so the JSON
    stays valid even before the frames exist on disk.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    images, annotations = [], []
    ann_id = 1
    for rec in records:
        frame = int(rec["frame"])
        images.append({"id": frame + 1, "file_name": f"{image_name}_{frame:04d}.jpg",
                       "frame_index": frame})
        for obj in rec.get("objects", []):
            annotations.append({
                "id": ann_id,
                "image_id": frame + 1,
                "category_id": LABEL_TO_INDEX.get(obj["class"], 0) + 1,
                "bbox": [round(v, 2) for v in to_coco_box(obj["box"])],
                "area": round(float((obj["box"][2] - obj["box"][0])
                                    * (obj["box"][3] - obj["box"][1])), 2),
                "iscrowd": 0,
                "track_id": obj.get("track_id"),
            })
            ann_id += 1
    payload = {
        "info": {"description": "Synthetic traffic frames, generated by video_core.synth",
                 "licence": "CC0-1.0"},
        "images": images,
        "annotations": annotations,
        "categories": [{"id": i + 1, "name": name} for i, name in enumerate(labels)],
    }
    path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return path


def read_coco(path: str | Path) -> tuple[list[dict], list[dict], list[str]]:
    """Read a COCO instances file back into ``(records, boxes, category names)``."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    names = [c["name"] for c in payload["categories"]]
    by_image: dict[int, list[dict]] = {}
    for ann in payload["annotations"]:
        by_image.setdefault(int(ann["image_id"]), []).append({
            "class": names[int(ann["category_id"]) - 1],
            "box": from_coco_box(ann["bbox"]),
            "track_id": ann.get("track_id"),
        })
    records = [
        {"frame": int(img.get("frame_index", img["id"] - 1)),
         "objects": by_image.get(int(img["id"]), [])}
        for img in payload["images"]
    ]
    return records, payload["annotations"], names


# ---------------------------------------------------------------------------
# YOLO and Pascal VOC
# ---------------------------------------------------------------------------


def write_yolo(path: str | Path, records: Sequence[dict], *, width: int, height: int,
               labels: Sequence[str] = LABELS) -> Path:
    """One ``.txt`` per frame in YOLO format, plus ``classes.txt``."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    (path / "classes.txt").write_text("\n".join(labels) + "\n", encoding="utf-8")
    for rec in records:
        lines = []
        for obj in rec.get("objects", []):
            idx = LABEL_TO_INDEX[obj["class"]]
            cx, cy, w, h = to_yolo(obj["box"], width, height)
            lines.append(f"{idx} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
        (path / f"frame_{int(rec['frame']):04d}.txt").write_text("\n".join(lines) + "\n",
                                                                encoding="utf-8")
    return path


def write_voc(path: str | Path, rec: dict, *, width: int, height: int,
              image_name: str) -> Path:
    """Pascal VOC XML for one frame (1-based coordinates, as the format specifies)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    root = ET.Element("annotation")
    ET.SubElement(root, "filename").text = image_name
    size = ET.SubElement(root, "size")
    ET.SubElement(size, "width").text = str(width)
    ET.SubElement(size, "height").text = str(height)
    ET.SubElement(size, "depth").text = "3"
    for obj in rec.get("objects", []):
        node = ET.SubElement(root, "object")
        ET.SubElement(node, "name").text = obj["class"]
        bnd = ET.SubElement(node, "bndbox")
        x1, y1, x2, y2 = [int(round(v)) + 1 for v in obj["box"]]  # to 1-based
        ET.SubElement(bnd, "xmin").text = str(x1)
        ET.SubElement(bnd, "ymin").text = str(y1)
        ET.SubElement(bnd, "xmax").text = str(x2)
        ET.SubElement(bnd, "ymax").text = str(y2)
    tree = ET.ElementTree(root)
    ET.indent(tree)
    tree.write(path, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Splits
# ---------------------------------------------------------------------------


def split_by_video(
    items: Sequence[dict],
    *,
    fractions: tuple[float, float, float] = (0.6, 0.2, 0.2),
    seed: int = 0,
) -> dict[str, list[dict]]:
    """Split *videos* into train/val/test so no frame of a video appears twice.

    ``items`` are ``{"video": str, ...}`` records; the split is over the unique video names
    and every record of a video follows its video. This is the only split that answers the
    question a deployment will ask: does the system work on footage it has not seen?
    """
    if abs(sum(fractions) - 1.0) > 1e-6:
        raise ValueError("fractions must sum to 1")
    names = sorted({str(item["video"]) for item in items})
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(names))
    n_train = int(round(fractions[0] * len(names)))
    n_val = int(round(fractions[1] * len(names)))
    train = {names[i] for i in order[:n_train]}
    val = {names[i] for i in order[n_train:n_train + n_val]}
    test = set(names) - train - val
    return {
        "train": [item for item in items if str(item["video"]) in train],
        "val": [item for item in items if str(item["video"]) in val],
        "test": [item for item in items if str(item["video"]) in test],
    }


def video_leakage(splits: dict[str, Sequence[dict]]) -> dict:
    """Report videos shared between splits. The number a leaky split cannot hide."""
    names = {key: {str(item["video"]) for item in items} for key, items in splits.items()}
    overlaps = {}
    keys = list(names)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            shared = names[a] & names[b]
            if shared:
                overlaps[f"{a}-{b}"] = sorted(shared)
    return {"videos": {k: len(v) for k, v in names.items()}, "overlaps": overlaps,
            "leaky": bool(overlaps)}


def frame_split_leakage(records: Sequence[dict], splits: dict[str, Sequence[dict]]) -> dict:
    """How much a *frame*-level split would leak, for comparison with the video split."""
    frames = {key: {int(r["frame"]) for r in items} for key, items in splits.items()}
    keys = list(frames)
    shared = 0
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            shared += len(frames[a] & frames[b])
    return {"shared_frame_ids": shared, "leaky": shared > 0}
