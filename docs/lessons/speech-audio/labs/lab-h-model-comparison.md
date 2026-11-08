# Lab H - Compare inference speed and recognition quality across models

**Section path:** [Overview](../index.md) · Module [SA14](../sa14-optimization-and-deployment.md) · **Lab H** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 10% of the section assessment |
| **Time** | 3 hours |
| **Hardware** | CPU-only |
| **Code** | `projects/speech-audio/lab_h_model_comparison.py` |
| **Prerequisite** | SA07, SA08, SA14 |

## The task

Train three recognisers that differ only in size and temporal stride, then measure the
trade-off instead of guessing it. Quality is measured on clean audio and at 10 dB SNR; speed
is measured as a real-time factor.

You must produce:

1. a table of parameters, size, stride, training time, WER, and RTF;
2. the relative comparison against the baseline;
3. the lexicon ablation on the worst model;
4. a recommendation with the error budget that justifies it.

## Run it

```bash
cd projects/speech-audio
python lab_h_model_comparison.py
python lab_h_model_comparison.py --selftest   # 3 epochs
```

This lab retrains all three models every run (about 25 s on CPU) instead of using the shared
cache, because the training-time column is part of the comparison and a cache hit would report
0.0 s for a model that takes five.

```text
=== speed and quality
model     params  size MB  stride  step ms  train s  WER clean  WER 10dB  median ms  RTF
------------------------------------------------------------------------------------------
small     94299   0.370    3       30       5.440    0.000      0.361     37.500     0.0036
baseline  166623  0.650    2       20       5.470    0.000      0.028     45.000     0.0043
accurate  372615  1.430    1       10       12.110   0.000      0.750     76.800     0.0073

=== relative to the baseline
  small     params x0.57  RTF x0.86  clean WER +0.000  noisy WER +0.333
  accurate  params x2.24  RTF x1.70  clean WER +0.000  noisy WER +0.722
```

## What the numbers say

* **The middle model is the best in noise** (0.028 WER at 10 dB, against 0.361 for the
  smallest and 0.750 for the largest). More capacity is not more robustness: with 204 training
  clips the 372k model has room to memorise, and on noise it does worse than a model less than
  half its size. This is the same overfitting story as SA06, seen from the deployment side.
* **Stride dominates compute**: stride 1 costs 1.70x the time of stride 2, and emits steps
  every 10 ms instead of 20 ms. That is the whole cost of the accurate model - it is the same
  architecture family with a finer output grid.
* **Clean WER is useless for choosing** - all three reach 0.000. The noisy column is where
  the decision lives.
* **RTF is far below 1** for all three (0.0037-0.0075), so on this machine every model is
  more than a hundred times faster than real time. Latency is not the constraint here;
  accuracy and memory are.

## Additional measurements you can reproduce

Same baseline model, same 10.52 s of test audio:

| Setting | Median time | RTF |
| --- | --- | --- |
| one batch, 1 thread (the lab default) | 45.8 ms | 0.0044 |
| one batch, 2 threads | 33.0 ms | 0.0031 |
| one batch, 8 threads | 27.6 ms | 0.0026 |
| clip by clip, 1 thread | 78.9 ms | 0.0075 |
| clip by clip, 8 threads | 73.4 ms | 0.0070 |

Threading saturates around two threads on this 36-clip batch. Batching the whole set is 1.7x
faster than 36 separate calls at one thread and 2.7x at eight. For a streaming interface you
cannot batch, so the per-clip row is the one that matters. Reproduce it with
`torch.set_num_threads(n)`, and remember the first row is the lab default, chosen because
training numbers reproduce there (SA06), not because it is fastest.

The timing columns are the only ones that move between runs: the WER numbers above come out
identical every time, but `train s` and `median ms` vary by 5-10% with machine load. Quote
them with that caveat or not at all.

## Reading the trade-off honestly

A comparison table is only meaningful if one variable changes at a time. Here the three
models differ in `stride_time`, `width`, and `hidden` together, so "the accurate model is the
worst in noise" is a statement about the bundle, not about any single knob. If you need to
attribute the difference, run three more models changing one parameter each.

The other trap is a single-run comparison. These runs are reproducible - the seeding fix in
SA06 makes identical numbers come out of identical code - but 36 test clips is a small sample,
so treat differences under about 0.1 WER as noise. The gaps here (0.361, 0.028, 0.750) are far
larger than that, and the closed-vocabulary decoder takes the worst model from 0.750 to 0.028
without training anything, which is the cheapest fix in the table.

## Checks

```text
PASS  stride 1 is slower than stride 3
PASS  every model produces WER in [0, 2]
PASS  at least one model is faster than real time
PASS  lexicon decoding does not hurt
```

## Write-up requirements

1. The speed/quality table with the relative comparison.
2. A recommendation: which model for a live assistant, which for batch transcription of
   archives, and what error budget justifies each.
3. One paragraph on why clean WER cannot pick a model here.
4. The measurement conditions (machine, threads, batch size) so someone else could reproduce
   it.

## Independent extensions

* Change only `stride_time` (1, 2, 3) with width and hidden fixed, and re-measure.
* Measure with `torch.set_num_threads(1)` to simulate a shared CPU.
* Add a fourth model with `width=8, hidden=32` and see whether accuracy collapses or holds.

Next: [Assessment](../assessment.md) · [Model card](../model-card.md)
