"""Lab 5 - Train an object detector on annotated images.

Steps: load the annotated detection set, verify the annotations, train the
heatmap detector, decode boxes, and report mAP@0.5. The lab also writes the
annotations it used, so a grader can check the data rather than trust the model.

Run:

    python lab5_detector_training.py
    python lab5_detector_training.py --selftest
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vision_core import annotations as ann_mod
from vision_core import datasets, dataio, detection, detection_train, models

OUTPUTS = Path(__file__).resolve().parent / "outputs"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    epochs = 8 if args.selftest else args.epochs

    records = dataio.detection_records()
    split = int(len(records) * 0.8)
    train_records, test_records = records[:split], records[split:]
    print(f"images {len(records)}  train {len(train_records)}  test {len(test_records)}")
    print(f"boxes  {sum(len(r.meta['boxes']) for r in records)}  classes {datasets.SHAPE_CLASSES}")

    # Validate before training: bad annotations produce a model that never learns.
    problems = 0
    for rec in records:
        h, w = rec.image.shape[:2]
        boxes = [ann_mod.Annotation(detection_train.SHAPE_INDEX[o["class"]], tuple(o["xyxy"])) for o in rec.meta["boxes"]]
        report = ann_mod.validate_annotations(boxes, w, h, len(datasets.SHAPE_CLASSES))
        problems += len(report["problems"])
    print(f"annotation check: {problems} problem(s)")

    model, history = detection_train.train_detector(
        train_records,
        num_classes=len(datasets.SHAPE_CLASSES),
        epochs=epochs,
        width=24,
        batch_size=16,
        lr=2e-3,
        size_weight=0.5,
        seed=0,
    )

    results = detection.predict_records(model, test_records, score_threshold=0.3)
    metrics = detection_train.quick_detector_metrics(model, test_records, datasets.SHAPE_CLASSES, score_threshold=0.3)
    print("\n=== test metrics at score threshold 0.30, IoU 0.50")
    print(f"mAP@0.5     {metrics['map50']:.3f}")
    print(f"precision   {metrics['precision']:.3f}")
    print(f"recall      {metrics['recall']:.3f}")
    print(f"predictions {metrics['n_predictions']} for {sum(len(r.ground_truth) for r in results)} ground-truth boxes")
    for name, ap in metrics["per_class_ap50"].items():
        print(f"  AP50 {name:<8} {ap:.3f}")

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    checkpoint = models.save_checkpoint(
        model,
        OUTPUTS / "detector.pt",
        {"classes": list(datasets.SHAPE_CLASSES), "stride": model.stride, "map50": metrics["map50"], "epochs": epochs},
    )
    report_path = OUTPUTS / "lab5_detector_report.json"
    report_path.write_text(
        json.dumps(
            {
                "epochs": epochs,
                "history": {k: v for k, v in history.items() if isinstance(v, list)},
                "metrics": metrics,
                "score_threshold": 0.3,
                "iou_threshold": 0.5,
                "train_images": len(train_records),
                "test_images": len(test_records),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\ncheckpoint {checkpoint}\nreport     {report_path}")

    failures = 0
    if problems:
        print(f"FAIL  {problems} invalid annotation(s)")
        failures += 1
    if metrics["n_predictions"] == 0:
        print("FAIL  the detector produced no boxes at all")
        failures += 1
    if not 0.0 <= metrics["map50"] <= 1.0:
        print("FAIL  mAP outside 0-1")
        failures += 1
    if not checkpoint.exists():
        print("FAIL  checkpoint not written")
        failures += 1

    print(f"\n{failures} failure(s)")
    if failures == 0:
        print("PASS  detector trained, decoded, and scored on held-out images")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
