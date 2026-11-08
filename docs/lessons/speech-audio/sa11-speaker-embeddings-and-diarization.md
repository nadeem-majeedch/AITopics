# SA11 - Speaker embeddings and diarization, conceptually {#sa11}

**Section path:** [Overview](index.md) · **Module 11** · [Ethics](ethics-and-consent.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 2.5 h reading, 1.5 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | SA03, SA06, SA08 |
| **You will produce** | Verification scores with an EER, a diarization output with a DER, and a written distinction between recognition and identification |

!!! danger "Read this before the code"
    **Speech recognition asks what was said. Speaker recognition asks who said it.** They
    are different tasks with different risks. A transcript system can be reviewed by
    reading its output; a speaker identification system turns every recording into
    biometric data about an identifiable person, whether or not that was the intent.

    This section runs on **synthetic voices only**: parameter sets in code, not people.
    Applying the same code to real recordings requires a lawful basis, notice to the people
    recorded, a retention policy, and usually a data-protection review. Do not collect
    voice recordings from classmates, colleagues, or users without documented consent.

## Why this module exists

Two tasks share the word "speaker":

* **Verification** (1:1): "is this the person who claims to be enrolled?" - a yes/no
  decision, measured by false acceptance and false rejection.
* **Identification** (1:N): "which enrolled person is this?" - a ranking, measured by rank-1
  accuracy.
* **Diarization**: "who spoke when?" - segmentation and clustering, measured by diarization
  error rate.

All three need the same primitive: an embedding that represents voice rather than words.

## Building an embedding without a neural network

```python
from speech_core import speaker

emb = speaker.speaker_embedding(samples, sample_rate=16_000)
print(emb.shape)      # (18,)
```

That vector is two things concatenated:

1. **Spectral**: mean and standard deviation of MFCCs 1-8 over time - vocal tract shape.
2. **Pitch**: median F0 (on a log scale) and its standard deviation, from an
   autocorrelation pitch track.

Pitch gets its own weight (`pitch_weight=3.0`) because it is the cue that separates voices
with the same vowel space.

```python
track = speaker.f0_track(samples, sample_rate=16_000)
print(round(float(np.nanmedian(track)), 1))   # 93.6 Hz for voice 0
```

## The measurement that matters: EER

A verification system outputs a similarity score. Pick a threshold and you get:

* **FAR** (false acceptance rate): impostors accepted;
* **FRR** (false rejection rate): genuine speakers rejected.

Lower the threshold and FAR rises; raise it and FRR rises. The **equal error rate** is where
they cross - a single number summarising the trade-off, useful for comparing embeddings but
never sufficient for a deployment decision, where the costs of the two errors differ.

```python
from speech_core import speaker

scores, same = speaker.pair_scores(records)          # all pairs + ground truth
report = speaker.verification_report(scores, same)
print(report["eer"]["eer"], report["eer"]["threshold"])
```

Measured on the 288-clip speech corpus (24 voices, 41,328 pairs, 1,584 genuine):

| Embedding | EER | Threshold at EER |
| --- | --- | --- |
| MFCC statistics only (`pitch_weight=0`) | 0.516 | 0.849 |
| MFCC + pitch (`pitch_weight=3`) | 0.298 | 0.773 |

An EER of 0.516 is chance: the spectral-only embedding measures *what was said* more than
*who said it*, because the same speaker saying different words looks less similar than two
speakers saying the same word. This is the same failure that made the fingerprint in
[Lab A](labs/lab-a-environmental-sound-classifier.md) useless for speech, and it is the most
important lesson in the module.

Adding pitch nearly halves the error rate. A trained embedding network (x-vector,
ECAPA-TDNN) would take it far lower - typically EER below 0.02 on clean read speech - but
requires training data and a training objective (classification over speakers, or triplet
loss), which is outside this section's CPU budget.

## Identification

```python
from speech_core import metrics

embeddings = [speaker.speaker_embedding(r.samples, r.sample_rate) for r in records]
result = metrics.identification_accuracy(probes, probe_labels, gallery, gallery_labels)
print(result["rank1"])
```

Rank-1 accuracy requires a **gallery** (enrolled voices) and a **probe** set, and it must be
reported with the gallery size: 0.9 rank-1 over 5 voices is very different from 0.9 over
5,000.

## Diarization: who spoke when

The pipeline is three steps, and every one of them can be attacked separately:

```text
1. window the audio   (30 ms..30 s windows, 50% overlap)
2. embed each window  (speaker_embedding)
3. cluster            (k-means with k = number of speakers)
4. write labels onto a non-overlapping grid, merge runs
```

```python
from speech_core import datasets, speaker

mix = datasets.make_diarization_mix()
segments = speaker.diarize(mix["samples"], mix["sample_rate"], n_speakers=2)
for s in segments[:4]:
    print(s.start, s.end, s.speaker, s.confidence)
print(speaker.diarization_report(segments, mix["segments"]))
```

Measured on the 3.48 s two-speaker mix, 6 turns:

| Metric | Value |
| --- | --- |
| DER | 0.192 |
| Missed speech | 0.020 |
| False-alarm speech | 0.061 |
| Speaker confusion | 0.111 |
| Correct | 0.869 |

DER is `(miss + false alarm + confusion) / total speech`, so a perfect system scores 0.0 and
a system that labels everything as one speaker scores around 0.5 on a balanced two-speaker
recording. The 0.192 here comes mostly from confusion: the clustering assigns a few windows
to the wrong voice, and the boundaries are 10-50 ms off.

Three implementation details that changed the number, in order of size:

1. **Pitch in the clustering features.** Without it, k-means clusters by word, not voice.
2. **A speech mask.** Without it, the silence between turns is labelled with whichever
   speaker the nearest window belonged to, which appears as false-alarm speech (the first
   version scored DER 1.21, with false alarm 0.75).
3. **Non-overlapping output.** Labelling overlapping windows independently produces
   overlapping segments, which cannot be scored or read.

## Where diarization fails

| Situation | Why it fails | What production systems do |
| --- | --- | --- |
| Overlapping speech | one label per frame by construction | separate overlap detection, or a permutation-invariant model |
| Unknown speaker count | k must be given | estimate k from eigenvalue gaps or a threshold |
| Very short turns (< 0.3 s) | too few frames for an embedding | lower the window, accept more errors |
| Same-gender, similar-pitch speakers | embeddings nearly identical | better embeddings, not better clustering |
| Different channels per speaker | embedding encodes the channel | channel compensation, or per-channel normalisation |

## Distinguishing the tasks in your own writing

| Statement | Task | Consequence if wrong |
| --- | --- | --- |
| "The system transcribed the call" | ASR | content is exposed; retention rules apply |
| "The system verified the caller" | verification | a false accept is an authentication bypass |
| "The system identified the speaker" | identification | biometric processing of an identifiable person |
| "The system labelled who spoke when" | diarization | still biometric-adjacent; usually needs consent |

If you cannot say which row your system is in, it is not ready to be described.

## Debugging advice

| Symptom | Cause | Fix |
| --- | --- | --- |
| EER near 0.5 | embedding measures content, not voice | add pitch, or train an embedding model |
| EER 0.0 suspiciously | genuine and impostor pairs mixed | check `same` labels and split disjointness |
| DER > 1.0 | overlapping or inaccurate segments, missed speech | mask silence, non-overlapping grid |
| All windows in one cluster | k too small, or embeddings constant | check `emb.std()`, raise k |
| Boundary off by exactly the hop | grid written at window start | account for window centre |

## Exercises

1. Reproduce the EER table with `pitch_weight` 0, 1, 3 and 6. Where does it stop improving?
2. Score the diarization with `n_speakers=1` and `n_speakers=3`. What does DER do, and why
   is "just use more clusters" not a strategy?
3. Compute rank-1 identification with a gallery of 3 voices and of 12 voices from the same
   embeddings. How much does gallery size cost?
4. Write two sentences describing a system that transcribes meetings and also labels
   speakers, and identify which data-protection obligations each sentence triggers.

Next: [SA12 - Audio event detection and environmental sound](sa12-audio-event-detection.md)
