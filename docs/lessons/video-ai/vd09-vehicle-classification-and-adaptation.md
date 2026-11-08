# VD09 - Vehicle classification and domain adaptation {#vd09}

**Section path:** [Overview](index.md) · **Module 9** · [Lab 4](labs/lab-4-domain-adaptation.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 5 hours: 2 h reading, 3 h practice |
| **Hardware** | CPU-only; 3.4 M-parameter checkpoint for the baseline |
| **Prerequisites** | [VD06](vd06-detection-on-frames.md), [CV08](../computer-vision/cv06-transfer-learning.md) |
| **You will produce** | A three-way comparison (zero-shot, fine-tuned, from-scratch) on four unseen videos, with the gap explained |

## Why this module exists

"Can we classify vehicles into car / motorcycle / bus / truck?" sounds like a classification
problem. It is mostly a *domain* problem: the classes are easy, and the footage is not. A model
trained on daylight highway images meets a night clip with headlight glare and a rain clip with
motion blur, and its accuracy collapses - not because it cannot tell a bus from a truck, but
because it has never seen a bus in this light.

This module is about measuring that gap honestly and about what actually closes it.

## Three models, one task

| Model | Weight initialisation | Trained on | Parameters |
| --- | --- | --- | --- |
| COCO zero-shot | COCO-pretrained SSDLite | nothing extra | 3,440,060 |
| Fine-tuned | same COCO weights, new 4-class head | 60 aug'd frames from 2 train videos | 3,440,060 |
| From scratch | random | same 60 frames | 138,579 |

The measured result on four videos the models never saw:

| Video | COCO zero-shot | Fine-tuned | From scratch |
| --- | --- | --- | --- |
| `street_quiet` (val, day) | 0.000 | **0.156** | 0.289 |
| `street_night` | 0.000 | 0.033 | 0.096 |
| `street_rain` | 0.000 | 0.033 | 0.297 |
| `street_shake` | 0.100 | **0.295** | 0.443 |

Four facts, in the order that matters:

1. **Fine-tuning improved mAP on 4 of 4 held-out videos.** The zero-shot model does not detect
   this footage at all; the fine-tuned one does, barely.
2. **It did not reach the in-domain detector.** 0.156 vs 0.289 on validation, and 0.033 vs 0.297
   on rain. Five epochs over 60 frames buy a prior ("vehicles are rectangles on a road"), not a
   solution.
3. **Zero-shot recall is 0.000-0.100**, which is the number that kills the "just use a
   pretrained model" plan. mAP near zero with 36 detections on the shake clip is not a tuning
   problem.
4. **Random init beat transfer on three of four videos.** That is not a paradox: the from-scratch
   model's 138k parameters were shaped entirely by this section's rendering style, while the
   fine-tuned model had to unlearn 80 COCO classes' worth of features with 60 frames.

Fact 4 is the one students find hardest to accept, so it is worth stating precisely: with
tiny, stylistically narrow data, **a small model trained on the target distribution can beat a
large model adapted to it**. The right conclusion is not "pretraining is useless" - it is
"measure both, and do not assume the bigger model wins".

## What fine-tuning here actually is

```python
from video_core.detect import TrafficSSDLite, finetune_traffic_detector

model = TrafficSSDLite(score_threshold=0.6)
model.build()
print(model.pretrained_transfer)          # {'copied_tensors': 404, 'fresh_tensors': ...}
history = finetune_traffic_detector(epochs=5, stride=2, lr=3e-4, seed=0)
```

The procedure, exactly:

1. Load `ssdlite320_mobilenet_v3_large` with COCO weights.
2. Replace the box and class heads with 4-class equivalents.
3. Copy every tensor whose **shape still matches** - 404 of them. The backbone and feature
   pyramid survive; the classification and regression heads do not.
4. Train on frames from `street_day` and `street_dusk` only, stride 2, 5 epochs, lr 3e-4.
5. Choose a score threshold on `street_quiet` (validation) by best F1 → 0.6.
6. Evaluate once on the four test videos.

That is a **frame-level fine-tune of an image detector**. No clip, no temporal layer, no video
model. The lab asserts it:

```
[PASS] no temporal model is claimed here  (frame-level fine-tuning only; see Lab 6 ...)
```

Step 3 is what makes the word "fine-tuning" true rather than decorative: something pretrained
survived into the new model, and the count (404) is reported so you can see how much.

## The threshold curve, and why it is not a detail

| Threshold | mAP@0.5 | precision | recall | F1 | detections |
| --- | --- | --- | --- | --- | --- |
| 0.30 | 0.224 | 0.019 | 0.688 | 0.037 | 8790 |
| 0.40 | 0.216 | 0.069 | 0.500 | 0.122 | 1730 |
| 0.50 | 0.211 | 0.273 | 0.450 | 0.340 | 396 |
| **0.60** | 0.156 | **0.670** | 0.312 | **0.426** | 112 |
| 0.70 | 0.030 | 0.765 | 0.054 | 0.101 | 17 |

mAP is highest at 0.30 and F1 peaks at 0.60. That is not a contradiction: mAP integrates over
all thresholds, so it rewards a detector that emits a wide ranked list, while F1 at one
operating point rewards a detector whose boxes are mostly right when it fires. **Which one you
optimise depends on what the system does next**:

- A tracker (Lab 3) hates false positives: each one creates an ID and possibly a crossing. F1 at
  a high threshold is the right target.
- A recall-first alert ("flag anything that might be a pedestrian") wants the 0.30 end, and must
  then absorb 8,790 detections.

Choosing on validation and reporting on test - once - is the discipline. Note also that the COCO
baseline keeps its own 0.30: re-tuning a baseline you did not train would flatter your model at
the baseline's expense.

## What "domain gap" is composed of

Four shifts are present in this section's test set, and they are not interchangeable:

| Shift | What changes | Why fine-tuning struggles |
| --- | --- | --- |
| **Night** | low light, headlights, different colour statistics | 2 train videos, both daylight |
| **Rain** | blur, spray, reflections | no rain in training |
| **Camera shake** | every box moves between frames | frame-level training cannot learn it |
| **Crowd** | occlusion, overlap | labels exist, but boxes are harder |

Fine-tuning 60 frames moves the *style* prior a little; it does not synthesise a lighting
condition that was never in the training data. That is why the night and rain columns move by
0.033 while the shake column moves by 0.195 - shake is largely a *framing* change, which the
model's features already handle once the head knows what a vehicle looks like.

Real fixes, in order of value per hour:

1. **Collect target-domain data.** Ten night clips beat any architecture change.
2. **Augment for the shift you have** - brightness, blur, noise, JPEG - and verify on a
   held-out clip of the *same* shift, not on the clean one.
3. **Adapt the threshold per condition**, and report which threshold each condition used.
4. **Fine-tune more than the head** if your data supports it (here: not with 60 frames).

## Classification versus detection

This module is about detection adapted to a domain, because that is the shape of the problem in
a counting pipeline: you need boxes, then a class per box. The same three-way comparison applies
to pure classification (crop the vehicle, classify the crop), and the conclusion transfers:
**domain fit beats model size at this scale.**

If you only need class counts per clip ("how many buses passed"), a per-object classifier on
tracker output is the cheap path - the tracker already gives you identity, and a classifier on
crops can be trained on far more samples than a detector can (Lab 3's 14 tracks per 6 vehicles
is 14 crops; the detector needed 60 full frames).

## Common mistakes

| Mistake | Symptom | Fix |
| --- | --- | --- |
| Calling this "training a video model" | an inaccurate report | say frame-level fine-tune; cite Lab 6 for temporal |
| Choosing the threshold on test | scores 5-10 points too good | choose on val, report once |
| Evaluating on the training videos | 0.9 mAP, useless system | held-out videos only |
| Comparing models at different thresholds | favourite model "wins" | fix each model's operating point on val |
| Concluding "pretraining does not help" | over-generalising one table | it helped 4/4 vs zero-shot; it lost to in-domain scratch |

## Checks

- [ ] You can state the three models' parameter counts and what each was trained on.
- [ ] You can explain why the from-scratch model won while pretraining still helped.
- [ ] You can read the threshold table and pick a threshold for a tracker, with a reason.
- [ ] You can name the 404 copied tensors and why that count makes "fine-tuned" honest.
- [ ] You can describe one concrete change that would close the night gap, and its cost.
