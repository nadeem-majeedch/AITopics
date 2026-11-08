# SA07 - Speech to text and automatic speech recognition {#sa07}

**Section path:** [Overview](index.md) · **Module 7** · [Lab C](labs/lab-c-transcribe-clip.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 5 hours: 2.5 h reading, 2.5 h practice |
| **Hardware** | CPU-only (12 epochs take about 3 seconds) |
| **Prerequisites** | SA03, SA06, F11-F13 |
| **You will produce** | A character-level CTC recogniser, decoded transcripts, and an explanation of the alignment it learned |

## Why this module exists

Speech recognition is the audio task with the largest gap between "a tutorial" and "a
system". A tutorial trains a model to map a clip to a label. A recogniser must map a
variable-length signal to a variable-length string, and nobody has marked where each
character starts.

CTC (connectionist temporal classification) solves the alignment problem by refusing to
solve it: the network emits one distribution per frame, and the loss sums over every
alignment consistent with the transcript. This module implements the smallest complete
version - a convolutional front end, a bidirectional GRU, a character vocabulary, and a
greedy decoder - in about 170k parameters.

## What a real system adds

| Component | This section | Production |
| --- | --- | --- |
| Acoustic model | TinyCRNN, from scratch | Whisper, wav2vec2, Conformer (millions of parameters) |
| Vocabulary | 14 characters + blank | 30k-100k subword units |
| Language model | none (or a 6-word lexicon) | n-gram or neural LM, heavily weighted |
| Training data | 204 synthetic clips | 10k-5M hours |
| Alignment | CTC | CTC, RNN-T, or attention |
| Decoding | greedy | beam search with LM fusion |

The architecture is a miniature of the real thing; the discipline - grouping splits by
speaker, reporting WER, checking the frame budget - transfers unchanged.

## The vocabulary and the blank

```python
from speech_core import text

vocab = text.build_char_vocab(["yes", "no", "stop", "start", "left", "right"])
# ['<blank>', 'a', 'e', 'f', 'g', 'h', 'i', 'l', 'n', 'o', 'p', 'r', 's', 't', 'y']
```

Index 0 is the blank. It is not a space: it is the symbol that means "no output here". It
exists because CTC collapses repeats. Without a blank between them, the frames for "s s"
in "stop" and the frames for one long "s" are indistinguishable.

## The model

```python
from speech_core import models

model = models.TinyCRNN(vocab_size=15, n_mels=40, width=16, hidden=64, stride_time=2)
print(models.count_parameters(model))         # 166,623
print(round(models.model_size_mb(model), 3))  # 0.646
```

Input `(B, 1, 40, T)` -> two conv blocks that pool **frequency only** (2x1 max pools) ->
time-major reshape -> BiGRU(64) -> linear to 15 logits per frame.

Pooling frequency only is the important design choice. If you pool time as well, the output
becomes shorter than the transcript and CTC cannot represent it. `stride_time=2` is the
controlled way to shorten the time axis: it halves compute and doubles the minimum duration
each output step can represent (20 ms).

The frame budget is a hard constraint:

```text
a 0.42 s clip -> 42 Mel frames -> 21 output steps at stride 2
"start" is 5 characters, needing at least 6 steps (one per character plus a blank)
margin = 15 steps
```

`training.train_ctc` checks this before training and raises with a message that names the
clip, the transcript length, and the frame count:

```text
ValueError: clip 0: 12 characters need at least 13 frames, model gives 8.
Lower stride_time or raise max_frames.
```

If you see `RuntimeError: CTC loss is not finite`, the usual causes are a transcript longer
than the frame budget (silently `inf`), a blank index that is not 0, or an unnormalised
input producing NaN.

## Training

```python
from speech_core import asr, datasets, text

splits = datasets.group_split(records, seed=1)          # by speaker
vocab = text.build_char_vocab([r.transcript for r in splits["train"]])
rec, history = asr.Recognizer.train(
    splits["train"], splits["val"], vocab,
    epochs=12, lr=3e-3, batch_size=16, seed=0, log=True,
)
print(rec.mean, rec.std)        # -30.9468 22.9468 - carry these with the weights
```

Twelve epochs on 204 clips take about 3 seconds and drive the CTC loss from 3.05 to 0.012.
`asr.Recognizer` exists so that the weights, vocabulary, and normalisation statistics travel
together. It is not a convenience: it is the fix for the most common silent bug in audio
inference.

## Decoding

Three steps, in this order:

1. **argmax per frame**: `ssssttt_aaaa_rrr__tt`
2. **collapse repeats**: `st_ar t`
3. **drop blanks**: `start`

```python
from speech_core import asr

decoded, confidence = asr.ctc_greedy_decode(log_probs, rec.vocab)
# 'start', 0.822
```

Confidence is the mean probability of the emitted symbols. It is not a calibrated
probability of correctness; it ranks clips usefully and should not be printed to users as a
percentage without calibration (SA14).

**Lexicon-constrained decoding** is legitimate when the vocabulary is closed:

```python
decision = asr.lexicon_decode("stp", ["yes", "no", "stop", "start", "left", "right"], max_ratio=0.5)
# {'text': 'stop', 'raw': 'stp', 'distance': 1, 'ratio': 0.25, 'applied': True}
```

It recovers a one-character slip and cannot recover a mis-heard word: at 5 dB SNR the
hypotheses `sto` and `n` snap to `stop` and `no` (ratios 0.25 and 0.50), because the lexicon
is six words long. It cannot rescue `sar` (for "start"), which is two edits away from the
nearest word. [Lab D](labs/lab-d-wer-evaluation.md) measures the gain (WER 0.722 -> 0.222 at
5 dB) and states the caveat: it is only honest on a closed vocabulary.

## What this recogniser cannot do, precisely

* **Out of vocabulary.** Six words, 14 characters. "banana" becomes something else; the
  decoder has no symbol for `b`.
* **Continuous speech.** The corpus is isolated words. Nothing in training taught the model
  word boundaries.
* **New voices.** Speaker-disjoint splits mean WER 0.000 on three unseen voices, but those
  voices come from the same synthesiser. Human voices would be much harder.
* **Accents, children, disordered speech, other languages.** Not represented at all.
* **Background noise.** 10 dB SNR raises WER to 0.028, and 5 dB to 0.722 before lexicon
  decoding. Noise is the dominant failure mode in every lab here.

Every one of those gaps is a line in the model card, not a footnote.

## Expected results

```text
clip          : speaker_06, "start", 0.4188 s, 6701 samples
frames        : 42 Mel frames -> 21 output steps
frame labels  : ssssttt_aaaa_rrr__tt
transcript    : 'start'  confidence 0.822
WAV round trip: 'start'  confidence 0.823 (same text)
test WER      : 0.000 with 12 epochs, 204 training clips, 3 unseen speakers
```

## Debugging advice

| Symptom | Cause | Fix |
| --- | --- | --- |
| Empty transcript with high loss | blank dominates: too few epochs or lr too low | train longer, raise lr |
| Repeated characters (`stooop`) | blank collapsed: `log_softmax` applied twice or stride too small | check the decode path |
| Text is nonsense but loss is low | normalisation mismatch at inference | use `Recognizer`, or pass the training mean/std |
| `ValueError` about frame budget | transcript longer than output steps | lower `stride_time`, raise `max_frames` |
| `RuntimeError: CTC loss is not finite` | `inf` from an impossible alignment | check the budget and blank index |
| Train WER 0, test WER 0.6 | clip-level split | regroup by speaker |

## Exercises

1. Train with `stride_time=4` and compute the shortest word that can no longer be
   represented. Confirm the error message.
2. Remove the blank from the vocabulary and decode "sstop". What happens, and why?
3. Compute the greedy decode by hand for a 6-frame, 3-symbol example where two identical
   letters are separated by a blank and where they are not.
4. Raise `max_ratio` in `lexicon_decode` from 0.5 to 0.9 and show a case where it turns a
   correct rejection into a wrong action.

Next: [SA08 - Word error rate and transcription evaluation](sa08-wer-and-transcription-evaluation.md)
