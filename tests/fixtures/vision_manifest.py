"""Build a tiny, deterministic manifest-managed dataset for CI.

The complete P06 corpus is generated and git-ignored, so CI cannot rely on it.
This fixture writes six 2x2 PNGs (two classes across train/val/test) and a real
``manifest.json`` in the same shape as ``vision_core.manifest``. It is small
enough to build in a temporary directory on every test run and is never the
source of a course result.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

CLASSES = ("circle", "square")
SPLITS = ("train", "val", "test")


def build_manifest_fixture(data_dir: Path, name: str = "objects_p06_fixture") -> Path:
    """Write the fixture under ``data_dir`` and return the dataset directory."""
    root = Path(data_dir) / name
    files: dict[str, dict[str, object]] = {}
    splits: dict[str, int] = {}
    class_counts: dict[str, dict[str, int]] = {}
    source_groups: dict[str, int] = {}

    for split_index, split in enumerate(SPLITS):
        records = []
        for label, class_name in enumerate(CLASSES):
            relative = f"{split}/{len(records):05d}.png"
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            colour = (20 + split_index * 40 + label * 8, 60, 120)
            Image.new("RGB", (2, 2), colour).save(path)
            raw = path.read_bytes()
            records.append(
                {
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "bytes": len(raw),
                    "split": split,
                    "label": label,
                    "label_name": class_name,
                    "source_id": f"{split}-{class_name}",
                }
            )
        for index, entry in enumerate(records):
            files[f"{split}/{index:05d}.png"] = entry
        splits[split] = len(records)
        class_counts[split] = {class_name: 1 for class_name in CLASSES}
        source_groups[split] = len(records)

    payload = {
        "dataset": "objects_p06_fixture",
        "version": "1.0.0",
        "classes": list(CLASSES),
        "seed": 0,
        "parameters": {"purpose": "test fixture"},
        "splits": splits,
        "class_counts": class_counts,
        "source_groups": source_groups,
        "files": files,
    }
    (root / "manifest.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    return root
