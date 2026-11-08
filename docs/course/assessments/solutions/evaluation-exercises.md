# Evaluation exercises - worked answers

```markdown
**Assessments:** [Overview](../index.md) · [Solutions](index.md) · [Evaluation exercises](../evaluation-exercises.md)
```

All values below were computed from the definitions, not estimated. Intermediate steps
are shown so you can find an arithmetic slip.

---

## EE1 - Confusion matrix to metrics

Counts: TP = 15, FN = 5, FP = 10, TN = 40. Total = 70, positives = 20, negatives = 50.

| Metric | Working | Value |
| --- | --- | --- |
| Accuracy | (15 + 40) / 70 | 0.7857 |
| Precision | 15 / (15 + 10) | 0.6000 |
| Recall (sensitivity) | 15 / (15 + 5) | 0.7500 |
| F1 | 2 x 15 / (2 x 15 + 10 + 5) | 0.6667 |
| Specificity | 40 / (40 + 10) | 0.8000 |

**Summary number:** recall (0.75), because the stated cost is missing churners. It hides
that one in four predicted positives is wrong, so the retention team reviews 25 contacts
to reach 15 churners, and it hides the calibration of the scores.

**Strong answer:** also notes that recall alone can be gamed by predicting everything
positive, so recall should be reported with precision or with the review volume.

---

## EE2 - Average precision by hand

| Rank | Score | Match | TP | FP | Precision | Recall |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.90 | yes | 1 | 0 | 1.0000 | 0.3333 |
| 2 | 0.80 | no | 1 | 1 | 0.5000 | 0.3333 |
| 3 | 0.70 | yes | 2 | 1 | 0.6667 | 0.6667 |
| 4 | 0.60 | no | 2 | 2 | 0.5000 | 0.6667 |
| 5 | 0.50 | yes | 3 | 2 | 0.6000 | 1.0000 |

AP with the all-point rule, summing precision at each change in recall times the recall
increment:

```
(1/3) x 1.0000 + (1/3) x 0.6667 + (1/3) x 0.6000 = 0.3333 + 0.2222 + 0.2000 = 0.7556
```

**If the third detection were a false positive:** matches `[1, 0, 0, 0, 1]`, precision
`[1.0, 0.5, 0.3333, 0.25, 0.4]`, recall `[1/3, 1/3, 1/3, 1/3, 2/3]`. Only two recall
changes matter: `(1/3) x 1.0 + (1/3) x 0.4 = 0.4667`. A single ranking error costs about
0.29 AP here, which is why AP is sensitive to early false positives.

---

## EE3 - Word error rate with counts

| # | Ref length | S | D | I | WER |
| --- | --- | --- | --- | --- | --- |
| 1 | 6 | 1 (sat -> is) | 1 (the) | 0 | 2/6 = 0.3333 |
| 2 | 7 | 2 (two -> 2, seven -> 7) | 0 | 0 | 2/7 = 0.2857 |
| 3 | 4 | 0 | 0 | 1 (please) | 1/4 = 0.2500 |

Mean WER = (0.3333 + 0.2857 + 0.2500) / 3 = **0.2897** (0.29).

Pair 1 has the highest WER. Intuition agrees that it is the worst transcript: it loses a
content word ("the mat" becomes "mat") and substitutes a verb, changing the meaning.
Pair 2's errors are formatting: "two" and "seven" are semantically correct as digits, so
WER overstates the damage unless the normalisation converts digits to words. Pair 3's
insertion adds politeness and barely changes meaning. **Lesson:** WER weights all word
errors equally; a normalisation rule and an error taxonomy are part of the metric, not an
afterthought.

---

## EE4 - Expected calibration error

ECE is the weighted mean of |confidence - accuracy| per bin:

```
(50 x |0.60 - 0.50| + 30 x |0.80 - 0.70| + 20 x |0.95 - 0.90|) / 100
= (50 x 0.10 + 30 x 0.10 + 20 x 0.05) / 100
= (5 + 3 + 1) / 100 = 0.09
```

The model is **over-confident**: in every bin the observed accuracy is below the mean
confidence. Before showing probabilities to a reviewer, fit temperature scaling on a
validation set (never on test), recompute the table, and report ECE before and after.
If the model stays over-confident, consider abstention rather than displaying a number
that overstates certainty.

**Caveat a strong answer adds:** 100 items across three bins is a small calibration
sample; the bin with 20 items has a wide uncertainty, and ECE is sensitive to binning.

---

## EE5 - Population stability index

```
PSI = (0.30 - 0.50) x ln(0.30/0.50)
    + (0.40 - 0.30) x ln(0.40/0.30)
    + (0.30 - 0.20) x ln(0.30/0.20)
    = (-0.20 x -0.5108) + (0.10 x 0.2877) + (0.10 x 0.4055)
    = 0.1022 + 0.0288 + 0.0405 = 0.1715
```

PSI = **0.17**, which is "moderate" by the common rule of thumb (0.1-0.25). It says the
population moved: the low bin lost 20 points of share, and the high bin gained 10.

**Limitations:** PSI depends on the binning, has no direction (a shift up and a shift
down can look similar if bins are coarse), is computed on one feature at a time, and says
nothing about whether accuracy changed. It is an early warning, not a diagnosis. A strong
answer pairs it with a per-feature contribution and a label-based metric when labels
arrive.

---

## EE6 - Retrieval ranking metrics

Recall@3: the gold document appears in the top three for queries 1, 2, 4, and 5; query 3
has gold `d3`, which is not in `d2, d5, d6`. So 4/5 = **0.80**.

Reciprocal ranks: 1/3 (rank 3), 1/2 (rank 2), 0 (not found), 1/3 (rank 3), 1/2 (rank 2).
MRR = (0.3333 + 0.5 + 0 + 0.3333 + 0.5) / 5 = 1.6667 / 5 = **0.3333**.

Recall@3 can be high while MRR is low because recall only asks whether the gold document
is somewhere in the list; MRR penalises putting it third. For a user who reads only the
first result, MRR (or precision@1) reflects the experience; recall@3 describes whether
the system could support a reader who scans. Report both, and say which matches the
interface.

---

## EE7 - Inter-annotator agreement

Observed agreement: (40 + 45) / 100 = **0.85**.

Expected agreement by chance: A says relevant 50 times, B says relevant 45 times, so
`pe = (50/100)(45/100) + (50/100)(55/100) = 0.225 + 0.275 = 0.50`.

Cohen's kappa: `(0.85 - 0.50) / (1 - 0.50) = 0.35 / 0.50 =` **0.70**.

**Interpretation:** 85% agreement looks high, but half of it is expected from the
marginals alone, so kappa is 0.70 - substantial but not near-perfect. Kappa adds the
correction for chance, which matters when one label dominates: two annotators who both
say "not relevant" 90% of the time will agree 82% by chance while agreeing on almost
nothing informative. A strong answer notes that kappa also depends on prevalence, and
that per-class agreement or a confusion matrix between annotators is more diagnostic.
