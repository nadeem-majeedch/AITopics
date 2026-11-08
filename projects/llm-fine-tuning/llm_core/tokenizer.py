"""Three tokenizers, from the simplest possible to a small byte-pair encoder.

The point of having all three in one file is comparison. A character tokenizer
has a tiny vocabulary and long sequences; a word tokenizer has a large
vocabulary and short sequences; byte-pair encoding sits in between and is what
production models actually use. Every class exposes ``encode``, ``decode`` and a
vocabulary size, so the rest of the package can swap them without changes.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

WORD_PATTERN = re.compile(r"[A-Za-z0-9']+|[^\sA-Za-z0-9]")
PUNCTUATION = ".,!?;:"


@dataclass
class CharTokenizer:
    """One id per character, plus ``<pad>``/``<unk>``.

    Character tokenizers are the right teaching choice for a from-scratch model:
    the vocabulary is small enough to train on a CPU in seconds, and every
    generated token is a readable character. They are the wrong choice for
    production because a sentence becomes hundreds of steps and the model has
    to relearn spelling from scratch.
    """

    vocab: tuple[str, ...] = ()
    pad_id: int = 0
    unk_id: int = 1
    stoi: dict[str, int] = field(default_factory=dict, repr=False)

    @classmethod
    def from_text(cls, text: str, min_count: int = 1) -> "CharTokenizer":
        counts = Counter(text)
        kept = sorted(char for char, count in counts.items() if count >= min_count)
        vocab = ("<pad>", "<unk>", *kept)
        tokenizer = cls(vocab=vocab)
        tokenizer.stoi = {char: index for index, char in enumerate(vocab)}
        return tokenizer

    def __len__(self) -> int:
        return len(self.vocab)

    @property
    def vocab_size(self) -> int:
        return len(self.vocab)

    def encode(self, text: str) -> list[int]:
        return [self.stoi.get(char, self.unk_id) for char in text]

    def decode(self, ids) -> str:
        chars = []
        for index in ids:
            index = int(index)
            if index == self.pad_id:
                continue
            chars.append("?" if index == self.unk_id else self.vocab[index])
        return "".join(chars)


@dataclass
class WordTokenizer:
    """One id per whitespace word, with punctuation kept as its own token."""

    vocab: tuple[str, ...] = ()
    pad_id: int = 0
    unk_id: int = 1
    lowercase: bool = True
    stoi: dict[str, int] = field(default_factory=dict, repr=False)

    @classmethod
    def from_text(cls, text: str, min_count: int = 1, lowercase: bool = True) -> "WordTokenizer":
        counts = Counter(_words(text, lowercase))
        kept = sorted(word for word, count in counts.items() if count >= min_count)
        vocab = ("<pad>", "<unk>", *kept)
        tokenizer = cls(vocab=vocab, lowercase=lowercase)
        tokenizer.stoi = {word: index for index, word in enumerate(vocab)}
        return tokenizer

    def __len__(self) -> int:
        return len(self.vocab)

    @property
    def vocab_size(self) -> int:
        return len(self.vocab)

    def encode(self, text: str) -> list[int]:
        return [self.stoi.get(word, self.unk_id) for word in _words(text, self.lowercase)]

    def decode(self, ids) -> str:
        words = []
        for index in ids:
            index = int(index)
            if index == self.pad_id:
                continue
            words.append("<unk>" if index == self.unk_id else self.vocab[index])
        text = " ".join(words)
        return re.sub(r"\s+([.,!?;:])", r"\1", text)


def _words(text: str, lowercase: bool = True) -> list[str]:
    return WORD_PATTERN.findall(text.lower() if lowercase else text)


@dataclass
class BPETokenizer:
    """A minimal byte-level byte-pair encoder.

    Training starts from the 256 possible bytes and repeatedly merges the most
    frequent adjacent pair. Merging the *most frequent* pair is what makes the
    vocabulary efficient: common words become one or two tokens, while rare
    words fall back to smaller pieces instead of an ``<unk>`` token.
    """

    merges: list[tuple[int, int]] = field(default_factory=list)
    vocab_size: int = 256
    pad_id: int = 0
    unk_id: int = 1

    def __post_init__(self) -> None:
        self.ranks: dict[tuple[int, int], int] = {pair: index for index, pair in enumerate(self.merges)}
        table = {index: bytes([index]) for index in range(256)}
        for index, (left, right) in enumerate(self.merges):
            table[256 + index] = table[left] + table[right]
        self.table = table

    def __len__(self) -> int:
        return 256 + len(self.merges)

    @classmethod
    def train(cls, text: str, vocab_size: int = 300, *, verbose: bool = False) -> "BPETokenizer":
        if vocab_size < 257:
            raise ValueError("vocab_size must be at least 257 to hold the bytes and one merge")
        ids = list(text.encode("utf-8"))
        merges: list[tuple[int, int]] = []
        for step in range(vocab_size - 256):
            counts = Counter(zip(ids, ids[1:]))
            if not counts:
                break
            # Highest count first; ties broken by the smaller pair so the result
            # is reproducible across Python versions.
            pair = max(counts.items(), key=lambda item: (item[1], -item[0][0], -item[0][1]))[0]
            if counts[pair] < 2:
                break
            new_id = 256 + step
            merged: list[int] = []
            index = 0
            while index < len(ids):
                if index + 1 < len(ids) and (ids[index], ids[index + 1]) == pair:
                    merged.append(new_id)
                    index += 2
                else:
                    merged.append(ids[index])
                    index += 1
            ids = merged
            merges.append(pair)
            if verbose and (step + 1) % 50 == 0:
                print(f"merge {step + 1:4d}  pair {pair}  tokens left {len(ids)}")
        tokenizer = cls(merges=merges)
        tokenizer.vocab_size = len(tokenizer)
        return tokenizer

    def encode(self, text: str) -> list[int]:
        ids = list(text.encode("utf-8"))
        while len(ids) >= 2:
            candidates = [
                (self.ranks[(ids[index], ids[index + 1])], index)
                for index in range(len(ids) - 1)
                if (ids[index], ids[index + 1]) in self.ranks
            ]
            if not candidates:
                break
            rank, index = min(candidates)
            ids[index : index + 2] = [256 + rank]
        return ids

    def decode(self, ids) -> str:
        raw = b"".join(self.table[int(index)] for index in ids if int(index) in self.table)
        return raw.decode("utf-8", errors="replace")


def tokenizer_report(tokenizer, text: str) -> dict:
    """Sequence length, vocabulary size, and characters per token."""

    ids = tokenizer.encode(text)
    return {
        "name": type(tokenizer).__name__,
        "vocab_size": len(tokenizer),
        "tokens": len(ids),
        "characters": len(text),
        "chars_per_token": round(len(text) / max(1, len(ids)), 2),
    }


__all__ = ["BPETokenizer", "CharTokenizer", "WordTokenizer", "tokenizer_report"]
