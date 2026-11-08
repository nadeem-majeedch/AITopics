"""Low-rank adaptation (LoRA), written out rather than imported.

LoRA freezes every original weight and learns two small matrices per adapted
layer. For a ``d -> d`` projection with rank ``r``, the adapter has
``r * (d_in + d_out)`` parameters instead of ``d_in * d_out``, and the update is
scaled by ``alpha / r`` so changing the rank does not silently change the
effective learning rate.

    W' = W + (alpha / r) * B @ A

``B`` starts at zero, so at step 0 the adapted model is exactly the base model.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class LoRALinear(nn.Module):
    """A frozen ``nn.Linear`` plus a trainable low-rank update."""

    def __init__(self, base: nn.Linear, rank: int = 4, alpha: float = 8.0) -> None:
        super().__init__()
        if rank <= 0:
            raise ValueError("rank must be positive")
        self.base = base
        for parameter in self.base.parameters():
            parameter.requires_grad = False
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank
        self.lora_A = nn.Linear(base.in_features, rank, bias=False)
        self.lora_B = nn.Linear(rank, base.out_features, bias=False)
        nn.init.normal_(self.lora_A.weight, mean=0.0, std=0.02)
        nn.init.zeros_(self.lora_B.weight)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.base(x) + self.lora_B(self.lora_A(x)) * self.scaling

    @torch.no_grad()
    def merged_weight(self) -> torch.Tensor:
        delta = self.lora_B.weight @ self.lora_A.weight
        return self.base.weight + delta * self.scaling


def apply_lora(
    model: nn.Module,
    *,
    rank: int = 4,
    alpha: float = 8.0,
    targets: tuple[str, ...] = ("c_attn", "c_proj"),
    freeze_base: bool = True,
) -> dict:
    """Replace matching ``nn.Linear`` modules in place and report the result."""

    replaced: list[str] = []
    for name, module in list(model.named_modules()):
        if not isinstance(module, nn.Linear):
            continue
        leaf = name.rsplit(".", 1)[-1]
        if leaf not in targets:
            continue
        parent_name, _, attribute = name.rpartition(".")
        parent = model.get_submodule(parent_name) if parent_name else model
        setattr(parent, attribute, LoRALinear(module, rank=rank, alpha=alpha))
        replaced.append(name)
    if not replaced:
        raise ValueError(f"no linear layers matched targets {targets}")
    if freeze_base:
        freeze_except_lora(model)
    trainable, total = trainable_parameters(model)
    return {
        "replaced": replaced,
        "rank": rank,
        "alpha": alpha,
        "trainable_parameters": trainable,
        "total_parameters": total,
        "trainable_fraction": round(trainable / total, 4),
    }


def freeze_except_lora(model: nn.Module) -> int:
    """Freeze everything except adapter weights, as LoRA training normally does."""

    frozen = 0
    for name, parameter in model.named_parameters():
        wants_grad = "lora_" in name
        parameter.requires_grad = wants_grad
        if not wants_grad:
            frozen += 1
    return frozen


def trainable_parameters(model: nn.Module) -> tuple[int, int]:
    """``(trainable, total)`` unique parameter counts."""

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    return trainable, total


def lora_state_dict(model: nn.Module) -> dict[str, torch.Tensor]:
    """Only the adapter weights: what you would actually save and ship."""

    return {name: value.detach().clone() for name, value in model.state_dict().items() if "lora_" in name}


def lora_bytes(model: nn.Module) -> int:
    return sum(tensor.numel() * tensor.element_size() for tensor in lora_state_dict(model).values())


def merge_lora(model: nn.Module) -> int:
    """Fold every adapter into its base weight and restore plain ``nn.Linear``.

    Merging changes nothing about the model's function, which is exactly what the
    notebook verifies: logits before and after agree to floating-point tolerance.
    """

    merged = 0
    for name, module in list(model.named_modules()):
        if not isinstance(module, LoRALinear):
            continue
        parent_name, _, attribute = name.rpartition(".")
        parent = model.get_submodule(parent_name) if parent_name else model
        with torch.no_grad():
            module.base.weight.copy_(module.merged_weight())
        module.base.weight.requires_grad = True
        setattr(parent, attribute, module.base)
        merged += 1
    return merged


__all__ = [
    "LoRALinear",
    "apply_lora",
    "freeze_except_lora",
    "lora_bytes",
    "lora_state_dict",
    "merge_lora",
    "trainable_parameters",
]
