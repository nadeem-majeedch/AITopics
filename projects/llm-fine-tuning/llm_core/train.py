"""Pre-training loop, learning-rate schedule, and loss estimation.

The loop is intentionally explicit: batching, the forward pass, backpropagation,
gradient clipping, the schedule, and bookkeeping are all visible. Reading it once
is meant to be enough to explain every number a training run reports.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

import torch


@dataclass
class History:
    """What a run actually measured.

    ``losses`` holds the most recent mini-batch loss at each logging step, not a
    smoothed epoch average. ``evals`` holds held-out losses measured with the
    model in evaluation mode.
    """

    losses: list[float] = field(default_factory=list)
    steps_logged: list[int] = field(default_factory=list)
    learning_rates: list[float] = field(default_factory=list)
    evals: list[tuple[int, float]] = field(default_factory=list)
    seconds: float = 0.0
    tokens: int = 0

    def summary(self) -> dict:
        if not self.losses:
            return {"steps": 0}
        return {
            "steps": self.steps_logged[-1],
            "first_loss": round(self.losses[0], 4),
            "last_loss": round(self.losses[-1], 4),
            "seconds": round(self.seconds, 2),
            "tokens": self.tokens,
            "tokens_per_second": round(self.tokens / max(self.seconds, 1e-9)),
            "evals": [(step, round(loss, 4)) for step, loss in self.evals],
        }


def lr_at(step: int, total_steps: int, base_lr: float, *, warmup: int = 10, min_ratio: float = 0.1) -> float:
    """Linear warm-up followed by cosine decay to ``min_ratio * base_lr``.

    Warm-up matters at the start of training, when the loss surface is steep and
    a full-size step can destroy the randomly initialised weights. The cosine
    tail lets the model settle instead of bouncing around the minimum.
    """

    if warmup > 0 and step < warmup:
        return base_lr * (step + 1) / warmup
    progress = (step - warmup) / max(1, total_steps - warmup)
    progress = min(max(progress, 0.0), 1.0)
    return base_lr * (min_ratio + (1.0 - min_ratio) * 0.5 * (1.0 + math.cos(math.pi * progress)))


def get_batch(data: torch.Tensor, batch_size: int, block_size: int, generator: torch.Generator):
    """Sample ``batch_size`` random windows and their one-token-shifted targets."""

    if not isinstance(data, torch.Tensor):
        data = torch.as_tensor(list(data), dtype=torch.long)
    if len(data) <= block_size + 1:
        raise ValueError(f"need more than {block_size + 1} tokens, got {len(data)}")
    starts = torch.randint(0, len(data) - block_size - 1, (batch_size,), generator=generator)
    x = torch.stack([data[start : start + block_size] for start in starts])
    y = torch.stack([data[start + 1 : start + block_size + 1] for start in starts])
    return x, y


@torch.no_grad()
def estimate_loss(
    model: torch.nn.Module,
    data: torch.Tensor,
    *,
    batch_size: int = 16,
    block_size: int = 128,
    batches: int = 8,
    seed: int = 1234,
) -> float:
    """Average cross-entropy over fixed random windows (deterministic).

    The seed is fixed so two evaluations of the same weights are comparable; a
    fresh random draw each time would add noise exactly where the comparison is
    supposed to be precise.
    """

    model.eval()
    generator = torch.Generator().manual_seed(seed)
    total = 0.0
    for _ in range(batches):
        x, y = get_batch(data, batch_size, block_size, generator)
        _, loss = model(x, y)
        total += float(loss.item())
    model.train()
    return total / batches


def train_lm(
    model: torch.nn.Module,
    token_ids,
    *,
    steps: int = 200,
    batch_size: int = 16,
    block_size: int = 128,
    lr: float = 3e-3,
    seed: int = 0,
    log_every: int = 25,
    eval_ids=None,
    eval_every: int = 0,
    eval_batches: int = 8,
    weight_decay: float = 0.01,
    grad_clip: float = 1.0,
    warmup: int = 10,
    min_lr_ratio: float = 0.1,
) -> History:
    """Train a causal LM on a flat token stream and return measured history."""

    data = torch.as_tensor(list(token_ids), dtype=torch.long)
    eval_data = None if eval_ids is None else torch.as_tensor(list(eval_ids), dtype=torch.long)
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

        x, y = get_batch(data, batch_size, block_size, generator)
        optimizer.zero_grad(set_to_none=True)
        _, loss = model(x, y)
        loss.backward()
        if grad_clip > 0:
            torch.nn.utils.clip_grad_norm_(parameters, grad_clip)
        optimizer.step()

        history.tokens += int(x.numel())
        if step % log_every == 0 or step == steps - 1:
            history.losses.append(float(loss.item()))
            history.steps_logged.append(step + 1)
            history.learning_rates.append(round(current_lr, 6))

        if eval_data is not None and eval_every and (step + 1) % eval_every == 0:
            history.evals.append(
                (step + 1, estimate_loss(model, eval_data, batch_size=batch_size, block_size=block_size, batches=eval_batches))
            )

    history.seconds = time.perf_counter() - started
    return history


__all__ = ["History", "estimate_loss", "get_batch", "lr_at", "train_lm"]
