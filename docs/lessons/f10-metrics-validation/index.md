# F10 - Metrics, overfitting, underfitting, data leakage, and cross-validation {#f10}

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Level** | 1 - Machine learning foundations (M02) |
| **Study time** | 10 hours: 3 h theory, 3 h guided notebook, 3 h lab, 1 h assessment |
| **Hardware** | CPU-only; the notebook writes one small figure |
| **Prerequisites** | F08 (metrics and baselines) and F09 (trees, ensembles, cross-validation) |
| **You will produce** | An executed notebook, an overfitting investigation with a model recommendation memo, a knowledge check, and a short reflection |

## Why this module exists

A model that predicts which students are at risk of failing reports **92%
accuracy**. Only **21.2%** of students are at risk, so a rule that predicts "never
at risk" already scores **78.8%**. The 92% model catches 24 of 32 at-risk students
and misses 8. That is useful, but the headline number hides the misses.

The same notebook then adds the end-of-term `final_score` as a feature and reaches
**100% accuracy**. The model is useless: the final score is unavailable when the
prediction must be made. A depth-15 tree reaches **100% training accuracy** and
**82% validation accuracy**, another sign that a number can be technically correct
and practically misleading.

This module makes evaluation the subject. You will compute metrics from counts,
turn error costs into a threshold, read an overfitting curve, run cross-validation,
and recognize the leakage that produces perfect but worthless results.

## Learning objectives

By the end of this module, you can:

1. Explain why accuracy misleads on an imbalanced target and compute the majority
   baseline from the positive rate.
2. Compute accuracy, precision, recall, and F1 from a confusion matrix and explain
   which error each metric emphasizes.
3. Translate false-negative and false-positive costs into expected cost, and choose
   a threshold from that calculation.
4. Interpret ROC-AUC and PR-AUC, including their no-skill values, and explain why
   PR-AUC is more informative when positives are rare.
5. Diagnose overfitting and underfitting from training and validation scores across
   a complexity sweep, and select complexity on validation data.
6. Explain stratified k-fold cross-validation, report mean and standard deviation,
   and keep model selection separate from the final test.
7. Identify target, preprocessing, duplicate, temporal, and group leakage, and
   prevent each with a split or pipeline rule.

## Before you start

| Requirement | Why it matters |
| --- | --- |
| F08: confusion matrix and precision/recall | This module derives and interprets them under imbalance |
| F09: trees, forests, and CV | The complexity sweep uses decision trees; CV is extended here |
| pandas and scikit-learn basics | You will reshape probabilities, labels, and metric outputs |
| matplotlib | The notebook saves an overfitting curve; the `Agg` backend is set for you |
| About 1 GB free disk | The table is 500 rows; the figure is small |

The notebook generates its student table in code with seed 42. The repository
generator and dataset card document the same columns:

- [Dataset card](../../technical/foundation-assets.md#foundation-datasets) - provenance, license,
  and the warning that the table is not a measurement of any real course.
- [Data generator](../../technical/foundation-assets.md#data-generator) - the script that
  writes `student_performance.csv` and a SHA-256 manifest.

The notebook derives `at_risk` from `final_score < 70`. In the leakage section it
then uses `final_score` as a feature. That contradiction is deliberate: it shows
how a target-derived column can produce a perfect score.

## The concepts you need

### 1. Accuracy and the base rate

The **base rate** (or prevalence) is the share of positive cases. If 21.2% of rows
are positive, a constant "negative" prediction is correct 78.8% of the time. That
is the **majority baseline**.

| Quantity | Value |
| --- | --- |
| Rows | 500 |
| Positive rate (`at_risk`) | 0.212 |
| Majority baseline accuracy | 0.788 |
| Notebook model accuracy | 0.920 |
| Absolute improvement | 0.132 |
| At-risk students in the 150-row test set | 32 |
| At-risk students caught (recall 0.750) | 24 |
| At-risk students missed | 8 |

Accuracy treats a missed at-risk student and a false alarm as one error each. When
positives are rare, a model can raise accuracy by being conservative and still miss
most of the cases you care about. Report the baseline, the confusion matrix, and a
metric that reflects the decision.

**Balanced accuracy** is the average of recall on the positive class and recall on
the negative class. It gives both classes equal weight, which is useful when the
base rate is skewed.

### 2. The confusion matrix and four metrics

A **confusion matrix** counts the four outcomes of a binary decision:

|  | Predicted negative | Predicted positive |
| --- | --- | --- |
| **Actual negative** | True negative (TN) | False positive (FP) |
| **Actual positive** | False negative (FN) | True positive (TP) |

The notebook's test result is `[[114, 4], [8, 24]]`:

- TN = 114, FP = 4, FN = 8, TP = 24, total = 150.

| Metric | Formula | Value | What it emphasizes |
| --- | --- | --- | --- |
| Accuracy | `(TP + TN) / total` | 138 / 150 = 0.920 | Overall correctness |
| Precision | `TP / (TP + FP)` | 24 / 28 = 0.857 | Trust in a positive flag |
| Recall | `TP / (TP + FN)` | 24 / 32 = 0.750 | Coverage of actual positives |
| F1 | `2PR / (P + R)` | 0.800 | Balance of precision and recall |
| Specificity | `TN / (TN + FP)` | 114 / 118 = 0.966 | Coverage of negatives |

Read the matrix before the aggregate metrics. Here the model is strong at ruling
out risk and weaker at finding every at-risk student: 8 of 32 are missed. Whether
that is acceptable depends on what happens to a missed student.

### 3. Thresholds and expected cost

A classifier outputs a probability. The **threshold** turns it into a label. Lower
the threshold to catch more positives; raise it to reduce false alarms.

The notebook's threshold table on the test set:

| Threshold | Precision | Recall | F1 | Implied TP | Implied FP | Implied FN |
| --- | --- | --- | --- | --- | --- | --- |
| 0.3 | 0.763 | 0.906 | 0.829 | 29 | 9 | 3 |
| 0.4 | 0.788 | 0.812 | 0.800 | 26 | 7 | 6 |
| 0.5 | 0.857 | 0.750 | 0.800 | 24 | 4 | 8 |
| 0.6 | 0.909 | 0.625 | 0.741 | 20 | 2 | 12 |

The counts are reconstructed from the rounded precision and recall with 32 actual
positives; your own run may differ by one row.

**Expected cost** converts the matrix into the unit that matters:

```text
expected cost = cost_FN * FN + cost_FP * FP
```

```python
pred = (probability >= 0.3).astype(int)
fn = ((y_test == 1) & (pred == 0)).sum()
fp = ((y_test == 0) & (pred == 1)).sum()
expected_cost = 2 * fn + 1 * fp
```

Suppose a missed at-risk student costs twice a false alarm (`cost_FN = 2`,
`cost_FP = 1`):

| Threshold | FN cost | FP cost | Total |
| --- | --- | --- | --- |
| 0.3 | 3 x 2 = 6 | 9 x 1 = 9 | **15** |
| 0.4 | 6 x 2 = 12 | 7 x 1 = 7 | 19 |
| 0.5 | 8 x 2 = 16 | 4 x 1 = 4 | 20 |
| 0.6 | 12 x 2 = 24 | 2 x 1 = 2 | 26 |

Under this cost ratio, 0.3 is best even though its F1 is only slightly higher and
its precision is lower. Now reverse the ratio (`cost_FN = 1`, `cost_FP = 2`):

| Threshold | Total |
| --- | --- |
| 0.3 | 3 + 18 = 21 |
| 0.4 | 6 + 14 = 20 |
| 0.5 | 8 + 8 = 16 |
| 0.6 | 12 + 4 = 16 |

The best region moves up to 0.5-0.6. There is no universally correct threshold.
Document the cost assumption, choose on validation data, and report the test result
once.

### 4. ROC-AUC and PR-AUC

Threshold-free metrics summarize ranking quality across all possible thresholds.

- The **ROC curve** plots true positive rate (recall) against false positive rate
  (`FP / (FP + TN)`). **ROC-AUC** is the area under it; 0.5 is random ranking.
- The **precision-recall curve** plots precision against recall. **PR-AUC** (average
  precision) summarizes it; the no-skill value equals the positive rate, not 0.5.

The notebook reports **ROC-AUC 0.963** and **PR-AUC 0.892** with a positive rate of
0.212. The PR-AUC is the more demanding summary here: a random ranker would score
about 0.212, while the model scores 0.892. ROC-AUC looks closer to perfect because
the large negative class makes the false-positive rate small even when there are
several false positives.

| Metric | Range | No-skill value | Best used when |
| --- | --- | --- | --- |
| ROC-AUC | 0 to 1 | 0.5 | Classes are roughly balanced, or you care about both classes |
| PR-AUC | 0 to 1 | Positive rate | Positives are rare and false positives matter |
| Accuracy | 0 to 1 | Majority rate | Classes are balanced and errors cost the same |

Both are ranking metrics. They do not choose a threshold, and they do not guarantee
that predicted probabilities are **calibrated** (that a 0.8 score really means
about 80% risk). Calibration is a separate check.

### 5. Overfitting and underfitting

**Underfitting** means the model is too simple: training and validation scores are
both low. **Overfitting** means the model fits noise: training performance keeps
rising while validation performance stalls or falls. The gap between the two is the
practical signal.

The notebook sweeps decision-tree depth from 1 to 15:

| Observation | Value |
| --- | --- |
| Best validation depth | 4 |
| Training accuracy at depth 15 | 1.000 |
| Validation accuracy at depth 15 | 0.820 |
| Train-validation gap at depth 15 | 0.180 |

Training accuracy rises monotonically with depth; validation accuracy peaks at
depth 4 and does not improve on that peak. The best depth is chosen on validation
data. Perfect training accuracy is evidence of capacity, not of quality.

Ways to control overfitting:

- reduce complexity (shallower trees, fewer features, stronger regularization);
- collect more data or augment it;
- use early stopping for iterative models;
- average many models, as a forest does;
- simplify the feature set and remove leaky or noisy columns.

**Learning curves** plot training and validation scores against training-set size.
A large persistent gap suggests more data may help; two low curves that meet
suggest underfitting.

### 6. Cross-validation

**k-fold cross-validation** divides the data into `k` folds. For each fold, train
on the other `k-1` and score on the held-out fold. **Stratified** k-fold preserves
the class ratio in each fold, which matters when positives are rare.

The notebook uses stratified 5-fold CV and reports PR-AUC per fold:

```text
fold scores: 0.736, 0.872, 0.898, 0.868, 0.885
mean: 0.852    standard deviation: 0.059
```

The standard deviation describes fold-to-fold variation, not a 95% confidence
interval. The standard error of the mean is roughly `0.059 / sqrt(5) = 0.026`, but
folds are not independent because their training sets overlap. Report the mean and
spread, and avoid claiming a difference smaller than the variation.

CV is for **model selection**: choosing features, hyperparameters, or a model
family. The final **test** set is for one honest estimate after all choices are
fixed. If you use CV to tune and then report the best CV score as your final
result, you have optimized on the evaluation and the number is optimistic. **Nested
CV** separates tuning (inner folds) from estimation (outer folds) when you need a
single cross-validated estimate.

For grouped data (for example, several rows per student), use `GroupKFold` so the
same group never appears in train and validation. For time-ordered data, use a
forward-chaining split; random folds leak the future into the past.

### 7. Data leakage

**Data leakage** is any information in training that would not be available at
prediction time, or that lets the model see the evaluation rows. It produces
scores that do not survive deployment.

| Type | Example | Prevention |
| --- | --- | --- |
| Target leakage | Using `final_score` to predict `at_risk` | Drop columns derived from the target or created after the prediction time |
| Preprocessing leakage | Fitting a scaler or encoder on all rows before splitting | Fit inside a pipeline, on training folds only |
| Duplicate leakage | The same row or near-duplicate appears in train and test | Deduplicate before splitting; group related rows |
| Temporal leakage | A random split on time-ordered data | Split by time; train on the past, test on the future |
| Group leakage | Multiple rows per customer or student across splits | Use `GroupKFold` or split by group |

The notebook's demonstration is stark:

| Feature set | Test accuracy |
| --- | --- |
| With `final_score` | 1.000 |
| Without `final_score` | 0.860 |

The first model is not better. It is answering a question that will not exist when
the prediction is needed. Treat a suspiciously perfect score as a leakage alarm,
not a triumph.

## Guided walkthrough

The [guided notebook](notebook.md) is the evidence for this chapter. It runs
quickly on a CPU and has six sections. The quoted numbers come from the verified
Windows 11 CPU run with Python 3.12.10; no GPU or Colab run was used.

1. **An imbalanced target.** Builds `at_risk` from `final_score < 70`, reports a
   0.212 positive rate and a 0.788 majority baseline.
2. **Confusion matrix and threshold-dependent metrics.** Splits 70/30, fits
   logistic regression, and reports the matrix `[[114, 4], [8, 24]]` plus accuracy,
   precision, recall, F1, ROC-AUC, and PR-AUC.
3. **Threshold selection.** Sweeps 0.3, 0.4, 0.5, and 0.6 and prints precision,
   recall, and F1 for each.
4. **Cross-validation.** Reports five PR-AUC fold scores with mean 0.852 and
   standard deviation 0.059.
5. **Overfitting.** Sweeps tree depth 1-15, saves
   `outputs/f10_overfitting_curve.png`, and prints the best validation depth (4) and
   the depth-15 train/validation scores.
6. **Target leakage.** Adds `final_score`, reaches 1.000 test accuracy, removes it,
   and reports 0.860.

Two methodological notes:

- The threshold table is computed on the same test rows used for the headline
  metrics. That is a teaching shortcut. In the lab, choose the threshold on
  validation rows and score test once.
- The depth sweep takes a fresh split of the full table with the same seed, so its
  validation rows are the same rows as the earlier test set. Treat the curve as a
  demonstration, not as a
  clean model-selection protocol.

## Practical exercise

This exercise is separate from the independent lab. It takes about 45 minutes.

1. **Reconstruct the threshold economics.** From the threshold table, derive the
   implied TP, FP, and FN counts at 0.3 and 0.6 using 32 actual positives. Compute
   expected cost with `cost_FN = 2` and `cost_FP = 1`. Expected observation: 15 at
   0.3 versus 26 at 0.6, so the lower threshold wins under this ratio.
2. **Reverse the costs.** Repeat with `cost_FN = 1` and `cost_FP = 2`. Expected
   observation: 21 at 0.3 versus 16 at 0.6, so the preferred threshold moves up.
   Write two sentences explaining why the metric did not change but the decision
   did.
3. **Break preprocessing on purpose.** In a copy of the notebook, fit
   `StandardScaler` on all rows before the CV loop, then run the same CV. Expected
   observation: PR-AUC may change by only a few thousandths, because scaling
   statistics are stable on 500 rows. That small change is exactly why leakage must
   be prevented by construction; you cannot rely on a dramatic symptom.
4. **Reproduce the leak.** Add `final_score` to the feature matrix and fit a
   depth-3 tree. Expected observation: test accuracy 1.000. Remove the column and
   confirm the score falls to about 0.86. Explain in three sentences why the higher
   number is the worse model.

## Common mistakes and how to diagnose them

| Symptom | Likely cause | First check |
| --- | --- | --- |
| 0.92 accuracy described as excellent with no baseline | Base rate ignored | Compute `max(p, 1-p)` and the confusion matrix |
| Recall is 0.75 but the report only quotes accuracy | Aggregate metric hides misses | Count FN and name who they represent |
| Threshold chosen on test, then test metrics quoted | Selection on the evaluation set | Choose on validation; freeze; score test once |
| PR-AUC compared with 0.5 as the baseline | No-skill PR-AUC is the positive rate | Compare with 0.212, not 0.5 |
| Standard deviation treated as a 95% confidence interval | Spread across folds misread | Report mean ± std and note that folds overlap |
| Scaler fitted before the split | Preprocessing leakage | Move it into a `Pipeline`; fit on training rows |
| `final_score` kept because it "improves" the model | Target leakage | Ask whether the column exists at prediction time |
| Depth chosen by training accuracy | Overfitting read as skill | Select on validation; inspect the gap |

## Checkpoint

You are ready for the lab when you can:

- [ ] Compute the majority baseline from the positive rate.
- [ ] Derive precision, recall, and F1 from a confusion matrix without a library.
- [ ] Choose a threshold from a stated cost ratio and defend it.
- [ ] Explain why PR-AUC uses the positive rate as its no-skill value.
- [ ] Identify the best depth from a train/validation curve and say why it is not
      the deepest tree.
- [ ] Report CV mean and standard deviation and explain what they do and do not
      mean.
- [ ] Name three leakage types and the prevention for each.

## Next step

1. Run the [guided notebook](notebook.md) and check your outputs against the
   expected results.
2. Complete the [lab brief](lab.md): a controlled complexity sweep on a new target,
   ending in a memo that recommends a model.
3. Score your work with the [assessment](assessment.md).
4. Continue to [F11 - Neural network fundamentals](../f11-neural-networks/index.md),
   where the same evaluation discipline applies to gradient-based models.

---

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)
