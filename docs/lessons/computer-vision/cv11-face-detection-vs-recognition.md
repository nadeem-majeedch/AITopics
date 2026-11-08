# CV11 - Face detection versus face recognition {#cv11}

**Section path:** [Overview](index.md) · **Module 11** · [Face exercises](faces.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 6 hours: 2.5 h reading, 3.5 h practice |
| **Hardware** | CPU-only, synthetic faces generated locally |
| **Prerequisites** | CV08 (detection), CV09 (IoU), CV02 (consent and provenance) |
| **You will produce** | Measured per-group detection recall, a landmark error, a verification curve with its EER, and a written data-protection position on your own demo |

!!! danger "Scope of this module"
    Everything here uses **synthetic faces** rendered from code, or images you have
    written consent to use. The module builds no covert identification, no surveillance,
    no face search over real people, and no system that recognises someone without their
    knowledge. If your project needs to identify real people, it needs consent, a legal
    basis, and a data-protection review - not a better model.

## The five things people call "face recognition"

They are different problems with different outputs, different metrics, and different
risks. Conflating them is the source of most bad claims.

| Task | Question | Output | Metric |
| --- | --- | --- | --- |
| **Face detection** | is there a face, and where? | box | recall, precision, IoU |
| **Landmarks** | where are the eyes, nose, mouth? | coordinates | mean/median pixel error |
| **Embedding** | what is a fixed-length vector for this face? | vector | none by itself |
| **Verification** | are these two the same person? (1:1) | score + threshold | FAR, FRR, EER |
| **Identification** | who is this, from a gallery? (1:N) | ranked list | rank-1 accuracy, false-match rate |

Embeddings are the substrate for the last two. A detector tells you *where*, an embedding
tells you *how to compare*, and verification/identification are two different questions
you can ask of the comparison.

## Detection: a classical rule, and why we use one

The section's detector is deliberately **not** a neural network. It implements the Kovac
skin-tone rule (RGB thresholds plus a chroma condition), finds the largest connected
component, and returns its bounding box.

That choice is pedagogical. A modern learned detector is accurate enough that its
demographic failures are subtle; a colour rule fails loudly, which makes the mechanism
visible and measurable in one run.

```python
detected = faces.detect_face(image)          # {'found': bool, 'box': (...), 'area': ...}
report = faces.detection_report(records)     # per-group recall at IoU 0.3
```

### Measured, 64 synthetic faces, 8 identities, 5 tone groups

| Group | Recall | n |
| --- | --- | --- |
| tone_a | 1.000 | 16 |
| tone_b | 1.000 | 24 |
| tone_c | 1.000 | 8 |
| tone_d_dark | **0.000** | 8 |
| tone_e_light | **0.000** | 8 |
| **overall** | **0.750** | 64 |

The rule works on mid-tones and fails completely at both ends of the luminance range.
This is the single most important number in the section: an overall recall of 0.750 would
be reported as "acceptable" by anyone who did not stratify.

!!! warning "What this number does and does not mean"
    It is a property of *this rule*, not of the people in the images. Real systems fail
    differently and less absolutely - but they do fail unevenly. Published audits of
    commercial systems have found higher error rates for darker-skinned faces and for
    women, which is why NIST's face-recognition evaluations report accuracy by
    demographic group. The lesson transfers: **always stratify, and report every group.**

## Landmarks

```python
landmarks = faces.locate_landmarks(image, box)      # eyes, nose, mouth centres
error = faces.landmark_error(predicted, truth)      # median pixel distance
```

Measured: landmarks localized on **64/64** faces with a **median error of 3.74 px** on
48-pixel faces, i.e. ~8% of face width. Enough for alignment and blink detection;
not enough for gaze estimation.

Landmarks are the bridge to alignment: rotating and scaling a face so the eyes sit at
fixed coordinates makes embeddings far more comparable. Skipping alignment is a common
reason a home-grown recogniser underperforms.

## Verification: the threshold is the system

An embedding model outputs a similarity score. A *system* outputs a decision, and the
decision needs a threshold.

```python
row = metrics.verification_metrics(scores, same_identity, threshold=0.9)
# {'far': ..., 'frr': ..., 'tar': ..., 'accuracy': ..., 'n': ...}
```

Two error rates, and you cannot lower both at once:

- **FAR** (false acceptance rate) - different people accepted as the same. The security
  error.
- **FRR** (false rejection rate) - the same person rejected. The usability error.
- **EER** - the threshold where FAR = FRR. A single-number summary of separability.

### Measured, 2016 pairs from 64 synthetic faces (224 same-identity pairs)

| Threshold | FAR | FRR | Accuracy |
| --- | --- | --- | --- |
| 0.90 | 0.049 | 0.607 | 0.889 |
| 0.95 | 0.000 | 0.955 | 0.894 |
| 0.98 | 0.000 | 0.996 | 0.889 |
| **EER** | 0.216 | 0.214 | at threshold **0.855** |

EER 0.215 is poor - this is a hand-built embedding on synthetic faces, not a trained
network. The shape of the result is what matters: tightening the threshold to 0.95 buys
FAR 0.000 at the cost of rejecting 95.5% of genuine pairs. **Accuracy stays ~0.89 at every
threshold**, which is why accuracy is the wrong metric for verification: the base rate
dominates it.

## Identification: 1:N is harder, and always answers

Measured: **rank-1 accuracy 0.812** for 16 probe images against a 48-image gallery.

Now the number that matters more: probes of people **not enrolled in the gallery** were
matched anyway **4 times out of 4** at threshold 0.5.

An identification system without a rejection threshold always returns *someone*. That is
the risk a 1:N deployment carries and a 1:1 check does not. Deployments need:

- an explicit rejection threshold and a measured false-match rate at it,
- a human in the loop for any consequential decision,
- a log of every query, who made it, and why.

## Privacy, consent, and law

Face data is **special-category personal data** under the GDPR (Article 9) and is
regulated separately in several jurisdictions: Illinois BIPA and Texas CUBI require
written consent before collecting biometric identifiers; some US states and cities
restrict police use; the EU AI Act treats real-time remote biometric identification in
public spaces as prohibited except in narrow, authorised cases. Rules differ by country
and change; check your jurisdiction and get legal review - this page is engineering
guidance, not legal advice.

Minimum engineering practice for anything involving real faces:

1. **Consent or a lawful basis, documented, before collection.** "It was on the internet"
   is neither.
2. **Data minimisation.** Store embeddings, not images, when you only need comparison -
   and treat embeddings as biometric data, because they are.
3. **Purpose limitation.** A system built to unlock one phone must not become a search
   index over a building's visitors.
4. **Retention limits and deletion.** A deletion request must remove embeddings, indexes,
   caches, and backups on a stated schedule.
5. **Transparency.** People should know a face system is operating, unless a narrow legal
   exception applies.
6. **Stratified evaluation** before deployment, including the worst-performing group, and
   re-evaluation after any model or threshold change.
7. **No covert identification.** Not as a demo, not as a class project, not "just to see".

## False matches: the arithmetic of 1:N

If a system has a 0.1% false-match rate per comparison, then searching a gallery of 1,000
people gives a `1 - (1 - 0.001)^1000 ≈ 63%` chance of at least one false match. The
per-comparison number that looked excellent becomes a coin flip at scale. This is why
false-match rate must be measured *at the operating threshold and gallery size you will
deploy*, not quoted from a paper.

## Practice (consent-based, synthetic only)

1. Run `python project_faces.py`. Record overall recall and every group's recall.
2. Lower the detector's IoU threshold from 0.3 to 0.1. Does the dark/light-tone recall
   change? Explain what that tells you about the failure.
3. Plot (as a text table) FAR and FRR for thresholds 0.80 to 0.98 in steps of 0.02. Find
   the EER yourself and compare with the reported 0.855.
4. Add three unenrolled identities, run identification, and report how many were accepted
   at threshold 0.5.
5. Write a 200-word data-protection note for a hypothetical door-unlock demo: what you
   store, why, for how long, and what you would refuse to build.

## Check yourself

1. Distinguish verification from identification, and say which metric each needs.
2. Why does overall recall of 0.750 misrepresent this detector?
3. A vendor quotes 99.9% accuracy for 1:1 and 99% for 1:N. What two questions do you ask
   before believing either?

## What comes next

[CV12](cv12-embeddings-and-similarity.md) generalises the embedding idea beyond faces:
image similarity search, indexing, and the precision@k metric that decides whether a
"similar images" feature is useful.
