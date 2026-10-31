# F10 assessment

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**

F10 uses the course's standard module weights. There is no proctored exam. You
assess yourself against published criteria, keep the evidence, and decide whether
you are ready for F11.

| Component | Weight | Evidence |
| --- | --- | --- |
| Knowledge check | 20% | Answers to the eight questions below |
| Guided notebook | 30% | Executed notebook with outputs, figure, and notes |
| Independent lab | 40% | Complexity sweeps, recommendation memo, and test result |
| Reflection | 10% | 200-300 word reflection |

## Part A - Knowledge check (20%)

Answer first, then open the answer to check.

**1. A target has a 0.212 positive rate. A model reports 0.920 accuracy. What is
the majority baseline, what is the improvement, and what does accuracy hide?**

??? note "Answer"
    The majority baseline is `max(0.212, 0.788)` = **0.788**, so the improvement is
    **0.132**, or 13.2 percentage points. Accuracy hides the error mix: the
    notebook's model misses 8 of 32 at-risk students and raises 4 false alarms.
    A model can improve accuracy by being conservative on the rare class, so report
    the confusion matrix, recall, precision, and the cost-weighted result.

**2. From the confusion matrix `[[114, 4], [8, 24]]`, compute accuracy, precision,
recall, and F1. Show the counts you use.**

??? note "Answer"
    TN = 114, FP = 4, FN = 8, TP = 24; total = 150. Accuracy = (114 + 24) / 150 =
    **0.920**. Precision = 24 / (24 + 4) = **0.857**. Recall = 24 / (24 + 8) =
    **0.750**. F1 = 2 x 0.857 x 0.750 / (0.857 + 0.750) = **0.800**. The model is
    better at ruling out risk than at finding every at-risk student.

**3. At threshold 0.3 the confusion matrix implies 3 false negatives and 9 false
positives; at 0.6 it implies 12 false negatives and 2 false positives. Compute
expected cost for (a) `cost_FN = 2`, `cost_FP = 1` and (b) `cost_FN = 1`,
`cost_FP = 2`. Which threshold wins in each case?**

??? note "Answer"
    (a) 0.3: `3 x 2 + 9 x 1 = 15`; 0.6: `12 x 2 + 2 x 1 = 26`. Threshold **0.3**
    wins. (b) 0.3: `3 x 1 + 9 x 2 = 21`; 0.6: `12 x 1 + 2 x 2 = 16`. Threshold
    **0.6** wins. The metrics are unchanged; the cost ratio reverses the decision.
    This is why the threshold is a business choice, not a property of the model.

**4. The model reports PR-AUC 0.892 with a 0.212 positive rate. What is the no-skill
PR-AUC, and why is PR-AUC often more informative than ROC-AUC here?**

??? note "Answer"
    The no-skill PR-AUC equals the positive rate, **0.212**, so 0.892 is a large
    gain over random ranking. ROC-AUC's no-skill value is 0.5, and 0.963 sounds
    close to perfect, but with rare positives the false-positive rate stays small
    even when precision is imperfect. PR-AUC focuses on the positive class and is
    more demanding.

**5. Read this code. What is wrong, and how do you fix it?**

```python
X_scaled = StandardScaler().fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.3, random_state=42
)
```

??? note "Answer"
    The scaler is fitted on all rows, including the rows that become the test set,
    before the split. The training features therefore depend on test-set means and
    standard deviations. This is preprocessing leakage and makes the test score
    optimistic. Split first, fit the scaler on `X_train`, then transform `X_train`
    and `X_test`. A `Pipeline` makes the correct order automatic inside
    cross-validation.

**6. Name three types of data leakage and one prevention for each.**

??? note "Answer"
    Any three: **target leakage** (a feature derived from the target, such as
    `final_score`), prevented by dropping post-outcome columns; **preprocessing
    leakage** (fitting a scaler or encoder on all rows), prevented by fitting inside
    a pipeline on training folds; **duplicate leakage** (the same row in train and
    test), prevented by deduplicating before the split; **temporal leakage** (a
    random split on time-ordered data), prevented by splitting by time;
    **group leakage** (multiple rows per person across splits), prevented with
    `GroupKFold` or a group-level split.

**7. A depth-15 tree reaches 1.000 training accuracy and 0.820 validation accuracy.
Diagnose the problem and name three actions.**

??? note "Answer"
    The tree is overfitting: it memorizes the training rows and does not generalize
    as well. The 0.180 gap is the evidence, not the perfect training score. Actions:
    reduce depth or choose the best validation depth (4 in the notebook); raise
    `min_samples_leaf` or prune; simplify the feature set; collect more data; use
    cross-validation to confirm the choice; and check for leakage if validation is
    also suspiciously high.

**8. Cross-validation reports PR-AUC 0.852 ± 0.059 with folds from 0.736 to 0.898.
Can you claim the model reaches 0.9? What should you report?**

??? note "Answer"
    No. The mean is 0.852, one fold is 0.736, and the standard deviation is 0.059,
    so 0.9 is within the observed variation but not supported as a stable estimate.
    Report the mean, the standard deviation, and the fold range, and note that the
    folds overlap so the spread is not a confidence interval. Use the mean and
    spread for model selection, then report a one-time test score. Claiming 0.9
    would overstate the evidence.

**Self-score:** 2.5 points per question, 20 points total. Full credit requires the
arithmetic or the mechanism, not just the term.

## Part B - Guided notebook (30%)

| Criterion | Weight | Evidence |
| --- | --- | --- |
| Completeness | 10% | All six sections executed top to bottom; the figure is saved |
| Correctness | 10% | Assertions pass; metrics and the leakage gap match the healthy-run table |
| Interpretation | 10% | A short note on the accuracy trap, the depth curve, and the leakage result |

Add three or four sentences under the final cell: why 0.920 accuracy is not enough,
where validation accuracy peaks, and why the 1.000 leakage score is not a better
model.

## Part C - Independent lab (40%)

The lab is scored with the five-dimension rubric on the
[lab brief](lab.md#rubric): technical correctness 30, evaluation and diagnosis 25,
reproducibility 15, data and ethics 15, and communication 15. That score out of
100 becomes 40% of the module total.

Common reasons for losing marks:

- Choosing the deepest tree because its training accuracy is highest.
- Comparing a tree and a forest on different splits or feature sets.
- Selecting the threshold on the test set.
- Reporting expected cost that does not reconcile with the confusion matrix.
- A memo that lists numbers without a recommendation.
- Ignoring the fairness risk of using neighborhood in a marketing model.

## Part D - Reflection (10%)

Write 200-300 words in `reflection.md`. Answer all three prompts:

1. Which evidence convinced you that the more complex model was worse: the
   training score, the validation gap, or the cost? Why?
2. How did the 6:1 cost ratio affect the threshold you recommended?
3. What will you do differently in your next project to keep model selection and
   final evaluation separate?

Reflection is not a summary of the steps. It is your reasoning about evidence,
trade-offs, and process.

## Scoring worksheet

| Component | Maximum | Your score | Notes |
| --- | --- | --- | --- |
| Knowledge check | 20 | | 2.5 points per question |
| Guided notebook | 30 | | 10 completeness, 10 correctness, 10 interpretation |
| Independent lab | 40 | | Lab rubric out of 100, scaled to 40 |
| Reflection | 10 | | All three prompts, specific evidence |
| **Total** | **100** | | |

| Score | Interpretation |
| --- | --- |
| 90-100 | Ready for F11; evidence is complete and reproducible |
| 75-89 | Ready, but fix the weakest rubric dimension first |
| 60-74 | Rerun the notebook and revise the sweep or memo |
| Below 60 | Repeat the module; the evaluation protocol or leakage check is missing |

These bands are for your own planning. They are not a university grade and do not
confer credit.

## Academic integrity and AI assistance

- You may use an AI assistant to explain a metric, a curve, or a scikit-learn
  argument.
- You must run the sweeps and verify every number and cost yourself.
- Disclose substantive assistance in your reflection: what you asked, what you
  used, and what you verified.
- Do not submit a memo that describes a sweep you did not run.

The full policy is in [Academic integrity](../../course/assessments.md#academic-integrity)
and [How to study](../../course/how-to-study.md#academic-integrity-and-ai-assistants).

## Completion checklist

- [ ] I answered all eight knowledge questions before opening the answers.
- [ ] My notebook ran from a clean kernel and saved the overfitting figure.
- [ ] I can compute precision, recall, F1, and expected cost from counts.
- [ ] My lab sweeps depth and leaf size under one protocol.
- [ ] My chosen model and threshold were selected on validation.
- [ ] The test set was scored once, and the flag is recorded.
- [ ] My memo recommends a model and rejects an alternative with evidence.
- [ ] My reflection addresses all three prompts with specific evidence.
- [ ] I saved the package in my portfolio under `f10-overfitting/`.

**Next:** [F11 - Neural network fundamentals](../f11-neural-networks/index.md).
Read the [M02 plan](../../syllabus/level-1-foundations.md#m02) for module-level
context.

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**
