"""Lab 8 - Compare inference latency and model size across deployment configurations.

Measured, not estimated:

* float32 baseline vs dynamic int8 quantization (and what quantization actually
  converts in a convolutional model);
* thread count (1, 2, 4, 8) - the same model is 3-6x slower single-threaded;
* batch size - per-item cost falls, per-call cost rises;
* input size - pixels are quadratic.

Every row prints median and p90 latency, because a laptop's tail is what users
feel.

Run:

    python lab8_deployment.py
    python lab8_deployment.py --selftest
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vision_core import datasets, dataio, models, optimize, training

OUTPUTS = Path(__file__).resolve().parent / "outputs"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    runs = max(5, args.runs // 2) if args.selftest else args.runs

    splits = dataio.classification_splits()
    train_split = splits["train"]

    print("training a small classifier to benchmark (2 epochs)")
    model = models.TinyCNN(num_classes=len(datasets.SHAPE_CLASSES), width=16)
    _, model = training.train_classifier(
        model,
        train_split["images"][:64],
        train_split["labels"][:64],
        train_split["images"][:32],
        train_split["labels"][:32],
        epochs=2,
        seed=0,
        log=False,
    )
    mean, std = training.dataset_stats(train_split["images"])
    sample_raw = splits["test"]["images"][:1]
    sample = training.prepare_inputs(sample_raw, mean, std)

    info = models.summarize_model(model)
    print(f"model {info['class']}  params {info['parameters_total']}  size {info['size_mb']:.4f} MB  int8 estimate {info['estimated_int8_mb']:.4f} MB")
    print(f"threads available {torch.get_num_threads()}")

    report = optimize.deployment_report(model, sample, runs=runs)

    print("\n=== float32 vs dynamic int8")
    print(optimize.format_table([report["baseline"], report["quantized"]], ["label", "median_ms", "p90_ms", "size_mb"]))
    print(f"speedup {report['quantization_speedup']:.2f}x  size change {report['size_change_mb']:+.4f} MB  "
          f"top-1 agreement {report['top1_agreement']:.3f}")
    print("note: dynamic quantization only converts Linear layers; convolutions stay float")

    print("\n=== threads")
    print(optimize.format_table(report["threads"], ["threads", "median_ms", "p90_ms"]))

    print("\n=== batch size (per-item cost is what matters)")
    print(optimize.format_table(report["batch"], ["batch_size", "median_ms", "per_item_ms"]))

    print("\n=== input size")
    print(optimize.format_table(report["input_size"], ["input_size", "median_ms"]))

    single = next(r for r in report["threads"] if r["threads"] == 1)
    many = max(report["threads"], key=lambda r: r["threads"])
    print(f"\nsingle-thread {single['median_ms']:.2f} ms vs {many['threads']}-thread {many['median_ms']:.2f} ms "
          f"({single['median_ms'] / max(1e-9, many['median_ms']):.1f}x)")

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    path = OUTPUTS / "lab8_deployment.json"
    path.write_text(json.dumps({"model": info, **report}, indent=2) + "\n", encoding="utf-8")
    print(f"\nreport: {path}")

    failures = 0
    if report["baseline"]["median_ms"] <= 0:
        print("FAIL  baseline latency must be positive")
        failures += 1
    if report["baseline"]["size_mb"] <= 0:
        print("FAIL  model size must be positive")
        failures += 1
    batch_rows = report["batch"]
    if len(batch_rows) > 1 and batch_rows[-1]["per_item_ms"] > batch_rows[0]["per_item_ms"]:
        print("FAIL  per-item cost should fall as batch size grows")
        failures += 1
    if not 0.0 <= report["top1_agreement"] <= 1.0:
        print("FAIL  agreement outside 0-1")
        failures += 1
    if not path.exists():
        print("FAIL  report not written")
        failures += 1

    print(f"\n{failures} failure(s)")
    if failures == 0:
        print("PASS  latency, size, threads, batch, and input size all measured")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
