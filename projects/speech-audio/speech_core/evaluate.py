"""Evaluation and robustness suites shared by the labs.

Three questions this file answers, all of which students ask late and should ask early:

1. Does the classifier still work when the world is not the test set? (noise, gain,
   speaking rate, clipping)
2. What does the recogniser actually get wrong, and does a lexicon hide it?
3. What does inference cost, and does that cost fit a real-time budget?

Each function returns plain dictionaries so it can be dumped to JSON and compared
between runs - the labs commit only the numbers they measured.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

import json

import numpy as np
import torch

from . import asr, audio, metrics, text, training
from .datasets import AudioRecord


# ---------------------------------------------------------------------------
# Classifier evaluation
# ---------------------------------------------------------------------------


def classifier_report(
    model: torch.nn.Module,
    records: Sequence[AudioRecord],
    class_names: Sequence[str],
    n_mels: int = 40,
    mean: float = 0.0,
    std: float = 1.0,
    max_frames: int | None = None,
) -> dict:
    x, _, _ = training.build_inputs(records, n_mels=n_mels, max_frames=max_frames)
    x = training.normalize_inputs(x, mean, std)
    pred, probs = training.predict(model, x)
    truth = np.array([r.label for r in records], dtype=np.int64)
    report = metrics.classification_report(truth, pred, class_names)
    report["confusions"] = [
        {"true": a, "predicted": b, "count": c} for a, b, c in metrics.top_confusions(report, class_names)
    ]
    report["mean_confidence"] = float(np.mean(probs.max(axis=1))) if len(probs) else 0.0
    report["confidence_correct"] = np.corrcoef(probs.max(axis=1), (pred == truth).astype(float))[0, 1] if len(probs) > 1 and (pred == truth).std() > 0 else 0.0
    return report


# ---------------------------------------------------------------------------
# Robustness conditions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Condition:
    """One perturbation applied to the same clips, so accuracy difference is causal."""

    name: str
    description: str
    apply: Callable[[np.ndarray, int, int], np.ndarray]


def _noise(snr_db: float):
    def apply(samples: np.ndarray, sample_rate: int, seed: int) -> np.ndarray:
        return audio.add_noise(samples, snr_db, seed=seed)

    return apply


def _gain(gain_db: float):
    def apply(samples: np.ndarray, sample_rate: int, seed: int) -> np.ndarray:
        return audio.change_gain(samples, gain_db)

    return apply


def _speed(factor: float):
    def apply(samples: np.ndarray, sample_rate: int, seed: int) -> np.ndarray:
        return audio.time_stretch(samples, factor, sample_rate)

    return apply


def _bandwidth(sample_rate: int):
    """Simulate a narrowband line: resample down to 4 kHz and back up."""
    low = max(1000, sample_rate // 4)

    def apply(samples: np.ndarray, sr: int, seed: int) -> np.ndarray:
        down = audio.resample(samples, sr, low)
        return audio.resample(down, low, sr)

    return apply


CONDITIONS: tuple[Condition, ...] = (
    Condition("clean", "unmodified test clips", lambda s, sr, seed: s),
    Condition("snr_20", "white noise at 20 dB SNR (mild office)", _noise(20.0)),
    Condition("snr_10", "white noise at 10 dB SNR (busy cafe)", _noise(10.0)),
    Condition("snr_5", "white noise at 5 dB SNR (street)", _noise(5.0)),
    Condition("gain_-12db", "12 dB quieter, as if recorded further away", _gain(-12.0)),
    Condition("slower_1.15x", "speaking rate slowed by 15% (stress, emphasis)", _speed(1.15)),
    Condition("narrowband_4khz", "band-limited to 4 kHz, as on a phone call", _bandwidth(16_000)),
)


def apply_condition(records: Sequence[AudioRecord], condition: Condition, seed: int = 0) -> list[AudioRecord]:
    out = []
    for i, record in enumerate(records):
        samples = condition.apply(record.samples, record.sample_rate, seed + i)
        out.append(
            AudioRecord(
                samples=np.asarray(samples, dtype=np.float32),
                sample_rate=record.sample_rate,
                label=record.label,
                source_id=record.source_id,
                meta={**record.meta, "condition": condition.name},
            )
        )
    return out


def robustness_suite(
    model: torch.nn.Module,
    records: Sequence[AudioRecord],
    class_names: Sequence[str],
    conditions: Sequence[Condition] = CONDITIONS,
    n_mels: int = 40,
    mean: float = 0.0,
    std: float = 1.0,
) -> dict:
    """Accuracy per condition, plus the drop relative to clean audio."""
    max_frames = max(training.mel_matrix(r, n_mels).shape[0] for r in records)
    rows = []
    clean = None
    for condition in conditions:
        perturbed = apply_condition(records, condition)
        report = classifier_report(model, perturbed, class_names, n_mels=n_mels, mean=mean, std=std, max_frames=max_frames)
        if condition.name == "clean":
            clean = report["accuracy"]
        rows.append(
            {
                "condition": condition.name,
                "description": condition.description,
                "accuracy": report["accuracy"],
                "mean_confidence": report["mean_confidence"],
            }
        )
    for row in rows:
        row["drop_vs_clean"] = None if clean is None else clean - row["accuracy"]
    return {"baseline": clean, "rows": rows, "worst": min(rows, key=lambda r: r["accuracy"])}


# ---------------------------------------------------------------------------
# ASR evaluation
# ---------------------------------------------------------------------------


def transcription_rows(
    model: torch.nn.Module,
    records: Sequence[AudioRecord],
    vocab: Sequence[str],
    mean: float = 0.0,
    std: float = 1.0,
    n_mels: int = 40,
) -> list[dict]:
    return asr.transcribe_records(model, records, vocab, mean=mean, std=std, n_mels=n_mels)


def asr_report(
    model: torch.nn.Module,
    records: Sequence[AudioRecord],
    vocab: Sequence[str],
    lexicon: Sequence[str] | None = None,
    max_ratio: float = 0.5,
    mean: float = 0.0,
    std: float = 1.0,
    n_mels: int = 40,
) -> dict:
    """Corpus WER/CER, per-word accuracy, and the lexicon ablation.

    Two error rates are reported on purpose. Corpus WER weights by length, so one bad
    long utterance can matter less than several bad short ones; the mean of per-clip
    WERs weights every clip equally. Quoting whichever is lower is a common trick and
    the reason both are printed.
    """
    rows = transcription_rows(model, records, vocab, mean=mean, std=std, n_mels=n_mels)
    pairs = [(row["reference"], row["text"]) for row in rows]
    corpus = text.corpus_error_rates(pairs)
    per_word: dict[str, dict] = {}
    for ref, hyp in pairs:
        bucket = per_word.setdefault(ref, {"n": 0, "correct": 0})
        bucket["n"] += 1
        if text.normalize_text(ref) == text.normalize_text(hyp):
            bucket["correct"] += 1
    for word, bucket in per_word.items():
        bucket["accuracy"] = bucket["correct"] / bucket["n"] if bucket["n"] else 0.0
    report = {
        **corpus,
        "per_word": per_word,
        "confusions": [{"reference": a, "recognised": b, "count": c} for a, b, c in text.confusion_pairs(pairs)],
        "examples": rows[:8],
        "mean_confidence": float(np.mean([r["confidence"] for r in rows])) if rows else 0.0,
    }
    if lexicon:
        report["lexicon"] = lexicon_ablation(pairs, lexicon, max_ratio=max_ratio)
    return report


def lexicon_ablation(pairs: Sequence[tuple[str, str]], lexicon: Sequence[str], max_ratio: float = 0.5) -> dict:
    """WER before and after snapping hypotheses to the nearest known word."""
    raw, snapped, changed = [], [], 0
    for reference, hypothesis in pairs:
        decision = asr.lexicon_decode(hypothesis, lexicon, max_ratio=max_ratio)
        raw.append((reference, text.normalize_text(hypothesis)))
        snapped.append((reference, decision["text"]))
        changed += int(decision["applied"])
    before = text.corpus_error_rates(raw)
    after = text.corpus_error_rates(snapped)
    return {
        "max_ratio": max_ratio,
        "lexicon_size": len(lexicon),
        "wer_before": before["wer"],
        "wer_after": after["wer"],
        "absolute_gain": before["wer"] - after["wer"],
        "utterances_changed": changed,
        "caveat": "Snapping only works for a closed vocabulary; it does not improve a model that mis-hears acoustically similar words.",
    }


# ---------------------------------------------------------------------------
# Latency
# ---------------------------------------------------------------------------


def latency_report(
    cases: Sequence[dict],
    runs: int = 15,
    warmup: int = 2,
) -> list[dict]:
    """``cases`` is ``[{"label", "callable", "audio_seconds", "params"}]``.

    Median wall time and real-time factor. RTF < 1 means faster than the audio plays,
    which is the minimum for a live captioning interface; RTF > 1 means the transcript
    falls behind the speaker.
    """
    rows = []
    for case in cases:
        stats = metrics.benchmark(
            case["callable"],
            runs=runs,
            warmup=warmup,
            label=case["label"],
            audio_seconds=float(case.get("audio_seconds", 0.0)),
        )
        row = stats.as_dict()
        row["params"] = case.get("params")
        rows.append(row)
    return rows


def save_report(path: str | Path, payload: dict) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=_plain) + "\n", encoding="utf-8")
    return path


def _plain(value):
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Path):
        return str(value)
    return str(value)
