# SA03 - Waveforms, spectrograms, and Mel spectrograms {#sa03}

**Section path:** [Overview](index.md) · **Module 3** · [Lab B](labs/lab-b-waveform-vs-spectrogram.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 2 h reading, 2 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | SA01, SA02 |
| **You will produce** | Three representations of the same clip, their shapes, and a measured comparison of which one a weak classifier can use |

## Why this module exists

The waveform is the signal. It is also the worst representation for a model, because
amplitude against time hides the structure that distinguishes sounds. Two clips can have
almost identical waveforms - same length, same loudness - and be an alarm and birdsong.

The spectrogram is the representation that works, and the Mel spectrogram is the version
every speech system uses. This module derives both from the Fourier transform in a few
lines, so that the parameters (`n_fft`, hop, number of Mel bands) stop being magic
numbers and become choices with consequences.

## The short-time Fourier transform

Speech is not stationary: the spectrum changes as the mouth moves. The STFT cuts the
signal into overlapping windows and takes a Fourier transform of each:

```text
frame t  =  samples[t*hop : t*hop + win_length]  *  hann_window(win_length)
STFT[t]  =  rfft(frame_t, n=n_fft)               -> n_fft/2 + 1 complex bins
```

With a 16 kHz rate, `n_fft = 400`, `hop = 160`, `win_length = 400`:

* window = 25 ms, hop = 10 ms, so frames overlap by 60%;
* bins are `16000 / 400 = 40 Hz` apart, 201 bins from 0 to 8000 Hz;
* a 1 s clip yields `1 + (16000 + 400 - 400) // 160 = 101` frames.

```python
from speech_core import synth, features
import numpy as np

clip = synth.tone(440.0, 0.3, 16_000)
spec = features.power_spectrogram(clip, sample_rate=16_000, n_fft=400, hop_length=160)
print(spec.shape)                     # (31, 201)
print(int(np.argmax(spec.mean(axis=0))) * 40)     # 440 Hz
```

`center=True` pads by half a window on both sides, so frame 0 is centred on sample 0. Set
it to `False` and every timestamp shifts by 12.5 ms - small, systematic, and enough to
misalign frame-level labels.

## From power to decibels

Power is `|STFT|²`. It spans six orders of magnitude, so it is converted to dB with a
floor relative to the maximum:

```python
db = features.power_to_db(power, ref=power.max(), top_db=80.0)
```

`top_db=80` clips everything more than 80 dB below the peak, which prevents a silent band
from dominating colour maps and normalisation. Without the clip, one digital-silence
sample (-inf dB) makes the whole feature map NaN.

## The Mel scale

Human hearing is not linear in frequency: we distinguish 100 Hz from 200 Hz easily and
1000 Hz from 1100 Hz hardly at all. The Mel scale warps frequency to match:

```text
mel(f) = 2595 * log10(1 + f / 700)
```

A Mel filterbank places 40 triangular filters evenly on the Mel scale between 20 Hz and
8 kHz. Low bands are narrow (fine resolution where speech energy is), high bands are wide.

```python
bank = features.mel_filterbank(16_000, n_fft=400, n_mels=40)
print(bank.shape)                        # (40, 201)
print(round(float(bank.sum(axis=1).mean()), 5))    # 1.0 - each filter is area-normalised
centres = features.mel_band_frequencies(16_000, 40)
print(round(float(centres[0]), 1), round(float(centres[-1]), 1))   # 65.1 7487.0
```

Each row sums to one so a log-Mel value is comparable across filter widths; without that,
wide high-frequency bands would dominate every distance you compute.

## MFCCs: decorrelating the Mel bands

The discrete cosine transform of the log-Mel energies gives cepstral coefficients. They
decorrelate neighbouring bands, which made them ideal for Gaussian models in the 1980s and
still makes them useful for compact representations such as speaker embeddings.

```python
mfcc = features.mfcc(clip, sample_rate=16_000, n_mfcc=13)
print(mfcc.shape)          # (31, 13)
```

Coefficient 0 is overall energy, 1-3 carry the spectral envelope that distinguishes vowel
sounds, and higher coefficients carry mostly noise. This section's ASR uses log-Mel, not
MFCC, because convolutional networks handle correlated bands fine and Mel loses less.

## Visualising without matplotlib

`features.ascii_spectrogram` renders a Mel spectrogram into a character grid, and
`features.save_spectrogram_png` writes a PNG with Pillow. Both exist because a student on
a locked-down machine still needs to see the data.

```python
mel = features.mel_spectrogram(clip, n_mels=40)
print(features.ascii_spectrogram(mel, width=56, height=10))
features.save_spectrogram_png(mel, "outputs/clip.png", title="440 Hz tone")
```

Alarm and rain look nothing alike in that grid: an alarm is a repeating vertical bar (a
short burst repeating at a fixed rate), rain is a broadband wash that decays with
frequency. That visual difference is exactly what a convolutional classifier learns.

## Measured comparison

[Lab B](labs/lab-b-waveform-vs-spectrogram.md) trains the same nearest-centroid classifier
on three representations of the same four classes, with held-out sources:

| Representation | Dimensions | Accuracy |
| --- | --- | --- |
| Raw waveform (64 evenly spaced samples) | 64 | 0.472 |
| Mel spectrogram (mean + std over time) | 80 | 0.778 |
| MFCC (mean + std over time) | 26 | 0.778 |

The waveform is not useless - 0.472 is well above the 0.25 chance level, because loudness
and periodicity differ between classes. But it loses almost half of the available signal
structure, and it needs 64 numbers per clip to do it.

The Mel distances between class centroids explain the pattern:

| Pair | Mel distance |
| --- | --- |
| alarm vs birdsong | 30.9 |
| rain vs birdsong | 55.6 |
| alarm vs rain | 65.0 |
| rain vs footsteps | 152.0 |

The closest pair is where a weak classifier's errors come from; the farthest pair is why
two classes are never confused by this representation.

## Debugging advice

| Symptom | Cause | Fix |
| --- | --- | --- |
| Spectrogram is uniform grey | dB conversion with the wrong reference | use `ref=power.max()`, check `top_db` |
| All features are -80 | input is silence after trimming | lower `trim_silence` threshold, plot the waveform |
| Shape is `(40, T)` not `(T, 40)` | Mel matrix is band-major | transpose before feeding a time-major model |
| Frames = 1 for a whole clip | `n_fft` larger than the clip | pad the signal, or lower `n_fft` |
| MFCC 0 dominates every distance | coefficient 0 is energy | drop coefficient 0 before comparing clips |
| Same clip gives different features | normalisation statistics recomputed per clip | compute once on train, reuse |

## Exercises

1. Reproduce the 101-frame figure for a 1 s clip, then compute the frame count for
   0.29 s and explain the difference using the formula.
2. Change `n_mels` from 40 to 80 and 128. Which classes become easier and which become
   harder in Lab B's nearest-centroid test?
3. Show that `power_to_db` without `top_db` produces `-inf` for a digital-silence frame,
   and that this poisons the mean of the whole matrix.
4. Compute the Mel filterbank by hand for 8 bands: list the centre frequencies and check
   them against `mel_band_frequencies`.

Next: [SA04 - Segmentation, labelling, and dataset preparation](sa04-segmentation-and-datasets.md)
