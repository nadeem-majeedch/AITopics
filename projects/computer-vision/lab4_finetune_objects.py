"""Lab 4 - Fine-tune a pretrained model to recognise everyday objects.

The task: four coarse object classes (mug, bottle, book, phone). The starting
point is the offline backbone from Lab 3, or a freshly built one if it is absent.

Deliverables written to ``outputs/``:

* ``lab4_objects.pt`` - the fine-tuned model;
* ``lab4_model_card.md`` - a model card with measured numbers filled in.

The card is checked for unfilled placeholders: a card that still says
``{{limitations}}`` has not been written and fails the selftest.

Run:

    python lab4_finetune_objects.py
    python lab4_finetune_objects.py --selftest
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vision_core import cards, datasets, dataio, evaluation, models, training, transfer
from vision_core.metrics import classification_report

OUTPUTS = Path(__file__).resolve().parent / "outputs"


def get_backbone(epochs: int):
    """Reuse the saved backbone when present so labs compose; otherwise build it."""
    checkpoint = OUTPUTS / "pretrained_backbone.pt"
    model = models.TinyCNN(num_classes=len(datasets.SHAPE_CLASSES), width=16)
    if checkpoint.exists():
        models.load_checkpoint(model, checkpoint)
        print(f"loaded backbone from {checkpoint}")
        return model
    shapes = dataio.classification_splits()
    print("no checkpoint found; building the backbone now")
    backbone, _ = transfer.build_pretrained_backbone(
        shapes["train"]["images"], shapes["train"]["labels"], len(datasets.SHAPE_CLASSES), epochs=epochs, out_path=checkpoint, log=False
    )
    return backbone


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    epochs = 4 if args.selftest else args.epochs

    objects = dataio.object_splits()
    backbone = get_backbone(epochs)
    print(f"train {len(objects['train']['labels'])}  val {len(objects['val']['labels'])}  test {len(objects['test']['labels'])}")

    model, history = transfer.train_partial_finetune(
        backbone,
        objects["train"]["images"],
        objects["train"]["labels"],
        objects["val"]["images"],
        objects["val"]["labels"],
        num_classes=len(datasets.OBJECT_CLASSES),
        epochs=epochs,
        seed=0,
    )
    print("\n=== validation accuracy")
    print(history.ascii_plot("val_acc"))

    mean, std = transfer.dataset_stats(objects["train"]["images"])
    predicted, probs = training.predict(model, objects["test"]["images"], mean, std)
    report = classification_report(list(objects["test"]["labels"]), list(predicted), datasets.OBJECT_CLASSES)
    robustness = evaluation.robustness_suite(model, objects["test"]["images"], list(objects["test"]["labels"]), mean, std)

    print(f"\ntest accuracy {report['accuracy']:.3f}  macro F1 {report['macro_f1']:.3f}")
    for name, stats in report["per_class"].items():
        print(f"  {name:<8} precision {stats['precision']:.2f} recall {stats['recall']:.2f} support {stats['support']}")
    print("\n=== robustness")
    print(evaluation.format_robustness(robustness))

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    checkpoint = models.save_checkpoint(
        model,
        OUTPUTS / "lab4_objects.pt",
        {"classes": list(datasets.OBJECT_CLASSES), "test_accuracy": report["accuracy"], "history": history.to_dict()},
    )
    card_path = cards.write_model_card(
        OUTPUTS / "lab4_model_card.md",
        model_name="Objects-4 fine-tuned classifier",
        version="1.0.0",
        date="2026-11-01",
        author="student",
        task="4-class image classification of coarse everyday-object icons",
        architecture="TinyCNN (3 conv blocks, global average pooling, linear head)",
        parameters=models.count_parameters(model, trainable_only=False),
        input_spec="32x32 RGB, normalized per channel",
        output_spec="4 class scores (mug, bottle, book, phone)",
        licence="CC0-1.0 (course code); synthetic data, no third-party images",
        intended_use="Course exercise only: demonstrating partial fine-tuning on a CPU.",
        out_of_scope="Not for real product recognition. The classes are drawings, not photographs.",
        training_data="AITopics synthetic object set: 72 images from 24 sources, source-level split.",
        metrics_table=[
            {"name": "test accuracy", "value": f"{report['accuracy']:.3f}", "dataset": "objects test (n=9)", "note": "small set; ±1 image = 0.11"},
            {"name": "macro F1", "value": f"{report['macro_f1']:.3f}", "dataset": "objects test", "note": ""},
            {"name": "robustness (worst)", "value": f"{robustness['worst_accuracy']:.3f}", "dataset": "objects test", "note": robustness["worst_condition"]},
        ],
        failure_modes=(
            "Confuses the two vertically elongated silhouettes (bottle, phone) when the shadow gradient is strong; "
            "accuracy drops under occlusion because the object occupies a small part of the frame."
        ),
        robustness=evaluation.format_robustness(robustness),
        safety="No personal data. No faces. Synthetic images only.",
        limitations=(
            "Trained on 72 synthetic icons. Expect near-random performance on photographs. "
            "The 'pretrained' trunk is a small synthetic backbone, not ImageNet; the fine-tuning benefit "
            "measured here is smaller than it would be with real pretrained weights."
        ),
        reproduce_command="python lab4_finetune_objects.py",
        review="Self-reviewed against the section rubric; metrics regenerated on every run.",
    )
    check = cards.check_card(card_path)
    print(f"\nmodel: {checkpoint}")
    print(f"card: {card_path}  complete={check['complete']}  missing={check['missing']}")

    failures = 0
    if not check["complete"]:
        print(f"FAIL  model card has unfilled fields: {check['missing']}")
        failures += 1
    if not 0.0 <= report["accuracy"] <= 1.0:
        print("FAIL  accuracy outside 0-1")
        failures += 1
    if not checkpoint.exists():
        print("FAIL  checkpoint not written")
        failures += 1

    print(f"\n{failures} failure(s)")
    if failures == 0:
        print("PASS  fine-tuned model saved and documented with measured metrics")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
