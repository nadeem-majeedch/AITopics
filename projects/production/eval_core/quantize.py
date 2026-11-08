"""Post-training quantization and honest size/latency accounting.

The procedure is symmetric per-tensor int8 quantization::

    scale = max(|W|) / 127
    q     = round(W / scale)   clamped to [-127, 127]
    W'    = q * scale

It is the simplest real quantization scheme, and it is enough to show the trade-off
the lesson is about: smaller weights, a small accuracy cost, and a latency change
that you must measure rather than assume.

What this module does **not** do is run int8 kernels. The dequantized weights are
multiplied in float, so the measured latency includes dequantization and is not
what a production int8 runtime would achieve. The report says so, and the lesson
tells you to measure on your own target instead of trusting a course number.
"""

from __future__ import annotations

import time
from typing import Callable, Sequence

import numpy as np


def quantize_array(weights: np.ndarray, bits: int = 8) -> tuple[np.ndarray, float]:
    """Symmetric per-tensor quantization. Bias vectors and 1-D arrays stay float."""
    weights = np.asarray(weights, dtype=np.float32)
    limit = 2 ** (bits - 1) - 1
    max_abs = float(np.max(np.abs(weights))) if weights.size else 0.0
    scale = max_abs / limit if max_abs > 0 else 1.0
    q = np.clip(np.round(weights / scale), -limit, limit).astype(np.int8)
    return q, scale


def dequantize_array(q: np.ndarray, scale: float) -> np.ndarray:
    return (q.astype(np.float32) * np.float32(scale)).astype(np.float32)


def quantize_model(params: dict[str, np.ndarray], bits: int = 8) -> tuple[dict, dict]:
    """Quantize every 2-D weight matrix; keep biases in float32."""
    quantized: dict[str, np.ndarray] = {}
    meta: dict[str, dict] = {}
    for name, value in params.items():
        array = np.asarray(value)
        if array.ndim >= 2 and array.size >= 64:
            q, scale = quantize_array(array, bits)
            quantized[name] = q
            meta[name] = {"scale": scale, "quantized": True, "bits": bits}
        else:
            quantized[name] = array.astype(np.float32)
            meta[name] = {"scale": 1.0, "quantized": False, "bits": 32}
    return quantized, meta


def dequantize_model(quantized: dict, meta: dict) -> dict[str, np.ndarray]:
    restored = {}
    for name, value in quantized.items():
        info = meta[name]
        restored[name] = dequantize_array(value, info["scale"]) if info["quantized"] else np.asarray(value)
    return restored


def float_size_bytes(params: dict[str, np.ndarray]) -> int:
    return int(sum(np.asarray(value).size * 4 for value in params.values()))


def quantized_size_bytes(quantized: dict, meta: dict) -> int:
    total = 0
    for name, value in quantized.items():
        if meta[name]["quantized"]:
            total += np.asarray(value).size * 1  # int8
            total += 4  # one float32 scale per tensor
        else:
            total += np.asarray(value).size * 4
    return int(total)


def compression_ratio(params: dict[str, np.ndarray], quantized: dict, meta: dict) -> float:
    original = float_size_bytes(params)
    return original / quantized_size_bytes(quantized, meta) if original else float("nan")


def time_calls(fn: Callable[[], object], repeats: int = 200, warmup: int = 20) -> dict:
    """Median and p95 wall-clock latency in milliseconds for one call."""
    for _ in range(warmup):
        fn()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - start) * 1000.0)
    samples.sort()
    return {
        "repeats": repeats,
        "median_ms": samples[len(samples) // 2],
        "p95_ms": samples[min(len(samples) - 1, int(round(0.95 * (len(samples) - 1))))],
        "min_ms": samples[0],
        "max_ms": samples[-1],
    }


def top1_agreement(logits_a: np.ndarray, logits_b: np.ndarray) -> float:
    a = np.argmax(np.asarray(logits_a), axis=1)
    b = np.argmax(np.asarray(logits_b), axis=1)
    return float((a == b).mean())


def quantization_report(original: dict[str, np.ndarray], quantized: dict, meta: dict,
                        probs_original: np.ndarray, probs_quantized: np.ndarray,
                        y_true: Sequence[int]) -> dict:
    """Assemble the numbers a model card would need."""
    from . import metrics

    preds_original = (probs_original >= 0.5).astype(int)
    preds_quantized = (probs_quantized >= 0.5).astype(int)
    return {
        "original_bytes": float_size_bytes(original),
        "quantized_bytes": quantized_size_bytes(quantized, meta),
        "compression": compression_ratio(original, quantized, meta),
        "accuracy_original": metrics.accuracy(y_true, preds_original),
        "accuracy_quantized": metrics.accuracy(y_true, preds_quantized),
        "accuracy_delta": metrics.accuracy(y_true, preds_quantized) - metrics.accuracy(y_true, preds_original),
        "auc_original": metrics.roc_auc(y_true, probs_original),
        "auc_quantized": metrics.roc_auc(y_true, probs_quantized),
        "prediction_agreement": float((preds_original == preds_quantized).mean()),
        "mean_abs_probability_shift": float(np.abs(probs_original - probs_quantized).mean()),
    }
