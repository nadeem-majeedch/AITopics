"""Lab 6 - Action recognition: a single frame versus a sequence.

Goal: train two models on the same clips and show, with numbers, why video models exist.

* The **frame baseline** sees one 64x64 frame at a time and predicts the action. It is what
  most quick "video AI" demos actually are.
* The **temporal model** sees the whole 8-frame clip: the same 2-D CNN per frame, then a GRU
  over the per-frame features, trained end to end on clips.

The dataset is built so the comparison is fair. Each clip is a bright square on a dark
background, and the five classes are defined *by motion*: moving right, moving left,
approaching (growing), departing (shrinking), stationary (jittering). Start position and
size are drawn from overlapping distributions, so

* a square at x=30 could be moving right or left,
* a square of side 20 could be growing or shrinking,
* a stationary square and a slowly moving one differ by about a pixel.

That is the honest version of a real action-recognition problem: a still frame of a person
standing cannot distinguish walking from standing still, and no image model can fix that by
being bigger.

Note what is **not** claimed: the temporal model here is small, trained from scratch on
synthetic clips, and is not a Kinetics-pretrained 3-D CNN. It is a genuine temporal model -
it consumes a sequence and its gradients flow through time - which is exactly the property
Lab 4's fine-tuned detector lacks. Module 13 explains when a pretrained video backbone
(I3D, SlowFast, VideoMAE) is worth its download and licence.

Run:

    python lab6_action_recognition.py               # ~40 s on CPU
    python lab6_action_recognition.py --selftest    # small data, checks only
    python lab6_action_recognition.py --per-class 80 --epochs 25

Output:

    outputs/lab6_clip_<class>.png     one 8-frame strip per class
    outputs/lab6_action_recognition.json
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lab_support as support
from video_core import actions, metrics, synth, video


def clip_strip(action: str, seed: int, path: Path) -> Path:
    """One clip's frames tiled left to right, with the class name in the file name."""
    frames, meta = synth.action_clip(action, seed=seed)
    rgb = [cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR) for frame in frames]
    labels = [f"t={i}" for i in range(len(frames))]
    sheet = video.contact_sheet(rgb, cols=len(rgb), thumb=(64, 64), labels=labels)
    cv2.imwrite(str(path), sheet)
    return path


def confusion_rows(report: dict, names: list[str]) -> list[dict]:
    rows = []
    for i, name in enumerate(names):
        row = {"class": name}
        for j, other in enumerate(names):
            row[other] = report["confusion"][i][j]
        rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--per-class", type=int, default=60, help="clips per class (default 60)")
    parser.add_argument("--frames", type=int, default=8, help="frames per clip (default 8)")
    parser.add_argument("--frame-epochs", type=int, default=15)
    parser.add_argument("--temporal-epochs", type=int, default=20)
    parser.add_argument("--selftest", action="store_true", help="small data, checks only")
    args = parser.parse_args()

    per_class = 20 if args.selftest else args.per_class
    frame_epochs = 6 if args.selftest else args.frame_epochs
    temporal_epochs = 8 if args.selftest else args.temporal_epochs

    support.rule("clips")
    splits = actions.split_by_seed(n_per_class=per_class)
    classes = splits["classes"]
    print(f"  classes    : {classes}")
    print(f"  clip       : {splits['x_train'].shape[1]} frames of "
          f"{splits['x_train'].shape[2]}x{splits['x_train'].shape[3]} grayscale")
    print(f"  train/test : {len(splits['y_train'])} / {len(splits['y_test'])} clips")
    print("  split      : disjoint random seeds, so no test clip shares a draw with training")
    print("  why it is hard: a single frame of a moving square looks like a single frame of")
    print("               a stationary square. Nothing in one frame says which way it moves.")

    for i, name in enumerate(classes):
        path = support.OUT / f"lab6_clip_{name}.png"
        clip_strip(name, 7 + i, path)
    print(f"  strips     : lab6_clip_<class>.png ({len(classes)} files)")

    support.rule("model 1: single-frame classifier (the baseline)")
    started = time.perf_counter()
    frame_model, frame_hist = actions.train_frame_model(
        splits["x_train"], splits["y_train"], epochs=frame_epochs)
    frame_train_s = time.perf_counter() - started
    frame_preds = actions.predict_frames(frame_model, splits["x_test"])
    per_frame = frame_preds.reshape(-1)
    per_frame_truth = np.repeat(splits["y_test"], frame_preds.shape[1])
    frame_frame_acc = float((per_frame == per_frame_truth).mean())
    votes = actions.frame_vote_predictions(frame_model, splits["x_test"])
    frame_clip_acc = float((votes == splits["y_test"]).mean())
    stability = actions.stability(frame_preds)
    print(f"  parameters : {sum(p.numel() for p in frame_model.parameters()):,}")
    print(f"  train time : {frame_train_s:.1f} s  (loss {frame_hist['loss'][0]} -> "
          f"{frame_hist['loss'][-1]})")
    print(f"  per frame  : {frame_frame_acc:.3f} accuracy (chance is "
          f"{1 / len(classes):.2f})")
    print(f"  per clip   : {frame_clip_acc:.3f} after majority-voting the 8 frames")
    print(f"  stability  : frames agree in {stability['clips_all_frames_agree']}/"
          f"{stability['clips']} clips "
          f"({stability['fraction_agree']:.2f}); mean distinct labels per clip "
          f"{stability['mean_distinct_labels_per_clip']}")
    print("  A vote cannot rescue a model that cannot see motion: it just picks the most")
    print("  common guess among eight equally uninformed guesses.")

    support.rule("model 2: CNN + GRU over the clip (a temporal model)")
    started = time.perf_counter()
    temporal_model, temporal_hist = actions.train_temporal_model(
        splits["x_train"], splits["y_train"], epochs=temporal_epochs)
    temporal_train_s = time.perf_counter() - started
    temporal_preds = actions.predict_temporal(temporal_model, splits["x_test"])
    temporal_acc = float((temporal_preds == splits["y_test"]).mean())
    print(f"  parameters : {sum(p.numel() for p in temporal_model.parameters()):,}")
    print(f"  train time : {temporal_train_s:.1f} s  (loss {temporal_hist['loss'][0]} -> "
          f"{temporal_hist['loss'][-1]})")
    print(f"  per clip   : {temporal_acc:.3f} accuracy")
    print("  The only architectural difference is that this model's input is (T, H, W) and")
    print("  its gradients flow across time. Same frame encoder, same data, same seed.")

    support.rule("where each model is right")
    frame_report = metrics.classification_report(splits["y_test"], votes, classes)
    temporal_report = metrics.classification_report(splits["y_test"], temporal_preds, classes)
    rows = []
    for name in classes:
        rows.append({
            "class": name,
            "frame_f1": frame_report["per_class"][name]["f1"],
            "temporal_f1": temporal_report["per_class"][name]["f1"],
            "frame_recall": frame_report["per_class"][name]["recall"],
            "temporal_recall": temporal_report["per_class"][name]["recall"],
            "support": frame_report["per_class"][name]["support"],
        })
    support.table(rows, ["class", "frame_f1", "temporal_f1", "frame_recall",
                         "temporal_recall", "support"])
    support.table(confusion_rows(temporal_report, classes), ["class", *classes])
    print("  (confusion rows = truth, columns = prediction)")

    support.rule("speed")
    single = metrics.benchmark(lambda: actions.predict_frames(frame_model, splits["x_test"]),
                               runs=3, n_items=len(splits["x_test"]), label="frame model")
    clip = metrics.benchmark(lambda: actions.predict_temporal(temporal_model, splits["x_test"]),
                             runs=3, n_items=len(splits["x_test"]), label="temporal model")
    support.table([single, clip], ["label", "runs", "median_ms", "throughput_per_s"])
    print(f"  per clip   : {single['median_ms'] / len(splits['x_test']):.2f} ms (frame model, "
          f"all {splits['x_test'].shape[1]} frames) vs "
          f"{clip['median_ms'] / len(splits['x_test']):.2f} ms (temporal model)")
    print("  Both are cheap here because the model is small. The real cost of a temporal")
    print("  model is that it needs a whole clip before it can answer, which adds latency")
    print("  and a buffer to a live system.")

    gain = temporal_acc - frame_clip_acc
    results = [
        support.check("the temporal model beats the frame baseline clearly", gain >= 0.15,
                      f"{frame_clip_acc:.3f} -> {temporal_acc:.3f} (+{gain:.3f})"),
        support.check("the temporal model is better than guessing", temporal_acc >= 0.6,
                      f"{temporal_acc:.3f}"),
        support.check("the frame baseline is not secretly solving it", frame_clip_acc <= 0.7,
                      f"{frame_clip_acc:.3f}"),
        support.check("single frames disagree within clips (the ambiguity is real)",
                      stability["fraction_agree"] < 0.9,
                      f"{stability['fraction_agree']:.2f} agree"),
        support.check("per-frame accuracy is far below clip accuracy",
                      frame_frame_acc < temporal_acc - 0.1,
                      f"{frame_frame_acc:.3f} vs {temporal_acc:.3f}"),
    ]

    support.write_report("lab6_action_recognition.json", {
        "lab": "action recognition: frame baseline vs temporal model",
        "clips": {"per_class": per_class, "frames": int(splits["x_train"].shape[1]),
                  "size": int(splits["x_train"].shape[2]), "classes": classes,
                  "train": len(splits["y_train"]), "test": len(splits["y_test"])},
        "frame_model": {"parameters": int(sum(p.numel() for p in frame_model.parameters())),
                        "train_seconds": round(frame_train_s, 2),
                        "history": frame_hist, "per_frame_accuracy": round(frame_frame_acc, 4),
                        "clip_vote_accuracy": round(frame_clip_acc, 4),
                        "stability": stability, "report": frame_report,
                        "latency": single},
        "temporal_model": {"parameters": int(sum(p.numel() for p in temporal_model.parameters())),
                           "train_seconds": round(temporal_train_s, 2),
                           "history": temporal_hist, "accuracy": round(temporal_acc, 4),
                           "report": temporal_report, "latency": clip},
        "checks": results,
    })
    return support.all_checks(results)


if __name__ == "__main__":
    raise SystemExit(main())
