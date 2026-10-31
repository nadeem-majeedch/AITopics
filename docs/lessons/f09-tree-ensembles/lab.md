# F09 lab - A cost-sensitive early-warning comparison

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)

| | |
| --- | --- |
| **Weight** | 40% of the F09 assessment |
| **Time** | About 3 hours |
| **Hardware** | CPU-only |
| **Starter file** | `labs/foundations/f09_classifier_comparison.md` in the repository |
| **Prerequisite** | A completed run of the [guided notebook](notebook.md) |

## The scenario

**Riverside Community College** runs a 12-week certification prep course. In the
past, about half of the learners passed. Advisors can contact a learner at week 4
with a 15-minute call and a study plan, but they cannot contact everyone.

The college has budgeted **30 staff hours per cohort**, which is about 120 calls
for 500 learners. A learner who fails without an early call needs about **4 hours**
of remedial tutoring later. A call to a learner who would have passed anyway costs
about **0.25 hours** of staff time.

Your job is to compare classifiers, choose one, and recommend a contact rule. The
recommendation must be written so that an academic director who does not read code
can follow the reasoning and challenge the assumptions.

This is not the notebook again. The notebook compares models on accuracy and
cross-validation. This lab adds a prediction-time constraint, unequal error costs,
a capacity limit, an explainability requirement, and a written justification.

## Why it matters

Metric choice is a decision, not a technicality. A model with the best accuracy
can be the wrong model when one error costs 16 times the other. A model with the
best recall can be useless when the program can only contact 120 people.

The lab also forces you to defend a model choice in prose. In real projects, the
person who approves the intervention rarely reads your notebook. They read the
memo.

## Constraints

| Constraint | Value |
| --- | --- |
| Data | `datasets/foundations/generated/student_performance.csv`, 500 rows |
| Label | `at_risk = 1 - passed` (1 = did not pass) |
| Prediction time | Week 4; only `study_hours`, `attendance`, `prior_score`, `sleep_hours`, `tutoring`, `course` are available |
| Forbidden features | `final_score`, `passed`, and `at_risk`; all are outcome information |
| Split | 60% train, 20% validation, 20% test, stratified, fixed seed |
| Missed failing learner | 4.0 staff hours |
| Unnecessary call | 0.25 staff hours |
| Capacity | At most 120 flags per 500 learners (24%) |
| Explainability | An advisor must be able to explain a flag using the model's inputs |
| Metric justification | 600-900 words, with arithmetic and uncertainty |

Generate the CSV with `python scripts/make_foundation_data.py` if it is absent,
and record the SHA-256 from `datasets/foundations/generated/manifest.json`. The
[dataset card](../../technical/foundation-assets.md#foundation-datasets) documents the CC0 license
and the limitation that this table is not a measurement of any real course.

## Required steps

### Step 1 - Provenance and label

Load the CSV. Assert 500 rows and 8 columns. Record the seed, hash, Python
version, and scikit-learn version. Confirm the at-risk rate is close to 0.51 (the
pass rate is close to 0.49).

Create `at_risk = 1 - passed`, so the positive class is the learner who needs
support. Drop `final_score` and `passed` before building the feature matrix, and
state in the memo why keeping `final_score` would be target leakage.

**Validation check 1 - forbidden columns.** Assert that `final_score`, `passed`,
and `at_risk` do not appear in `X.columns`. Save the assertion output in the
notebook.

### Step 2 - Split and freeze the test set

Split 60/20/20 with `stratify=y` and a fixed `random_state`. Print the row counts
and the positive rate per split. Do not touch the test rows until Step 7.

### Step 3 - Baselines with costs

Compute two decision baselines on the validation rows:

- **Flag nobody:** zero false positives, and every failing learner is a false
  negative.
- **Flag everybody:** every failing learner is caught, and every passing learner
  is a false positive, which also violates the capacity limit.

Express each as expected staff hours per 1,000 learners using

```text
expected hours = 4.0 * false negatives + 0.25 * false positives
```

These two numbers are the range your model must improve on.

### Step 4 - Compare candidates under one protocol

Fit and compare at least four candidates:

1. logistic regression in a pipeline with scaling and one-hot encoding;
2. a decision tree with `max_depth=3`;
3. a random forest with at least 200 trees;
4. histogram gradient boosting.

Use the same repeated stratified cross-validation on the training rows, for
example 5 folds x 3 repeats, and the same scoring. Report accuracy, recall,
precision, F1, and PR-AUC as mean and standard deviation. Include the baseline
majority rate in the table.

**Validation check 2 - fold integrity.** Assert that every model was scored with
the same `RepeatedStratifiedKFold` object and the same seed, and that the
preprocessing lives inside each pipeline.

### Step 5 - Choose a metric and a shortlist

Write down the metric you will use to rank models **before** looking at the test
set. Defend it with the 16:1 cost ratio and the 24% capacity limit. A defensible
approach is to rank with PR-AUC, then compare the top models by expected cost at
their chosen thresholds, with recall and precision reported alongside. Accuracy
alone is not defensible here.

Keep the top two models for threshold analysis. Explain why you dropped the
others.

### Step 6 - Threshold and capacity analysis

On the validation rows, sweep thresholds from 0.05 to 0.95 in steps of 0.05. For
each threshold and each shortlisted model, compute:

- the flag rate, which must stay at or below 24%;
- the confusion matrix;
- precision and recall;
- expected staff hours per 1,000 learners.

Choose the model and threshold with the lowest validation cost inside the capacity
limit. If the best threshold flags more than 24%, move it up until the limit is
met and report the cost at that point.

**Validation check 3 - cost arithmetic.** Recompute the expected hours from your
chosen confusion matrix by hand or in a separate cell. It must match the reported
number. Check that you did not swap false negatives and false positives.

### Step 7 - Test once

Freeze the model, preprocessing, and threshold. Score the 100 test rows once.
Report the confusion matrix, precision, recall, F1, PR-AUC, flag rate, and expected
hours per 1,000 learners. Compare with the validation result and with both
baselines. Report a worse result honestly; do not retune and re-score.

**Validation check 4 - test discipline.** Record a flag such as
`"test_scored": true` with a timestamp in `metrics.json`, and state in the memo
that the test set was used once.

### Step 8 - Error analysis

Inspect at least five false negatives and five false positives. Describe their
feature profiles in plain language: attendance, study hours, prior score. Do not
use `final_score` to explain the errors; it is unavailable at prediction time.
State one pattern you trust and one pattern that may be noise given 100 test rows.

### Step 9 - Write the decision memo

Use the headings below. The memo is the main deliverable. It must contain the
comparison table, the cost calculation, the chosen threshold, the capacity check,
the error analysis, and an explicit recommendation with a confidence statement.

## Deliverables

```text
f09-classifier-comparison/
  README.md
  f09_classifier_comparison.ipynb
  outputs/
    model_comparison.csv      # CV mean and std per model and metric
    metrics.json              # validation and test metrics, threshold, costs, hash
  decision_memo.md
  reflection.md
```

Do not commit the generated CSV, the virtual environment, or `outputs/`. Copy the
files into your submission folder outside the repository.

## Report template (decision memo)

```markdown
# Riverside early-warning decision memo

## 1. Recommendation
The model, threshold, expected cost, and flag rate, in five sentences or fewer.

## 2. Decision context
Who is contacted, when, at what cost, and with what capacity.

## 3. Data and prediction time
Rows, split sizes, seed, SHA-256, available features, and the leakage exclusion.

## 4. Candidate models and protocol
The four models, the repeated CV folds, and the metrics table.

## 5. Metric justification
Why this metric follows from the 16:1 cost ratio and the 24% capacity limit.

## 6. Threshold and cost analysis
The sweep table, the chosen threshold, and the expected hours per 1,000 learners.

## 7. Test result
One-time test metrics, confusion matrix, and a comparison with validation.

## 8. Error analysis
False negatives, false positives, and which patterns may be noise.

## 9. Risks and limitations
Synthetic data, small test set, missing context, fairness, and explainability.

## 10. What would change my recommendation
The evidence or cost change that would reverse the decision.
```

## Rubric

| Dimension | Weight | Excellent | Developing |
| --- | --- | --- | --- |
| Technical correctness | 30 | Four models run under one protocol; pipelines are fold-safe; costs and capacity are computed correctly | Models run but protocols differ or cost arithmetic is wrong |
| Evaluation and diagnosis | 25 | Metric choice is justified before test; threshold chosen on validation; error analysis separates signal from noise | Metrics listed without justification; threshold chosen by habit |
| Reproducibility | 15 | Seed, hash, folds, versions, and commands reproduce the table and the test score | Missing key settings; the test score cannot be rebuilt |
| Data and ethics | 15 | Leakage excluded, synthetic provenance stated, fairness and intervention risks discussed | Weak limitations or an implied disciplinary use |
| Communication | 15 | Memo is decision-first, precise, and readable by a non-programmer; uncertainty is explicit | Memo is a notebook walkthrough with no recommendation |

A component with no evidence scores zero.

## Privacy and safety constraints

- The table is synthetic. Do not add real student records, names, IDs, or grades.
- Do not frame the model as a gatekeeper. It prioritizes **support**, not
  punishment, admission, or grading.
- If you discuss real deployment, name the legal and policy constraints that would
  apply to student data in your jurisdiction, such as consent, retention, and
  access rules.
- Do not use `final_score` or any end-of-term variable as a feature, even if it
  raises accuracy. That is the leakage this lab is designed to catch.
- Do not claim that the model improves pass rates. The lab evaluates prediction,
  not the effect of the intervention.
- Do not commit data files, credentials, or absolute local paths.

## Self-check before submission

- [ ] The hash, seed, split sizes, and package versions are recorded.
- [ ] No forbidden column is in the feature matrix.
- [ ] All models used the same folds and the same preprocessing rules.
- [ ] The metric was chosen and written down before the test score was seen.
- [ ] The threshold respects the 24% capacity limit.
- [ ] The expected cost reconciles with the confusion matrix.
- [ ] The test set was scored once, and the flag is recorded.
- [ ] The memo contains all ten headings and a clear recommendation.
- [ ] The error analysis does not use `final_score`.
- [ ] No personal data or secrets are in the submission.

Next: use the [assessment page](assessment.md) to score your evidence and write
the reflection.

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)
