"""Load the generated corpora from disk, or regenerate them when they are absent.

Students start from a fresh clone where ``data/`` does not exist. Every loader here
therefore has two paths: read the manifest if the generator has been run, otherwise
build the same corpus in memory with the same seeds. The numbers in the lessons are
identical either way - the generator is a cache, not a dependency.

Run ``python scripts/make_audio_data.py`` from the repository root to materialise the
WAV files (about 17 MB) for the exercises that need file I/O: playback, formats, and
the "load a folder of clips" workflow.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

import numpy as np

from . import audio, datasets
from .datasets import DATA_ROOT, AudioRecord

__all__ = [
    "DATA_ROOT",
    "available",
    "dataset_card",
    "load_env_corpus",
    "load_speech_corpus",
    "load_manifest",
    "read_clip",
    "summary",
]


def available() -> dict[str, bool]:
    """Which generated sub-corpora exist on disk right now."""
    return {
        "root_exists": DATA_ROOT.exists(),
        "env": (DATA_ROOT / "env" / "manifest.json").exists(),
        "speech": (DATA_ROOT / "speech" / "manifest.json").exists(),
    }


def load_manifest(subdir: str) -> list[dict]:
    path = DATA_ROOT / subdir / "manifest.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def read_clip(row: dict, subdir: str) -> AudioRecord:
    """Turn one manifest row back into an ``AudioRecord``."""
    samples, rate = audio.read_wav(DATA_ROOT / subdir / "wavs" / row["file"])
    meta = {k: v for k, v in row.items() if k not in {"file", "label", "source_id", "sample_rate"}}
    return AudioRecord(
        samples=samples,
        sample_rate=rate,
        label=int(row["label"]),
        source_id=str(row["source_id"]),
        meta=meta,
    )


def load_env_corpus(
    n_sources: int = 20,
    variants_per_source: int = 3,
    seed: int = 1,
) -> tuple[list[AudioRecord], str]:
    """Environmental sounds, from disk when present. Returns ``(records, origin)``."""
    rows = load_manifest("env")
    if rows:
        return [read_clip(row, "env") for row in rows], "disk"
    return datasets.make_env_dataset(n_sources=n_sources, variants_per_source=variants_per_source, seed=seed), "generated"


def load_speech_corpus(
    n_speakers: int = 24,
    utterances_per_word: int = 2,
    seed: int = 2,
    words: Sequence[str] | None = None,
) -> tuple[list[AudioRecord], str]:
    """Isolated-word speech corpus, from disk when present."""
    rows = load_manifest("speech")
    if rows:
        return [read_clip(row, "speech") for row in rows], "disk"
    kwargs = {} if words is None else {"words": words}
    return (
        datasets.make_speech_dataset(
            n_speakers=n_speakers,
            utterances_per_word=utterances_per_word,
            seed=seed,
            **kwargs,
        ),
        "generated",
    )


def dataset_card() -> dict:
    """The generated dataset card, or a minimal stand-in when nothing is on disk."""
    path = DATA_ROOT / "dataset_card.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "name": "AITopics synthetic audio corpora",
        "origin": "not generated in this checkout",
        "licence": "CC0-1.0 (generated here, no recordings of people)",
        "n_env": None,
        "n_speech": None,
        "note": "Run scripts/make_audio_data.py to write the WAV files and this card.",
    }


def summary() -> dict:
    """Small status dict the labs print at start-up."""
    env_rows = load_manifest("env")
    speech_rows = load_manifest("speech")
    level_env = [row.get("rms") for row in env_rows if row.get("rms") is not None]
    level_speech = [row.get("rms") for row in speech_rows if row.get("rms") is not None]
    return {
        "root": str(DATA_ROOT),
        "files": available(),
        "n_env": len(env_rows),
        "n_speech": len(speech_rows),
        "env_classes": len({row.get("class") for row in env_rows}) if env_rows else len(datasets.ENV_CLASSES),
        "speakers": len({row.get("speaker") for row in speech_rows}) if speech_rows else None,
        "speech_words": sorted({row.get("transcript") for row in speech_rows}) if speech_rows else list(datasets.WORDS),
        "median_rms_env": float(np.median(level_env)) if level_env else None,
        "median_rms_speech": float(np.median(level_speech)) if level_speech else None,
        "bytes": _disk_bytes(DATA_ROOT),
    }


def _disk_bytes(root: Path) -> int:
    if not root.exists():
        return 0
    return int(sum(p.stat().st_size for p in root.rglob("*") if p.is_file()))
