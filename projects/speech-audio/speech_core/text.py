"""Text normalisation and the error metrics that decide whether an ASR works.

WER is the headline metric of this section and it is easy to compute in a way that
flatters the system:

* averaging per-utterance WER weights a five-word clip the same as a fifty-word one;
* not normalising case/punctuation makes "Yes." and "yes" count as a substitution;
* dropping empty references makes deletions vanish from the denominator.

``corpus_error_rates`` computes totals over the whole corpus, which is the convention
that avoids all three.
"""

from __future__ import annotations

import re
import string
from dataclasses import dataclass
from typing import Iterable, Sequence

_PUNCT = str.maketrans({c: " " for c in string.punctuation})
_WS = re.compile(r"\s+")


def normalize_text(text: str, keep_case: bool = False) -> str:
    """Lowercase, strip punctuation, collapse whitespace.

    Deliberately conservative: no number-to-word expansion and no spell correction,
    because both hide errors that the metric is supposed to reveal.
    """
    out = str(text).translate(_PUNCT)
    out = _WS.sub(" ", out).strip()
    return out if keep_case else out.lower()


def words(text: str) -> list[str]:
    normalised = normalize_text(text)
    return normalised.split() if normalised else []


@dataclass
class EditCounts:
    substitutions: int = 0
    insertions: int = 0
    deletions: int = 0
    matches: int = 0

    @property
    def errors(self) -> int:
        return self.substitutions + self.insertions + self.deletions

    def as_dict(self) -> dict:
        return {
            "substitutions": self.substitutions,
            "insertions": self.insertions,
            "deletions": self.deletions,
            "matches": self.matches,
            "errors": self.errors,
        }


def edit_operations(reference: Sequence[str], hypothesis: Sequence[str]) -> EditCounts:
    """Levenshtein alignment with the operation mix, not just the distance.

    The mix is what tells you *what to fix*: substitutions point at acoustics,
    deletions at recall (speech dropped), insertions at spurious detections.
    """
    n, m = len(reference), len(hypothesis)
    cost = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        cost[i][0] = i
    for j in range(m + 1):
        cost[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            same = reference[i - 1] == hypothesis[j - 1]
            cost[i][j] = min(
                cost[i - 1][j] + 1,  # deletion
                cost[i][j - 1] + 1,  # insertion
                cost[i - 1][j - 1] + (0 if same else 1),  # match or substitution
            )
    counts = EditCounts()
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and reference[i - 1] == hypothesis[j - 1] and cost[i][j] == cost[i - 1][j - 1]:
            counts.matches += 1
            i, j = i - 1, j - 1
        elif i > 0 and j > 0 and cost[i][j] == cost[i - 1][j - 1] + 1:
            counts.substitutions += 1
            i, j = i - 1, j - 1
        elif i > 0 and cost[i][j] == cost[i - 1][j] + 1:
            counts.deletions += 1
            i -= 1
        else:
            counts.insertions += 1
            j -= 1
    return counts


def word_error_rate(reference: str, hypothesis: str) -> dict:
    """WER for one pair, with the raw counts attached."""
    ref, hyp = words(reference), words(hypothesis)
    counts = edit_operations(ref, hyp)
    denominator = max(len(ref), 1)
    return {
        "wer": counts.errors / denominator,
        "reference_words": len(ref),
        "hypothesis_words": len(hyp),
        **counts.as_dict(),
    }


def character_error_rate(reference: str, hypothesis: str) -> dict:
    ref = list(normalize_text(reference).replace(" ", ""))
    hyp = list(normalize_text(hypothesis).replace(" ", ""))
    counts = edit_operations(ref, hyp)
    return {"cer": counts.errors / max(len(ref), 1), **counts.as_dict(), "reference_chars": len(ref)}


def corpus_error_rates(pairs: Iterable[tuple[str, str]]) -> dict:
    """Aggregate WER/CER over (reference, hypothesis) pairs.

    Total errors divided by total reference words. This is the only version that
    is comparable across systems evaluated on the same corpus.
    """
    totals = EditCounts()
    char_totals = EditCounts()
    ref_words = hyp_words = ref_chars = 0
    n = 0
    worst: list[dict] = []
    for reference, hypothesis in pairs:
        ref, hyp = words(reference), words(hypothesis)
        counts = edit_operations(ref, hyp)
        totals.substitutions += counts.substitutions
        totals.insertions += counts.insertions
        totals.deletions += counts.deletions
        totals.matches += counts.matches
        ref_words += len(ref)
        hyp_words += len(hyp)
        ref_chars += len(normalize_text(reference).replace(" ", ""))
        char_counts = edit_operations(
            list(normalize_text(reference).replace(" ", "")), list(normalize_text(hypothesis).replace(" ", ""))
        )
        char_totals.substitutions += char_counts.substitutions
        char_totals.insertions += char_counts.insertions
        char_totals.deletions += char_counts.deletions
        char_totals.matches += char_counts.matches
        n += 1
        worst.append(
            {
                "reference": reference,
                "hypothesis": hypothesis,
                "wer": counts.errors / max(len(ref), 1),
                **counts.as_dict(),
            }
        )
    worst.sort(key=lambda row: row["wer"], reverse=True)
    return {
        "wer": totals.errors / max(ref_words, 1),
        "cer": char_totals.errors / max(ref_chars, 1),
        "reference_chars": ref_chars,
        "char_substitutions": char_totals.substitutions,
        "char_insertions": char_totals.insertions,
        "char_deletions": char_totals.deletions,
        "substitutions": totals.substitutions,
        "insertions": totals.insertions,
        "deletions": totals.deletions,
        "reference_words": ref_words,
        "hypothesis_words": hyp_words,
        "n_utterances": n,
        "sentence_accuracy": sum(1 for row in worst if row["errors"] == 0) / max(n, 1),
        "worst": worst[:5],
    }


def confusion_pairs(pairs: Iterable[tuple[str, str]], top: int = 10) -> list[tuple[str, str, int]]:
    """Most frequent (reference, hypothesis) word substitutions across a corpus."""
    counts: dict[tuple[str, str], int] = {}
    for reference, hypothesis in pairs:
        ref, hyp = words(reference), words(hypothesis)
        n, m = len(ref), len(hyp)
        cost = [[0] * (m + 1) for _ in range(n + 1)]
        for i in range(n + 1):
            cost[i][0] = i
        for j in range(m + 1):
            cost[0][j] = j
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost[i][j] = min(
                    cost[i - 1][j] + 1,
                    cost[i][j - 1] + 1,
                    cost[i - 1][j - 1] + (0 if ref[i - 1] == hyp[j - 1] else 1),
                )
        i, j = n, m
        while i > 0 and j > 0:
            if ref[i - 1] == hyp[j - 1] and cost[i][j] == cost[i - 1][j - 1]:
                i, j = i - 1, j - 1
            elif cost[i][j] == cost[i - 1][j - 1] + 1:
                key = (ref[i - 1], hyp[j - 1])
                counts[key] = counts.get(key, 0) + 1
                i, j = i - 1, j - 1
            elif cost[i][j] == cost[i - 1][j] + 1:
                i -= 1
            else:
                j -= 1
    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return [(ref, hyp, count) for (ref, hyp), count in ranked[:top]]


# ---------------------------------------------------------------------------
# Character vocabulary for CTC
# ---------------------------------------------------------------------------


def build_char_vocab(transcripts: Sequence[str]) -> list[str]:
    """CTC vocabulary: blank at index 0, then sorted unique characters."""
    chars = sorted({c for text in transcripts for c in normalize_text(text) if c != " "})
    return ["<blank>", *chars]


def encode_transcript(text: str, vocab: Sequence[str]) -> list[int]:
    index = {c: i for i, c in enumerate(vocab)}
    return [index[c] for c in normalize_text(text) if c in index and c != " "]


def decode_indices(indices: Sequence[int], vocab: Sequence[str]) -> str:
    return "".join(vocab[i] for i in indices if 0 < i < len(vocab))
