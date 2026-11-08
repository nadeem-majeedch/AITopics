# Lab 6 - Action recognition: a single frame versus a sequence

**Section path:** [Overview](../index.md) · Modules [VD11](../vd11-action-recognition.md), [VD05](../vd05-image-vs-temporal-models.md) · **Lab 6** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 13% of the section assessment |
| **Time** | 4 hours |
| **Hardware** | CPU-only; ~40 s for both models |
| **Code** | `projects/video-ai/lab6_action_recognition.py` |
| **Prerequisites** | [Lab 4](lab-4-domain-adaptation.md) (to see what frame-level means), VD05, VD11 |

## Objectives

1. Train a **frame classifier** that sees one frame at a time, and measure per-frame and
   majority-voted clip accuracy.
2. Train a **temporal model** (CNN + GRU) on the same clips, seeds, and data.
3. Measure the difference, per class as well as in aggregate.
4. Explain the confusion the temporal model still has, with two testable hypotheses.
5. Report the parameter and latency cost of temporality, and the real cost (latency to answer).

## Prerequisites

- Modules VD05 and VD11 read - especially the claim table about what may be called "temporal".
- Clips are generated at run time by `synth.action_dataset`; no downloads.

## Procedure

### 1. Run it

```bash
cd projects/video-ai
python lab6_action_recognition.py
```

| Flag | Meaning |
| --- | --- |
| `--per-class 60` | clips per class (default 60) |
| `--frames 8` | frames per clip |
| `--frame-epochs 15` | frame-model epochs |
| `--temporal-epochs 20` | temporal-model epochs |
| `--selftest` | small data, checks only |

### 2. Look at the class strips

```
outputs/lab6_clip_right.png
outputs/lab6_clip_left.png
outputs/lab6_clip_approach.png
outputs/lab6_clip_depart.png
outputs/lab6_clip_stationary.png
```

Each is an 8-frame strip. Confirm for yourself that a single frame cannot tell `right` from
`left`: the square looks identical, only its position differs, and position alone is ambiguous
by construction.

### 3. Compare the three numbers

| Model | Accuracy |
| --- | --- |
| per frame | 0.447 |
| per clip, majority vote | 0.507 |
| per clip, temporal | **0.813** |

Chance is 0.20. The gap between 0.507 and 0.813 is the value of temporality.

### 4. Read the per-class table

| Class | frame F1 | temporal F1 | frame recall | temporal recall |
| --- | --- | --- | --- | --- |
| right | 0.400 | 0.632 | 0.294 | 0.706 |
| left | 0.571 | 0.400 | 0.769 | 0.308 |
| approach | **0.000** | **1.000** | 0.000 | 1.000 |
| depart | 0.542 | 0.963 | 1.000 | 1.000 |
| stationary | 1.000 | 0.952 | 1.000 | 1.000 |

Answer: which class accounts for most of the aggregate gain, and which class got *worse*?

### 5. Explain the confusion matrix

```
           right  left  approach  depart  stationary
right         12     3         0       1           1
left           9     4         0       0           0
approach       0     0        22       0           0
depart         0     0         0      13           0
stationary     0     0         0       0          10
```

Nine of thirteen `left` clips predicted `right`. Propose two hypotheses (§5 of
[VD11](../vd11-action-recognition.md) suggests two) and describe the experiment that would
distinguish them.

### 6. Check the shuffle claim for yourself

```python
import numpy as np
from video_core.actions import predict_temporal

clips = np.random.default_rng(0).random((4, 8, 64, 64)).astype(np.float32)
forward = predict_temporal(model, clips)
backward = predict_temporal(model, clips[:, ::-1])
print((forward == backward).mean())    # < 1.0 means order matters
```

A frame model would give identical outputs for both, because it never sees the order.

## Expected output

```
=== clips
  classes    : ['right', 'left', 'approach', 'depart', 'stationary']
  clip       : 8 frames of 64x64 grayscale
  train/test : 225 / 75 clips

=== model 1: single-frame classifier (the baseline)
  parameters : 23,845
  train time : 9.5 s  (loss 1.3941 -> 0.7343)
  per frame  : 0.447 accuracy (chance is 0.20)
  per clip   : 0.507 after majority-voting the 8 frames
  stability  : frames agree in 37/75 clips (0.49); mean distinct labels per clip 1.56

=== model 2: CNN + GRU over the clip (a temporal model)
  parameters : 48,805
  train time : 14.4 s  (loss 1.5551 -> 0.3128)
  per clip   : 0.813 accuracy

  per clip   : 0.65 ms (frame model, all 8 frames) vs 0.69 ms (temporal model)

  [PASS] the temporal model beats the frame baseline clearly  (0.507 -> 0.813 (+0.307))
  [PASS] the temporal model is better than guessing  (0.813)
  [PASS] the frame baseline is not secretly solving it  (0.507)
  [PASS] single frames disagree within clips (the ambiguity is real)  (0.49 agree)
  [PASS] per-frame accuracy is far below clip accuracy  (0.447 vs 0.813)

  5/5 checks passed
```

## Evaluation

| Criterion | Marks | Evidence |
| --- | --- | --- |
| Both models trained, 5/5 checks | 3 | output |
| Frame/vote/temporal compared, chance stated | 3 | 0.447 / 0.507 / 0.813 vs 0.20 |
| Per-class analysis identifies `approach` and `left` | 3 | the two rows that matter |
| Two testable hypotheses for left/right | 2 | plus the experiment that distinguishes |
| Cost of temporality, including latency-to-answer | 2 | 48,805 params, 0.69 ms, 0.8 s window |

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Temporal model ≈ frame baseline | clip tensor not ordered, or GRU bypassed | check `_to_clip_tensor` shape `(N, T, 1, H, W)` |
| Everything predicts `stationary` | class imbalance in a custom split | use `split_by_seed` |
| Frame model scores 0.9 | data leak: same seed in train and test | use the provided split |
| Results vary between runs | unseeded init | keep `set_seed` before construction |
| Very slow on CPU | torch threads oversubscribing | `VIDEO_AI_THREADS=1` |

## Extensions

1. **Longer clips.** Run with `--frames 16`. Does `left`/`right` improve? What does that tell you
   about the receptive field needed?
2. **Frame-rate ablation.** Subsample clips (every second frame) and re-measure. Is the temporal
   model robust to a lower frame rate?
3. **Temporal pooling baseline.** Replace the GRU with mean-pooling over frame features. Is the
   gain from *sequence modelling* or merely from *seeing more frames*? This is the sharpest
   possible test of what temporality buys.
4. **Pretrained backbone.** Freeze a small torchvision backbone as the frame encoder, train only
   the GRU. Compare with the from-scratch version (cf. [VD13](../vd13-fine-tuning.md)).
5. **Traffic actions.** Apply the same architecture to the traffic clips to classify "crossing
   left→right" vs "right→left" and compare with the geometric counter in Lab 3. Which is more
   accurate per compute-second?

## Submit

- Full output and `outputs/lab6_action_recognition.json`, plus one class strip.
- The three accuracy numbers with the chance baseline.
- The per-class table analysis and your two hypotheses.
- One paragraph on the real cost of temporality, beyond milliseconds.
