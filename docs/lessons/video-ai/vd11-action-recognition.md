# VD11 - Action recognition and temporal information {#vd11}

**Section path:** [Overview](index.md) · **Module 11** · [Lab 6](labs/lab-6-action-recognition.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 5 hours: 2 h reading, 3 h practice |
| **Hardware** | CPU-only; both models train in seconds |
| **Prerequisites** | [VD05](vd05-image-vs-temporal-models.md), [F11](../index.md#foundation-sequence) |
| **You will produce** | Two models, one number that separates them, and a per-class table that says where the difference comes from |

## Why this module exists

Module 5 argued that some questions are undecidable from a single frame. This module proves it
with a measurement, then shows what a temporal model buys and what it costs.

The task is deliberately small: five classes of motion, 8-frame clips, 64x64 grayscale. Small
enough to train in ten seconds, hard enough that a frame model cannot fake it.

## The task, and why it is a fair fight

```
classes: right, left, approach, depart, stationary
clip   : 8 frames of 64x64 grayscale
train/test: 225 / 75 clips (disjoint random seeds)
```

A square moves across the frame (`right`, `left`), grows and shrinks (`approach`, `depart`), or
stays put (`stationary`). One frame of a moving square is indistinguishable from one frame of a
stationary square: the pixels contain a position, not a velocity. The only way to know is to
compare two frames.

That is the whole lesson in one sentence, and the numbers make it unavoidable:

| Model | Input | Accuracy |
| --- | --- | --- |
| Frame classifier, per frame | one frame | 0.447 |
| Frame classifier, majority vote over 8 frames | 8 independent frames | 0.507 |
| CNN + GRU | 8 ordered frames | **0.813** |

Chance is 0.20. The frame model is well above chance - it can see size, which separates
`approach` from the rest poorly but not never - and nowhere near the temporal model.

## Why voting cannot rescue it

Majority voting over eight uninformed guesses is still uninformed. The measured stability makes
this concrete:

```
stability: frames agree in 37/75 clips (0.49); mean distinct labels per clip 1.56
```

Half the clips have frames that disagree with each other. Voting resolves a disagreement that
exists *because* each frame is guessing from the same insufficient evidence. The 0.447 → 0.507
gain is variance reduction, not information.

State that distinction whenever you report an aggregate: **"majority vote over per-frame
predictions, no temporal receptive field"** is the accurate description.

## The temporal model, and what actually changed

```python
from video_core.actions import FrameClassifier, TemporalClassifier

frame_model = FrameClassifier(n_classes=5)                     # 23,845 parameters
temporal_model = TemporalClassifier(n_classes=5, hidden=64)    # 48,805 parameters
```

The two share the same frame encoder design and differ in one structural fact: the temporal
model's input is `(T, H, W)`, its encoder runs per frame, and a GRU consumes the sequence of
embeddings. Gradients flow across time, so the encoder learns features that are *useful in
sequence*, not just per frame.

| | Frame model | Temporal model |
| --- | --- | --- |
| Parameters | 23,845 | 48,805 (2.0x) |
| Train time | 9.5 s | 14.4 s (1.5x) |
| Latency, 8-frame clip | 0.65 ms | 0.69 ms (1.06x) |
| Accuracy, clip level | 0.507 | **0.813** |

The interesting column is latency. Doubling parameters cost 6% of per-clip latency, because at
this scale the fixed overhead dominates. **The real cost of temporality is not FLOPs - it is that
the model cannot answer until it has a whole clip**, which adds a buffer and a fixed delay to a
live system. Report that, not just the milliseconds: an action model with an 8-frame window at
10 fps answers 0.8 s late, by construction.

## Where the difference comes from: the per-class table

| Class | frame F1 | temporal F1 | frame recall | temporal recall | support |
| --- | --- | --- | --- | --- | --- |
| right | 0.400 | 0.632 | 0.294 | 0.706 | 17 |
| left | 0.571 | 0.400 | 0.769 | 0.308 | 13 |
| approach | **0.000** | **1.000** | 0.000 | 1.000 | 22 |
| depart | 0.542 | 0.963 | 1.000 | 1.000 | 13 |
| stationary | 1.000 | 0.952 | 1.000 | 1.000 | 10 |

Three things to notice, and they are the reason per-class reporting exists:

1. **`approach` goes from 0.000 to 1.000.** The frame model never once got it right - a growing
   square in one frame looks like a medium-sized square. This single class accounts for most of
   the aggregate gap.
2. **`right` and `left` remain confused** even for the temporal model (0.632 and 0.400). Both
   are horizontal motion; the difference is direction, which a GRU over 8 frames can learn but
   only weakly from 225 training clips. A frame model's 0.571 on `left` is *better* than the
   temporal model's 0.400 - the temporal model traded left/right accuracy for approach/depart.
3. **`stationary` is 1.000 for both.** A shape that does not move is recognisable from one
   frame, which is exactly the case where temporality buys nothing.

The aggregate 0.813 hides a 0.400. Report per class, or you will deploy a model that is
confidently wrong about which way traffic flows.

## Confusion matrix, read as a story

```
           right  left  approach  depart  stationary     (rows = truth)
right         12     3         0       1           1
left           9     4         0       0           0
approach       0     0        22       0           0
depart         0     0         0      13           0
stationary     0     0         0       0          10
```

Nine of the thirteen `left` clips are predicted `right` - a systematic sign error, not noise.
Two hypotheses, both testable in an extension:

- **Seed bias in the generator**: if the square's starting position correlates with direction,
  a model can learn "starts at the right edge → moves left" for the training seeds and fail on
  test seeds. Check the generator's position ranges.
- **Symmetric appearance**: a grayscale square has no front or back, so only the *sequence*
  distinguishes the two, and 8 frames at this speed may be too short.

The fix for the second is more frames or a longer-range temporal model; the fix for the first is
data. Diagnosing which one you have is the exercise.

## Designing the clip: length, stride, and offset

Three parameters decide whether the task is even solvable:

| Parameter | Here | Rule |
| --- | --- | --- |
| Clip length | 8 frames | must cover the event's duration; 2 s at 10 fps needs 20 frames |
| Stride between frames | 1 | stride > 1 shortens the clip's temporal span |
| Overlap between clips | 50% in training | more samples, but correlated ones |

An 8-frame clip at 10 fps spans 0.7 s. A vehicle crossing a line takes ~3 s. So the same
architecture applied to traffic would need ~30 frames, and the encoder's temporal receptive field
would have to be longer than a single GRU step's - which is what stacking or attention buys.

## Clip-level metrics versus frame-level metrics

Report both, and label them:

- **Per-frame accuracy** (0.447) answers "if I classify one frame, how often am I right?"
- **Clip accuracy** (0.813) answers "if I watch this clip, how often am I right?"
- **Clip accuracy from votes** (0.507) answers the same question for a model that has no
  temporal receptive field.

A system that raises an alert per clip needs the second; a system that overlays labels per frame
needs the first. Quoting the clip number for a per-frame product is one of the easiest ways to
ship something that does not work.

## Checks

- [ ] You can explain why `approach` is 0.000 for a frame model without using the word "bias".
- [ ] You can state the temporal model's parameter and latency cost per clip.
- [ ] You can say what the real cost of temporality is, beyond FLOPs.
- [ ] You can read the confusion matrix and propose two testable explanations.
- [ ] You can compute how many frames a 3-second event needs at 10 fps.
