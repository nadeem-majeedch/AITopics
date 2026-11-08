# SA05 - Audio classification with traditional machine learning {#sa05}

**Section path:** [Overview](index.md) · **Module 5** · [Lab A](labs/lab-a-environmental-sound-classifier.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 2 h reading, 2 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | SA03, SA04, F07-F10 |
| **You will produce** | Three classical baselines with the same split, and an argument for which one you would ship |

## Why this module exists

Before a neural network, there were working audio classifiers: nearest centroid on Mel
statistics, k-nearest neighbours, logistic regression, and later SVM and random forest on
MFCCs. They are still the right first experiment, for three reasons.

1. **They are fast.** Seconds, not minutes, so you can try five feature sets in the time a
   CNN takes to finish one epoch.
2. **They expose the features.** A logistic regression on 80 Mel statistics either finds a
   separating hyperplane or it does not; a CNN can hide a broken feature pipeline behind
   enough capacity.
3. **They set the floor.** If a CNN does not beat k-NN on identical features, the CNN is
   not earning its complexity - and on this corpus that is exactly what happens.

## Turning a clip into a vector

Classical models need a fixed-length vector. The simplest useful one is the mean and
standard deviation of each Mel band over time:

```python
import numpy as np
from speech_core import features

def clip_vector(samples, sample_rate=16_000, n_mels=40):
    mel = features.mel_spectrogram(samples, sample_rate=sample_rate, n_mels=n_mels)  # (T, n_mels)
    return np.concatenate([mel.mean(axis=0), mel.std(axis=0)])                      # (2 * n_mels,)
```

Averaging over time discards *when* things happened. For environmental sounds with a
steady character that is fine; for speech it destroys most of the information, which is why
recognition needs sequence models. This trade-off is the reason feature engineering for
audio died: hand-built summaries cannot represent timing.

Other classical choices, and what they cost:

| Feature | Dimensions | Keeps timing? | Notes |
| --- | --- | --- | --- |
| Mel mean + std | 80 | no | strong baseline, used here |
| MFCC mean + std | 26 | no | compact, decorrelated |
| Mel spectrogram flattened | 101 x 40 | yes | huge, needs many samples |
| Frame-level MFCC + delta | 39 per frame | yes | needs a sequence model to use |
| Chroma / spectral contrast | 12-20 | partly | music-oriented, rarely useful for speech |

## Three baselines, measured

Same grouped split, same 80-dimensional Mel statistics, standardised with training
statistics only:

| Model | Test accuracy | Notes |
| --- | --- | --- |
| Nearest centroid | 0.778 | one prototype per class, Euclidean distance |
| k-NN (k=5) | 1.000 | no training at all |
| Logistic regression | 1.000 | multinomial, C=1.0, 2,000 iterations |

```python
import numpy as np

def nearest_centroid(train_x, train_y, test_x, n_classes):
    mu, sd = train_x.mean(axis=0), train_x.std(axis=0) + 1e-6
    train_z, test_z = (train_x - mu) / sd, (test_x - mu) / sd
    centres = np.stack([train_z[train_y == c].mean(axis=0) for c in range(n_classes)])
    distances = np.linalg.norm(test_z[:, None, :] - centres[None, :, :], axis=2)
    return distances.argmin(axis=1)
```

The standardisation matters: Mel band energies differ by tens of dB across frequency, so
unscaled Euclidean distance is dominated by the loudest band. Fitting the mean and standard
deviation on the training split and applying them to test is the same discipline as in
neural training, for the same reason.

## Reading these numbers honestly

Three of four models reach 1.000, and nearest centroid reaches 0.778. That is not evidence
that audio classification is easy; it is evidence that **this corpus is easy**. Four
synthetic classes, one sound per clip, no overlapping events, no reverberation, and a
source-level split with 56 training sources.

What you can still learn from a saturated result:

* **Which class the weak model fails on.** Nearest centroid's 0.778 comes from specific
  confusions, and [Lab B](labs/lab-b-waveform-vs-spectrogram.md) shows the class centroids
  that cause them.
* **What a real degradation does.** Lab A's robustness table drops to 0.667 at 5 dB SNR and
  0.778 at -12 dB gain, for a network trained on this same easy corpus.
* **Whether the split is honest.** A perfect score on a leaky split is worthless; the
  audit is what makes 1.000 meaningful.

When you meet a benchmark where every method scores above 0.99, assume the benchmark is
saturated and go find a harder one - not that the problem is solved.

## Class imbalance and class weights

The corpus is balanced (60 clips per class), so no weights are needed. Real corpora are
not: an alarm detector sees thousands of hours of non-alarm. Two standard responses:

```python
from speech_core import training

counts = [60, 60, 60, 60]
weights = [sum(counts) / (len(counts) * c) for c in counts]   # inverse frequency
training.train_classifier(..., class_weights=weights)          # torch CrossEntropyLoss
```

The second response is to change the metric: accuracy is meaningless at 1% prevalence, so
report recall at a fixed false-positive rate instead (Module SA14).

## Cross-validation for small corpora

With 240 clips, a single 168/36/36 split is noisy. Grouped k-fold gives a range:

```python
import numpy as np
from speech_core import datasets

sources = sorted({r.source_id for r in records})
folds = np.array_split(np.random.default_rng(0).permutation(sources), 5)
for fold in folds:
    held_out = set(fold)
    train = [r for r in records if r.source_id not in held_out]
    test = [r for r in records if r.source_id in held_out]
    ...  # fit on train, score on test, collect
```

Group by source inside every fold, or the folds leak in exactly the way the outer split was
designed to avoid.

## Debugging advice

| Symptom | Cause | Fix |
| --- | --- | --- |
| k-NN accuracy is 1.000 but centroid is 0.78 | classes are multi-modal, one prototype is not enough | try k=3-5 centroids per class, or accept k-NN |
| All predictions are one class | features not standardised, or a constant feature | check `X.std(axis=0).min()` |
| Training accuracy 1.0, test 0.3 | split leaks are absent but the corpus is tiny | more sources, augmentation |
| Logistic regression will not converge | unscaled features or `max_iter` too low | standardise, raise `max_iter` |
| Accuracy changes by 0.1 between runs | 36 test clips is a small sample | report a confidence interval or use k-fold |

## Exercises

1. Reproduce the three baselines. Then shuffle the labels and confirm all three fall to
   chance - a sanity check that catches leakage in the *pipeline*.
2. Compute a 95% Wilson interval for 36/36 correct. How many test clips would you need to
   distinguish 0.95 from 1.00?
3. Replace the Mel mean/std vector with a flattened 1 s Mel spectrogram and retrain k-NN.
   What happens, and why?
4. Add Gaussian noise at 10 dB SNR to the test set only. Which baseline degrades least, and
   does that match the CNN in Lab A?

Next: [SA06 - A basic neural audio classifier](sa06-neural-audio-classifier.md)
