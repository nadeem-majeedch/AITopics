# SA10 - Text to speech and pretrained speech generation {#sa10}

**Section path:** [Overview](index.md) · **Module 10** · [Lab G](labs/lab-g-voice-chatbot.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 2 h reading, 2 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | SA01, SA03, SA07 |
| **You will produce** | A synthesiser, a round-trip intelligibility measurement, and a list of what a real TTS system would change |

## Why this module exists

A voice interface that only listens is half an interface. Text to speech is also the part
of audio where the gap between "works" and "sounds like a person" is largest, and where
students most often skip measurement because "it obviously works".

This module builds a formant synthesiser from first principles - a glottal pulse through
three resonators - and measures what it produces with the recogniser from
[SA07](sa07-asr-and-stt.md). It then describes what production TTS actually is, so you know
which parts of the problem you are not solving.

## How speech is produced, and how to fake it

| Real speech | Model | This section's approximation |
| --- | --- | --- |
| Vocal folds vibrate | glottal pulse train at F0 | impulse train at 95-200 Hz, with jitter |
| Vocal tract shapes sound | formants F1-F3 | three resonator filters per phoneme |
| Lips, tongue change slowly | transitions | linear interpolation between phonemes |
| Lungs supply energy | amplitude envelope | per-phoneme gain, 5 ms fades |

A phoneme in this synthesiser is a triple of centre frequencies and bandwidths:

```python
from speech_core import synth

print(synth.PHONEMES["a"])
# Phoneme(kind='vowel', duration=0.12, formants=(730.0, 1090.0, 2440.0),
#         bandwidths=(80.0, 100.0, 140.0), voiced=True, burst_hz=2000.0)
print(synth.word_phonemes("start"))     # ('s', 't', 'a', 'r', 't')
```

The synthesiser concatenates phoneme audio and applies a pitch contour per voice profile.
Twelve base profiles span 95-200 Hz, and `datasets.voice_for(i)` derives 24 distinguishable
voices with small pitch, formant, and rate jitter.

```python
from speech_core import synth, datasets

profile = datasets.voice_for(0)
samples = synth.speak("start", profile, 16_000)
print(len(samples) / 16_000)     # 0.404 s for voice 0
```

## The text-to-speech front end

Real TTS has three stages, and this section implements two of them badly on purpose:

```text
text normalisation -> grapheme to phoneme -> acoustic model -> vocoder
"Dr. Smith"        "dɑktər smɪθ"            mel frames         waveform
```

* **Normalisation**: numbers, dates, abbreviations. "3/4" is "three quarters" or "March
  fourth" depending on context.
* **Grapheme to phoneme**: English spelling does not determine pronunciation. This section
  sidesteps the problem: six known words are looked up, everything else is spelled letter
  by letter using a crude letter-to-sound table.
* **Acoustic model + vocoder**: produce the waveform. Here, a formant synthesiser produces
  audio directly; there is no learned acoustic model.

```python
from speech_core import tts

engine = tts.FormantTTS(voice_index=1)
result = engine.synthesize("start left")
print(result.as_dict())
# {'text': 'start left', 'words': ['start', 'left'], 'duration': 0.896,
#  'in_vocabulary': True, 'note': ''}

unknown = engine.synthesize("banana")
# {'duration': 0.768, 'in_vocabulary': False,
#  'note': 'spelled 1 word(s) outside the vocabulary: banana'}
```

The `note` field is the honest part: the synthesiser tells you when it is spelling rather
than speaking. A system that hides that produces confident gibberish.

## Measuring synthesis

Two measurements matter, and neither is "it sounds fine to me".

**Intelligibility**: run the synthesised audio back through a recogniser and compute WER.
This is circular (your own recogniser, your own synthesiser) but it catches regressions,
and the round trip is exactly what a voice assistant does.

```python
from speech_core import tts, datasets, text, evaluate

engine = tts.FormantTTS(voice_index=0)
rec = ...  # a trained Recognizer
pairs = [(word, rec.transcribe_samples(*_synth(engine, word))["text"]) for word in datasets.WORDS]
text.corpus_error_rates(pairs)["wer"]
```

Measured across all 24 synthetic voices, six words each (144 hypotheses): corpus WER
**0.000**. Every voice, every word, correct.

That result is a warning, not a triumph. The synthesiser builds words from the same phoneme
inventory the recogniser was trained on, so the round trip measures *consistency*, not
intelligibility: neither component can reveal that the other is unrealistic. Two things make
it worth keeping anyway.

* **It is a regression test.** Earlier code in this module produced `yest`, `nop`, and
  `stotpt` on 7 of 24 voices (corpus WER 0.104), because the synthesiser released a trailing
  plosive after nasals and the recogniser transcribed that release as a character. The round
  trip caught it every time, with no listener required.
* **It says nothing about naturalness or human intelligibility.** A listener study is the only
  honest measure of those, and no amount of self-consistency substitutes for it.

Report the round trip as a pipeline check and nothing more. "The synthesiser is understandable
because the recogniser hears it" is circular, and a marker will (and should) fail it.

**Naturalness**: the standard measure is a mean opinion score (MOS) from human listeners,
on a 1-5 scale. It cannot be automated honestly, it needs consenting listeners, and any
number quoted without the listener pool and the instructions is meaningless. This
synthesiser would score near the bottom: flat prosody, no coarticulation, audible seams.

## What a real TTS system is

| Approach | Example | Size | Quality | Notes |
| --- | --- | --- | --- | --- |
| Formant (this module) | - | kilobytes | robotic | fully interpretable, no training |
| Concatenative | unit selection | large DB | natural for one voice | needs a recorded corpus and consent |
| Neural acoustic + vocoder | Tacotron/WaveNet, FastSpeech/HiFi-GAN | 50-500 MB | near-human | GPU for training, CPU for inference |
| End-to-end | VITS | ~100 MB | near-human | single model, harder to control |
| Hosted | commercial APIs | none | near-human | audio leaves your machine; per-character cost |

`tts.neural_tts_available()` reports why the neural path is not used here:

```python
tts.neural_tts_available()
# (False, "No neural TTS package is installed (checked piper, TTS, torchaudio). ...")
```

That is a deliberate check rather than a try/except at import: a student should see a reason,
not a stack trace.

## Voice cloning, and why this module does not do it

Cloning a voice from a few seconds of audio is technically easy now and ethically fraught.
The relevant facts:

* a voice is personal data in several jurisdictions, and in some it is a protected
  characteristic;
* cloning requires the *speaker's* consent, not the recording owner's;
* synthetic speech is now used for fraud, and the defence is a shared secret, not voice
  recognition;
* publishing a cloned voice model is publishing derived personal data.

This section keeps every voice a parameter set in code, which is the only version of this
exercise that can be handed to students without a consent process.

## Debugging advice

| Symptom | Cause | Fix |
| --- | --- | --- |
| Output is silence | all phonemes outside the vocabulary and letter map empty | check `result.in_vocabulary` and `result.note` |
| Clicks between words | missing fades | `synth._fade` is applied per phoneme; concatenate with gaps |
| Speech is unintelligibly fast | `profile.rate` too high | clamp to 0.8-1.25 |
| Round-trip WER is 1.0 | recogniser trained on different sample rate or normalisation | check `Recognizer.mean/std` |
| Volume varies between utterances | inconsistent `gain_db` per profile | normalise output with `audio.peak_normalize` |

## Exercises

1. Reproduce the round-trip table, then swap the recogniser for one trained with fewer
   epochs. Does intelligibility drop as fast as recognition accuracy?
2. Add a seventh word to `synth.WORDS` by composing existing phonemes. Does the recogniser
   refuse it (out of vocabulary) as expected?
3. Measure the duration of "Sorry, could you say that again?" (3.219 s measured). At 150
   words per minute, how long should it be?
4. Write the consent script you would use to record a colleague's voice for a TTS model,
   including what happens to the model if they withdraw.

Next: [SA11 - Speaker embeddings and diarization](sa11-speaker-embeddings-and-diarization.md)
