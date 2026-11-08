"""Inference latency, model size, quantization, and thread counts.

Every number printed by this module is measured, not estimated. The four
configurations in Lab 8 answer four different deployment questions:

* **Does quantization help?** Dynamic int8 quantization targets ``Linear`` layers.
  In a convolutional classifier it converts almost nothing, so the honest answer
  is usually "barely" - which is worth learning before shipping it.
* **Does a smaller model help more?** Halving channel width cuts parameters ~4x
  and usually cuts latency more than quantization does.
* **Does input size matter?** It is quadratic; halving pixels is a large win.
* **Do threads matter?** On a laptop, going from 1 to 8 threads helps, and then
  stops helping. Reporting a single-thread number as "the latency" overstates it,
  and reporting the 8-thread number understates the cost in a shared server.

Timing excludes the first call (warm-up) because it includes lazy initialization
and is not representative.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np
import torch
import torch.nn as nn

from .models import model_size_mb, set_seed


@dataclass
class LatencyStats:
    label: str
    median_ms: float
    p90_ms: float
    min_ms: float
    max_ms: float
    runs: int
    size_mb: float = 0.0

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "median_ms": round(self.median_ms, 3),
            "p90_ms": round(self.p90_ms, 3),
            "min_ms": round(self.min_ms, 3),
            "max_ms": round(self.max_ms, 3),
            "runs": self.runs,
            "size_mb": round(self.size_mb, 4),
        }


def benchmark(fn: Callable[[], object], runs: int = 20, warmup: int = 3, label: str = "") -> LatencyStats:
    """Median and p90 wall-clock latency over ``runs`` calls after ``warmup``.

    p90 is reported alongside the median because tail latency is what users
    notice, and because a laptop with other work running produces a heavy tail
    that the median hides.
    """
    for _ in range(max(0, warmup)):
        fn()
    timings = []
    for _ in range(max(1, runs)):
        started = time.perf_counter()
        fn()
        timings.append((time.perf_counter() - started) * 1000.0)
    arr = np.asarray(timings)
    return LatencyStats(
        label=label,
        median_ms=float(np.median(arr)),
        p90_ms=float(np.percentile(arr, 90)),
        min_ms=float(arr.min()),
        max_ms=float(arr.max()),
        runs=len(arr),
    )


def benchmark_model(model: nn.Module, sample: torch.Tensor, runs: int = 20, label: str = "") -> LatencyStats:
    """Benchmark a full forward pass in eval mode with gradients disabled."""
    model.eval()

    with torch.no_grad():
        stats = benchmark(lambda: model(sample), runs=runs, label=label or type(model).__name__)
    stats.size_mb = model_size_mb(model)
    return stats


def quantize_dynamic(model: nn.Module) -> nn.Module:
    """Apply PyTorch dynamic int8 quantization to ``Linear`` layers.

    Wrapped so the call works across torch versions that moved the namespace, and
    so a failure is reported rather than crashing a lab. Note what it does *not*
    do: convolutions stay float, so a conv-heavy model changes size by a few percent.
    """
    model = model.eval()
    try:
        from torch.ao.quantization import quantize_dynamic as _qd

        return _qd(model, {nn.Linear}, dtype=torch.qint8)
    except Exception:
        try:
            from torch.quantization import quantize_dynamic as _qd_legacy

            return _qd_legacy(model, {nn.Linear}, dtype=torch.qint8)
        except Exception as exc:  # pragma: no cover - version dependent
            print(f"[optimize] dynamic quantization unavailable: {type(exc).__name__}: {exc}")
            return model


def halve_width(model: nn.Module) -> nn.Module:
    """Rebuild the same architecture at half the channel width.

    Returns a *new, untrained* model: this measures the cost of a smaller
    architecture, not the accuracy of a trained one. Lab 8 asks students to train
    it briefly and report both latency and accuracy, because latency alone is not
    a deployment decision.
    """
    from .models import TinyCNN

    if isinstance(model, TinyCNN):
        return TinyCNN(num_classes=model.num_classes, width=max(4, model.width // 2))
    raise TypeError(f"halve_width supports TinyCNN, got {type(model).__name__}")


def thread_sweep(model: nn.Module, sample: torch.Tensor, thread_counts: Sequence[int] = (1, 2, 4, 8), runs: int = 10) -> list[dict]:
    """Latency against ``torch.set_num_threads``, restoring the original value after."""
    original = torch.get_num_threads()
    rows = []
    try:
        for count in thread_counts:
            torch.set_num_threads(max(1, int(count)))
            stats = benchmark_model(model, sample, runs=runs, label=f"threads={count}")
            rows.append({"threads": int(count), **stats.as_dict()})
    finally:
        torch.set_num_threads(original)
    return rows


def batch_sweep(model: nn.Module, sample: torch.Tensor, batch_sizes: Sequence[int] = (1, 4, 8), runs: int = 10) -> list[dict]:
    """Throughput per item against batch size.

    Larger batches amortize overhead, so per-item time falls even though per-call
    time rises. Reporting only per-call latency makes batching look useless.
    """
    rows = []
    for bs in batch_sizes:
        repeated = sample.repeat(int(bs), 1, 1, 1) if sample.dim() == 4 else sample.repeat(int(bs), 1)
        stats = benchmark_model(model, repeated, runs=runs, label=f"batch={bs}")
        rows.append(
            {
                "batch_size": int(bs),
                "median_ms": round(stats.median_ms, 3),
                "per_item_ms": round(stats.median_ms / max(1, int(bs)), 3),
                "size_mb": round(stats.size_mb, 4),
            }
        )
    return rows


def input_size_sweep(model: nn.Module, sample: torch.Tensor, sizes: Sequence[int] = (24, 32, 48), runs: int = 10) -> list[dict]:
    """Latency against square input size, to show the quadratic cost of pixels."""
    rows = []
    for size in sizes:
        resized = torch.nn.functional.interpolate(sample, size=(int(size), int(size)), mode="bilinear", align_corners=False)
        stats = benchmark_model(model, resized, runs=runs, label=f"size={size}")
        rows.append({"input_size": int(size), "median_ms": round(stats.median_ms, 3), "size_mb": round(stats.size_mb, 4)})
    return rows


def top1_agreement(a: torch.Tensor, b: torch.Tensor) -> float:
    """Fraction of samples where two models' argmax predictions agree.

    Used to check that quantization changed timing without changing behaviour;
    agreement below 1.0 is a finding, not automatically a failure.
    """
    return float((a.argmax(1) == b.argmax(1)).float().mean())


def format_table(rows: Sequence[dict], columns: Sequence[str] | None = None) -> str:
    """Render a list of dicts as a fixed-width table."""
    if not rows:
        return "(no rows)"
    columns = list(columns or rows[0].keys())
    widths = [max(len(str(c)), max((len(f"{r.get(c, '')}") for r in rows), default=0)) for c in columns]
    header = "  ".join(str(c).ljust(w) for c, w in zip(columns, widths))
    lines = [header, "-" * len(header)]
    for row in rows:
        lines.append("  ".join(str(row.get(c, "")).ljust(w) for c, w in zip(columns, widths)))
    return "\n".join(lines)


def deployment_report(model: nn.Module, sample: torch.Tensor, runs: int = 15) -> dict:
    """One call that produces every measurement Lab 8 needs."""
    set_seed(0)
    baseline = benchmark_model(model, sample, runs=runs, label="float32")
    quantized = quantize_dynamic(model)
    quant_stats = benchmark_model(quantized, sample, runs=runs, label="dynamic int8")

    with torch.no_grad():
        agreement = top1_agreement(model(sample), quantized(sample))

    return {
        "baseline": baseline.as_dict(),
        "quantized": quant_stats.as_dict(),
        "quantization_speedup": round(baseline.median_ms / max(1e-9, quant_stats.median_ms), 3),
        "size_change_mb": round(quant_stats.size_mb - baseline.size_mb, 4),
        "top1_agreement": agreement,
        "threads": thread_sweep(model, sample, runs=max(5, runs // 2)),
        "batch": batch_sweep(model, sample, runs=max(5, runs // 2)),
        "input_size": input_size_sweep(model, sample, runs=max(5, runs // 2)),
    }
