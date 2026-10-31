# F08 assessment

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**

F08 uses the course's standard module weights. There is no proctored exam. You
assess yourself against published criteria, keep the evidence, and decide whether
you are ready for F09.

| Component | Weight | Evidence |
| --- | --- | --- |
| Knowledge check | 20% | Answers to the eight questions below |
| Guided notebook | 30% | Executed notebook with outputs and notes |
| Independent lab | 40% | Valuation screen, model card, and report |
| Reflection | 10% | 200-300 word reflection |

## Part A - Knowledge check (20%)

Answer first, then open the answer to check. A correct answer in your own words
is worth more than a memorized sentence.

**1. What distinguishes a regression task from a classification task? Name the
target, output, and a typical metric for each.**

??? note "Answer"
    Regression predicts a numeric quantity, such as a sale price; its output is a
    number and MAE or RMSE is a typical metric. Classification predicts a discrete
    label, such as pass/fail; its output is a class or a probability plus a
    threshold, and accuracy, precision, recall, or F1 is typical. The distinction
    comes from the target and the decision, not from the algorithm: logistic
    regression is a classifier despite its name.

**2. The student classifier scores 0.728 accuracy. Why is the 0.512 majority
baseline essential to interpreting that number?**

??? note "Answer"
    The classes are nearly balanced (50.9% negative, 49.1% positive), so predicting
    the majority class already scores 0.512. The model improves accuracy by about
    0.216, or 21.6 percentage points. Without the baseline, 0.728 sounds strong;
    with it, the improvement is real but modest, and the confusion matrix shows
    that 21 of 61 positive cases are still missed.

**3. A model makes three predictions. Actual prices are 240,000, 300,000, and
360,000 USD; predictions are 260,000, 290,000, and 340,000 USD. Compute MAE and
RMSE.**

??? note "Answer"
    Errors (prediction minus actual) are +20,000, -10,000, and -20,000. Absolute
    errors are 20,000, 10,000, and 20,000, so MAE = 50,000 / 3 = **16,667 USD**.
    Squared errors are 400,000,000, 100,000,000, and 400,000,000; the mean is
    300,000,000, so RMSE = sqrt(300,000,000) = **17,321 USD**. RMSE exceeds MAE
    because the two 20,000-dollar errors are weighted more heavily.

**4. A classifier produces the confusion matrix `[[51, 13], [21, 40]]`, where rows
are actual and columns are predicted. Compute accuracy, precision, recall, and
F1.**

??? note "Answer"
    There are 125 rows: TN 51, FP 13, FN 21, TP 40. Accuracy = (51 + 40) / 125 =
    **0.728**. Precision = 40 / (40 + 13) = **0.755**. Recall = 40 / (40 + 21) =
    **0.656**. F1 = 2 x 0.755 x 0.656 / (0.755 + 0.656) = **0.702**. Precision is
    higher than recall because the model raises 13 false alarms but misses 21
    positives.

**5. The house model reports R-squared 0.829 on the test set. Explain what that
means and name one thing it does not tell you.**

??? note "Answer"
    The model explains about 82.9% of the variance of sale price in the test rows,
    leaving 17.1% unexplained. It does not tell you the size of a typical error in
    dollars (MAE is 21,708), whether errors are concentrated in some neighborhoods,
    whether the relationship is causal, or whether the model is good enough for a
    particular decision.

**6. Read this code. What is wrong, and how would you fix it?**

```python
scaler = StandardScaler().fit(X)
X_train_s = scaler.transform(X_train)
X_test_s = scaler.transform(X_test)
```

??? note "Answer"
    The scaler is fitted on `X`, which includes the test rows, so the training
    features are transformed with statistics computed partly from test data. This
    is preprocessing leakage and makes the test score optimistic and invalid. Fit
    on the training rows only: `scaler = StandardScaler().fit(X_train)`, then
    transform both sets. The same rule applies to encoders, imputers, and feature
    selectors.

**7. The standardized area coefficient is 46,020. A colleague says "each extra
square foot adds 46,020 dollars." Is that correct? Explain what the number means.**

??? note "Answer"
    No. The coefficient is in standardized units: a one-standard-deviation increase
    in area, holding the other features fixed, is associated with a 46,020-dollar
    higher prediction. In this table one SD of area is roughly 500 square feet, so
    the rough natural-unit effect is about 92 dollars per square foot. It is an
    association in this model, not a causal price per square foot.

**8. A tutoring program can afford false alarms but treats a missed likely-failing
student as four times more costly. Which metric and threshold direction do you
choose, and what do you report alongside it?**

??? note "Answer"
    Prioritize recall and lower the threshold so more students are flagged, then
    report precision and the expected cost at the chosen threshold so the false
    alarms are visible. Accuracy alone is the wrong summary because the two errors
    have different costs. State the cost ratio, choose the threshold on validation
    rows, and report the confusion matrix at that threshold.

**Self-score:** 2.5 points per question, 20 points total. Award full credit only
when the answer includes the mechanism, the arithmetic, or the diagnostic step,
not just the term.

## Part B - Guided notebook (30%)

| Criterion | Weight | Evidence |
| --- | --- | --- |
| Completeness | 10% | All six sections executed top to bottom; no failed or skipped required cell |
| Correctness | 10% | Assertions pass; metrics match the healthy-run table within tolerance |
| Interpretation | 10% | A short markdown note explaining the baseline improvement, the ridge result, and one limitation |

A notebook with saved outputs but no interpretation is incomplete. Under the
final cell, add three or four sentences stating the baseline-to-model improvement
for both tasks, why ridge and linear are nearly identical here, and one feature
the model omits.

## Part C - Independent lab (40%)

The lab is scored with the five-dimension rubric on the
[lab brief](lab.md#rubric): technical correctness 30, evaluation and diagnosis 25,
reproducibility 15, data and ethics 15, and communication 15. That score out of
100 becomes 40% of the module total.

Common reasons for losing marks:

- Reporting test metrics before the cutoff and model are frozen.
- A cutoff chosen by habit at 325,000 with no cost table.
- No latency measurement, or a measurement taken before warm-up.
- A model artifact over 2 MB, or a reload check that was never run.
- A model card that lists metrics but no out-of-scope use or fairness risk.
- Claiming the synthetic data represents a real housing market.

## Part D - Reflection (10%)

Write 200-300 words in `reflection.md`. Answer all three prompts:

1. Which number changed your interpretation most: the baseline, the ridge result,
   or the confusion matrix? What did it change?
2. Where could a coefficient or an aggregate metric mislead the fund's analyst,
   and what would you add to the report to prevent that?
3. What will you record in your next lab so that the latency measurement and the
   cutoff decision can be reproduced by someone else?

Reflection is not a summary of the steps. It is your reasoning about evidence,
trade-offs, and what you will change next time.

## Scoring worksheet

| Component | Maximum | Your score | Notes |
| --- | --- | --- | --- |
| Knowledge check | 20 | | 2.5 points per question |
| Guided notebook | 30 | | 10 completeness, 10 correctness, 10 interpretation |
| Independent lab | 40 | | Lab rubric out of 100, scaled to 40 |
| Reflection | 10 | | All three prompts, specific evidence |
| **Total** | **100** | | |

Use this scale for self-study:

| Score | Interpretation |
| --- | --- |
| 90-100 | Ready for F09; evidence is complete and reproducible |
| 75-89 | Ready, but fix the weakest rubric dimension first |
| 60-74 | Rerun the notebook and revise the lab analysis |
| Below 60 | Repeat the module; the baseline or leakage checks are probably missing |

These bands are for your own planning. They are not a university grade and do not
confer credit.

## Academic integrity and AI assistance

- You may use an AI assistant to explain an error, a metric, or a scikit-learn
  argument.
- You must run the notebook and the lab yourself and verify every number you
  report.
- If you use generated code, read it, test it, and disclose the assistance in your
  reflection: what you asked, what you used, and what you checked independently.
- Do not submit a model card or report that describes a run you did not perform.

The full policy is in [Academic integrity](../../course/assessments.md#academic-integrity)
and [How to study](../../course/how-to-study.md#academic-integrity-and-ai-assistants).

## Completion checklist

- [ ] I answered all eight knowledge questions before opening the answers.
- [ ] My notebook ran from a clean kernel and contains outputs.
- [ ] I can compute precision, recall, and F1 from a confusion matrix by hand.
- [ ] My lab compares against both baselines and meets the latency and size
      budgets.
- [ ] My cutoff was chosen on validation and the test set was scored once.
- [ ] My model card states intended use, out-of-scope use, and fairness risks.
- [ ] My reflection addresses all three prompts with specific evidence.
- [ ] I saved the package in my portfolio under `f08-house-prices/`.

**Next:** [F09 - Decision trees, random forests, and gradient boosting](../f09-tree-ensembles/index.md).
Read the [M02 plan](../../syllabus/level-1-foundations.md#m02) if you want the
module-level context.

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**
