# F09 - Decision trees, random forests, and gradient boosting {#f09}

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Level** | 1 - Machine learning foundations (M02) |
| **Study time** | 10 hours: 3 h theory, 3 h guided notebook, 3 h lab, 1 h assessment |
| **Hardware** | CPU-only. Five hundred rows and a few hundred trees train in seconds. |
| **Prerequisites** | F08 (linear and logistic regression, baselines, confusion matrix) and basic pandas |
| **You will produce** | An executed notebook, a cost-sensitive classifier comparison with a written justification, a knowledge check, and a short reflection |

## Why this module exists

A tutoring provider wants to flag learners who are likely to fail a certification
exam. An analyst fits a decision tree and reports **100% training accuracy**. On
held-out learners the same tree scores **66.4%**, barely better than a coin flip.
A second analyst fits a random forest and reports **76%** on one test split. A
third runs five-fold cross-validation and finds the forest at **71.4%** and plain
logistic regression at **74.2%**.

All three numbers are real results from the guided notebook. They disagree because
the evaluation protocol changed, not because the data changed. This module teaches
you how trees split data, why a deep tree memorizes, how forests and boosting
correct for a single tree's weaknesses, and how to compare models without fooling
yourself with one lucky split.

## Learning objectives

By the end of this module, you can:

1. Explain how a decision tree chooses a split using Gini impurity or entropy,
   and why the choice is greedy.
2. Diagnose underfitting and overfitting from a table of training depth, training
   accuracy, test accuracy, and the gap between them.
3. Explain bootstrap sampling and random feature subsets in a random forest, and
   why averaging many trees reduces variance.
4. Explain how gradient boosting fits trees sequentially to residual errors, and
   what the learning rate and iteration count control.
5. Compare models with the same stratified cross-validation folds and report mean
   plus standard deviation instead of a single split.
6. Keep preprocessing inside a pipeline so each fold fits its own encoder and
   scaler.
7. Interpret impurity-based feature importance and state at least two reasons it
   is not a causal effect.

## Before you start

| Requirement | Why it matters |
| --- | --- |
| F08: baselines and confusion matrix | Tree comparisons still need a baseline and error counts |
| F08: train/test discipline | You will add cross-validation on top of a held-out split |
| pandas and scikit-learn basics | You will build a `ColumnTransformer` and inspect a DataFrame |
| About 1 GB free disk | The table is 500 rows; no downloads are needed |
| No GPU | The notebook trains 200-tree forests on the CPU |

The notebook generates the student table in code with seed 42. The repository
generator writes the same columns to CSV:

- [Dataset card](../../technical/foundation-assets.md#foundation-datasets) - provenance, license,
  and limits of the synthetic tables.
- [Data generator](../../technical/foundation-assets.md#data-generator) - the script that
  writes `student_performance.csv`.

The notebook's simplified generator omits the course effect from the pass
formula, so its class balance (0.49) and accuracy will not match F10 exactly.
That is expected; do not mix metrics across notebooks without checking the data.

## The concepts you need

### 1. A decision tree splits the feature space

A **decision tree** asks a sequence of yes/no questions about features. Each
internal node tests one feature against a threshold, each branch sends rows left or
right, and each **leaf** stores a prediction: the mean target for regression or the
majority class for classification. **Depth** is the number of splits on the longest
path from root to leaf.

A split is chosen to reduce **impurity**, a measure of how mixed the labels are in
a node. Two common measures for a node with positive fraction `p`:

```text
Gini impurity = 1 - (p^2 + (1-p)^2)
Entropy       = -(p * log2(p) + (1-p) * log2(1-p))
```

A pure node has impurity 0. A 50/50 node has Gini 0.5 and entropy 1.0.

**Worked example.** A parent node has 10 rows, 6 positive and 4 negative, so its
Gini is `1 - (0.6^2 + 0.4^2) = 0.48`. A candidate split sends 6 rows (5 positive,
1 negative) left and 4 rows (1 positive, 3 negative) right:

```text
left Gini  = 1 - ((5/6)^2 + (1/6)^2) = 0.278
right Gini = 1 - ((1/4)^2 + (3/4)^2) = 0.375
weighted   = 0.6 * 0.278 + 0.4 * 0.375 = 0.317
gain       = 0.48 - 0.317 = 0.163
```

The tree tries every feature and threshold, keeps the split with the largest gain,
and repeats. It is **greedy**: each split is locally best, not guaranteed to
produce the smallest tree overall.

```python
tree = DecisionTreeClassifier(max_depth=5, random_state=42)
tree.fit(X_train, y_train)
```

Trees need little preprocessing: they can use raw numeric features and are
invariant to monotone scaling. They cannot consume raw text or unordered
categories, so those must be encoded first.

### 2. Depth controls underfitting and overfitting

A **shallow** tree has high bias: it cannot represent the pattern, so both training
and test scores are low. That is **underfitting**. A **deep** tree has high
variance: it can memorize individual training rows, so training accuracy rises
while test accuracy stalls or falls. That is **overfitting**. The distance between
training and test performance is the practical alarm.

| `max_depth` | Leaves | Train accuracy | Test accuracy | Gap |
| --- | --- | --- | --- | --- |
| 2 | 4 | 0.659 | 0.656 | 0.003 |
| 5 | 25 | 0.811 | 0.696 | 0.115 |
| None (unlimited) | 86 | 1.000 | 0.664 | 0.336 |

Depth 2 is underfitting: it has almost no gap, but both scores are weak. Depth 5
fits the training data better and generalizes best of the three. The unlimited
tree is a perfect memorizer with the largest gap and a lower test score than depth
5.

The best depth is the one selected on validation data, not the one with perfect
training accuracy. In the notebook, the tree depth 5 test score (0.696) is higher
than the unlimited tree (0.664) even though the unlimited tree looks unbeatable on
training rows.

### 3. Random forests average many trees

A **random forest** fits many decision trees and averages their votes. Each tree
is trained on a **bootstrap sample**: rows drawn with replacement, so about 63.2%
of distinct rows appear in a given sample and the rest are left out. At each split,
the tree considers only a random subset of features. The randomness **decorrelates**
the trees, so their errors do not all point the same way. Averaging correlated
predictions reduces variance without adding much bias.

```python
forest = RandomForestClassifier(
    n_estimators=200,
    min_samples_leaf=5,
    random_state=42,
    n_jobs=-1,
)
forest.fit(X_train, y_train)
```

Key settings:

| Setting | Effect | Notebook value |
| --- | --- | --- |
| `n_estimators` | More trees reduce variance but cost time; returns diminish | 200 |
| `max_features` | Fewer features per split means more decorrelation | scikit-learn default |
| `min_samples_leaf` | Larger leaves smooth predictions and limit overfitting | 5 |
| `n_jobs` | Parallel CPU cores; does not change the result | -1 |

On the notebook's single split the forest scores **0.76** test accuracy. Section 5
shows why that number needs a second protocol before you trust the ranking.

### 4. Gradient boosting fits trees in sequence

**Gradient boosting** builds an ensemble sequentially. Start with a simple
prediction. Fit a small tree to the current errors (more precisely, the negative
gradient of the loss), add it to the ensemble with a **learning rate** that shrinks
its contribution, then repeat. Each tree corrects part of what the previous
ensemble got wrong.

```python
boosting = HistGradientBoostingClassifier(
    max_iter=200,
    learning_rate=0.05,
    random_state=42,
)
boosting.fit(X_train, y_train)
```

`HistGradientBoostingClassifier` bins numeric features into histograms, which makes
it fast on tabular data. `max_iter` is the number of boosting rounds and
`learning_rate` controls how much each round contributes. A small learning rate
with many rounds often generalizes well but trains longer; a large rate can
overshoot. The notebook's configuration scores **0.736** on the single test split.

| Property | Random forest | Gradient boosting |
| --- | --- | --- |
| Tree construction | Independent, in parallel | Sequential, each tree depends on the last |
| Main mechanism | Variance reduction by averaging | Bias reduction by correcting errors |
| Key risks | Many trees cost time; still opaque | Overfits if rounds too many or rate too high |
| Typical strength | Robust default on small tables | Strong accuracy when tuned carefully |

### 5. Compare with the same folds, not one split

**Cross-validation** (CV) splits the data into `k` parts, trains on `k-1`, tests on
the held-out part, and repeats until every part has been held out once. **Stratified**
k-fold keeps the class ratio close to the full table in every fold. Report the mean
and standard deviation across folds; the spread tells you how much the result
depends on which rows landed where.

The notebook uses the same stratified 5-fold split for all four models:

| Model | CV accuracy (mean ± std) |
| --- | --- |
| Logistic regression | **0.742 ± 0.027** |
| Random forest | 0.714 ± 0.033 |
| Gradient boosting | 0.678 ± 0.044 |
| Decision tree, depth 5 | 0.662 ± 0.044 |

Compare this with the single-split results: the forest scored 0.76 and boosting
0.736 there. The single split was kind to the ensembles. Under CV, logistic
regression leads, and the forest is 0.028 behind with a standard deviation of
0.033. That difference is smaller than the fold-to-fold noise, so the honest
conclusion is "logistic regression is at least as good on this table," not "the
forest is worse by exactly 2.8 points."

A single split is one sample. CV is several samples with overlapping training
sets. Neither replaces a final held-out test for a model you intend to ship.

### 6. Keep preprocessing inside the pipeline

A **pipeline** chains preprocessing and a model into one object. A
`ColumnTransformer` applies different transformations to different columns:

```python
preprocess = ColumnTransformer([
    ("num", StandardScaler(), ["study_hours", "attendance", "prior_score", "sleep_hours"]),
    ("cat", OneHotEncoder(handle_unknown="ignore"), ["tutoring", "course"]),
])

model = Pipeline([
    ("pre", preprocess),
    ("model", LogisticRegression(max_iter=2000, random_state=42)),
])
```

When `cross_val_score` evaluates this pipeline, it clones the whole object for each
fold. The scaler and encoder are fitted on that fold's training rows only. If you
fit the encoder on all rows before cross-validation, each fold's training data has
already seen the validation fold's category levels and scaling statistics. That is
**preprocessing leakage**, and it makes the CV score optimistic.

`handle_unknown="ignore"` prevents a crash when a fold contains a category that
was absent from its training rows; the unseen level becomes all zeros.

### 7. Feature importance is a hint, not a cause

Impurity-based **feature importance** records how much each feature reduced
impurity across the forest, weighted by the number of rows passing through the
split. The notebook's forest ranks:

| Feature | Importance |
| --- | --- |
| `study_hours` | 0.267 |
| `attendance` | 0.256 |
| `prior_score` | 0.233 |
| `sleep_hours` | 0.126 |
| `tutoring_yes` | 0.037 |
| `tutoring_no` | 0.034 |
| `course_Math` | 0.017 |
| `course_Physics` | 0.016 |

Two cautions:

1. **Bias.** Impurity importance favors features with many distinct values and can
   split credit among correlated features. A one-hot encoded category is divided
   across its dummy columns, which makes each dummy look weak even when the
   category matters.
2. **Correlation is not causation.** A high importance means the feature helped
   predict in this sample, not that changing it would change the outcome. Use
   permutation importance on held-out data, controlled experiments, or domain
   knowledge before making a causal claim.

## Guided walkthrough

The [guided notebook](notebook.md) is the evidence for this chapter. It runs
quickly on a CPU and has six sections. The quoted numbers come from the verified
Windows 11 CPU run with Python 3.12.10; no GPU or Colab run was used.

1. **Data and preprocessing.** Generates 500 students with 6 features, confirms a
   0.49 positive rate, and builds a `ColumnTransformer` that scales numeric columns
   and one-hot encodes categorical ones.
2. **A single tree and depth.** Fits depth 2, 5, and unlimited trees and prints
   train accuracy, test accuracy, and leaf counts. This is the overfitting table.
3. **Random forest.** Fits 200 trees with `min_samples_leaf=5` and scores 0.76 on
   the test split.
4. **Gradient boosting.** Fits 200 histogram-based rounds at learning rate 0.05 and
   scores 0.736 on the same split.
5. **Cross-validation.** Re-scores logistic regression, a depth-5 tree, the forest,
   and boosting on identical stratified folds. This is the table you should quote.
6. **Feature importance.** Prints the forest's impurity importances and explains
   why they are not causal.

The notebook ends with a checklist. If you cannot answer one item, rerun the
section that produced its evidence.

## Practical exercise

This exercise is separate from the independent lab. It takes about 45 minutes.

1. **Reproduce the comparison.** Run the notebook top to bottom and copy the CV
   table. Expected observation: logistic regression 0.742 ± 0.027, random forest
   0.714 ± 0.033, boosting 0.678 ± 0.044, depth-5 tree 0.662 ± 0.044. If your
   numbers differ by more than about 0.01, check that all four models used the same
   `cv` object and the same `X`, `y`.
2. **Sweep one hyperparameter.** With the same folds, fit random forests with
   `min_samples_leaf` set to 1, 5, and 20. Record mean CV accuracy, standard
   deviation, and training accuracy for each. Expected observation: leaf 1 drives
   training accuracy toward 1.0 and usually leaves CV at or below the leaf-5
   result; leaf 20 underfits and usually lowers both. The best setting is chosen on
   CV, not on training.
3. **Quantify the gap.** Using the depth table, compute train minus test accuracy
   for depths 2, 5, and None. Expected observation: about 0.003, 0.115, and 0.336.
   Explain in two sentences which model you would deploy and why the unlimited tree
   is not it.
4. **Change the metric.** Re-score the same four models with `scoring="f1"` and
   then `scoring="average_precision"`. Expected observation: because the classes
   are nearly balanced, F1 will be close to accuracy; PR-AUC may reorder models
   that accuracy treats as similar. Report whether the ranking changed, and do not
   treat a change smaller than one standard deviation as a real difference.

## Common mistakes and how to diagnose them

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Model chosen because training accuracy is 1.000 | Overfitting was read as skill | Compare test or CV accuracy; compute the train-test gap |
| Forest looks better on one split but loses under CV | Single-split noise | Report the CV mean and std; do not rank on one split |
| CV score is suspiciously high | Encoder or scaler fitted before CV | Move preprocessing into the `Pipeline` |
| Models compared with different folds | A new `train_test_split` or `KFold` per model | Reuse one `cv` object for every candidate |
| Feature importance called "the cause" | Impurity importance misread | State that it is predictive, then use permutation importance or an experiment |
| One-hot category importance looks negligible | Importance split across dummy columns | Sum the dummies for the category before comparing |
| More trees always assumed better | Diminishing returns and compute cost ignored | Compare 50, 200, and 500 trees on the same folds |
| Category value crashes the encoder in a fold | Unseen level in validation | Use `handle_unknown="ignore"` |

## Checkpoint

You are ready for the lab when you can:

- [ ] Explain what a tree split optimizes and why the search is greedy.
- [ ] Identify underfitting and overfitting from a depth table without the labels.
- [ ] Explain what a random forest averages and why that reduces variance.
- [ ] Explain how boosting differs from bagging in one sentence.
- [ ] State why the CV ranking is more trustworthy than the single-split ranking.
- [ ] Explain why preprocessing must be fitted inside each CV fold.
- [ ] Name two reasons feature importance is not a causal effect.

## Next step

1. Run the [guided notebook](notebook.md) and check your outputs against the
   expected results.
2. Complete the [lab brief](lab.md): compare classifiers for an early-warning
   program with unequal error costs, and justify your metric in writing.
3. Score your work with the [assessment](assessment.md).
4. Continue to [F10 - Metrics, overfitting, underfitting, data leakage, and cross-validation](../f10-metrics-validation/index.md),
   where evaluation becomes the main subject rather than a comparison tool.

---

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)
