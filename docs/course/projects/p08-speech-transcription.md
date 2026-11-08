# P08 - Speech recognition and transcription application

```markdown
**Projects:** [Index](index.md) · [Completion checklist](completion-checklist.md) · [Report template](report-template.md)
```

| | |
| --- | --- |
| **Difficulty** | Intermediate |
| **Effort** | 40-50 hours |
| **Hardware** | CPU-only for the course corpus; a GPU helps for larger models |
| **Prerequisites** | [SA02 loading and preprocessing](../../lessons/speech-audio/sa02-loading-and-preprocessing.md), [SA03 waveform, spectrogram, Mel](../../lessons/speech-audio/sa03-waveform-spectrogram-mel.md), [SA07 ASR and speech to text](../../lessons/speech-audio/sa07-asr-and-stt.md), [SA08 word error rate](../../lessons/speech-audio/sa08-wer-and-transcription-evaluation.md), [SA09 adapting a pretrained ASR](../../lessons/speech-audio/sa09-adapting-pretrained-asr.md), [SA14 optimization and deployment](../../lessons/speech-audio/sa14-optimization-and-deployment.md) |
| **Builds on** | Speech labs C, D, E, and F |
| **Ethics** | Read [ethics and consent](../../lessons/speech-audio/ethics-and-consent.md) before recording anything |

## 1. Problem statement and motivation

A small team records meetings, lectures, or field interviews and needs searchable
text. Off-the-shelf transcription is good on clean studio audio and much worse on
the audio people actually record: one phone microphone, a fan, overlapping speech,
and names the model has never seen.

This project builds a transcription pipeline around a pretrained recogniser, then
measures where it fails. The deliverable is not "I ran Whisper"; it is a WER table
by condition, an error taxonomy, and a transcript format that a reader can trust
because uncertain segments are marked.

**Decision supported:** whether a transcript is good enough to quote, search, or
archive without a human listening check.

## 2. Intended learning outcomes

1. Load, resample, and normalise audio correctly, and prove the pipeline preserves
   duration and content.
2. Run a pretrained ASR model locally and record its provenance and licence.
3. Compute WER and CER from scratch, with normalisation rules stated explicitly.
4. Evaluate by condition: clean, noisy, quiet, accented or synthetic speaker,
   domain vocabulary.
5. Analyse errors by substitution, deletion, and insertion type with examples.
6. Add domain vocabulary correction and measure the change honestly.
7. Produce timestamped transcripts with a confidence or uncertainty indication.

## 3. Difficulty and prerequisites

**Level:** Intermediate. 40-50 hours: 8 audio pipeline, 10 ASR integration, 12
evaluation, 8 vocabulary adaptation, 8 application, 8 writing.

Requires SA02, SA03, SA07-SA09. If you have never computed WER by hand, do the
SA08 exercise first; a wrong normalisation rule can move WER by several points.

## 4. Scope and out-of-scope features

**In scope**

- One pretrained ASR model (local weights) plus one simpler baseline (for example
  a tiny model or a keyword spotter) if feasible.
- Timestamped transcription of 20-60 short clips, or one 10-minute recording split
  into segments.
- WER/CER by condition and by speaker group present in your data.
- Vocabulary correction using a domain word list.
- A CLI that transcribes a file or a folder and writes `.txt` and `.json` outputs.
- Optional: a simple GUI or web page, reusing P05 patterns.

**Out of scope**

- Training an ASR model from scratch.
- Speaker identification, diarisation, or biometric use of voice. Diarisation is a
  separate topic and not required here.
- Voice cloning or speech synthesis.
- Transcribing other people's private conversations. Consent is mandatory.
- Claims about languages or accents not represented in your evaluation set.

## 5. Dataset options, licences, and preparation

| Option | Source | Licence | Notes |
| --- | --- | --- | --- |
| A (default, offline) | `python scripts/make_audio_data.py` → `data/audio/speech/` | CC0-1.0, synthetic | 24 synthetic speakers x 6 words x 2; no real voices |
| B | LibriSpeech `dev-clean` subset | CC BY 4.0 per the dataset page | Real speech, read audiobooks; download required |
| C | Common Voice, your language | CC0-1.0 | Check the version and the speaker metadata you use |
| D | Your own recordings | Consent from every speaker, documented | Best for domain vocabulary; delete raw audio when done unless consent allows retention |

**Preparation**

1. Generate option A and read the dataset card. Note explicitly that synthetic
   voices are not a substitute for real speech.
2. For option B-D, write a consent and retention note: who spoke, what they agreed
   to, where files live, when they are deleted.
3. Build a manifest: file, duration, sample rate, channels, transcript, condition
   label (clean/noisy/quiet), speaker pseudonym.
4. Split clips into dev and test by speaker, not by clip, so a speaker cannot
   appear in both.
5. Normalise text for scoring: lowercase, strip punctuation, expand or remove
   numbers consistently, collapse whitespace. Write the rules down and keep them in
   one function used by every metric.

## 6. Recommended baseline

**Pretrained ASR, default settings, no adaptation.** Report WER on the full test
set and by condition. This is the number every later change must beat.

If a pretrained model cannot be downloaded in your environment, use the course's
synthetic corpus with a small local model or a keyword-based recogniser and state
plainly that the result does not transfer to real speech.

Second baseline: the same model with a greedy decoding change (for example beam
width or temperature 0) to show that decoding settings matter.

## 7. Milestones

| # | Milestone | Evidence | Hours |
| --- | --- | --- | --- |
| 1 | Audio pipeline and manifest | Duration check, resampling test, consent note | 8 |
| 2 | WER implementation | Hand-checked examples including insertion and deletion | 6 |
| 3 | Baseline transcription | Transcripts, WER/CER overall and by condition | 10 |
| 4 | Error analysis | Substitution/deletion/insertion counts with examples | 8 |
| 5 | Vocabulary adaptation | Word list or correction layer, before/after WER | 8 |
| 6 | Application and package | CLI, timestamps, report, rerun | 10 |

## 8. Repository or folder structure

```text
capstone-p08/
  README.md
  requirements.txt
  configs/
    asr.yaml              # model id, sample rate, beam, language, device
  data/
    dataset-card.md
    consent.md
    manifest.csv          # path, duration, transcript, condition, speaker
  src/
    audio.py              # load, resample, mono, trim, duration assertions
    transcribe.py         # model wrapper, timestamps, chunking
    textnorm.py           # one normalisation function for scoring and output
    wer.py                # wer, cer, alignment-based error counts
    vocab.py              # domain word list and correction
    evaluate.py
    cli.py
  tests/
    test_audio.py
    test_wer.py
    test_textnorm.py
  reports/
    report.md
    model-card.md
  outputs/
    transcripts/
    metrics.json
    errors.csv
```

## 9. Detailed development tasks

1. `audio.py`: load with a library that reports sample rate, convert to mono,
   resample to the model's rate, and assert that duration is within 1% of the
   original. Peak-normalise only if the model expects it; document the choice.
2. Chunking: for long files, split on silence or fixed windows with overlap, then
   merge transcripts without duplicating words at the boundary. Test the merge on a
   known sentence.
3. `textnorm.py`: lowercase, remove punctuation, normalise digits, collapse spaces.
   The same function must be used for reference and hypothesis. A test asserts that
   both sides are normalised identically.
4. `wer.py`: Levenshtein alignment over words; return WER, CER, and counts of
   substitutions, deletions, insertions. Test with hand-computed cases:
   one substitution in four words = 0.25; one insertion = 0.25; empty reference
   raises a clear error rather than dividing by zero.
5. `transcribe.py`: run the model with the pinned decoding config, capture word or
   segment timestamps if the model exposes them, and store raw output plus
   normalised text separately.
6. Baseline evaluation: WER and CER overall, by condition, and by speaker. Report
   the number of clips in each cell; a cell with two clips is not a result.
7. Error analysis: for the worst 30 errors, label the cause (homophone,
   named entity, number, disfluency, noise, truncation, reference error). Report
   counts and quote three pairs.
8. `vocab.py`: a domain word list with canonical spellings. Apply either
   constrained decoding (if supported) or a post-hoc fuzzy correction limited to
   near-matches. Measure both precision and damage: correction can fix names and
   break ordinary words. Report WER before and after, plus the number of changed
   tokens.
9. `cli.py`: `transcribe.py audio.wav --out out/` writes `out/audio.txt`,
   `out/audio.json`, and prints WER if a reference is supplied. Folder mode
   processes every `.wav` and writes a summary table.
10. Uncertainty: mark segments where the model's average token probability is low,
    or where the audio is clipped or silent. A transcript that flags two uncertain
    names is more useful than one that silently invents them.
11. Model card: model provenance, licence, languages evaluated, conditions
    evaluated, WER table, known failures, consent and retention statement.
12. Latency: real-time factor (processing seconds per audio second) on your
    hardware, median and p95.

## 10. Testing and evaluation plan

| Test | Proves | Pass condition |
| --- | --- | --- |
| Audio duration test | Resampling is lossless in length | Within 1% of original |
| Mono conversion test | Channels handled | Stereo input yields expected mono length |
| WER unit tests | Metric is correct | Hand cases pass, including insertions |
| Normalisation symmetry | No silent mismatch | Reference and hypothesis pass the same function |
| Chunk merge test | No duplicated words | Merged text equals the expected sentence |
| Vocab correction test | Correction is bounded | Only near-matches change; unrelated words untouched |
| CLI smoke test | Works outside notebook | Transcribes one file and writes both outputs |

Protocol: choose decoding settings on dev, evaluate test once. Vocabulary correction
parameters (edit distance, threshold) are chosen on dev and reported.

## 11. Metrics

**Quantitative**

| Metric | Why |
| --- | --- |
| WER overall and by condition | The standard, with the caveat that it weights words equally |
| CER | Useful for short clips and morphology |
| Substitution/deletion/insertion counts | Tells you *how* it fails |
| Named-entity error rate | Names are what users search for |
| Real-time factor | Whether it is usable |
| Percentage of segments flagged uncertain | Honesty and review workload |

**Qualitative**

- Three transcript excerpts with errors, and what a reader would conclude.
- Whether the model hallucinates fluent text during silence (test explicitly with
  10 seconds of silence).
- Consent and retention practice, stated plainly.

## 12. Expected deliverables

- [ ] Audio pipeline with duration assertions.
- [ ] Manifest with conditions and speaker pseudonyms.
- [ ] WER/CER implementation with tests.
- [ ] Baseline transcriptions and a metrics table by condition.
- [ ] Error taxonomy with counts.
- [ ] Vocabulary correction with before/after results and damage count.
- [ ] CLI producing `.txt` and `.json` with timestamps or uncertainty marks.
- [ ] Model card, consent note, and report.
- [ ] Tests passing.

## 13. Suggested extensions

- Add speaker diarisation for two-speaker clips and report diarisation error rate.
- Add a search interface over transcripts with timestamp links.
- Compare two model sizes at equal accuracy budget and report the real-time factor.
- Evaluate on a genuinely noisy recording you make yourself, with consent, and
  report the gap from the clean set.

## 14. Common failure modes and troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| WER above 1.0 | References and hypotheses normalised differently | Use one normalisation function; inspect a failing pair |
| Transcript is empty | Wrong sample rate or silent audio | Check duration and RMS; resample to the model rate |
| Words duplicated at chunk boundaries | Overlap merged naively | Merge with overlap-aware stitching; test it |
| Model invents text in silence | Hallucination on non-speech | Detect low energy and skip; report the behaviour |
| Numbers always wrong | Normalisation mismatch (digits vs words) | Choose one convention and apply it to both sides |
| Names consistently wrong | Out-of-vocabulary tokens | Domain word list or constrained decoding; measure damage |
| Slow on CPU | Model too large for the hardware | Smaller model, quantisation, or shorter chunks; report RTF |
| Different results per run | Sampling enabled | Use greedy or fixed seed; record decoding config |

## 15. Marking rubric

| Criterion | Weight | 4 - Excellent | 3 - Meets | 2 - Approaching | 1 - Not yet |
| --- | --- | --- | --- | --- | --- |
| Audio pipeline correctness | 15% | Duration checks, resampling tests, chunk merging verified | Correct pipeline | Minor errors | Audio mishandled |
| Metric implementation | 20% | WER/CER from scratch, hand-checked, error counts | Correct WER via a library with tests | WER only, unverified | Wrong metric |
| Evaluation design | 20% | Conditions, speakers, named entities, uncertainty flags | WER by condition | Overall WER only | No meaningful evaluation |
| Adaptation and analysis | 15% | Vocabulary change measured with damage count | Adaptation attempted and measured | Attempted, unmeasured | None |
| Application and packaging | 15% | CLI with timestamps, JSON, real-time factor | Working CLI | Notebook only | Does not run |
| Ethics, consent, communication | 15% | Consent documented, hallucination tested, limits precise | Consent and limits stated | Thin | Ignores consent or overclaims |

**Bands:** 90-100 portfolio-ready; 80-89 solid; 70-79 pipeline works, evaluation
thin; below 70 the transcript quality claim is unsupported.

## 16. Self-review checklist

- [ ] Every recording has documented consent or a licence.
- [ ] Normalisation is one function used on both sides.
- [ ] WER is reported with clip counts per condition.
- [ ] Named entities are evaluated separately.
- [ ] Silence behaviour is tested.
- [ ] Vocabulary correction reports damage, not just gains.
- [ ] Uncertainty or low-confidence segments are marked.
- [ ] Model licence and provenance are recorded.
- [ ] No raw audio of other people is committed.

## 17. Report template

Use the shared [report template](report-template.md), adding:

1. **Audio and consent** - sources, conditions, retention, speaker handling.
2. **Metric definition** - normalisation rules and a worked WER example.
3. **Results by condition** - table with clip counts and error counts.
4. **Error taxonomy** - cause, count, three quoted pairs.
5. **Adaptation** - vocabulary change, WER before/after, tokens changed.

## 18. Demonstration and presentation checklist

- [ ] Transcribe a clean clip and a noisy one, showing both outputs.
- [ ] Show WER by condition with counts.
- [ ] Show one substitution, one deletion, one insertion with timestamps.
- [ ] Show a name corrected by the vocabulary layer.
- [ ] Show silence handling.
- [ ] State consent and retention in one sentence.
- [ ] Answer: "Would you publish this transcript unedited? Under what conditions?"

**Demo trap:** demoing only the clean clip. The noisy one is the evaluation.

---

**Previous:** [P07 object detector](p07-object-detector.md) · **Next:** [P09 video analytics](p09-video-vehicle-analytics.md) · [Index](index.md)
