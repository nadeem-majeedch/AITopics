# Model card: the systems in this section

**Section path:** [Overview](index.md) · [Assessment](assessment.md) · [Ethics](ethics-and-consent.md)

A model card is the one page that lets somebody else decide whether to trust your system. For
audio it must state what the model was trained on, how it was evaluated, what it cannot do,
and what the consent position is for the data. The helper that builds these in code is
`projects/speech-audio/speech_core/cards.py`.

```python
from speech_core import cards

card = cards.asr_model_card({"wer_clean": 0.0, "wer_5db_snr": 0.722})
cards.save_card(card, "outputs/model_card.md")     # Markdown, or .json
```

`build_model_card` reports any missing required section in `incomplete_fields` rather than
inventing content, and `render_markdown` produces the page below.

## Card 1: environmental sound classifier

| Field | Value |
| --- | --- |
| Task | 4-class clip classification: alarm, rain, footsteps, birdsong |
| Intended use | coursework; comparing representations and robustness |
| Out of scope | any safety, security, or medical alerting; field recordings; speaker identification |
| Training data | 240 synthetic clips, 80 sources x 3 variants, CC0-1.0, grouped by source |
| Evaluation | accuracy 1.000 on 36 held-out clips; robustness table in [Lab A](labs/lab-a-environmental-sound-classifier.md) |
| Model | `TinyAudioCNN`, 72,276 parameters, 0.29 MB |
| Limitations | synthetic classes are far cleaner than field recordings; one event per clip; no demographic dimension exists |

Why the out-of-scope line matters: a classifier that reports 1.000 on four synthetic classes
would be picked up by an enthusiastic reader as "an alarm detector". It is not one. It has
never seen a real alarm, a siren, a smoke detector, or a crowded room.

## Card 2: isolated-word recogniser

The generated card, with the numbers measured in [Lab D](labs/lab-d-wer-evaluation.md):

```markdown
# Model card: AITopics TinyCRNN isolated-word recogniser

Version `0.1.0` - task: **Character-level CTC speech recognition over a six-word vocabulary**

## Intended use
- Coursework: how CTC alignment, decoding, and WER evaluation work
- A baseline for the adaptation and latency labs

## Out of scope - do not use for
- Transcribing real conversations, meetings, or calls
- Any language other than the six synthetic command words
- Speaker identification or verification
- Accessibility, medical, legal, or safety transcription

## Training data
- **corpus**: synthetic formant speech, 24 voices x 6 words x 2 utterances
- **vocabulary**: yes, no, start, stop, left, right
- **split**: speaker-disjoint (17 train / 4 val / 3 test voices)
- **licence**: CC0-1.0
- **not_used**: Whisper, wav2vec2, or any pretrained checkpoint - trained from scratch

## Evaluation
- **wer_clean**: 0.000
- **wer_10db_snr**: 0.028
- **wer_5db_snr**: 0.722
- **wer_5db_snr_after_lexicon**: 0.222
- **test_utterances**: 36 from 3 unseen speakers
- **speed**: RTF 0.0042 (baseline, CPU, batched, one thread)

## Limitations
- Closed vocabulary: an out-of-vocabulary word can only be spelled or dropped
- No accent, dialect, child-speech, or disordered-speech evaluation exists
- Single-channel, 16 kHz, one speaker at a time
- Synthetic voices are easier than human voices; real WER would be higher
- Character error rate can look better than word error rate on short words

## Consent, rights, and provenance
All training audio is synthesised from code; no speaker donated a recording. Adapting this
recipe to real speech requires documented consent for every speaker, a licence review of the
corpus, and a plan to delete the data on request.
```

## What every card in this section must contain

| Section | Failure if missing |
| --- | --- |
| Intended use | the model is used for something adjacent and wrong |
| Out of scope | nobody is told what it must not do |
| Training data + licence | provenance cannot be audited |
| Evaluation with conditions | a single clean number is mistaken for capability |
| Limitations | "unmeasured" is read as "fine" |
| Consent and rights | a deletion request has no answer |

Two things that are not optional for a voice system, and are easy to forget:

* **the vocabulary**, spelled out - "six words" is not enough if the reader cannot tell
  whether their word is one of them;
* **the condition** every number was measured in - clean, 10 dB, narrowband.

## Template for your own project

```text
Name / version:
Task (one sentence):
Intended use (bullets):
Out of scope (bullets, specific):
Data: source, licence, consent basis, retention, deletion path
Split: how speakers/sources were separated
Evaluation: metric, corpus size, condition, per-group breakdown
Speed: RTF and hardware, measured
Limitations: specific, including the unmeasured dimensions
Failure behaviour: what the user sees on low confidence or silence
Monitoring: three signals, with thresholds
Owner: a person, not a team name
```

A card with every field filled but generic ("may not work on all accents") is weaker than one
that says what was measured: "no accented speech was in the training data; WER on the
corpus's 24 synthetic voices is 0.000, and no real speaker has been evaluated."

## Related

* [Ethics, consent, and rights](ethics-and-consent.md) - the checklist behind the consent
  section.
* [SA14](sa14-optimization-and-deployment.md) - the deployment checklist that pairs with this
  card.
* [Assessment](assessment.md) - the capstone requires a card in this format.
