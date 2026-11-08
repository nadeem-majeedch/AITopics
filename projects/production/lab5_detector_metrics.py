"""Lab 5 - object-detector evaluation: IoU, matching, AP, and mAP.

The data is synthetic (40 images, three classes, generated boxes) and the detector
output is stored, so the metrics are the only thing under test. That is the point:
metric implementations are code, and code has bugs.

The lab reports:

* per-class AP at IoU 0.5, with the ground-truth and prediction counts that make
  the number interpretable;
* mAP, defined here as the mean of per-class AP (state the definition, because
  mAP has several);
* the sensitivity of mAP to the IoU threshold;
* precision and recall at one operating confidence, plus a sweep, because a
  detector is deployed at a threshold and AP is threshold-free.

One hand-checked example is in the selftest. If an AP implementation disagrees
with an example you can compute on paper, it is wrong, however plausible the
number looks.

    python lab5_detector_metrics.py
    python lab5_detector_metrics.py --selftest
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_core import (  # noqa: E402
    Checks,
    Report,
    average_precision,
    base_parser,
    class_balance,
    data,
    environment_snapshot,
    iou,
    match_image,
    mean_ap,
    measured_footer,
    precision_recall_at,
    threshold_sweep,
    write_json,
)

OUT_DIR = data.ROOT / "outputs" / "production" / "lab5"
CLASSES = ("person", "bike", "sign")
IOU_THRESHOLD = 0.5
CONFIDENCE = 0.5


def run() -> dict:
    data.ensure_data()
    gt = data.load_json(data.DATA / "detector" / "gt.json")
    preds = data.load_json(data.DATA / "detector" / "preds.json")

    at_half = mean_ap(gt, preds, CLASSES, iou_threshold=0.5)
    by_iou = [
        {"iou": threshold, **{"mAP": mean_ap(gt, preds, CLASSES, iou_threshold=threshold)["mAP"]}}
        for threshold in (0.3, 0.5, 0.7)
    ]
    operating = precision_recall_at(gt, preds, CLASSES, IOU_THRESHOLD, CONFIDENCE)
    sweep = threshold_sweep(gt, preds, CLASSES, IOU_THRESHOLD)

    return {
        "images": len(gt),
        "classes": CLASSES,
        "class_counts": class_balance(gt, CLASSES),
        "per_class": at_half["per_class"],
        "mAP": at_half["mAP"],
        "by_iou": by_iou,
        "operating_point": operating,
        "sweep": sweep,
        "total_predictions": sum(len(image["detections"]) for image in preds),
        "environment": environment_snapshot(),
    }


def build_report(result: dict) -> Report:
    report = Report(
        "Lab 5 - evaluating an object detector",
        f"{result['images']} synthetic images, {result['total_predictions']} predictions, "
        f"{sum(result['class_counts'].values())} ground-truth boxes.",
    )
    report.heading("Definition used")
    report.text(
        "AP is computed per class with greedy one-to-one matching at IoU >= 0.5, ranked by confidence, "
        "using all-point interpolation. mAP is the unweighted mean of the three per-class AP values. "
        "A detection with the wrong class is a false positive, even if its box is perfect."
    )

    report.heading("Per-class AP at IoU 0.5")
    report.table(
        [
            {"class": row["class"], "ground truth": row["ground_truth"], "predictions": row["predictions"],
             "AP@0.5": row["ap"]}
            for row in result["per_class"]
        ],
        ["class", "ground truth", "predictions", "AP@0.5"],
    )
    report.text(f"mAP@0.5 = **{result['mAP']:.3f}**")

    report.heading("Sensitivity to the IoU threshold")
    report.table(result["by_iou"], ["iou", "mAP"])

    operating = result["operating_point"]
    report.heading(f"Operating point at confidence {operating['score_threshold']}")
    report.table(
        [{"tp": operating["tp"], "fp": operating["fp"], "fn": operating["fn"],
          "precision": operating["precision"], "recall": operating["recall"], "f1": operating["f1"]}],
        ["tp", "fp", "fn", "precision", "recall", "f1"],
    )
    report.text(
        "AP says how well the ranking separates objects from background across all thresholds. "
        "This table says what happens at the threshold you would actually deploy. A system can have a "
        "respectable AP and a poor operating point if its scores are badly calibrated."
    )

    report.heading("Threshold sweep")
    report.table(
        [{"confidence": row["score_threshold"], "precision": row["precision"],
          "recall": row["recall"], "f1": row["f1"]} for row in result["sweep"]],
        ["confidence", "precision", "recall", "f1"],
    )

    report.heading("Limits of this measurement")
    report.bullets([
        "The boxes are synthetic and well separated. None of the hard cases matter here: occlusion, "
        "crowds, boxes at the image edge, and class ambiguity.",
        "40 images is far too few for a stable mAP. Report the interval, or report counts, not just the mean.",
        "AP@0.5 is not comparable to mAP@[.5:.95]. Papers mix the two; say which one you computed.",
    ])
    return report


def selftest() -> int:
    checks = Checks("lab 5 - detector metrics")

    # Hand-checked AP: 2 boxes, predictions at 0.9 (tp), 0.8 (fp), 0.4 (tp).
    # Recall/precision pairs: (0.5, 1.0), (0.5, 0.5), (1.0, 2/3). The precision
    # envelope from the right is (1.0, 2/3, 2/3), so
    # AP = 0.5*1.0 + 0*2/3 + 0.5*2/3 = 5/6. Writing this out is the point: an AP
    # implementation that "looks plausible" is worth nothing until it reproduces
    # an example this small.
    gt_small = [{"image_id": "i1", "boxes": [
        {"class": "person", "box": [0.0, 0.0, 0.2, 0.2]},
        {"class": "person", "box": [0.5, 0.5, 0.7, 0.7]},
    ]}]
    pred_small = [{"image_id": "i1", "detections": [
        {"class": "person", "box": [0.0, 0.0, 0.2, 0.2], "score": 0.9},
        {"class": "person", "box": [0.8, 0.8, 0.9, 0.9], "score": 0.8},
        {"class": "person", "box": [0.5, 0.5, 0.7, 0.7], "score": 0.4},
    ]}]
    small_ap = average_precision(gt_small, pred_small, "person", 0.5)["ap"]
    checks.close("AP matches the hand-computed value", small_ap, 5 / 6, 1e-9)

    checks.close("IoU of identical boxes is 1", iou([0, 0, 1, 1], [0, 0, 1, 1]), 1.0, 1e-9)
    checks.close("IoU of disjoint boxes is 0", iou([0, 0, 1, 1], [2, 2, 3, 3]), 0.0, 1e-9)

    matched = match_image(gt_small[0]["boxes"], pred_small[0]["detections"], 0.5)
    checks.equal("one true positive per ground-truth box", matched["tp"], 2)
    checks.equal("the duplicate prediction is a false positive", matched["fp"], 1)
    checks.equal("no ground truth left unmatched", matched["fn"], 0)

    wrong_class = [{"image_id": "i1", "detections": [
        {"class": "bike", "box": [0.0, 0.0, 0.2, 0.2], "score": 0.9},
    ]}]
    checks.equal("a perfect box with the wrong class scores zero",
                 average_precision(gt_small, wrong_class, "person", 0.5)["ap"], 0.0)

    result = run()
    checks.check("mAP is a plausible fraction", 0.3 < result["mAP"] < 0.95, f"{result['mAP']:.3f}")
    checks.check("per-class AP is ordered like the synthetic detector",
                 result["per_class"][0]["ap"] > result["per_class"][2]["ap"],
                 f"person {result['per_class'][0]['ap']:.3f} vs sign {result['per_class'][2]['ap']:.3f}")
    checks.check("stricter IoU never raises mAP",
                 result["by_iou"][0]["mAP"] >= result["by_iou"][1]["mAP"] >= result["by_iou"][2]["mAP"],
                 str([round(row["mAP"], 3) for row in result["by_iou"]]))
    checks.check("operating point is a valid ratio",
                 0.0 <= result["operating_point"]["precision"] <= 1.0
                 and 0.0 <= result["operating_point"]["recall"] <= 1.0)
    checks.check("threshold sweep is monotone in recall",
                 all(left["recall"] >= right["recall"]
                     for left, right in zip(result["sweep"], result["sweep"][1:])),
                 str([round(row["recall"], 3) for row in result["sweep"]]))

    report = build_report(result)
    path = report.write(OUT_DIR, "report.md", measured_footer(result["environment"]))
    write_json(OUT_DIR, "metrics.json", result)
    checks.check("report written", path.exists() and path.stat().st_size > 1000)
    return checks.report()


def main() -> int:
    parser = base_parser(__doc__ or "")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    result = run()
    print(build_report(result).render(measured_footer(result["environment"])))
    write_json(OUT_DIR, "metrics.json", result)
    print(f"\nwritten: {OUT_DIR / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
