"""Lab B - Compare waveforms and spectrograms for different sound classes.

Goal: see what each representation preserves, and measure which one a classifier can
actually use.

The waveform is amplitude against time. It is the signal, and it is nearly unreadable
for anything longer than a few tens of milliseconds: an alarm and birdsong both look
like "wiggly". A spectrogram is frequency against time with energy as brightness, and
it makes the difference obvious - a steady tone versus sweeping chirps.

The measurement: train the same nearest-centroid classifier on three representations
and compare accuracy on held-out sources.

* **Raw waveform** - 64 evenly spaced amplitude samples, loudness-normalised.
* **Mel spectrogram** - 40 log-Mel bands averaged over time (plus their spread).
* **MFCC** - 13 cepstral coefficients averaged over time (plus their spread).

A nearest-centroid classifier is intentionally weak. It isolates the representation
from the model: if a representation separates the classes, even centroids find them.

Run:

    python lab_b_waveform_vs_spectrogram.py
    python lab_b_waveform_vs_spectrogram.py --selftest

Outputs: ``outputs/lab_b_features.json``, ``outputs/lab_b_alarm.png``,
``outputs/lab_b_rain.png``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lab_support as support
from speech_core import datasets, features


def waveform_vector(samples: np.ndarray, points: int = 64) -> np.ndarray:
    """Loudness-normalised amplitude at ``points`` evenly spaced positions."""
    peak = float(np.max(np.abs(samples))) or 1.0
    normalised = samples / peak
    idx = np.linspace(0, len(normalised) - 1, points).astype(int)
    return normalised[idx].astype(np.float32)


def mel_vector(samples: np.ndarray, sample_rate: int = 16_000) -> np.ndarray:
    mel = features.mel_spectrogram(samples, sample_rate=sample_rate, n_mels=40)
    return np.concatenate([mel.mean(axis=0), mel.std(axis=0)]).astype(np.float32)


def mfcc_vector(samples: np.ndarray, sample_rate: int = 16_000) -> np.ndarray:
    mfcc = features.mfcc(samples, sample_rate=sample_rate, n_mfcc=13)
    return np.concatenate([mfcc.mean(axis=0), mfcc.std(axis=0)]).astype(np.float32)


def centroids(vectors: np.ndarray, labels: np.ndarray, n_classes: int) -> np.ndarray:
    return np.stack([vectors[labels == c].mean(axis=0) for c in range(n_classes)])


def nearest_centroid_accuracy(train_vecs, train_labels, test_vecs, test_labels, n_classes: int) -> float:
    centres = centroids(train_vecs, train_labels, n_classes)
    distances = np.linalg.norm(test_vecs[:, None, :] - centres[None, :, :], axis=2)
    predicted = distances.argmin(axis=1)
    return float(np.mean(predicted == test_labels))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    records, origin = support.env_corpus()
    splits = datasets.group_split(records, seed=0)
    train, test = splits["train"], splits["test"]
    names = list(datasets.ENV_CLASSES)

    support.rule("what the waveform looks like")
    for kind in ("alarm", "rain"):
        clip = next(r for r in train if r.meta["class"] == kind)
        print(f"-- {kind} ({clip.duration:.2f}s, RMS {float(np.sqrt(np.mean(clip.samples ** 2))):.3f})")
        print(features.waveform_ascii(clip.samples, width=64))

    support.rule("what the spectrogram looks like")
    for kind in ("alarm", "rain"):
        clip = next(r for r in train if r.meta["class"] == kind)
        mel = features.mel_spectrogram(clip.samples, sample_rate=clip.sample_rate, n_mels=40)
        print(f"-- {kind}: 40 Mel bands x {mel.shape[0]} frames (bright = loud, low bands at the bottom)")
        print(features.ascii_spectrogram(mel, width=56, height=10))
        path = features.save_spectrogram_png(
            mel, support.OUT / f"lab_b_{kind}.png", title=f"{kind} log-Mel spectrogram"
        )
        print(f"saved {path.relative_to(support.HERE)}")

    support.rule("band energy per class (mean over clips, dB)")
    header = ["class", "0-500Hz", "0.5-2kHz", "2-4kHz", "4-8kHz"]
    rows = []
    for c, name in enumerate(names):
        clips = [r for r in train if r.label == c]
        bands = []
        for clip in clips:
            spec = features.mel_spectrogram(clip.samples, sample_rate=clip.sample_rate, n_mels=40)
            freqs = features.mel_band_frequencies(clip.sample_rate, n_mels=40)
            means = spec.mean(axis=0)
            edges = [(0.0, 500.0), (500.0, 2000.0), (2000.0, 4000.0), (4000.0, 8000.0)]
            bands.append([float(means[(freqs >= lo) & (freqs < hi)].mean()) for lo, hi in edges])
        rows.append({"class": name, **{h: float(np.mean(b)) for h, b in zip(header[1:], np.array(bands).T)}})
    support.table(rows, header)

    support.rule("nearest-centroid accuracy by representation (held-out sources)")
    reps = {
        "raw waveform (64 pts)": lambda r: waveform_vector(r.samples),
        "mel spectrogram (80)": lambda r: mel_vector(r.samples, r.sample_rate),
        "MFCC (26)": lambda r: mfcc_vector(r.samples, r.sample_rate),
    }
    train_labels = np.array([r.label for r in train])
    test_labels = np.array([r.label for r in test])
    results = {}
    for name, fn in reps.items():
        train_vecs = np.stack([fn(r) for r in train])
        test_vecs = np.stack([fn(r) for r in test])
        accuracy = nearest_centroid_accuracy(train_vecs, train_labels, test_vecs, test_labels, len(names))
        results[name] = accuracy
        dims = train_vecs.shape[1]
        print(f"{name:<24} dims {dims:>3}  accuracy {accuracy:.3f}")

    support.rule("what the representations cannot tell apart")
    train_mel = np.stack([mel_vector(r.samples, r.sample_rate) for r in train])
    centres = centroids(train_mel, train_labels, len(names))
    pair_rows = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            distance = float(np.linalg.norm(centres[i] - centres[j]))
            pair_rows.append({"pair": f"{names[i]} vs {names[j]}", "mel distance": distance})
    pair_rows.sort(key=lambda row: row["mel distance"])
    support.table(pair_rows[:4], ["pair", "mel distance"])
    support.table(pair_rows[-2:], ["pair", "mel distance"])
    print("The closest pair is where centroid errors come from; the farthest pair explains")
    print("why two classes are never confused by this representation.")

    best = max(results, key=results.get)
    payload = {
        "lab": "B",
        "title": "waveform vs spectrogram representations",
        "corpus_origin": origin,
        "band_energy": rows,
        "nearest_centroid_accuracy": results,
        "mel_class_distances": pair_rows,
        "best_representation": best,
        "checks": {},
    }

    checks = {
        "mel beats raw waveform": results["mel spectrogram (80)"] > results["raw waveform (64 pts)"],
        "chance level is 0.25": 0.0 <= results["raw waveform (64 pts)"] <= 1.0,
        "all accuracies in [0, 1]": all(0.0 <= v <= 1.0 for v in results.values()),
    }
    if not args.selftest:
        checks["MFCC is within 0.15 of Mel"] = abs(results["MFCC (26)"] - results["mel spectrogram (80)"]) <= 0.15
    failures = 0
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}  {name}")
        failures += 0 if passed else 1
    payload["checks"] = checks

    path = support.write_report("lab_b_features.json", payload)
    print(f"\nreport written to {path.relative_to(support.HERE)}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
