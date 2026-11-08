"""Generate every audio corpus used by the speech section.

Run once, from the repository root:

    python scripts/make_audio_data.py

Outputs (all under ``data/audio/``, which is git-ignored because it is generated):

    env/      wavs/ + manifest.json + leakage.json   4 environmental classes
    speech/   wavs/ + manifest.json + leakage.json   24 speakers x 6 words x 2
    diarization/  one two-speaker mix plus its truth file
    dataset_card.json                                licence, provenance, sizes, issues

Everything is deterministic: the same script and the same seeds produce byte-identical
WAVs, so the numbers a student measures match the ones printed in the lessons.

**There are no recordings of real people here.** Every clip is synthesised from code
and released CC0-1.0, which is what makes the section usable without consent
paperwork. It also means no claim is made that these clips resemble a real
deployment: the realism gap is stated in every module and in the dataset card.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "projects" / "speech-audio"))

from speech_core import audio, datasets  # noqa: E402

OUT = REPO_ROOT / "data" / "audio"


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _annotate_manifest(subdir: str, records, grouped: dict[str, list]) -> None:
    """Add measured level, duration, and split membership to the pooled manifest."""
    split_of = {id(record): name for name, subset in grouped.items() for record in subset}
    path = OUT / subdir / "manifest.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    if len(rows) != len(records):
        raise RuntimeError(f"{subdir}: manifest has {len(rows)} rows for {len(records)} records")
    for row, record in zip(rows, records):
        row["rms"] = round(audio.rms(record.samples), 6)
        row["duration"] = round(record.duration, 4)
        row["split"] = split_of[id(record)]
    path.write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")


def build_env() -> dict:
    records = datasets.make_env_dataset(n_sources=20, variants_per_source=3, seed=1)
    grouped = datasets.group_split(records, seed=0)
    naive = datasets.random_split(records, seed=0)

    # One manifest for the whole corpus, with the split as a column. Per-split folders
    # are written too, because the "load a directory of clips" workflow needs them.
    datasets.save_corpus(records, OUT, "env", "env")
    for split_name, subset in grouped.items():
        datasets.save_corpus(subset, OUT, f"env/{split_name}", f"env_{split_name}")
    _annotate_manifest("env", records, grouped)

    audit_grouped = datasets.audit_leakage(grouped)
    audit_naive = datasets.audit_leakage(naive, max_pairs=400)
    _write_json(OUT / "env" / "leakage.json", {"grouped": audit_grouped, "random": audit_naive})

    levels = {
        name: round(float(np.median([audio.rms(r.samples) for r in subset])), 4)
        for name, subset in grouped.items()
    }
    return {
        "n_clips": len(records),
        "n_sources": len({r.source_id for r in records}),
        "classes": list(datasets.ENV_CLASSES),
        "splits": {k: len(v) for k, v in grouped.items()},
        "balance": datasets.class_balance(records, datasets.ENV_CLASSES),
        "median_rms_per_split": levels,
        "grouped_leak": audit_grouped["leaky"],
        "grouped_cross_duplicates": audit_grouped["cross_split_near_duplicate_count"],
        "random_leak": audit_naive["leaky"],
        "random_cross_duplicates": audit_naive["cross_split_near_duplicate_count"],
    }


def build_speech() -> dict:
    records = datasets.make_speech_dataset(n_speakers=24, utterances_per_word=2, seed=2)
    grouped = datasets.group_split(records, seed=1)
    naive = datasets.random_split(records, seed=1)

    datasets.save_corpus(records, OUT, "speech", "speech")
    for split_name, subset in grouped.items():
        datasets.save_corpus(subset, OUT, f"speech/{split_name}", f"speech_{split_name}")
    _annotate_manifest("speech", records, grouped)

    audit_grouped = datasets.audit_leakage(grouped)
    audit_naive = datasets.audit_leakage(naive, max_pairs=400)
    _write_json(OUT / "speech" / "leakage.json", {"grouped": audit_grouped, "random": audit_naive})

    durations = np.array([r.duration for r in records])
    return {
        "n_clips": len(records),
        "n_speakers": len({r.source_id for r in records}),
        "words": list(datasets.WORDS),
        "splits": {k: len(v) for k, v in grouped.items()},
        "split_speakers": {k: len({r.source_id for r in v}) for k, v in grouped.items()},
        "balance": datasets.class_balance(records, datasets.WORDS),
        "duration_min": round(float(durations.min()), 3),
        "duration_median": round(float(np.median(durations)), 3),
        "duration_max": round(float(durations.max()), 3),
        "grouped_leak": audit_grouped["leaky"],
        "grouped_cross_duplicates": audit_grouped["cross_split_near_duplicate_count"],
        "random_leak": audit_naive["leaky"],
        "random_cross_duplicates": audit_naive["cross_split_near_duplicate_count"],
    }


def build_diarization() -> dict:
    mix = datasets.make_diarization_mix()
    audio.write_wav(OUT / "diarization" / "two_speakers.wav", mix["samples"], mix["sample_rate"])
    _write_json(
        OUT / "diarization" / "truth.json",
        {
            "segments": mix["segments"],
            "speakers": mix["speakers"],
            "duration": round(len(mix["samples"]) / mix["sample_rate"], 3),
            "note": "Speakers are synthetic voices from voice_for(0) and voice_for(5).",
        },
    )
    return {
        "duration": round(len(mix["samples"]) / mix["sample_rate"], 3),
        "segments": len(mix["segments"]),
        "speakers": mix["speakers"],
    }


def main() -> int:
    started = time.perf_counter()
    print(f"writing corpora to {OUT}")
    env = build_env()
    print(f"  env:         {env['n_clips']} clips, {env['n_sources']} sources, hard_leak={env['grouped_leak']}")
    speech = build_speech()
    print(f"  speech:      {speech['n_clips']} clips, {speech['n_speakers']} speakers, {speech['duration_median']}s median")
    diar = build_diarization()
    print(f"  diarization: {diar['duration']}s, {diar['segments']} segments")

    total_bytes = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
    card = {
        "name": "AITopics synthetic audio corpora",
        "version": "1.0.0",
        "generator": "scripts/make_audio_data.py",
        "licence": "CC0-1.0",
        "provenance": (
            "Every clip is synthesised from code: formant speech (glottal pulse through three "
            "resonators) and procedural environmental sounds. No recording of a person, and no "
            "third-party audio, was used. Fixed seeds make the output reproducible byte for byte."
        ),
        "consent": (
            "Not applicable: no human subjects, no recorded voices, no personal data. The "
            "voices are parameter sets, not people. If you replace this corpus with real "
            "recordings you must document consent, licence, retention, and the right to erasure."
        ),
        "splits": {
            "env": "grouped by source_id (80 sources, 3 variants each)",
            "speech": "grouped by speaker (24 voices, disjoint across train/val/test)",
        },
        "sizes": {"env": env, "speech": speech, "diarization": diar, "total_bytes": total_bytes, "total_mb": round(total_bytes / (1024 * 1024), 2)},
        "known_issues": [
            "Synthetic speech is more regular than human speech: expect real-world WER to be worse.",
            "Six-word closed vocabulary only; no out-of-vocabulary evaluation.",
            "Environmental classes never overlap and never co-occur with speech.",
            "No accents, no children's voices, no disordered speech, no multiple languages.",
            "The voices differ mainly in pitch and formant scale, so speaker tasks are easier than reality.",
        ],
        "elapsed_seconds": round(time.perf_counter() - started, 2),
    }
    _write_json(OUT / "dataset_card.json", card)
    print(f"  card:        {total_bytes / (1024 * 1024):.2f} MB total")
    print(f"done in {time.perf_counter() - started:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
