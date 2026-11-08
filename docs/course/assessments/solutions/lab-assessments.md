# Lab assessments - solution approaches

```markdown
**Assessments:** [Overview](../index.md) · [Solutions](index.md) · [Lab assessments](../lab-assessments.md)
```

These are approaches, not copyable solutions. A lab assessment is about whether your
evidence answers the question; identical code with no evidence fails, and imperfect code
with a complete evidence trail can pass.

---

## LA1 - Compare two models with uncertainty

**Approach**

1. Load the CSV, drop identifiers, encode the target, and stratify the split. Save the
   row indices, not just the arrays, so the split can be audited.
2. Fit a scaler and the two models inside a pipeline, so no statistic crosses the split.
3. Bootstrap rows of the test set with replacement; for each resample compute accuracy
   and AUC for both models on the *same* resampled rows; store the differences.
4. Report the 2.5th and 97.5th percentiles.

**What good evidence looks like**

- Interval widths that reflect the test size; a 20-row test set gives very wide
  intervals, and the write-up says so.
- A paired difference interval that includes zero, with the conclusion "no measured
  difference at this sample size", not "the models are equal".
- The AUC interval computed from resampled scores, not from a formula applied to one
  number.

**Common failure:** bootstrapping each model independently and comparing overlapping
intervals. Overlap is not a test; the paired difference is the quantity of interest.

---

## LA2 - Audit faithfulness in a RAG answer set

**Approach**

1. Chunk with metadata and build an index; persist it so retrieval is reproducible.
2. Retrieve top-3 per question; store question, chunk ids, spans, and scores.
3. Write the annotation guide before labelling: supported means the span contains the
   claim's entities and numbers and a reader would accept it as evidence; partly means
   it supports part; unsupported means it does not; no citation means none was given.
4. Label 20 answers. Re-label five a day later and report agreement.

**What good evidence looks like**

- Separate retrieval recall@3 and unsupported-claim rate, with counts.
- At least one quoted unsupported case and one missing-citation case.
- A statement that 20 labels is a small sample and the rate is an estimate.

**Common failure:** labelling documents rather than spans. A document can be relevant
while the cited paragraph is not.

---

## LA3 - Verify a detector metric by hand

**Approach**

1. Convert COCO and YOLO annotations into one record type with `image_id`, `class`,
   `xyxy`, and verify round-trip equality on a sample.
2. Implement IoU; test identical boxes (1.0), disjoint (0.0), and a known half-overlap.
3. Sort predictions by score, match greedily to unused ground truth at IoU ≥ 0.5, and
   mark matches as used.
4. Build precision/recall arrays and integrate with the rule you state.
5. Include a five-box worked example in the write-up, with the IoU matrix and the
   matching decisions.

**What good evidence looks like**

- A hand-worked example that agrees with the code to three decimals.
- AP in [0, 1] for every class, and the rule (11-point or all-point) named.
- A threshold sweep table showing precision and recall moving in opposite directions.

**Common failure:** computing AP per image and averaging images. AP is computed over
the pooled detections per class, not per image.

---

## LA4 - WER with an error taxonomy

**Approach**

1. Write `normalise(text)` once; apply it to reference and hypothesis; test that both
   sides go through it.
2. Implement alignment and return `(S, D, I)` plus WER and CER.
3. Group by condition from the manifest and report counts per group.
4. Hand-check three pairs, including an insertion case, and show the alignment.

**What good evidence looks like**

- WER with `S`, `D`, `I`, and the reference length, so a reader can recompute it.
- Explicit handling of empty references: excluded and counted, or an error, never 0.0.
- An error table with 20 labelled errors and a category count.

**Common failure:** normalising the hypothesis but not the reference (or the reverse),
which moves WER by several points and looks like a model difference.

---

## LA5 - Counting logic with tests

**Approach**

1. Represent the line as two endpoints plus a normal; compute the signed side of a point.
2. Keep the last known side per track id; count only when a matched track changes sign
   between consecutive frames, and require a minimum displacement.
3. Write the five unit tests first, with synthetic trajectories, then implement until
   they pass.
4. Run on the clip, compare per direction with the manifest, and report absolute error.

**What good evidence looks like**

- Tests that fail on the naive implementation (proving they test something).
- Per-direction counts and errors, not a total that hides cancellation.
- A named failure: an occlusion that loses a track, or a parked car that never crosses.

**Common failure:** counting when the centre is within a pixel band of the line, which
turns jitter into repeated counts; the test for jitter is what catches it.

---

## LA6 - Permission matrix and attack tests

**Approach**

1. Write `policy.json` with roles, tools, resource patterns, and approval flags; default
   deny.
2. Implement `check(role, tool, args)` that resolves the resource path, rejects escapes,
   and returns allow, deny, or needs-approval.
3. Gate approval in the loop before dispatch; on denial or timeout, do not call the tool.
4. Run the six tests and record expected versus observed, plus the control responsible.

**What good evidence looks like**

- A table with all six rows, including a failed attack attempt and the control that
  stopped it.
- An audit excerpt for the approved action with actor, tool, decision, and correlation
  id.
- A statement of residual risk: what the controls do not prevent.

**Common failure:** checking permissions inside the tool implementation. By then the
decision to act has been made; the gate belongs at dispatch, before any side effect.
