# Speech and audio: assessment

**Section path:** [Overview](index.md) · **Assessment**

| | |
| --- | --- |
| **Total** | 100 points: 72 labs, 20 capstone report, 8 written answers |
| **Pass** | 60 points, with at least 5 of 8 labs submitted and the capstone submitted |
| **Time** | 58 hours of study, of which 30 are labs |

## What is assessed

| Component | Weight | Evidence |
| --- | --- | --- |
| Lab A - environmental sound classifier | 10 | `outputs/lab_a_env_classifier.json` + write-up |
| Lab B - representations | 6 | `outputs/lab_b_features.json` + the two PNGs |
| Lab C - transcribe a clip | 8 | `outputs/lab_c_transcribe.json` + annotated frame labels |
| Lab D - WER evaluation | 10 | `outputs/lab_d_wer.json` + condition table |
| Lab E - adaptation | 10 | `outputs/lab_e_adaptation.json` + consent statement |
| Lab F - STT interface | 8 | working CLI + `outputs/lab_f_stt.json` |
| Lab G - voice chatbot | 10 | `outputs/lab_g_voice_chatbot.json` + turn table |
| Lab H - model comparison | 10 | `outputs/lab_h_model_comparison.json` + recommendation |
| Capstone report | 20 | model card, deployment checklist, limitation analysis |
| Written answers | 8 | four short answers, one page total |

Every lab writes its own JSON report, so your numbers are auditable: a marker can re-run the
script and compare. That cuts both ways - do not edit the JSON, and do not paste numbers from
a different run into your write-up.

## Marking bands

Each lab is marked on four things, not on the accuracy number:

| Criterion | Weight in a lab | What earns full marks |
| --- | --- | --- |
| Correctness of the measurement | 40% | the right split, the right metric, counts shown |
| Error analysis | 25% | you say *which* examples fail and why |
| Honesty about limits | 20% | the number is reported with its condition and its variance |
| Reproducibility | 15% | seed, epochs, split, and command are stated |

A student who reports 0.83 accuracy with a correct split, a per-class table, and a stated
variance scores higher than one who reports 1.000 with no split audit. The second is not
evidence; it is a number.

## What a good write-up contains

1. **The command** that produced the numbers.
2. **The configuration**: epochs, seed, split, model size.
3. **The table**, with counts or supports where they exist.
4. **Two or three sentences of interpretation** that could not be copied from this page,
   because they refer to *your* run.
5. **One limitation** you found, not one from the list.

Anything else is optional.

## Capstone: document a voice interface

Choose one of these, or propose your own:

* a command interface for a hands-free tool (the Lab G assistant, extended);
* a transcription service for short recordings, with a retention policy;
* an environmental-sound monitor with an alerting threshold.

Produce:

| Section | Required content |
| --- | --- |
| Intended use | who uses it, for what, in what conditions |
| Out of scope | what it must not be used for, stated plainly |
| Data | provenance, licence, consent basis, retention, deletion path |
| Evaluation | WER or accuracy with condition table, per-class or per-word breakdown |
| Robustness | what happens at low SNR, wrong sample rate, silence, and accents |
| Speed | RTF on the target hardware, measured |
| Failure behaviour | what the user sees when confidence is low |
| Monitoring | the three signals you would alert on |
| Accountability | who owns it, and how a complaint is handled |

The [model card](model-card.md) template is the format; the
[ethics page](ethics-and-consent.md) is the checklist. A capstone that omits the out-of-scope
section is incomplete regardless of its accuracy.

## Rubric for the capstone

| Band | Description |
| --- | --- |
| 18-20 | Every section filled with measured numbers; limitations are specific to the system; the deployment checklist is complete and honest |
| 14-17 | Complete, with one or two unmeasured claims or a generic limitation list |
| 10-13 | Missing robustness or consent detail; numbers present but not reproducible |
| 6-9 | A demo description rather than an evaluation; no condition table |
| 0-5 | No measurable evaluation, or a claim contradicted by the student's own output |

## Written answers (8 points)

Answer all four, one paragraph each, citing a number you measured:

1. Why is a clip-level split of speaker data a bug, and what does it inflate?
2. Your recogniser reaches WER 0.000 on the clean test set. What does that number *not*
   tell you?
3. Adaptation improved noisy WER and worsened clean WER. How do you decide whether to ship
   it?
4. Name one thing your system would do if a user's accent is not represented in the training
   data, and one thing you would do about it.

## Academic integrity

* Report your own runs. Re-running a lab with a different seed produces different numbers, and
  that is fine - the marker is checking that your interpretation matches your output.
* You may use any public library, but state what you used. The exercise is the measurement,
  not the implementation.
* Do not submit audio recorded from other people without their documented consent. If an
  exercise asks for real audio, synthetic or self-recorded audio is acceptable, and is what
  the lab expects.
* Do not paste a model card from another project. The point of the card is that it describes
  your system's measured behaviour.
