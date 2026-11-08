# SA12 - Audio event detection and environmental sound classification {#sa12}

**Section path:** [Overview](index.md) · **Module 12** · [Lab A](labs/lab-a-environmental-sound-classifier.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 2 h reading, 2 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | SA03, SA06, SA08 |
| **You will produce** | A clip classifier, a frame-level detector, and a threshold sweep with precision and recall |

## Why this module exists

"Audio classification" and "audio event detection" are usually the same model with
different evaluation. Classification says *which sound is in this clip*; detection says
*when each sound occurs, in a stream that contains several*. The distinction decides your
labels, your loss, your metric, and whether your system can run on an endless stream at all.

This module builds the clip-level version (already in [SA06](sa06-neural-audio-classifier.md)),
adds a frame-level detector, and measures both with metrics that match the task.

## Clip-level versus frame-level

| | Clip classification | Event detection |
| --- | --- | --- |
| Input | 1 s clip | continuous stream |
| Output | one label per clip | a set of (onset, offset, class) |
| Labels needed | one per clip | time boundaries per event |
| Typical metric | accuracy, per-class recall | segment F1, event F1 with a collar, mAP |
| Can events overlap? | no | yes, and that is the hard part |
| This section's example | 4 environmental classes | energy-gated speech/background |

Multilabel detection is where the difficulty lives: a street recording contains traffic,
speech, and a horn at once, and a softmax over classes cannot represent that. The usual fix
is one sigmoid per class with a binary loss, plus a post-processing step that turns
per-frame probabilities into events.

## A frame-level detector you can reason about

Energy gating is the simplest detector: label a frame as "sound present" when its RMS
exceeds a threshold. It cannot tell you *what* the sound is, but it is the right first
component of any detector - you do not want to run a classifier on silence.

```python
import numpy as np
from speech_core import audio

def energy_mask(samples, sample_rate, threshold):
    frame, hop = int(0.02 * sample_rate), int(0.01 * sample_rate)
    mask = np.zeros(len(samples), dtype=bool)
    for start in range(0, len(samples) - frame, hop):
        if audio.rms(samples[start : start + frame]) > threshold:
            mask[start : start + frame] = True
    return mask
```

Measured against the diarization truth (6 turns, 3.48 s, speech in 2.06 s of it):

| Threshold (RMS) | Precision | Recall |
| --- | --- | --- |
| 0.005 | 0.948 | 1.000 |
| 0.010 | 0.948 | 0.985 |
| 0.020 | 0.969 | 0.949 |
| 0.040 | 0.991 | 0.655 |

The sweep is the whole lesson: there is no single correct threshold, only a trade-off curve.
Choose the operating point from the cost of the two errors. For a voice assistant, a false
positive costs a wasted recognition pass; for a glass-break alarm, a false negative is the
failure you are trying to prevent.

## Metrics that match the task

Accuracy is the wrong metric for detection, for three reasons: events are rare (most frames
are background), the boundaries are fuzzy (a 30 ms offset is not an error), and events
overlap.

| Metric | Definition | When to use |
| --- | --- | --- |
| Frame precision / recall | per-frame correctness | quick debugging, class-agnostic |
| Segment-based F1 | an event counts if it overlaps truth by > 50% | DCASE-style detection |
| Event F1 with collar | onset within ±200 ms counts | onset-sensitive tasks |
| mAP | area under precision-recall across thresholds | comparing detectors without picking a threshold |

```python
truth = np.zeros(len(samples), dtype=bool)
for segment in truth_segments:
    truth[int(segment["start"] * sr) : int(segment["end"] * sr)] = True
predicted = energy_mask(samples, sr, 0.02)
tp = int(np.sum(predicted & truth)); fp = int(np.sum(predicted & ~truth)); fn = int(np.sum(~predicted & truth))
precision = tp / max(tp + fp, 1)
recall = tp / max(tp + fn, 1)
```

Those three counts - not the F1 - are what you report. F1 hides which error dominates.

## The clip-level baseline, measured

[Lab A](labs/lab-a-environmental-sound-classifier.md) trains a convolutional classifier on
four classes and reports, on 36 held-out clips:

| Class | Precision | Recall | Support |
| --- | --- | --- | --- |
| alarm | 1.000 | 1.000 | 3 |
| rain | 1.000 | 1.000 | 12 |
| footsteps | 1.000 | 1.000 | 15 |
| birdsong | 1.000 | 1.000 | 6 |

Those supports are the real story. With 3 alarm clips in the test set, a single mistake moves
alarm recall by 0.33, so the table cannot distinguish a good model from a lucky one. A
detection benchmark needs thousands of events, which is why DCASE tasks are built on
multi-hour recordings rather than a few hundred clips.

## Building the pipeline properly

```text
stream -> frame features (log-Mel, 25 ms/10 ms)
       -> per-frame scores (CNN or CRNN over a context window)
       -> smoothing (median filter over 3-5 frames)
       -> thresholding per class
       -> event assembly (merge gaps < 100 ms, drop events < 100 ms)
       -> output events
```

Two steps there are usually skipped by students and always present in working systems:

* **Smoothing.** Frame scores flicker; a median filter over 3-5 frames removes isolated
  spikes without moving onsets much.
* **Event assembly.** A detector that fires on 4 consecutive frames has detected one event,
  not four. Merging and minimum-duration rules turn frames into events.

## Data and labelling for detection

Clip labels are cheap; event labels are expensive. Practical options, in order of cost:

1. **Weak labels** (clip contains class X) plus multiple-instance learning.
2. **Synthetic mixtures**: mix isolated clips at known times, so the labels are exact.
   `datasets.make_diarization_mix` does exactly this for speakers, and the same trick works
   for sound events.
3. **Strong labels** by hand: annotate onsets and offsets in an audio editor, with a written
   protocol and a second annotator for a subset to measure agreement.

This section uses option 2, which is why the truth file is exact and why the numbers look
better than a field recording would.

## Debugging advice

| Symptom | Cause | Fix |
| --- | --- | --- |
| Precision 1.0, recall 0.2 | threshold too high | lower it, look at the sweep |
| Everything detected | threshold below the noise floor | check `audio.rms` of a silent region |
| Events merge into one long event | gap tolerance too large | lower `max_gap` in assembly |
| Same event counted twice | onset detection triggering on both edges | hysteresis: separate on/off thresholds |
| F1 high but onsets late | frame-level metric ignores timing | add an onset collar to the metric |

## Exercises

1. Reproduce the threshold sweep and pick the operating point for (a) a voice assistant and
   (b) a smoke alarm. Justify both.
2. Build a two-event synthetic mix (alarm over rain) and show that a softmax classifier
   cannot represent it. What output layer would?
3. Add a 5-frame median filter to the energy mask and re-measure precision and recall. Which
   one improves?
4. Compute event F1 with a ±200 ms collar for the energy detector against the six-turn truth.
   Compare with the frame-level numbers.

Next: [SA13 - Building a voice-enabled chatbot](sa13-voice-chatbot.md)
