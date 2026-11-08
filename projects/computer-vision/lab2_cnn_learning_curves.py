"""Lab 2 - Train a CNN from scratch and read its learning curves.

The deliverable is not "a model". It is a *history*: per-epoch train and
validation loss and accuracy, an ASCII chart in the terminal, and a PNG for the
report. From the curves you decide whether the model is underfitting (both losses
high), overfitting (train falls, validation rises), or fitted.

Run:

    python lab2_cnn_learning_curves.py
    python lab2_cnn_learning_curves.py --selftest
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vision_core import datasets, dataio, models, training
from vision_core.imaging import AugmentConfig, augment

OUTPUTS = Path(__file__).resolve().parent / "outputs"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--no-augment", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    epochs = 6 if args.selftest else args.epochs
    splits = dataio.classification_splits()
    train_split, val_split = splits["train"], splits["val"]

    print(f"train {len(train_split['labels'])}  val {len(val_split['labels'])}  test {len(splits['test']['labels'])}")
    print(f"model: TinyCNN width 16, params {models.count_parameters(models.TinyCNN(num_classes=3))}")

    config = AugmentConfig(hflip_p=0.5, rotate_deg=8, max_shift=2, brightness=0.15, noise_std=0.02)
    augment_fn = None if args.no_augment else (lambda img, rng: augment(img, config, rng))

    # Seed before the layers are initialised. Training reseeds the shuffle, but a
    # seed applied after construction leaves the initial weights random, so two
    # runs of the same command report different curves.
    models.set_seed(0)
    model = models.TinyCNN(num_classes=len(datasets.SHAPE_CLASSES), width=16)
    history, model = training.train_classifier(
        model,
        train_split["images"],
        train_split["labels"],
        val_split["images"],
        val_split["labels"],
        epochs=epochs,
        batch_size=16,
        lr=2e-3,
        seed=0,
        augment_fn=augment_fn,
    )

    print("\n=== val accuracy curve")
    print(history.ascii_plot("val_acc"))
    print("\n=== train vs val loss")
    print(history.ascii_plot("val_loss"))

    mean, std = training.dataset_stats(train_split["images"])
    predicted, _ = training.predict(model, splits["test"]["images"], mean, std)
    test_accuracy = float(np.mean(predicted == splits["test"]["labels"]))

    print(f"\nbest epoch {history.best_epoch}  best val_acc {history.best_val_acc:.3f}")
    print(f"test accuracy {test_accuracy:.3f}  overfitting gap {history.overfitting_gap():+.3f}")
    print(f"total training time {sum(history.epoch_seconds):.1f}s")

    png = history.plot_png(OUTPUTS / "lab2_learning_curves.png", title="Lab 2: TinyCNN on synthetic shapes")
    metrics_path = OUTPUTS / "lab2_history.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps({**history.to_dict(), "test_accuracy": test_accuracy, "augmented": not args.no_augment}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"figure: {png}")
    print(f"history: {metrics_path}")

    failures = 0
    if history.epochs < 1:
        print("FAIL  no epochs recorded")
        failures += 1
    if not png.exists() or png.stat().st_size < 1000:
        print("FAIL  figure was not written")
        failures += 1
    if not (0.0 <= test_accuracy <= 1.0):
        print("FAIL  test accuracy outside 0-1")
        failures += 1
    if args.selftest and history.best_val_acc < 0.5:
        print(f"FAIL  val accuracy {history.best_val_acc:.3f} below the 0.50 floor for 6 epochs")
        failures += 1

    print(f"\n{failures} failure(s)")
    if failures == 0:
        print("PASS  training ran, curves recorded, model evaluated")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
