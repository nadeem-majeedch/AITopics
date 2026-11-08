# Ethics, consent, and rights for voice systems

**Section path:** [Overview](index.md) · [Assessment](assessment.md) · [Model card](model-card.md)

Voice is different from images and text in one specific way: a recording identifies a person
even when it contains no name, and a model trained on it can reproduce characteristics of
that person. This page is the checklist for the parts of a voice project that are not
measured in WER.

## The distinction that must be stated in every project

| Task | Question | Data | Risk |
| --- | --- | --- | --- |
| Speech recognition (ASR) | what was said? | audio + transcript | content disclosure, retention |
| Speaker verification | is this the enrolled person? | audio + identity labels | authentication bypass |
| Speaker identification | which person is this? | audio + identity labels | biometric processing of an identifiable person |
| Diarization | who spoke when? | audio + segment labels | biometric-adjacent; needs consent |
| Synthesis (TTS) | say this text in a voice | text + voice model | impersonation, fraud |
| Voice conversion / cloning | say this in *that* person's voice | paired or unpaired audio | impersonation, non-consensual intimate audio |

"The system identifies speakers" and "the system transcribes speech" are not the same
sentence, and using one to describe the other is a misrepresentation with legal consequences
in several jurisdictions. In this section, [SA11](sa11-speaker-embeddings-and-diarization.md)
covers the speaker tasks and uses synthetic voices only.

## Why this section is entirely synthetic

Every clip is generated from code: formant speech and procedural environmental sounds,
released CC0-1.0. There are no recordings of people anywhere in the section.

That choice is not a shortcut around the ethics; it is the only way to hand a course to
students without asking them to collect biometric data. The cost is stated in every module:
synthetic voices are more regular than human voices, the vocabulary is six words, and there
are no accents, children, or disordered speech. When a module reports WER 0.000, it is a
statement about this corpus, not about a system that works on people.

## What real recordings require

Before the first training run on real audio, a project needs all six:

| Requirement | What "documented" means |
| --- | --- |
| **Lawful basis** | a written basis for processing (consent, contract, legitimate interest) recorded before collection |
| **Consent** | specific to machine-learning training, revocable, and separate from "we may record this call" |
| **Notice** | the people recorded know what is captured and what it is used for |
| **Purpose limitation** | the stated use; a new use needs a new basis |
| **Retention** | a period, a deletion mechanism, and a named owner |
| **Security** | access control, encryption, and a log of who listened to what |

A generic recording release usually does not cover training a model, and almost never covers
publishing a model that reproduces a voice.

## Consent is not a checkbox

Three questions that distinguish real consent from paper:

1. **Can they withdraw?** If the answer is "we would have to retrain everything", say so up
   front, and say what withdrawal can actually achieve.
2. **Do they know what the model will be used for?** "Research" is not a purpose.
3. **Do they know the model can memorise characteristics of their voice?** A speaker-adapted
   checkpoint is derived personal data.

Deletion requests are the hard case. A trained model cannot un-learn one clip reliably; the
practical options are retraining without the data, or rolling back to a checkpoint that
predates it. Both need to exist *before* the request arrives.

## Rights in the audio you use

| Source | What you need to check |
| --- | --- |
| Your own recordings | consent from other speakers present; a licence you can document |
| A public dataset | the dataset licence, plus the consent basis of the original collection |
| Broadcast or podcasts | usually not licensed for model training - check, do not assume |
| Customer calls | contractual basis, retention policy, disclosure |
| Synthetic corpora (this section) | CC0-1.0, no consent needed, no personal data |

A dataset card is not a licence. If a corpus says "research use" it may exclude commercial
training; if it says "CC BY-NC" it excludes commercial use entirely.

## Limitations that belong in a model card

The four dimensions reviewers ask about, and what this section can say:

| Dimension | This corpus | A real deployment would need |
| --- | --- | --- |
| **Accent and dialect** | none represented | WER broken down by accent group |
| **Background noise** | measured: 0.028 WER at 10 dB, 0.722 at 5 dB | condition table per environment |
| **Language coverage** | six English words | per-language evaluation, and a statement of what is unsupported |
| **Demographic performance** | unmeasured - no people recorded | stratified evaluation, with the caveat that it is descriptive, not a fairness guarantee |
| **Age and speech differences** | children, elderly, disordered speech untested | targeted data and separate reporting |
| **Channel** | 16 kHz mono, synthetic | telephone, far-field, mobile, codec effects |

"Unmeasured" is not "no bias". It means the disparity is unknown, which is a risk to state,
not a clean bill of health. A model card that says "no demographic data was collected" is
honest; one that says "the model is unbiased" is not supported by anything.

## Speaker identification is a different product

If your system can answer "who is this", it is processing biometric data. That triggers:

* a lawful basis specific to biometric processing in several jurisdictions;
* notice to every person whose voice is enrolled;
* a way to revoke enrolment;
* usually a data-protection impact assessment;
* a hard look at whether the task can be done without identifying people (diarization with
  anonymous labels often can).

Voice verification as an authentication factor also needs a fallback, because voices change
with illness and age, and because replay attacks are cheap.

## Synthesis and impersonation

Text to speech is not neutral when it can reproduce a person:

* **Cloning needs the speaker's consent**, not the recording owner's.
* **Disclose synthetic speech** where a listener could be deceived.
* **Do not build a clone as a course exercise** from a classmate's voice, even with verbal
  permission.
* **Fraud defence is a shared secret**, not voice recognition: a voice is now cheap to fake.

The synthesiser in [SA10](sa10-tts-and-speech-generation.md) uses parameter sets, not
recordings, and says so in its output.

## Accessibility and inclusion

Voice interfaces exclude people when:

* they require speech the system was never trained on (stutter, dysarthria, accent, a
  tracheostomy);
* they have no non-voice alternative;
* they fail silently instead of saying "I did not understand";
* they speak too fast, too quietly, or only in one language.

Minimum commitments: a keyboard or text alternative, a visible transcript, a stated
confidence behaviour, and a way to correct the system. None of those is expensive; all of
them are usually missing.

## Practical checklist

Print this next to the [deployment checklist](sa14-optimization-and-deployment.md#responsible-deployment-checklist).

- [ ] Every speaker has a documented basis for this specific use.
- [ ] Notice is visible to users, not buried in terms.
- [ ] Retention period and deletion path exist and have been tested once.
- [ ] Transcripts, embeddings, and checkpoints are in the data map as personal data.
- [ ] The task is described accurately (recognition vs identification vs synthesis).
- [ ] Limitations are written down, including the unmeasured ones.
- [ ] There is a non-voice path to the same outcome.
- [ ] A named person answers complaints.
- [ ] Synthetic audio, if used, is disclosed as synthetic.

## Where to read further

* Your jurisdiction's data-protection authority guidance on biometric data.
* The dataset card and licence of any corpus you use, read in full.
* [Model card](model-card.md) in this section, for the format of a limitation statement.
* [SA11](sa11-speaker-embeddings-and-diarization.md) for the technical distinction between
  recognition and identification.
