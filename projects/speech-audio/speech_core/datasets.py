"""Synthetic audio corpora, splits, leakage audits, and corpus persistence.

Every corpus here is generated from code with a fixed seed and released CC0-1.0.
There are no recordings of real people, so there is no consent to obtain and no
licence to negotiate - and also no claim that these clips resemble a real
deployment distribution. Modules that need realism say so and point at Lab E,
which uses a small dataset you are permitted to use and must document.

The split rule is the same as the vision section's, for the same reason: variants of
one source must not straddle the train/test boundary. For speech the "source" is a
**speaker**. Splitting by utterance instead of by speaker is how a recogniser reports
95% accuracy on a speaker it has already heard - the audio equivalent of a leaky
image split.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from . import audio, features, synth

DEFAULT_SR = 16_000
#: ``<repo>/data/audio`` - generated, git-ignored, rebuilt by scripts/make_audio_data.py.
#: Every loader falls back to generating in memory, so the labs run without it.
DATA_ROOT = Path(__file__).resolve().parents[3] / "data" / "audio"

ENV_CLASSES: tuple[str, ...] = synth.ENV_CLASSES
WORDS: tuple[str, ...] = tuple(synth.WORDS)

#: Intents used by the voice-assistant lab. The map is data, not behaviour.
COMMANDS: dict[str, str] = {
    "yes": "confirm",
    "no": "deny",
    "start": "start",
    "stop": "stop",
    "left": "previous",
    "right": "next",
}


@dataclass
class AudioRecord:
    """One clip plus everything needed to evaluate it honestly."""

    samples: np.ndarray
    sample_rate: int
    label: int
    source_id: str
    meta: dict = field(default_factory=dict)

    @property
    def duration(self) -> float:
        return len(self.samples) / float(self.sample_rate)

    @property
    def transcript(self) -> str:
        return str(self.meta.get("transcript", ""))

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "source_id": self.source_id,
            "duration": round(self.duration, 4),
            **{k: v for k, v in self.meta.items() if k != "samples"},
        }


# ---------------------------------------------------------------------------
# Environmental sounds
# ---------------------------------------------------------------------------


def make_env_dataset(
    n_sources: int = 20,
    variants_per_source: int = 3,
    duration: float = 1.0,
    sample_rate: int = DEFAULT_SR,
    seed: int = 1,
) -> list[AudioRecord]:
    """Four environmental classes; each source is one rendering, variants add noise/gain.

    Source-level grouping matters here too: the three variants of one alarm share
    its beep rate and pitch, so a random split lets a classifier recognise the
    specific alarm rather than the class.
    """
    records: list[AudioRecord] = []
    for class_index, kind in enumerate(ENV_CLASSES):
        for source in range(n_sources):
            base_seed = seed * 10_000 + class_index * 1_000 + source
            base = synth.env_sound(kind, duration, sample_rate, seed=base_seed, gain_db=-6.0)
            for variant in range(variants_per_source):
                rng = np.random.default_rng(base_seed + 100 + variant)
                shift = int(rng.integers(0, max(1, int(0.2 * sample_rate))))
                rolled = np.roll(base, shift)
                snr = float(rng.choice([30.0, 20.0, 12.0, 6.0]))
                noisy = audio.add_noise(rolled, snr, seed=int(rng.integers(0, 10_000)))
                gain = float(rng.uniform(-9.0, -1.0))
                clip = audio.change_gain(noisy, gain - 6.0)
                records.append(
                    AudioRecord(
                        samples=clip.astype(np.float32),
                        sample_rate=sample_rate,
                        label=class_index,
                        source_id=f"{kind}-src{source:02d}",
                        meta={
                            "class": kind,
                            "variant": variant,
                            "snr_db": snr,
                            "seed": base_seed,
                            "duration": duration,
                        },
                    )
                )
    return records


# ---------------------------------------------------------------------------
# Synthetic speech
# ---------------------------------------------------------------------------


def voice_for(index: int) -> synth.VoiceProfile:
    """Deterministic speaker profile for speaker ``index``.

    The 12 base profiles cover a pitch range of 95-200 Hz; beyond that, pitch,
    formant scale, and rate are jittered so the corpus has 24 distinguishable
    speakers rather than 12 doubled.
    """
    base = synth.VOICES[index % len(synth.VOICES)]
    cycle = index // len(synth.VOICES)
    rng = np.random.default_rng(9000 + index)
    f0 = float(base.f0 * (1.0 + 0.06 * cycle) * rng.uniform(0.97, 1.03))
    scale = float(base.formant_scale * rng.uniform(0.98, 1.02))
    rate = float(np.clip(base.rate * rng.uniform(0.95, 1.05), 0.8, 1.25))
    return synth.VoiceProfile(
        name=f"speaker_{index:02d}",
        f0=f0,
        formant_scale=scale,
        rate=rate,
        breathiness=base.breathiness,
        gain_db=base.gain_db,
        seed=index * 7 + 1,
    )


def make_speech_dataset(
    n_speakers: int = 24,
    words: Sequence[str] = WORDS,
    utterances_per_word: int = 2,
    sample_rate: int = DEFAULT_SR,
    seed: int = 2,
) -> list[AudioRecord]:
    """Isolated-word corpus: ``n_speakers`` voices x ``words`` x utterances."""
    records: list[AudioRecord] = []
    for speaker_index in range(n_speakers):
        profile = voice_for(speaker_index)
        for word_index, word in enumerate(words):
            for utt in range(utterances_per_word):
                rng = np.random.default_rng(seed * 100_000 + speaker_index * 100 + word_index * 10 + utt)
                # Small per-utterance variation: gain and a little noise, not new phonemes.
                clip = synth.speak(word, profile, sample_rate)
                clip = audio.change_gain(clip, float(rng.uniform(-4.0, 0.0)))
                snr = float(rng.choice([40.0, 25.0, 15.0]))
                clip = audio.add_noise(clip, snr, seed=int(rng.integers(0, 100_000)))
                records.append(
                    AudioRecord(
                        samples=clip.astype(np.float32),
                        sample_rate=sample_rate,
                        label=word_index,
                        source_id=profile.name,
                        meta={
                            "transcript": word,
                            "speaker": profile.name,
                            "f0": round(profile.f0, 1),
                            "utterance": utt,
                            "snr_db": snr,
                        },
                    )
                )
    return records


def make_diarization_mix(
    speaker_indices: Sequence[int] = (0, 5),
    words_per_speaker: Sequence[str] = ("start", "left", "stop"),
    sample_rate: int = DEFAULT_SR,
    gap: float = 0.25,
    seed: int = 3,
) -> dict:
    """A two-speaker clip with segment boundaries, for the diarization exercise.

    Returns a dict with the mixed samples, the per-segment truth, and the source
    speakers. The task is to recover *who spoke when* without being told which
    voices are present - not to identify the people, who are synthetic.
    """
    pieces: list[np.ndarray] = []
    segments: list[dict] = []
    cursor = 0.0
    for speaker_index, word in zip(speaker_indices * len(words_per_speaker), list(words_per_speaker) * len(speaker_indices)):
        profile = voice_for(speaker_index)
        clip = synth.speak(word, profile, sample_rate)
        pieces.append(clip)
        segments.append(
            {
                "start": round(cursor, 3),
                "end": round(cursor + len(clip) / sample_rate, 3),
                "speaker": profile.name,
                "word": word,
            }
        )
        cursor += len(clip) / sample_rate
        silence = np.zeros(int(gap * sample_rate), dtype=np.float32)
        pieces.append(silence)
        cursor += gap
    return {
        "samples": np.concatenate(pieces).astype(np.float32),
        "sample_rate": sample_rate,
        "segments": segments,
        "speakers": [voice_for(i).name for i in speaker_indices],
        "seed": seed,
    }


# ---------------------------------------------------------------------------
# Splitting and leakage
# ---------------------------------------------------------------------------


def group_split(
    records: Sequence[AudioRecord],
    fractions: tuple[float, float, float] = (0.7, 0.15, 0.15),
    seed: int = 0,
) -> dict[str, list[AudioRecord]]:
    """Split by ``source_id`` so no source crosses a boundary."""
    if abs(sum(fractions) - 1.0) > 1e-6:
        raise ValueError("fractions must sum to 1")
    sources = sorted({r.source_id for r in records})
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(sources))
    n_train = int(round(fractions[0] * len(sources)))
    n_val = int(round(fractions[1] * len(sources)))
    train_sources = {sources[i] for i in order[:n_train]}
    val_sources = {sources[i] for i in order[n_train : n_train + n_val]}
    test_sources = set(sources) - train_sources - val_sources
    return {
        "train": [r for r in records if r.source_id in train_sources],
        "val": [r for r in records if r.source_id in val_sources],
        "test": [r for r in records if r.source_id in test_sources],
    }


def random_split(
    records: Sequence[AudioRecord],
    fractions: tuple[float, float, float] = (0.7, 0.15, 0.15),
    seed: int = 0,
) -> dict[str, list[AudioRecord]]:
    """Split per clip - the leaky baseline the audit is meant to catch."""
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(records))
    n_train = int(round(fractions[0] * len(records)))
    n_val = int(round(fractions[1] * len(records)))
    shuffled = [records[i] for i in order]
    return {
        "train": shuffled[:n_train],
        "val": shuffled[n_train : n_train + n_val],
        "test": shuffled[n_train + n_val :],
    }


def fingerprint(samples: np.ndarray, sample_rate: int = DEFAULT_SR, n_bits: int = 64) -> np.ndarray:
    """Coarse spectral-shape fingerprint: mean log-Mel across time, resampled to bits.

    The shape is centred on its own mean before thresholding, so loudness and gain
    cannot move a bit. Two renderings of the same source land within a couple of bits;
    different classes sit tens of bits apart, which is what makes the near-duplicate
    audit informative rather than noise.
    """
    mel = features.mel_spectrogram(samples, sample_rate=sample_rate, n_mels=32)
    shape = mel.mean(axis=0)
    centred = shape - float(shape.mean())
    x_old = np.linspace(0.0, 1.0, len(centred))
    x_new = np.linspace(0.0, 1.0, n_bits)
    resampled = np.interp(x_new, x_old, centred)
    return (resampled > 0.0).astype(np.int8)


def hamming(a: np.ndarray, b: np.ndarray) -> int:
    return int(np.sum(np.asarray(a) != np.asarray(b)))


def near_duplicate_pairs(
    records: Sequence[AudioRecord], max_distance: int = 10
) -> list[tuple[int, int, int]]:
    """Pairs of records whose fingerprints differ by at most ``max_distance`` bits."""
    fps = [fingerprint(r.samples, r.sample_rate) for r in records]
    pairs: list[tuple[int, int, int]] = []
    for i in range(len(fps)):
        for j in range(i + 1, len(fps)):
            distance = hamming(fps[i], fps[j])
            if distance <= max_distance:
                pairs.append((i, j, distance))
    return pairs


def audit_leakage(
    splits: dict[str, list[AudioRecord]], max_distance: int = 4, max_pairs: int = 4000
) -> dict:
    """Report hard source overlap and soft near-duplicates across splits.

    The **decision** is made on hard overlap: the same speaker or source id on both
    sides of a split. That is unambiguous and always a bug.

    The soft count is a diagnostic, not a verdict. A coarse fingerprint keys on
    spectral *content*, so on speech it groups clips by the word spoken rather than by
    the voice: the same speaker saying two different words looks less similar than two
    speakers saying the same word. Treat a non-zero soft count as "look at these pairs",
    never as "the split is broken".
    """
    names = list(splits)
    overlap: dict[str, int] = {}
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            shared = {r.source_id for r in splits[left]} & {r.source_id for r in splits[right]}
            overlap[f"{left}__{right}"] = len(shared)
    shared_total = sum(overlap.values())

    cross_pairs = 0
    cross_min = None
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            a, b = splits[left][:max_pairs], splits[right][:max_pairs]
            if not a or not b:
                continue
            fps_a = [fingerprint(r.samples, r.sample_rate) for r in a]
            fps_b = [fingerprint(r.samples, r.sample_rate) for r in b]
            for fa in fps_a:
                for fb in fps_b:
                    distance = hamming(fa, fb)
                    if distance <= max_distance:
                        cross_pairs += 1
                        cross_min = distance if cross_min is None else min(cross_min, distance)
    return {
        "source_overlap": overlap,
        "n_shared_sources": shared_total,
        "cross_split_near_duplicate_count": cross_pairs,
        "closest_cross_split_distance": cross_min,
        "distance_threshold": max_distance,
        "hard_leaky": shared_total > 0,
        "soft_leaky": cross_pairs > 0,
        "leaky": shared_total > 0,
        "decision_basis": "hard source/speaker overlap",
        "soft_metric_caveat": (
            "Fingerprint distance measures spectral content, not identity: for speech it "
            "separates words, not voices. Use it to find repeated clips, not to certify a split."
        ),
    }


def class_balance(records: Iterable[AudioRecord], class_names: Sequence[str]) -> dict[str, int]:
    counts = {name: 0 for name in class_names}
    for record in records:
        if 0 <= record.label < len(class_names):
            counts[class_names[record.label]] += 1
    return counts


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def save_corpus(
    records: Sequence[AudioRecord],
    root: str | Path,
    subdir: str,
    name_prefix: str = "clip",
) -> list[dict]:
    """Write WAVs plus a manifest; returns the manifest rows."""
    root = Path(root) / subdir
    images_dir = root / "wavs"
    images_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for i, record in enumerate(records):
        filename = f"{name_prefix}_{i:04d}.wav"
        audio.write_wav(images_dir / filename, record.samples, record.sample_rate)
        row = {
            "file": filename,
            "label": record.label,
            "source_id": record.source_id,
            "sample_rate": record.sample_rate,
            **record.meta,
        }
        rows.append(row)
    (root / "manifest.json").write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
    return rows
