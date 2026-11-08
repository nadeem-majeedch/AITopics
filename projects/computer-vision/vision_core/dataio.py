"""Load the generated datasets, or regenerate them deterministically if absent.

Every lab calls these functions instead of touching ``data/`` directly. Two
properties matter:

* **No hard dependency on a generated directory.** If ``data/computer-vision`` is
  missing (fresh clone, CI, a student who deleted it), the same seeds are used to
  build the data in memory, so a lab still runs and still reports the same
  numbers. The lesson pages quote those numbers.
* **One place to change a seed.** If a dataset is regenerated with different
  seeds, the labs follow automatically.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

import numpy as np

from . import datasets

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = REPO_ROOT / "data" / "computer-vision"


def _load_arrays(root: Path, prefix: str) -> dict | None:
    files = {name: root / f"{name}_{prefix}.npy" for name in ("train", "val", "test")}
    if not all(f.exists() for f in files.values()):
        return None
    out = {}
    for name, path in files.items():
        key = "labels" if prefix == "labels" else "images"
        out.setdefault(key, {})[name] = np.load(path)
    return out


def classification_splits(seed: int = 0) -> dict[str, dict[str, np.ndarray]]:
    """``{split: {"images": NHWC, "labels": N}}`` from disk, else built in memory."""
    on_disk = _load_arrays(DATA_ROOT / "classification", "images")
    labels_on_disk = _load_arrays(DATA_ROOT / "classification", "labels")
    if on_disk and labels_on_disk:
        return {
            split: {"images": on_disk["images"][split], "labels": labels_on_disk["labels"][split]}
            for split in ("train", "val", "test")
        }

    records = datasets.make_classification_dataset(n_sources=100, size=32, seed=seed, variants_per_source=3)
    grouped = datasets.group_split(records, seed=seed)
    return {
        split: {"images": np.stack([r.image for r in part]), "labels": np.array([r.label for r in part], dtype=np.int64)}
        for split, part in grouped.items()
    }


def object_splits(seed: int = 1) -> dict[str, dict[str, np.ndarray]]:
    on_disk = _load_arrays(DATA_ROOT / "objects", "images")
    labels_on_disk = _load_arrays(DATA_ROOT / "objects", "labels")
    if on_disk and labels_on_disk:
        return {
            split: {"images": on_disk["images"][split], "labels": labels_on_disk["labels"][split]}
            for split in ("train", "val", "test")
        }
    records = datasets.make_object_dataset(n_sources=40, size=32, seed=seed, variants_per_source=3)
    grouped = datasets.group_split(records, seed=seed)
    return {
        split: {"images": np.stack([r.image for r in part]), "labels": np.array([r.label for r in part], dtype=np.int64)}
        for split, part in grouped.items()
    }


def classification_records(seed: int = 0) -> list[datasets.ImageRecord]:
    """Records (with ``source_id``) for the leakage audits."""
    records = datasets.make_classification_dataset(n_sources=100, size=32, seed=seed, variants_per_source=3)
    return records


def detection_records(n_images: int = 200, seed: int = 2) -> list[datasets.ImageRecord]:
    on_disk = DATA_ROOT / "detection" / "images"
    coco_path = DATA_ROOT / "detection" / "annotations_coco.json"
    if on_disk.exists() and coco_path.exists():
        from . import annotations as ann_mod

        from .imaging import load_image

        data = json.loads(coco_path.read_text(encoding="utf-8"))
        parsed, _names = ann_mod.from_coco(data)
        records = []
        for item in sorted(data["images"], key=lambda i: i["file_name"]):
            stem = Path(item["file_name"]).stem
            image = load_image(on_disk / item["file_name"])
            boxes = [
                {"class": datasets.SHAPE_CLASSES[a.class_id], "xyxy": [int(v) for v in a.box]}
                for a in parsed.get(stem, [])
            ]
            records.append(
                datasets.ImageRecord(image=image, label=-1, source_id=f"det-{stem}", meta={"boxes": boxes, "width": item["width"], "height": item["height"]})
            )
        if records:
            return records
    return datasets.make_detection_dataset(n_images=n_images, size=64, seed=seed)


def segmentation_records(n_images: int = 80, seed: int = 3) -> list[datasets.ImageRecord]:
    images_path = DATA_ROOT / "segmentation" / "images.npy"
    masks_path = DATA_ROOT / "segmentation" / "masks.npy"
    if images_path.exists() and masks_path.exists():
        images = np.load(images_path)
        masks = np.load(masks_path)
        return [
            datasets.ImageRecord(image=images[i], label=-1, source_id=f"seg-{i:04d}", meta={"mask": masks[i]})
            for i in range(len(images))
        ]
    return datasets.make_segmentation_dataset(n_images=n_images, size=64, seed=seed)


def face_records(per_identity: int = 8, seed: int = 4) -> list:
    from . import faces as faces_mod

    return faces_mod.make_face_dataset(per_identity=per_identity, seed=seed)


def dataset_card() -> dict:
    """The generated card, or a minimal stand-in when the data was built in memory."""
    path = DATA_ROOT / "dataset_card.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "name": "AITopics synthetic vision corpus",
        "licence": "CC0-1.0 (public domain dedication)",
        "source": "generated in memory by vision_core.datasets (data/ not present)",
        "contains_personal_data": False,
    }


def summary() -> dict:
    """Small inventory printed by Lab 1 and used by the section's selftests."""
    cls = classification_splits()
    objs = object_splits()
    det = detection_records()
    seg = segmentation_records()
    return {
        "data_root": str(DATA_ROOT),
        "exists_on_disk": DATA_ROOT.exists(),
        "classification": {k: int(len(v["labels"])) for k, v in cls.items()},
        "objects": {k: int(len(v["labels"])) for k, v in objs.items()},
        "detection_images": len(det),
        "detection_boxes": sum(len(r.meta["boxes"]) for r in det),
        "segmentation_images": len(seg),
        "licence": dataset_card().get("licence", "unknown"),
    }
