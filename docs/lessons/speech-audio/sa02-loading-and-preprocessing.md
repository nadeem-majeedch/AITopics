# SA02 - Loading, playing, visualising, and preprocessing audio {#sa02}

**Section path:** [Overview](index.md) · **Module 2** · [SA01](sa01-audio-fundamentals.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 2 h reading, 2 h practice |
| **Hardware** | CPU-only; playback optional |
| **Prerequisites** | SA01, F03 |
| **You will produce** | A loader that survives real-world files, a preprocessing chain you can defend, and a peak/RMS report |

## Why this module exists

Between "a file on disk" and "a tensor a model can use" there are six decisions, and
each one silently changes the data if you get it wrong: channel handling, sample rate,
amplitude scaling, silence trimming, level normalisation, and padding. This module makes
each decision explicit and shows what breaks when it is made by accident.

The library situation is part of the lesson. Most tutorials begin with `librosa.load`,
`torchaudio.load`, or `soundfile.read`. Each is excellent and each brings a dependency
stack that fails on a locked-down laptop, a fresh Windows install, or a CI runner. This
section implements WAV I/O with the standard library's `wave` module, so the only hard
requirements are NumPy, SciPy for filtering and resampling, and PyTorch for the models.

## Reading a file without a framework

```python
from speech_core import audio

samples, rate = audio.read_wav("data/audio/speech/wavs/speech_0000.wav")
print(samples.dtype, samples.shape, rate)      # float32 (4671,) 16000
```

`read_wav` does four things, in order:

1. reads the header and **refuses anything that is not 16-bit PCM** rather than
   returning nonsense for a 24-bit or float WAV;
2. converts int16 to float32 by dividing by 32768;
3. averages channels if the file is stereo;
4. returns the rate, so the caller can decide whether to resample.

Refusing loudly on an unsupported format is a design choice. The alternative - best-effort
decoding - produces audio that is quieter or noisier than expected with no error, which is
much harder to debug than an exception.

```python
info = audio.wav_info(path)
# sample_rate, channels, bit_depth, frames, duration_s, rms, peak, bytes
```

`wav_info` is the function to call first on any unfamiliar file. If `channels` is 2 or
`sample_rate` is 44100, you already know why the model will fail.

## Playback without an audio device

```python
played, message = audio.play_wav(path)
print(played, message)
# False  "no audio device available (this environment is headless); use the WAV file"
```

Playback is the one operation that legitimately fails in a headless environment: a CI
runner, a container, or a remote VM has no sound card. Raising there would make every
exercise unrunnable, so `play_wav` returns `(False, reason)` and the caller decides. The
exercises never depend on hearing anything.

!!! tip "Listening is still part of the job"
    On your own machine, open the WAV files in any player. A spectrogram will not tell
    you that a clip is clipped, that two words are concatenated, or that the "silence" is
    a hum. Listen to at least a few files from every corpus you build.

## The preprocessing chain, decision by decision

```text
file -> mono -> resample to 16 kHz -> (optional) trim silence
     -> (optional) peak normalise -> feature extraction -> per-dataset normalisation
```

**Mono.** Average channels. Recorded speech from one microphone is usually already mono;
stereo usually means a music bed or two microphones, both of which change the problem.

**Resample to the model's rate.** Models are trained at one rate. `audio.resample` uses a
polyphase filter (`scipy.signal.resample_poly`), which is both fast and correct:

```python
from speech_core import audio
samples, rate = audio.read_wav("clip_44k.wav")   # rate == 44100
if rate != 16_000:
    samples = audio.resample(samples, rate, 16_000)
    rate = 16_000
```

**Trim silence.** `audio.trim_silence(samples, threshold=0.01, pad=160)` removes
leading/trailing near-silence and keeps 10 ms of margin. This matters for fixed-length
models: a clip that is 60% silence spends 60% of its capacity on nothing. It is also a
way to destroy information, because a quiet word at the start of a recording can fall
below the threshold.

**Peak-normalise.** `audio.peak_normalize(samples, target_db=-3.0)` scales the loudest
sample to -3 dBFS. It equalises clips recorded at different distances, and it does not
change the signal-to-noise ratio - noise is scaled with the speech.

**Pad or trim to a fixed length.** `audio.pad_or_trim(samples, n)` for frame-based
models. When padding a batch, pad with the *minimum* feature value, not zero: after dB
conversion a silent Mel band sits near -80, and a zero would look like a loud broadband
burst to the model.

```python
import numpy as np
from speech_core import audio, features, training

# What training.build_inputs does, in three lines:
mats = [features.mel_spectrogram(r.samples, sample_rate=r.sample_rate, n_mels=40) for r in records]
floor = float(min(m.min() for m in mats))
stacked = np.full((len(mats), 1, 40, max(m.shape[0] for m in mats)), floor, dtype=np.float32)
for i, mat in enumerate(mats):
    stacked[i, 0, :, : mat.shape[0]] = mat.T
```

## Dynamic range: why dB and why normalise statistics

Mel spectrograms are computed on power and converted to dB, which compresses the huge
dynamic range of audio (a whisper and a shout differ by ~60 dB, six orders of magnitude
in power). Two normalisations then apply:

* **per-clip**: peak or RMS normalisation, because microphones and distances differ;
* **per-dataset**: subtract the training mean and divide by the training standard
  deviation, because the network trains better on inputs near zero.

The second one is where the classic bug lives. The statistics belong to the training
set; at inference you must reuse the same numbers.

```python
rec = asr.Recognizer.load("outputs/recogniser.pt")   # keeps weights, vocab, mean, std
print(rec.mean, rec.std)                             # -30.95 22.95 for this corpus
```

`training.train_ctc` returns `mean` and `std` in its history, and
`asr.Recognizer` stores them next to the weights. If you build your own pipeline,
carry those two numbers with the checkpoint - a model file without them is incomplete.

## Expected results

Measured on the generated corpus (Windows 11, Python 3.12.10):

```text
speech clip   : 16 kHz, mono, 16-bit, 0.186-0.431 s (median 0.293 s)
wav_info      : frames 4671, duration_s 0.2919, rms 0.05507, peak 0.3251, bytes 9386
after trim    : 0.292 s - the synthesiser already fades, so almost nothing is removed
mel matrix    : (30, 40) for this clip at 25 ms windows / 10 ms hop
resample      : 44.1 kHz -> 16 kHz preserves duration to within one sample per second
```

## Debugging advice

| Symptom | Cause | Fix |
| --- | --- | --- |
| `ValueError: expected 16-bit PCM, found 24-bit` | 24-bit or float WAV | convert with any audio editor, or add a decoder deliberately |
| Model output is noise, no error | sample rate mismatch | check `wav_info`; resample before features |
| Clips are much shorter than expected | `trim_silence` threshold too high | lower to 0.005 and inspect the waveform |
| Loudness varies wildly between clips | no level normalisation | `peak_normalize` per clip, or RMS-normalise |
| Batch has a bright stripe at the end | zero padding in dB features | pad with the minimum value |
| `play_wav` returns False | headless machine | expected; use the file, or listen locally |

## Exercises

1. Take a 44.1 kHz stereo file, load it, and write three versions: original, mono,
   16 kHz. Report the byte size of each and the duration of each, and explain why the
   duration is unchanged.
2. Measure the RMS of the generated env corpus per class. Which class is quietest, and
   by how many dB?
3. Break the padding: switch the fill value in a copied `build_inputs` from the floor to
   0.0 and measure classifier accuracy with the same training budget.
4. Write a loader that accepts a folder of WAVs, reports every file whose sample rate or
   channel count differs from the rest, and resamples them.

Next: [SA03 - Waveforms, spectrograms, and Mel spectrograms](sa03-waveform-spectrogram-mel.md)
