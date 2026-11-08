# Model evaluation exercises

```markdown
**Assessments:** [Overview](index.md) · **Evaluation exercises** · [Solutions](solutions/evaluation-exercises.md)
```

Seven hand-computable exercises. Use a calculator or a short script, but write the
intermediate steps: the values matter less than whether you can explain them. Answers
with working are in
[solutions/evaluation-exercises.md](solutions/evaluation-exercises.md).

**Marking:** 4 = correct with working and interpretation; 3 = correct value;
2 = method right, arithmetic wrong; 1 = no usable method.

---

## EE1 - Confusion matrix to metrics

A binary classifier produced this test-set confusion matrix (positive = "will churn"):

| | Predicted positive | Predicted negative |
| --- | --- | --- |
| **Actual positive** | 15 | 5 |
| **Actual negative** | 10 | 40 |

Compute accuracy, precision, recall, F1, and specificity. Then answer: the team cares
most about not missing churners. Which single number would you put in the summary, and
what does it hide?

---

## EE2 - Average precision by hand

Three ground-truth objects. Five detections, sorted by score:

| Rank | Score | Matches a ground-truth box? |
| --- | --- | --- |
| 1 | 0.90 | yes |
| 2 | 0.80 | no |
| 3 | 0.70 | yes |
| 4 | 0.60 | no |
| 5 | 0.50 | yes |

Compute precision and recall after each detection, then AP using the all-point rule
(sum of precision at each change in recall). What would AP be if the third detection
were a false positive instead?

---

## EE3 - Word error rate with counts

For each pair, compute substitutions, deletions, insertions, and WER against the
reference word count. Then give the corpus WER as the mean of the three.

| # | Reference | Hypothesis |
| --- | --- | --- |
| 1 | the cat sat on the mat | the cat is on mat |
| 2 | book a table for two at seven | book a table for 2 at 7 |
| 3 | i need a refund | i need a refund please |

Which pair has the highest WER, and does that match your intuition about which
transcript is "worst"?

---

## EE4 - Expected calibration error

Three confidence bins from a validation set:

| Bin | Mean confidence | Observed accuracy | Items |
| --- | --- | --- | --- |
| 0.55-0.65 | 0.60 | 0.50 | 50 |
| 0.75-0.85 | 0.80 | 0.70 | 30 |
| 0.90-1.00 | 0.95 | 0.90 | 20 |

Compute ECE. Is the model over- or under-confident? What would you do before showing
these probabilities to a human reviewer?

---

## EE5 - Population stability index

Expected and actual proportions across three bins:

| Bin | Expected | Actual |
| --- | --- | --- |
| low | 0.50 | 0.30 |
| mid | 0.30 | 0.40 |
| high | 0.20 | 0.30 |

Compute PSI = Σ (actual − expected) × ln(actual / expected). Interpret the value
using the common rule of thumb (< 0.1 stable, 0.1-0.25 moderate, > 0.25 significant),
and state one limitation of PSI as a drift signal.

---

## EE6 - Retrieval ranking metrics

Five queries, each with a ranked list of three documents and one gold document:

| Query | Ranked list | Gold |
| --- | --- | --- |
| 1 | d1, d2, d3 | d3 |
| 2 | d9, d1, d4 | d1 |
| 3 | d2, d5, d6 | d3 |
| 4 | d7, d8, d9 | d9 |
| 5 | d3, d1, d2 | d1 |

Compute recall@3 and MRR. Then explain why recall@3 can be 0.8 while MRR is 0.33, and
which one better reflects "the user reads the first result only".

---

## EE7 - Inter-annotator agreement

Two annotators label 100 items as relevant or not:

| | B: relevant | B: not relevant |
| --- | --- | --- |
| **A: relevant** | 40 | 10 |
| **A: not relevant** | 5 | 45 |

Compute observed agreement and Cohen's kappa. Then answer: is 85% agreement good
enough to trust the labels, and what does kappa add that the percentage does not?
