# Lab E - Adapt a pretrained model to a small permitted speech dataset

**Section path:** [Overview](../index.md) · Module [SA09](../sa09-adapting-pretrained-asr.md) · **Lab E** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 10% of the section assessment |
| **Time** | 3 hours |
| **Hardware** | CPU-only (under 10 s per run) |
| **Code** | `projects/speech-audio/lab_e_adaptation.py` |
| **Prerequisite** | SA07, SA08, SA09 |

## The task

Take the recogniser trained on clean synthetic voices, show it degrade on noisy audio from
speakers it has never heard, then adapt it with eighteen noisy clips and measure what
changed - including what got worse.

You must produce:

1. the before number on the held-out noisy clips;
2. the after number for a frozen front end and for full fine-tuning;
3. a clean-audio check to catch forgetting;
4. a statement of the consent and rights position for the adaptation data.

## The protocol, which is the point

| Item | Value |
| --- | --- |
| Base model | trained on 17 speakers, clean audio |
| New speakers | 3, never seen in training |
| Domain shift | white noise at 5 dB SNR |
| Adaptation set | utterance 0 of each word, 18 clips |
| Evaluation set | utterance 1 of each word, 18 clips |
| Clean check | the same 18 words without noise |

Adapting on one utterance and evaluating on another is not a technicality. Adapt on the clips
you evaluate on and you measure memorisation, which is the single most common way adaptation
results are overstated.

## Run it

```bash
cd projects/speech-audio
python lab_e_adaptation.py
python lab_e_adaptation.py --selftest   # 4 base epochs, 3 adaptation epochs
python lab_e_adaptation.py --snr 10     # easier domain: base WER is already 0.028
```

```text
=== before adaptation
WER on noisy new speakers : 0.722
WER on clean new speakers : 0.000
  ref yes    hyp 'yes'      conf 0.93
  ref no     hyp 'n'        conf 0.88
  ref stop   hyp 's'        conf 0.81
  ref start  hyp 'sar'      conf 0.90
  ref left   hyp 'left'     conf 0.92
  ref right  hyp 'rl'       conf 0.86

=== frozen-front-end adaptation
frozen      : 16,464 of 166,623 parameters (10%)
The convolution stack keeps the spectral patterns it learned; the GRU and output
head absorb the new acoustic conditions.
```

## Measured result

| Variant | Trainable parameters | Noisy WER | Clean WER | Time |
| --- | --- | --- | --- | --- |
| no adaptation | 0 | 0.722 | 0.000 | - |
| frozen front end | 150,159 | 0.000 | 0.000 | ~0.5 s |
| full fine-tune | 166,623 | 0.000 | 0.000 | ~0.6 s |

The WER columns reproduce exactly; the second column jitters between about 0.5 s and 1.5 s on
the same machine depending on warm-up, so quote it as an order of magnitude, not a benchmark.

Read the table in three directions:

* **Adaptation worked**: 0.722 -> 0.000 on the held-out noisy clips, with 18 clips of
  adaptation data (three words per speaker, one utterance each) from speakers the model had
  never heard.
* **The forgetting check is uninformative here**, and that is the honest finding: clean WER was
  already 0.000 and cannot go lower, so "no clean regression" only tells you the test set is
  saturated. Runs of this lab before the seeding bug was fixed produced clean WER 0.167 for the
  frozen variant - real forgetting that this clean set was too easy to expose. Widen the clean
  test before you claim adaptation is free.
* **Full fine-tuning was not worse** here, because the model is 167k parameters and the
  adaptation set is 18 clips. With a 300M-parameter checkpoint the ordering usually reverses.

## Checks

```text
PASS  adaptation and evaluation clips are disjoint
PASS  adaptation used unseen speakers
PASS  frozen parameters are a strict subset
PASS  WER in [0, 2] everywhere
PASS  adaptation improves the noisy WER
PASS  clean accuracy is not destroyed
```

The last check allows a regression up to 0.2 WER: adaptation is a trade, not a free win, and
a lab that demands monotone improvement would be teaching the wrong thing.

## Consent and rights

The "new speakers" are synthetic voice profiles, so this lab has no consent question. With
real speakers you would need, before the first training run:

1. written permission that names model training, not just recording;
2. the purpose and the prohibited uses;
3. a retention period and a tested deletion path, including model rollback;
4. an owner accountable for the derived checkpoint.

Write those four for a corpus of 50 customer calls, and identify which one a deletion request
would break first.

## Write-up requirements

1. The before/after table with all three variants and the clean column.
2. One paragraph on why adaptation and evaluation sets must be disjoint, with the number you
   would have reported if they were not.
3. The forgetting check, and whether you would ship the adapted model.
4. The four consent fields above, filled in for a scenario of your choice.

## Independent extensions

* Adapt with 6 clips instead of 18 and find where the gain disappears.
* Adapt at 10 dB instead of 5 dB: does the model still handle 5 dB afterwards?
* Compare adaptation with lexicon decoding alone (WER 0.722 -> 0.222 at 5 dB in Lab D).
  Which is cheaper, and when would you still adapt?

Next: [Lab F - Build a simple speech-to-text interface](lab-f-stt-interface.md)
