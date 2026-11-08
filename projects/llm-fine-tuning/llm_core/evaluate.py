"""Measurement helpers: perplexity, answer overlap, diversity, and generation.

Every function here returns a number the lessons can quote. Nothing is estimated
from intuition: if a notebook says a tuned model scored higher, the number came
from one of these functions on a held-out split.
"""

from __future__ import annotations

import math
import re
from collections import Counter

import torch

from .tokenizer import tokenizer_report

TOKEN_RE = re.compile(r"[a-z0-9']+")


def perplexity(loss: float) -> float:
    """``exp(cross-entropy)``: the effective number of equally likely next tokens."""

    return math.exp(min(loss, 20.0))


def bits_per_token(loss: float) -> float:
    return loss / math.log(2)


def normalize_text(text: str) -> str:
    return " ".join(TOKEN_RE.findall(text.lower()))


def word_f1(prediction: str, reference: str) -> float:
    """Bag-of-words F1, the standard cheap check for short-answer generation.

    It rewards producing the right content words and ignores word order, so it is
    a weak metric - a shuffled answer can score well. It is used here because it
    is honest about a tiny model: exact match would be zero for almost everything
    and would tell the reader nothing about whether fine-tuning helped.
    """

    predicted = Counter(normalize_text(prediction).split())
    actual = Counter(normalize_text(reference).split())
    if not predicted or not actual:
        return 0.0
    overlap = sum((predicted & actual).values())
    precision = overlap / sum(predicted.values())
    recall = overlap / sum(actual.values())
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def exact_match(prediction: str, reference: str) -> float:
    return float(normalize_text(prediction) == normalize_text(reference))


def generation_report(predictions, references) -> dict:
    """Separate free-running generation quality from teacher-forced token accuracy.

    ``predictions`` and ``references`` are equal-length sequences of strings.
    Exact match is deliberately strict; word F1 and the empty/repetition rates
    describe *why* a model that predicts many answer tokens correctly still
    produces poor prose. Answer-token accuracy belongs to ``masked_accuracy``
    and must be reported separately: it gives the model the true prefix.
    """

    predictions = list(predictions)
    references = list(references)
    if len(predictions) != len(references):
        raise ValueError("predictions and references must have the same length")
    if not predictions:
        raise ValueError("generation report needs at least one example")
    rows = [
        {
            "exact_match": exact_match(prediction, reference),
            "word_f1": word_f1(prediction, reference),
            "empty": not prediction.strip(),
            "chars": len(prediction),
            "repetition_3": repetition_rate(prediction),
        }
        for prediction, reference in zip(predictions, references)
    ]
    return {
        "n": len(rows),
        "exact_match": round(mean(row["exact_match"] for row in rows), 4),
        "mean_word_f1": round(mean(row["word_f1"] for row in rows), 4),
        "empty_rate": round(mean(row["empty"] for row in rows), 4),
        "mean_chars": round(mean(row["chars"] for row in rows), 1),
        "mean_repetition_3": round(mean(row["repetition_3"] for row in rows), 4),
    }


def distinct_n(texts: list[str], n: int = 2) -> float:
    """Unique n-grams divided by all n-grams: low values mean repetition."""

    grams = []
    for text in texts:
        tokens = normalize_text(text).split()
        grams.extend(tuple(tokens[index : index + n]) for index in range(len(tokens) - n + 1))
    if not grams:
        return 0.0
    return len(set(grams)) / len(grams)


def repetition_rate(text: str, n: int = 3) -> float:
    """Share of n-grams that occur more than once."""

    tokens = normalize_text(text).split()
    grams = [tuple(tokens[index : index + n]) for index in range(len(tokens) - n + 1)]
    if not grams:
        return 0.0
    repeated = sum(count - 1 for count in Counter(grams).values() if count > 1)
    return repeated / len(grams)


def tokenizer_comparison(tokenizers: dict, text: str) -> list[dict]:
    """Vocabulary/sequence-length trade-off for several tokenizers on one text."""

    rows = []
    for name, tokenizer in tokenizers.items():
        row = tokenizer_report(tokenizer, text)
        row["name"] = name
        rows.append(row)
    return rows


@torch.no_grad()
def generate_text(
    model,
    tokenizer,
    prompt: str,
    *,
    max_new_tokens: int = 80,
    temperature: float = 0.0,
    top_k: int | None = None,
    seed: int | None = None,
    stop_ids: tuple[int, ...] = (),
) -> str:
    """Generate a continuation and return only the new text.

    ``temperature=0`` is greedy decoding: deterministic, and the right default
    for evaluation. Sampling with a seed is for demonstrations.
    """

    ids = tokenizer.encode(prompt)
    if not ids:
        raise ValueError("prompt encodes to no tokens")
    idx = torch.tensor([ids], dtype=torch.long)
    generator = None if seed is None else torch.Generator().manual_seed(seed)
    out = model.generate(
        idx,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_k=top_k,
        generator=generator,
        stop_ids=stop_ids,
    )
    new_ids = out[0, len(ids) :].tolist()
    return tokenizer.decode(new_ids)


def generate_answer(model, tokenizer, question: str, **kwargs) -> str:
    """Greedy answer for one FAQ question, cut at the first newline.

    The newline is both a training terminator and a stop token for character
    models. Stopping during generation avoids spending the whole token budget
    after the answer has already ended; the post-hoc split remains for tokenizers
    that do not encode whitespace as a token.
    """

    from .sft import format_prompt

    newline_ids = tuple(tokenizer.encode("\n"))
    text = generate_text(
        model,
        tokenizer,
        format_prompt(question),
        stop_ids=newline_ids,
        **kwargs,
    )
    return text.split("\n")[0].strip()


@torch.no_grad()
def masked_accuracy(model, examples, *, pad_id: int, batch_size: int = 16, first_k: int | None = None) -> float:
    """Share of answer tokens the model predicts correctly when teacher-forced.

    This is the honest primary metric for a tiny fine-tuned model. It asks, at
    each answer position, whether the correct next token had the highest score,
    given the true prefix. Free-running generation compounds one mistake into
    many, so exact-match on generated answers is near zero at this scale and
    says more about decoding than about learning.
    """

    from .sft import pad_batch

    model.eval()
    correct = 0
    total = 0
    for start in range(0, len(examples), batch_size):
        x, y = pad_batch(examples[start : start + batch_size], pad_id)
        logits, _ = model(x)
        predictions = logits.argmax(dim=-1)
        mask = y != -100
        if first_k is not None:
            # Only the first ``first_k`` answer tokens of each example: the ones
            # that decide whether the model has learned the response format.
            rank = torch.cumsum(mask.int(), dim=1)
            mask = mask & (rank <= first_k)
        correct += int((predictions[mask] == y[mask]).sum())
        total += int(mask.sum())
    return correct / max(1, total)


def mean(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def format_table(rows: list[dict], columns: list[str]) -> str:
    """A plain-text table, because notebooks should not need pandas to print."""

    widths = {column: max(len(column), *(len(str(row.get(column, ""))) for row in rows)) for column in columns}
    header = "  ".join(column.ljust(widths[column]) for column in columns)
    rule = "  ".join("-" * widths[column] for column in columns)
    lines = [header, rule]
    for row in rows:
        lines.append("  ".join(str(row.get(column, "")).ljust(widths[column]) for column in columns))
    return "\n".join(lines)


__all__ = [
    "bits_per_token",
    "distinct_n",
    "exact_match",
    "format_table",
    "generation_report",
    "generate_answer",
    "generate_text",
    "masked_accuracy",
    "mean",
    "normalize_text",
    "perplexity",
    "repetition_rate",
    "tokenizer_comparison",
    "word_f1",
]
