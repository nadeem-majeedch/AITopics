# CV13 - Model optimization and inference {#cv13}

**Section path:** [Overview](index.md) · **Module 13** · [Lab 8](labs/lab8-deployment-comparison.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 1.5 h reading, 2.5 h practice |
| **Hardware** | CPU-only; every number below was measured on a laptop CPU |
| **Prerequisites** | CV05, CV08 |
| **You will produce** | A latency table across four configurations, and one paragraph on which optimisation you would actually ship |

## Why this module exists

A model that takes 400 ms per image cannot serve a 30 fps camera, and a 90 MB model does
not fit in a mobile app. Deployment questions are quantitative: how many milliseconds, how
many megabytes, at what accuracy cost. This module measures all three on the section's own
model instead of quoting benchmarks from elsewhere.

## What you measure, and how

```python
stats = optimize.benchmark_model(model, sample, runs=20)
print(stats.median_ms, stats.p90_ms, stats.min_ms, stats.max_ms)
```

Rules that make a latency number trustworthy:

1. **Warm up.** The first call includes lazy initialisation and is 5-50x slower. Discard it
   (the helper does one warmup run).
2. **Report a distribution, not one run.** Median for the typical case, p90 for the tail.
3. **Fix the thread count.** Latency changes with `torch.set_num_threads`.
4. **State the input shape and batch size.** "0.44 ms" means nothing without them.
5. **Measure on the deployment target.** A desktop CPU number does not predict a phone.

## Size: parameters are not megabytes

```python
info = models.summarize_model(model)
# {'parameters_total': 72499, 'size_mb': 0.2897, 'estimated_int8_mb': 0.0691}
```

The 0.2897 MB is the serialized state dict, not `params * 4 = 0.2765 MB`. Buffers, pickle
overhead, and batch-norm statistics account for the difference, and the file on disk is
what ships.

## Measured results

Model: `TinyCNN`, 3 classes, 72,499 parameters, 32x32 input, batch 1, Windows 11 CPU.

### Threads

| Threads | Median ms | p90 ms |
| --- | --- | --- |
| 1 | 0.639 | 0.650 |
| 2 | 0.553 | 0.565 |
| 4 | 0.475 | 0.484 |
| 8 | 0.443 | 0.458 |

Single-thread to 8-thread is **1.4x**, not 8x. Small convolutions do not parallelise well;
the per-op overhead dominates. This is the number that decides whether you serve one
request per core or batch across cores.

### Batch size

| Batch | Median ms | Per item ms |
| --- | --- | --- |
| 1 | 0.419 | 0.419 |
| 4 | 0.971 | 0.243 |
| 8 | 1.22 | 0.152 |

Batching cuts per-item cost by **2.8x** at batch 8 while raising total latency. Throughput
and latency are different objectives: batching is right for offline scoring, wrong for
interactive requests with a deadline.

### Input size

| Input | Median ms |
| --- | --- |
| 24x24 | 0.425 |
| 32x32 | 0.441 |
| 48x48 | 0.586 |

Cost grows with pixels, not linearly here because fixed overhead dominates at these sizes.
At 224x224 the ratio would be much steeper - and that is where input-size reduction pays.

### Dynamic INT8 quantisation

| Config | Median ms | Size MB | Top-1 agreement |
| --- | --- | --- | --- |
| float32 | 0.441 | 0.2897 | - |
| dynamic int8 | 0.503 | 0.2901 | 1.000 |

Result: **0.876x** - it is *slower*, and the file is 0.2 KB larger. Both facts are
instructive:

- `quantize_dynamic` converts `nn.Linear` layers only. This model is almost entirely
  convolutions, so almost nothing was converted; the one converted layer added
  quantise/dequantise overhead.
- Adding quantised modules adds parameters to the state dict, hence the tiny size
  increase, not a decrease.

!!! warning "An optimisation you did not measure is a rumour"
    "Quantisation gives 4x speedup" is true for large transformer and ResNet-class models,
    false here. The honest report is: *this* optimisation, on *this* model, on *this*
    hardware, cost 12% latency and changed nothing else. If you had shipped it on the
    strength of the general claim, you would have made the product slower.

For convolution-heavy models, the real levers are: static quantisation of activations
(QAT or PTQ with calibration), a smaller width, fewer input pixels, or an inference runtime
built for the target (ONNX Runtime, TFLite, Core ML).

## Accuracy cost must be measured, not assumed

```python
agreement = optimize.top1_agreement(model, optimized, sample)   # 1.0 here
```

Agreement of 1.000 on 32 dummy inputs means little. Real practice: run the *evaluation
set* through both models and report accuracy for each. A 1% accuracy loss may be a fine
trade for 3x throughput - but only if you measured both numbers.

## Choosing a deployment configuration

| Constraint | Lever | Cost |
| --- | --- | --- |
| Interactive latency < 50 ms | smaller input, smaller width | accuracy |
| Throughput on a server | batching, more threads | memory, tail latency |
| Mobile / edge | static int8, pruning, TFLite | accuracy, engineering time |
| No GPU available | fewer FLOPs, smaller model | accuracy |
| Power budget | fewer ops per frame, frame skipping | freshness |

Write the table for your own model before optimising. "Make it faster" without a target
produces unmeasurable work.

## Practice

1. Complete the four tables above on your machine. Report hardware and thread count.
2. Halve the model width (`optimize.halve_width`) and measure latency, size, and test
   accuracy. Is the trade worth it?
3. Measure batch 1 vs batch 16 per-item latency. State which your use case needs.
4. Write one paragraph: which single optimisation would you ship for a 30 fps camera, and
   what evidence supports it?

## Check yourself

1. Why is single-thread to 8-thread only 1.4x here?
2. Dynamic int8 made this model slower. Give two reasons rooted in what it actually converts.
3. Your model is 4 MB and 40 ms. Name two levers to reach 10 ms and the accuracy risk of each.

## What comes next

[CV14](cv14-evaluation-robustness-deployment.md) closes the section: robustness,
calibration, error analysis, model cards, monitoring - the evidence a deployed vision
system owes its users.
