# Face detection, landmarks, verification, and identification {#faces}

**Section path:** [Overview](index.md) · Module [CV11](cv11-face-detection-vs-recognition.md) · **Hands-on** · [Assessment](assessment.md)

| | |
| --- | --- |
| **Hardware** | CPU-only |
| **Code** | `projects/computer-vision/project_faces.py` |
| **Data** | 64 synthetic faces, 8 identities, 5 tone groups - generated locally, CC0-1.0 |
| **Time** | 3 hours for all five exercises |

!!! danger "What this page will not help you build"
    No covert identification. No surveillance. No search over real people's faces. No
    "just a demo" that recognises someone who has not consented. The exercises use
    synthetic faces rendered from code, and every method here is deliberately simple so the
    *failure* is measurable.

## The five distinctions

| Task | Input | Output | Metric | Failure that matters |
| --- | --- | --- | --- | --- |
| Detection | image | box | recall, precision | missing faces in some conditions |
| Landmarks | image + box | 5 coordinates | median pixel error | misalignment upstream of everything |
| Embedding | face crop | vector | (none alone) | features that ignore identity |
| Verification (1:1) | two faces | same/different + score | FAR, FRR, EER | accepting an impostor |
| Identification (1:N) | one face + gallery | ranked list | rank-1, false-match rate | always returning *someone* |

Detection answers *where*. Recognition is two different questions - *is this the same
person* (verification) and *who is this* (identification) - and they have different error
consequences. Embeddings are how both are computed.

## Run the reference program

```bash
cd projects/computer-vision
python project_faces.py
```

Verified output:

```text
=== detection (IoU >= 0.3)
overall recall 0.750 on 64 images
  tone_a           recall 1.000  (16/16)
  tone_b           recall 1.000  (24/24)
  tone_c           recall 1.000  (8/8)
  tone_d_dark      recall 0.000  (0/8)
  tone_e_light     recall 0.000  (0/8)

=== landmarks
localized on 64/64 faces; median error 3.74 px

=== verification (2016 pairs, 224 same-identity)
  threshold 0.90: FAR 0.049  FRR 0.607  accuracy 0.889
  threshold 0.95: FAR 0.000  FRR 0.955  accuracy 0.894
  threshold 0.98: FAR 0.000  FRR 0.996  accuracy 0.889
  equal error rate 0.215 at threshold 0.855

=== identification
rank-1 0.812 on 16 probes against 48 enrolled images
unenrolled people matched anyway at threshold 0.5: 4/4

report: .../outputs/faces_report.json
0 failure(s)
PASS  detection, landmarks, verification, and identification all measured
```

## Exercise 1 - Detection, stratified

```python
from vision_core import faces

records = faces.make_face_dataset(per_identity=8, size=40, seed=0)
report = faces.detection_report(records)
print(report["overall_recall"], report["per_group"])
```

1. Reproduce the table. Report overall recall **and** every group.
2. Explain why 0.750 is the wrong headline. (Hint: two groups are at exactly zero.)
3. Lower the IoU threshold to 0.1 and re-run. Does dark/light-tone recall recover? What
   does the answer tell you about the mechanism?

The detector is the Kovac skin-tone rule plus a connected component. It is classical on
purpose: a learned detector fails subtly, this one fails loudly, and the mechanism is
visible in a single RGB threshold.

## Exercise 2 - Landmarks and alignment

```python
box = faces.detect_face(image)["box"]
landmarks = faces.locate_landmarks(image, box)
error = faces.landmark_error(landmarks, truth)
```

1. Report median error on all detections (reference: 3.74 px on 48-px faces).
2. Align a face by rotating and scaling so the eyes sit at fixed coordinates, then
   re-extract the embedding. Report whether verification improves. This is the standard
   reason alignment exists.

## Exercise 3 - Verification: the threshold is the system

```python
from vision_core import metrics
row = metrics.verification_metrics(scores, same_identity, threshold=0.9)
print(row["far"], row["frr"], row["accuracy"])
```

1. Reproduce FAR/FRR at 0.90, 0.95, 0.98.
2. Find the EER yourself by scanning thresholds 0.80-0.99 in steps of 0.01.
3. Write the sentence a product owner needs: *"At threshold X, 1 in N different people are
   accepted, and about M in 100 genuine attempts are rejected."*

## Exercise 4 - Identification with a rejection option

```python
report = metrics.identification_metrics(probe_vectors, probe_names, gallery_vectors, gallery_names)
```

1. Report rank-1 (reference: 0.812, 16 probes, 48 gallery images).
2. Add three identities that are **not** enrolled. Report how many are accepted at 0.5.
   Reference run: **4 of 4**. Without a rejection threshold, 1:N always answers.
3. Add a rejection threshold, then report the trade: how many impostors rejected, how many
   genuine probes refused.

## Exercise 5 - Write the data-protection note

For a hypothetical consenting door-unlock demo (one enrolled person, their own device),
write 200 words covering:

- what is stored (image? embedding? both?) and why the minimum,
- retention and deletion, including backups and index rebuilds,
- who can query, and what is logged,
- what you would refuse to build even if asked,
- which law applies where you live, and that you are not a lawyer.

## Ethics, consent, and the law

**Consent and lawful basis.** Face images and face embeddings are special-category
biometric data under the GDPR (Art. 9). Several jurisdictions require explicit written
consent before collecting biometric identifiers (for example Illinois BIPA and Texas
CUBI). Public availability is not consent.

**Demographic performance.** Systems fail unevenly. The measured 0.000 recall for two tone
groups here is a synthetic, exaggerated version of a real phenomenon: NIST's face
recognition evaluations report accuracy by demographic group precisely because the
differences are large enough to matter. Always stratify, always report the worst group,
and never deploy on a pooled number alone.

**False matches scale with gallery size.** At a 0.1% per-comparison false-match rate, a
1,000-person gallery has roughly a 63% chance of at least one false match per query. Quote
false-match rates at your operating threshold *and* gallery size.

**Identification is not verification.** A 1:1 check with consent (unlocking your own phone)
and a 1:N search over a population are different systems with different legal treatment.
The EU AI Act restricts real-time remote biometric identification in public spaces;
several jurisdictions restrict police use; rules change and vary. Get legal review.

**Prohibited in this course.** Building or demonstrating: covert identification, face
search over people who have not consented, age/gender/emotion inference on real people,
"attendance by face" for students or employees, or any pipeline whose purpose is to track
individuals without their knowledge. If an employer or client asks for one, the correct
engineering answer is no, in writing.

**False positives have names.** A face system's error is not an abstraction: it is a person
denied a flight, a payment, or a room. Design for human review of any consequential
decision, and log enough to reverse a wrong one.

## Submission

```text
cv-faces/
  README.md            # what you ran, versions, hardware
  detection.md         # table with every group, plus the mechanism explanation
  verification.md      # FAR/FRR at three thresholds, your own EER, the product sentence
  identification.md    # rank-1, impostor acceptance, rejection-threshold trade
  dataprotection.md    # the 200-word note
```

## Rubric

| Criterion | Marks | What earns full marks |
| --- | --- | --- |
| Stratified detection analysis | 25 | all groups reported; mechanism explained; no pooled-only claim |
| Verification metrics | 25 | FAR/FRR/EER correct and interpreted as a product decision |
| Identification and rejection | 20 | impostor acceptance measured; threshold trade quantified |
| Data protection note | 20 | specific, minimal, legally aware, states limits of own knowledge |
| Scope discipline | 10 | no prohibited use attempted or half-built |

## Extensions

1. Replace the colour rule with a learned detector and re-run the stratification. Does the
   gap close, move, or persist?
2. Add pose variation (yaw ±30°) to the synthetic renderer and report the effect on
   landmark error and EER.
3. Compute an ROC curve and mark the operating point you would choose for a door lock.
4. Write a one-page refusal memo for a hypothetical request to run face recognition on a
   school's CCTV.
