# Lab 8 - Compare inference latency and model size across configurations

**Section path:** [Overview](../index.md) · Module [CV13](../cv13-optimization-and-inference.md) · **Lab 8** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 13% of the section assessment |
| **Time** | 3 hours |
| **Hardware** | CPU-only; report your own hardware |
| **Code** | `projects/computer-vision/lab8_deployment.py` |
| **Prerequisite** | CV05, CV13 |

## The task

Measure, do not assume. Four configuration axes on one model: precision (float32 vs dynamic
int8), threads, batch size, and input resolution. Report median and p90 latency, model
size, and the accuracy cost of anything you change.

Deliverables:

1. four tables (precision, threads, batch, input size),
2. model size and parameter count,
3. a recommendation for one stated deployment constraint,
4. one optimisation you tested and **rejected**, with the measurement that rejected it.

## Setup

```bash
python scripts/make_vision_data.py
cd projects/computer-vision
python lab8_deployment.py --runs 20
```

The script trains a small classifier for 2 epochs so the benchmark is self-contained; it
is not trying to be accurate, only to be the right *shape* of model (conv-heavy, 72,499
parameters).

## Run it

Verified on Windows 11, Python 3.12.10, torch 2.14.1+cpu, 8 threads available:

```text
model TinyCNN  params 72499  size 0.2897 MB  int8 estimate 0.0691 MB
threads available 8

=== float32 vs dynamic int8
label          median_ms  p90_ms  size_mb
float32        0.441      0.472   0.2897
dynamic int8   0.503      0.507   0.2900
speedup 0.88x  size change +0.0002 MB  top-1 agreement 1.000
note: dynamic quantization only converts Linear layers; convolutions stay float

=== threads
threads  median_ms  p90_ms
1        0.639      0.650
2        0.553      0.565
4        0.475      0.484
8        0.443      0.458

=== batch size
batch_size  median_ms  per_item_ms
1           0.419      0.419
4           0.971      0.243
8           1.22       0.152

=== input size
input_size  median_ms
24          0.425
32          0.441
48          0.586

single-thread 0.64 ms vs 8-thread 0.44 ms (1.4x)

report: .../outputs/lab8_deployment.json
0 failure(s)
PASS  latency, size, threads, batch, and input size all measured
```

## Interpreting each table

**Precision.** Dynamic int8 is *slower* here (0.503 vs 0.441 ms) and the file is 0.2 KB
larger. `quantize_dynamic` converts `nn.Linear` only; this model is almost all
convolutions, so almost nothing converted and the one converted layer added
quantise/dequantise overhead. Top-1 agreement is 1.000 - accuracy was never the issue.

**Threads.** 1 → 8 threads gives 1.4x, not 8x. Small convolutions are dominated by per-op
overhead; more cores cannot help a 0.44 ms job.

**Batch.** Per-item cost falls 2.76x from batch 1 to 8, while total latency rises. Batching
trades latency for throughput; it is right for offline scoring and wrong for a single
interactive request.

**Input size.** 24x24 costs about the same as 32x32 here because fixed overhead dominates.
The ratio grows at larger sizes; test at *your* deployment resolution.

## Test cases

| Check | Expected | Verification |
| --- | --- | --- |
| Baseline latency positive | yes | printed |
| p90 >= median | yes | printed |
| Size positive, matches params | ~0.29 MB | printed |
| Per-item cost falls with batch | yes | table |
| Thread sweep includes 1 and max | yes | table |
| Agreement in [0, 1] | yes | printed |
| Rejected optimisation documented | present | your write-up |

## Rubric

| Criterion | Marks | What earns full marks |
| --- | --- | --- |
| Correct measurement | 25 | warmup discarded, median + p90, hardware and threads stated |
| Four tables complete | 20 | precision, threads, batch, input size |
| Interpretation | 25 | explains the quantisation result and the thread scaling, not just quotes |
| Recommendation | 20 | one constraint, one configuration, with the numbers that justify it |
| Rejected optimisation | 10 | an optimisation you measured and did not ship, with evidence |

## Extensions

1. Halve the model width (`optimize.halve_width`) and report latency, size, and accuracy.
2. Measure at 96x96 and 128x128 and fit the pixel-count relationship.
3. Run the model with `torch.set_num_threads(1)` under a simulated request load and report
   p90 across 200 requests.
4. Export to ONNX and measure with ONNX Runtime, if available. Report the speedup or its
   absence.

## Submit

```text
cv-lab8/
  README.md           # hardware, OS, torch version, commands
  tables.md           # four tables
  decision.md         # constraint, chosen configuration, justification, rejected option
  lab8_deployment.json
```

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Latency wildly variable | no warmup, or other load | warm up once; close other apps; report p90 |
| int8 faster in your run | different hardware/backends | fine - report your numbers, not these |
| All latencies equal up to 2 decimals | timer resolution | increase runs, report microseconds |
