# SA04 - Segmentation, labelling, and dataset preparation {#sa04}

**Section path:** [Overview](index.md) · **Module 4** · [Lab A](labs/lab-a-environmental-sound-classifier.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 2 h reading, 2 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | SA01-SA03 |
| **You will produce** | A manifest with provenance, a split that cannot leak, and a leakage audit you can explain |

## Why this module exists

An audio dataset is not a folder of WAVs. It is a table of clips with, for every row: who
or what produced it, what is in it, how it was recorded, and which split it belongs to.
Without that table you cannot split correctly, cannot audit leakage, and cannot tell a
reviewer what your model was trained on.

The specific failure this module prevents is the **clip-level split of speaker data**. Two
recordings of the same person are near-duplicates: same vocal tract, same microphone, often
the same sentence. Split by clip and the test set contains the training set's speakers,
which inflates accuracy and hides the fact that the model does not generalise to new
voices.

## What a clip needs

| Field | Why it is needed | Example |
| --- | --- | --- |
| `file` | locate the audio | `speech_0042.wav` |
| `label` | the target | `3` (`stop`) |
| `source_id` | grouping key for splits and leakage | `speaker_07` |
| `sample_rate` | detect mismatches before training | `16000` |
| `duration` | catch truncated or concatenated clips | `0.312` |
| `rms` | catch level outliers | `0.0412` |
| provenance | licence, consent, collection method | synthetic, CC0-1.0 |

The generator writes exactly this. `datasets.save_corpus` writes the WAVs and
`manifest.json`; `scripts/make_audio_data.py` adds measured RMS and duration plus the
split column, and writes `dataset_card.json` with provenance, licence, sizes, and known
issues.

## Segmentation: from a long recording to labelled clips

Two situations produce a corpus, and they need different tools.

**Isolated clips already** (one word, one sound per file). Label from the filename or the
folder. This is the easy case and the case this section generates.

**One long recording** (a meeting, a field recording, a call). You must cut it, and the
cut is a labelling decision:

```python
from speech_core import audio

samples, rate = audio.read_wav("long_recording.wav")
trimmed = audio.trim_silence(samples, threshold=0.01, pad=160)

# Fixed windows, 1 s with 50% overlap: simple, and it cuts words in half.
window, hop = rate, rate // 2
chunks = [trimmed[i : i + window] for i in range(0, len(trimmed) - window + 1, hop)]

# Energy-based segmentation: put boundaries where the level drops.
energy = [audio.rms(trimmed[i : i + window]) for i in range(0, len(trimmed), hop)]
```

Fixed windows guarantee a shape and guarantee some clips are half a word. Energy
segmentation gives natural boundaries and fails on quiet speech, on background noise, and
on speech that never pauses. There is no free option; choose one and record the choice in
the manifest.

For the diarization exercise, `datasets.make_diarization_mix` builds a two-speaker clip
with exact segment boundaries. Its truth file is the thing you score against:

```json
{"segments": [{"start": 0.0, "end": 0.404, "speaker": "speaker_00"},
              {"start": 0.654, "end": 0.942, "speaker": "speaker_05"}, ...]}
```

## Splitting by source, not by clip

```python
from speech_core import datasets

splits = datasets.group_split(records, seed=0)
# {'train': 168, 'val': 36, 'test': 36} clips, and zero shared sources
naive = datasets.random_split(records, seed=0)
# {'train': 168, 'val': 36, 'test': 36} clips, 65 shared sources
```

`group_split` chooses the split at the level of `source_id` (a speaker, a recording
session, a device, a room) and then assigns every clip of that source to the same split.
`random_split` is included so the audit can show what the mistake looks like.

## The leakage audit

```python
audit = datasets.audit_leakage(splits)
print(audit["n_shared_sources"], audit["hard_leaky"])   # 0 False
print(audit["cross_split_near_duplicate_count"])        # diagnostic only
```

Two numbers, two meanings:

* **hard overlap** - the same `source_id` appears on both sides of a split. Always a bug.
  This is the decision.
* **soft near-duplicates** - two *different* sources whose fingerprints are within a few
  bits. A diagnostic.

The soft number needs a warning that this section measures rather than asserts. The
fingerprint is a coarse spectral-shape signature:

```python
fp = datasets.fingerprint(samples)     # 64 bits, gain-invariant
distance = datasets.hamming(fp_a, fp_b)
```

Measured on this corpus, same-source variants sit at a median of 2 bits apart for
environmental sounds, while different sources sit at a median of 25. For **speech** the
same measurement collapses: same-speaker pairs and different-speaker pairs both sit around
10 bits, because the fingerprint keys on *what was said*, not *who said it*. On the speech
corpus the soft count is therefore ~3,861 pairs even in a perfectly grouped split, and it
must not be read as leakage.

This is a useful lesson in measurement design: a fingerprint is only valid for the kind of
duplicate you designed it to find.

## Class balance and what it hides

```python
datasets.class_balance(records, datasets.ENV_CLASSES)
# {'alarm': 60, 'rain': 60, 'footsteps': 60, 'birdsong': 60}
```

Balanced counts are not balanced difficulty. Footsteps are quiet and transient, rain is
broadband, and a classifier can be 100% accurate on alarms and 60% on rain with every class
present 60 times. Per-class recall is the number that reveals this, which is why
[Lab A](labs/lab-a-environmental-sound-classifier.md) prints it.

## Corpus facts you can check

| Corpus | Clips | Sources / speakers | Classes | Splits (clips) |
| --- | --- | --- | --- | --- |
| `env` | 240 | 80 sources, 3 variants each | 4 | 168 / 36 / 36 |
| `speech` | 288 | 24 voices | 6 words | 204 / 48 / 36 |
| `diarization` | 1 mix | 2 voices | - | 3.482 s, 6 turns |

Speech is split by **speaker**: 17 train, 4 validation, 3 test voices, and the test voices
appear in no other split.

## Consent and rights in the manifest

Every generated corpus carries `"licence": "CC0-1.0"` and an explicit note that no human
recordings were used. If you replace it with real audio, the manifest needs four more
fields before any training happens: the licence, the consent basis, the retention period,
and the deletion contact. [Ethics, consent, and rights](ethics-and-consent.md) covers what
those mean.

## Debugging advice

| Symptom | Cause | Fix |
| --- | --- | --- |
| Test accuracy far above validation | sources shared across splits | run `audit_leakage`; regroup |
| `audit_leakage` reports soft duplicates everywhere | fingerprint matched to the wrong task | compare content, not identity; check thresholds |
| Manifest rows out of order with records | split then re-saved without the split column | regenerate with `make_audio_data.py` |
| A class has 0 recall | silence or clipping in that class | inspect RMS and peak per class |
| Splits are empty | too few sources for the fractions | lower `n_sources` requirement or change fractions |

## Exercises

1. Run `group_split` and `random_split` on the speech corpus, and report
   `n_shared_sources` for each. Then train a recogniser on both and compare test WER.
2. Build an energy-based segmenter for the diarization mix and score its boundaries
   against `truth.json` with a 50 ms tolerance.
3. Add a `device` field to the manifest and split by it. Does accuracy drop more than
   splitting by speaker?
4. Take 30 seconds of any recording you have the right to use, cut it into 1 s windows,
   and write a manifest with the fields above. Do not commit the audio.

Next: [SA05 - Audio classification with traditional machine learning](sa05-classical-classification.md)
