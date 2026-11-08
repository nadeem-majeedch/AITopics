# VD13 - Fine-tuning compatible models for video tasks {#vd13}

**Section path:** [Overview](index.md) · **Module 13** · [Lab 4](labs/lab-4-domain-adaptation.md) · [Lab 6](labs/lab-6-action-recognition.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 5 hours: 2 h reading, 3 h practice |
| **Hardware** | CPU-only for the frame-level recipe; a GPU for the temporal one |
| **Prerequisites** | [VD09](vd09-vehicle-classification-and-adaptation.md), [VD11](vd11-action-recognition.md), [CV08](../computer-vision/cv06-transfer-learning.md) |
| **You will produce** | One fine-tune you can defend line by line, and a written statement of which kind it is |

## Why this module exists

"Fine-tuned" is the most over-claimed verb in applied machine learning, and video is where the
over-claiming is most visible. This module separates the two things people mean by it, gives you
a recipe for each, and gives you the language to report exactly what you did.

**The distinction, stated once, plainly:**

| | Frame-level (image-model) fine-tuning | True temporal (video-model) fine-tuning |
| --- | --- | --- |
| Input unit | one frame | a clip, ordered |
| Pretrained on | images (ImageNet/COCO) | video (Kinetics, Something-Something) |
| Temporal layers | none | 3D conv, recurrent, or attention over time |
| Learns motion | **no** | yes |
| Data needed | hundreds of frames | thousands of clips |
| This section | **Lab 4** | not attempted; Lab 6 trains a temporal model **from scratch** |

Nothing in this section claims a temporal model was fine-tuned. Lab 4's own check says so:

```
[PASS] no temporal model is claimed here  (frame-level fine-tuning only; see Lab 6 ...)
```

## Part 1: frame-level fine-tuning of an image detector

This is the recipe Lab 4 runs, and it is the right one for detection, counting, and attributes -
tasks where the unit of decision is a frame or an object.

### Step 1: keep what fits, replace what does not

```python
from video_core.detect import TrafficSSDLite

model = TrafficSSDLite(score_threshold=0.6)
model.build()
print(model.pretrained_transfer)
# {'copied_tensors': 404, 'fresh_tensors': ...}
```

Copy by shape, not by name: an SSD's head tensors change shape when the class count changes from
91 to 5, and a name-based copy either crashes or silently loads a wrongly-shaped tensor. 404
tensors survived - the backbone and the regression path - and those are what make the word
"fine-tuned" accurate.

### Step 2: train on frames from the training videos only

```python
history = finetune_traffic_detector(epochs=5, stride=2, lr=3e-4, seed=0)
```

| Setting | Value | Why |
| --- | --- | --- |
| Epochs | 5 | 60 frames; more epochs overfit within minutes |
| Stride | 2 | 30 frames/video is enough and halves the cost |
| LR | 3e-4 | 10x below a from-scratch LR, because the weights are already good |
| Seed | 0 | reproducibility; set before model construction |
| Scope | `street_day`, `street_dusk` | validation and test clips are never trained on |

Measured cost: ~41 s on one CPU thread for 5 epochs. That is the honest scale of this recipe -
it is cheap because it is small, not because fine-tuning is cheap in general.

### Step 3: choose one operating point on validation

Five thresholds were swept on `street_quiet` (the validation clip) and 0.6 won on F1 (0.426).
That single number was then applied to all four test videos, once. The result:

| Video | zero-shot | fine-tuned | from scratch |
| --- | --- | --- | --- |
| quiet (val) | 0.000 | 0.156 | 0.289 |
| night | 0.000 | 0.033 | 0.096 |
| rain | 0.000 | 0.033 | 0.297 |
| shake | 0.100 | 0.295 | 0.443 |

Fine-tuning improved 4 of 4 held-out videos and still lost to a 138k-parameter model trained on
the target distribution. Both facts belong in the report.

### Step 4: say what you did, in one sentence

> "We fine-tuned a COCO-pretrained SSDLite320-MobileNetV3 for four vehicle classes: 404 tensors
> were transferred, the heads were reinitialised, and the network was trained for 5 epochs on 60
> frames from two training videos, with the score threshold selected on a separate validation
> video. The model is applied per frame; no temporal component was trained."

That sentence is auditable. "We fine-tuned a video model" is not.

## Part 2: what a true temporal fine-tune requires

If your task genuinely needs motion - action recognition, event detection, behaviour - then a
frame-level fine-tune is the wrong tool, and this is the honest shape of the right one.

| Requirement | Why | Typical numbers |
| --- | --- | --- |
| A video-pretrained backbone | image weights have no motion features | Kinetics-400, ~30 M+ parameters |
| Clip sampling | 8-32 frames per clip, temporal stride | 8-16 frames, stride 2-4 |
| A temporal head | 3D conv, (2+1)D, or transformer over time | replaces the 2D pool |
| Clip-level labels | the label is about a window, not a frame | thousands of clips |
| Compute | 3D conv is 3-10x a 2D conv per clip | GPU-hours, not CPU-seconds |
| Evaluation | clip accuracy, per-class F1, temporal IoU | never per-frame accuracy alone |

The cheapest credible version is **2D backbone + temporal head**, frozen backbone:

```python
# sketch: the shape of a temporal fine-tune, not implemented in this section
backbone = torchvision.models.mobilenet_v3_small(weights="IMAGENET1K_V1").features
for p in backbone.parameters():
    p.requires_grad = False                     # freeze: the data is small
head = nn.GRU(576, 64, batch_first=True)        # temporal layer, trained
classifier = nn.Linear(64, n_classes)
```

Freezing the backbone and training only the temporal head is what makes a temporal fine-tune
tractable on a small dataset - and it is exactly the experiment Lab 6 runs *from scratch* with a
23k-parameter encoder, arriving at 0.813 clip accuracy. The next step up is unfreezing the last
block, then the whole backbone, in that order, checking validation each time.

### Why this section does not run it

Three reasons, all of which belong in a report when you choose not to:

1. **No video-pretrained weights are compatible with a 60-frame synthetic dataset** in a way that
   would teach anything transferable; the domain is too far from Kinetics.
2. **The task is already solved by explicit temporal logic** (the tracker) at a fraction of the
   cost, and the tracker is debuggable in a way a 3D CNN is not.
3. **The honest comparison is the point.** Lab 6 shows what a temporal model buys *when the task
   needs one*; Lab 4 shows what a frame-level fine-tune buys *when the task does not*.

## Reporting checklist for any fine-tune

- [ ] Base model, its pretraining dataset, and its licence.
- [ ] What was transferred (count of tensors/layers), what was reinitialised.
- [ ] Exactly which videos/frames were trained on, and which were held out.
- [ ] Epochs, learning rate, batch size, augmentation, seed.
- [ ] How the operating threshold was chosen, and on which split.
- [ ] Whether any temporal layer exists. If none, say "frame-level" explicitly.
- [ ] The comparison baseline and its tuning (fairness both ways).
- [ ] Where it still fails, with a number.

## Common mistakes

| Mistake | Consequence | Fix |
| --- | --- | --- |
| Training and evaluating on frames from the same video | 0.9 mAP, useless system | split by video |
| Copying tensors by name | silently wrong shapes | copy by shape, count them |
| LR too high for a fine-tune | destroys pretrained features in one epoch | 10x below from-scratch |
| Re-tuning the baseline's threshold | unfair comparison | fix each model's point on val |
| Calling it a video model | inaccurate claim | name the input unit |
| Reporting only mAP | hides recall collapse | print P/R/F1 and per-class |

## Checks

- [ ] You can state the difference between the two kinds of fine-tuning in one sentence.
- [ ] You can name the 404 transferred tensors and why the count matters.
- [ ] You can list the four requirements a true temporal fine-tune adds.
- [ ] You can write an auditable one-sentence description of your own fine-tune.
- [ ] You can explain why fine-tuning beat zero-shot 4/4 and still lost to a smaller model.
