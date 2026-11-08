# Lab A - Classify a small environmental-sound dataset

**Section path:** [Overview](../index.md) · Modules [SA04](../sa04-segmentation-and-datasets.md), [SA06](../sa06-neural-audio-classifier.md), [SA12](../sa12-audio-event-detection.md) · **Lab A** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 10% of the section assessment |
| **Time** | 3 hours |
| **Hardware** | CPU-only (about 20 s end to end) |
| **Code** | `projects/speech-audio/lab_a_env_classifier.py` |
| **Prerequisite** | SA03, SA04, SA06 |

## The task

Train a convolutional classifier on four synthesised environmental classes, then report it
honestly: accuracy on a source-disjoint split, the same model on a leaky split, per-class
recall, and a robustness table.

You must produce:

1. the split audit for both splits (shared sources, leak decision);
2. test accuracy on the grouped split, with per-class precision and recall;
3. the leaky-split accuracy and the difference;
4. a robustness table over noise, gain, rate, and bandwidth.

## Setup

```bash
python -m pip install -r requirements/audio.txt
python scripts/make_audio_data.py          # ~2 s, writes data/audio/ and the dataset card
cd projects/speech-audio
python lab_a_env_classifier.py             # full run
python lab_a_env_classifier.py --selftest  # 6 epochs, assertions only
```

The lab works if `data/audio` is missing: the corpus is regenerated in memory from the same
seeds, and the report says `origin: generated`.

## Run it

```text
=== corpus
origin      : disk  (E:\AITopics\data\audio)
clips       : 240  classes 4 ['alarm', 'rain', 'footsteps', 'birdsong']
sources     : 80
licence     : CC0-1.0
consent     : no human recordings; clips are generated from code
balance     : {'alarm': 60, 'rain': 60, 'footsteps': 60, 'birdsong': 60}

=== split audit
split                shared_sources  leaky
------------------------------------------
grouped by source    0               False
per clip (naive)     65              True

=== training (14 epochs, grouped split)
 1.0 | oooooooooo**o
 ...
best epoch 3, val accuracy 1.000, train-validation gap -0.042

=== test accuracy
accuracy 0.944 on 36 held-out clips (sources never seen in training)
class      precision  recall  f1     support
-------------------------------------------
alarm      1.000      1.000   1.000  3
rain       1.000      0.833   0.909  12
footsteps  1.000      1.000   1.000  15
birdsong   0.750      1.000   0.857  6
  biggest confusion: rain -> birdsong x2
```

!!! warning "A saturated result is a warning, not a win"
    Four classes, one sound per clip, held-out sources: the task is easy, and 0.944 here is
    34 correct clips out of 36, not a capability. Two misses are `rain`-as-`birdsong`. The
    robustness table below is where the model actually loses clips, and it is the number you
    should quote. With `models.set_seed` called before the network is built, these numbers
    reproduce exactly across runs and machines of the same torch build; see SA06.

Robustness, same model, 36 test clips perturbed:

| Condition | Accuracy | Drop vs clean | Mean confidence |
| --- | --- | --- | --- |
| clean | 0.944 | 0.000 | 0.816 |
| 20 dB SNR | 0.944 | 0.000 | 0.804 |
| 10 dB SNR | 0.889 | 0.056 | 0.739 |
| 5 dB SNR | 0.667 | 0.278 | 0.626 |
| -12 dB gain | 0.778 | 0.167 | 0.731 |
| slower 1.15x | 0.944 | 0.000 | 0.778 |
| narrowband 4 kHz | 0.972 | -0.028 | 0.715 |

Three rows deserve a sentence each. Confidence falls before accuracy does (0.816 -> 0.739 at
10 dB for 0.056 accuracy), which is useful only if the confidence is calibrated (SA14).
Narrowband *gains* accuracy (+0.028), because removing the high band also removes the noise
the closed-test set can afford - a single-seed curiosity, not a finding, and exactly the kind
of row students over-interpret. And -12 dB gain costs 0.167 without changing a single
spectral peak, which is a normalisation problem wearing a robustness costume.

## Checks the script performs

```text
PASS  grouped split has no shared source
PASS  naive split does share sources
PASS  accuracy in [0, 1]
PASS  clean condition equals test accuracy
PASS  noise at 5 dB is not better than clean
PASS  grouped accuracy beats chance
```

Exit code is 0 only when every check passes. `--selftest` runs 6 epochs and skips the
"beats chance" check so CI stays fast.

## What to look for

* **The leaky split inflates a little** (+0.056): the grouped model misses two `rain` clips
  that the leaky one gets, because the leaky split lets it see the same rain source in
  training. Compare with the computer vision section, where the same mistake added 0.111.
  Leakage costs what the variants are worth - here, little; that does not make it acceptable.
* **Supports of 3-15 clips.** One mistake changes a class recall by 0.07-0.33. The table is
  honest about its own noise if you read the support column.
* **Confidence tracks degradation earlier than accuracy**, which is the argument for
  monitoring confidence in production (SA14).

## Write-up requirements

1. The audit table and one sentence on why the decision is made on hard overlap.
2. Test accuracy with support counts, and the leaky number with the difference.
3. The robustness table, plus which condition you would fix first and how.
4. One paragraph: what would change if these were field recordings instead of synthesis.

## Independent extensions

* Lower `n_sources` to 10 and re-run: does the leaky split inflate now?
* Add random gain augmentation to training and re-measure the -12 dB row.
* Replace global average pooling with max pooling and compare the 5 dB row.

Next: [Lab B - Compare waveforms and spectrograms](lab-b-waveform-vs-spectrogram.md)
