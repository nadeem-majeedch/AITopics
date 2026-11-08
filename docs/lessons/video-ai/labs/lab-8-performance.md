# Lab 8 - Performance: sampling, model size, resolution, and what each one costs

**Section path:** [Overview](../index.md) · Module [VD14](../vd14-evaluation-and-deployment.md) · **Lab 8** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 10% of the section assessment |
| **Time** | 4 hours |
| **Hardware** | CPU-only; ~1 min for all measurements |
| **Code** | `projects/video-ai/lab8_performance.py` |
| **Prerequisites** | Labs 2, 3; VD14 |

## Objectives

1. Measure the three performance levers - sampling rate, model size, working resolution - with
   an accuracy number beside each.
2. Distinguish levers that save real time from levers that only feel like they should.
3. Measure memory as process RSS before and after loading each model.
4. Produce a capacity budget for one camera from your own measurements.

## Prerequisites

- TinyDetector cache and COCO SSDLite weights available (Lab 2 and 3).
- A quiet machine. Close other Python processes; timings are the measurement.

## Procedure

### 1. Run it

```bash
cd projects/video-ai
python lab8_performance.py
```

| Flag | Meaning |
| --- | --- |
| `--video street_crowd` | measure on a different clip |
| `--selftest` | fewer strides, checks only |

### 2. Lever 1: sampling rate

| Stride | Frames | ms per video-second | Speedup | mAP@0.5 | Counted | Count error |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 60 | 44.9 | 1.00x | 0.918 | 6 | 2 |
| 2 | 30 | 22.2 | 2.02x | 0.926 | 7 | 3 |
| 3 | 20 | 14.5 | 3.10x | 0.928 | 5 | 1 |
| 5 | 12 | 9.8 | **4.58x** | 0.912 | 6 | 2 |

The payoff is real and nearly linear. The cost is not in mAP - it is in the *count*, which is
noisy because the tracker sees fewer frames per vehicle. Note the non-monotonic count error
(3 at stride 2, 1 at stride 3, 2 at stride 5): with 6 vehicles, one miscount moves the number by
one, so a 12-frame sample cannot resolve small differences. Say that in your report instead of
claiming an optimum.

### 3. Lever 2: model size

| Model | Parameters | ms/frame | mAP@0.5 |
| --- | --- | --- | --- |
| TinyDetector (scratch) | 138,579 | **4.19** | **0.918** |
| SSDLite320 (COCO) | 3,440,060 | 58.71 | 0.000 |

14x the latency for a model that scores zero here. The lever that matters is not parameter
count but **fit to the domain** - a fact Lab 4 measured from the accuracy side.

### 4. Lever 3: working resolution

| Scale | Frame size | ms/frame | mAP@0.5 | Recall |
| --- | --- | --- | --- | --- |
| 1.00 | 640x360 | 4.24 | 0.918 | 0.897 |
| 0.50 | 320x180 | 3.97 | 0.918 | 0.897 |
| 0.25 | 160x90 | 3.80 | 0.925 | 0.908 |

A 16x pixel reduction bought 1.12x in time. Both models resize to a fixed input, so inference
cost is unchanged; you saved decode time on 4 MB clips, which is nearly nothing. **Do not quote
a resolution change as a speed-up unless you measured it on the model you ship** - this is the
lab's most transferable lesson.

### 5. Memory

```
process RSS: 232.1 MB -> 235.0 MB after loading TinyDetector
process RSS after both models: 388.3 MB
```

Loading a 0.5 MB model costs ~3 MB RSS; holding both costs ~150 MB. Memory is a deployment
constraint with a price, not a rounding error.

### 6. Build your capacity budget

From your own numbers, compute for one 10 fps 640x360 camera on one core:

```
end-to-end ms/frame (yours)  = ______
frames/s available           = 1000 / ms  = ______
camera needs                 = 10 frames/s
headroom                     = ______ x
```

Then answer: how many cameras fit on one core at stride 1? At stride 3?

## Expected output

```
=== models and memory
  TinyDetector  : 138,579 parameters (~0.5 MB float32), tiny_w24_e30_s2_seed0
  process RSS   : 232.1 MB -> 235.0 MB after loading it

=== 1. sampling rate on street_day
  stride  frames  wall_s  ms_per_video_s  speedup  map50  counted  count_error  tracks
  1       60      0.269   44.900          1.000    0.918  6        2            14
  2       30      0.133   22.200          2.020    0.926  7        3            12
  3       20      0.087   14.500          3.100    0.928  5        1            9
  5       12      0.059   9.800           4.580    0.912  6        2            9

=== 2. model size
  TinyDetector (scratch)  138579   4.190   0.918
  SSDLite320 (COCO)       3440060  58.710  0.000
  process RSS after both models: 388.3 MB

=== 3. working resolution
  1.000  640x360  0.261  4.240  0.918  0.897
  0.500  320x180  0.246  3.970  0.918  0.897
  0.250  160x90   0.231  3.800  0.925  0.908

  [PASS] timings were warmed up (no first-call inflation)  (4.19 ms/frame)
  [PASS] stride reduces compute  (4.58x)
  [PASS] detector still works at the largest stride  (mAP 0.912)
  [PASS] the larger pretrained model is slower  (58.71 ms)
  [PASS] resolution does not change inference cost much  (1.12x)
  [PASS] memory was measured, not assumed  (373 MB)

  6/6 checks passed
```

Your absolute milliseconds will differ; the *ratios* should be in the same neighbourhood. If your
stride-5 speedup is far from ~4.6x, check that decode time is not dominating (a cold disk cache
does exactly that).

## Evaluation

| Criterion | Marks | Evidence |
| --- | --- | --- |
| All three levers measured | 3 | three tables from your run |
| Resolution result explained | 3 | fixed input size → inference unchanged |
| Model-size result explained | 2 | domain fit, not parameter count |
| Memory measured, not estimated | 1 | RSS before/after |
| Capacity budget computed | 1 | cameras per core at two strides |

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| First measurement is 5-10x slower | cold graph / lazy init | the lab warms up; if you write your own loop, discard the first call |
| Speedup at stride 5 is only ~2x | decode cost dominates | warm the file cache, or measure on a larger clip |
| RSS jumps by hundreds of MB | both models resident | measure each in a separate process for clean numbers |
| mAP changes between runs | non-deterministic training | reuse the cached detector; do not retrain |
| `process_memory_mb()` returns -1 | unsupported platform probe | Windows/macOS/Linux supported; check the docstring |
| Everything is slower on battery | CPU frequency scaling | plug in, or report it |

## Extensions

1. **Batch inference.** Run the detector on 4 frames at once instead of 1+1+1+1 and report
   throughput change. Is there headroom left at batch 1?
2. **Thread count.** Run with 1, 2, and 4 torch threads. Where does it stop scaling, and why?
3. **Quantisation.** Convert the model to `torch.quantization.quantize_dynamic` and report the
   latency and mAP change. Does it help a model this small?
4. **Decode cost in isolation.** Time `iter_frames` with no model at all. What fraction of
   end-to-end time is decode on your machine? That fraction is the ceiling on any model speed-up.
5. **A real camera budget.** Pick a target (e.g. 4 cameras at 15 fps), compute the required
   ms/frame, and state which levers you would pull and what accuracy you would give up.

## Submit

- Full output and `outputs/lab8_performance.json`.
- The three tables from your machine, with CPU model and thread count.
- Your capacity budget, with arithmetic.
- One paragraph on a lever you expected to help and that did not - with the measurement.
