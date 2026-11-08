"""A small, readable GPT: the model used for pre-training and fine-tuning.

This is deliberately not a scaled-down copy of a production architecture with
hidden tricks. It is the smallest model that still contains every mechanism the
lessons discuss: token and position embeddings, masked self-attention, residual
streams, layer normalisation, an MLP block, and a language-model head with
optional weight tying.

With ``n_layer=2``, ``n_head=4`` and ``n_embd=96`` it trains on a CPU in under a
minute, which is what makes the exercises practical.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class GPTConfig:
    vocab_size: int
    block_size: int = 128
    n_layer: int = 2
    n_head: int = 4
    n_embd: int = 96
    dropout: float = 0.1
    tie_weights: bool = True

    def as_dict(self) -> dict:
        return {
            "vocab_size": self.vocab_size,
            "block_size": self.block_size,
            "n_layer": self.n_layer,
            "n_head": self.n_head,
            "n_embd": self.n_embd,
            "dropout": self.dropout,
            "tie_weights": self.tie_weights,
        }


class CausalSelfAttention(nn.Module):
    """Multi-head self-attention where position ``t`` may only attend to ``<= t``.

    The mask is the whole point. Without it the model can read the next token
    while predicting it, training loss collapses to near zero, and generation
    produces nonsense because the information it relied on is not there yet.
    """

    def __init__(self, config: GPTConfig) -> None:
        super().__init__()
        if config.n_embd % config.n_head:
            raise ValueError("n_embd must be divisible by n_head")
        self.n_head = config.n_head
        self.head_dim = config.n_embd // config.n_head
        self.c_attn = nn.Linear(config.n_embd, 3 * config.n_embd)
        self.c_proj = nn.Linear(config.n_embd, config.n_embd)
        self.attn_dropout = nn.Dropout(config.dropout)
        self.resid_dropout = nn.Dropout(config.dropout)
        mask = torch.tril(torch.ones(config.block_size, config.block_size, dtype=torch.bool))
        self.register_buffer("mask", mask.view(1, 1, config.block_size, config.block_size), persistent=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch, steps, channels = x.shape
        q, k, v = self.c_attn(x).split(channels, dim=2)
        q = q.view(batch, steps, self.n_head, self.head_dim).transpose(1, 2)
        k = k.view(batch, steps, self.n_head, self.head_dim).transpose(1, 2)
        v = v.view(batch, steps, self.n_head, self.head_dim).transpose(1, 2)
        scores = (q @ k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        scores = scores.masked_fill(~self.mask[:, :, :steps, :steps], float("-inf"))
        weights = self.attn_dropout(F.softmax(scores, dim=-1))
        out = weights @ v
        out = out.transpose(1, 2).contiguous().view(batch, steps, channels)
        return self.resid_dropout(self.c_proj(out))


class MLP(nn.Module):
    """Position-wise feed-forward network: expand, non-linearity, project back."""

    def __init__(self, config: GPTConfig) -> None:
        super().__init__()
        self.c_fc = nn.Linear(config.n_embd, 4 * config.n_embd)
        self.c_proj = nn.Linear(4 * config.n_embd, config.n_embd)
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.dropout(self.c_proj(F.gelu(self.c_fc(x))))


class Block(nn.Module):
    """Pre-norm transformer block: normalise, transform, add to the residual stream."""

    def __init__(self, config: GPTConfig) -> None:
        super().__init__()
        self.ln1 = nn.LayerNorm(config.n_embd)
        self.attn = CausalSelfAttention(config)
        self.ln2 = nn.LayerNorm(config.n_embd)
        self.mlp = MLP(config)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.ln1(x))
        return x + self.mlp(self.ln2(x))


class TinyGPT(nn.Module):
    """A causal language model small enough to train on a laptop CPU."""

    def __init__(self, config: GPTConfig) -> None:
        super().__init__()
        self.config = config
        self.token_emb = nn.Embedding(config.vocab_size, config.n_embd)
        self.pos_emb = nn.Embedding(config.block_size, config.n_embd)
        self.drop = nn.Dropout(config.dropout)
        self.blocks = nn.ModuleList(Block(config) for _ in range(config.n_layer))
        self.ln_f = nn.LayerNorm(config.n_embd)
        self.head = nn.Linear(config.n_embd, config.vocab_size, bias=False)
        if config.tie_weights:
            self.head.weight = self.token_emb.weight
        self.apply(self._init_weights)
        # GPT-2 style scaling of residual projections keeps activations stable
        # as depth grows, without changing the architecture.
        for block in self.blocks:
            nn.init.normal_(block.attn.c_proj.weight, mean=0.0, std=0.02 / math.sqrt(2 * config.n_layer))
            nn.init.normal_(block.mlp.c_proj.weight, mean=0.0, std=0.02 / math.sqrt(2 * config.n_layer))

    @staticmethod
    def _init_weights(module: nn.Module) -> None:
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, idx: torch.Tensor, targets: torch.Tensor | None = None):
        _, steps = idx.shape
        if steps > self.config.block_size:
            raise ValueError(f"sequence of {steps} exceeds block_size {self.config.block_size}")
        positions = torch.arange(steps, device=idx.device)
        x = self.drop(self.token_emb(idx) + self.pos_emb(positions))
        for block in self.blocks:
            x = block(x)
        logits = self.head(self.ln_f(x))
        loss = None
        if targets is not None:
            # -100 marks prompt tokens in supervised fine-tuning; they are
            # excluded from the loss rather than trained as targets.
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.reshape(-1), ignore_index=-100)
        return logits, loss

    @torch.no_grad()
    def generate(
        self,
        idx: torch.Tensor,
        max_new_tokens: int = 80,
        *,
        temperature: float = 1.0,
        top_k: int | None = None,
        generator: torch.Generator | None = None,
        stop_ids: tuple[int, ...] = (),
    ) -> torch.Tensor:
        """Append tokens to ``idx``; temperature 0 means greedy decoding."""

        self.eval()
        for _ in range(max_new_tokens):
            window = idx[:, -self.config.block_size :]
            logits, _ = self(window)
            logits = logits[:, -1, :]
            if temperature <= 0:
                next_id = logits.argmax(dim=-1, keepdim=True)
            else:
                logits = logits / max(temperature, 1e-6)
                if top_k is not None:
                    k = min(top_k, logits.size(-1))
                    cutoff = torch.topk(logits, k).values[:, -1].unsqueeze(-1)
                    logits = logits.masked_fill(logits < cutoff, float("-inf"))
                probs = F.softmax(logits, dim=-1)
                next_id = torch.multinomial(probs, num_samples=1, generator=generator)
            idx = torch.cat([idx, next_id], dim=1)
            if stop_ids and int(next_id.item()) in stop_ids:
                break
        return idx

    @property
    def block_size(self) -> int:
        return self.config.block_size

    def parameter_count(self, trainable_only: bool = False) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad or not trainable_only)

    def param_bytes(self, dtype_bytes: int = 4) -> int:
        """Bytes for a dense copy of the unique parameters at ``dtype_bytes`` each."""

        return self.parameter_count() * dtype_bytes


def build_model(vocab_size: int, *, seed: int = 0, **overrides) -> TinyGPT:
    """Construct a model with a fixed seed and optional config overrides."""

    torch.manual_seed(seed)
    config = GPTConfig(vocab_size=vocab_size, **overrides)
    return TinyGPT(config)


__all__ = ["Block", "CausalSelfAttention", "GPTConfig", "MLP", "TinyGPT", "build_model"]
