"""Deterministic teaching data for the language-model units (M06-M08).

The datasets are produced by ``scripts/make_training_data.py`` and are not
committed: they are synthetic, released CC0-1.0, and regenerate byte-for-byte
from a fixed seed. Every function here works offline and never touches the
network, so notebooks that call :func:`ensure_datasets` are restart-and-run
safe on a fresh checkout.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "datasets" / "training" / "generated"
GENERATOR = ROOT / "scripts" / "make_training_data.py"
MANIFEST = DATA_DIR / "manifest.json"


def ensure_datasets(*, force: bool = False, quiet: bool = True) -> Path:
    """Generate the CSV/text files if they are missing, then return their folder."""

    if force or not MANIFEST.exists():
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--out", str(DATA_DIR)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"dataset generation failed:\n{result.stdout}\n{result.stderr}")
        if not quiet:
            print(result.stdout.strip())
    return DATA_DIR


def manifest() -> dict:
    """Rows, columns, and SHA-256 digests recorded by the generator."""

    ensure_datasets()
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def read_rows(name: str) -> list[dict[str, str]]:
    """Read one generated CSV as a list of string dictionaries."""

    path = ensure_datasets() / name
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_text(name: str = "tiny_corpus.txt") -> str:
    return (ensure_datasets() / name).read_text(encoding="utf-8")


def load_corpus() -> str:
    """The small synthetic corpus used for pre-training in M06."""

    return read_text("tiny_corpus.txt")


def load_faq(split: str | None = None) -> list[dict[str, str]]:
    """Instruction pairs: ``question``, ``answer``, ``topic``, ``split``.

    ``train`` has 120 pairs and ``validation``/``test`` have 16 each. Splits are
    disjoint by question template, not by topic: every topic appears in all
    three splits. That makes a held-out score a test of paraphrase robustness,
    not of generalisation to a new subject area.
    """

    rows = read_rows("faq_pairs.csv")
    if split is not None:
        rows = [row for row in rows if row["split"] == split]
        if not rows:
            raise ValueError(f"unknown or empty split: {split!r}")
    return rows


def load_tickets(messy: bool = True) -> list[dict[str, str]]:
    """Support tickets, optionally the messy variant with duplicates and typos."""

    return read_rows("tickets_messy.csv" if messy else "tickets_clean.csv")


def corpus_sentences(text: str | None = None) -> list[str]:
    """Non-empty sentences of the corpus, in file order."""

    raw = load_corpus() if text is None else text
    return [line.strip() for line in raw.splitlines() if line.strip()]


def vocab_preview(text: str | None = None, limit: int = 12) -> dict:
    """A quick character/word summary used in the first notebook section."""

    raw = load_corpus() if text is None else text
    words = raw.split()
    return {
        "characters": len(raw),
        "lines": raw.count("\n"),
        "words": len(words),
        "unique_words": len(set(words)),
        "unique_characters": len(set(raw)),
        "most_common_words": Counter(words).most_common(limit),
    }


__all__ = [
    "DATA_DIR",
    "MANIFEST",
    "ROOT",
    "corpus_sentences",
    "ensure_datasets",
    "load_corpus",
    "load_faq",
    "load_tickets",
    "manifest",
    "read_rows",
    "read_text",
    "vocab_preview",
]
