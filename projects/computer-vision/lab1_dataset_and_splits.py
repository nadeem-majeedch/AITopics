"""Lab 1 - Build an image classifier dataset and split it without leakage.

What this lab demonstrates with numbers rather than advice:

* the dataset's licence and provenance, printed from its card;
* the difference between splitting images and splitting *sources*;
* how much accuracy a leaky split invents.

Run:

    python lab1_dataset_and_splits.py            # full run
    python lab1_dataset_and_splits.py --selftest # assertions for CI
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vision_core import datasets, dataio, imaging, models, training


def train_and_score(splits: dict, epochs: int, seed: int = 0) -> float:
    """Train the same model on a split and return test accuracy."""
    model = models.TinyCNN(num_classes=len(datasets.SHAPE_CLASSES), width=16)
    training.train_classifier(
        model,
        splits["train"]["images"],
        splits["train"]["labels"],
        splits["val"]["images"],
        splits["val"]["labels"],
        epochs=epochs,
        batch_size=16,
        lr=2e-3,
        seed=seed,
        log=False,
    )
    mean, std = training.dataset_stats(splits["train"]["images"])
    predicted, _ = training.predict(model, splits["test"]["images"], mean, std)
    return float(np.mean(predicted == splits["test"]["labels"]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    card = dataio.dataset_card()
    summary = dataio.summary()
    print("=== dataset card")
    print(f"name      : {card.get('name')}")
    print(f"licence   : {card.get('licence')}")
    print(f"source    : {card.get('source')}")
    print(f"personal  : {card.get('contains_personal_data')}")
    print(f"on disk   : {summary['exists_on_disk']}  ({summary['data_root']})")
    print(f"splits    : {summary['classification']}")

    records = dataio.classification_records()
    grouped = datasets.group_split(records, seed=0)
    naive = datasets.random_split(records, seed=0)
    audit_grouped = datasets.audit_leakage(grouped)
    audit_naive = datasets.audit_leakage(naive)

    print("\n=== leakage audit")
    print(f"grouped by source : shared sources {audit_grouped['n_shared_sources']}, "
          f"cross-split look-alikes {audit_grouped['cross_split_near_duplicate_count']}")
    print(f"random per image  : shared sources {audit_naive['n_shared_sources']}, "
          f"cross-split look-alikes {audit_naive['cross_split_near_duplicate_count']}")

    splits = dataio.classification_splits()
    epochs = 5 if args.selftest else args.epochs
    honest = train_and_score(splits, epochs)
    leaky = train_and_score({key: _as_arrays(part) for key, part in naive.items()}, epochs)

    print("\n=== test accuracy after the same training budget")
    print(f"grouped split : {honest:.3f}   (this is the number you may report)")
    print(f"leaky split   : {leaky:.3f}   (inflated: test images have near-copies in train)")
    print(f"inflation     : {leaky - honest:+.3f}")

    failures = 0
    if audit_grouped["n_shared_sources"] != 0:
        print("FAIL  grouped split shares a source across splits")
        failures += 1
    if audit_naive["n_shared_sources"] == 0:
        print("FAIL  the naive split should share sources; the audit found none")
        failures += 1
    if not (0.0 <= honest <= 1.0 and 0.0 <= leaky <= 1.0):
        print("FAIL  accuracy outside 0-1")
        failures += 1

    print(f"\n{len(records)} images from {len({r.source_id for r in records})} sources; {failures} failure(s)")
    if failures == 0:
        print("PASS  source-level grouping removes the hard leak in this dataset")
    return 0 if failures == 0 else 1


def _as_arrays(records) -> dict:
    return {
        "images": np.stack([r.image for r in records]),
        "labels": np.array([r.label for r in records], dtype=np.int64),
    }


if __name__ == "__main__":
    raise SystemExit(main())
