# Lab B - Compare waveforms and spectrograms for different sound classes

**Section path:** [Overview](../index.md) · Module [SA03](../sa03-waveform-spectrogram-mel.md) · **Lab B** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 6% of the section assessment |
| **Time** | 2 hours |
| **Hardware** | CPU-only |
| **Code** | `projects/speech-audio/lab_b_waveform_vs_spectrogram.py` |
| **Prerequisite** | SA01, SA03 |

## The task

Look at the same four classes through three representations, then measure which one a weak
classifier can actually use.

You must produce:

1. the waveform and spectrogram of one alarm and one rain clip, side by side;
2. the band-energy table per class;
3. nearest-centroid accuracy for raw waveform, Mel, and MFCC;
4. the closest and farthest class pairs in Mel space, and what that implies.

## Run it

```bash
cd projects/speech-audio
python lab_b_waveform_vs_spectrogram.py
```

```text
=== what the waveform looks like
-- alarm (1.00s, RMS 0.064)
 ...
=== what the spectrogram looks like
-- alarm: 40 Mel bands x 101 frames (bright = loud, low bands at the bottom)
::.:..:::..:.:::...:::::::::::::-:::::-:
:::::::.::::#%#::::-*#-::.::::::::::::::
 ...
saved outputs/lab_b_alarm.png
```

The alarm spectrogram is a repeating vertical bar: a short broadband burst at a fixed rate.
Rain is a wash that decays with frequency. Those are the structures that a convolutional
classifier learns, and they are invisible in the waveform.

## Measured results

Band energy (mean over clips, dB, relative to the per-clip peak):

| Class | 0-500 Hz | 0.5-2 kHz | 2-4 kHz | 4-8 kHz |
| --- | --- | --- | --- | --- |
| alarm | -21.79 | -16.58 | -17.71 | -20.59 |
| rain | -2.01 | -13.09 | -17.31 | -20.80 |
| footsteps | -35.01 | -37.07 | -36.64 | -36.49 |
| birdsong | -18.69 | -17.12 | -14.93 | -17.28 |

Footsteps are 15-30 dB below everything else across the board: quiet and transient. Rain has
most of its energy below 500 Hz. Birdsong is the only class whose peak is in the 2-4 kHz band.

Nearest-centroid accuracy, held-out sources:

| Representation | Dimensions | Accuracy |
| --- | --- | --- |
| Raw waveform (64 evenly spaced samples) | 64 | 0.472 |
| Mel spectrogram (mean + std over time) | 80 | 0.778 |
| MFCC (mean + std over time) | 26 | 0.778 |

Distances between class centroids in Mel space:

| Pair | Distance |
| --- | --- |
| alarm vs birdsong | 30.9 |
| rain vs birdsong | 55.6 |
| alarm vs rain | 65.0 |
| rain vs footsteps | 152.0 |

The closest pair is where centroid errors come from. The waveform at 0.472 is well above the
0.25 chance level - loudness and periodicity do carry information - but it loses half of what
Mel keeps.

## What to look for

* **Two different words for "similar".** The waveform comparison is done after peak
  normalisation, so amplitude is not the cue; periodicity and envelope are.
* **MFCC matches Mel with 26 numbers instead of 80.** That is the point of the DCT: fewer,
  decorrelated features carrying nearly the same information.
* **A weak classifier isolates the representation.** If you used a CNN here, you would not
  know whether the gains came from features or capacity.

## Checks

```text
PASS  mel beats raw waveform
PASS  chance level is 0.25
PASS  all accuracies in [0, 1]
PASS  MFCC is within 0.15 of Mel
```

## Write-up requirements

1. The two spectrogram images with one sentence each on what distinguishes them.
2. The accuracy table, with an explanation of why 64 waveform samples cannot compete.
3. The closest pair, and a hypothesis for the confusion it causes.
4. One paragraph explaining what a 1 s fixed window would hide.

## Independent extensions

* Change `n_mels` to 80 and re-measure. Does nearest centroid improve, saturate, or degrade?
* Use 256 waveform samples instead of 64. Where does the waveform representation stop
  improving?
* Add a fifth "class" by mixing rain and alarm 50/50 and show which class it is closest to.

Next: [Lab C - Transcribe a short audio clip](lab-c-transcribe-clip.md)
