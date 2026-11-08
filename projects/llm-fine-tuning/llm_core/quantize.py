"""Weight-only quantization, simulated in floating point.

Real int8 or 4-bit inference needs kernels that multiply quantized values
directly. This module does something simpler and honest: it rounds weights to a
grid, stores the scale, and dequantizes before the forward pass. That reproduces
the *accuracy* and *size* effects of weight-only quantization exactly, while
measuring no speed-up at all - the arithmetic is still float32.

The lessons say so explicitly rather than implying a latency win that was never
measured.
"""

from __future__ import annotations

import copy

import torch

BITS = (8, 4)


def quantize_tensor(weight: torch.Tensor, bits: int = 8) -> tuple[torch.Tensor, torch.Tensor]:
    """Symmetric per-output-channel quantization of a 2-D weight matrix."""

    if weight.ndim != 2:
        raise ValueError("quantize_tensor expects a 2-D matrix")
    if bits not in BITS:
        raise ValueError(f"bits must be one of {BITS}")
    qmax = 2 ** (bits - 1) - 1
    float_weight = weight.detach().to(torch.float32)
    scale = float_weight.abs().amax(dim=1, keepdim=True).clamp(min=1e-8) / qmax
    quantized = torch.round(float_weight / scale).clamp(-qmax, qmax).to(torch.int8)
    return quantized, scale


def dequantize_tensor(quantized: torch.Tensor, scale: torch.Tensor) -> torch.Tensor:
    return quantized.to(torch.float32) * scale


def quantized_size_bytes(state: dict, bits: int = 8) -> int:
    """Bytes for quantized 2-D weights plus float32 scales and untouched vectors."""

    total = 0
    for tensor in state.values():
        if tensor.ndim >= 2 and tensor.is_floating_point():
            rows = tensor.shape[0]
            total += (tensor.numel() * bits + 7) // 8 + rows * 4
        else:
            total += tensor.numel() * tensor.element_size()
    return total


def quantize_state_dict(state: dict, bits: int = 8) -> tuple[dict, dict]:
    """Return a dequantized copy of ``state`` plus a measurement report."""

    output: dict[str, torch.Tensor] = {}
    max_error = 0.0
    error_sum = 0.0
    elements = 0
    matrices = 0
    for name, tensor in state.items():
        if tensor.ndim >= 2 and tensor.is_floating_point():
            quantized, scale = quantize_tensor(tensor, bits)
            restored = dequantize_tensor(quantized, scale)
            diff = (restored - tensor.to(torch.float32)).abs()
            max_error = max(max_error, float(diff.max()))
            error_sum += float(diff.sum())
            elements += diff.numel()
            matrices += 1
            output[name] = restored.to(tensor.dtype)
        else:
            output[name] = tensor.clone()
    original_bytes = sum(t.numel() * t.element_size() for t in state.values())
    new_bytes = quantized_size_bytes(state, bits)
    return output, {
        "bits": bits,
        "matrices": matrices,
        "elements": elements,
        "max_abs_error": round(max_error, 6),
        "mean_abs_error": round(error_sum / max(1, elements), 6),
        "original_bytes": original_bytes,
        "quantized_bytes": new_bytes,
        "compression_ratio": round(original_bytes / max(1, new_bytes), 3),
    }


def quantized_copy(model: torch.nn.Module, bits: int = 8) -> tuple[torch.nn.Module, dict]:
    """Deep-copy a model, round its weights, and load them back.

    The copy is a normal float model, so it can be evaluated with the same code
    as the original. Only its weights differ, by at most one quantization step.
    """

    clone = copy.deepcopy(model)
    state = clone.state_dict()
    restored, report = quantize_state_dict(state, bits)
    clone.load_state_dict(restored)
    return clone, report


def top1_agreement(logits_a: torch.Tensor, logits_b: torch.Tensor) -> float:
    """Share of positions where two logit tensors pick the same next token."""

    if logits_a.shape != logits_b.shape:
        raise ValueError("logit shapes differ")
    return float((logits_a.argmax(dim=-1) == logits_b.argmax(dim=-1)).float().mean())


__all__ = [
    "BITS",
    "dequantize_tensor",
    "quantize_state_dict",
    "quantize_tensor",
    "quantized_copy",
    "quantized_size_bytes",
    "top1_agreement",
]
