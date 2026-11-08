"""Lab A - Classify a small environmental-sound dataset.

Goal: take four synthesised environmental classes (alarm, rain, footsteps, birdsong),
train a small convolutional classifier on log-Mel features, and report accuracy in a
way that is honest about the split.

Three measurements matter more than the accuracy itself:

1. **Grouped vs per-clip splits.** Three variants of one alarm share its beep rate, so
   a random split lets the model recognise *that alarm* in the test set rather than
   recognising alarms. The lab trains both and prints both numbers.
2. **Which class the errors come from.** A single accuracy hides a class that is never
   detected; per-class recall does not.
3. **What happens outside the test set.** Noise, gain, and bandwidth changes are the
   conditions a deployed system actually meets.

Run:

    python lab_a_env_classifier.py             # full run (~20 s on CPU)
    python lab_a_env_classifier.py --selftest  # shorter budget, assertions only

Output: ``outputs/lab_a_env_classifier.json``
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lab_support as support
from speech_core import datasets, evaluate, metrics, models, training


def train(splits, epochs: int, seed: int = 0):
    """Train one classifier on log-Mel features and return it with its normalisation."""
    max_frames = max(training.mel_matrix(r).shape[0] for r in splits["train"] + splits["test"])
    x_train, _, _ = training.build_inputs(splits["train"], n_mels=40, max_frames=max_frames)
    x_val, _, _ = training.build_inputs(splits["val"], n_mels=40, max_frames=max_frames)
    mean, std = training.feature_stats(x_train)
    # Seed before construction: the initial weights are drawn from the global torch RNG,
    # and train_classifier seeds only after this line would have run.
    models.set_seed(seed)
    model = models.TinyAudioCNN(num_classes=len(datasets.ENV_CLASSES), width=16)
    history, model = training.train_classifier(
        model,
        training.normalize_inputs(x_train, mean, std),
        [r.label for r in splits["train"]],
        training.normalize_inputs(x_val, mean, std),
        [r.label for r in splits["val"]],
        epochs=epochs,
        batch_size=16,
        lr=2e-3,
        seed=seed,
        augment=True,
        log=False,
    )
    return model, mean, std, history, max_frames


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=14)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    records, origin = support.env_corpus()
    epochs = 6 if args.selftest else args.epochs

    support.rule("corpus")
    card = support.dataio.dataset_card()
    print(f"origin      : {origin}  ({support.dataio.DATA_ROOT})")
    print(f"clips       : {len(records)}  classes {len(datasets.ENV_CLASSES)} {list(datasets.ENV_CLASSES)}")
    print(f"sources     : {len({r.source_id for r in records})}")
    print(f"licence     : {card.get('licence')}")
    print(f"consent     : no human recordings; clips are generated from code")
    print(f"balance     : {datasets.class_balance(records, datasets.ENV_CLASSES)}")

    grouped = datasets.group_split(records, seed=0)
    naive = datasets.random_split(records, seed=0)
    a_grouped = datasets.audit_leakage(grouped)
    a_naive = datasets.audit_leakage(naive)

    support.rule("split audit")
    support.table(
        [
            {"split": "grouped by source", "shared_sources": a_grouped["n_shared_sources"], "leaky": a_grouped["leaky"]},
            {"split": "per clip (naive)", "shared_sources": a_naive["n_shared_sources"], "leaky": a_naive["leaky"]},
        ],
        ["split", "shared_sources", "leaky"],
    )
    print("decision is made on hard source overlap; the fingerprint count is a diagnostic.")

    support.rule(f"training ({epochs} epochs, grouped split)")
    model, mean, std, history, max_frames = train(grouped, epochs)
    print(history.ascii_plot(width=40, height=8))
    print(f"best epoch {history.best_epoch}, val accuracy {history.best_val_acc:.3f}, "
          f"train-validation gap {history.overfitting_gap:+.3f}")

    support.rule("test accuracy")
    report = evaluate.classifier_report(model, grouped["test"], datasets.ENV_CLASSES, mean=mean, std=std, max_frames=max_frames)
    print(f"accuracy {report['accuracy']:.3f} on {report['n']} held-out clips "
          f"(sources never seen in training)")
    rows = [{"class": name, **values} for name, values in report["per_class"].items()]
    support.table(rows, ["class", "precision", "recall", "f1", "support"])
    for confusion in report["confusions"]:
        print(f"  biggest confusion: {confusion['true']} -> {confusion['predicted']} x{confusion['count']}")

    support.rule("same model, leaky split (what not to report)")
    model_naive, mean_n, std_n, _, max_n = train(naive, epochs)
    naive_report = evaluate.classifier_report(model_naive, naive["test"], datasets.ENV_CLASSES, mean=mean_n, std=std_n, max_frames=max_n)
    print(f"grouped split : {report['accuracy']:.3f}")
    print(f"leaky split   : {naive_report['accuracy']:.3f}   ({naive_report['accuracy'] - report['accuracy']:+.3f})")
    print("The leaky number is not a better model, only a test set that repeats training sounds.")

    support.rule("robustness on the grouped test set")
    robust = evaluate.robustness_suite(model, grouped["test"], datasets.ENV_CLASSES, mean=mean, std=std)
    support.table(robust["rows"], ["condition", "accuracy", "drop_vs_clean", "mean_confidence"])
    print(f"worst condition: {robust['worst']['condition']} (accuracy {robust['worst']['accuracy']:.3f})")

    payload = {
        "lab": "A",
        "title": "environmental sound classification",
        "corpus": {"origin": origin, "clips": len(records), "classes": list(datasets.ENV_CLASSES), "sources": len({r.source_id for r in records})},
        "splits": {k: len(v) for k, v in grouped.items()},
        "audit": {"grouped": a_grouped, "naive": a_naive},
        "history": history.to_dict(),
        "test": {"accuracy": report["accuracy"], "per_class": report["per_class"], "confusions": report["confusions"]},
        "leaky_split_accuracy": naive_report["accuracy"],
        "robustness": robust,
        "model": models.summarize_model(model),
        "checks": {},
    }

    failures = 0
    checks = {
        "grouped split has no shared source": a_grouped["n_shared_sources"] == 0,
        "naive split does share sources": a_naive["n_shared_sources"] > 0,
        "accuracy in [0, 1]": 0.0 <= report["accuracy"] <= 1.0,
        "clean condition equals test accuracy": abs(robust["rows"][0]["accuracy"] - report["accuracy"]) < 1e-9,
        "noise at 5 dB is not better than clean": robust["rows"][3]["accuracy"] <= robust["rows"][0]["accuracy"] + 1e-9,
    }
    if not args.selftest:
        checks["grouped accuracy beats chance"] = report["accuracy"] > 1.0 / len(datasets.ENV_CLASSES)
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}  {name}")
        failures += 0 if passed else 1
    payload["checks"] = checks

    path = support.write_report("lab_a_env_classifier.json", payload)
    print(f"\nreport written to {path.relative_to(support.HERE)}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
