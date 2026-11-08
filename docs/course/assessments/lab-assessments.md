# Practical lab assessments

```markdown
**Assessments:** [Overview](index.md) · **Lab assessments** · [Solutions](solutions/lab-assessments.md)
```

Six timed practical tasks. Each is a smaller, independent version of a module lab:
you get inputs, a time budget, and a required evidence list. They are meant to be done
without a notebook open, using documentation only.

These are **not** graded. Use the pass conditions to decide whether your evidence is
complete, and the [course lab rubric](../assessments.md#lab-rubric) to score quality.

**Rules for all six**

- Time budget includes writing, not just coding.
- Allowed: language and library documentation, your own notes, the course lessons.
- Not allowed: copying a module lab solution, or presenting a tutorial's numbers as
  your result.
- Every number in your write-up must come from a file your code produced.
- If a check cannot run on your machine, say so and explain what you did instead.

---

## LA1 - Compare two models with uncertainty

**Time:** 3 hours. **Maps to:** F10, P01.

**Input:** `data/production/customers/customers.csv` (generate with
`python scripts/make_eval_data.py`), target `churned`.

**Tasks**

1. Build a stratified 70/15/15 split with a fixed seed, saved to disk.
2. Train logistic regression and a gradient-boosted model on identical features.
3. Report accuracy and ROC AUC with 95% bootstrap intervals (1,000 resamples).
4. Report the paired difference in accuracy with an interval.
5. State whether the difference is distinguishable from zero at your sample size.

**Evidence**

- `metrics.json` with point estimates, intervals, and resample count.
- A 150-word interpretation that does not claim a winner if the interval spans zero.
- The split file or its hash, so the comparison is reproducible.

**Pass conditions**

- Intervals are computed on the test set, not the training set.
- The paired interval resamples the same rows for both models.
- The write-up distinguishes "no measured difference" from "the models are equal".

---

## LA2 - Audit faithfulness in a RAG answer set

**Time:** 3 hours. **Maps to:** CA13, CA14, P04.

**Input:** `data/chatbots-rag/` corpus and `test_questions.json`.

**Tasks**

1. Build an index with a documented chunk size and overlap.
2. Retrieve top-3 for each test question and record `doc_id` and span.
3. For 20 answers (extractive is fine), label each citation: supported, partly
   supported, unsupported, or no citation.
4. Report retrieval recall@3 and the unsupported-claim rate.
5. Quote two unsupported cases and name the cause.

**Evidence**

- `answers.jsonl` with question, answer, citation, and label.
- A short annotation guide written before labelling.
- A table of recall@3 and unsupported rate with counts.

**Pass conditions**

- Labels distinguish "citation missing" from "citation wrong".
- At least one failure is quoted verbatim.
- The write-up does not describe recall as answer quality.

---

## LA3 - Verify a detector metric by hand

**Time:** 3 hours. **Maps to:** CV09, P07.

**Input:** `data/computer-vision/detection/` (images, YOLO labels, COCO json).

**Tasks**

1. Convert annotations to a single internal format and prove round-trip equality.
2. Implement IoU and greedy matching at IoU 0.5.
3. Compute AP for one class on five images and verify it against a hand-computed
   example you include in the write-up.
4. Compute mAP@0.5 with a provided or self-trained detector's predictions.
5. Sweep the score threshold and report precision, recall, and false positives per
   image at three thresholds.

**Evidence**

- `metrics.json` with per-class AP and the sweep.
- The hand-worked example (boxes, IoUs, matches, precision/recall points).
- One annotated image showing a true positive and a false positive.

**Pass conditions**

- A prediction cannot match more than one ground-truth box.
- AP is between 0 and 1, and the rule (11-point or all-point) is stated.
- The threshold sweep shows the precision/recall trade-off, not just one point.

---

## LA4 - WER with an error taxonomy

**Time:** 3 hours. **Maps to:** SA08, P08.

**Input:** `data/audio/speech/` manifest and transcripts.

**Tasks**

1. Write one text normalisation function and use it for both reference and
   hypothesis.
2. Implement WER with substitution, deletion, and insertion counts.
3. Report WER and CER overall, and per condition present in the manifest.
4. Hand-check three pairs, including one with an insertion.
5. Categorise 20 errors (homophone, named entity, number, truncation, reference
   error) and report counts.

**Evidence**

- `wer.py` with unit tests for four hand cases.
- A metrics table with clip counts per condition.
- An error table with 20 rows and categories.

**Pass conditions**

- Empty reference is handled explicitly, not with a crash or a silent zero.
- WER is not reported without the counts behind it.
- Normalisation rules are written down.

---

## LA5 - Counting logic with tests

**Time:** 4 hours. **Maps to:** VD08, P09.

**Input:** `projects/video-ai/data/video/` clips and `manifest.json` ground truth.

**Tasks**

1. Represent a counting line as a segment plus a normal.
2. Implement side tracking per object id and count a crossing only on a side change.
3. Write unit tests for: a single crossing, a double crossing, jitter across the
   line, an object that appears already past the line, and an object that never
   crosses.
4. Run on one clip and compare counts with the manifest ground truth per direction.
5. Report the absolute error and one failure case.

**Evidence**

- Five passing unit tests.
- A counts table: predicted, ground truth, absolute error, per direction.
- One frame sequence or description showing a missed or extra count.

**Pass conditions**

- Jitter does not produce repeated counts.
- Track loss and rebirth do not silently double count, or the limitation is stated.
- Ground truth comparison is per direction, not only total.

---

## LA6 - Permission matrix and attack tests

**Time:** 4 hours. **Maps to:** M15 material, P12.

**Input:** `data/agents/` corpus, CSV, and task files.

**Tasks**

1. Define two roles and a permission matrix in JSON: tool, resource pattern,
   approval required.
2. Implement a `check(role, tool, args)` function that denies by default.
3. Implement an approval gate for one write or send action, with denial and timeout.
4. Run six tests: allowed read, denied tool, denied path, approval granted, approval
   denied, injected instruction in a document.
5. Record the outcome of each test in a table with the control that produced it.

**Evidence**

- `policy.json` and the check function with tests.
- A six-row results table: test, expected, observed, control.
- An audit excerpt for the approved action.

**Pass conditions**

- An unlisted tool is denied for every role.
- A denied approval results in no side effect, proven by the audit log or state.
- The injection test result is reported even if the control failed.

---

## Self-scoring

Use the [course lab rubric](../assessments.md#lab-rubric):

| Criterion | Weight | Evidence in these tasks |
| --- | --- | --- |
| Technical correctness | 30% | Code runs, edge cases handled, tests pass |
| Evaluation and evidence | 25% | Metrics with counts, baselines, failure analysis |
| Reproducibility | 15% | Seeds, versions, rerun command |
| Data and ethics | 15% | Licence, privacy, limitations |
| Communication | 15% | Write-up states what the evidence supports |

A task with correct code and no evidence scores below one with imperfect code and a
complete, honest evidence trail.
