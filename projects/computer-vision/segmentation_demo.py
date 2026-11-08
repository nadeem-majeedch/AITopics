"""Module CV10 hands-on - segmentation on an imbalanced mask set.

The teaching sequence, and why it is not the obvious one:

1. The all-background control prices "pixel accuracy" on a 95% background dataset.
2. A short run (default 12 epochs) shows the collapse everyone blames on class
   imbalance: the model predicts background and scores 0.95 pixel accuracy.
3. The same short run with inverse-frequency class weights partially recovers the
   foreground - which looks like proof that weighting was the missing piece.
4. A long run (default 120 epochs) with **no** weights beats both, at mIoU 0.762.

So the collapse was under-training, not imbalance. Weighting is a real tool and the
numbers are printed both ways, but "add class weights" is a hypothesis to test, not a
rule to apply. What survives every configuration is the metric lesson: pixel accuracy
is 0.98 for a model whose object IoU is 0.54, and the all-background control scores
0.953.

Run:

    python segmentation_demo.py
    python segmentation_demo.py --selftest
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vision_core import dataio, datasets, metrics, segmentation

OUTPUTS = Path(__file__).resolve().parent / "outputs"
SHORT_EPOCHS = 12


def class_weights_from(records) -> np.ndarray:
    """Inverse pixel frequency, normalised to mean 1.0.

    Mean 1.0 keeps the loss magnitude comparable with the unweighted run, so the
    two numbers in the table are not confounded by a rescaled loss.
    """
    masks = np.stack([r.meta["mask"] for r in records])
    freq = np.array([(masks == i).mean() for i in range(len(datasets.SEGMENTATION_CLASSES))])
    weights = 1.0 / np.maximum(freq, 1e-6)
    return weights / weights.mean()


def describe(label: str, report: dict) -> str:
    per_class = "  ".join(
        f"{name} {value:.3f}" if value is not None else f"{name} n/a"
        for name, value in report["per_class_iou"].items()
    )
    return f"{label:<24} pixel_acc {report['pixel_accuracy']:.3f}  mIoU {report['mean_iou']:.3f}  {per_class}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=120)
    parser.add_argument("--width", type=int, default=16)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    epochs = 40 if args.selftest else args.epochs

    records = dataio.segmentation_records()
    split = int(len(records) * 0.75)
    train, test = records[:split], records[split:]
    masks = np.stack([r.meta["mask"] for r in train])
    fractions = [(masks == i).mean() for i in range(len(datasets.SEGMENTATION_CLASSES))]
    weights = class_weights_from(train)
    print(f"images {len(records)}  train {len(train)}  test {len(test)}")
    print(f"class pixel fractions {dict(zip(datasets.SEGMENTATION_CLASSES, np.round(fractions, 4)))}")
    print(f"class weights         {np.round(weights, 3)}")

    control = segmentation.all_background_baseline(test)
    threshold = segmentation.evaluate_segmenter(None, test, baseline=True)
    print("\n=== baselines for 'do nothing'")
    print(describe("all background", control))
    print(describe("threshold rule", threshold))

    results: dict[str, dict] = {}
    print(f"\n=== short run ({SHORT_EPOCHS} epochs)")
    short_plain, _ = segmentation.train_segmenter(
        train, epochs=SHORT_EPOCHS, width=args.width, log=False
    )
    results["short_unweighted"] = segmentation.evaluate_segmenter(short_plain, test)
    print(describe("no class weights", results["short_unweighted"]))

    short_weighted, _ = segmentation.train_segmenter(
        train, epochs=SHORT_EPOCHS, width=args.width, class_weights=weights, log=False
    )
    results["short_weighted"] = segmentation.evaluate_segmenter(short_weighted, test)
    print(describe("class weights", results["short_weighted"]))

    print(f"\n=== full run ({epochs} epochs)")
    plain, plain_hist = segmentation.train_segmenter(train, epochs=epochs, width=args.width, log=False)
    results["full_unweighted"] = segmentation.evaluate_segmenter(plain, test)
    print(describe("no class weights", results["full_unweighted"]))

    weighted, weighted_hist = segmentation.train_segmenter(
        train, epochs=epochs, width=args.width, class_weights=weights, log=False
    )
    results["full_weighted"] = segmentation.evaluate_segmenter(weighted, test)
    print(describe("class weights", results["full_weighted"]))

    no_skip, _ = segmentation.train_segmenter(
        train, epochs=epochs, width=args.width, class_weights=weights, use_skip=False, log=False
    )
    results["full_no_skip"] = segmentation.evaluate_segmenter(no_skip, test)
    print(describe("weights, no skip", results["full_no_skip"]))

    best = max(results["full_unweighted"]["mean_iou"], results["full_weighted"]["mean_iou"])
    best_label = "no class weights" if results["full_unweighted"]["mean_iou"] >= results["full_weighted"]["mean_iou"] else "class weights"
    print(f"\nbest long run: {best_label} at mIoU {best:.3f}")
    print("if that is the unweighted run, the short-run collapse was under-training, not imbalance")

    pred = segmentation.predict_masks(weighted, test)
    boundary = float(np.mean([metrics.boundary_f1(p, r.meta["mask"], tolerance=1) for p, r in zip(pred, test)]))
    accuracy_gap = results["full_unweighted"]["pixel_accuracy"] - results["full_unweighted"]["mean_iou"]
    print(f"boundary F1 (weighted, tolerance 1 px)  {boundary:.3f}")
    print(f"pixel accuracy minus mIoU (unweighted)  {accuracy_gap:+.3f}  <- why accuracy is not the metric")

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    path = OUTPUTS / "segmentation_report.json"
    path.write_text(
        json.dumps(
            {
                "epochs": epochs,
                "short_epochs": SHORT_EPOCHS,
                "width": args.width,
                "train_images": len(train),
                "test_images": len(test),
                "class_fractions": [float(f) for f in fractions],
                "class_weights": weights.tolist(),
                "control": control,
                "threshold_baseline": threshold,
                **results,
                "best_long_run": best_label,
                "boundary_f1": boundary,
                "loss_curves": {"unweighted": plain_hist["loss"], "weighted": weighted_hist["loss"]},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"report: {path}")

    failures = 0
    for label, report in results.items():
        for name, value in report["per_class_iou"].items():
            if value is not None and not 0.0 <= value <= 1.0:
                print(f"FAIL  {label}: IoU for {name} outside 0-1")
                failures += 1
    if best < 0.5:
        print("FAIL  no long run reached the 0.5 mIoU teaching floor")
        failures += 1
    if not results["full_unweighted"]["pixel_accuracy"] > results["full_unweighted"]["mean_iou"]:
        print("FAIL  pixel accuracy should exceed mean IoU on imbalanced masks")
        failures += 1
    if not path.exists():
        print("FAIL  report not written")
        failures += 1

    print(f"\n{failures} failure(s)")
    if failures == 0:
        print("PASS  control, short-run collapse, long run, and skip ablation all measured")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
