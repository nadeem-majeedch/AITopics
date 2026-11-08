"""Small helpers shared by the speech labs (loading, caching, printing, JSON output).

Nothing here is part of the teaching content - it keeps each lab file focused on the
experiment instead of on argument parsing and file paths.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Sequence

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from speech_core import asr, dataio, datasets, text  # noqa: E402

OUT = HERE / "outputs"
CACHE = OUT / "cache"


def write_report(name: str, payload: dict) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
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


def rule(title: str) -> None:
    print(f"\n=== {title}")


def table(rows: Sequence[dict], columns: Sequence[str]) -> None:
    if not rows:
        print("(no rows)")
        return
    widths = {col: max(len(col), *(len(_cell(row.get(col))) for row in rows)) for col in columns}
    print("  ".join(f"{col:<{widths[col]}}" for col in columns))
    print("-" * (sum(widths.values()) + 2 * (len(columns) - 1)))
    for row in rows:
        print("  ".join(f"{_cell(row.get(col)):<{widths[col]}}" for col in columns))


def _cell(value) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    if value is None:
        return "-"
    return str(value)


def env_corpus():
    records, origin = dataio.load_env_corpus()
    return records, origin


def speech_splits(seed: int = 1):
    records, origin = dataio.load_speech_corpus()
    splits = datasets.group_split(records, seed=seed)
    return splits, origin


def vocab_for(records) -> list[str]:
    return text.build_char_vocab([r.transcript for r in records])


def recognizer(
    key: str,
    epochs: int = 12,
    train_records=None,
    val_records=None,
    *,
    seed: int = 0,
    lr: float = 3e-3,
    stride_time: int = 2,
    width: int = 16,
    hidden: int = 64,
    log: bool = False,
    force: bool = False,
):
    """Train a recogniser once and reuse it, keyed by the settings that change it.

    Training the reference model takes a few seconds on CPU, but eight labs each
    retraining it wastes a minute of every student's time. The cache is content-free:
    delete ``outputs/cache`` and everything rebuilds.
    """
    CACHE.mkdir(parents=True, exist_ok=True)
    tag = f"{key}_e{epochs}_lr{lr:g}_s{stride_time}_w{width}_h{hidden}_seed{seed}.pt"
    path = CACHE / tag
    if path.exists() and not force:
        return asr.Recognizer.load(path)

    if train_records is None or val_records is None:
        splits, _ = speech_splits()
        train_records = splits["train"]
        val_records = splits["val"]
    started = time.perf_counter()
    rec, history = asr.Recognizer.train(
        train_records,
        val_records,
        epochs=epochs,
        seed=seed,
        lr=lr,
        stride_time=stride_time,
        width=width,
        hidden=hidden,
        log=log,
    )
    rec.meta["wall_seconds"] = round(time.perf_counter() - started, 2)
    rec.save(path)
    return rec


def wer_of(rec, records) -> dict:
    rows = rec.transcribe(records)
    report = text.corpus_error_rates([(r["reference"], r["text"]) for r in rows])
    report["rows"] = rows
    return report
