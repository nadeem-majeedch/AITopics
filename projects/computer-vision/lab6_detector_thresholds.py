"""Lab 6 - Evaluate a detector across confidence thresholds.

A detector has no single precision. It has a curve, and the operating point is a
decision. This lab reports:

* precision, recall, and F1 at seven thresholds;
* the threshold with the best F1, and the counts behind it;
* mAP@0.5 and mAP@[.5:.95] (the latter is much stricter and usually much lower);
* per-class AP, because a mean can hide one class that never works.

Run:

    python lab6_detector_thresholds.py
    python lab6_detector_thresholds.py --selftest
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vision_core import datasets, dataio, detection, detection_train, models

OUTPUTS = Path(__file__).resolve().parent / "outputs"


def load_or_train(records, epochs: int):
    """Use Lab 5's checkpoint when available; otherwise train a small one."""
    # width must match Lab 5's checkpoint (24); a mismatch fails state_dict loading loudly
    model = models.TinyHeatmapDetector(num_classes=len(datasets.SHAPE_CLASSES), width=24, stride=4)
    checkpoint = OUTPUTS / "detector.pt"
    if checkpoint.exists():
        models.load_checkpoint(model, checkpoint)
        print(f"loaded detector from {checkpoint}")
        return model
    print("no checkpoint found; training a small detector")
    model, _ = detection_train.train_detector(records, num_classes=len(datasets.SHAPE_CLASSES), epochs=epochs, width=24, size_weight=0.5, seed=0, log=False)
    return model


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    records = dataio.detection_records()
    split = int(len(records) * 0.8)
    test_records = records[split:]
    model = load_or_train(records[:split], 4 if args.selftest else args.epochs)

    # Decode once at a permissive threshold, then sweep by filtering scores.
    results = detection.predict_records(model, test_records, score_threshold=0.02)
    report = detection.detector_report(results, datasets.SHAPE_CLASSES)

    print(f"\n=== threshold sweep ({len(test_records)} images, IoU 0.50)")
    print(detection.format_sweep(report["sweep"]))
    best = report["best_f1"]
    print(f"\nbest F1 {best['f1']:.3f} at threshold {best['threshold']:.2f} "
          f"(precision {best['precision']:.3f}, recall {best['recall']:.3f}, tp {best['tp']}, fp {best['fp']}, fn {best['fn']})")
    print(f"mAP@0.5        {report['map50']:.3f}")
    print(f"mAP@[.5:.95]   {report['map50_95']:.3f}")
    for name, ap in report["per_class_ap50"].items():
        print(f"  AP50 {name:<8} {ap:.3f}")

    print("\n=== what the sweep means")
    low = report["sweep"][0]
    high = report["sweep"][-1]
    print(f"at {low['threshold']:.2f}: recall {low['recall']:.3f}, precision {low['precision']:.3f} "
          f"({low['fp']} false positives)")
    print(f"at {high['threshold']:.2f}: recall {high['recall']:.3f}, precision {high['precision']:.3f} "
          f"({high['fn']} missed objects)")
    print("choosing between these is a product decision, not a metric one")

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    path = OUTPUTS / "lab6_thresholds.json"
    path.write_text(
        json.dumps(
            {
                "sweep": report["sweep"],
                "best_f1": best,
                "map50": report["map50"],
                "map50_95": report["map50_95"],
                "per_class_ap50": report["per_class_ap50"],
                "n_images": report["n_images"],
                "n_ground_truth": report["n_ground_truth"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\nreport: {path}")

    failures = 0
    if len(report["sweep"]) < 5:
        print("FAIL  expected at least five threshold rows")
        failures += 1
    if not (0.0 <= report["map50"] <= 1.0 and 0.0 <= report["map50_95"] <= 1.0):
        print("FAIL  mAP outside 0-1")
        failures += 1
    if report["map50_95"] > report["map50"] + 1e-9:
        print("FAIL  mAP@[.5:.95] cannot exceed mAP@0.5")
        failures += 1
    if not path.exists():
        print("FAIL  report not written")
        failures += 1

    print(f"\n{failures} failure(s)")
    if failures == 0:
        print("PASS  precision/recall trade-off measured across thresholds")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
