# Lab C - Transcribe a short audio clip

**Section path:** [Overview](../index.md) · Module [SA07](../sa07-asr-and-stt.md) · **Lab C** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 8% of the section assessment |
| **Time** | 3 hours |
| **Hardware** | CPU-only (12 epochs: about 3 s) |
| **Code** | `projects/speech-audio/lab_c_transcribe_clip.py` |
| **Prerequisite** | SA06, SA07 |

## The task

Take one clip from a speaker the model never heard, transcribe it, and show every step
between frames and text. Then prove the same clip gives the same answer after a round trip
through a WAV file.

You must produce:

1. the model summary (parameters, size, normalisation statistics);
2. the per-frame symbol sequence before collapsing;
3. the final transcript with its confidence;
4. the same clip re-read from disk;
5. the frame-budget calculation for that clip.

## Run it

```bash
cd projects/speech-audio
python lab_c_transcribe_clip.py
python lab_c_transcribe_clip.py --selftest   # same 12 epochs, assertions only
```

```text
=== corpus and vocabulary
origin      : disk
splits      : {'train': 204, 'val': 48, 'test': 36}  (split by speaker)
vocabulary  : 15 symbols ['<blank>', 'a', 'e', 'f', 'g', 'h', 'i', 'l', 'n', 'o', 'p', 'r', 's', 't', 'y']
blank is index 0; CTC needs it to separate repeated letters.

=== training the recogniser (12 epochs)
parameters  : 166,623  (0.65 MB on disk)
features    : 40 log-Mel bands, normalised mean -30.95 / std 22.95
frame stride: 2 (10 ms frames -> 20 ms per output step)
trained on  : 204 clips in 6.46s

=== one clip from a speaker the model never heard (speaker_06)
reference   : 'start'
duration    : 0.42s  (6701 samples at 16000 Hz)
frame labels: ssssttt_aaaa_rrr__tt
             (21 frames; '_' is the CTC blank)
transcript  : 'start'   confidence 0.822

=== the same clip after a round trip through a WAV file
file        : outputs/lab_c_clip.wav  {... 'bit_depth': 16, 'frames': 6701, 'duration_s': 0.4188, ...}
transcript  : 'start'   confidence 0.822

=== why the frame budget matters
clip frames 42 -> 21 output steps after stride 2
transcript 5 characters needs at least 6 steps (one per character plus a blank)
margin      : 15 steps
```

## What the frame labels tell you

`ssssttt_aaaa_rrr__tt` is the model's raw per-frame guess. Three things to notice:

* **Repeats are normal.** "s" spans four frames because the fricative lasts 40 ms, and "t"
  is emitted three times; CTC collapses runs of the same symbol.
* **Blanks separate identical symbols.** Without the two blanks, `aaaaa` and `rrrr` would be
  fine, but a word like "sstop" could not be represented.
* **The alignment is not supervised.** Nobody told the model where the "a" starts; the loss
  summed over all alignments consistent with "start".

## Expected results

| Item | Value |
| --- | --- |
| Parameters | 166,623 |
| Checkpoint size | 0.646 MB |
| Training | 204 clips, 12 epochs, 6.5 s |
| Frame budget | 42 frames -> 21 steps, 6 needed, margin 15 |
| Transcript | `'start'`, confidence 0.822 |
| WAV round trip | same text, confidence 0.823 |

The confidence moves from 0.822 to 0.823 after 16-bit quantisation: the text survives and
the probability shifts in the third decimal. A *character* difference would be a real
finding - the features do change slightly, and a model near a decision boundary can flip.

## Checks

```text
PASS  transcript matches the reference
PASS  WAV round trip gives the same text
PASS  confidence above 0.5
PASS  frame budget has positive margin
```

## Write-up requirements

1. The frame-label sequence, annotated: where each phoneme starts and ends.
2. The frame-budget arithmetic for a longer word you invent (e.g. "restart").
3. The confidence, plus one sentence on why it is not a probability of correctness.
4. What you would change to transcribe two words in one clip.

## Independent extensions

* Set `stride_time=4` and find the shortest word that no longer fits.
* Transcribe the same word from all three test speakers and compare confidences.
* Corrupt the clip with 10 dB noise and re-run: does the frame sequence change before the
  transcript does?

Next: [Lab D - Evaluate speech recognition with word error rate](lab-d-wer-evaluation.md)
