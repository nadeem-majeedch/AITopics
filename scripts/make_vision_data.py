"""Generate every dataset used by the computer vision section.

Run once, from the repository root:

    python scripts/make_vision_data.py
    python scripts/make_vision_data.py --check
    python scripts/make_vision_data.py --check --json

``--check`` verifies the existing ``objects_p06`` directory against its
``manifest.json`` without writing any data. It reports missing, modified,
unexpected and byte-identical files, class counts, source-group integrity, and
source overlap between splits. The machine-readable report is written to
``objects_p06/manifest_check.json`` and the exit status is 0 only when it passes.

Outputs (all under ``data/computer-vision/``, which is git-ignored because it is
generated):

    classification/   train|val|test PNGs + manifests + leakage audits
    objects/          the four everyday-object classes for the fine-tuning lab
    objects_p06/      the 960-image stratified P06 set plus manifest.json
    detection/        images, YOLO labels, COCO json, data.yaml
    segmentation/     images and masks
    faces/            synthetic faces + faces.json ground truth
    dataset_card.json licence, provenance, sizes, and known issues

Everything is deterministic: the same script and the same seeds produce
byte-identical images, so a student's numbers are comparable to the ones printed
in the lesson pages.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "projects" / "computer-vision"))

from vision_core import annotations, datasets, faces, imaging, manifest  # noqa: E402
from vision_core.detection_train import SHAPE_INDEX  # noqa: E402

OUT = REPO_ROOT / "data" / "computer-vision"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def build_classification() -> dict:
    records = datasets.make_classification_dataset(n_sources=100, size=32, seed=0, variants_per_source=3)
    grouped = datasets.group_split(records, seed=0)
    naive = datasets.random_split(records, seed=0)

    datasets.save_split_images(grouped, OUT / "classification", datasets.SHAPE_CLASSES)
    datasets.save_split_images(naive, OUT / "classification_random_split", datasets.SHAPE_CLASSES)

    audit_grouped = datasets.audit_leakage(grouped)
    audit_naive = datasets.audit_leakage(naive)
    _write_json(OUT / "classification" / "leakage.json", audit_grouped)
    _write_json(OUT / "classification_random_split" / "leakage.json", audit_naive)

    # Combined arrays are what the labs load; keep them as .npy for speed.
    for name, split in grouped.items():
        np.save(OUT / "classification" / f"{name}_images.npy", np.stack([r.image for r in split]))
        np.save(OUT / "classification" / f"{name}_labels.npy", np.array([r.label for r in split], dtype=np.int64))

    return {
        "n_images": len(records),
        "n_sources": len({r.source_id for r in records}),
        "splits": {k: len(v) for k, v in grouped.items()},
        "balance": datasets.class_balance(records, datasets.SHAPE_CLASSES),
        "grouped_leak": audit_grouped["leaky"],
        "grouped_cross_duplicates": audit_grouped["cross_split_near_duplicate_count"],
        "naive_leak": audit_naive["leaky"],
        "naive_cross_duplicates": audit_naive["cross_split_near_duplicate_count"],
    }


def build_objects() -> dict:
    records = datasets.make_object_dataset(n_sources=40, size=32, seed=1, variants_per_source=3)
    grouped = datasets.group_split(records, seed=1)
    datasets.save_split_images(grouped, OUT / "objects", datasets.OBJECT_CLASSES)
    for name, split in grouped.items():
        np.save(OUT / "objects" / f"{name}_images.npy", np.stack([r.image for r in split]))
        np.save(OUT / "objects" / f"{name}_labels.npy", np.array([r.label for r in split], dtype=np.int64))
    return {
        "n_images": len(records),
        "splits": {k: len(v) for k, v in grouped.items()},
        # Per-class counts are the first thing a capstone must inspect: a small
        # random source split can leave a class absent from validation or test.
        "balance": {k: datasets.class_balance(v, datasets.OBJECT_CLASSES) for k, v in grouped.items()},
    }


def build_objects_p06() -> dict:
    """Larger, class-stratified object set for the P06 evaluation capstone.

    The 120-image ``objects`` set stays unchanged for the labs. This set has 60
    source groups per class (240 total) and four variants per source, giving
    168/36/36 images per class with every class present in every split. That is
    enough to make per-class test metrics meaningful, while remaining a synthetic
    teaching set rather than a real-world benchmark.
    """
    records = datasets.make_object_dataset(n_sources=240, size=32, seed=11, variants_per_source=4)
    grouped = datasets.stratified_group_split(records, seed=11)
    datasets.save_split_images(grouped, OUT / "objects_p06", datasets.OBJECT_CLASSES)
    for name, split in grouped.items():
        np.save(OUT / "objects_p06" / f"{name}_images.npy", np.stack([r.image for r in split]))
        np.save(OUT / "objects_p06" / f"{name}_labels.npy", np.array([r.label for r in split], dtype=np.int64))
    payload = manifest.build_manifest(
        OUT / "objects_p06",
        grouped,
        datasets.OBJECT_CLASSES,
        dataset="objects_p06",
        seed=11,
        parameters={"n_sources": 240, "variants_per_source": 4, "size": 32, "fractions": [0.7, 0.15, 0.15]},
    )
    manifest.write_manifest(OUT / "objects_p06", payload)

    def overlap(left: str, right: str) -> int:
        return len(
            {r.source_id for r in grouped[left]} & {r.source_id for r in grouped[right]}
        )

    return {
        "n_images": len(records),
        "n_sources": len({r.source_id for r in records}),
        "splits": {k: len(v) for k, v in grouped.items()},
        "balance": {k: datasets.class_balance(v, datasets.OBJECT_CLASSES) for k, v in grouped.items()},
        "source_overlap": {
            "train_test": overlap("train", "test"),
            "train_val": overlap("train", "val"),
            "val_test": overlap("val", "test"),
        },
        "manifest": {"version": payload["version"], "files": len(payload["files"])},
    }


def build_detection() -> dict:
    records = datasets.make_detection_dataset(n_images=200, size=64, seed=2)
    images = {f"{i:04d}": r.image for i, r in enumerate(records)}
    labels = {
        f"{i:04d}": [annotations.Annotation(SHAPE_INDEX[o["class"]], tuple(o["xyxy"])) for o in r.meta["boxes"]]
        for i, r in enumerate(records)
    }
    annotations.write_yolo_dataset(OUT / "detection", images, labels, datasets.SHAPE_CLASSES)
    coco = annotations.to_coco(images, labels, datasets.SHAPE_CLASSES, description="synthetic shapes with bounding boxes")
    annotations.write_coco(OUT / "detection" / "annotations_coco.json", coco)

    boxes_per_image = [len(v) for v in labels.values()]
    classes = [b.class_id for v in labels.values() for b in v]
    return {
        "n_images": len(records),
        "n_boxes": int(sum(boxes_per_image)),
        "boxes_per_image": {"min": int(min(boxes_per_image)), "max": int(max(boxes_per_image)), "mean": float(np.mean(boxes_per_image))},
        "class_counts": {name: int(classes.count(i)) for i, name in enumerate(datasets.SHAPE_CLASSES)},
        "coco_categories": len(coco["categories"]),
    }


def build_segmentation() -> dict:
    records = datasets.make_segmentation_dataset(n_images=80, size=64, seed=3)
    directory = OUT / "segmentation"
    (directory / "images").mkdir(parents=True, exist_ok=True)
    (directory / "masks").mkdir(parents=True, exist_ok=True)
    for i, rec in enumerate(records):
        stem = f"{i:04d}"
        imaging.save_image(rec.image, directory / "images" / f"{stem}.png")
        imaging.save_image(rec.meta["mask"], directory / "masks" / f"{stem}.png")
    np.save(directory / "images.npy", np.stack([r.image for r in records]))
    np.save(directory / "masks.npy", np.stack([r.meta["mask"] for r in records]))
    totals = np.zeros(len(datasets.SEGMENTATION_CLASSES), dtype=np.int64)
    for rec in records:
        for c in range(len(datasets.SEGMENTATION_CLASSES)):
            totals[c] += int((rec.meta["mask"] == c).sum())
    fraction = totals / totals.sum()
    return {
        "n_images": len(records),
        "class_pixel_fraction": {name: float(fraction[i]) for i, name in enumerate(datasets.SEGMENTATION_CLASSES)},
    }


def build_faces() -> dict:
    records = faces.make_face_dataset(per_identity=8, size=faces.FACE_SIZE, seed=4)
    directory = OUT / "faces"
    (directory / "images").mkdir(parents=True, exist_ok=True)
    index = []
    for i, rec in enumerate(records):
        name = f"{i:03d}_{rec.identity}.png"
        imaging.save_image(rec.image, directory / "images" / name)
        index.append(
            {
                "file": name,
                "identity": rec.identity,
                "tone_group": rec.tone_group,
                "truth_box": list(rec.truth_box),
                "landmarks": rec.landmarks,
                "variant": rec.meta["variant"],
            }
        )
    _write_json(directory / "faces.json", {"size": faces.FACE_SIZE, "records": index})

    report = faces.detection_report(records)
    return {
        "n_images": len(records),
        "n_identities": len({r.identity for r in records}),
        "detector_recall": report["overall_recall"],
        "per_tone_group": report["per_group"],
    }


def build_dataset_card(stats: dict) -> dict:
    card = {
        "name": "AITopics synthetic vision corpus",
        "version": "1.0.0",
        "created": "2026-11-01",
        "source": "generated by scripts/make_vision_data.py",
        "licence": "CC0-1.0 (public domain dedication)",
        "attribution": "Generated for the AITopics course; no third-party images are included.",
        "contains_personal_data": False,
        "contains_real_people": False,
        "notes": [
            "All images are rendered from NumPy primitives; no scrape, no download, no real person.",
            "The face set is synthetic and exists to teach detection, landmarks, verification, and identification concepts.",
            "Synthetic data is not a substitute for real photographs when real-world accuracy matters.",
            "Class indices follow SHAPE_CLASSES / OBJECT_CLASSES / SEGMENTATION_CLASSES order.",
            "objects_p06 ships with manifest.json (SHA-256 per image). Run scripts/make_vision_data.py --check to verify it; duplicate variants within a split are reported as warnings, duplicates across splits as failures.",
        ],
        "stats": stats,
    }
    _write_json(OUT / "dataset_card.json", card)
    return card


def run_check(as_json: bool = False) -> int:
    """Verify ``objects_p06`` against its manifest without regenerating data."""
    root = OUT / "objects_p06"
    result = manifest.check_dataset(root)
    if root.is_dir():
        (root / manifest.CHECK_NAME).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if as_json:
        print(json.dumps(result, indent=2))
    else:
        print("\n".join(manifest.summarize(result)))
        if root.is_dir():
            print(f"report: {root / manifest.CHECK_NAME}")
    return 0 if result["ok"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate the synthetic vision datasets (CC0-1.0), or verify the P06 set against its manifest."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the existing objects_p06 dataset against manifest.json; write no data",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="with --check, print the machine-readable report instead of the summary",
    )
    args = parser.parse_args(argv)
    if args.check:
        return run_check(args.json)

    OUT.mkdir(parents=True, exist_ok=True)
    print(f"generating into {OUT}")

    print("\n[1/5] classification")
    cls = build_classification()
    print(f"  images {cls['n_images']}  sources {cls['n_sources']}  splits {cls['splits']}  balance {cls['balance']}")
    print(f"  grouped split leaks: {cls['grouped_leak']} (cross-split near-duplicates {cls['grouped_cross_duplicates']})")
    print(f"  naive split leaks:   {cls['naive_leak']} (cross-split near-duplicates {cls['naive_cross_duplicates']})")

    print("\n[2/5] objects")
    obj = build_objects()
    print(f"  images {obj['n_images']}  splits {obj['splits']}")
    print(f"  per-class counts {obj['balance']}")

    print("\n[2b/6] P06 object evaluation set")
    p06 = build_objects_p06()
    print(f"  images {p06['n_images']}  splits {p06['splits']}  sources {p06['n_sources']}")
    print(f"  per-class counts {p06['balance']}  source overlap {p06['source_overlap']}")
    print(f"  manifest v{p06['manifest']['version']} for {p06['manifest']['files']} files")

    print("\n[3/5] detection")
    det = build_detection()
    print(f"  images {det['n_images']}  boxes {det['n_boxes']}  per image {det['boxes_per_image']}")
    print(f"  class counts {det['class_counts']}")

    print("\n[4/5] segmentation")
    seg = build_segmentation()
    print(f"  images {seg['n_images']}  pixel fractions {seg['class_pixel_fraction']}")

    print("\n[5/5] faces")
    fc = build_faces()
    print(f"  images {fc['n_images']}  identities {fc['n_identities']}  detector recall {fc['detector_recall']:.3f}")
    for group, stats in sorted(fc["per_tone_group"].items()):
        print(f"    {group}: recall {stats['recall']:.3f} on {stats['n']} images")

    card = build_dataset_card({"classification": cls, "objects": obj, "objects_p06": p06, "detection": det, "segmentation": seg, "faces": fc})
    print(f"\ndataset card: {OUT / 'dataset_card.json'}  (licence {card['licence']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
