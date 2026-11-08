# SA08 - Word error rate and transcription evaluation {#sa08}

**Section path:** [Overview](index.md) · **Module 8** · [Lab D](labs/lab-d-wer-evaluation.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 2 h reading, 2 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | SA07, F10 (metrics) |
| **You will produce** | A WER report with counts, a per-word table, and a condition table - the three things a reviewer asks for |

## Why this module exists

Accuracy is the wrong metric for transcription, and WER is a metric people misuse in three
specific ways: they average per-sentence WERs instead of pooling counts, they report only
the clean condition, and they quote a number from a corpus whose vocabulary they control
without saying so. This module implements WER correctly, then measures each of those
mistakes.

## The formula

```text
WER = (S + D + I) / N
```

`S` substitutions, `D` deletions, `I` insertions, `N` reference words. WER can exceed 1.0:
insertions are counted in the numerator but not the denominator, so a system that emits
three words for every one is worse than a system that emits nothing.

```python
from speech_core import text

text.word_error_rate("start the engine now", "start engine now")
# {'wer': 0.25, 'deletions': 1, 'substitutions': 0, 'insertions': 0, 'matches': 3, ...}
```

The counts come from a Levenshtein alignment over words, with a backtrace that reports
which operation happened. Reporting only the rate hides whether the system is dropping words
or inventing them - and those need different fixes.

## Corpus WER versus mean per-clip WER

```python
pairs = [("a b c d", "a b c d"), ("yes", "no")]
text.corpus_error_rates(pairs)["wer"]        # 0.2  = 1 error / 5 reference words
```

```python
import numpy as np
np.mean([text.word_error_rate(r, h)["wer"] for r, h in pairs])   # 0.5
```

Same two utterances, two different numbers: 0.2 pooled, 0.5 averaged per clip. Pooling
weights by length, so one long correct sentence dilutes one short wrong one. Averaging
treats every utterance equally.

Neither is "correct" in the abstract; the pooled number is what the literature reports and
what is comparable across systems on the same corpus. The problem is a report that switches
between them, or quotes the lower one. Print both.

On the six-word corpus here they coincide (every clip is one word), which is itself a
reminder that a one-word corpus cannot exercise the distinction. Lab D prints both anyway so
the habit is in place before you meet a real corpus.

## Character error rate

CER applies the same edit distance to characters:

```python
text.character_error_rate("start", "stat")
# {'cer': 0.2, 'deletions': 1, 'reference_chars': 5, ...}
```

CER is useful when the errors are sub-word (a missing "r" in "start"), and misleading when
compared across languages or scripts of different length. Report it alongside WER, not
instead of it.

## Measured report

Verified run of [Lab D](labs/lab-d-wer-evaluation.md), 36 test clips from 3 unseen speakers:

| Corpus | WER | CER | Sentence accuracy | Errors |
| --- | --- | --- | --- | --- |
| clean | 0.000 | 0.000 | 1.000 | 0 sub / 0 ins / 0 del |
| 10 dB SNR | 0.028 | 0.007 | 0.972 | 1 sub / 0 ins / 0 del |
| 5 dB SNR | 0.722 | 0.355 | 0.278 | 26 sub / 0 ins / 0 del |

The clean number is saturation, not capability: six isolated words from the same
synthesiser. 10 dB barely dents it - one clip, one missing character. 5 dB is where the
model fails, and a report that quoted only 10 dB would be describing a model that does not
exist under realistic noise. Quote the whole curve, and say which condition your users are
actually in.

Per-word accuracy at 5 dB:

| Word | Accuracy |
| --- | --- |
| left | 0.667 |
| yes | 0.667 |
| no | 0.167 |
| stop | 0.167 |
| right | 0.000 |
| start | 0.000 |

A single WER of 0.722 would hide that `left` and `yes` mostly survive while `right` and
`start` never do. Per-word analysis is where the debugging starts.

Confusions at 5 dB:

| Reference | Recognised | Count |
| --- | --- | --- |
| no | n | 5 |
| start | sar | 3 |
| yes | ys | 2 |
| start | star | 2 |
| right | rl | 2 |
| stop | s | 2 |

Every one of those is a single-character deletion or substitution, not a whole-word
confusion - the model hears the word and fumbles one phoneme, mostly the vowel or the
trailing consonant. That distinction decides the fix: a lexicon or a language model recovers
the near misses; more acoustic training data would help the words that vanish.

## Conditions

| Condition | WER | CER | Sentence accuracy | WER after lexicon |
| --- | --- | --- | --- | --- |
| clean | 0.000 | 0.000 | 1.000 | 0.000 |
| 20 dB SNR | 0.000 | 0.000 | 1.000 | 0.000 |
| 10 dB SNR | 0.028 | 0.007 | 0.972 | 0.000 |
| 5 dB SNR | 0.722 | 0.355 | 0.278 | 0.222 |
| -12 dB gain | 0.556 | 0.246 | 0.444 | 0.167 |
| slower 1.15x | 0.167 | 0.043 | 0.833 | 0.000 |
| narrowband 4 kHz | 0.833 | 0.435 | 0.167 | 0.333 |

`WER after lexicon` is the number you get if you are allowed to snap hypotheses to the six
known words. It is legitimate for a closed command vocabulary and dishonest for open
speech. Report which one you are doing.

## The lexicon ablation

```python
from speech_core import evaluate

result = evaluate.lexicon_ablation(pairs, ["yes", "no", "stop", "start", "left", "right"])
# {'wer_before': 0.722, 'wer_after': 0.222, 'absolute_gain': 0.5,
#  'utterances_changed': 19, 'max_ratio': 0.5, ...}
```

Snapping fixes 19 of 36 hypotheses at 5 dB. It does not fix the remaining 0.222, and it
cannot fix a case where the wrong word is acoustically plausible - "left" and "right" are
both two syllables, and no edit distance will save you.

## What a WER number must state

* the corpus and its size, and whether speakers are disjoint from training;
* the condition (clean, noisy, far-field, telephone);
* whether a lexicon or language model was used in decoding;
* the normalisation (lowercase, punctuation, filler words);
* the pooled WER, and ideally the per-word table.

A WER without those five is not comparable to anything.

## Debugging advice

| Symptom | Cause | Fix |
| --- | --- | --- |
| WER > 1.5 | decoder inserting blanks as letters | check vocabulary indices; blank must be 0 |
| WER differs from your hand count | normalisation differs (case, punctuation) | use one `normalize_text` everywhere |
| Clean WER 0, noisy WER 1.0 | no robustness training | augmentation, or accept the limit and say so |
| Sentence accuracy 0 but WER low | one character off in every clip | look at CER and the confusion list |
| Per-word accuracy 0 for one word | that word is systematically deleted | check the frame budget for its length |

## Exercises

1. Hand-compute WER for reference "the left engine stopped" and hypothesis "the left engine
   stop". How many operations, and which?
2. Construct a case where insertions push WER above 1.0. What would you report instead?
3. Take the Lab D JSON, recompute per-word accuracy from the raw utterances, and confirm it
   matches the printed table.
4. Set `max_ratio` in the lexicon ablation to 0.25 and 0.75 and plot WER against the
   threshold. What does the shape of that curve tell you about the error distribution?

Next: [SA09 - Fine-tuning or adapting a compatible pretrained model](sa09-adapting-pretrained-asr.md)
