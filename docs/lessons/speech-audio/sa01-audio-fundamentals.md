# SA01 - Audio fundamentals: sampling, amplitude, frequency, channels {#sa01}

**Section path:** [Overview](index.md) · **Module 1** · [Lab B](labs/lab-b-waveform-vs-spectrogram.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 3 hours: 1.5 h reading, 1.5 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | F03 (NumPy), F04 (pandas) |
| **You will produce** | A table of sample counts and file sizes you computed by hand, and a resampling experiment |

## Why this module exists

Every audio bug that is not a modelling bug is a units bug. A file is 44.1 kHz and the
model expects 16 kHz, so it transcribes gibberish. A stereo recording is fed in as
interleaved samples, so the "speech" is two people at half speed. A clip is passed as
int16 where the code expects floats in [-1, 1], so every sample clips and the model
learns from white noise. None of these raise an exception.

Four numbers describe an audio file completely, and you should be able to derive the
fifth (file size) without opening it.

## The four numbers

| Quantity | Symbol | Typical speech value | What it controls |
| --- | --- | --- | --- |
| Sample rate | `sr` | 16,000 Hz | Highest frequency you can represent: `sr/2` |
| Duration | `t` | 0.3-10 s | Number of samples: `n = sr * t` |
| Channels | `c` | 1 (mono) | Storage layout: interleaved, `n * c` values |
| Bit depth | `b` | 16 | Amplitude resolution: `2^b` levels |

A one-second, 16 kHz, mono, 16-bit recording is `16000 * 1 * 2 = 32,000` bytes of sample
data plus a 44-byte WAV header. This repository's generated files are exactly that:
`audio.wav_info()` on a one-second clip reports `bytes: 32044`.

```python
from speech_core import audio

info = audio.wav_info("data/audio/env/env_0000.wav")
# {'file': 'env_0000.wav', 'sample_rate': 16000, 'channels': 1, 'bit_depth': 16,
#  'frames': 16000, 'duration_s': 1.0, 'rms': 0.043, 'peak': 0.10855, 'bytes': 32044}
```

`frames` is the number of samples per channel. For mono, `frames == n`. The 44 extra
bytes are the RIFF/WAVE header: `read_wav` hides it, but a storage estimate that ignores
it is wrong by 0.14% per file - which matters when you have a million files.

## Sampling rate and the Nyquist limit

A sample rate of 16,000 Hz can represent frequencies up to 8,000 Hz, the Nyquist
frequency. Anything above that is not merely lost; it is **aliased** back into the
signal as a lower frequency.

```text
tone at 3 kHz, sampled at 16 kHz   -> appears at 3 kHz      (correct)
tone at 6 kHz, sampled at 16 kHz   -> appears at 6 kHz      (correct, below 8 kHz)
the same tone decimated 4x to 4 kHz -> appears at 2 kHz     (6 kHz folds to 4 - 2)
tone at 9 kHz, sampled at 16 kHz   -> appears at 7 kHz      (16 - 9, aliased)
```

Speech intelligibility lives between 300 Hz and 4 kHz, which is why telephony used
8 kHz sampling and why 16 kHz is the standard for speech recognition: it captures the
consonants that distinguish "s" from "f". Music needs 44.1 kHz because cymbals and
harmonics extend past 10 kHz.

```python
import numpy as np
from speech_core import synth, features

tone = synth.tone(6000.0, 0.5, 16_000)      # 6 kHz: fine at 16 kHz sampling
down = tone[::4]                             # decimate to 4 kHz the naive way
spec = features.power_spectrogram(down, sample_rate=4_000, n_fft=400)
peak_hz = int(np.argmax(spec.mean(axis=0))) * (4_000 / 400)
# peak_hz == 2000, not 6000: the tone folded to 2 kHz with no filter in the way
```

The lesson is not "never decimate"; it is "resample with a filter", which is what
`audio.resample` does using `scipy.signal.resample_poly`. Naive slicing is a filterless
decimation and aliases everything above the new Nyquist.

!!! warning "Resample before you train, not after you fail"
    A recogniser trained on 16 kHz clips and fed 44.1 kHz clips will not error. It will
    produce wrong text with high confidence. The interface in
    [Lab F](labs/lab-f-stt-interface.md) resamples and reports what it changed.

## Amplitude, decibels, and the float convention

Digital amplitude is a number per sample. Two conventions coexist and mixing them is a
classic bug:

* **int16**: -32768 to 32767, what a 16-bit WAV stores.
* **float**: -1.0 to 1.0, what every model and DSP library expects.

`audio.to_float` and `audio.to_int16` convert with clipping, never wrapping. A float
value of 1.4 written with a cast to int16 wraps to a large negative number - a click that
sounds like damage.

Decibels are a ratio, not a unit:

```text
dB = 20 * log10(amplitude / reference)      for amplitude
dB = 10 * log10(power / reference)          for power
-6 dB  -> amplitude x 0.501
+6 dB  -> amplitude x 1.995
```

```python
from speech_core import audio, synth

clip = synth.tone(440.0, 0.3, 16_000, amplitude=0.5)
quieter = audio.change_gain(clip, -6.0)
print(round(float(quieter.max()), 3))     # 0.251: half the amplitude
print(round(audio.rms(clip), 4), round(audio.rms(quieter), 4))
# 0.3496 0.1752 - RMS halves too, because RMS is amplitude-like
```

Mean squared amplitude is power; RMS is its square root and behaves like amplitude.
`audio.snr_between(reference, estimate)` reports the ratio of signal power to error
power, which is how every noise experiment in this section is specified.

## Frequency: what "a 440 Hz tone" means

A pure tone is `sin(2 * pi * f * t)`. Real sounds are sums of many frequencies with
different phases. The Fourier transform answers "how much of each frequency is in this
window", and the short-time Fourier transform answers it per 25 ms window, which is how a
spectrogram is built.

```python
from speech_core import synth, features
import numpy as np

tone = synth.tone(440.0, 0.3, 16_000)
spec = features.power_spectrogram(tone, sample_rate=16_000, n_fft=400)
# 400-point FFT at 16 kHz -> 201 bins, 40 Hz apart
peak_bin = int(spec.mean(axis=0).argmax())      # 11
print(peak_bin * 40)                            # 440 Hz
```

Frequency resolution and time resolution trade off. A 400-sample window (25 ms) gives
40 Hz bins and smears events shorter than 25 ms; a 1024-sample window gives 15.6 Hz bins
and smears 64 ms. Speech recognition standardised on 25 ms windows with a 10 ms hop
because that matches the timescale of a phoneme.

## Channels and layouts

Stereo is two channels interleaved: `[L0, R0, L1, R1, ...]`. Reading it as mono gives an
alternating signal at half the original rate - speech that sounds like it is under water.

```python
from speech_core import audio
import numpy as np

stereo = np.array([[0.2, 0.4], [0.6, 0.8]], dtype=np.float32)  # (frames, channels)
mono = audio.to_mono(stereo)          # averaged: [0.3, 0.7]
```

Averaging can cancel a signal that is out of phase between channels. For speech from one
microphone this is rare; for a stereo music mix it is a real risk, which is why
downmixing is a decision to record, not a detail to hide.

## Expected results you can reproduce

Run this and compare - every number below is measured, not illustrative:

```python
from speech_core import audio, synth, features
import numpy as np

samples = synth.tone(440.0, 0.25, 16_000)
print(len(samples))                              # 4000
print(features.power_spectrogram(samples, n_fft=400).shape)   # (26, 201)
print(round(audio.rms(samples), 4))              # 0.2093 (the 5 ms fades cost a little RMS)
resampled = audio.resample(samples, 16_000, 8_000)
print(len(resampled))                            # 2000
print(round(len(resampled) / 8000, 3))           # 0.25 - same duration
```

The spectrogram has 26 frames: `1 + (4000 + 400 - 400) // 160`. Note that `stft` with
`center=True` pads by half a window on each side, so the first frame is centred on sample
0 rather than starting there.

## Debugging advice

| Symptom | Likely cause | Check |
| --- | --- | --- |
| Speech sounds slow and deep | read as stereo when it is mono, or wrong sample rate | `wav_info(path)["channels"]`, compare `frames / sample_rate` to the real duration |
| Transcribe returns empty or garbage with no error | model input not resampled to 16 kHz | print `len(samples) / sample_rate` and compare with the file |
| Waveform looks like a solid block | samples are int16 but treated as float | `max(abs(samples))` > 1.5 means unscaled integers |
| Everything clips at ±1 | gain applied after normalisation | `peak_normalize` last, or lower the gain |
| A click at the start or end | fades missing | `synth` applies 5 ms fades; your own concatenation must too |
| Spectrogram is all one colour | dB conversion with the wrong reference | `power_to_db(..., ref=power.max())` puts the loudest bin at 0 dB |

## Exercises

1. Compute the file size of a 10-minute 44.1 kHz stereo 16-bit recording, and of the
   same audio at 16 kHz mono. Which is 30x smaller, and what does that cost?
2. Generate a 12 kHz tone at 44.1 kHz, decimate by 4 without filtering, and find the
   aliased peak. Then repeat with `audio.resample` and explain the difference.
3. Take a stereo clip you make by mixing two tones, downmix it, and show a case where
   averaging loses one of them (hint: invert one channel).
4. Show that a 25 ms window smears a 5 ms burst: compare `n_fft=400` and `n_fft=1024`
   spectrograms of a click.

Next: [SA02 - Loading, playing, visualising, and preprocessing audio](sa02-loading-and-preprocessing.md)
