# SA09 - Fine-tuning or adapting a compatible pretrained model {#sa09}

**Section path:** [Overview](index.md) · **Module 9** · [Lab E](labs/lab-e-adaptation.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 5 hours: 2.5 h reading, 2.5 h practice |
| **Hardware** | CPU-only for this lab; a real pretrained model needs a GPU for comfort |
| **Prerequisites** | SA07, SA08 |
| **You will produce** | A before/after WER table, a forgetting check, and an adaptation protocol you can apply to a real checkpoint |

## Why this module exists

Almost nobody trains a recogniser from scratch. You take a model that already knows a
language, adapt it to your domain - an accent, a microphone, a vocabulary, a noise
condition - and you measure whether the adaptation helped.

The measurement is where projects go wrong. Adapt on the same clips you evaluate on and you
measure memorisation. Fine-tune every parameter on 18 clips and you destroy what the model
knew. Report the "after" number without the "before" number and nobody can tell whether the
training did anything.

## When adaptation is the right move

| Situation | Adaptation helps? | Why |
| --- | --- | --- |
| New accent, 1-50 hours | yes, with a frozen front end | acoustics differ, language is the same |
| New vocabulary (product names) | yes, but fix the lexicon/LM first | the acoustic model already hears the sounds |
| New microphone or codec | yes, mild | channel mismatch is a nuisance variable |
| Different language | yes, with much more data | the phoneme inventory changes |
| 10 clean clips | no | not enough signal; use a lexicon instead |
| Domain shift you cannot characterise | measure first | adaptation can make it worse |

The rule: adaptation is a data problem before it is a modelling problem. Eighteen clips can
fix a channel; they cannot teach a vocabulary.

## What "pretrained" means in this course

This section's base recogniser was trained in [Lab C](labs/lab-c-transcribe-clip.md) on
synthetic voices. It is not Whisper or wav2vec2. The mechanics are identical - freeze a
feature front end, train a small head, keep an untouched evaluation set - and the numbers
belong to this corpus. When you apply the same recipe to a downloaded checkpoint, three
practical differences appear:

* the checkpoint expects a specific feature pipeline (80 Mel bins, 30 s chunks, its own
  normalisation) - use its `processor`, not your own;
* it has millions of parameters, so freeze aggressively and use a small learning rate
  (1e-5 to 1e-4, not 1e-3);
* it ships a tokenizer, and your new vocabulary must be expressible in it.

Alternatives when a pretrained model is too large for the machine:

| Option | Download | Hardware | Where it fits |
| --- | --- | --- | --- |
| Small CTC model trained here | 0.65 MB | CPU | learning the mechanics |
| Whisper `tiny` | ~75 MB | CPU, slow | real English, offline |
| `wav2vec2-base` + CTC head | ~360 MB | GPU preferred | research and fine-tuning |
| Hosted speech API | none | network | production, costs money and sends audio off-device |

None of the core exercises needs a paid API or a download. If you do use a hosted API, the
audio leaves your machine - which is a consent question, not just an engineering one.

## The protocol

```python
from speech_core import asr, training

base = asr.Recognizer.load("outputs/cache/base_....pt")

# 1. Measure before, on the exact clips you will evaluate on later.
before = wer(base, eval_set)

# 2. Freeze the feature extractor.
frozen = asr.freeze_feature_extractor(base.model)   # returns parameters frozen

# 3. Fine-tune the rest, at a low learning rate, with early stopping by hand.
history, base.model = training.train_ctc(
    base.model, adapt_set, base.vocab, eval_set,
    epochs=8, lr=1e-3, batch_size=8, seed=1, log=False,
)
base.mean, base.std = history["mean"], history["std"]   # new feature statistics!

# 4. Measure after, on the same clips, plus the clean set for forgetting.
after = wer(base, eval_set)
clean_after = wer(base, clean_eval)
```

Four details in that snippet are the difference between a result and a story:

* **Disjoint sets.** Adapt on utterance 0 of each word, evaluate on utterance 1, same
  speakers. Otherwise you are scoring the training data.
* **Frozen front end.** In this model the conv stack is 16,464 of 166,623 parameters (10%).
  Freezing it keeps the spectral patterns and lets the GRU adapt to the new acoustics.
* **New normalisation.** `train_ctc` recomputes the feature mean and standard deviation on
  the adaptation set and returns them. Store them in the `Recognizer` or inference breaks.
* **Forgetting check.** A model that improves on noise and loses clean accuracy has traded
  one failure for another. Report both.

## Measured result

[Lab E](labs/lab-e-adaptation.md), noise adaptation at 5 dB SNR, 18 adaptation clips:

| Variant | Trainable params | Noisy WER | Clean WER | Time |
| --- | --- | --- | --- | --- |
| no adaptation | 0 | 0.722 | 0.000 | - |
| frozen front end | 150,159 | 0.000 | 0.000 | ~0.5 s |
| full fine-tune | 166,623 | 0.000 | 0.000 | ~0.6 s |

Three things to read from that table:

1. Adaptation works: WER 0.722 -> 0.000 on the held-out noisy clips, from 18 clips of audio
   from speakers the model had never heard.
2. The forgetting column is flat, and that is a limitation of the test, not evidence that
   nothing was forgotten. Clean WER started at 0.000 and cannot improve. Runs of this lab before
   its seeding was fixed produced clean WER 0.167 for the frozen variant: real catastrophic
   forgetting that this clean set was too easy to show. A saturated test cannot detect a
   regression, so quote the forgetting check only when the before-number has room to fall.
3. Full fine-tuning was not worse here, and was faster, because the corpus is tiny and the
   model is small. On a 300M-parameter checkpoint the ordering usually reverses: full
   fine-tuning on 18 clips forgets catastrophically.

## Evaluating adaptation honestly

| Question | Measurement |
| --- | --- |
| Did it improve the target domain? | WER on held-out target clips, before vs after |
| Did it damage the original domain? | WER on the original clean test set |
| Was it the data or the recipe? | same clips, frozen vs full, one variable at a time |
| Would a lexicon have done it cheaper? | WER after lexicon snapping, no training at all |

That last row matters more than students expect. At 5 dB SNR, lexicon decoding alone takes
WER from 0.722 to 0.222 without touching a weight. If your vocabulary is closed, try the free
option first.

## Consent and rights for adaptation data

Adapting to a person's voice means training on that person's voice. Before you do:

* **permission**: written, specific to training a model, not a generic recording release;
* **purpose**: what the adapted model will be used for, and what it will not;
* **retention**: how long the clips are kept, and how a deletion request is honoured -
  including retraining or rollback;
* **scope**: an adapted model can memorise speaker characteristics, so treat the checkpoint
  as derived personal data.

Synthetic speakers avoid all four questions, which is why this lab uses them. A real
deployment does not get that option. See [Ethics, consent, and rights](ethics-and-consent.md).

## Debugging advice

| Symptom | Cause | Fix |
| --- | --- | --- |
| Loss explodes in the first epoch | learning rate too high for fine-tuning | 1e-4 or lower, gradient clipping |
| WER gets worse after adaptation | adapted on evaluation clips, or too many epochs | check disjointness, fewer epochs |
| Clean WER collapses | full fine-tuning on very little data | freeze the front end |
| Transcripts become empty | new normalisation statistics not stored | rebuild the `Recognizer` with `history["mean"]`, `history["std"]` |
| Nothing changes at all | parameters frozen by mistake | `asr.adapter_parameters(model)` should be non-empty |

## Exercises

1. Repeat Lab E with 6 adaptation clips instead of 18. Where does the gain disappear?
2. Freeze the GRU as well as the convolutions and train only the output layer. Is 15-way
   linear enough to adapt to noise?
3. Evaluate the adapted model on the original clean **training** speakers. Does it still
   recognise them?
4. Write the four consent fields from this module for a hypothetical corpus of customer
   service calls, and identify which one a deletion request would break.

Next: [SA10 - Text to speech and pretrained speech generation](sa10-tts-and-speech-generation.md)
