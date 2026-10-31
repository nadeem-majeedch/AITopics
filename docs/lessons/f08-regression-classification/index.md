# F08 - Regression and classification {#f08}

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Level** | 1 - Machine learning foundations (M02) |
| **Study time** | 10 hours: 3 h theory, 3 h guided notebook, 3 h lab, 1 h assessment |
| **Hardware** | CPU-only. The full notebook runs in seconds on a laptop. |
| **Prerequisites** | F07 concepts (supervised vs unsupervised learning), pandas and NumPy basics, and train/test splitting |
| **You will produce** | An executed notebook, a valuation screen with a model card, a knowledge check, and a short reflection |

## Why this module exists

A regional property fund has 40 candidate listings and one analyst. The fund asks
two questions: **what will each home sell for**, and **which listings deserve a
manual review**. A vendor offers a model with "73% accuracy" for the second
question. The fund's own majority-class guess already scores 51%, so the vendor's
number is 22 points better than doing nothing, not 73% good.

The first question is a **regression** problem: the answer is a number. The
second is a **classification** problem: the answer is a label. Both fail in the
same way when you skip the baseline, choose a metric by habit, or let the test
set influence training. This module builds both models on synthetic data, checks
every claim against a baseline, and ends with a decision rule rather than a bare
accuracy number.

## Learning objectives

By the end of this module, you can:

1. Distinguish regression from classification by naming the target, loss, output,
   and decision for each task.
2. Build a mean baseline and a majority-class baseline, and quantify how much a
   model improves on them.
3. Fit linear and ridge regression on standardized features and read coefficients
   as per-standard-deviation associations, not causal effects.
4. Fit logistic regression, obtain probabilities with `predict_proba`, and turn
   them into labels at a stated threshold.
5. Compute MAE, RMSE, R-squared, accuracy, precision, recall, and F1 from raw
   numbers, including from a confusion matrix.
6. Select a metric from a stated decision and error cost, and explain the
   precision-recall trade-off in plain language.
7. Identify claims that the evidence does not support, such as a causal reading of
   a coefficient or a deployment claim based on one test split.

## Before you start

| Requirement | Why it matters |
| --- | --- |
| F07: supervised vs unsupervised learning | You should know what a feature, label, and generalization mean |
| F05: train, validation, and test splits | Every metric in this module is computed on held-out rows |
| pandas and NumPy basics (F03) | You will build DataFrames, one-hot encode categories, and use arrays |
| scikit-learn installed | `requirements/notebooks.txt` includes it; no GPU package is needed |
| About 1 GB free disk | The tables are tiny; the environment dominates the footprint |

The notebook generates its two tables in code. The repository also ships a
documented generator and a dataset card:

- [Dataset card](../../technical/foundation-assets.md#foundation-datasets) - provenance, license,
  and known limitations of the synthetic tables.
- [Data generator](../../technical/foundation-assets.md#data-generator) - the script that
  writes `house_prices.csv` and `student_performance.csv`.

The house table has 600 rows and a nonlinear price surface. The student table has
500 rows and a binary `passed` target. Both are synthetic and carry no personal
data.

## The concepts you need

### 1. Two tasks, one workflow

A **feature** is an input column available when the prediction is made. A
**label** (or target) is what you predict. A **loss function** scores how wrong a
prediction is during training. **Generalization** is performance on rows the model
did not train on.

| Question | Task | Target | Typical loss | Output | Decision |
| --- | --- | --- | --- | --- | --- |
| What will this house sell for? | Regression | `sale_price` (dollars) | Squared error or absolute error | A number | Bid, hold, or review |
| Will this student pass? | Classification | `passed` (0 or 1) | Log loss | A probability, then a label | Invite to tutoring or not |

Both tasks follow the same workflow: define the decision, split the data, build a
baseline, fit a model, evaluate on held-out rows, and state the limitations. The
model class changes; the discipline does not.

### 2. Baselines are the bar

A **baseline** is the simplest defensible prediction. For regression, predict the
training mean for every row. For classification, predict the majority class.

```python
baseline = np.full_like(y_test, y_train.mean())   # regression
majority = int(np.bincount(y_train).argmax())
baseline_pred = np.full_like(y_test, majority)    # classification
```

In the notebook the mean baseline scores **MAE 51,734** and **RMSE 66,281**. The
majority-class baseline scores **0.512 accuracy** because the training set is
50.9% class 0 and 49.1% class 1. Any model you report must beat these numbers,
and you must say by how much.

Two rules:

- Compute the baseline statistic on the **training** rows only. Using the test
  mean or test majority is a subtle form of leakage.
- Report the baseline next to the model, not in a footnote. A model that scores
  0.728 against a 0.512 baseline is useful; the same model against a 0.70 baseline
  is not.

### 3. Linear regression

Linear regression predicts a weighted sum:

```text
prediction = intercept + b1*x1 + b2*x2 + ... + bk*xk
```

It chooses coefficients that minimize the sum of squared errors on the training
data. That choice is called **ordinary least squares**.

Three regression metrics cover different questions:

| Metric | Formula | Unit | What it emphasizes |
| --- | --- | --- | --- |
| MAE | mean of `abs(actual - predicted)` | Dollars | Typical error; easy to explain |
| RMSE | square root of mean squared error | Dollars | Large errors; punishes outliers |
| R-squared | `1 - SS_residual / SS_total` | None | Share of variance explained on this data |

On the 150 test houses, linear regression scores **MAE 21,708**, **RMSE 27,354**,
and **R-squared 0.829**. That is a 58% reduction in MAE from the 51,734 baseline.
The model still misses by about 21,700 dollars on a typical house, so it supports
screening, not a final valuation.

**Standardize before comparing coefficients.** A **standard deviation** (SD)
measures spread. After standardization, each coefficient is the predicted change
in the target for a one-SD change in that feature, holding the others fixed.

| Feature | Standardized coefficient | Approximate 1 SD here | Rough effect per natural unit |
| --- | --- | --- | --- |
| `area_sqft` | 46,020 | 500 sq ft | about +92 USD per sq ft |
| `bedrooms` | 25,913 | 1.4 bedrooms | about +18,500 USD per bedroom |
| `age_years` | -14,158 | 17 years | about -820 USD per year |
| `distance_km` | -14,062 | 2.8 km | about -5,000 USD per km |
| `garage` | 7,129 | 0.5 for a binary column | about +14,000 USD with a garage |

The natural-unit column is a rough conversion using the generator's spreads; your
sample differs slightly. Read it as association, not causation. A house with a
garage is not automatically worth 14,000 dollars more because of the garage; the
garage may stand in for size, neighborhood, or age.

A negative R-squared is possible on held-out data: the model can be worse than
predicting the test mean. That is a useful alarm, not an error in the formula.

### 4. Ridge regression

**Ridge regression** adds a penalty on the size of the coefficients:

```text
minimize: sum of squared errors + alpha * sum(beta_i squared)
```

The penalty shrinks coefficients toward zero. It helps when features are
correlated, when there are many features relative to rows, or when a small change
in the data makes ordinary least squares unstable. The intercept is not penalized,
and `alpha` controls the strength.

In the notebook, `Ridge(alpha=10.0)` scores **MAE 21,699**, **RMSE 27,382**, and
**R-squared 0.829**. That is nearly identical to linear regression. With 5 features
and 450 training rows, there is little instability to fix. The lesson is not that
ridge is useless; it is that regularization earns its place when the data has a
problem it can solve. Always standardize before tuning `alpha`, or the penalty
will punish features for their units rather than their influence.

### 5. Logistic regression

Logistic regression models the **log-odds** of the positive class:

```text
log(p / (1 - p)) = intercept + b1*x1 + ... + bk*xk
p = 1 / (1 + exp(-score))
```

The output is a probability between 0 and 1. A **threshold** converts it to a
label; 0.5 is a default, not a law. In scikit-learn, `predict` applies 0.5, while
`predict_proba` returns the probability so you can choose your own threshold.

```python
probability = classifier.predict_proba(X_test_scaled)[:, 1]
label = (probability >= 0.5).astype(int)
```

On 125 test students, logistic regression produces this **confusion matrix**,
where rows are actual and columns are predicted:

|  | Predicted 0 | Predicted 1 |
| --- | --- | --- |
| **Actual 0** | 51 (true negative) | 13 (false positive) |
| **Actual 1** | 21 (false negative) | 40 (true positive) |

From those four counts:

- Accuracy = (51 + 40) / 125 = **0.728**
- Precision = 40 / (40 + 13) = **0.755**
- Recall = 40 / (40 + 21) = **0.656**
- F1 = 2 x 0.755 x 0.656 / (0.755 + 0.656) = **0.702**

The model catches about two thirds of the students who pass and raises 13 false
alarms. Whether that is good depends on what the prediction triggers. If a positive
prediction only sends an optional enrichment email, missing some passing students
is tolerable. If a negative prediction is used to deny a place, the 21 false
negatives are a serious harm.

### 6. Metrics that match the decision

**Accuracy** is the share of correct labels. It hides the mix of errors, and it
misleads when one class dominates. **Precision** answers "when the model says
positive, how often is it right?" **Recall** answers "of the actual positives, how
many did we find?" **F1** is their harmonic mean.

| Metric | Question it answers | Costly error it ignores |
| --- | --- | --- |
| Accuracy | How many labels are correct? | Both error types equally, and class balance |
| Precision | How trustworthy is a positive flag? | Missed positives |
| Recall | How many positives are found? | False alarms |
| F1 | A single balance of precision and recall | The dollar cost of each error |
| MAE | How large is a typical dollar error? | Large individual misses |
| RMSE | How large are the largest errors? | Typical-case performance |

There is no universally best metric. A metric is a claim about what matters.
State the decision and the cost of each error before you choose one. For ranking
with rare positives, F10 introduces ROC-AUC and PR-AUC.

### 7. From metric to decision

A regression model becomes a decision when you attach a rule:

```text
review the listing if predicted_price >= 325,000
```

A classifier becomes a decision when you attach a threshold and an action. Both
rules create two kinds of error, and those errors usually cost different amounts:

| Situation | Prefer | Move the threshold | Consequence |
| --- | --- | --- | --- |
| Missing a likely home buyer is expensive | Higher recall | Down | More false alarms, more analyst time |
| Reviewing a weak listing is expensive | Higher precision | Up | More missed opportunities |
| Both errors cost about the same | F1 or accuracy | Near 0.5 | Simple to defend |
| You must rank, not label | ROC-AUC or PR-AUC | No threshold | F10 covers this |

The notebook reports the default 0.5 threshold. The practical exercise sweeps it.
The lab asks you to fix a threshold from a stated cost and defend it in a model
card.

## Guided walkthrough

The [guided notebook](notebook.md) is the evidence for this chapter. It runs in
seconds on a CPU and has six sections plus a metric summary. The quoted numbers
come from the verified Windows 11 CPU run with Python 3.12.10; no GPU or Colab run
was used.

1. **Regression data and a baseline.** Generates 600 houses, splits 450/150, and
   scores the training-mean baseline at MAE 51,734 and RMSE 66,281.
2. **Linear and ridge regression.** Standardizes with statistics from the training
   rows only, then scores both models at about MAE 21,700 and R-squared 0.829.
3. **Coefficients.** Prints the five standardized coefficients, which show area and
   bedrooms as the strongest positive associations.
4. **Classification data and a majority baseline.** Generates 500 students, splits
   375/125 with `stratify=y`, and confirms a 0.512 majority baseline.
5. **Logistic regression and the confusion matrix.** Fits the classifier and prints
   the matrix, accuracy, precision, recall, and F1.
6. **Metric guidance.** A short table maps decision contexts to metrics.

Each code section ends with an assertion. An assertion is a machine-checked claim:
for example, that R-squared exceeds 0.5 or that the classifier beats the majority
baseline. If an assertion fails, do not delete it. Diagnose the cause.

## Practical exercise

This exercise is separate from the independent lab. It takes about 45 minutes and
uses the notebook's data.

1. **Reproduce and record.** Run the notebook top to bottom. Record the split
   sizes (450/150 and 375/125), the baseline metrics, and the model metrics.
   Expected observation: the linear model cuts MAE by more than half, and ridge is
   within a few hundred dollars of linear.
2. **Recompute one row by hand.** From the confusion matrix `[[51, 13], [21, 40]]`,
   compute accuracy, precision, recall, and F1 with a calculator. Expected
   observation: your values match 0.728, 0.755, 0.656, and 0.702 within rounding.
   If not, check which cell you used as the true positive.
3. **Add the omitted location feature.** The notebook uses five numeric features
   and leaves `neighbourhood` out. In a copy of the notebook, build dummy columns
   from the training rows with `pd.get_dummies(..., drop_first=True)`, reindex the
   test rows to the same columns, and refit linear regression. Expected observation:
   MAE usually improves, because neighborhood shifts prices by tens of thousands of
   dollars in the generator. A small worsening on one split is also possible; if
   the result changes dramatically, you probably encoded before splitting or let
   the test columns differ.
4. **Sweep the threshold.** Using `predict_proba`, compute precision, recall, and
   F1 at thresholds 0.3, 0.4, 0.5, 0.6, and 0.7. Expected observation: recall
   falls and precision generally rises as the threshold increases. Choose a
   threshold for offering an optional advanced session to students predicted to
   pass, and state the cost assumption behind it. Write two sentences explaining
   why 0.5 was not automatically right and whether a false positive or a false
   negative is the more costly error for that action.

## Common mistakes and how to diagnose them

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Accuracy 0.728 is called "good" with no baseline | The 0.512 majority baseline was omitted | Print the baseline next to every accuracy number |
| Test metrics look far better than expected | Scaler or encoder fitted on all rows | Search for `.fit(X)` before the split; fit on `X_train` only |
| Coefficient read as "dollars per square foot" | Standardized coefficients were interpreted as raw units | Multiply by the feature SD, or refit on unstandardized features for a raw-unit model |
| R-squared compared across two different targets | R-squared is relative to the variance of its own target | Compare MAE/RMSE in the same units, or use the same target |
| "Location does not matter" | `neighbourhood` was dropped from the feature matrix | Check the `feature_columns` list; encode the category instead |
| Threshold tuned on the test set, then test metrics reported | Model selection happened on test rows | Choose the threshold on validation rows; touch test once |
| Precision or recall is 0 or undefined | The model predicted one class only, or `zero_division` hid it | Print the confusion matrix and the predicted class counts |
| RMSE is smaller than MAE | A coding error, not a modeling insight | Check that both metrics use the same predictions and rows |

## Checkpoint

You are ready for the lab when you can:

- [ ] Explain the difference between regression and classification using the two
      notebook examples.
- [ ] State the baseline and the improvement for both tasks without looking at
      the notebook.
- [ ] Read a standardized coefficient correctly and name one thing it does not
      prove.
- [ ] Compute precision and recall from a 2x2 confusion matrix.
- [ ] Name the metric you would report for a decision where a missed positive is
      four times as costly as a false alarm.
- [ ] Explain why the scaler must be fitted after the split.

## Next step

1. Run the [guided notebook](notebook.md) and check your outputs against the
   expected results.
2. Complete the [lab brief](lab.md): a valuation screen under a latency budget,
   with a fixed decision threshold and a model card.
3. Score your work with the [assessment](assessment.md).
4. Continue to [F09 - Decision trees, random forests, and gradient boosting](../f09-tree-ensembles/index.md),
   where the same student table is used to compare nonlinear models under one
   cross-validation protocol.

---

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)
