# VD05 - Image models versus temporal video models {#vd05}

**Section path:** [Overview](index.md) · **Module 5** · [Lab 6](labs/lab-6-action-recognition.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 2 h reading, 2 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | [VD04](vd04-labelling-and-annotation-formats.md), [F13](../index.md#foundation-sequence) |
| **You will produce** | A written justification of whether your model is temporal, with a measurement that supports the claim |

## Why this module exists

There is a sentence that appears in far too many project reports: *"We fine-tuned a video
model."* It is usually false. What happened is that a still-image network was run once per
frame, and the frames were never compared to each other. The system is then described as
temporal, evaluated as if it were temporal, and deployed into a task - an action, a direction,
an event - whose answer exists only in the differences between frames.

This module gives you the vocabulary to tell the two apart, and a measurement that decides it.

## What a frame model can and cannot see

An image model receives one frame `x_t` and returns `f(x_t)`. Whatever it knows about time, it
knows from a single instant.

| Task | Decidable from one frame? | Why |
| --- | --- | --- |
| Is there a vehicle in this frame? | yes | appearance |
| Which class of vehicle? | mostly | shape, size |
| Is it raining? | mostly | wet road, spray |
| Which way is it moving? | **no** for a symmetric vehicle; yes if motion blur or pose gives it away | direction is a difference |
| Is a person walking left or right? | **no** | a walk cycle is symmetric in time |
| Did a vehicle cross the line? | no | needs two positions |
| Is someone falling? | no | the answer is the transition |

The last three are the tasks this section's later labs are about, and they are exactly the
tasks where a frame model's accuracy sits at chance while a temporal model does well. Lab 6
measures it: per-frame accuracy 0.447 on a 5-class motion task (chance is 0.20), majority
voting the clip's frames 0.507, a small temporal model 0.813.

Per-frame 0.447 is not "the model is bad". It is "the information is not there". A frame model
on a direction task can only use cues like the vehicle's orientation or a motion trail - it
never sees where the vehicle was a moment ago, because it has no memory.

## The five architectures, in the order you will meet them

| Family | Idea | Temporal? | Cost | Typical use |
| --- | --- | --- | --- | --- |
| **Per-frame 2D CNN** | classify each frame independently | no | cheapest | detection, attributes |
| **Frame + vote** | majority over per-frame predictions | weakly | same as per-frame | a baseline you must report |
| **2D CNN + recurrent head** | features per frame, then GRU/LSTM over the sequence | yes | +small | action recognition, small data |
| **3D CNN / (2+1)D** | convolve over space and time jointly | yes | 3-10x | action recognition at scale |
| **Transformer over tokens** | attention across space-time patches | yes | large | modern video backbones |

This section implements the first three, because they fit on a CPU and because the difference
between them is the lesson. The fourth and fifth are named so you know what you are choosing
not to use, and Module 12 says when that choice is wrong.

### Frame + vote is not temporal

Majority voting looks like it uses time. It does not: each frame is classified in isolation,
then a fixed rule combines the outputs. It cannot learn *"the object was on the left, now it is
on the right"*, because no feature ever encodes a change. It does reduce variance - Lab 6 shows
0.447 → 0.507 - which is why it is a fair baseline and an unfair final answer.

The honest description is: *"a per-frame classifier with a majority-vote aggregation; it has no
temporal receptive field."* That sentence is what a reviewer needs.

### What "temporal" actually means

A model is temporal if its output depends on the **order** of frames, not just their set. Two
tests decide it:

1. **Shuffle test.** Permute the frames of a clip and re-run. A temporal model's output changes;
   a frame model's does not. Lab 6 reports the frame model's stability as 0.49 (frames within a
   clip agree only half the time) and the temporal model's accuracy as unchanged under the
   training-order it was built for - the shuffle test is the reason a recurrent head must be
   evaluated on ordered clips.
2. **Reverse test.** Play the clip backwards. A direction-sensitive model should flip its
   prediction; a frame model will not.

Run both before you write the word "temporal" in a report.

## The code, side by side

Both models are deliberately small enough to train in seconds on a CPU.

```python
from video_core import actions

# Per-frame: one frame in, one label out. No memory.
frame_model = actions.FrameClassifier(n_classes=5)
per_frame = actions.predict_frames(frame_model, clips)          # (N, 8) - one label per frame
voted = actions.frame_vote_predictions(frame_model, clips)      # (N,)   - majority per clip
print(actions.stability(per_frame))                             # how often frames agree

# Temporal: a whole ordered clip in, one label out. A GRU carries state across frames.
temporal_model = actions.TemporalClassifier(n_classes=5, hidden=64)
clip_labels = actions.predict_temporal(temporal_model, clips)   # (N,)
```

`clips` is a float array of shape `(N, 8, 64, 64)`; `predict_frames` reshapes it to `(N*8, 64,
64)` internally, which is exactly the point - the frame model never sees the 8 as a sequence.

Parameters, measured: the frame model has 23,845; the temporal model 48,805. Latency for one
8-frame clip: 0.65 ms versus 0.69 ms. The temporal model is barely more expensive - the cost of
temporality here is 6% of latency, not an order of magnitude. That is a useful correction to
the folk belief that temporal models are prohibitively expensive at small scale.

### The receptive field, in time

A GRU with hidden size 64 over 8 frames has a temporal receptive field of the whole clip: the
last hidden state has seen all 8 frames. A 3D convolution with kernel 3 and stride 1 sees 3
frames at a time at the first layer, 5 at the second, and so on. If your action takes 2 seconds
to unfold at 10 fps, an 8-frame clip cannot see it - and no amount of training fixes a
receptive field that is too short. Choose clip length from the duration of the event, not from
what fits in memory.

## The claim rule

Use this table when writing up a video system:

| What you did | What you may write | What you may not write |
| --- | --- | --- |
| Loaded a pretrained image detector, ran it per frame | "a pretrained image detector applied per frame" | "a video model" |
| Fine-tuned that detector on frames from your videos | "a frame-level fine-tune of an image detector on video frames" | "fine-tuned a video model" |
| Trained a 2D CNN on clips, no temporal head | "a frame classifier, aggregated by voting" | "temporal modelling" |
| Trained a CNN+GRU on ordered clips | "a temporal model over 8-frame clips" | "state of the art on video" |
| Fine-tuned a pretrained 3D backbone | "a fine-tuned temporal backbone" | "we solved tracking" |

The rule behind the table: **the claim must name the architecture and the unit of input**. If
the unit of input is a frame, the model is an image model, however it is used.

This section's own honest position: Labs 2-5 use an image detector per frame and a frame-level
fine-tune (Lab 4 copies 404 tensors from the pretrained SSDLite backbone into a traffic-head
model). No temporal model is trained anywhere in this section except Lab 6, which trains a
small CNN+GRU from scratch and reports it as such. Module 13 covers what a true temporal
fine-tune would require and why this section does not pretend to do one.

## When a frame model is the right answer

Temporality is not a virtue; it is a cost you pay for information you need.

- **Detection** is largely per-frame. The box in frame *t* does not need frame *t-1* to exist.
  Temporal information helps by *smoothing* detections across frames - which is what a tracker
  does, more cheaply and more interpretably than a 3D detector.
- **Attributes** (colour, category) are per-frame or per-object-crop. Lab 5's garment model is
  an image model by design, and that is correct.
- **Counting** is temporal, but the temporality lives in the tracker, not the detector: the
  counter needs identity over time, and `video_core.tracking` provides it.

So the architecture of a real system is usually: **image model per frame + explicit temporal
logic**. That is not a compromise; it is the design that lets you debug each part.

## Checks

- [ ] You can name three tasks that are undecidable from a single frame.
- [ ] You can explain why majority voting is not temporal, in one sentence.
- [ ] You can run the shuffle test on a model and say what a change in output proves.
- [ ] You can state the parameter and latency cost of the temporal head in Lab 6 (48,805 vs
      23,845; 0.69 ms vs 0.65 ms per 8-frame clip).
- [ ] You can rewrite a false "video model" claim into an accurate one without losing meaning.
