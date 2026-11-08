"""Lab 3 - Compare training from scratch with transfer learning.

Three conditions, identical data and budget:

1. from scratch - random weights, all parameters trained;
2. frozen features - pretrained trunk frozen, only a linear head trained;
3. partial fine-tune - last block unfrozen, lower learning rate.

The comparison reports accuracy *and* trainable parameter count *and* time,
because the interesting result is usually the ratio between them.

**Honesty note, printed by the script itself:** the "pretrained" trunk here was
trained on the section's small synthetic set, not on ImageNet. The mechanism is
the same; the size of the benefit is not transferable to real photographs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vision_core import datasets, dataio, models, transfer

OUTPUTS = Path(__file__).resolve().parent / "outputs"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    epochs = 6 if args.selftest else args.epochs
    shapes = dataio.classification_splits()
    objects = dataio.object_splits()

    print("=== stage 1: build the offline backbone (3 shape classes)")
    backbone, backbone_history = transfer.build_pretrained_backbone(
        shapes["train"]["images"],
        shapes["train"]["labels"],
        num_classes=len(datasets.SHAPE_CLASSES),
        width=16,
        epochs=epochs,
        seed=0,
        out_path=OUTPUTS / "pretrained_backbone.pt",
        log=False,
    )
    print(f"backbone val_acc {backbone_history.best_val_acc:.3f}  feature_dim {backbone.feature_dim}")
    print("note: this trunk is trained on synthetic shapes, NOT ImageNet")

    print("\n=== stage 2: three conditions on the everyday-object task (4 classes)")
    results = transfer.compare_scratch_vs_transfer(
        backbone,
        objects["train"]["images"],
        objects["train"]["labels"],
        objects["val"]["images"],
        objects["val"]["labels"],
        objects["test"]["images"],
        objects["test"]["labels"],
        num_classes=len(datasets.OBJECT_CLASSES),
        seed=0,
        epochs=epochs,
        log=False,
    )

    print(f"\n{'condition':<32} {'test_acc':>9} {'trainable':>10} {'seconds':>8}")
    print("-" * 63)
    for r in results:
        print(f"{r.name:<32} {r.test_accuracy:>9.3f} {r.n_trainable_parameters:>10d} {r.seconds:>8.1f}")

    best = max(results, key=lambda r: r.test_accuracy)
    print(f"\nbest condition: {best.name} ({best.test_accuracy:.3f})")

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    path = OUTPUTS / "lab3_transfer_comparison.json"
    path.write_text(
        json.dumps(
            {
                "backbone": {"val_acc": backbone_history.best_val_acc, "epochs": backbone_history.epochs, "honest_note": "synthetic pretraining"},
                "conditions": [r.as_dict() for r in results],
                "best": best.name,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"results: {path}")

    failures = 0
    if len(results) != 3:
        print("FAIL  expected three conditions")
        failures += 1
    for r in results:
        if not 0.0 <= r.test_accuracy <= 1.0:
            print(f"FAIL  {r.name}: accuracy outside 0-1")
            failures += 1
    scratch = next(r for r in results if r.name == "scratch")
    probe = next(r for r in results if "linear" in r.name)
    if probe.n_trainable_parameters >= scratch.n_trainable_parameters:
        print("FAIL  the linear probe should train far fewer parameters than scratch")
        failures += 1

    print(f"\n{failures} failure(s)")
    if failures == 0:
        print("PASS  three conditions measured with differing parameter budgets")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
