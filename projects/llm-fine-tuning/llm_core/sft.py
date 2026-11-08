"""Supervised fine-tuning: chat templates, prompt masking, and the SFT loop.

Supervised fine-tuning teaches a pre-trained language model a *behaviour*: given
a user turn, produce an assistant turn. The model already knows how to continue
text; what it does not know is where the answer starts and which tokens it is
supposed to be learning from.

That is what prompt masking fixes. The user's question stays in the input, but
its tokens are labelled ``-100`` so the cross-entropy loss ignores them. Only the
assistant's answer contributes to the gradient.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import torch

from .train import History, lr_at

SYSTEM_PROMPT = "You are the Northwind Bikes support assistant. Answer briefly and factually."
ASSISTANT_PREFIX = "Assistant:"


@dataclass
class SFTExample:
    input_ids: list[int]
    labels: list[int]
    prompt_tokens: int
    prompt_truncated: bool = False
    answer_truncated: bool = False

    @property
    def answer_tokens(self) -> int:
        return sum(1 for label in self.labels if label != -100)


def format_prompt(question: str) -> str:
    """The exact string the model sees at inference time."""

    return f"User: {question.strip()}\n{ASSISTANT_PREFIX}"


def format_example(question: str, answer: str) -> str:
    """Prompt plus answer, in the same layout as :func:`format_prompt`."""

    return f"{format_prompt(question)} {answer.strip()}\n"


def build_example(question: str, answer: str, tokenizer, block_size: int = 192) -> SFTExample:
    """Tokenise one pair, shift targets, and mask every prompt token.

    A causal language model at position ``t`` predicts token ``t + 1``. The
    labels therefore start at the token *after* the last prompt token: the first
    answer token is predicted from the prompt, and every earlier prompt position
    is excluded with ``-100``. Forgetting this shift trains the model to copy its
    input, which produces a suspiciously tiny loss and degenerate generation.

    Both sides are bounded by ``block_size``. A prompt longer than half the block
    loses its oldest tokens (its end is kept, including the assistant prefix), so
    an unusually long ticket cannot crowd the answer out or produce a sequence
    the model cannot accept. The flags on the returned example record whether
    truncation happened; project code should count them rather than hide them.
    """

    if block_size < 2:
        raise ValueError("block_size must leave room for at least one prompt and one answer token")
    prompt_ids = tokenizer.encode(format_prompt(question))
    answer_ids = tokenizer.encode(" " + answer.strip() + "\n")

    prompt_budget = max(1, block_size // 2)
    prompt_truncated = len(prompt_ids) > prompt_budget
    if prompt_truncated:
        prompt_ids = prompt_ids[-prompt_budget:]

    answer_budget = max(1, block_size - len(prompt_ids))
    answer_truncated = len(answer_ids) > answer_budget
    if answer_truncated:
        answer_ids = answer_ids[:answer_budget]

    tokens = prompt_ids + answer_ids
    full_labels = [-100] * len(prompt_ids) + list(answer_ids)
    input_ids = tokens[:-1]
    labels = full_labels[1:]
    return SFTExample(
        input_ids=input_ids,
        labels=labels,
        prompt_tokens=len(prompt_ids),
        prompt_truncated=prompt_truncated,
        answer_truncated=answer_truncated,
    )


def build_examples(pairs, tokenizer, block_size: int = 192) -> list[SFTExample]:
    return [build_example(pair["question"], pair["answer"], tokenizer, block_size) for pair in pairs]


def prompt_fraction(examples: list[SFTExample]) -> float:
    """Share of tokens that are masked. A sanity check, not a goal."""

    total = sum(len(example.labels) for example in examples)
    masked = sum(1 for example in examples for label in example.labels if label == -100)
    return round(masked / max(1, total), 3)


def pad_batch(examples: list[SFTExample], pad_id: int):
    """Right-pad a fixed list of examples; used by collate and by evaluation."""

    width = max(len(example.input_ids) for example in examples)
    x = torch.full((len(examples), width), pad_id, dtype=torch.long)
    y = torch.full((len(examples), width), -100, dtype=torch.long)
    for row, example in enumerate(examples):
        length = len(example.input_ids)
        x[row, :length] = torch.tensor(example.input_ids, dtype=torch.long)
        y[row, :length] = torch.tensor(example.labels, dtype=torch.long)
    return x, y


def collate(examples: list[SFTExample], batch_size: int, pad_id: int, generator: torch.Generator):
    """Sample a batch, right-pad it, and keep padding out of the loss."""

    indices = torch.randint(0, len(examples), (batch_size,), generator=generator).tolist()
    return pad_batch([examples[index] for index in indices], pad_id)
@torch.no_grad()
def estimate_sft_loss(
    model: torch.nn.Module,
    examples: list[SFTExample],
    *,
    pad_id: int,
    batch_size: int = 8,
    batches: int = 8,
    seed: int = 1234,
) -> float:
    model.eval()
    generator = torch.Generator().manual_seed(seed)
    total = 0.0
    for _ in range(batches):
        x, y = collate(examples, batch_size, pad_id, generator)
        _, loss = model(x, y)
        total += float(loss.item())
    model.train()
    return total / batches


def train_sft(
    model: torch.nn.Module,
    examples: list[SFTExample],
    *,
    steps: int = 150,
    batch_size: int = 8,
    lr: float = 1e-3,
    seed: int = 0,
    pad_id: int = 0,
    log_every: int = 25,
    eval_examples: list[SFTExample] | None = None,
    eval_every: int = 0,
    weight_decay: float = 0.01,
    grad_clip: float = 1.0,
    warmup: int = 10,
    min_lr_ratio: float = 0.1,
) -> History:
    """Fine-tune on masked examples, reporting only answer-token loss."""

    if not examples:
        raise ValueError("no SFT examples")
    generator = torch.Generator().manual_seed(seed)
    torch.manual_seed(seed)
    parameters = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(parameters, lr=lr, weight_decay=weight_decay)
    history = History()
    started = time.perf_counter()
    model.train()
    for step in range(steps):
        current_lr = lr_at(step, steps, lr, warmup=warmup, min_ratio=min_lr_ratio)
        for group in optimizer.param_groups:
            group["lr"] = current_lr
        x, y = collate(examples, batch_size, pad_id, generator)
        optimizer.zero_grad(set_to_none=True)
        _, loss = model(x, y)
        loss.backward()
        if grad_clip > 0:
            torch.nn.utils.clip_grad_norm_(parameters, grad_clip)
        optimizer.step()

        history.tokens += int((y != -100).sum())
        if step % log_every == 0 or step == steps - 1:
            history.losses.append(float(loss.item()))
            history.steps_logged.append(step + 1)
            history.learning_rates.append(round(current_lr, 6))
        if eval_examples is not None and eval_every and (step + 1) % eval_every == 0:
            history.evals.append(
                (
                    step + 1,
                    estimate_sft_loss(model, eval_examples, pad_id=pad_id, batch_size=batch_size),
                )
            )
    history.seconds = time.perf_counter() - started
    return history


__all__ = [
    "ASSISTANT_PREFIX",
    "SFTExample",
    "SYSTEM_PROMPT",
    "build_example",
    "build_examples",
    "collate",
    "estimate_sft_loss",
    "format_example",
    "format_prompt",
    "pad_batch",
    "prompt_fraction",
    "train_sft",
]
