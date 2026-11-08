# Lab F - Build a simple speech-to-text interface

**Section path:** [Overview](../index.md) · Module [SA14](../sa14-optimization-and-deployment.md) · **Lab F** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 8% of the section assessment |
| **Time** | 2 hours |
| **Hardware** | CPU-only; no microphone needed |
| **Code** | `projects/speech-audio/lab_f_stt_interface.py` |
| **Prerequisite** | SA07, SA14 |

## The task

Wrap the recogniser in something a person could use, and handle the three situations every
transcript interface meets: silence, low confidence, and files that are not 16 kHz mono.

You must produce:

1. a CLI that transcribes a WAV file you provide;
2. a demo mode that exercises clean, noisy, and silent input;
3. a stated confidence floor and what happens below it;
4. the conversion log for any file that needed resampling or downmixing.

## Run it

```bash
cd projects/speech-audio
python lab_f_stt_interface.py                     # built-in demo
python lab_f_stt_interface.py --file my_clip.wav  # your own file (repeatable)
python lab_f_stt_interface.py --interactive       # type paths, one per line
python lab_f_stt_interface.py --selftest
```

```text
=== interface
model       : 166,623 parameters, 15 output symbols
vocabulary  : yes, no, stop, start, left, right
confidence floor: 0.70 - below this the interface asks for a repeat
silence threshold: RMS 0.004 - below this it reports no speech instead of guessing

=== demo: synthesised utterances, including the failures
  yes_speaker_00.wav     [#######################.] 0.97  yes (from 'yest')
  start_speaker_03.wav   [########################] 0.98  start
  right_speaker_07.wav   [#####################...] 0.86  right
  left_speaker_02.wav    [#####################...] 0.88  left (from 'let')
  silence.wav            [........................] 0.00  (no speech detected)

=== summary
status   count
--------------
ok       4
silence  1
```

## The three behaviours that matter

| Input | Output | Why |
| --- | --- | --- |
| silent clip | `(no speech detected)` | a model always produces characters; guessing is worse |
| clean `yes` | `yes (from 'yest')` | one extra character, snapped to the six known words (ratio 0.25) |
| clean `left` | `left (from 'let')` | one character short, snapped to `left` (ratio 0.25) |
| 44.1 kHz stereo | converted, then transcribed | `resampled 44100 Hz -> 16000 Hz`, `downmixed to mono` |

Two things to take from those rows. First, correction is visible: the interface prints
`yes (from 'yest')`, so a user can see what was changed. Second, confidence is *not* calibrated
across lengths - `start` at 0.98 and `right` at 0.86 are both five characters, while a short
fragment scores well on mean symbol probability even when it is wrong (Lab D's `n` for `no`
came in at 0.87). Calibrate before showing a percentage to a user (SA14), and keep the raw text
alongside any correction.

## Checks

```text
PASS  clean demo clips are recognised
PASS  silence is reported as silence
PASS  every result has a status
```

## Files that are not 16 kHz mono

`load_audio` does the conversion and reports what it did:

```python
samples, rate, notes = load_audio(path)
# notes: ['downmixed to mono', 'resampled 44100 Hz -> 16000 Hz']
```

Two rules:

* resample with a filter (`audio.resample`), never by slicing, or everything above the new
  Nyquist aliases into the speech band;
* report the conversion, because a silent change to the input is a silent change to the
  output.

## Write-up requirements

1. A transcript of the demo run, with the confidence floor and the silence threshold stated.
2. Output for one file of your own, including the conversion notes (do not commit the audio).
3. What you would show a user instead of a raw confidence number, and why.
4. One failure mode your interface does not handle, and how you would test it.

## Independent extensions

* Lower the confidence floor to 0.5 and re-run: which results change status?
* Add a `--json` flag that prints machine-readable results for scripting.
* Add a batch mode over a folder, with a summary of statuses and the slowest file.

Next: [Lab G - Connect speech input and responses to a chatbot](lab-g-voice-chatbot.md)
