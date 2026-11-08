# VD14 - Evaluation, performance profiling, and deployment {#vd14}

**Section path:** [Overview](index.md) · **Module 14** · [Lab 7](labs/lab-7-integrated-analytics.md) · [Lab 8](labs/lab-8-performance.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 5 hours: 2 h reading, 3 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | [VD08](vd08-counting-and-traffic-flow.md), [VD12](vd12-video-classification-and-events.md) |
| **You will produce** | A benchmark table you can defend, and a deployment plan with a measured budget |

## Why this module exists

Two reports are usually missing from a student video project, and their absence is why the
project does not survive contact with a camera: **a profile** (what does a frame cost, and where?)
and **an error contract** (what happens when the input is not a video?). This module is those two
things, plus the metrics that make a claim checkable.

## Metrics: one per task, no universals

| Task | Primary metric | Report with it | Do not report alone |
| --- | --- | --- | --- |
| Detection | mAP@0.5 | P, R, per-class AP, TP/FP/FN | mAP only |
| Tracking | MOTA | IDSW, fragments, track count vs objects | MOTA only |
| Counting | absolute error per class:direction | total error and cell error separately | total only |
| Classification | macro F1 | per-class P/R/F1, confusion matrix | accuracy on balanced data |
| Event detection | event P/R + timing error | tolerance window, false alarms/hour | "it detected events" |
| Performance | median ms/frame (+ max) | RSS, model size, machine, threads | one lucky run |

The pattern: every primary metric in this table can be gamed by a degenerate system. mAP by
emitting thousands of boxes; MOTA by emitting nothing on hard frames; total count by ignoring
class; accuracy by predicting the majority class. The "report with it" column is the antidote.

## Profiling: the three levers, measured

Lab 8 measures every lever on the same clip, with warm-up and medians, so the numbers are
comparable.

### Lever 1: sampling rate (the big one)

| Stride | Frames | ms per video-second | Speedup | mAP@0.5 | Counted | Count error |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 60 | 44.9 | 1.00x | 0.918 | 6 | 2 |
| 2 | 30 | 22.2 | 2.02x | 0.926 | 7 | 3 |
| 3 | 20 | 14.5 | 3.10x | 0.928 | 5 | 1 |
| 5 | 12 | 9.8 | **4.58x** | 0.912 | 6 | 2 |

Cost falls almost linearly, because work per processed frame is constant. The accuracy column
barely moves here - and that is the trap: at some stride the *tracker* stops seeing vehicles
often enough to associate them, and the count degrades long before mAP does. Test the stride on
your counting metric, not just your detector's.

### Lever 2: model size (the honest surprise)

| Model | Parameters | ms/frame | mAP@0.5 |
| --- | --- | --- | --- |
| TinyDetector (scratch) | 138,579 | **4.19** | **0.918** |
| SSDLite320 (COCO) | 3,440,060 | 58.71 | 0.000 |

14x the latency for a model that scores zero here. The lesson is not "small models are better";
it is **model size is not accuracy - it is accuracy on the data the model was trained for.** A
general-purpose detector is a bargain when your domain matches COCO and a liability when it does
not.

### Lever 3: working resolution (measured, not assumed)

| Scale | Frame size | ms/frame | mAP@0.5 | Recall |
| --- | --- | --- | --- | --- |
| 1.00 | 640x360 | 4.24 | 0.918 | 0.897 |
| 0.50 | 320x180 | 3.97 | 0.918 | 0.897 |
| 0.25 | 160x90 | 3.80 | 0.925 | 0.908 |

A 16x reduction in pixels bought 1.12x in time, because both models resize to a fixed input -
the cost is in the network, not in the frame. This is exactly the kind of "optimisation" that
sounds obviously right and is measurably wrong. Resolution *does* matter for accuracy as objects
shrink, and for decode cost on large files, which this 4 MB clip is too small to show.

### Memory

```
process RSS: 232.1 MB -> 235.0 MB after loading TinyDetector
process RSS after both models: 388.3 MB
```

Measured with `metrics.process_memory_mb()`, which reads the OS (on Windows through
`GetProcessMemoryInfo`), not an estimate from parameter counts. Two lessons: loading a 0.5 MB
model costs ~3 MB of RSS, and holding both models costs 150 MB more - so "we'll just keep the
big one loaded" is a memory decision, not a free one.

## The benchmark harness

```python
from video_core.metrics import benchmark

result = benchmark(lambda: detector.predict(frame), runs=5, warmup=2)
print(result["median_ms"], result["max_ms"], result["throughput_per_s"])
# {'label': '', 'runs': 5, 'median_ms': 4.19, 'mean_ms': ..., 'min_ms': ...,
#  'max_ms': ..., 'items': 1, 'throughput_per_s': 238.6}
```

Warm-up matters: the first call includes lazy initialisation and can be 5-10x slower. Reporting a
cold first call as "latency" is the most common profiling error in student work. Report the
machine, the thread count (this section pins torch to one thread), and the input size alongside
any timing - otherwise the number is not comparable to anything.

## Deployment: the error contract

A pipeline that works on good input and crashes on bad input is not deployable. Lab 7 defines the
contract explicitly:

| Input | Behaviour | Exit code |
| --- | --- | --- |
| valid clip | analyse, write summary + video | 0 |
| missing path | `input error: file not found` | 2 |
| truncated MP4 | `input error: no decodable frames` | 2 |
| HTML page named `.mp4` | `input error: no decodable frames` | 2 |
| zero-byte file | `input error: no decodable frames` | 2 |
| video bytes with `.txt` name | `input error: cannot open with any installed decoder` | 2 |
| bad config key or unknown model | `config error: model must be 'tiny' or 'ssdlite'` | 3 |

The `.txt` case is worth knowing precisely: OpenCV's FFmpeg backend dispatches on the extension,
so valid video bytes under a `.txt` name are refused. The message names the decoder, not the
suffix, which is the right level of detail - the user needs to know the file could not be opened,
not which layer decided.

Every failure prints a reason and stops **before writing anything**, so a failed run never leaves
a half-written summary that a dashboard might pick up.

## A capacity budget you can defend

Worked from the measured numbers, for one 10 fps 640x360 camera on one CPU core:

| Item | Value | Source |
| --- | --- | --- |
| Detector cost per frame | 4.19 ms | Lab 8 |
| Tracker + counter | ~0.5 ms | Lab 7 (22.01 ms/frame total at stride 1 including I/O) |
| End-to-end at stride 1 | ~22 ms/frame → ~45 fps | Lab 7 |
| Frames per second available | 45 | derived |
| Camera frames per second | 10 | input |
| Headroom | 4.5x | derived |
| At stride 3 | ~14.5 ms/video-second | Lab 8 |

The headroom is what lets you add a second camera to the same core, or run at 30 fps. Do this
arithmetic before promising a deployment, and re-measure on the target machine - these are
laptop numbers, and a container with 1 vCPU will be slower.

## What to write in the report

1. **Accuracy**, per task, with the metric's caveat and the split it was measured on.
2. **Speed**, median and worst case (`max_ms`), with machine, threads, resolution, stride.
3. **Memory**, measured RSS, with what was loaded.
4. **Failure behaviour**, the table above, from actual tests.
5. **The weakest number**, stated by you before a reviewer finds it.

Point 5 is the one that distinguishes an engineer's report from a demo. Every system has a weak
number; the only question is whether you know it.

## Checks

- [ ] You can name the primary metric for each of the five tasks and its companion metric.
- [ ] You can explain why a 16x pixel reduction bought only 1.12x in time.
- [ ] You can state the sampling lever's payoff (4.58x at stride 5) and its cost.
- [ ] You can reproduce the exit-code table by breaking a file on purpose.
- [ ] You can compute a capacity budget for one camera from measured numbers.
