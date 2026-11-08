# Lab D - Evaluate speech recognition with word error rate

**Section path:** [Overview](../index.md) · Module [SA08](../sa08-wer-and-transcription-evaluation.md) · **Lab D** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 10% of the section assessment |
| **Time** | 3 hours |
| **Hardware** | CPU-only |
| **Code** | `projects/speech-audio/lab_d_wer_evaluation.py` |
| **Prerequisite** | SA07, SA08 |

## The task

Produce the report a reviewer would ask for: WER with counts, the pooled-versus-averaged
comparison, per-word accuracy, confusions, a lexicon ablation, and a condition table.

You must produce:

1. clean and 5 dB SNR WER, CER, and sentence accuracy;
2. the error counts (substitutions, insertions, deletions);
3. per-word accuracy on the degraded corpus;
4. the lexicon ablation with its caveat;
5. a seven-condition table.

## Run it

```bash
cd projects/speech-audio
python lab_d_wer_evaluation.py
python lab_d_wer_evaluation.py --selftest   # 4 epochs
```

```text
=== corpus
origin      : disk
train       : 204 clips, 17 speakers
test        : 36 clips, 3 unseen speakers

=== clean test set (saturated - do not quote this as a capability)
corpus WER        : 0.000
mean of per-clip  : 0.000
character error   : 0.000
sentence accuracy : 1.000
errors            : 0 substitutions, 0 insertions, 0 deletions over 36 reference words

=== 5 dB SNR (the same clips, heavily noisier)
  ok  ref yes    hyp 'yes'      conf 0.79
  err ref yes    hyp 'ys'       conf 0.88
  err ref no     hyp 'n'        conf 0.87
  err ref no     hyp 'n'        conf 0.88
  err ref stop   hyp 'sto'      conf 0.89
  err ref stop   hyp 'so'       conf 0.85
...
corpus WER        : 0.722
mean of per-clip  : 0.722
character error   : 0.355
sentence accuracy : 0.278
errors            : 26 substitutions, 0 insertions, 0 deletions over 36 reference words
```

## Per-word and confusions at 5 dB

| Word | Accuracy |
| --- | --- |
| left | 0.667 |
| no | 0.167 |
| right | 0.000 |
| start | 0.000 |
| stop | 0.167 |
| yes | 0.667 |

| Reference | Recognised | Count |
| --- | --- | --- |
| no | n | 5 |
| start | sar | 3 |
| yes | ys | 2 |
| start | star | 2 |
| right | rl | 2 |
| stop | s | 2 |

Only `left` and `yes` survive most of the time, and the two words that fail completely -
`start` and `right` - are the two with the loudest initial fricative, which white noise at
5 dB buries. The `no` row is the sharpest: five of six clips lose the vowel entirely, because
it is the shortest word in the set (about 0.2 s) and the noise occupies most of its frames.

## Lexicon ablation

```text
threshold          : normalised edit distance <= 0.5
WER before         : 0.722
WER after          : 0.222  (+0.500)
utterances changed : 19 of 36
```

Legitimate for a six-word closed vocabulary. It recovers `n` -> `no` and `s` -> `no`-like
fragments it can reach in one edit, and cannot reach `sar`, which needs two. On open speech
snapping would be cheating, and the script prints that caveat with the number.

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

The worst condition is narrowband (telephone) at 0.833, marginally worse than 5 dB of white
noise, and the -12 dB row is a level bug rather than a robustness result: no spectral shape
changed, only the normalisation statistics the recogniser was trained with. Note how flat
the top of the table is - 20 dB and clean are identical, so a report that only quotes "10 dB"
would describe a model that is almost perfect while the same model fails 72% of words at
5 dB.

## Checks

```text
PASS  corpus WER in [0, 2]
PASS  counts add up to the reported errors
PASS  noise does not improve WER
PASS  lexicon does not make WER worse
PASS  per-word accuracy covers every word
PASS  every condition was measured
```

## Write-up requirements

1. The clean and 5 dB tables with counts, not just rates.
2. One paragraph on corpus versus mean-per-clip WER, and why every clip here is one word.
3. The per-word table and the fix you would try for the worst word.
4. The condition table with a recommendation for the deployment you care about.

## Independent extensions

* Lower `max_ratio` to 0.25 and re-run the ablation. Which words stop being corrected?
* Train on clean plus 10 dB and 5 dB noisy clips (mixing them into the training set) and
  re-measure both conditions.
* Compute a 95% confidence interval for WER on 36 utterances. How precise is 0.722 really?

Next: [Lab E - Adapt a pretrained model](lab-e-adaptation.md)
