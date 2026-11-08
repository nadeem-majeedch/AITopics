# SA14 - Inference optimization, evaluation, and responsible deployment {#sa14}

**Section path:** [Overview](index.md) · **Module 14** · [Lab F](labs/lab-f-stt-interface.md) · [Lab H](labs/lab-h-model-comparison.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 5 hours: 2 h reading, 3 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | SA08, SA09, SA13 |
| **You will produce** | A speed/quality table, a calibration number, and the deployment checklist you would sign |

## Why this module exists

A model that works in a notebook and a system that can be deployed are separated by five
questions: how fast is it, how sure is it, what does it do when it fails, what data does it
keep, and who is accountable. This module answers each with a measurement rather than an
opinion.

## Speed: what actually matters

The right metric is not milliseconds; it is the **real-time factor** (RTF): processing time
divided by audio duration. RTF below 1 means faster than the audio plays, which is the
minimum for live transcription. RTF above 1 means the transcript falls behind.

Measured with [Lab H](labs/lab-h-model-comparison.md), 36 test clips, 10.52 s of audio:

| Model | Parameters | Size (MB) | Stride | Step (ms) | Train (s) | WER clean | WER 10 dB | Median (ms) | RTF |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| small | 94,299 | 0.37 | 3 | 30 | 5.44 | 0.000 | 0.361 | 37.5 | 0.0036 |
| baseline | 166,623 | 0.65 | 2 | 20 | 5.47 | 0.000 | 0.028 | 45.0 | 0.0043 |
| accurate | 372,615 | 1.43 | 1 | 10 | 12.11 | 0.000 | 0.750 | 76.8 | 0.0073 |

Three things this table says, and one it does not:

1. **Bigger is not automatically better.** The 167k model is much better in noise than both
   its smaller and larger neighbours (WER 0.028, against 0.361 and 0.750). With 204 training
   clips, the 372k model has enough capacity to memorise and nothing left over for noise. This
   is the deployment consequence of the overfitting section in SA06, and it is the number one
   reason to benchmark your own corpus instead of copying a model-size table.
2. **Stride dominates compute.** Stride 1 costs 1.70x the time of stride 2 for the same
   audio, and stride 3 is slightly *faster* than stride 2 (RTF 0.0036 vs 0.0043) while
   emitting 30 ms steps. The accurate model's entire cost is its finer output grid.
3. **Accuracy saturates on clean audio.** All three reach WER 0.000, so clean WER cannot
   choose between them. The noisy column can - and so can the lexicon check: snapping the
   worst model to the six known words takes it from 0.750 to 0.028 without a single gradient.
4. It does **not** say these numbers transfer. They are CPU-only, this machine, this corpus.

## Where the time actually goes

Two measurements that surprise students, both on the baseline model:

| Setting | Median time for 10.52 s of audio | RTF |
| --- | --- | --- |
| one batch, 1 thread | 47.0 ms | 0.0045 |
| one batch, 2 threads | 33.0 ms | 0.0031 |
| one batch, 8 threads | 27.6 ms | 0.0026 |
| clip by clip, 1 thread | 78.9 ms | 0.0075 |
| clip by clip, 8 threads | 73.4 ms | 0.0070 |

* **Threads saturate early.** Going from 1 to 2 threads saves 30%; the last 6 threads save
  another 16%. Small convolutions on short sequences do not parallelise well, and thread
  synchronisation costs more than it saves.
* **Batching matters more than threading.** At one thread the batched pass is 1.7x faster
  than 36 single-clip calls, and at 8 threads the gap widens to 2.7x. If you control the
  server, batch; if you are streaming, you cannot, and you pay the per-call overhead.
* **The lab default is one thread**, chosen for reproducibility (SA06), not speed. On a
  deployment box you would raise it; the accuracy numbers would then wobble in the third
  decimal, which is why benchmarks should pin it.

## Levers, in the order you should try them

| Lever | Effect on this model | Risk |
| --- | --- | --- |
| Raise `stride_time` | linear reduction in compute | must keep frames >= transcript length |
| Reduce `width`/`hidden` | fewer parameters and FLOPs | accuracy, especially in noise |
| Batch requests | 1.7-2.7x here | adds latency; useless for streaming |
| Limit `torch.set_num_threads` | frees cores for other work | slower per request |
| Quantise weights (int8) | typically 2-4x on CPU | accuracy loss; **not measured here** |
| Distil a bigger model into a smaller one | large | needs a teacher and data |
| Prune channels | moderate | needs fine-tuning to recover |

Two levers are deliberately listed without numbers. Quantisation and distillation change the
model, and quoting an expected speedup as if it were measured is exactly the habit this
section is trying to break. If you apply them, measure RTF and WER again.

## Confidence and calibration

The recogniser prints a confidence per utterance. It is the mean probability of the emitted
symbols, which is not the probability that the transcript is correct.

```python
from speech_core import metrics

ece = metrics.expected_calibration_error(confidences, correct, n_bins=10)
```

Expected calibration error is the weighted gap between confidence and accuracy across
bins. A model that says 0.9 and is right 70% of the time is overconfident, and any interface
that shows the number as a percentage is lying to its user.

Three honest options for a user-facing interface:

1. **Do not show a number.** Show a state: "confident" / "not sure, please repeat".
2. **Calibrate first** on held-out data (temperature scaling, isotonic regression), then show
   the calibrated value with a stated error bar.
3. **Show the alternatives** the decoder considered, which is more useful than a scalar.

## What to evaluate before shipping

| Question | Measurement | This section's number |
| --- | --- | --- |
| Does it work on new speakers? | WER on speaker-disjoint test | 0.000 clean, 0.028 at 10 dB, 0.722 at 5 dB |
| Does it work in noise? | WER per SNR condition | see the condition table in SA08 |
| Is it fast enough? | RTF on target hardware | 0.0036-0.0073 on this CPU |
| Is the confidence meaningful? | ECE, or a reliability diagram | not measured here; compute it |
| Does it fail safely? | silence and low-confidence behaviour | Lab F: silence -> "no speech" |
| Does adaptation break the old domain? | before/after on both corpora | Lab E: clean 0.000 -> 0.000 (saturated, see SA09) |
| Who is harmed by an error? | error analysis by group | see the limitation below |

## The limitations you must publish

Every audio system in this section shares a limitation list that belongs in its model card:

* **Accent and dialect.** Not represented: the corpus has no accents at all.
* **Background noise.** WER rises from 0.000 to 0.028 at 10 dB SNR, and to 0.722 at 5 dB.
* **Language coverage.** Six English words. Nothing else is tested, and nothing else works.
* **Demographic performance.** No demographic data exists here, because no people were
  recorded. That is not the same as "no bias" - it means the question is unmeasured, and an
  unmeasured disparity is a risk, not an absence of one.
* **Children, elderly, disordered speech.** Untested, and typically the worst-performing
  groups for real recognisers.
* **Overlapping speech.** Unsupported by construction.
* **Speaker characteristics.** Not evaluated for fairness, and speaker identification is a
  different task with its own risks (SA11).

A model card that omits these is not a model card; it is marketing. The section's template is
in [Model card](model-card.md).

## Responsible deployment checklist

Print this before shipping anything that processes voice.

| Area | Question | Evidence required |
| --- | --- | --- |
| Consent | Did every speaker consent to *this* use, including model training? | signed release or documented lawful basis |
| Notice | Do users know they are being recorded and processed? | UI text, or an audible cue |
| Retention | How long is audio kept, and who can delete it? | policy plus a tested deletion path |
| Derived data | Are transcripts, embeddings, or checkpoints treated as personal data? | storage map, access control |
| Vendor | Does audio leave the device? To whom, under what terms? | data processing agreement |
| Failure modes | What happens on low confidence, silence, and noise? | Lab F behaviour, with a test |
| Human override | Can a user correct or ignore the output? | interface affordance |
| Access | Are transcripts available to the people they describe? | export path |
| Monitoring | How would you notice degradation after deployment? | dashboards, sampled WER audits |
| Accountability | Who signs off, and who answers complaints? | a named owner |

## Monitoring after deployment

Models do not degrade in the lab; they degrade in the field, when the microphone changes, the
office gets noisier, or the user population shifts. Three cheap signals catch most of it:

1. **Confidence distribution drift.** A drop in mean confidence precedes a drop in accuracy.
2. **Silence and no-speech rate.** A sudden rise means a broken input path, not a quiet day.
3. **Sampled human review.** Fifty randomly chosen clips a week, transcribed by hand, gives
   an honest WER that no dashboard can fake.

None of those requires storing everything. Store aggregates and the reviewed sample, not the
whole stream, unless you have a documented reason and consent for the rest.

## Debugging advice

| Symptom | Cause | Fix |
| --- | --- | --- |
| RTF above 1 in production but 0.003 locally | wrong thread count, no batching, or a much larger model | measure on the target machine |
| Latency spikes | per-request model loading | load once, reuse |
| Confidence always 0.99 | model overfit, or `softmax` on wrong axis | check calibration and decode path |
| Output degrades over weeks | microphone or codec change | monitor confidence, re-audit WER |
| Memory grows | retaining audio buffers | stream in fixed chunks, release |

## Exercises

1. Reproduce the thread and batching table. Then try `torch.set_num_threads(4)` and explain
   why the gain does not continue.
2. Compute ECE for the Lab D recogniser on the 10 dB condition, using confidence and
   correct/incorrect. Is it over- or under-confident?
3. Take the deployment checklist and fill it in for the assistant in
   [Lab G](labs/lab-g-voice-chatbot.md). Which rows would block a real deployment?
4. Write the three monitoring signals you would alert on, with thresholds, and say what you
   would do when each fires.

Next: [Assessment](assessment.md) · [Model card](model-card.md) · [Ethics, consent, and rights](ethics-and-consent.md)
